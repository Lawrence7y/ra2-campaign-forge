#!/usr/bin/env python3
"""Independent verifier for survive(N) terminal frame invariance."""
import json, re, sys
from collections import defaultdict
from pathlib import Path

def read_json(path):
    try:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        obj = json.loads(text)
        return (obj, None) if isinstance(obj, dict) else (None, f"expected JSON object, got {type(obj).__name__}")
    except Exception as exc:
        return None, str(exc)

def extract_frame(data):
    if not isinstance(data, dict) or not isinstance(data.get("result"), dict):
        return None, "<missing result>"
    res = data["result"]
    obs = res.get("observation")
    candidates = []
    if isinstance(obs, dict) and isinstance(obs.get("terminal"), dict):
        candidates.append(("result.observation.terminal", obs["terminal"]))
    if isinstance(res.get("terminal"), dict):
        candidates.append(("result.terminal", res["terminal"]))
    for prefix, term in candidates:
        for key in ("frame_at", "frame"):
            if key in term and term[key] is not None:
                return term[key], f"{prefix}.{key}"
    return None, "<missing terminal/frame>"

def infer_n(trip, condition, pre):
    m = re.findall(r"(?<![a-z0-9])s(\d+)(?![a-z0-9])", trip, re.I)
    if len(set(m)) == 1:
        return int(m[0]), "trip_name:s<N>"
    if isinstance(pre, dict):
        for k in ("design_n", "n", "N", "survive_seconds", "survive_s"):
            v = pre.get(k)
            if isinstance(v, int) and not isinstance(v, bool):
                return v, f"CONFIG_PRE.{k}"
        blob = " ".join(str(pre.get(k, "")) for k in ("condition", "label", "scenario", "name", "trip"))
        m2 = re.findall(r"(?<![a-z0-9])(?:s|survive[_\s(]*)(\d+)(?![a-z0-9])", blob, re.I)
        if len(set(m2)) == 1:
            return int(m2[0]), "CONFIG_PRE:label"
    if condition is not None:
        m3 = re.findall(r"(?<![a-z0-9])(?:s|survive[_\s(]*)(\d+)(?![a-z0-9])", str(condition), re.I)
        if len(set(m3)) == 1:
            return int(m3[0]), "condition:label"
    return None, "unclassified"

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: verify_survive.py <root_dir>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        sys.exit(f"ERROR: not a directory: {root}")
    files = sorted(root.rglob("TRIP_RESULT.json"))
    if not files:
        sys.exit(f"ERROR: no TRIP_RESULT.json found under {root}")
    rows, anomalies = [], []
    for res_path in files:
        trip_dir = res_path.parent
        trip = trip_dir.name
        res_data, res_err = read_json(res_path)
        pre_data, pre_err = read_json(trip_dir / "CONFIG_PRE.json")
        ok = res_data.get("ok") if res_data else None
        outcome = res_data.get("outcome") if res_data else None
        frame_at, frame_path = extract_frame(res_data)
        condition = pre_data.get("condition") if pre_data else None
        diff = pre_data.get("config_diff_vs_pristine") if pre_data else None
        if isinstance(diff, list):
            changed = [str(x.get("file") or x.get("path") or x.get("name") or x) if isinstance(x, dict) else str(x) for x in diff]
            changed_str = ",".join(changed) if changed else "[]"
        else:
            changed, changed_str = None, "<missing>"
        n_val, n_src = infer_n(trip, condition, pre_data)
        rows.append(dict(trip=trip, condition=condition, changed_str=changed_str, frame_at=frame_at,
                         frame_path=frame_path, ok=ok, outcome=outcome, n=n_val, n_src=n_src))
        if res_err: anomalies.append(f"{trip}: TRIP_RESULT.json error: {res_err}")
        if pre_err: anomalies.append(f"{trip}: CONFIG_PRE.json error: {pre_err}")
        if frame_at is None: anomalies.append(f"{trip}: missing frame_at ({frame_path})")
        if ok is not True: anomalies.append(f"{trip}: ok={ok!r}, outcome={outcome!r}")
        if not isinstance(condition, str) or not condition.strip():
            anomalies.append(f"{trip}: missing/empty condition")
        elif changed is not None:
            cl = condition.lower()
            if ("pristine" in cl or "baseline" in cl) and changed:
                anomalies.append(f"{trip}: unexpected condition {condition!r} with changed_files={changed}")
            if not changed and not any(k in cl for k in ("pristine", "baseline", "control", "default")):
                anomalies.append(f"{trip}: condition {condition!r} has empty config_diff_vs_pristine")
        if pre_data is not None and changed is None: anomalies.append(f"{trip}: missing/non-list config_diff_vs_pristine")
        if n_val is None: anomalies.append(f"{trip}: could not classify design N")
    print("TABLE:")
    print("trip | condition | changed_files | frame_at | ok | outcome")
    for r in rows:
        print(f"{r['trip']} | {r['condition']} | {r['changed_str']} | {r['frame_at']} | {r['ok']} | {r['outcome']}")
    print("EXTRACTION_PATHS:")
    for r in rows:
        print(f"  {r['trip']}: {r['frame_path']} (N_source={r['n_src']})")
    print("INFERENCE_RULE: Unique token s<N> in trip dir name (case-insensitive); fallback to CONFIG_PRE.{design_n,n,N,survive_seconds,survive_s} or s<N>/survive<N> in CONFIG_PRE label/condition.")
    unclassified = [r for r in rows if r["n"] is None]
    print("UNCLASSIFIED: " + (", ".join(r["trip"] for r in unclassified) if unclassified else "none"))
    by_n = defaultdict(list)
    for r in rows:
        if r["n"] is not None: by_n[r["n"]].append(r)
    refuted = []
    print("PER_N_SUMMARY:")
    for n in sorted(by_n):
        frames = [r["frame_at"] for r in by_n[n]]
        uniq = sorted({f for f in frames if f is not None})
        missing = sum(1 for f in frames if f is None)
        inv = (len(uniq) == 1 and missing == 0)
        exp = 15 * n + 90
        law_ok = inv and (uniq[0] == exp)
        print(f"  N={n}: trips={len(frames)} frames={frames} expected={exp} invariant={inv} equals_15N_plus_90={law_ok}")
        if not inv: refuted.append(f"N={n} frames={frames}")
        if len(uniq) > 1: anomalies.append(f"duplicated N={n} with different frames: {uniq}")
        if inv and not law_ok: anomalies.append(f"N={n}: invariant frame {uniq[0]} != 15*{n}+90 ({exp})")
    print("VERDICT: " + ("CLAIM REFUTED: " + ("; ".join(refuted) if refuted else "no classified N groups") if (not by_n or refuted) else "CLAIM HOLDS per-N frames are invariant"))
    print("ANOMALIES:" + ("" if anomalies else " none"))
    for a in anomalies:
        print(f"  - {a}")

if __name__ == "__main__":
    main()
