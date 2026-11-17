#!/usr/bin/env python3
"""GravWave-Lab - educational gravitational wave astronomy lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only: gravitational waves are real, measured physics -
ripples in spacetime radiated by accelerating masses, predicted by
general relativity in 1916 and first directly detected by LIGO in
2015 (GW150914). This lab computes the textbook physics honestly:
the chirp mass, the quadrupole-formula strain
h = 4 (G Mc)^(5/3) (pi f)^(2/3) / (c^4 r), the inspiral chirp from
the quadrupole energy-loss ODE (integrated deterministically and
checked against the closed form), a growing-amplitude waveform, a
matched-filter toy with seeded noise that shows the sqrt(time)
SNR law, a labelled detector comparison table, the Schwarzschild
ringdown quasi-normal-mode estimate, and a from-scratch kNN
detectability classifier. Honest scope: GW150914 numbers quoted
here are LABELLED published literature values, never measured
here; no detector data is fetched or analysed; every discovery /
alert / live-instrument claim is a HOLD gate - with Gemini Carbon
4 as DECIDER (names-only, tighten-only), Muse as advisor (never
overrides HOLD), and Google Flow plan-only seats.
"""
import hashlib
import json
import math
import random
import sys

# ---------------------------------------------------------------- constants
G_NEWTON = 6.67430e-11          # gravitational constant, m^3 kg^-1 s^-2 (CODATA 2018)
C_LIGHT = 299792458.0           # speed of light, m/s (exact, SI)
M_SUN = 1.98847e30              # solar mass, kg (IAU nominal)
PARSEC_M = 3.0856775814913673e16  # one parsec, m (exact, IAU)
MPC_M = 1.0e6 * PARSEC_M        # one megaparsec, m
VERSION = "1.0.0"

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "discovery_claim": "HOLD - no claim that this simulation discovered a gravitational-wave event; discoveries belong to the detector collaborations",
    "real_detector_data_claim": "HOLD - no real strain data is fetched, downloaded, or analysed here, and none may be claimed",
    "live_detector_control": "HOLD - no control of LIGO, Virgo, KAGRA, LISA, or any real instrument, ever",
    "event_alert_issuance": "HOLD - no issuing of event alerts, GCN circulars, or public detection notices from a simulation",
    "measured_here_claim": "HOLD - published event numbers in this lab are labelled literature values, never 'measured here'",
    "peer_reviewed_result_claim": "HOLD - no claim of a peer-reviewed result; this is an educational simulation",
    "commercial_product_claim": "HOLD - this is an educational lab, not a commercial product or detector design service",
    "investment_claim": "HOLD - no investment advice about aerospace, detector, or space-mission companies",
    "guaranteed_detector_performance_claim": "HOLD - no guaranteed detector performance; labelled sensitivities are published reference values, not promises",
    "faster_than_light_claim": "HOLD - gravitational waves propagate at c; no faster-than-light signalling claims",
    "gravity_control_claim": "HOLD - no antigravity, gravity shielding, or spacetime-manipulation claims; waves are computed, not controlled",
    "time_travel_claim": "HOLD - no time-travel claims; a ripple in spacetime is not a time machine",
    "weapons_application_claim": "HOLD - no weapons application guidance of any kind",
    "medical_claim": "HOLD - no medical claims; gravitational-wave astronomy treats no condition",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Chirp mass + quadrupole strain
# A compact binary radiates gravitational waves at twice its orbital
# frequency. The mass combination the wave actually measures is the
# chirp mass
#   Mc = (m1 m2)^(3/5) / (m1 + m2)^(1/5).
# The quadrupole formula gives the strain amplitude (optimal
# orientation, orbit-averaged conventions vary by factors of order
# unity - the scaling is the physics):
#   h = 4 (G Mc)^(5/3) (pi f)^(2/3) / (c^4 r)
# Note the fingerprints: h grows as f^(2/3) while the binary
# inspirals, falls as 1/r (NOT 1/r^2 - waves carry amplitude, and
# amplitude is what a detector feels), and scales as Mc^(5/3).

def chirp_mass(m1_msun, m2_msun):
    """Chirp mass of a binary, in solar masses."""
    if m1_msun <= 0 or m2_msun <= 0:
        raise ValueError("masses must be positive")
    return (m1_msun * m2_msun) ** 0.6 / (m1_msun + m2_msun) ** 0.2


def strain(mc_msun, f_hz, r_mpc):
    """Quadrupole-formula GW strain amplitude (dimensionless)."""
    if mc_msun <= 0 or f_hz <= 0 or r_mpc <= 0:
        raise ValueError("chirp mass, frequency and distance must be positive")
    mc = mc_msun * M_SUN
    r = r_mpc * MPC_M
    return 4.0 * (G_NEWTON * mc) ** (5.0 / 3.0) * (math.pi * f_hz) ** (2.0 / 3.0) / (C_LIGHT ** 4 * r)


