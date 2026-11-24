#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W75 · build the two-trip A/B comparison table from the raw artifacts.
Writes out/AB_COMPARISON.json (pure file output; no console-text artifacts)."""
import json
import w75_lib as L

OUT = L.OUT


def load(tag):
    s = json.loads((OUT / ("TRIP_%s.json" % tag)).read_text(encoding="utf-8"))
    c = json.loads((OUT / ("controls_trip%s.json" % tag.lower())
                    if False else OUT / ("controls_%s.json" % ("tripA" if tag == "A" else "tripB")))
                   .read_text(encoding="utf-8"))
    nd = [json.loads(x) for x in
          (OUT / ("scen_readings_%s.ndjson" % ("tripA" if tag == "A" else "tripB")))
          .read_text(encoding="utf-8").splitlines() if x.strip()]
    return s, c, nd


A, cA, ndA = load("A")
B, cB, ndB = load("B")


def series(nd):
    return {r["label"]: r for r in nd}


sA, sB = series(ndA), series(ndB)

rows = []
for label in ("campaign_menu_baseline", "after_hover", "after_click_t0",
              "after_click_t1", "after_click_t2", "after_click_t3"):
    a, b = sA[label], sB[label]
    rows.append({
        "label": label,
        "A_sel_ctrl_id": a["sel_ctrl_id"], "A_sel_hex": a["sel_ctrl_id_hex"],
        "B_sel_ctrl_id": b["sel_ctrl_id"], "B_sel_hex": b["sel_ctrl_id_hex"],
        "A_scen_ptr": a["scen_ptr"], "B_scen_ptr": b["scen_ptr"],
        "A_battle_idx_i32": a["scen_battle_idx_i32"],
        "B_battle_idx_i32": b["scen_battle_idx_i32"],
        "A_battle_idx_hex": a["scen_battle_idx_hex"],
        "B_battle_idx_hex": b["scen_battle_idx_hex"],
        "A_scen_filename": a["scen_filename"],
        "B_scen_filename": b["scen_filename"],
        "A_frame": a["frame"], "B_frame": b["frame"],
        "A_mode": a["mode"], "B_mode": b["mode"],
        "A_battle_cnt": a["battle_cnt"], "B_battle_cnt": b["battle_cnt"],
    })

res = {
    "tripA": {
        "exe_sha_in_place": A.get("sandbox_exe_final_sha"),
        "pid": A.get("pid"), "ok": A.get("ok"),
        "campaign_menu_reached": A.get("campaign_menu_reached"),
        "controls": A.get("controls"),
        "hotzone": A.get("hotzone"),
        "after_click": A.get("after_click"),
        "log_delta": A.get("log_delta"),
        "config_restore_all_match": A.get("config_restore_all_match"),
        "residual_own_pid": A.get("residual_own_pid"),
        "lock_after": A.get("lock_after"),
    },
    "tripB": {
        "exe_sha_in_place": B.get("sandbox_exe_final_sha"),
        "pid": B.get("pid"), "ok": B.get("ok"),
        "campaign_menu_reached": B.get("campaign_menu_reached"),
        "controls": B.get("controls"),
        "hotzone": B.get("hotzone"),
        "after_click": B.get("after_click"),
        "log_delta": B.get("log_delta"),
        "config_restore_all_match": B.get("config_restore_all_match"),
        "residual_own_pid": B.get("residual_own_pid"),
        "lock_after": B.get("lock_after"),
    },
    "per_sample": rows,
    "control_delta": {
        "n_controls_A": cA["n_controls"], "n_controls_B": cB["n_controls"],
        "n_visible_A": cA["summary"]["n_visible"],
        "n_visible_B": cB["summary"]["n_visible"],
        "has_1771_A": cA["summary"]["has_1771"],
        "has_1771_B": cB["summary"]["has_1771"],
        "ctrl_ids_A": cA["summary"]["ctrl_ids"],
        "ctrl_ids_B": cB["summary"]["ctrl_ids"],
        "ids_only_in_A": sorted(set(cA["summary"]["ctrl_ids"])
                                - set(cB["summary"]["ctrl_ids"])),
        "ids_only_in_B": sorted(set(cB["summary"]["ctrl_ids"])
                                - set(cA["summary"]["ctrl_ids"])),
    },
    "note": ("scen_ptr values are plain JSON integers in the source ndjson; "
             "a pwsh console rendering showed '64011-128' for tripB's 64011128 "
             "-- display artifact only, confirmed by hexdump."),
}
(OUT / "AB_COMPARISON.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1, default=str),
    encoding="utf-8")

with (OUT / "AB_COMPARISON.tsv").open("w", encoding="utf-8",
                                      newline="\n") as f:
    cols = ["label", "A_sel_ctrl_id", "A_sel_hex", "B_sel_ctrl_id",
            "B_sel_hex", "A_battle_idx_i32", "B_battle_idx_i32",
            "A_scen_filename", "B_scen_filename", "A_frame", "B_frame"]
    f.write("\t".join(cols) + "\n")
    for r in rows:
        f.write("\t".join(str(r[c]) for c in cols) + "\n")

print("AB_COMPARISON written")
