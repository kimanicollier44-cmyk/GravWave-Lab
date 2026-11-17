"""Tests for GravWave-Lab: every number checked against analytics."""
import math

import pytest

import main as m


# ---- chirp mass + quadrupole strain
def test_chirp_mass_gw150914():
    assert abs(m.chirp_mass(36.0, 29.0) - 28.0956) < 0.15


def test_chirp_mass_matches_published():
    assert abs(m.chirp_mass(36.0, 29.0) - 28.1) < 0.5


def test_chirp_mass_equal_mass():
    # Mc(m, m) = m * 2^(-1/5)
    assert abs(m.chirp_mass(30.0, 30.0) - 30.0 * 2.0 ** (-0.2)) < 1e-9


def test_chirp_mass_symmetric():
    assert m.chirp_mass(10.0, 25.0) == m.chirp_mass(25.0, 10.0)


def test_chirp_mass_bns():
    assert abs(m.chirp_mass(1.4, 1.4) - 1.2188) < 0.01


def test_chirp_mass_invalid():
    with pytest.raises(ValueError):
        m.chirp_mass(0.0, 10.0)


def test_strain_gw150914_band():
    h = m.strain(m.chirp_mass(36.0, 29.0), 150.0, 410.0)
    assert 1.9e-21 < h < 2.35e-21


def test_strain_f_scaling():
    mc = m.chirp_mass(36.0, 29.0)
    ratio = m.strain(mc, 150.0, 410.0) / m.strain(mc, 35.0, 410.0)
    assert abs(ratio - (150.0 / 35.0) ** (2.0 / 3.0)) < 1e-9


def test_strain_inverse_r_not_r_squared():
    mc = m.chirp_mass(36.0, 29.0)
    ratio = m.strain(mc, 150.0, 4100.0) / m.strain(mc, 150.0, 410.0)
    assert abs(ratio - 0.1) < 1e-12


def test_strain_mc_scaling():
    ratio = m.strain(20.0, 100.0, 410.0) / m.strain(10.0, 100.0, 410.0)
    assert abs(ratio - 2.0 ** (5.0 / 3.0)) < 1e-9


def test_strain_invalid():
    with pytest.raises(ValueError):
        m.strain(10.0, 0.0, 100.0)


# ---- GW150914 labelled reference
def test_gw150914_labelled_values():
    rep = m.gw150914_report()
    assert rep["peak_strain_published"] == 1.0e-21
    assert rep["chirp_mass_published_msun"] == 28.1
    assert "not measured here" in rep["label"]


def test_gw150914_lab_estimate_above_published():
    rep = m.gw150914_report()
    assert rep["strain_lab_optimal_orientation"] > rep["peak_strain_published"]


def test_mirror_displacement_math():
    rep = m.gw150914_report()
    assert abs(rep["mirror_displacement_published_peak_m"] - 4.0e-18) < 1e-30


# ---- inspiral chirp ODE
def test_t_coal_gw150914_35hz():
    assert 0.17 < m.time_to_coalescence(m.chirp_mass(36.0, 29.0), 35.0) < 0.21


def test_t_coal_gw150914_10hz():
    assert 5.0 < m.time_to_coalescence(m.chirp_mass(36.0, 29.0), 10.0) < 5.7


def test_t_coal_bns_10hz():
    assert 950.0 < m.time_to_coalescence(m.chirp_mass(1.4, 1.4), 10.0) < 1060.0


def test_numeric_matches_analytic():
    num = m.inspiral_numeric(m.chirp_mass(36.0, 29.0), 35.0, 150.0)
    assert abs(num["t_numeric_s"] - num["t_analytic_s"]) < 0.05 * num["t_analytic_s"]
    assert abs(num["cycles_numeric"] - num["cycles_analytic"]) < 0.01 * num["cycles_analytic"]


def test_cycles_bands():
    mc = m.chirp_mass(36.0, 29.0)
    assert 9.0 < m.cycles_between(mc, 35.0, 150.0) < 10.4
    assert 80.0 < m.cycles_between(mc, 10.0, 150.0) < 90.0
    assert 15000.0 < m.cycles_between(m.chirp_mass(1.4, 1.4), 10.0, 400.0) < 17000.0


def test_f_isco_65msun():
    assert 60.0 < m.f_isco(65.0) < 75.0


def test_chirp_accelerates():
    mc = m.chirp_mass(36.0, 29.0)
    assert m.df_dt(mc, 150.0) > m.df_dt(mc, 35.0) > 0


# ---- waveform
def test_waveform_shape():
    w = m.waveform(m.chirp_mass(36.0, 29.0), 410.0)
    assert 700 < w["samples"] < 820
    assert abs(w["f"][0] - 35.0) < 1e-9
    assert abs(w["f"][-1] - 150.0) < 3.0