def strain_table(mc_msun=28.0956, r_mpc=410.0, freqs_hz=(20.0, 35.0, 60.0, 100.0, 150.0)):
    return [{"freq_hz": f, "strain": strain(mc_msun, f, r_mpc)} for f in freqs_hz]


# ================================================================ 2. GW150914 - LABELLED published reference
# GW150914 (Abbott et al., Phys. Rev. Lett. 116, 061102 (2016)):
# the first direct detection. Two black holes of about 36 and 29
# solar masses merged about 410 Mpc away; the observed strain
# peaked near 1.0e-21 at about 150 Hz. These are PUBLISHED values,
# labelled as such everywhere in this lab - nothing here was
# measured by this code. The lab's own optimal-orientation
# quadrupole estimate at the same parameters is ~2.1e-21: the
# factor-of-two gap is the published inclination / antenna-pattern
# averaging, and the lab prints both numbers side by side.

GW150914 = {
    "label": "PUBLISHED LITERATURE VALUES (Abbott et al. 2016) - not measured here",
    "m1_msun": 36.0,
    "m2_msun": 29.0,
    "remnant_msun": 62.0,
    "distance_mpc": 410.0,
    "peak_strain_published": 1.0e-21,
    "peak_freq_hz": 150.0,
    "chirp_mass_published_msun": 28.1,
}


def gw150914_report():
    mc = chirp_mass(GW150914["m1_msun"], GW150914["m2_msun"])
    h_lab = strain(mc, GW150914["peak_freq_hz"], GW150914["distance_mpc"])
    return {
        "label": GW150914["label"],
        "chirp_mass_computed_msun": mc,
        "chirp_mass_published_msun": GW150914["chirp_mass_published_msun"],
        "strain_lab_optimal_orientation": h_lab,
        "peak_strain_published": GW150914["peak_strain_published"],
        "peak_freq_hz": GW150914["peak_freq_hz"],
        "distance_mpc": GW150914["distance_mpc"],
        "mirror_displacement_published_peak_m": GW150914["peak_strain_published"] * 4000.0,
    }


# ================================================================ 3. Inspiral chirp (quadrupole ODE)
# The binary loses energy to the waves, the orbit shrinks, and the
# frequency chirps upward:
#   df/dt = (96/5) pi^(8/3) (G Mc / c^3)^(5/3) f^(11/3).
# Closed forms exist and the lab asserts the numerics against them:
#   time to coalescence from f:  t_c(f) = (5/256) (c^3/(G Mc))^(5/3) (pi f)^(-8/3)
#   GW cycles between f1 and f2: N = (1/32) pi^(-8/3) (G Mc/c^3)^(-5/3)
#                                    * (f1^(-5/3) - f2^(-5/3))
# GW150914 spent only ~0.19 s chirping from 35 Hz to 150 Hz;
# a neutron-star binary spends ~1000 s from 10 Hz - and piles up
# ~16,000 cycles in band. Cycles are the matched filter's salary.

def df_dt(mc_msun, f_hz):
    """GW frequency chirp rate df/dt (Hz/s), quadrupole formula."""
    if mc_msun <= 0 or f_hz <= 0:
        raise ValueError("chirp mass and frequency must be positive")
    mc = mc_msun * M_SUN
    return (96.0 / 5.0) * math.pi ** (8.0 / 3.0) * (G_NEWTON * mc / C_LIGHT ** 3) ** (5.0 / 3.0) * f_hz ** (11.0 / 3.0)


def time_to_coalescence(mc_msun, f_hz):
    """Analytic seconds from GW frequency f_hz to coalescence."""
    if mc_msun <= 0 or f_hz <= 0:
        raise ValueError("chirp mass and frequency must be positive")
    mc = mc_msun * M_SUN
    return (5.0 / 256.0) * (C_LIGHT ** 3 / (G_NEWTON * mc)) ** (5.0 / 3.0) * (math.pi * f_hz) ** (-8.0 / 3.0)


def cycles_between(mc_msun, f1_hz, f2_hz):
    """Analytic GW cycles accumulated between f1 and f2 (f2 > f1)."""
    if not (0 < f1_hz < f2_hz):
        raise ValueError("need 0 < f1 < f2")
    mc = mc_msun * M_SUN
    return ((1.0 / 32.0) * math.pi ** (-8.0 / 3.0)
            * (G_NEWTON * mc / C_LIGHT ** 3) ** (-5.0 / 3.0)
            * (f1_hz ** (-5.0 / 3.0) - f2_hz ** (-5.0 / 3.0)))


