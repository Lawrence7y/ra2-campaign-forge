# -*- coding: utf-8 -*-
"""R-062 freeze mutation suite (round-2 calibration -> frozen literals).

PROVENANCE (R-061 freeze discipline reused):
  * expected red-sets below are TRANSCRIBED from the sealed calibration
    manifest out/_r062_freeze.json (round 2: 112 cases, killed=112 /
    survived=0 / exc=0 / uncovered=0 over 126 gate labels). This file NEVER
    derives expectations at runtime (ruling 4): a case passes only if BOTH
    execution paths' actual red-sets are EXACTLY equal to the literal.
  * every case runs twice: gate incremental `_splice` build (default path in
    R-061's G.build) AND forced FULL decode rebuild (monkeypatch inside this
    process only; the gate file is untouched) -- both must match the frozen
    set (ruling 5).
  * the suite refuses to run unless gate file + image hashes still equal the
    hashes sealed in the manifest (expectations staleness guard).
  * manifest sha256 1e4e0ba0b42c6fa3d1a20d88d6cdbd507814e5bca24d88f1d4360914881ab214
    gate     sha256 611ca4d4bd14ea60296cab31f7a6fa248e85f99b54bd97bc3b98af4bbcdd1dff
    image    sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
  * RTTI/.rdata mutations (Rt-*, Vp-*): .text-only splice can't see them, but
    the gate's own load() maps sections for the blob; the FULL path here
    rebuilds the entire decode AND reloads the mutated blob -> both paths
    cover .rdata (the walk over stream is identical; rb() reads the blob).

STATUS: same review pipeline as R-061 -- pending independent review.
G-79 tail: every counted gate label must appear in >=1 frozen expectation.

Run:  python re_atlas/tools/mutate_r062_gate.py   (minutes: 112 x (splice+full))
Calibration history: out/_calib_r062_mut1.py / _r062_mut_calib{1,2}.txt.
"""
import hashlib
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
GATE_PATH = os.path.join(HERE, "r062_upward_trace_contract.py")
IMAGE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
MANIFEST = r"D:\Project\ra2-campaign-forge\out\_r062_freeze.json"

FROZEN_GATE_SHA = "611ca4d4bd14ea60296cab31f7a6fa248e85f99b54bd97bc3b98af4bbcdd1dff"
FROZEN_IMAGE_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
FROZEN_MANIFEST_SHA = "1e4e0ba0b42c6fa3d1a20d88d6cdbd507814e5bca24d88f1d4360914881ab214"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if sha(GATE_PATH) != FROZEN_GATE_SHA:
    print("STALE: gate bytes != freeze-sealed gate (edit invalidates expectations)")
    sys.exit(3)
if sha(IMAGE) != FROZEN_IMAGE_SHA:
    print("STALE: image bytes != freeze-sealed gamemd.exe")
    sys.exit(3)
if not os.path.exists(MANIFEST):
    print("MISSING provenance manifest: " + MANIFEST)
    sys.exit(3)
if sha(MANIFEST) != FROZEN_MANIFEST_SHA:
    print("STALE: out/_r062_freeze.json changed after transcription")
    sys.exit(3)

