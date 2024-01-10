""" Opentron REST Server """
from os import environ
from dataclasses import dataclass
from enum import Enum
from typing import Any, DefaultDict, Dict, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from opentrons.execute import get_protocol_api
from opentrons.simulate import get_protocol_api as get_simulated_protocol_api
from opentrons.protocol_api import InstrumentContext, MAX_SUPPORTED_VERSION, MIN_SUPPORTED_VERSION, ProtocolContext, Well
from opentrons.types import Point, Mount

FIXED_TRASH = 'fixedTrash'
VERSION = '0.4.0'
MAX_TIP_LENGTH = 80


class OpentronsRobotType(str, Enum):
    OT2 = 'OT-2 Standard'
    Flex = 'OT-3 Standard'


class CommandStatus(str, Enum):
    Completed = 'Completed'
    Failed = 'Failed'


class CommandId(str, Enum):
    Home = 'Home'
    HomeAll = 'HomeAll'
    Initialize = 'Initialize'
    SetApiVersion = 'SetApiVersion'
    LoadLabware = 'LoadLabware'
    AffixTip = 'AffixTip'
    EjectTip = 'EjectTip'
    Aspirate = 'Aspirate'
    Dispense = 'Dispense'
    ClearLabware = 'ClearLabware'
    LoadLabwareDef = 'LoadLabwareDef'
    GetLabware = 'GetLabware'
    Mix = 'Mix'
    MoveTo = 'MoveTo'
    BlowOut = 'BlowOut'
    ForceEjectTip = 'ForceEjectTip'
    TouchTip = 'TouchTip'


@dataclass
class SetApiVersionCommand():
    api_version: str

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'SetApiVersionCommand':
        return SetApiVersionCommand(api_version=state['api_version'])

    def to_dict(self) -> Dict[str, Any]:
        obj_dict: Dict[str, Any] = DefaultDict()
        obj_dict['api_version'] = self.api_version
        return obj_dict


@dataclass
class ResourceRef():
    name: str
    location: str

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'ResourceRef':
        return ResourceRef(name=state['name'], location=state['location'])

    def to_dict(self) -> Dict[str, Any]:
        obj_dict: Dict[str, Any] = DefaultDict()
        obj_dict['name'] = self.name
        obj_dict['location'] = self.location
        return obj_dict

    def __str__(self) -> str:
        return f'head: {self.name}, location: {self.location}'


@dataclass
class LoadLabwareDef():
    location: str
    labware_def: Dict[str, Any]

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'LoadLabwareDef':
        return LoadLabwareDef(location=state['location'], labware_def=state['labware_def'])

    def to_dict(self) -> Dict[str, Any]:
        obj_dict: Dict[str, Any] = DefaultDict()
        obj_dict['location'] = self.location
        obj_dict['labware_def'] = self.labware_def
        return obj_dict


@dataclass
class InstrumentCommand():
    ref: ResourceRef

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'InstrumentCommand':
        return InstrumentCommand(ref=ResourceRef.from_dict(state['head_ref']))

    def to_dict(self) -> Dict[str, Any]:
        obj_dict: Dict[str, Any] = DefaultDict()
        obj_dict['head_ref'] = self.ref.to_dict()
        return obj_dict


@dataclass
class WellRef(InstrumentCommand):
    slot: int
    well_id: str

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'WellRef':
        ref = super().from_dict(state).ref
        return WellRef(ref=ref, slot=state['slot'], well_id=state['well_id'])

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = super().to_dict()
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
        well_ref = super().from_dict(state)
        return PartialTransfer(ref=well_ref.ref, slot=well_ref.slot, well_id=well_ref.well_id,
                               volume=state['volume'], flowrate=state['flowrate'], z_bottom_offset=state['z_bottom_offset'],
                               post_aspirate_air_gap_ul=state.get('post_aspirate_air_gap_ul', None),
                               post_dispense_blowout_z_bottom_offset=state.get('post_dispense_blowout_z_bottom_offset', None))

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = super().to_dict()
        obj_dict['volume'] = self.volume
        obj_dict['flowrate'] = self.flowrate
        obj_dict['z_bottom_offset'] = self.z_bottom_offset
        if self.post_dispense_blowout_z_bottom_offset is not None:
            obj_dict['post_dispense_blowout_z_bottom_offset'] = self.post_dispense_blowout_z_bottom_offset
        if self.post_aspirate_air_gap_ul is not None:
            obj_dict['post_aspirate_air_gap_ul'] = self.post_aspirate_air_gap_ul
        return obj_dict