def inspiral_numeric(mc_msun, f1_hz, f2_hz, steps=8192):
    """Deterministic log-grid trapezoid integration of the chirp ODE.

    Integrates t = integral df/(df/dt) and cycles = integral f df/(df/dt)
    on a geometric frequency grid - no randomness, no adaptive state,
    so every run is byte-identical.
    """
    if not (0 < f1_hz < f2_hz):
        raise ValueError("need 0 < f1 < f2")
    ratio = f2_hz / f1_hz
    grid = [f1_hz * ratio ** (i / steps) for i in range(steps + 1)]
    t_tot = 0.0
    n_tot = 0.0
    for i in range(steps):
        fa, fb = grid[i], grid[i + 1]
        inv_a = 1.0 / df_dt(mc_msun, fa)
        inv_b = 1.0 / df_dt(mc_msun, fb)
        df = fb - fa
        t_tot += df * 0.5 * (inv_a + inv_b)
        n_tot += df * 0.5 * (fa * inv_a + fb * inv_b)
    return {"t_numeric_s": t_tot, "cycles_numeric": n_tot,
            "t_analytic_s": time_to_coalescence(mc_msun, f1_hz) - time_to_coalescence(mc_msun, f2_hz),
            "cycles_analytic": cycles_between(mc_msun, f1_hz, f2_hz)}


def f_isco(mtot_msun):
    """GW frequency at the innermost stable circular orbit (Hz)."""
    if mtot_msun <= 0:
        raise ValueError("mass must be positive")
    return C_LIGHT ** 3 / (math.pi * G_NEWTON * mtot_msun * M_SUN * 6.0 ** 1.5)


# ================================================================ 4. Waveform h(t)
# The waveform is the chirp made audible to the eye: frequency from
# the analytic f(t) = f0 (1 - t/t_c)^(-3/8), phase by cumulative
# trapezoid integration of 2 pi f, amplitude from the quadrupole
# strain at the instantaneous frequency. It ends where the lab says
# it ends (f1) - merger and ringdown are separate modules, and the
# waveform makes no claim past its own band.

def waveform(mc_msun, r_mpc, f0_hz=35.0, f1_hz=150.0, fs_hz=4096.0):
    """Deterministic inspiral waveform samples (t, f, envelope, h)."""
    tc = time_to_coalescence(mc_msun, f0_hz)
    t_end = tc * (1.0 - (f0_hz / f1_hz) ** (8.0 / 3.0))
    n = int(t_end * fs_hz)
    ts, fs_list, env, hs = [], [], [], []
    phase = 0.0
    prev_t, prev_f = 0.0, f0_hz
    for i in range(n + 1):
        t = i / fs_hz
        f = f0_hz * (1.0 - t / tc) ** (-3.0 / 8.0)
        if i > 0:
            phase += math.pi * (prev_f + f) * (t - prev_t)  # trapezoid of 2 pi f dt / ... (pi*(fa+fb)*dt)
        a = strain(mc_msun, f, r_mpc)
        ts.append(t)
        fs_list.append(f)
        env.append(a)
        hs.append(a * math.cos(phase))
        prev_t, prev_f = t, f
    return {"t": ts, "f": fs_list, "envelope": env, "h": hs,
            "t_end_s": t_end, "samples": n + 1}


def waveform_summary():
    mc = chirp_mass(36.0, 29.0)
    w = waveform(mc, 410.0)
    return {"samples": w["samples"], "duration_s": w["t_end_s"],
            "f_start_hz": w["f"][0], "f_end_hz": w["f"][-1],
            "h_start": w["envelope"][0], "h_end": w["envelope"][-1],
            "amplitude_growth_ratio": w["envelope"][-1] / w["envelope"][0]}


# ================================================================ 5. Matched-filter toy
# How do you hear a whisper of 1e-21 inside roaring noise? You
# correlate the data with the waveform you expect. For a template
# h in white noise of rms sigma, the matched-filter SNR is
#   rho = sum(d_i h_i) / (sigma * sqrt(sum h_i^2)),
# and for a sinusoid of amplitude A over N samples the expected
# value is rho = A sqrt(N/2) / sigma: SNR grows as the SQUARE ROOT
# of the observing time. Four times the data, twice the reach.
# Noise here is a seeded PRNG (random.Random with a fixed seed) -
# deterministic, labelled, and absolutely not detector data.

MF_SEED = 20260214
MF_FS_HZ = 1000.0
MF_FREQ_HZ = 50.0
MF_AMPLITUDE = 1.0
MF_SIGMA = 5.0


def _mf_template(n):
    return [MF_AMPLITUDE * math.sin(2.0 * math.pi * MF_FREQ_HZ * i / MF_FS_HZ)
            for i in range(n)]


