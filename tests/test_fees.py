import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fees import classify, threshold_for


def test_threshold_selection():
    assert threshold_for("BEV") == 2000
    assert threshold_for("PHEV") == 1800
    assert threshold_for("ICE") == 1800


def test_representative_value_cases():
    assert classify("BEV", 2100) == "double"     # BEV over 2000
    assert classify("BEV", 1950) == "ok"
    assert classify("PHEV", 1900) == "double"     # PHEV uses 1800
    assert classify("PHEV", 1700) == "ok"
    assert classify("ICE", 1700) == "ok"
    assert classify("ICE", 1850) == "double"


def test_boundary_is_ok():
    assert classify("BEV", 2000) == "ok"          # exactly at threshold = ok (strict >)
    assert classify("ICE", 1800) == "ok"


def test_range_cases():
    assert classify("ICE", None, 1750, 1850) == "borderline"   # straddles 1800
    assert classify("BEV", None, 1950, 2050) == "borderline"   # straddles 2000
    assert classify("ICE", None, 1850, 1900) == "double"       # entirely above
    assert classify("ICE", None, 1600, 1750) == "ok"           # entirely below


def test_unknown():
    assert classify("ICE", None, None, None) == "unknown"
    assert classify("BEV", None) == "unknown"
