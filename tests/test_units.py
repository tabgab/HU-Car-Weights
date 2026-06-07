import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from carweights.normalize.units import parse_weight, detect_basis


def test_single_values():
    assert parse_weight("1450") == (1450, None, None)
    assert parse_weight("1.450 kg") == (1450, None, None)
    assert parse_weight("1,450 kg") == (1450, None, None)
    assert parse_weight("kerb 1 620 kg") == (1620, None, None)


def test_range():
    assert parse_weight("1450 - 1620") == (1535, 1450, 1620)
    assert parse_weight("1450–1620 kg") == (1535, 1450, 1620)


def test_garbage_and_implausible():
    assert parse_weight("") == (None, None, None)
    assert parse_weight(None) == (None, None, None)
    assert parse_weight("n/a") == (None, None, None)
    assert parse_weight("50") == (None, None, None)       # below plausible floor
    assert parse_weight("9999") == (None, None, None)     # above plausible ceiling


def test_basis():
    assert detect_basis("Curb weight") == "curb"
    assert detect_basis("saját tömeg") == "curb"
    assert detect_basis("mass in running order") == "mass_in_running_order"
    assert detect_basis("Dry weight") == "dry"
    assert detect_basis("weight") == "unknown"
