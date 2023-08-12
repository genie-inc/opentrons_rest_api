""" Opentron REST Server """
from dataclasses import dataclass
from enum import Enum
from typing import Any, DefaultDict, Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from opentrons.execute import get_protocol_api
from opentrons.protocol_api import InstrumentContext, ProtocolContext, Well

FIXED_TRASH_SLOT = 12
VERSION = '0.1.0'

class CommandId(str, Enum):
    Home = 'Home'
    Initialize = 'Initialize'
    LoadLabware = 'LoadLabware'
    AffixTip = 'AffixTip'
    EjectTip = 'EjectTip'
    Aspirate = 'Aspirate'
    Dispense = 'Dispense'
    ClearLabware = 'ClearLabware'
    LoadLabwareDef = 'LoadLabwareDef'
    GetLabware = 'GetLabware'
    Mix = 'Mix'


@dataclass
class ResourceRef():
    name: str
    location: str

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'ResourceRef':
        return ResourceRef(name=state['name'], location=state['location'])


@dataclass
class LoadLabwareDef():
    location: str
    labware_def: Dict[str, Any]

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'LoadLabwareDef':
        return LoadLabwareDef(location=state['location'], labware_def=state['labware_def'])


@dataclass
class WellRef():
    slot: int
    well_id: str

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'WellRef':
        return WellRef(slot=state['slot'], well_id=state['well_id'])

    def to_dict(self) -> Dict[str, Any]:
        obj_dict: Dict[str, Any] = DefaultDict()
        obj_dict['slot'] = self.slot
        obj_dict['well_id'] = self.well_id
        return obj_dict


@dataclass
class PartialTransfer(WellRef):
    volume: float
    flowrate: float
    z_bottom_offset: float
    post_aspirate_air_gap_ul: Optional[float] = None
    post_dispense_blowout_z_bottom_offset: Optional[float] = None

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'PartialTransfer':
        return PartialTransfer(slot=state['slot'], well_id=state['well_id'], volume=state['volume'],
                               flowrate=state['flowrate'], z_bottom_offset=state['z_bottom_offset'],
                               post_aspirate_air_gap_ul=state.get('post_aspirate_air_gap_ul', None),
                               post_dispense_blowout_z_bottom_offset=state.get('post_dispense_blowout_z_bottom_offset', None))


@dataclass
class MixSettings(WellRef):
    volume: float
    cycles: int
    z_bottom_offset: float
    aspirate_flowrate: float
    dispense_flowrate: float
    post_mix_blowout_z_bottom_offset: Optional[float] = None

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'MixSettings':
        return MixSettings(slot=state['slot'], well_id=state['well_id'], volume=state['volume'],
                           cycles=state['cycles'], z_bottom_offset=state['z_bottom_offset'],
                           aspirate_flowrate=state['aspirate_flowrate'], dispense_flowrate=state['dispense_flowrate'],
                           post_mix_blowout_z_bottom_offset=state.get('post_mix_blowout_z_bottom_offset', None))

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = super().to_dict()
        obj_dict['volume'] = self.volume
        obj_dict['cycles'] = self.cycles
        obj_dict['z_bottom_offset'] = self.z_bottom_offset
        obj_dict['aspirate_flowrate'] = self.aspirate_flowrate
        obj_dict['dispense_flowrate'] = self.dispense_flowrate
        if self.post_mix_blowout_z_bottom_offset is not None:
            obj_dict['post_mix_blowout_z_bottom_offset'] = self.post_mix_blowout_z_bottom_offset
        return obj_dict