# ---- frozen literals (mechanical transcription via out/_gen_r062_lits.py;
# ---- provenance out/_r062_freeze.json; never re-derived here) -------------
CASES = [
    ("Ch-46cd7b", {0x46cd7a: 0xce}, ["U-chain-46cd7b", "U-hist-529160"]),
    ("Ch-4acec7", {0x4aceb8: 0xce}, ["U-chain-4acec7", "U-hist-527cc0"]),
    ("Ch-4ad77a", {0x4ad75e: 0xce}, ["U-chain-4ad77a", "U-hist-527cc0"]),
    ("Ch-4f1d7b", {0x4f1d78: 0x29}, ["U-chain-4f1d7b"]),
    ("Ch-4f1fe1", {0x4f1fe0: 0xcc}, ["U-chain-4f1fe1", "U-hist-528c00"]),
    ("Ch-4f208e", {0x4f208d: 0xcf}, ["U-chain-4f208e", "U-hist-528c00"]),
    ("Ch-4f2ced", {0x4f2cec: 0xcf}, ["U-chain-4f2ced"]),
    ("Ch-4f2d5c", {0x4f2d5b: 0xcf}, ["U-chain-4f2d5c"]),
    ("Ch-4f2e30", {0x4f2e2f: 0xcf}, ["U-chain-4f2e30"]),
    ("Ch-4f3219", {0x4f3218: 0xcf}, ["U-chain-4f3219"]),
    ("Ch-4f32a4", {0x4f32a3: 0xcf}, ["U-chain-4f32a4"]),
    ("Ch-4f32e9", {0x4f32e8: 0xcf}, ["U-chain-4f32e9"]),
    ("Ch-4f332e", {0x4f332d: 0xcf}, ["U-chain-4f332e"]),
    ("Ch-4f337c", {0x4f337b: 0xcf}, ["U-chain-4f337c"]),
    ("Ch-4f33ca", {0x4f33c9: 0xcf}, ["U-chain-4f33ca"]),
    ("Ch-4f38f9", {0x4f38f8: 0xcf}, ["U-chain-4f38f9", "U-hist-528c00"]),
    ("Ch-4f39c1", {0x4f39c0: 0xcf}, ["U-chain-4f39c1", "U-hist-528c00"]),
    ("Ch-4f3bf3", {0x4f3bf2: 0xcf}, ["U-chain-4f3bf3"]),
    ("Ch-5cefc9", {0x5cefc8: 0x39}, ["U-chain-5cefc9"]),
    ("Ch-5cf10e", {0x5cf10d: 0x39}, ["U-chain-5cf10e"]),
    ("Ch-5cf162", {0x5cf161: 0x39}, ["U-chain-5cf162"]),
    ("Ch-5cf284", {0x5cf283: 0x39}, ["U-chain-5cf284"]),
    ("Ch-5cf2e0", {0x5cf2df: 0x39}, ["U-chain-5cf2e0"]),
    ("Ch-5cf42c", {0x5cf42b: 0x39}, ["U-chain-5cf42c"]),
    ("Ch-5cf4c7", {0x5cf4c6: 0x39}, ["U-chain-5cf4c7"]),
    ("Ch-5cf9f0", {0x5cf9ef: 0x51}, ["U-chain-5cf9f0"]),
    ("Ch-5cfa65", {0x5cfa5d: 0x45}, ["U-chain-5cfa65"]),
    ("Ch-5cfaf0", {0x5cfaee: 0x4d}, ["U-chain-5cfaf0"]),
    ("Ch-5cfb63", {0x5cfb5b: 0x45}, ["U-chain-5cfb63"]),
    ("Ch-5cfbef", {0x5cfbed: 0x4d}, ["U-chain-5cfbef"]),
    ("Ch-5cfcf4", {0x5cfcf3: 0x51}, ["U-chain-5cfcf4"]),
    ("Ch-5cfd69", {0x5cfd66: 0x49}, ["U-chain-5cfd69"]),
    ("Ch-5cfe50", {0x5cfe4d: 0x49}, ["U-chain-5cfe50"]),
    ("Ch-5cffb5", {0x5cffb4: 0x51}, ["U-chain-5cffb5"]),
    ("Ch-5d76a9", {0x5d76a8: 0x01}, ["U-chain-5d76a9"]),
    ("Ch-641b3c", {0x641b3b: 0xce}, ["U-chain-641b3c", "U-hist-527cc0"]),
    ("Ch-6874a9", {0x68748c: 0xcc}, ["U-chain-6874a9", "U-hist-527cc0"]),
    ("Ch-687516", {0x687515: 0xcc}, ["U-chain-687516", "U-hist-527cc0"]),
    ("Ch-68a754", {0x68a748: 0xce}, ["U-chain-68a754", "U-hist-52a760"]),
    ("Ch-68a772", {0x68a771: 0xce}, ["U-chain-68a772", "U-hist-52a760"]),
    ("Ch-68a790", {0x68a77e: 0xce}, ["U-chain-68a790", "U-hist-52a760"]),
    ("Ch-69a53a", {0x69a539: 0xce}, ["U-chain-69a53a"]),
    ("Ch-69a659", {0x69a658: 0xce}, ["U-chain-69a659"]),
    ("Ch-71241d", {0x712411: 0xcf}, ["U-chain-71241d", "U-hist-527920"]),
    ("Ch-720577", {0x720576: 0xcc}, ["U-chain-720577", "U-hist-529160"]),
    ("Ch-75d8b2", {0x75d8b1: 0xce}, ["U-chain-75d8b2", "U-hist-527920"]),
    ("Ch-768236", {0x768235: 0xcc}, ["U-chain-768236", "U-hist-528c00"]),
    ("Ch-768287", {0x768286: 0xcc}, ["U-chain-768287", "U-hist-528c00"]),
    ("Ch-7682dc", {0x7682db: 0xcc}, ["U-chain-7682dc", "U-hist-528c00"]),
    ("Ch-768343", {0x768342: 0xcc}, ["U-chain-768343", "U-hist-528c00"]),
    ("Ch-7684b2", {0x7684b1: 0xcc}, ["U-chain-7684b2", "U-hist-527f20"]),
    ("Ch-768511", {0x768510: 0xcc}, ["U-chain-768511", "U-hist-527f20"]),
    ("Ch-768570", {0x76856f: 0xcc}, ["U-chain-768570", "U-hist-527f20"]),
    ("Ch-7685cf", {0x7685ce: 0xcc}, ["U-chain-7685cf", "U-hist-527f20"]),
    ("Ch-768643", {0x768642: 0xcc}, ["U-chain-768643", "U-hist-528c00"]),
    ("Ch-768713", {0x768712: 0xcc}, ["U-chain-768713", "U-hist-528c00"]),
    ("Ch-7687a0", {0x76879f: 0xcc}, ["U-chain-7687a0", "U-hist-528c00"]),
    ("Ch-76881a", {0x768819: 0xcc}, ["U-chain-76881a", "U-hist-528c00"]),
    ("Ch-7688d8", {0x7688d7: 0xcc}, ["U-chain-7688d8", "U-hist-528c00"]),
    ("Ch-768955", {0x768954: 0xcc}, ["U-chain-768955", "U-hist-527f20"]),
    ("Ch-768a21", {0x768a20: 0xcc}, ["U-chain-768a21", "U-hist-528c00"]),
    ("Ch-768ae1", {0x768ae0: 0xcc}, ["U-chain-768ae1", "U-hist-528c00"]),
    ("Ch-768b84", {0x768b83: 0xcc}, ["U-chain-768b84", "U-hist-528c00"]),
    ("Ch-768bc9", {0x768bc8: 0xcc}, ["U-chain-768bc9", "U-hist-528c00"]),
    ("Ch-768c0f", {0x768c0e: 0xcc}, ["U-chain-768c0f", "U-hist-528c00"]),
    ("Ch-768c7e", {0x768c7d: 0xcc}, ["U-chain-768c7e", "U-hist-528c00"]),
    ("Ch-768cc3", {0x768cc2: 0xcc}, ["U-chain-768cc3", "U-hist-528c00"]),
    ("Ch-768dd9", {0x768dd8: 0xcc}, ["U-chain-768dd9", "U-hist-528c00"]),
    ("Ch-768f91", {0x768f8e: 0x01}, ["U-chain-768f91"]),
    ("Ch-76c555", {0x76c554: 0x39}, ["U-chain-76c555"]),
    ("Ch-76cae0", {0x76cadf: 0xce}, ["U-chain-76cae0", "U-hist-528c00"]),
    ("Ch-76cc4b", {0x76cc4a: 0xcc}, ["U-chain-76cc4b", "U-hist-528c00"]),
    ("Ch-76ccbb", {0x76ccba: 0xcc}, ["U-chain-76ccbb", "U-hist-528c00"]),
    ("Ch-76cd0d", {0x76cd0c: 0xcc}, ["U-chain-76cd0d", "U-hist-528c00"]),
    ("Ch-770655", {0x770654: 0xcc}, ["U-chain-770655", "U-hist-528c00"]),
    ("Ch-770774", {0x770773: 0xcc}, ["U-chain-770774", "U-hist-528c00"]),
    ("Ch-77089d", {0x77089c: 0x25}, ["U-chain-77089d"]),
    ("Ch-771114", {0x771112: 0x21}, ["U-chain-771114"]),
    ("Ch-7711fd", {0x7711fc: 0x25}, ["U-chain-7711fd"]),
    ("Ch-77884f", {0x77884e: 0x39}, ["U-chain-77884f"]),
    ("Ch-77890c", {0x77890b: 0x39}, ["U-chain-77890c"]),
    ("Ch-778956", {0x778955: 0x39}, ["U-chain-778956"]),
    ("Ch-778bcf", {0x778bce: 0x39}, ["U-chain-778bcf"]),
    ("Ch-778dd1", {0x778dd0: 0x39}, ["U-chain-778dd1"]),
    ("Ch-778e24", {0x778e23: 0x39}, ["U-chain-778e24"]),
    ("Ch-779c3d", {0x779c3c: 0x25}, ["U-chain-779c3d"]),
    ("Ch-779ebd", {0x779ebc: 0x25}, ["U-chain-779ebd"]),
    ("Set-527920", {0x71241d: 0x90}, ["U-hist-527920", "U-set-527920", "U-tot-527920"]),
    ("Set-527cc0", {0x4acec7: 0x90}, ["U-hist-527cc0", "U-set-527cc0", "U-tot-527cc0"]),
    ("Set-527f20", {0x4f2e30: 0x90}, ["U-hist-527f20", "U-set-527f20", "U-tot-527f20"]),
    ("Set-528220", {0x474a5f: 0x90}, ["U-hist-528220", "U-set-528220", "U-tot-528220"]),
    ("Set-528c00", {0x4f1d7b: 0x90}, ["U-hist-528c00", "U-set-528c00", "U-tot-528c00"]),
    ("Set-529160", {0x46cd7b: 0x90}, ["U-hist-529160", "U-set-529160", "U-tot-529160"]),
    ("Set-52a760", {0x68a754: 0x90}, ["U-hist-52a760", "U-set-52a760", "U-tot-52a760"]),
    ("Ctl-5276d0", {0x41cd38: 0x81}, ["U-ctl-5276d0"]),
    ("Ctl-5283d0", {0x5fa9b4: 0xc1}, ["U-ctl-5283d0"]),
    ("Ctl-528a10", {0x41cd11: 0x81}, ["U-ctl-528a10"]),
    ("Ctl-528f00", {0x5fabb4: 0xc1}, ["U-ctl-528f00"]),
    ("Ctl-5295f0", {0x41ccc3: 0x81}, ["U-ctl-5295f0"]),
    ("Vp-0", {0x7787c7: 0x01}, ["U-vptrstore-7787c0"]),
    ("Vp-1", {0x779bba: 0x01}, ["U-vptrstore-779bb3"]),
    ("Vp-2", {0x779e3a: 0x01}, ["U-vptrstore-779e33"]),
    ("Rt-name", {0x817510: 0x58}, ["U-rtti-name"]),
    ("Rt-ctl", {0x8174c8: 0x95}, ["U-rtti-ctl"]),
    ("Adj-1", {0x5cefc5: 0x90}, ["U-chain-5cefc9", "U-hist-528c00", "U-lea-adj"]),
    ("P1f-edi", {0x689e9c: 0x8d}, ["U-chain-68a754", "U-chain-68a772", "U-chain-68a790", "U-p1f-edi"]),
    ("P1f-G", {0x687747: 0x1c}, ["U-p1f-G"]),
    ("P1f-Fcallers", {0x687853: 0x90}, ["U-p1f-Fcallers"]),
    ("P1f-Fhead", {0x689e90: 0x56}, ["U-p1f-Fhead"]),
    ("Drift-1", {0x68a770: 0xb9}, ["U-chain-68a790", "U-hist-52a760", "U-noverdict-drift", "U-set-52a760", "U-tot-52a760"]),
    ("Drift-thunk", {0x474a59: 0xb9}, ["U-chain-474a5f", "U-hist-528220", "U-noverdict-drift"]),
    ("P1f-slot", {0x686b4e: 0x18}, ["U-chain-6874a9", "U-chain-687516", "U-hist-527cc0", "U-p1f-slot0"]),
]

