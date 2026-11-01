# -*- coding: utf-8 -*-
"""R-061 freeze-candidate mutation suite (round-5 calibration -> frozen literals).

PROVENANCE (ruling 2026-10-26, six conditions):
  * expectations below are HAND-TRANSCRIBED from the sealed calibration manifest
    `out/_r061_freeze5.json` (round 5, 194 cases, killed=194 / survived=0 / exc=0 /
    splice-full-mismatch=0 / uncovered=0). This file NEVER derives expected
    red-sets from its own measurements (ruling 4): the expected set of every case
    is a literal; a case passes only if BOTH execution paths' actual red-sets are
    EXACTLY equal to that literal.
  * each case runs twice -- gate incremental `_splice` build AND forced FULL
    decode rebuild -- both must match the frozen red-set (ruling 5 cross-check,
    now part of formal verification instead of calibration-only).
  * the suite refuses to run unless gate file + image hashes still equal the
    hashes sealed in the manifest (expectation staleness guard).
  * manifest sha256 6330e5de64d5edf624771ef6eb0caeb2a39cbb3191e57d0c213deb1056c03ca8
    gate   sha256 3080309aa23e194e63601603a6527abe988502710de942995968d2bea121ebfc
    image  sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476

STATUS: freeze CANDIDATE pending out-of-family independent review (ruling 6).
Until that review passes this suite documents reproducibility of the frozen
calibration, NOT an independently verified claim.

G-79 machine tail: every counted gate label must appear in some case's frozen
expected set (bidirectional assertion<->killer reconciliation, computed from the
literals + the gate's label inventory -- zero-hit => exit 1).

Rounds 0-5 calibration history kept at out/_calib_r061_mut*.py / _r061_mut_calib*.txt.
"""
import hashlib
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
GATE_PATH = os.path.join(HERE, "r061_witness_this_contract.py")
IMAGE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
MANIFEST = r"D:\Project\ra2-campaign-forge\out\_r061_freeze5.json"

FROZEN_GATE_SHA = "3080309aa23e194e63601603a6527abe988502710de942995968d2bea121ebfc"
FROZEN_IMAGE_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
FROZEN_MANIFEST_SHA = "6330e5de64d5edf624771ef6eb0caeb2a39cbb3191e57d0c213deb1056c03ca8"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---- staleness guard: hash-pin before executing anything -------------------
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
    print("STALE: out/_r061_freeze5.json changed after transcription")
    sys.exit(3)

