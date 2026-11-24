#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 2 - BUILD with v12 (offline).

One package that enables BOTH --mapselmd and --csf-out/--csf-base (a COMPLETE
official CSF clone, never a minimal CSF). Records command/exit/artifacts.
"""
from __future__ import annotations

import json
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "build"


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  v12=str(C.V12), design=str(C.DESIGN), csf_text=C.CSF_TEXT)

        # (0) re-verify the official CSF base ourselves
        base = C.CSF_BASE
        sink.step("csf_base_check", path=str(base), size=base.stat().st_size,
                  sha256=L.sha256_file(base))
        assert base.stat().st_size == C.OFFICIAL_CSF_SIZE
        assert L.sha256_file(base) == C.OFFICIAL_CSF_SHA

        # (1) validate
        v = C.v12_cmd(sink, "validate", ["validate", str(C.DESIGN)])
        if v["exit_code"] != 0:
            raise RuntimeError("validate exit %s" % v["exit_code"])

        # (2) build - BOTH features on, csf-out outside any game directory
        C.CSF_WORK.parent.mkdir(parents=True, exist_ok=True)
        if C.CSF_WORK.is_file():
            C.CSF_WORK.unlink()
        b = C.v12_cmd(sink, "build_v12", [
            "build", "--design", str(C.DESIGN), "--out", str(C.PKG_OUT),
            "--mapselmd",
            "--csf-out", str(C.CSF_WORK),
            "--csf-base", str(C.CSF_BASE),
        ], timeout=300)
        if b["exit_code"] != 0:
            raise RuntimeError("build exit %s: %s" % (b["exit_code"], b["stderr_tail"][-800:]))

        # (3) artifact inventory
        files = []
        for p in sorted(C.PKG.rglob("*"), key=lambda x: x.as_posix().lower()):
            if p.is_file():
                files.append({"rel": p.relative_to(C.PKG).as_posix(),
                              "size": p.stat().st_size,
                              "sha256": L.sha256_file(p)})
        sink.step("package_files", package=str(C.PKG), files=files, n=len(files))

        def art(name):
            p = C.PKG / name
            return p if p.is_file() else None

        # (4) MAPSELMD.INI = complete official clone + appended stages
        pm = art("MAPSELMD.INI")
        assert pm, "MAPSELMD.INI missing"
        ms = {"size": pm.stat().st_size, "sha256": L.sha256_file(pm)}
        raw = pm.read_bytes()
        ms["crlf_only"] = (raw.count(b"\n") == raw.count(b"\r\n")
                           and raw.count(b"\r\n") > 0)
        ms["matches_w39_appended"] = (ms["size"] == C.W39_APPENDED_MAPSEL_SIZE
                                      and ms["sha256"] == C.W39_APPENDED_MAPSEL_SHA)
        ms["appended_stage_sections"] = [x.decode("latin-1") for x in
                                         re.findall(rb"\[(RA2F_ECH0[12]_[0-9A-F]{8})\]", raw)]
        ms["nod_keys_8_9"] = [(k.decode(), v.decode("latin-1")) for k, v in
                              re.findall(rb"(?m)^(8|9)=([^\r\n]+)", raw)]
        sink.step("mapselmd_artifact", **ms)

        # (5) ra2md.csf = complete official CSF clone + our label
        pc = art("ra2md.csf")
        assert pc, "ra2md.csf missing"
        cs = {"size": pc.stat().st_size, "sha256": L.sha256_file(pc),
              "gt_official": pc.stat().st_size > C.OFFICIAL_CSF_SIZE,
              "magic": pc.read_bytes()[:4].decode("latin-1")}
        sink.step("csf_artifact", **cs)
        assert cs["magic"] == " FSC", cs

        # (6) csf_patch.json: label + value + completeness
        pp = art("csf_patch.json")
        assert pp, "csf_patch.json missing"
        patch = json.loads(pp.read_text(encoding="utf-8"))
        patch["_text_matches_design"] = (patch.get("text") == C.CSF_TEXT)
        sink.step("csf_patch", **patch)

        # (7) BATTLEMD98.INI Description = CSF label (NOT raw text)
        pb = art("BATTLEMD98.INI")
        assert pb, "BATTLEMD98.INI missing"
        bt = pb.read_text(encoding="utf-8", errors="replace")
        desc = [x for x in bt.splitlines() if x.startswith("Description=")]
        sink.step("battle98", size=pb.stat().st_size,
                  sha256=L.sha256_file(pb), description_lines=desc,
                  battles_lines=[x for x in bt.splitlines()
                                 if x.startswith("15=") or x.startswith("Scenario=")])

        # (8) maps: SkipMapSelect=no, NextScenario chain
        for name in ("ECH01.MAP", "ECH02.MAP"):
            p = art(name)
            assert p, name + " missing"
            txt = p.read_bytes().decode("latin-1")
            sink.step("map_basic", name=name, size=p.stat().st_size,
                      sha256=L.sha256_file(p),
                      next_scenario=[x for x in txt.splitlines()
                                     if x.startswith("NextScenario=")],
                      skip_mapsel=[x for x in txt.splitlines()
                                   if x.startswith("SkipMapSelect=")],
                      end_of_game=[x for x in txt.splitlines()
                                   if x.startswith("EndOfGame=")])

        # (9) BUILD_REPORT self-checks
        pr = art("BUILD_REPORT.txt")
        if pr:
            sink.step("build_report", text=pr.read_text(encoding="utf-8", errors="replace"))

        # (10) csf-out working file == package copy
        sink.step("csf_work", path=str(C.CSF_WORK), size=C.CSF_WORK.stat().st_size,
                  sha256=L.sha256_file(C.CSF_WORK),
                  identical_to_pkg=(C.CSF_WORK.read_bytes() == pc.read_bytes()))

        ok = True
        sink.step("build_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok)
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