_ORIG_BUILD = None


def _full_mode():
    """monkeypatch (this process only): force FULL decode rebuild -- the
    R-061 freeze-suite reviewed mechanism; the incremental _splice path and
    this one must produce identical red-sets or the case is MISMATCH."""
    import r061_witness_this_contract as G61

    def build_full(mut):
        buf = bytearray(G61._ctx["buf"])
        for a, v in (mut or {}).items():
            buf[a - G61._ctx["TLO"]] = v
        st = G61._full_stream(buf)
        c, i, p = G61._maps(st)
        return st, c, i, p, buf
    return build_full


def red_of(Gmod, mut, full):
    """run gate check under the mutation via the gate's own load env path."""
    import r061_witness_this_contract as G61
    _orig = G61.build
    if full:
        G61.build = _full_mode()
    try:
        os.environ["R062_MUTATE"] = ",".join(
            "0x%X=0x%X" % (k, v) for k, v in sorted(mut.items()))
        Gmod.load()
        R2, _n2 = Gmod.check_body()
    finally:
        G61.build = _orig
    return sorted(l for l, c_, _ in R2 if not c_)


def main():
    GR = importlib.import_module("r062_upward_trace_contract")
    # baseline (no mutation) must be all green (ruling 3)
    os.environ.pop("R062_MUTATE", None)
    GR.load()
    R, n = GR.check_body()
    ALL = [l for l, c_, _ in R]
    if n != len(R):
        print("BASELINE NOT GREEN (%d/%d) -- abort (ruling 3)" % (n, len(R)))
        sys.exit(2)
    print("baseline %d/%d PASS" % (n, len(R)), flush=True)

    exact = survived = ms = mf = exc = 0
    covered = set()
    import time
    for name, mut, exp in CASES:
        t = time.time()
        try:
            red_sp = red_of(GR, mut, full=False)
            red_fu = red_of(GR, mut, full=True)
        except Exception as ex:
            exc += 1
            print("%-16s EXC:%r" % (name, ex), flush=True)
            continue
        if not red_sp:
            survived += 1
            print("%-16s SURVIVED (no killer)" % name, flush=True)
            continue
        if red_sp != exp:
            ms += 1
            print("%-16s SPLICE-MISMATCH sp=%s exp=%s" % (name, red_sp, exp),
                  flush=True)
            continue
        if red_fu != exp:
            mf += 1
            print("%-16s FULL-MISMATCH fu=%s exp=%s" % (name, red_fu, exp),
                  flush=True)
            continue
        exact += 1
        covered |= set(exp)
        print("%-16s %.1fs EXACT" % (name, time.time() - t), flush=True)
    os.environ.pop("R062_MUTATE", None)

    exp_labels = set()
    for _, _, exp in CASES:
        exp_labels |= set(exp)
    phantom = sorted(exp_labels - set(ALL))
    unc = sorted(set(ALL) - covered)
    print("\n== R-062 FREEZE-SUITE TALLY ==")
    print("cases=%d exact=%d survived=%d exc=%d splice-mismatch=%d full-mismatch=%d"
          % (len(CASES), exact, survived, exc, ms, mf))
    print("labels=%d covered-by-literals=%d uncovered=%d phantom-expectations=%d"
          % (len(ALL), len(ALL) - len(unc), len(unc), len(phantom)))
    for x in unc:
        print("  UNCOVERED", x)
    for x in phantom:
        print("  PHANTOM", x)
    ok = (exact == len(CASES) and not survived and not exc and not ms
          and not mf and not unc and not phantom)
    print("== %d/%d cases exact-killed (pending independent review) =="
          % (exact, len(CASES)))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