def test_waveform_envelope_monotonic_and_grows():
    w = m.waveform(m.chirp_mass(36.0, 29.0), 410.0)
    env = w["envelope"]
    assert all(env[i] <= env[i + 1] for i in range(len(env) - 1))
    assert env[-1] > 2.5 * env[0]


def test_waveform_end_matches_strain_formula():
    mc = m.chirp_mass(36.0, 29.0)
    w = m.waveform(mc, 410.0)
    assert abs(w["envelope"][-1] - m.strain(mc, w["f"][-1], 410.0)) < 1e-12 * w["envelope"][-1]


def test_waveform_deterministic():
    mc = m.chirp_mass(36.0, 29.0)
    assert m.waveform(mc, 410.0)["h"] == m.waveform(mc, 410.0)["h"]


# ---- matched-filter toy
def test_matched_filter_detects():
    rep = m.matched_filter_report()
    assert rep["t10"]["snr_measured"] > 8.0


def test_matched_filter_near_analytic():
    rep = m.matched_filter_report()
    assert abs(rep["t10"]["snr_measured"] - rep["t10"]["snr_analytic"]) < 0.35 * rep["t10"]["snr_analytic"]


def test_matched_filter_sqrt_scaling():
    rep = m.matched_filter_report()
    assert 1.55 < rep["snr_ratio_40_over_10"] < 2.45


def test_matched_filter_noise_only_quiet():
    rep = m.matched_filter_report()
    assert abs(rep["noise_only"]["snr_measured"]) < 5.5


def test_matched_filter_zero_noise_exact():
    n = int(10.0 * m.MF_FS_HZ)
    tmpl = m._mf_template(n)
    rho = sum(t * t for t in tmpl) / (m.MF_SIGMA * math.sqrt(sum(t * t for t in tmpl)))
    analytic = m.MF_AMPLITUDE * math.sqrt(n / 2.0) / m.MF_SIGMA
    assert abs(rho - analytic) < 1e-6 * analytic


def test_matched_filter_deterministic():
    assert m.matched_filter(10.0)["snr_measured"] == m.matched_filter(10.0)["snr_measured"]


# ---- detectors (labelled)
def test_detector_table():
    det = m.detector_report()
    assert det["detectors"][0]["arm_m"] == 4000.0
    assert all(d["labelled"] for d in det["detectors"])
    assert det["detectors"][4]["arm_m"] == 2.5e9


# ---- ringdown
def test_ringdown_62():
    rd = m.ringdown(62.0)
    assert 185.0 < rd["freq_hz"] < 205.0
    assert 3.0e-3 < rd["tau_s"] < 3.9e-3


def test_ringdown_q_identity():
    rd = m.ringdown(62.0)
    assert abs(rd["quality_factor"] - m.QNM_RE / (2.0 * m.QNM_IM)) < 0.02


def test_ringdown_inverse_mass_scaling():
    ratio = m.ringdown(10.0)["freq_hz"] / m.ringdown(62.0)["freq_hz"]
    assert abs(ratio - 6.2) < 0.07


def test_ringdown_below_spinning_published():
    assert m.ringdown(62.0)["freq_hz"] < m.ringdown_report()["gw150914_remnant_published_hz"]


# ---- classifier
def test_classifier_scenarios():
    rep = m.detectability_report()
    assert rep["gw150914_like"] == "detectable"
    assert rep["gw150914_far_low_freq"] == "marginal"
    assert rep["bns_40mpc_early"] == "marginal"
    assert rep["bns_40mpc_late"] == "detectable"
    assert rep["bns_400mpc"] == "undetectable"
    assert rep["heavy_bbh_100mpc"] == "detectable"


def test_classifier_consistent_with_strain_model():
    for mc_g in (1.2, 6.0, 28.1):
        for r_g in (40.0, 400.0, 4000.0):
            for f_g in (60.0, 150.0):
                expect = m._label_for_h(m.strain(mc_g, f_g, r_g))
                assert m.classify_detectability(mc_g, r_g, f_g) == expect


# ---- gates + seats
def test_hold_gates_all_present():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_claim_gates_hold():
    for action in ("discovery_claim", "real_detector_data_claim",
                   "live_detector_control", "event_alert_issuance",
                   "measured_here_claim", "faster_than_light_claim",
                   "gravity_control_claim", "time_travel_claim"):
        assert m.gate(action) == "HOLD"


def test_sandbox_proceeds():
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    b = m.brains_report()
    assert b["decider"]["can_override_hold"] is False
    assert b["advisor"]["can_override_hold"] is False
    assert b["flow"]["rendered"] is False and b["flow"]["live"] == 0


def test_demo_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]


def test_demo_deterministic():
    import io
    import contextlib
    out1, out2 = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out1):
        m.demo()
    with contextlib.redirect_stdout(out2):
        m.demo()
    assert out1.getvalue() == out2.getvalue()
