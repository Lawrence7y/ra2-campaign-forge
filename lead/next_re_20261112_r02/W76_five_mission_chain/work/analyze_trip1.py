import json, hashlib, re
from pathlib import Path
card = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W76_five_mission_chain")
out = card / "out"
nd = [json.loads(x) for x in (out/"run.ndjson").read_text(encoding="utf-8").splitlines() if x.strip()]
print("run.ndjson records:", len(nd))

def ev(step):
    return [r for r in nd if r.get("step") == step]

print("\n=== level_entered / level_advance / level_victory ===")
for r in nd:
    if r["step"] in ("level_entered", "level_advance", "level_victory"):
        w = r.get("w59", {})
        print(json.dumps({
            "step": r["step"], "level": r.get("level"),
            "from": r.get("from_level"), "to": r.get("to_level"),
            "fn": w.get("scen_filename"), "stage": w.get("scen_stage_idx"),
            "eog": w.get("scen_end_of_game"), "frame": w.get("frame"),
            "battle_idx": w.get("scen_battle_idx"),
            "skip_mapsel": w.get("scen_skip_mapsel"),
            "frame_advancing": r.get("frame_advancing"),
            "frame_stalled": r.get("frame_stalled"),
            "screenshot": (r.get("screenshot") or "").split("\\")[-1],
        }, ensure_ascii=False))

print("\n=== transition_ordering (all advances) ===")
for r in ev("transition_ordering"):
    print(json.dumps({k: r.get(k) for k in
                      ("from_level","to_level","fn_changed_before_stage_written",
                       "n_intermediate_samples","intermediate_samples")},
                     ensure_ascii=False))

print("\n=== transition_samples_full (compact) ===")
for r in ev("transition_samples_full"):
    print(r["from_level"], "->", r["to_level"], "n=", r["n_samples"],
          [(s["fn"], s["stage"], s["frame"]) for s in r["samples"]])

print("\n=== final_endofgame_observation ===")
for r in ev("final_endofgame_observation"):
    print("elapsed_s", r.get("elapsed_s"), "end_of_game_byte", r.get("end_of_game_byte"),
          "no_extra_start", r.get("no_extra_start"),
          "extra_scenario_candidates", r.get("extra_scenario_candidates"),
          "n_filename_samples", len(r.get("scen_filename_traj", [])))
    print("distinct filenames:", sorted(set(r.get("scen_filename_traj", []))))
    print("distinct stages:", sorted(set(str(x) for x in r.get("stage_traj", []))))
    print("distinct frames:", sorted(set(str(x) for x in r.get("frame_traj", []))))

print("\n=== task2_field_table ===")
for r in ev("task2_field_table"):
    print("all_match:", r.get("all_match"))
    for row in r.get("rows", []):
        print(" ", row["mission"], "0x35A0=", row["0x35A0_stage_idx"],
              "pred=", row["lead_prediction_0x35A0"], "match=", row["matches_lead_prediction"],
              "0x125C=", row["0x125C_scen_filename"], "eog=", row["0x34AC_end_of_game"],
              "frame=", row["frame"])

print("\n=== trip_result ===")
for r in ev("trip_result"):
    print("ok", r.get("ok"), "outcome", r.get("outcome"), "task2_all_match", r.get("task2_all_match"))
    print("levels", json.dumps(r.get("levels"), ensure_ascii=False))

print("\n=== error / blocked / fatal / UnableMapSelect ===")
errs = [r for r in nd if r["step"] in ("FATAL","trip_blocked","block_static_branch",
                                       "error_dialog","screenshot_error","close_error")]
print("error-ish steps:", len(errs), [r["step"] for r in errs])
raw = (out/"run.ndjson").read_text(encoding="utf-8")
for tok in ("UnableMapSelect", "Invalid stage", "MSG:UnableMapSelect"):
    print("count", tok, "=", raw.count(tok))

print("\n=== screenshots ===")
for p in sorted(out.glob("screen_*.png")):
    print(" ", p.name, p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()[:12])