# ---- frozen literals (transcribed mechanically from the sealed manifest;
# ---- provenance generator out/_gen_r061_freeze_lits.py, never re-derived) --
CASES = [
    ("A-527750", {0x5279e8: 0x64, 0x5279e9: 0xfd, 0x5279ea: 0xff, 0x5279eb: 0xff}, ["A-527750"]),
    ("A-5279bd", {0x527d89: 0x30, 0x527d8a: 0xfc, 0x527d8b: 0xff, 0x527d8c: 0xff}, ["A-5279bd"]),
    ("A-527d5b", {0x527ffc: 0x5b, 0x527ffd: 0xfd, 0x527ffe: 0xff, 0x527fff: 0xff}, ["A-527d5b"]),
    ("A-527fd1", {0x5282e8: 0xe5, 0x5282e9: 0xfc, 0x5282ea: 0xff, 0x5282eb: 0xff}, ["A-527fd1"]),
    ("A-5282a0", {0x528498: 0x04, 0x528499: 0xfe, 0x52849a: 0xff, 0x52849b: 0xff}, ["A-5282a0"]),
    ("A-528450", {0x528aef: 0x5d, 0x528af0: 0xf9, 0x528af1: 0xff, 0x528af2: 0xff}, ["A-528450"]),
    ("A-528aa7", {0x528ce2: 0xc1, 0x528ce3: 0xfd, 0x528ce4: 0xff, 0x528ce5: 0xff}, ["A-528aa7"]),
    ("A-528cb7", {0x528fc2: 0xf1, 0x528fc3: 0xfc, 0x528fc4: 0xff, 0x528fc5: 0xff}, ["A-528cb7"]),
    ("A-528f97", {0x52921e: 0x75, 0x52921f: 0xfd, 0x529220: 0xff, 0x529221: 0xff}, ["A-528f97"]),
    ("A-5291f3", {0x5296b6: 0x39, 0x5296b7: 0xfb, 0x5296b8: 0xff, 0x5296b9: 0xff}, ["A-5291f3"]),
    ("A-5293e3", {0x529394: 0xeb, 0x529395: 0xfe}, ["A-5293e3", "A-cold-5293e3", "A-sig-529394", "C-5293e3"]),
    ("A-52966e", {0x52a824: 0x46, 0x52a825: 0xee, 0x52a826: 0xff, 0x52a827: 0xff}, ["A-52966e"]),
    ("A-52a7de", {0x527798: 0x42, 0x527799: 0x30, 0x52779a: 0x00, 0x52779b: 0x00}, ["A-52a7de"]),
    ("A-cold", {0x529394: 0x90}, ["A-cold-5293e3", "A-sig-529394"]),
    ("Asig-5276d0", {0x5276d0: 0xb3}, ["A-sig-5276d0"]),
    ("Asig-527920", {0x527920: 0xb1}, ["A-sig-527920"]),
    ("Asig-527cc0", {0x527cc0: 0xb3}, ["A-sig-527cc0"]),
    ("Asig-527f20", {0x527f20: 0xb3}, ["A-sig-527f20"]),
    ("Asig-528220", {0x528220: 0xb3}, ["A-sig-528220"]),
    ("Asig-5283d0", {0x5283d0: 0xb3}, ["A-sig-5283d0"]),
    ("Asig-528a10", {0x528a10: 0xb3}, ["A-sig-528a10"]),
    ("Asig-528c00", {0x528c00: 0xb1}, ["A-sig-528c00"]),
    ("Asig-528f00", {0x528f00: 0x88}, ["A-sig-528f00"]),
    ("Asig-529160", {0x529160: 0xb1}, ["A-sig-529160"]),
    ("Asig-5295f0", {0x5295f0: 0xb3}, ["A-sig-5295f0"]),
    ("Asig-52a760", {0x52a760: 0xb3}, ["A-sig-52a760"]),
    ("B1-527750", {0x52772e: 0x31}, ["B1-527750"]),
    ("B2-527750", {0x527731: 0x2d}, ["B2-527750"]),
    ("B3-527750", {0x527751: 0x9c}, ["B3-527750"]),
    ("B4-527750", {0x52774e: 0xcf}, ["B4-527750"]),
    ("B1-5279bd", {0x52799b: 0x31}, ["B1-5279bd"]),
    ("B2-5279bd", {0x52799e: 0x2d}, ["B2-5279bd"]),
    ("B3-5279bd", {0x5279be: 0x2f}, ["B3-5279bd"]),
    ("B4-5279bd", {0x5279bc: 0xcf}, ["B4-5279bd"]),
    ("B1-527d5b", {0x527d33: 0x31}, ["B1-527d5b"]),
    ("B2-527d5b", {0x527d36: 0x2d}, ["B2-527d5b"]),
    ("B3-527d5b", {0x527d5c: 0x91}, ["B3-527d5b"]),
    ("B4-527d5b", {0x527d5a: 0xcf}, ["B4-527d5b"]),
    ("B2-527fd1", {0x527faa: 0x2d}, ["B2-527fd1"]),
    ("B3-527fd1", {0x527fd2: 0x1b}, ["B3-527fd1"]),
    ("B4-527fd1", {0x527fcf: 0xcf}, ["B4-527fd1"]),
    ("B1-5282a0", {0x52827e: 0x31}, ["B1-5282a0"]),
    ("B2-5282a0", {0x528281: 0x2d}, ["B2-5282a0"]),
    ("B3-5282a0", {0x5282a1: 0x4c}, ["B3-5282a0"]),
    ("B4-5282a0", {0x52829e: 0xcf}, ["B4-5282a0"]),
    ("B1-528450", {0x52842e: 0x31}, ["B1-528450"]),
    ("B2-528450", {0x528431: 0x2d}, ["B2-528450"]),
    ("B3-528450", {0x528451: 0x9c}, ["B3-528450"]),
    ("B4-528450", {0x52844e: 0xcf}, ["B4-528450"]),
    ("B1-528aa7", {0x528a85: 0x31}, ["B1-528aa7"]),
    ("B2-528aa7", {0x528a88: 0x2d}, ["B2-528aa7"]),
    ("B3-528aa7", {0x528aa8: 0x45}, ["B3-528aa7"]),
    ("B4-528aa7", {0x528aa5: 0xcf}, ["B4-528aa7"]),
    ("B1-528cb7", {0x528c95: 0x31}, ["B1-528cb7"]),
    ("B2-528cb7", {0x528c98: 0x2d}, ["B2-528cb7"]),
    ("B3-528cb7", {0x528cb8: 0x35}, ["B3-528cb7"]),
    ("B4-528cb7", {0x528cb5: 0xcf}, ["B4-528cb7"]),
    ("B1-528f97", {0x528f75: 0x31}, ["B1-528f97"]),
    ("B2-528f97", {0x528f78: 0x2d}, ["B2-528f97"]),
    ("B3-528f97", {0x528f98: 0x55}, ["B3-528f97"]),
    ("B4-528f97", {0x528f96: 0xcf}, ["B4-528f97"]),
    ("B1-5291f3", {0x5291d1: 0x31}, ["B1-5291f3"]),
    ("B2-5291f3", {0x5291d4: 0x2d}, ["B2-5291f3"]),
    ("B3-5291f3", {0x5291f4: 0xf9}, ["B3-5291f3"]),
    ("B4-5291f3", {0x5291f2: 0xcf}, ["B4-5291f3"]),
    ("B1-5293e3", {0x5293c1: 0x31}, ["B1-5293e3"]),
    ("B2-5293e3", {0x5293c4: 0x2d}, ["B2-5293e3"]),
    ("B3-5293e3", {0x5293e4: 0x09}, ["B3-5293e3"]),
    ("B4-5293e3", {0x5293e2: 0xcf}, ["B4-5293e3"]),
    ("B1-52966e", {0x52964c: 0x31}, ["B1-52966e"]),
    ("B2-52966e", {0x52964f: 0x2d}, ["B2-52966e"]),
    ("B3-52966e", {0x52966f: 0x7e}, ["B3-52966e"]),
    ("B4-52966e", {0x52966c: 0xcf}, ["B4-52966e"]),
    ("B1-52a7de", {0x52a7bc: 0x31}, ["B1-52a7de"]),
    ("B2-52a7de", {0x52a7bf: 0x2d}, ["B2-52a7de"]),
    ("B3-52a7de", {0x52a7df: 0x0e}, ["B3-52a7de"]),
    ("B4-52a7de", {0x52a7dc: 0xcf}, ["B4-52a7de"]),
    ("C-527750", {0x527700: 0x09}, ["C-527750"]),
    ("C-5279bd", {0x52796d: 0x09}, ["C-5279bd"]),
    ("C-527d5b", {0x527d05: 0x09}, ["C-527d5b"]),
    ("C-527fd1", {0x527f7a: 0x09}, ["C-527fd1"]),
    ("C-5282a0", {0x528250: 0x09}, ["C-5282a0"]),
    ("C-528450", {0x528400: 0x09}, ["C-528450"]),
    ("C-528aa7", {0x528a57: 0x09}, ["C-528aa7"]),
    ("C-528cb7", {0x528c65: 0x09}, ["C-528cb7"]),
    ("C-528f97", {0x528f47: 0x09}, ["C-528f97"]),
    ("C-5291f3", {0x5291a3: 0x09}, ["C-5291f3"]),
    ("C-5293e3", {0x529393: 0x09}, ["C-5293e3"]),
    ("C-52966e", {0x52961e: 0x09}, ["C-52966e"]),
    ("C-52a7de", {0x52a769: 0x1f}, ["C-52a7de"]),
    ("Gf-527750", {0x52775f: 0x11}, ["G-fill-527750"]),
    ("Gc-527750", {0x527746: 0x09}, ["G-cmp-527750"]),
    ("Gf-5279bd", {0x5279cc: 0x11}, ["G-fill-5279bd"]),
    ("Gc-5279bd", {0x5279b3: 0x09}, ["G-cmp-5279bd"]),
    ("Gf-527d5b", {0x527d6a: 0x11}, ["G-fill-527d5b"]),
    ("Gc-527d5b", {0x527d4e: 0x09}, ["G-cmp-527d5b"]),
    ("Gf-527fd1", {0x527fe0: 0x11}, ["G-fill-527fd1"]),
    ("Gc-527fd1", {0x527fc2: 0x50}, ["G-cmp-527fd1"]),
    ("Gf-5282a0", {0x5282af: 0x11}, ["G-fill-5282a0"]),
    ("Gc-5282a0", {0x528296: 0x09}, ["G-cmp-5282a0"]),
    ("Gf-528450", {0x52845f: 0x11}, ["G-fill-528450"]),
    ("Gc-528450", {0x528446: 0x09}, ["G-cmp-528450"]),
    ("Gf-528aa7", {0x528ab6: 0x11}, ["G-fill-528aa7"]),
    ("Gc-528aa7", {0x528a9d: 0x09}, ["G-cmp-528aa7"]),
    ("Gf-528cb7", {0x528cc6: 0x11}, ["G-fill-528cb7"]),
    ("Gc-528cb7", {0x528cad: 0x09}, ["G-cmp-528cb7"]),
    ("Gf-528f97", {0x528fa6: 0x11}, ["G-fill-528f97"]),
    ("Gc-528f97", {0x528f8d: 0x09}, ["G-cmp-528f97"]),
    ("Gf-5291f3", {0x529202: 0x11}, ["G-fill-5291f3"]),
    ("Gc-5291f3", {0x5291e9: 0x09}, ["G-cmp-5291f3"]),
    ("Gf-5293e3", {0x5293f2: 0x11}, ["G-fill-5293e3"]),
    ("Gc-5293e3", {0x5293d9: 0x09}, ["G-cmp-5293e3"]),
    ("Gf-52966e", {0x52967d: 0x11}, ["G-fill-52966e"]),
    ("Gc-52966e", {0x529664: 0x09}, ["G-cmp-52966e"]),
    ("Gf-52a7de", {0x52a7ed: 0x11}, ["G-fill-52a7de"]),
    ("Gc-52a7de", {0x52a7d4: 0x09}, ["G-cmp-52a7de"]),
    ("D2C-5276d0", {0x52780d: 0x2d}, ["D-2C-5276d0"]),
    ("D2C-527920", {0x527a62: 0x2d}, ["D-2C-527920"]),
    ("D2C-527cc0", {0x527e03: 0x2d}, ["D-2C-527cc0"]),
    ("D2C-528220", {0x52835d: 0x2d}, ["D-2C-528220"]),
    ("D2C-5283d0", {0x52850d: 0x2d}, ["D-2C-5283d0"]),
    ("D2C-528a10", {0x528b64: 0x2d}, ["D-2C-528a10"]),
    ("D2C-528c00", {0x528d5c: 0x2d}, ["D-2C-528c00"]),
    ("D2C-528f00", {0x52903c: 0x2d}, ["D-2C-528f00"]),
    ("D2C-529160", {0x529298: 0x2d}, ["D-2C-529160"]),
    ("D2C-529394", {0x529488: 0x2d}, ["D-2C-529394"]),
    ("D2C-5295f0", {0x52972b: 0x2d}, ["D-2C-5295f0"]),
    ("D2C-52a760", {0x52a897: 0x2d}, ["D-2C-52a760"]),
    ("D30-5276d0", {0x52783f: 0x31}, ["D-30-5276d0"]),
    ("D30-527920", {0x527a8b: 0x31}, ["D-30-527920"]),
    ("D30-527cc0", {0x527e2c: 0x31}, ["D-30-527cc0"]),
    ("D30-527f20", {0x52808b: 0x31}, ["D-30-527f20"]),
    ("D30-528220", {0x52838f: 0x31}, ["D-30-528220"]),
    ("D30-5283d0", {0x52853f: 0x31}, ["D-30-5283d0"]),
    ("D30-528a10", {0x528b96: 0x31}, ["D-30-528a10"]),
    ("D30-528c00", {0x528d80: 0x31}, ["D-30-528c00"]),
    ("D30-528f00", {0x529069: 0x31}, ["D-30-528f00"]),
    ("D30-529160", {0x5292c8: 0x31}, ["D-30-529160"]),
    ("D30-529394", {0x5294b3: 0x31}, ["D-30-529394"]),
    ("D30-5295f0", {0x52975d: 0x31}, ["D-30-5295f0"]),
    ("D30-52a760", {0x52a8c9: 0x31}, ["D-30-52a760"]),
    ("D2C-absent-527f20", {0x5281b6: 0xbe, 0x5281b7: 0x2c, 0x5281b8: 0x88, 0x5281b9: 0xb7, 0x5281ba: 0x00}, ["D-2C-527f20"]),
    ("Df-527818", {0x52781a: 0x09}, ["D-fill-527818"]),
    ("Df-52782c", {0x52782e: 0x09}, ["D-fill-52782c"]),
    ("Df-528070", {0x528072: 0x09}, ["D-fill-528070"]),
    ("Df-528368", {0x52836a: 0x09}, ["D-fill-528368"]),
    ("Df-528b73", {0x528b75: 0x09}, ["D-fill-528b73"]),
    ("Df-52904a", {0x52904c: 0x09}, ["D-fill-52904a"]),
    ("Df-52a8a2", {0x52a8a4: 0x09}, ["D-fill-52a8a2"]),
    ("Df-52a8b4", {0x52a8b6: 0x09}, ["D-fill-52a8b4"]),
    ("Dw2c", {0x52b4ab: 0x2d}, ["D-walk-2c", "D-walk-count"]),
    ("Dw30", {0x52b28b: 0x31}, ["D-walk-30", "D-walk-count"]),
    ("Dw2cR", {0x52b4af: 0x05}, ["D-walk-2c-ret"]),
    ("Dw30R", {0x52b28f: 0x05}, ["D-walk-30-ret"]),
    ("Cs-527750", {0x5275cd: 0xd1}, ["C-spill-527750"]),
    ("Cs-527d5b", {0x527b98: 0xd1}, ["C-spill-527d5b"]),
    ("Cs-528f97", {0x528df3: 0xd1}, ["C-spill-528f97"]),
    ("Cs-52a7de", {0x52a624: 0xd1}, ["C-spill-52a7de"]),
    ("Eh-5276d0-g8870c0", {0x5d93e0: 0xc1}, ["E-hist-5276d0"]),
    ("Eh-5276d0-g887180", {0x41cd38: 0x81}, ["E-hist-5276d0"]),
    ("Ec-5276d0", {0x41cd4a: 0x83}, ["E-cnt-5276d0", "E-hist-5276d0"]),
    ("Eh-5283d0-g8870c0", {0x5fa9b4: 0xc1}, ["E-hist-5283d0"]),
    ("Ec-5283d0", {0x427fb0: 0x1d}, ["E-cnt-5283d0"]),
    ("Eh-528a10-g8870c0", {0x5facd6: 0xc1}, ["E-hist-528a10"]),
    ("Eh-528a10-g887180", {0x41cd11: 0x81}, ["E-hist-528a10"]),
    ("Ec-528a10", {0x410aa1: 0x6c}, ["E-cnt-528a10"]),
    ("Eh-528f00-g8870c0", {0x5fabb4: 0xc1}, ["E-hist-528f00"]),
    ("Ec-528f00", {0x597b0d: 0xf0}, ["E-cnt-528f00"]),
    ("Eh-5295f0-g8870c0", {0x5fa74c: 0xc1}, ["E-hist-5295f0"]),
    ("Eh-5295f0-g887180", {0x41ccc3: 0x81}, ["E-hist-5295f0"]),
    ("Ec-5295f0", {0x41cc5d: 0x90}, ["E-cnt-5295f0"]),
    ("Ek-527920", {0x712411: 0xcf}, ["E-kind-527920"]),
    ("Ek-527cc0", {0x4aceb8: 0xce}, ["E-kind-527cc0"]),
    ("Ek-527f20", {0x4f2e2f: 0xcf}, ["E-kind-527f20"]),
    ("Ek-528c00", {0x4f1d76: 0x4d}, ["E-kind-528c00"]),
    ("Ek-529160", {0x46cd7a: 0xce}, ["E-kind-529160"]),
    ("Ek-52a760", {0x68a748: 0xce}, ["E-kind-52a760"]),
    ("Es-527920", {0x71241e: 0xff}, ["E-kind-527920", "E-scnt-527920"]),
    ("Es-527cc0", {0x4acec8: 0xf5}, ["E-kind-527cc0", "E-scnt-527cc0"]),
    ("Es-527f20", {0x4f2e31: 0xec}, ["E-kind-527f20", "E-scnt-527f20"]),
    ("Es-528220", {0x474a60: 0xbd}, ["A-5282a0", "E-kind-528220", "E-scnt-528220"]),
    ("Es-528c00", {0x4f1d7c: 0x81}, ["E-kind-528c00", "E-scnt-528c00"]),
    ("Es-529160", {0x46cd7c: 0xe1}, ["E-kind-529160", "E-scnt-529160"]),
    ("Es-52a760", {0x68a755: 0x08}, ["E-kind-52a760", "E-scnt-52a760"]),
    ("F1", {0x52cbfc: 0x59}, ["F1-new1"]),
    ("F2", {0x52ccde: 0x59}, ["F2-new2"]),
    ("F3", {0x52cc39: 0x1b}, ["F3-vptr"]),
    ("F4", {0x52c606: 0x87}, ["F4-fcallers"]),
    ("F5-887058", {0x40e245: 0x7f}, ["F5-stamp-887058"]),
    ("F5-8870c0", {0x40e2f5: 0x7f}, ["F5-stamp-8870c0"]),
    ("F5-887128", {0x40e195: 0x7f}, ["F5-stamp-887128"]),
    ("F5-887180", {0x40e035: 0x7f}, ["F5-stamp-887180"]),
    ("F5-887208", {0x40e0e5: 0x7f}, ["F5-stamp-887208"]),
    ("F5-89f518", {0x49b409: 0x7f}, ["F5-stamp-89f518"]),
]

