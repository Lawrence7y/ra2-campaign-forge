#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W40 · summarize the three live NDJSON sinks into one compact JSON + stdout."""
from __future__ import annotations

import json
from pathlib import Path

W40 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W40_csf_live")
OUT = W40 / "out"
TAGS = ["w40_A_minimal", "w40_B_full", "w40_C_nocsf"]


def rows(tag):
    p = OUT / (tag + ".ndjson")
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def main():
    summary = {}
    for tag in TAGS:
        rs = rows(tag)
        rec = {"tag": tag, "n_records": len(rs), "steps": [r.get("step") for r in rs]}
        for r in rs:
            s = r.get("step")
            if s in ("startup_outcome", "run_outcome", "error_dialog_detected",
                     "S0_main_menu", "S2_campaign_menu", "S2_campaign_menu_control",
                     "natural_exit_and_exit_code", "process_exited_exit_code",
                     "step0_desktop_precheck", "deploy_done",
                     "battle98_description_rewritten"):
                rec.setdefault("events", []).append(
                    {k: r.get(k) for k in
                     ("step", "outcome", "elapsed_s", "pid", "process_alive",
                      "visible_control_texts", "dialog_windows", "err_text_hits",
                      "exit_code", "exited", "wait_s", "window_station",
                      "thread_desktop", "input_desktop", "enum_windows_total",
                      "imagegrab", "pass", "loose_csf_sha256", "new", "old")})
            if s == "memory_search":
                h = r.get("hits", {})
                rec.setdefault("memory", []).append({
                    "label": r.get("label"),
                    "regions_scanned": r.get("regions_scanned"),
                    "bytes_read": r.get("bytes_read"),
                    "hits": {k: {"count": v.get("count"),
                                 "samples": [x.get("context") for x in v.get("samples", [])[:3]],
                                 "addrs": [x.get("addr") for x in v.get("samples", [])[:3]]}
                             for k, v in h.items()},
                })
            if s in ("meta_end", "restore_after_test", "residual_after_close"):
                rec.setdefault("heal", []).append(
                    {k: r.get(k) for k in ("step", "outcome", "gamemd_residual",
                                           "loose_csf_present", "battle98_sha256", "rows",
                                           "residual")})
        summary[tag] = rec
    (OUT / "live_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8")
    for tag, rec in summary.items():
        print("=" * 78)
        print(tag, "records=", rec["n_records"])
        for e in rec.get("events", []):
            print("  EVENT", json.dumps(e, ensure_ascii=True)[:420])
        for m in rec.get("memory", []):
            print("  MEMORY", m["label"], "regions=", m["regions_scanned"],
                  "bytes=", m["bytes_read"])
            for k, v in m["hits"].items():
                if v["count"]:
                    print("    HIT", k, "count=", v["count"],
                          "ctx=", json.dumps(v["samples"], ensure_ascii=True)[:300])
                else:
                    print("    miss", k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
