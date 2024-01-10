""" Command Parsing Tests """
from json import loads
from server.server import LoadLabwareDef, MoveDestination, PartialTransfer, MixSettings, ResourceRef, BlowoutSettings, TouchTipSettings, execute


def test_load_labware():
    with open('tests/server/biorad_96_wellplate_200ul_pcr.json') as command_file:
        commands = loads(command_file.read())
    labware = LoadLabwareDef.from_dict(commands['commands'][0]['command_input'][0])
    assert labware.location == '10'
    assert labware.labware_def['brand']['brandId'] == ['biorad_96_wellplate_200ul_pcr']
    assert labware.labware_def['ordering'][0][-1] == 'H1'
    assert labware.labware_def['wells']['C4']['depth'] == 10.8
    assert labware.labware_def['wells']['C4']['x'] == 41.28

    labware2 = LoadLabwareDef.from_dict(labware.to_dict())
    assert labware2.location == labware.location
    assert labware2.labware_def['brand']['brandId'] == labware.labware_def['brand']['brandId']
    assert labware2.labware_def['ordering'][0][-1] == labware.labware_def['ordering'][0][-1]
    assert labware2.labware_def['wells']['C4']['depth'] == labware.labware_def['wells']['C4']['depth']
    assert labware2.labware_def['wells']['C4']['x'] == labware.labware_def['wells']['C4']['x']


