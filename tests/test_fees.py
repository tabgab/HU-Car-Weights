import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fees import classify, threshold_for


def test_threshold_is_uniform():
    # Single 2000 kg rule for every powertrain (and unknown ones).
    assert threshold_for("BEV") == 2000
    assert threshold_for("PHEV") == 2000
    assert threshold_for("ICE") == 2000
    assert threshold_for(None) == 2000


def test_representative_value_cases():
    assert classify("BEV", 2100) == "double"
    assert classify("BEV", 1950) == "ok"
    assert classify("PHEV", 2050) == "double"
    assert classify("PHEV", 1900) == "ok"      # was double under the old 1800 rule
    assert classify("ICE", 1850) == "ok"       # was double under the old 1800 rule
    assert classify("ICE", 2001) == "double"


def test_boundary_is_ok():
    # exactly at threshold = ok (strict >)
    assert classify("BEV", 2000) == "ok"
    assert classify("ICE", 2000) == "ok"
    assert classify("PHEV", 2000) == "ok"


def test_range_cases():
    assert classify("ICE", None, 1950, 2050) == "borderline"   # straddles 2000
    assert classify("BEV", None, 1950, 2050) == "borderline"
    assert classify("ICE", None, 2050, 2100) == "double"       # entirely above
    assert classify("ICE", None, 1600, 1750) == "ok"           # entirely below
    assert classify("ICE", None, 1750, 1850) == "ok"           # below 2000 now


def test_unknown():
    assert classify("ICE", None, None, None) == "unknown"
    assert classify("BEV", None) == "unknown"