_ORIG_BUILD = None


def _full_mode(Gmod):
    """monkeypatch only inside this process: force FULL decode rebuild path."""
    def build_full(mut):
        buf = bytearray(Gmod._ctx["buf"])
        for a, v in (mut or {}).items():
            buf[a - Gmod._ctx["TLO"]] = v
        st = Gmod._full_stream(buf)
        c, i, p = Gmod._maps(st)
        return st, c, i, p, buf
    return build_full


def red_of(Gmod, mut, full):
    if full:
        Gmod.build = _full_mode(Gmod)
        try:
            R2, _ = Gmod.run_case(mut)
        finally:
            Gmod.build = _ORIG_BUILD
    else:
        R2, _ = Gmod.run_case(mut)
    return sorted(l for l, c_, _ in R2 if not c_)


def main():
    G = importlib.import_module("r061_witness_this_contract")
    global _ORIG_BUILD
    G.load()
    _ORIG_BUILD = G.build

    # baseline must be all green (ruling 3)
    R, n = G.run_case({})
    ALL = [l for l, c_, _ in R]
    if n != len(R):
        print("BASELINE NOT GREEN (%d/%d) -- abort (ruling 3)" % (n, len(R)))
        sys.exit(2)
    print("baseline %d/%d PASS" % (n, len(R)), flush=True)

    exact_ok = survived = mismatch_sp = mismatch_fu = exc = 0
    covered = set()
    for name, mut, exp in CASES:
        try:
            red_sp = red_of(G, mut, full=False)
            red_fu = red_of(G, mut, full=True)
        except Exception as ex:
            exc += 1
            print("%-22s EXC:%r" % (name, ex), flush=True)
            continue
        if not red_sp:
            survived += 1
            print("%-22s SURVIVED (no killer)" % name, flush=True)
            continue
        if red_sp != exp:
            mismatch_sp += 1
            print("%-22s SPLICE-MISMATCH sp=%s exp=%s" % (name, red_sp, exp), flush=True)
            continue
        if red_fu != exp:
            mismatch_fu += 1
            print("%-22s FULL-MISMATCH fu=%s exp=%s" % (name, red_fu, exp), flush=True)
            continue
        exact_ok += 1
        covered |= set(exp)
        print("%-22s EXACT %s" % (name, exp), flush=True)

    # G-79 tail: every gate label must be claimed by >=1 frozen expectation,
    # and every frozen expectation label must exist in the gate.
    exp_labels = set()
    for _, _, exp in CASES:
        exp_labels |= set(exp)
    phantom = sorted(exp_labels - set(ALL))
    unc = sorted(set(ALL) - covered)
    print("\n== FREEZE-SUITE TALLY ==")
    print("cases=%d exact=%d survived=%d exc=%d splice-mismatch=%d full-mismatch=%d"
          % (len(CASES), exact_ok, survived, exc, mismatch_sp, mismatch_fu))
    print("labels=%d covered-by-literals=%d uncovered=%d phantom-expectations=%d"
          % (len(ALL), len(ALL) - len(unc), len(unc), len(phantom)))
    for x in unc:
        print("  UNCOVERED", x)
    for x in phantom:
        print("  PHANTOM", x)
    ok = (exact_ok == len(CASES) and not survived and not exc
          and not mismatch_sp and not mismatch_fu and not unc and not phantom)
    print("== %d/%d cases exact-killed (freeze-candidate, pending independent review) =="
          % (exact_ok, len(CASES)))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