@dataclass
class BlowoutSettings(WellRef):
    flowrate: float
    z_bottom_offset: float

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'BlowoutSettings':
        well_ref = super().from_dict(state)
        return BlowoutSettings(ref=well_ref.ref, slot=well_ref.slot, well_id=well_ref.well_id,
                               flowrate=state['flowrate'], z_bottom_offset=state['z_bottom_offset'])

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = super().to_dict()
        obj_dict['flowrate'] = self.flowrate
        obj_dict['z_bottom_offset'] = self.z_bottom_offset
        return obj_dict


@dataclass
class XYZVector:
    x: float  # pylint: disable=invalid-name
    y: float  # pylint: disable=invalid-name
    z: float  # pylint: disable=invalid-name

    def to_dict(self) -> Dict[str, Any]:
        obj_dict: Dict[str, Any] = DefaultDict()
        obj_dict['x'] = self.x
        obj_dict['y'] = self.y
        obj_dict['z'] = self.z
        return obj_dict

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'XYZVector':
        return XYZVector(x=float(state['x']), y=float(state['y']), z=float(state['z']))


@dataclass
class MoveOffset():
    offset: XYZVector
    ignore_tip: bool

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'MoveOffset':
        return MoveOffset(offset=XYZVector.from_dict(state['offset']), ignore_tip=bool(state['ignore_tip']))

    def to_dict(self) -> Dict[str, Any]:
        obj_dict: Dict[str, Any] = DefaultDict()
        obj_dict['offset'] = self.offset.to_dict()
        obj_dict['ignore_tip'] = self.ignore_tip
        return obj_dict