def test_partial_transfer():
    with open('tests/server/partial_transfer_aspirate_commad.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    partial_transfer = PartialTransfer.from_dict(commands['commands'][0]['command_input'])
    assert partial_transfer.flowrate == 100
    assert partial_transfer.z_bottom_offset == 5
    assert partial_transfer.volume == 10.0
    assert partial_transfer.slot == 10
    assert partial_transfer.well_id == 'A1'
    assert partial_transfer.post_aspirate_air_gap_ul is None
    assert partial_transfer.post_dispense_blowout_z_bottom_offset is None
    assert partial_transfer.ref == ResourceRef('foo', 'left')

    partial_transfer2 = PartialTransfer.from_dict(partial_transfer.to_dict())
    assert partial_transfer2.flowrate == partial_transfer.flowrate
    assert partial_transfer2.z_bottom_offset == partial_transfer.z_bottom_offset
    assert partial_transfer2.volume == partial_transfer.volume
    assert partial_transfer2.slot == partial_transfer.slot
    assert partial_transfer2.well_id == partial_transfer.well_id
    assert partial_transfer2.post_aspirate_air_gap_ul is None
    assert partial_transfer2.post_dispense_blowout_z_bottom_offset is None
    assert partial_transfer2.ref == ResourceRef('foo', 'left')


def test_partial_transfer_with_airgap_and_blowout():
    with open('tests/server/partial_transfer_aspirate_command_with_airgap_and_blowout.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    partial_transfer = PartialTransfer.from_dict(commands['commands'][0]['command_input'])
    assert partial_transfer.flowrate == 100
    assert partial_transfer.z_bottom_offset == 5
    assert partial_transfer.volume == 10.0
    assert partial_transfer.slot == 10
    assert partial_transfer.well_id == 'A1'
    assert partial_transfer.post_aspirate_air_gap_ul == 10
    assert partial_transfer.post_dispense_blowout_z_bottom_offset == 20
    assert partial_transfer.ref == ResourceRef('foo', 'left')


def test_mix_settings():
    with open('tests/server/mix_settings_command.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    mix_settings = MixSettings.from_dict(commands['commands'][0]['command_input'])
    assert mix_settings.aspirate_flowrate == 100
    assert mix_settings.dispense_flowrate == 200
    assert mix_settings.z_bottom_offset == 5
    assert mix_settings.volume == 10.0
    assert mix_settings.slot == 10
    assert mix_settings.well_id == 'A1'
    assert mix_settings.cycles == 3
    assert mix_settings.post_mix_blowout_z_bottom_offset is None
    assert mix_settings.ref == ResourceRef('foo', 'left')

    settings_dict = mix_settings.to_dict()
    assert settings_dict['aspirate_flowrate'] == 100
    assert settings_dict['dispense_flowrate'] == 200
    assert settings_dict['z_bottom_offset'] == 5
    assert settings_dict['volume'] == 10.0
    assert settings_dict['slot'] == 10
    assert settings_dict['well_id'] == 'A1'
    assert settings_dict['cycles'] == 3
    assert settings_dict.get('post_mix_blowout_z_bottom_offset', None) is None
    assert settings_dict['head_ref'] == ResourceRef('foo', 'left').to_dict()


def test_mix_settings_with_blowout():
    with open('tests/server/mix_settings_command_blowout.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    mix_settings = MixSettings.from_dict(commands['commands'][0]['command_input'])
    assert mix_settings.aspirate_flowrate == 100
    assert mix_settings.dispense_flowrate == 200
    assert mix_settings.z_bottom_offset == 5
    assert mix_settings.volume == 10.0
    assert mix_settings.slot == 10
    assert mix_settings.well_id == 'A1'
    assert mix_settings.cycles == 3
    assert mix_settings.post_mix_blowout_z_bottom_offset == 6
    assert mix_settings.ref == ResourceRef('foo', 'left')

    settings_dict = mix_settings.to_dict()
    assert settings_dict['aspirate_flowrate'] == 100
    assert settings_dict['dispense_flowrate'] == 200
    assert settings_dict['z_bottom_offset'] == 5
    assert settings_dict['volume'] == 10.0
    assert settings_dict['slot'] == 10
    assert settings_dict['well_id'] == 'A1'
    assert settings_dict['cycles'] == 3
    assert settings_dict['post_mix_blowout_z_bottom_offset'] == 6
    assert settings_dict['head_ref'] == ResourceRef('foo', 'left').to_dict()


def test_execute_bad_command():
    result = execute({'commands': [{'command_id': 'foo'}]})
    assert len(result) == 1
    assert result[0]['command_id'] == 'foo'
    assert result[0]['status'] == 'Failed'
    assert result[0]['message'] == 'command_id: foo not a handled command'


def test_move_to_command():
    with open('tests/server/move_to_command.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    move = MoveDestination.from_dict(commands['commands'][0]['command_input'])
    assert move.slot == 12
    assert move.well_id == 'A1'
    assert move.ref == ResourceRef('foo', 'left')
    assert move.offset.offset.x == 0
    assert move.offset.offset.y == 1
    assert move.offset.offset.z == 2.2
    assert move.offset.ignore_tip
    assert move.min_z == 14.5

    move2 = MoveDestination.from_dict(move.to_dict())
    assert move2.slot == move.slot
    assert move2.well_id == move.well_id
    assert move2.ref == ResourceRef('foo', 'left')
    assert move2.offset.offset.x == move.offset.offset.x
    assert move2.offset.offset.y == move.offset.offset.y
    assert move2.offset.offset.z == move.offset.offset.z
    assert move2.offset.ignore_tip
    assert move2.min_z == move.min_z

    move.offset = None
    move.min_z = None
    move = MoveDestination.from_dict(move.to_dict())
    assert move.offset is None
    assert move.min_z is None


def test_blowout():
    with open('tests/server/blowout.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    blowout = BlowoutSettings.from_dict(commands['commands'][0]['command_input'])
    assert blowout.flowrate == 100
    assert blowout.z_bottom_offset == 5
    assert blowout.slot == 10
    assert blowout.well_id == 'A1'
    assert blowout.ref == ResourceRef('foo', 'left')

    blowout2 = BlowoutSettings.from_dict(blowout.to_dict())
    assert blowout2.flowrate == blowout.flowrate
    assert blowout2.z_bottom_offset == blowout.z_bottom_offset
    assert blowout2.slot == blowout.slot
    assert blowout2.well_id == blowout.well_id
    assert blowout2.ref == ResourceRef('foo', 'left')


def test_tip_touch():
    with open('tests/server/tip_touch.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    tip_touch = TouchTipSettings.from_dict(commands['commands'][0]['command_input'])
    assert tip_touch.offset_from_top == -1
    assert tip_touch.radius == 0.5
    assert tip_touch.speed == 50
    assert tip_touch.slot == 10
    assert tip_touch.well_id == 'A1'
    assert tip_touch.ref == ResourceRef('foo', 'left')
