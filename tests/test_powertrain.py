import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from carweights.normalize.powertrain import classify, normalize_drivetrain


def t(**kw):
    return classify(**kw)


def test_bev_from_battery_only():
    r = t(fuel="Electric", name="ID.4 Pro", battery_kwh=77.0)
    assert r.powertrain_type == "BEV" and r.powertrain_subtype == "BEV"


def test_phev_from_battery_and_engine():
    r = t(fuel="Plug-in Hybrid", name="RAV4 PHEV", battery_kwh=18.1, engine_displacement_cc=2487)
    assert r.powertrain_type == "PHEV"


def test_phev_keyword_beats_hybrid():
    r = t(fuel="plug-in hybrid", name="Kuga PHEV")
    assert r.powertrain_type == "PHEV"


def test_nissan_epower_is_ice():
    # series hybrid -> combustion bucket, NOT BEV
    r = t(fuel="Hybrid", name="Qashqai e-Power")
    assert r.powertrain_type == "ICE" and r.powertrain_subtype == "HEV"


def test_full_hybrid_is_ice():
    r = t(fuel="Hybrid", name="Corolla 1.8 Hybrid")
    assert r.powertrain_type == "ICE" and r.powertrain_subtype == "HEV"


def test_mild_hybrid_is_ice():
    r = t(fuel="Petrol MHEV", name="Vitara 1.4 48V")
    assert r.powertrain_type == "ICE" and r.powertrain_subtype == "MHEV"


def test_diesel_and_petrol():
    assert t(fuel="Diesel", name="Octavia 2.0 TDI").powertrain_subtype == "diesel"
    assert t(fuel="Petrol", name="Golf 1.5 TSI").powertrain_subtype == "petrol"


def test_etron_is_bev():
    r = t(name="Audi Q4 e-tron", battery_kwh=82.0)
    assert r.powertrain_type == "BEV"


def test_drivetrain():
    assert normalize_drivetrain("quattro") == "4WD"
    assert normalize_drivetrain("xDrive") == "4WD"
    assert normalize_drivetrain("FWD") == "2WD"
    assert normalize_drivetrain(None) is None