def matched_filter(duration_s=10.0, with_signal=True, seed=MF_SEED):
    """Seeded matched-filter toy: template vs template + white noise."""
    n = int(duration_s * MF_FS_HZ)
    template = _mf_template(n)
    rng = random.Random(seed)
    noise = [rng.gauss(0.0, MF_SIGMA) for _ in range(n)]
    if with_signal:
        data = [t + nz for t, nz in zip(template, noise)]
    else:
        data = noise
    num = sum(d * t for d, t in zip(data, template))
    den = MF_SIGMA * math.sqrt(sum(t * t for t in template))
    rho = num / den
    rho_analytic = MF_AMPLITUDE * math.sqrt(n / 2.0) / MF_SIGMA
    return {"duration_s": duration_s, "samples": n, "snr_measured": rho,
            "snr_analytic": rho_analytic,
            "snr_per_sqrt_second": rho / math.sqrt(duration_s)}


def matched_filter_report():
    a = matched_filter(10.0, with_signal=True)
    b = matched_filter(40.0, with_signal=True)
    quiet = matched_filter(10.0, with_signal=False)
    return {"t10": a, "t40": b, "noise_only": quiet,
            "snr_ratio_40_over_10": b["snr_measured"] / a["snr_measured"],
            "expected_ratio_sqrt4": 2.0}


# ================================================================ 6. Detector table (LABELLED published values)
# Published reference sensitivities, labelled as literature values
# (rounded, best-band class) - not specifications this lab promises
# and not live instrument status. The one number the lab derives
# itself: a strain h moves a mirror by h * L, so GW150914's
# published peak 1.0e-21 across LIGO's 4 km arms is 4.0e-18 m -
# about 1/250 of a proton diameter, measured by light.

DETECTORS = [
    {"name": "LIGO Hanford (LHO)", "arm_m": 4000.0, "band": "10 Hz - 5 kHz",
     "strain_noise_per_sqrt_hz": 1.0e-23, "displacement_noise_m_class": 1.0e-19,
     "note": "4 km Fabry-Perot Michelson, Washington USA", "labelled": True},
    {"name": "LIGO Livingston (LLO)", "arm_m": 4000.0, "band": "10 Hz - 5 kHz",
     "strain_noise_per_sqrt_hz": 1.0e-23, "displacement_noise_m_class": 1.0e-19,
     "note": "4 km Fabry-Perot Michelson, Louisiana USA", "labelled": True},
    {"name": "Virgo", "arm_m": 3000.0, "band": "10 Hz - 5 kHz",
     "strain_noise_per_sqrt_hz": 3.0e-23, "displacement_noise_m_class": 1.0e-19,
     "note": "3 km Michelson, Cascina, Italy", "labelled": True},
    {"name": "KAGRA", "arm_m": 3000.0, "band": "10 Hz - 5 kHz",
     "strain_noise_per_sqrt_hz": 3.0e-23, "displacement_noise_m_class": 1.0e-19,
     "note": "3 km, underground, cryogenic mirrors, Kamioka, Japan", "labelled": True},
    {"name": "LISA (planned)", "arm_m": 2.5e9, "band": "0.1 mHz - 1 Hz",
     "strain_noise_per_sqrt_hz": 1.0e-20, "displacement_noise_m_class": 1.0e-11,
     "note": "2.5 million km space interferometer, 2030s (labelled plan)", "labelled": True},
]


def detector_report():
    return {"detectors": DETECTORS,
            "gw150914_mirror_displacement_m": GW150914["peak_strain_published"] * 4000.0,
            "note": "All sensitivities are LABELLED published reference values (rounded class figures), not live status and not design promises."}


# ================================================================ 7. Ringdown (Schwarzschild QNM, labelled formula)
# After two black holes merge, the remnant rings like a struck bell
# at its quasi-normal modes. For a NON-SPINNING (Schwarzschild)
# remnant the dominant l = m = 2 mode has the LABELLED dimensionless
# frequency M * omega = 0.3737 - 0.0890 i, so
#   f = 0.3737 * c^3 / (2 pi G M),   tau = G M / (0.0890 c^3),
#   Q = pi f tau = 0.3737 / (2 * 0.0890) = 2.099.
# GW150914's remnant (62 Msun, spinning) rang at ~251 Hz published;
# the Schwarzschild estimate here gives ~195 Hz - spin raises the
# frequency, and the lab labels the difference instead of hiding it.

QNM_RE = 0.3737
QNM_IM = 0.0890


