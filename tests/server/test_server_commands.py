""" Command Parsing Tests """
from json import loads
from server.server import LoadLabwareDef, PartialTransfer, MixSettings, ResourceRef, execute


def test_load_labware():
    with open('tests/server/biorad_96_wellplate_200ul_pcr.json') as command_file:
        commands = loads(command_file.read())
    labware = LoadLabwareDef.from_dict(commands["commands"][0]['command_input'][0])
    assert labware.location == '10'
    assert labware.labware_def['brand']['brandId'] == ['biorad_96_wellplate_200ul_pcr']
    assert labware.labware_def['ordering'][0][-1] == 'H1'
    assert labware.labware_def['wells']['C4']['depth'] == 10.8
    assert labware.labware_def['wells']['C4']['x'] == 41.28


def test_partial_transfer():
    with open('tests/server/partial_transfer_aspirate_commad.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    partial_transfer = PartialTransfer.from_dict(commands["commands"][0]['command_input'])
    assert partial_transfer.flowrate == 100
    assert partial_transfer.z_bottom_offset == 5
    assert partial_transfer.volume == 10.0
    assert partial_transfer.slot == 10
    assert partial_transfer.well_id == "A1"
    assert partial_transfer.post_aspirate_air_gap_ul is None
    assert partial_transfer.post_dispense_blowout_z_bottom_offset is None
    assert partial_transfer.ref == ResourceRef("foo", "left")


def test_partial_transfer_with_airgap_and_blowout():
    with open('tests/server/partial_transfer_aspirate_command_with_airgap_and_blowout.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    partial_transfer = PartialTransfer.from_dict(commands["commands"][0]['command_input'])
    assert partial_transfer.flowrate == 100
    assert partial_transfer.z_bottom_offset == 5
    assert partial_transfer.volume == 10.0
    assert partial_transfer.slot == 10
    assert partial_transfer.well_id == "A1"
    assert partial_transfer.post_aspirate_air_gap_ul == 10
    assert partial_transfer.post_dispense_blowout_z_bottom_offset == 20
    assert partial_transfer.ref == ResourceRef("foo", "left")


def test_mix_settings():
    with open('tests/server/mix_settings_command.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    mix_settings = MixSettings.from_dict(commands["commands"][0]['command_input'])
    assert mix_settings.aspirate_flowrate == 100
    assert mix_settings.dispense_flowrate == 200
    assert mix_settings.z_bottom_offset == 5
    assert mix_settings.volume == 10.0
    assert mix_settings.slot == 10
    assert mix_settings.well_id == "A1"
    assert mix_settings.cycles == 3
    assert mix_settings.post_mix_blowout_z_bottom_offset is None
    assert mix_settings.ref == ResourceRef("foo", "left")

    settings_dict = mix_settings.to_dict()
    assert settings_dict["aspirate_flowrate"] == 100
    assert settings_dict["dispense_flowrate"] == 200
    assert settings_dict["z_bottom_offset"] == 5
    assert settings_dict["volume"] == 10.0
    assert settings_dict["slot"] == 10
    assert settings_dict["well_id"] == "A1"
    assert settings_dict["cycles"] == 3
    assert settings_dict.get("post_mix_blowout_z_bottom_offset", None) is None
    assert settings_dict["head_ref"] == ResourceRef("foo", "left").to_dict()


def test_mix_settings_with_blowout():
    with open('tests/server/mix_settings_command_blowout.json') as command_file:
        state_str = command_file.read()
    commands = loads(state_str)
    mix_settings = MixSettings.from_dict(commands["commands"][0]['command_input'])
    assert mix_settings.aspirate_flowrate == 100
    assert mix_settings.dispense_flowrate == 200
    assert mix_settings.z_bottom_offset == 5
    assert mix_settings.volume == 10.0
    assert mix_settings.slot == 10
    assert mix_settings.well_id == "A1"
    assert mix_settings.cycles == 3
    assert mix_settings.post_mix_blowout_z_bottom_offset == 6
    assert mix_settings.ref == ResourceRef("foo", "left")

    settings_dict = mix_settings.to_dict()
    assert settings_dict["aspirate_flowrate"] == 100
    assert settings_dict["dispense_flowrate"] == 200
    assert settings_dict["z_bottom_offset"] == 5
    assert settings_dict["volume"] == 10.0
    assert settings_dict["slot"] == 10
    assert settings_dict["well_id"] == "A1"
    assert settings_dict["cycles"] == 3
    assert settings_dict["post_mix_blowout_z_bottom_offset"] == 6
    assert settings_dict["head_ref"] == ResourceRef("foo", "left").to_dict()


def test_execute_bad_command():
    result = execute({"commands": [{"command_id": "foo"}]})
    assert len(result) == 1
    assert result[0]["command_id"] == "foo"
    assert result[0]["status"] == "Failed"
    assert result[0]["message"] == 'command_id: foo not a handled command'
