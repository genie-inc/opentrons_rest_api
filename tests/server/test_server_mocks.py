""" Opentrons simulated/mock tests """  # pylint: disable=protected-access
from unittest.mock import MagicMock, patch
from opentrons.simulate import get_protocol_api as get_simulated_protocol_api
from opentrons.types import Point
from server.server import MGR, discover, execute, get_instruments, get_labware, reset, version, CommandId, ContextManager, MoveDestination, MoveOffset, ResourceRef, TouchTipSettings, WellRef, XYZVector


def test_load_instrument_none_loaded():
    context = ContextManager()
    context._context = MagicMock()
    ref = ResourceRef('foo', 'bar')
    context.home(ref)
    assert context._context.load_instrument.call_args[0][0] == "foo"
    assert context._context.load_instrument.call_args[0][1] == "bar"


def test_load_instrument_replace_head():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    assert len(context.instruments) == 0

    ref = ResourceRef('p20_single_gen2', 'right')
    instrument = context.load_instrument(ref)
    assert len(context.instruments) == 1
    assert context.instruments["right"] == instrument

    ref = ResourceRef('p300_single', 'right')
    instrument_new = context.load_instrument(ref)
    assert len(context.instruments) == 1
    assert context.instruments["right"] == instrument_new


def test_load_two_heads():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    assert len(context.instruments) == 0

    ref1 = ResourceRef('p20_single_gen2', 'right')
    instrument1 = context.load_instrument(ref1)

    ref2 = ResourceRef('p300_single', 'left')
    instrument2 = context.load_instrument(ref2)

    assert len(context.instruments) == 2
    assert context.instruments["right"] == instrument1
    assert context.instruments["left"] == instrument2

    context.home(ref1)
    context.home(ref2)


def test_reset():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    assert len(context.instruments) == 0

    ref1 = ResourceRef('p20_single_gen2', 'right')
    instrument1 = context.load_instrument(ref1)

    ref2 = ResourceRef('p300_single', 'left')
    instrument2 = context.load_instrument(ref2)

    assert len(context.instruments) == 2
    assert context.instruments["right"] == instrument1
    assert context.instruments["left"] == instrument2

    context.reset()

    assert len(context.instruments) == 0
    assert context._context is None


def test_home_all():
    context = ContextManager()
    context._context = MagicMock()
    context.execute({'command_id': CommandId.HomeAll})
    context._context.home.assert_called_once()


def test_force_eject():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    assert len(context.instruments) == 0

    ref1 = ResourceRef('p20_single_gen2', 'right')
    instrument1 = context.load_instrument(ref1)

    assert not instrument1._has_tip
    well_ref = WellRef(ref1, 12, 'A1')

    context.force_eject_tip(well_ref)
    assert not instrument1._has_tip


def test_move_to():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    assert len(context.instruments) == 0

    ref = ResourceRef('p20_single_gen2', 'right')
    instrument = context.load_instrument(ref)
    instrument.move_to = MagicMock()

    context.move_to(MoveDestination(ref=ref, slot=12, well_id='A1', offset=None, min_z=None))
    assert instrument.move_to.mock_calls[0][2]['location'].point == Point(x=347.84, y=351.5, z=82.0)
    assert instrument.move_to.mock_calls[0][2]['minimum_z_height'] is None

    offset = MoveOffset(offset=XYZVector(-1.2, 2.0, 5.5), ignore_tip=True)
    context.move_to(MoveDestination(ref=ref, slot=12, well_id='A1', offset=offset, min_z=150))
    assert instrument.move_to.mock_calls[1][2]['location'].point == Point(x=346.64, y=353.5, z=87.5)
    assert instrument.move_to.mock_calls[1][2]['minimum_z_height'] == 150


def test_affix_tip():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    ref = ResourceRef('p20_single_gen2', 'right')
    instrument = context.load_instrument(ref)
    instrument.pick_up_tip = MagicMock()
    context.affix_tip(WellRef(ref, 12, 'A1'))
    instrument.pick_up_tip.assert_called_once()


def test_eject_tip():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    ref = ResourceRef('p20_single_gen2', 'right')
    instrument = context.load_instrument(ref)
    instrument.drop_tip = MagicMock()
    context.eject_tip(WellRef(ref, 12, 'A1'))
    instrument.drop_tip.assert_called_once()


def test_tip_touch():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    ref = ResourceRef('p20_single_gen2', 'right')
    instrument = context.load_instrument(ref)
    instrument.touch_tip = MagicMock()
    context.touch_tip(TouchTipSettings(ref=ref, slot=12, well_id='A1', offset_from_top=-1, radius=0.5, speed=20))
    instrument.touch_tip.assert_called_once()


def test_set_api_version():
    cleanup = MagicMock()
    context = ContextManager()
    context.api_version = '0.0.0'
    context._context = MagicMock()
    context._context.cleanup = cleanup
    with patch('server.server.get_protocol_api', return_value=MagicMock()):
        context.execute({'command_id': CommandId.SetApiVersion, 'command_input': {'api_version': '2.0'}})
    cleanup.assert_called_once()
    assert context.api_version == '2.0'
    assert context._context is not None


def test_mgr_version():
    reslt = version()
    assert 'version' in reslt
    assert 'protocol_api_version' in reslt


def test_mgr_reset():
    cleanup = MagicMock()
    MGR._context = MagicMock()
    MGR._context.cleanup = cleanup
    reset()
    cleanup.assert_called_once()
    assert MGR._context is None


def test_mgr_discover():
    MGR._context = MagicMock()
    result = discover()
    assert list(result.keys()) == ['left', 'right']
    MGR._context._core = None
    result = discover()
    assert result['status'] == 'Failed'
    assert "object has no attribute 'get_hardware'" in result['message']


def test_mgr_get_instruments():
    assert get_instruments() == []


def test_mgr_get_labware():
    assert get_labware() == []


def test_mgr_execute():
    assert execute({'commands': []}) == []