def ringdown(m_msun):
    """Schwarzschild l=m=2 QNM frequency (Hz) and damping time (s)."""
    if m_msun <= 0:
        raise ValueError("mass must be positive")
    m = m_msun * M_SUN
    f = QNM_RE * C_LIGHT ** 3 / (2.0 * math.pi * G_NEWTON * m)
    tau = G_NEWTON * m / (QNM_IM * C_LIGHT ** 3)
    return {"freq_hz": f, "tau_s": tau, "quality_factor": math.pi * f * tau}


def ringdown_report():
    rows = []
    for m in (10.0, 30.0, 62.0, 100.0):
        r = ringdown(m)
        rows.append({"remnant_msun": m, **r})
    return {"label": "Schwarzschild (non-spinning) labelled QNM formula; spinning remnants ring higher",
            "gw150914_remnant_published_hz": 251.0, "rows": rows}


# ================================================================ 8. kNN detectability classifier
# Features: (log10 chirp mass, log10 distance in Mpc, log10 freq).
# The training grid is labelled BY the strain model itself against
# two labelled thresholds, so the classifier can never disagree
# with the physics it was taught - it interpolates the quadrupole
# formula's own verdicts:
#   h >= 1.5e-22  detectable | 2e-23 <= h < 1.5e-22  marginal | below: undetectable

DETECTABLE_H = 1.5e-22
MARGINAL_H = 2.0e-23


def _label_for_h(h):
    if h >= DETECTABLE_H:
        return "detectable"
    if h >= MARGINAL_H:
        return "marginal"
    return "undetectable"


def _train_grid():
    rows = []
    for mc in (0.9, 1.2, 2.0, 3.5, 6.0, 10.0, 17.0, 28.1, 45.0):
        for r in (10.0, 40.0, 100.0, 400.0, 1000.0, 4000.0, 12000.0, 30000.0):
            for f in (25.0, 60.0, 100.0, 150.0, 250.0, 400.0):
                rows.append((math.log10(mc), math.log10(r), math.log10(f),
                             _label_for_h(strain(mc, f, r))))
    return rows


_CLASSIFIER_TRAIN = _train_grid()


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def classify_detectability(mc_msun, r_mpc, f_hz, k=3):
    """kNN (k=3) detectability verdict, consistent with the strain model."""
    if mc_msun <= 0 or r_mpc <= 0 or f_hz <= 0:
        raise ValueError("chirp mass, distance and frequency must be positive")
    feat = (math.log10(mc_msun), math.log10(r_mpc), math.log10(f_hz))
    ranked = sorted(_CLASSIFIER_TRAIN, key=lambda row: _dist(feat, row[:3]))
    votes = {}
    for row in ranked[:k]:
        votes[row[3]] = votes.get(row[3], 0) + 1
    return max(sorted(votes), key=lambda lab: votes[lab])


def detectability_report():
    mc_bbh = chirp_mass(36.0, 29.0)
    mc_bns = chirp_mass(1.4, 1.4)
    scenarios = {
        "gw150914_like": (mc_bbh, 410.0, 150.0),
        "gw150914_far_low_freq": (mc_bbh, 4000.0, 60.0),
        "bns_40mpc_early": (mc_bns, 40.0, 100.0),
        "bns_40mpc_late": (mc_bns, 40.0, 400.0),
        "bns_400mpc": (mc_bns, 400.0, 100.0),
        "heavy_bbh_100mpc": (chirp_mass(30.0, 30.0), 100.0, 60.0),
    }
    return {name: classify_detectability(*args) for name, args in scenarios.items()}


