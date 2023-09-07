""" Opentrons simulated/mock tests """  # pylint: disable=protected-access
from unittest.mock import MagicMock
from opentrons.simulate import get_protocol_api as get_simulated_protocol_api
from server.server import ResourceRef, ContextManager, WellRef


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


def test_force_eject():
    context = ContextManager()
    context._context = get_simulated_protocol_api('2.0')
    assert len(context.instruments) == 0

    ref1 = ResourceRef('p20_single_gen2', 'right')
    instrument1 = context.load_instrument(ref1)

    assert not instrument1._has_tip
    well_ref = WellRef(ref1, 12, 'A1')

    try:
        context.eject_tip(well_ref)
    except Exception as ex:  # pylint: disable=broad-except
        assert str(ex) == "Cannot perform DROPTIP without a tip attached"
    else:
        assert False

    # This will only pass if tip is actually set
    context.force_eject_tip(well_ref)

    assert not instrument1._has_tip
    try:
        context.eject_tip(well_ref)
    except Exception as ex:  # pylint: disable=broad-except
        assert str(ex) == "Cannot perform DROPTIP without a tip attached"
    else:
        assert False
