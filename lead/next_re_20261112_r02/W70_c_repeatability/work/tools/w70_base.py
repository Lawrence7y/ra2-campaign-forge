# -*- coding: utf-8 -*-
r"""W70 GLOBAL BASELINE (runs ONCE, before any cycle).  NO lock, NO gamemd.exe.

  1. Assert 0 live gamemd.exe.
  2. Full manifest of the REAL dir (ra2youli) -> out/real_pre.json, and assert
     it matches the W44 signed-off baseline (647 files / 1,989,215,270 B / 277
     maplike + four anchor hashes).
  3. Parse the OFFICIAL [SOV1] Scenario= from the real BATTLEMD.INI and persist
     it as OFFICIAL_SOV1.json — this is the exact filename T2 expects at
     Scen+0x125C (must NOT be RA2F_M1.MAP).

The REAL dir is READ-ONLY here.  git is read-only.  Everything lands in W70/out.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w70_lib as L
import w70_common as C

TAG = "base"


def parse_sov1(raw: bytes):
    """Return the [SOV1] Scenario= value (latin-1), or None."""
    txt = raw.decode("latin-1", errors="replace")
    lines = txt.splitlines()
    in_sov = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("[") and s.endswith("]"):
            if in_sov:
                break                      # next section ends [SOV1]
            in_sov = (s.upper() == "[SOV1]")
            continue
        if in_sov and s.lower().startswith("scenario="):
            return s.split("=", 1)[1].strip()
    return None


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    out = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="global baseline: real dir PRE manifest + official [SOV1] value",
                  real=str(C.REAL), lock=str(C.LOCK))
        residual = L.list_gamemd()
        sink.step("gamemd_guard", processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("live gamemd.exe at baseline: %r" % residual)

        # (1) real dir PRE full manifest
        rp = C.write_manifest(C.OUT / "real_pre.json", C.REAL)
        s = rp["summary"]
        sink.step("real_pre_summary", summary=s)
        assert s["file_count"] == C.BASELINE["file_count"], s
        assert s["total_bytes"] == C.BASELINE["total_bytes"], s
        assert s["maplike_count"] == C.BASELINE["maplike_count"], s
        for name, pref in C.BASELINE.items():
            if name in ("file_count", "total_bytes", "maplike_count"):
                continue
            h = s["hashes"].get(name)
            assert h and h.startswith(pref), (name, h, pref)
        sink.step("real_pre_baseline_ok", verdict=True)

        # (2) official [SOV1] Scenario
        b = (C.REAL / "BATTLEMD.INI").read_bytes()
        scen = parse_sov1(b)
        official_sha = L.sha256_file(C.REAL / "BATTLEMD.INI")
        o = {
            "source_file": str(C.REAL / "BATTLEMD.INI"),
            "source_size": len(b),
            "source_sha256": official_sha,
            "sov1_scenario": scen,
            "is_our_injected_map": bool(scen and "RA2F" in scen.upper()),
            "note": "T2 expects Scen+0x125C == this value after uninstall+restore; "
                    "must NOT be RA2F_M1.MAP / RA2F_M2.MAP / RA2F_M3.MAP",
        }
        (C.OUT / "OFFICIAL_SOV1.json").write_text(
            json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
        sink.step("official_sov1", **o)
        assert scen and not o["is_our_injected_map"], o

        # (3) package identity (byte-inventory of the reused W63 build)
        files = []
        for p in sorted(C.PKG.rglob("*"), key=lambda x: x.as_posix().lower()):
            if p.is_file():
                files.append({"rel": p.relative_to(C.PKG).as_posix(),
                              "size": p.stat().st_size,
                              "sha256": L.sha256_file(p)})
        pkg = {"package": str(C.PKG), "file_count": len(files), "files": files,
               "note": "byte-identical copy of W63_route_a_e2e/work/pkg/W63RouteA "
                       "(verified 0 mismatches); NOT modified by W70"}
        (C.OUT / "PACKAGE_INVENTORY.json").write_text(
            json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")
        sink.step("package_inventory", file_count=len(files),
                  battlemd_sha=next(f["sha256"] for f in files
                                    if f["rel"] == "BATTLEMD.INI"),
                  mapsel_sha=next(f["sha256"] for f in files
                                  if f["rel"] == "MAPSELMD.INI"))

        out = {"real_pre": str(C.OUT / "real_pre.json"),
               "official_sov1": scen, "official_sha256": official_sha,
               "lock": C.lock_read()}
        ok = True
        sink.step("base_result", ok=ok, **out)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