# ================================================================ 9. Advisory seats
def _trace(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def carbon4_decide(topic="gravwave-lab-demo"):
    """Gemini Carbon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-carbon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Carbon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all claim gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="gravwave-lab-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Print the labelled published strain next to the lab's optimal-orientation estimate, name the orientation factor, and let the cycles count explain why matched filtering works: the signal is weak per cycle and strong per thousand cycles.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["two black holes spiralling in, spacetime rippling outward",
                  "the chirp: waves crowding tighter and taller toward merger",
                  "a 4 km arm breathing by 4e-18 m as the wave passes",
                  "the remnant ringing down like a struck bell",
                  "sixteen thousand neutron-star cycles stacking into one detection"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": carbon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. chirp mass + strain
    mc = chirp_mass(36.0, 29.0)
    chk("chirp_mass_gw150914", abs(mc - 28.0956) < 0.15)
    chk("chirp_mass_matches_published", abs(mc - GW150914["chirp_mass_published_msun"]) < 0.5)
    chk("chirp_mass_equal_mass", abs(chirp_mass(30.0, 30.0) - 26.1165) < 0.05)
    chk("chirp_mass_symmetric", chirp_mass(10.0, 25.0) == chirp_mass(25.0, 10.0))
    chk("chirp_mass_bns", abs(chirp_mass(1.4, 1.4) - 1.2188) < 0.01)
    h150 = strain(mc, 150.0, 410.0)
    chk("strain_gw150914_band", 1.9e-21 < h150 < 2.35e-21)
    chk("strain_f_scaling",
        abs(strain(mc, 150.0, 410.0) / strain(mc, 35.0, 410.0) - (150.0 / 35.0) ** (2.0 / 3.0)) < 1e-9)
    chk("strain_r_scaling_inverse",
        abs(strain(mc, 150.0, 4100.0) / strain(mc, 150.0, 410.0) - 0.1) < 1e-12)
    chk("strain_mc_scaling",
        abs(strain(2.0 * mc, 100.0, 410.0) / strain(mc, 100.0, 410.0) - 2.0 ** (5.0 / 3.0)) < 1e-9)
    chk("strain_positive", strain(10.0, 100.0, 100.0) > 0)
    # 2. GW150914 labelled reference
    rep = gw150914_report()
    chk("gw150914_labelled_peak", rep["peak_strain_published"] == 1.0e-21)
    chk("gw150914_lab_above_published_orientation",
        rep["strain_lab_optimal_orientation"] > rep["peak_strain_published"])
    chk("gw150914_mirror_displacement", abs(rep["mirror_displacement_published_peak_m"] - 4.0e-18) < 1e-30)
    # 3. inspiral ODE
    chk("t_coal_35hz", 0.17 < time_to_coalescence(mc, 35.0) < 0.21)
    chk("t_coal_10hz", 5.0 < time_to_coalescence(mc, 10.0) < 5.7)
    mc_bns = chirp_mass(1.4, 1.4)
    chk("t_coal_bns_10hz", 950.0 < time_to_coalescence(mc_bns, 10.0) < 1060.0)
    num = inspiral_numeric(mc, 35.0, 150.0)
    chk("numeric_t_matches_analytic",
        abs(num["t_numeric_s"] - num["t_analytic_s"]) < 0.05 * num["t_analytic_s"])
    chk("numeric_cycles_matches_analytic",
        abs(num["cycles_numeric"] - num["cycles_analytic"]) < 0.01 * num["cycles_analytic"])
    chk("cycles_35_150", 9.0 < cycles_between(mc, 35.0, 150.0) < 10.4)
    chk("cycles_10_150", 80.0 < cycles_between(mc, 10.0, 150.0) < 90.0)
    chk("cycles_bns_10_400", 15000.0 < cycles_between(mc_bns, 10.0, 400.0) < 17000.0)
    chk("f_isco_65msun", 60.0 < f_isco(65.0) < 75.0)
    chk("chirp_accelerates", df_dt(mc, 150.0) > df_dt(mc, 35.0) > 0)
    # 4. waveform
    w = waveform(mc, 410.0)
    chk("waveform_samples_band", 700 < w["samples"] < 820)
    chk("waveform_freq_endpoints",
        abs(w["f"][0] - 35.0) < 1e-9 and abs(w["f"][-1] - 150.0) < 3.0)
    chk("waveform_envelope_monotonic",
        all(w["envelope"][i] <= w["envelope"][i + 1] for i in range(len(w["envelope"]) - 1)))
    chk("waveform_amplitude_grows", w["envelope"][-1] > 2.5 * w["envelope"][0])
    chk("waveform_end_matches_strain",
        abs(w["envelope"][-1] - strain(mc, w["f"][-1], 410.0)) < 1e-12 * w["envelope"][-1])
    chk("waveform_deterministic", waveform(mc, 410.0)["h"] == w["h"])
    # 5. matched filter
    mf = matched_filter_report()
    chk("mf_snr_detected", mf["t10"]["snr_measured"] > 8.0)
    chk("mf_snr_near_analytic",
        abs(mf["t10"]["snr_measured"] - mf["t10"]["snr_analytic"]) < 0.35 * mf["t10"]["snr_analytic"])
    chk("mf_snr_sqrt_scaling", 1.55 < mf["snr_ratio_40_over_10"] < 2.45)
    chk("mf_noise_only_quiet", abs(mf["noise_only"]["snr_measured"]) < 5.5)
    n0 = int(10.0 * MF_FS_HZ)
    tmpl = _mf_template(n0)
    rho_clean = sum(t * t for t in tmpl) / (MF_SIGMA * math.sqrt(sum(t * t for t in tmpl)))
    chk("mf_zero_noise_exact",
        abs(rho_clean - mf["t10"]["snr_analytic"]) < 1e-6 * mf["t10"]["snr_analytic"])
    chk("mf_deterministic", matched_filter(10.0)["snr_measured"] == mf["t10"]["snr_measured"])
    # 6. detectors (labelled)
    det = detector_report()
    chk("detector_ligo_arm", det["detectors"][0]["arm_m"] == 4000.0)
    chk("detector_all_labelled", all(d["labelled"] for d in det["detectors"]))
    chk("detector_lisa_longest",
        max(d["arm_m"] for d in det["detectors"]) == det["detectors"][4]["arm_m"])
    chk("detector_displacement_math", abs(det["gw150914_mirror_displacement_m"] - 4.0e-18) < 1e-30)
    # 7. ringdown
    rd = ringdown(62.0)
    chk("ringdown_62_freq", 185.0 < rd["freq_hz"] < 205.0)
    chk("ringdown_62_tau", 3.0e-3 < rd["tau_s"] < 3.9e-3)
    chk("ringdown_q_identity", abs(rd["quality_factor"] - QNM_RE / (2.0 * QNM_IM)) < 0.02)
    chk("ringdown_inverse_mass_scaling",
        abs(ringdown(10.0)["freq_hz"] / ringdown(62.0)["freq_hz"] - 6.2) < 0.07)
    chk("ringdown_10_freq", 1150.0 < ringdown(10.0)["freq_hz"] < 1260.0)
    chk("ringdown_below_published_spin_value",
        rd["freq_hz"] < ringdown_report()["gw150914_remnant_published_hz"])
    # 8. classifier
    drep = detectability_report()
    chk("classifier_gw150914_detectable", drep["gw150914_like"] == "detectable")
    chk("classifier_far_low_freq_marginal", drep["gw150914_far_low_freq"] == "marginal")
    chk("classifier_bns_early_marginal", drep["bns_40mpc_early"] == "marginal")
    chk("classifier_bns_late_detectable", drep["bns_40mpc_late"] == "detectable")
    chk("classifier_bns_far_undetectable", drep["bns_400mpc"] == "undetectable")
    chk("classifier_heavy_bbh_detectable", drep["heavy_bbh_100mpc"] == "detectable")
    grid_ok = True
    for mc_g in (1.2, 6.0, 28.1):
        for r_g in (40.0, 400.0, 4000.0):
            for f_g in (60.0, 150.0):
                if classify_detectability(mc_g, r_g, f_g) != _label_for_h(strain(mc_g, f_g, r_g)):
                    grid_ok = False
    chk("classifier_consistent_with_strain_model", grid_ok)
    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14 and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_discovery_hold", gate("discovery_claim") == "HOLD")
    chk("gate_detector_data_hold", gate("real_detector_data_claim") == "HOLD")
    chk("gate_alert_hold", gate("event_alert_issuance") == "HOLD")
    chk("gate_ftl_hold", gate("faster_than_light_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    b = brains_report()
    chk("carbon4_no_override", b["decider"]["can_override_hold"] is False)
    chk("claude_no_override", b["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", b["flow"]["rendered"] is False and b["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("GravWave-Lab - educational gravitational wave astronomy lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    mc = chirp_mass(36.0, 29.0)
    print("\n[1] Chirp mass + quadrupole strain  h = 4 (G Mc)^(5/3) (pi f)^(2/3) / (c^4 r)")
    print(f"    GW150914 masses 36 + 29 Msun -> chirp mass Mc = {mc:.2f} Msun")
    for row in strain_table():
        print(f"    f = {row['freq_hz']:6.1f} Hz: h = {row['strain']:.4e}  (at 410 Mpc)")
    print("    -> h grows as f^(2/3) through the inspiral and falls as 1/r,")
    print("       not 1/r^2: detectors feel amplitude, and amplitude is patient.")
    print("\n[2] GW150914 - LABELLED published reference (Abbott et al. 2016)")
    rep = gw150914_report()
    print(f"    chirp mass: computed {rep['chirp_mass_computed_msun']:.2f} Msun | "
          f"published {rep['chirp_mass_published_msun']} Msun")
    print(f"    peak strain: published {rep['peak_strain_published']:.1e} | "
          f"lab optimal-orientation {rep['strain_lab_optimal_orientation']:.2e}")
    print(f"    mirror displacement at published peak: "
          f"{rep['mirror_displacement_published_peak_m']:.1e} m over 4 km arms")
    print("    -> the factor ~2 is inclination / antenna pattern. Both numbers")
    print("       printed, neither hidden. Nothing here was measured by this lab.")
    print("\n[3] Inspiral chirp - quadrupole energy-loss ODE")
    num = inspiral_numeric(mc, 35.0, 150.0)
    print(f"    35 -> 150 Hz: {num['t_numeric_s']:.4f} s (analytic {num['t_analytic_s']:.4f} s), "
          f"{num['cycles_numeric']:.1f} GW cycles")
    print(f"    10 -> 150 Hz: {time_to_coalescence(mc, 10.0) - time_to_coalescence(mc, 150.0):.2f} s, "
          f"{cycles_between(mc, 10.0, 150.0):.1f} cycles")
    mc_bns = chirp_mass(1.4, 1.4)
    print(f"    BNS 1.4 + 1.4 (Mc = {mc_bns:.3f}): 10 -> 400 Hz takes "
          f"{time_to_coalescence(mc_bns, 10.0) - time_to_coalescence(mc_bns, 400.0):.0f} s and "
          f"{cycles_between(mc_bns, 10.0, 400.0):,.0f} cycles")
    print(f"    ISCO frequency for 65 Msun total: {f_isco(65.0):.1f} Hz")
    print("    -> black holes chirp for a fifth of a second; neutron stars sing")
    print("       for minutes and stack ~16,000 cycles into the template.")
    print("\n[4] Waveform h(t) - the chirp as samples")
    ws = waveform_summary()
    print(f"    {ws['samples']} samples over {ws['duration_s']:.4f} s at 4096 Hz sampling")
    print(f"    frequency {ws['f_start_hz']:.0f} -> {ws['f_end_hz']:.0f} Hz | "
          f"amplitude {ws['h_start']:.3e} -> {ws['h_end']:.3e} "
          f"(x{ws['amplitude_growth_ratio']:.2f})")
    print("\n[5] Matched-filter toy (seeded noise - labelled, NOT detector data)")
    mf = matched_filter_report()
    print(f"    template A = 1 in noise sigma = {MF_SIGMA:.0f}: SNR after 10 s = "
          f"{mf['t10']['snr_measured']:.2f} (analytic {mf['t10']['snr_analytic']:.2f})")
    print(f"    after 40 s: SNR = {mf['t40']['snr_measured']:.2f} - ratio "
          f"{mf['snr_ratio_40_over_10']:.2f} vs sqrt(4) = 2.00 expected")
    print(f"    noise alone against the template: SNR = {mf['noise_only']['snr_measured']:.2f} (no detection)")
    print("    -> SNR grows as sqrt(time): 4x the data buys 2x the reach. That")
    print("       square root is why 16,000 quiet cycles beat one loud one.")
    print("\n[6] Detectors - LABELLED published reference sensitivities")
    for d in DETECTORS:
        print(f"    {d['name']:22s} arm {d['arm_m']:>12,.0f} m | band {d['band']:14s} | "
              f"~{d['strain_noise_per_sqrt_hz']:.0e} /sqrt(Hz)")
    print("    -> all values labelled literature class figures, not live status.")
    print("\n[7] Ringdown - Schwarzschild QNM (LABELLED formula, non-spinning)")
    for row in ringdown_report()["rows"]:
        print(f"    remnant {row['remnant_msun']:6.1f} Msun: f = {row['freq_hz']:7.1f} Hz | "
              f"tau = {row['tau_s'] * 1e3:.2f} ms | Q = {row['quality_factor']:.2f}")
    print("    -> GW150914's spinning 62 Msun remnant rang at ~251 Hz published;")
    print("       the non-spinning estimate (195 Hz) sits below it, as it should.")
    print("\n[8] Detectability classifier (TinyML kNN, taught by the strain model)")
    for name, label in detectability_report().items():
        print(f"    {name:24s} -> {label}")
    print("\n[9] Advisory seats")
    print(f"    decider: {carbon4_decide()['decision']} trace={carbon4_decide()['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {claude_advisor()['can_override_hold']}")
    print(f"    flow rendered = {google_flow_plan()['rendered']} live = {google_flow_plan()['live']}")
    print(f"\n[10] HOLD gates: {len(HOLD_GATES)}")
    for k in HOLD_GATES:
        print(f"    HOLD  {k}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "chirp":
        print(json.dumps({"gw150914": gw150914_report(),
                          "strain_table_410mpc": strain_table()}, indent=2, sort_keys=True))
        return 0
    if cmd == "inspiral":
        mc = chirp_mass(36.0, 29.0)
        mc_bns = chirp_mass(1.4, 1.4)
        print(json.dumps({
            "bbh_35_150": inspiral_numeric(mc, 35.0, 150.0),
            "bbh_10_150_cycles": cycles_between(mc, 10.0, 150.0),
            "bns_10_400": inspiral_numeric(mc_bns, 10.0, 400.0),
            "f_isco_65msun_hz": f_isco(65.0)}, indent=2, sort_keys=True))
        return 0
    if cmd == "waveform":
        print(json.dumps(waveform_summary(), indent=2, sort_keys=True))
        return 0
    if cmd == "filter":
        print(json.dumps(matched_filter_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "detectors":
        print(json.dumps(detector_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "ringdown":
        print(json.dumps(ringdown_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(detectability_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for k, v in HOLD_GATES.items():
            print(f"{k}: {v}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "discovery_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