class ContextManager():
    def __init__(self):
        self._context: Optional[ProtocolContext] = None
        self.instruments: Dict[str, InstrumentContext] = DefaultDict()
        self._default_instrument: Optional[InstrumentContext] = None

    @property
    def ctx(self) -> ProtocolContext:
        if self._context is None:
            self._context = get_protocol_api('2.0')
        return self._context

    @property
    def default_instrument(self) -> InstrumentContext:
        if self._default_instrument is None:
            raise HTTPException(status_code=400, detail='Instrument not initialized')
        return self._default_instrument

    def load_instrument(self, ref: ResourceRef) -> InstrumentContext:
        if ref.location not in self.instruments:
            instrument = self.ctx.load_instrument(ref.name, ref.location)
            instrument.home()
            self.instruments[ref.location] = instrument
            if self._default_instrument is None:
                self._default_instrument = instrument
        return self.instruments[ref.location]

    def load_labware(self, ref: ResourceRef) -> None:
        self.ctx.load_labware(ref.name, ref.location)

    def load_labware_from_definition(self, arg: LoadLabwareDef) -> None:
        labware_label = arg.labware_def.get('metadata', {}).get('displayName', 'custom labware')
        self.ctx.load_labware_from_definition(arg.labware_def, arg.location, labware_label)  # type: ignore

    def get_well(self, ref: WellRef) -> Well:
        labware = self.ctx.loaded_labwares[ref.slot]
        return labware.wells_by_name()[ref.well_id]

    def clear_labware(self) -> None:
        for slot_id in self.ctx.deck:
            if self.ctx.deck[slot_id] is not None:
                if slot_id != FIXED_TRASH_SLOT:
                    del self.ctx.deck[slot_id]

    def mix(self, mix: MixSettings):
        """ Perform a standalone mix """
        self.default_instrument.flow_rate.aspirate = mix.aspirate_flowrate
        self.default_instrument.flow_rate.dispense = mix.dispense_flowrate
        location = self.get_well(mix).bottom(mix.z_bottom_offset)
        self.default_instrument.mix(volume=mix.volume, location=location, repetitions=mix.cycles)
        if mix.post_mix_blowout_z_bottom_offset is not None:
            location = self.get_well(mix).bottom(mix.post_mix_blowout_z_bottom_offset)
            self.default_instrument.blow_out(location=location)

    def reset(self) -> None:
        self.instruments = DefaultDict()
        self._default_instrument = None

        if self._context is not None:
            self._context.cleanup()
        self._context = None

    def aspirate(self, transfer: PartialTransfer) -> None:
        self.default_instrument.flow_rate.aspirate = transfer.flowrate
        location = self.get_well(transfer).bottom(transfer.z_bottom_offset)
        self.default_instrument.aspirate(volume=transfer.volume, location=location)
        if transfer.post_aspirate_air_gap_ul is not None:
            self.default_instrument.air_gap(transfer.post_aspirate_air_gap_ul)

    def dispense(self, transfer: PartialTransfer) -> None:
        self.default_instrument.flow_rate.dispense = transfer.flowrate
        location = self.get_well(transfer).bottom(transfer.z_bottom_offset)
        self.default_instrument.dispense(volume=transfer.volume, location=location)
        if transfer.post_dispense_blowout_z_bottom_offset is not None:
            location = self.get_well(transfer).bottom(transfer.post_dispense_blowout_z_bottom_offset)
            self.default_instrument.blow_out(location=location)

    def execute(self, command: Dict) -> Dict:
        try:
            command_id = command['command_id']
            if command_id == CommandId.Home:
                self.default_instrument.home()
            elif command_id == CommandId.Initialize:
                list(map(self.load_instrument, list(map(ResourceRef.from_dict, command['command_input']))))
            elif command_id == CommandId.LoadLabware:
                list(map(self.load_labware, list(map(ResourceRef.from_dict, command['command_input']))))
            elif command_id == CommandId.LoadLabwareDef:
                list(map(self.load_labware_from_definition, list(map(LoadLabwareDef.from_dict, command['command_input']))))
            elif command_id == CommandId.AffixTip:
                affix_well = self.get_well(WellRef.from_dict(command['command_input']))
                self.default_instrument.pick_up_tip(affix_well)
            elif command_id == CommandId.EjectTip:
                eject_well = self.get_well(WellRef.from_dict(command['command_input']))
                self.default_instrument.drop_tip(eject_well, False)
            elif command_id == CommandId.Aspirate:
                self.aspirate(PartialTransfer.from_dict(command['command_input']))
            elif command_id == CommandId.Dispense:
                self.dispense(PartialTransfer.from_dict(command['command_input']))
            elif command_id == CommandId.ClearLabware:
                self.clear_labware()
            elif command_id == CommandId.Mix:
                self.mix(MixSettings.from_dict(command['command_input']))
            else:
                raise ValueError(f'command_id: {command_id} not a handled command')

            return {'command_id': command_id, 'status': 'Completed'}
        except Exception as ex:  # pylint: disable=broad-except
            return {'command_id': command_id, 'status': 'Failed', 'message': str(ex)}


MGR = ContextManager()


@asynccontextmanager
async def lifespan():
    yield
    MGR.reset()

app = FastAPI(lifespan=lifespan)  # pylint: disable=invalid-name


@app.get('/version/')
def version():
    return {'version': VERSION}


@app.post('/reset')
def reset():
    MGR.reset()
    return {}


@app.get('/instruments/')
def get_instruments():
    return list(map(lambda lw: {'name': lw[1].name, 'location': lw[0]}, MGR.instruments.items()))


@app.get('/labware')
def get_labware():
    return list(map(lambda lw: {'name': lw[1].name, 'location': lw[0]}, MGR.ctx.loaded_labwares.items()))


@app.post('/commands')
def execute(req: Dict):
    return list(map(MGR.execute, req['commands']))