@dataclass
class MoveDestination(WellRef):
    offset: Optional[MoveOffset]
    min_z: Optional[float]

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'MoveDestination':
        ref = ResourceRef.from_dict(state['head_ref'])
        offset = MoveOffset.from_dict(state['offset']) if 'offset' in state else None
        return MoveDestination(ref=ref, slot=state['slot'], well_id=state['well_id'], offset=offset, min_z=state.get('min_z', None))

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = super().to_dict()
        if self.offset is not None:
            obj_dict['offset'] = self.offset.to_dict()
        if self.min_z is not None:
            obj_dict['min_z'] = self.min_z
        return obj_dict


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
        well_ref = super().from_dict(state)
        return MixSettings(ref=well_ref.ref, slot=well_ref.slot, well_id=well_ref.well_id,
                           volume=state['volume'], cycles=state['cycles'], z_bottom_offset=state['z_bottom_offset'],
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


@dataclass
class TouchTipSettings(WellRef):
    offset_from_top: float
    radius: float
    speed: float

    @classmethod
    def from_dict(cls, state: Dict[str, Any]) -> 'TouchTipSettings':
        well_ref = super().from_dict(state)
        return TouchTipSettings(ref=well_ref.ref, slot=well_ref.slot, well_id=well_ref.well_id, offset_from_top=float(state['offset_from_top']), radius=float(state['radius']), speed=float(state['speed']))

    def to_dict(self) -> Dict[str, Any]:
        obj_dict = super().to_dict()
        obj_dict['offset_from_top'] = self.offset_from_top
        obj_dict['radius'] = self.radius
        obj_dict['speed'] = self.speed
        return obj_dict


class ContextManager():
    def __init__(self):
        self._context: Optional[ProtocolContext] = None
        self.instruments: Dict[str, InstrumentContext] = DefaultDict()
        self.api_version = str(MIN_SUPPORTED_VERSION)

    @property
    def ctx(self) -> ProtocolContext:
        if self._context is None:
            if not self.debug:
                self._context = get_protocol_api(self.api_version)
            else:
                self._context = get_simulated_protocol_api(self.api_version)
        return self._context

    @property
    def _hardware(self):
        """ Using Private APIs -- may not work with all Opentrons software packages """
        return self.ctx._core.get_hardware()  # pylint: disable=protected-access

    @property
    def debug(self) -> bool:
        return 'OT_DEBUG' in environ

    def get_protocol_api(self, api_version_request: SetApiVersionCommand) -> ProtocolContext:
        if self.api_version != api_version_request.api_version:
            self.api_version = api_version_request.api_version
            self.reset()
        return self.ctx


    def load_instrument(self, ref: ResourceRef) -> InstrumentContext:
        if ref.location not in self.instruments or self.instruments[ref.location].hw_pipette.get('name', '') != ref.name:
            self.instruments[ref.location] = self.ctx.load_instrument(ref.name, ref.location, replace=True)

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
            deck_item: Any = self.ctx.deck[slot_id]
            if deck_item is not None and (not hasattr(deck_item, 'quirks') or FIXED_TRASH not in deck_item.quirks):
                del self.ctx.deck[slot_id]

    def mix(self, mix: MixSettings):
        """ Perform a standalone mix """
        self.load_instrument(mix.ref).flow_rate.aspirate = mix.aspirate_flowrate
        self.load_instrument(mix.ref).flow_rate.dispense = mix.dispense_flowrate
        location = self.get_well(mix).bottom(mix.z_bottom_offset)
        self.load_instrument(mix.ref).mix(volume=mix.volume, location=location, repetitions=mix.cycles)
        if mix.post_mix_blowout_z_bottom_offset is not None:
            location = self.get_well(mix).bottom(mix.post_mix_blowout_z_bottom_offset)
            self.load_instrument(mix.ref).blow_out(location=location)

    def move_to(self, dest: MoveDestination) -> None:
        """ Perform a move to the specified location """
        instrument = self.load_instrument(dest.ref)
        offset = XYZVector(x=0.0, y=0.0, z=0.0)
        if dest.offset is not None:
            offset = dest.offset.offset
            if dest.offset.ignore_tip:
                offset.z -= instrument.hw_pipette.get('tip_length', 0)
        location = self.get_well(dest).top().move(Point(offset.x, offset.y, offset.z))
        instrument.move_to(location=location, minimum_z_height=dest.min_z)

    def reset(self) -> None:
        self.instruments = DefaultDict()

        if self._context is not None:
            self._context.cleanup()
        self._context = None

    def aspirate(self, transfer: PartialTransfer) -> None:
        self.load_instrument(transfer.ref).flow_rate.aspirate = transfer.flowrate
        location = self.get_well(transfer).bottom(transfer.z_bottom_offset)
        self.load_instrument(transfer.ref).aspirate(volume=transfer.volume, location=location)
        if transfer.post_aspirate_air_gap_ul is not None:
            self.load_instrument(transfer.ref).air_gap(transfer.post_aspirate_air_gap_ul)

    def dispense(self, transfer: PartialTransfer) -> None:
        self.load_instrument(transfer.ref).flow_rate.dispense = transfer.flowrate
        location = self.get_well(transfer).bottom(transfer.z_bottom_offset)
        self.load_instrument(transfer.ref).dispense(volume=transfer.volume, location=location)
        if transfer.post_dispense_blowout_z_bottom_offset is not None:
            location = self.get_well(transfer).bottom(transfer.post_dispense_blowout_z_bottom_offset)
            self.load_instrument(transfer.ref).blow_out(location=location)

    def blow_out(self, blowout: BlowoutSettings) -> None:
        self.load_instrument(blowout.ref).flow_rate.blow_out = blowout.flowrate
        location = self.get_well(blowout).bottom(blowout.z_bottom_offset)
        self.load_instrument(blowout.ref).blow_out(location=location)

    def affix_tip(self, well_ref: WellRef) -> None:
        well = self.get_well(well_ref)
        self.load_instrument(well_ref.ref).pick_up_tip(well)

    def eject_tip(self, well_ref: WellRef) -> None:
        well = self.get_well(well_ref)
        self.load_instrument(well_ref.ref).drop_tip(well)

    def force_eject_tip(self, well_ref: WellRef) -> None:
        """ During error recovery it is possible for a tip to be attached, but the Context
            to not know it. This allows a force eject. """
        inst = self.load_instrument(well_ref.ref)
        if inst._has_tip:  # pylint: disable=protected-access
            self.eject_tip(well_ref)
        elif not self.ctx.is_simulating() and self._hardware.get_config().model == OpentronsRobotType.OT2:
            mount = Mount.string_to_mount(inst.mount)
            self._hardware.add_tip(mount, MAX_TIP_LENGTH)
            self.eject_tip(well_ref)

    def home(self, ref: ResourceRef) -> None:
        self.load_instrument(ref).home()

    def touch_tip(self, settings: TouchTipSettings) -> None:
        well = self.get_well(settings)
        self.load_instrument(settings.ref).touch_tip(well, settings.radius, settings.offset_from_top, settings.speed)

    def execute(self, command: Dict) -> Dict:
        try:
            command_id = command['command_id']
            if command_id == CommandId.HomeAll:
                self.ctx.home()
            elif command_id == CommandId.Home:
                self.home(ResourceRef.from_dict(command['command_input']))
            elif command_id == CommandId.SetApiVersion:
                self.get_protocol_api(SetApiVersionCommand.from_dict(command['command_input']))
            elif command_id == CommandId.Initialize:
                list(map(self.load_instrument, list(map(ResourceRef.from_dict, command['command_input']))))
            elif command_id == CommandId.LoadLabware:
                list(map(self.load_labware, list(map(ResourceRef.from_dict, command['command_input']))))
            elif command_id == CommandId.LoadLabwareDef:
                list(map(self.load_labware_from_definition, list(map(LoadLabwareDef.from_dict, command['command_input']))))
            elif command_id == CommandId.AffixTip:
                self.affix_tip(WellRef.from_dict(command['command_input']))
            elif command_id == CommandId.EjectTip:
                self.eject_tip(WellRef.from_dict(command['command_input']))
            elif command_id == CommandId.ForceEjectTip:
                self.force_eject_tip(WellRef.from_dict(command['command_input']))
            elif command_id == CommandId.Aspirate:
                self.aspirate(PartialTransfer.from_dict(command['command_input']))
            elif command_id == CommandId.Dispense:
                self.dispense(PartialTransfer.from_dict(command['command_input']))
            elif command_id == CommandId.BlowOut:
                self.blow_out(BlowoutSettings.from_dict(command['command_input']))
            elif command_id == CommandId.ClearLabware:
                self.clear_labware()
            elif command_id == CommandId.Mix:
                self.mix(MixSettings.from_dict(command['command_input']))
            elif command_id == CommandId.MoveTo:
                self.move_to(MoveDestination.from_dict(command['command_input']))
            elif command_id == CommandId.TouchTip:
                self.touch_tip(TouchTipSettings.from_dict(command['command_input']))
            else:
                raise ValueError(f'command_id: {command_id} not a handled command')

            return {'command_id': command_id, 'status': CommandStatus.Completed}
        except Exception as ex:  # pylint: disable=broad-except
            return {'command_id': command_id, 'status': CommandStatus.Failed, 'message': str(ex)}


MGR = ContextManager()


@asynccontextmanager
async def lifespan():
    yield
    MGR.reset()

app = FastAPI(lifespan=lifespan)  # pylint: disable=invalid-name


@app.get('/version/')
def version():
    return {'version': VERSION, 'protocol_api_version' : {'min': str(MIN_SUPPORTED_VERSION), 'max': str(MAX_SUPPORTED_VERSION)}}


@app.post('/reset')
def reset():
    MGR.reset()
    return {}


@app.get('/discover/')
def discover():
    """ This command uses a private API and therefore may not always work """
    try:
        attached = MGR._hardware.attached_instruments  # type: ignore # pylint: disable=protected-access
        return {'left': attached[Mount.LEFT], 'right': attached[Mount.RIGHT]}
    except Exception as ex:  # pylint: disable=broad-except
        return {'status': CommandStatus.Failed, 'message': str(ex)}


@app.get('/instruments/')
def get_instruments():
    return list(map(lambda lw: {'name': lw[1].name, 'location': lw[0]}, MGR.instruments.items()))


@app.get('/labware')
def get_labware():
    return list(map(lambda lw: {'name': lw[1].name, 'location': lw[0]}, MGR.ctx.loaded_labwares.items()))


@app.post('/commands')
def execute(req: Dict):
    return list(map(MGR.execute, req['commands']))
