#!/usr/bin/env python3
# R136-DS: independent recomputation of F24 corpus on-disk survival. READ-ONLY.
# No writes outside _r136/sub_deepseek/.
import os, sys, json, collections

ROOT   = "/home/t628/projects/ra2-campaign-forge"
LEAD   = os.path.join(ROOT, "lead")
TSV    = os.path.join(LEAD, "next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv")
SNAP   = os.path.join(LEAD, "next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv")

def read_tsv(path, ncol):
    rows = []
    with open(path, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
        header = f.readline().rstrip("\n").split("\t")
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln:
                continue
            p = ln.split("\t")
            if len(p) != ncol:
                continue
            rows.append(p)
    return header, rows

def stat1(rel, base):
    """Return ('OK'|'DIFF'|'ENOENT'|'OTHER', cur_bytes_or_None, detail)"""
    p = os.path.join(base, rel)
    try:
        st = os.stat(p)
        return ("OK", st.st_size, "")
    except FileNotFoundError:
        return ("ENOENT", None, "ENOENT")
    except NotADirectoryError:
        return ("ENOENT", None, "NotADirectory(path component is a file)")
    except PermissionError:
        return ("OTHER", None, "EACCES")
    except OSError as e:
        return ("OTHER", None, f"{e.__class__.__name__}:{e.errno}")

def main():
    out = {}
    hdr, rows = read_tsv(TSV, 4)
    out["tsv_header"] = hdr
    S1_n = len(rows)
    S1_bytes = sum(int(r[1]) for r in rows)
    out["S1"] = {"rows": S1_n, "sum_bytes": S1_bytes}

    # ---- S2: per-row stat under lead/ ----
    buckets = collections.defaultdict(list)   # state -> [(rel, listed, cur)]
    for rel, b, src, why in rows:
        lb = int(b)
        state, cur, det = stat1(rel, LEAD)
        if state == "OK":
            if cur == lb:
                buckets["same"].append((rel, lb, cur))
            else:
                buckets["diff"].append((rel, lb, cur))
        elif state == "ENOENT":
            buckets["enoent"].append((rel, lb, None))
        else:
            buckets["other"].append((rel, lb, det))

    same = buckets["same"]; diff = buckets["diff"]
    eno  = buckets["enoent"]; other = buckets["other"]
    out["S2"] = {
        "same_n": len(same), "same_bytes_listed": sum(x[1] for x in same),
        "same_bytes_current":  sum(x[2] for x in same),
        "diff_n": len(diff), "diff_listed_bytes": sum(x[1] for x in diff),
        "diff_current_bytes": sum(x[2] for x in diff),
        "diff_detail": [{"rel": r, "listed": l, "current": c, "delta": c - l} for r, l, c in diff],
        "enoent_n": len(eno), "enoent_listed_bytes": sum(x[1] for x in eno),
        "enoent_detail": [{"rel": r, "listed": l} for r, l, _ in eno],
        "other_n": len(other), "other_detail": other,
    }

    # ---- S3: self-check ----
    n_sum = len(same) + len(diff) + len(eno) + len(other)
    b_sum = (sum(x[1] for x in same) + sum(x[1] for x in diff)
             + sum(x[1] for x in eno))
    out["S3"] = {"bucket_n_sum": n_sum, "S1_n": S1_n, "n_equal": n_sum == S1_n,
                 "bucket_listed_bytes_sum": b_sum, "S1_bytes": S1_bytes,
                 "bytes_equal": b_sum == S1_bytes}

    # ---- S4: by source ----
    s4 = {}
    for src in sorted({r[2] for r in rows}):
        sub = [r for r in rows if r[2] == src]
        n = len(sub); by = sum(int(r[1]) for r in sub)
        ex_n = ex_b = 0
        for rel, b, s, why in sub:
            state, cur, det = stat1(rel, LEAD)
            if state in ("OK", "OTHER"):   # exists on disk
                ex_n += 1; ex_b += int(b)
        s4[src] = {"n": n, "bytes": by, "exists_n": ex_n, "exists_bytes": ex_b,
                   "missing_n": n - ex_n}
    out["S4"] = s4

    # ---- S5: ENOENT rels vs snapshot ----
    snap_hdr, snap_rows = read_tsv(SNAP, 5)
    out["snap_header"] = snap_hdr
    snap = {}
    for p in snap_rows:
        snap.setdefault(p[0], int(p[2]))   # rel -> ext,bytes,... ; bytes = col index 2
    out["snap_rows"] = len(snap_rows); out["snap_distinct_rel"] = len(snap)
    hit_same = hit_diff = absent = 0
    diff_detail = []; same_list = []
    for rel, lb, _ in eno:
        if rel in snap:
            if snap[rel] == lb:
                hit_same += 1; same_list.append(rel)
            else:
                hit_diff += 1
                diff_detail.append({"rel": rel, "listed_4417": lb, "snap": snap[rel]})
        else:
            absent += 1
    out["S5"] = {"in_snap_same_bytes": hit_same, "in_snap_diff_bytes": hit_diff,
                 "not_in_snap": absent, "diff_detail": diff_detail}

    # ---- S6: positive control (5 files outside the manifest) ----
    candidates = ["next_re_20261117_r14/R14_COMMON.md",
                  "next_re_20261117_r14/COMPACT_STATE.md",
                  "next_re_20261117_r14/DISC_ESTABLISH.tsv",
                  "next_re_20261117_r14/R17_R17_SLOT73_MAP",
                  "next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv"]
    ctl = []
    for c in candidates:
        state, cur, det = stat1(c, LEAD)
        ctl.append({"rel": c, "state": state, "bytes": cur, "detail": det})
    out["S6a"] = ctl

    # negative control: same manifest, base = project ROOT instead of lead/
    ok_root = 0
    for rel, b, src, why in rows:
        state, cur, det = stat1(rel, ROOT)
        if state in ("OK", "OTHER"):
            ok_root += 1
    out["S6b"] = {"root_hits": ok_root, "root_total": S1_n,
                  "root_hit_rate": round(ok_root / S1_n, 6) if S1_n else None,
                  "lead_hits": S1_n - len(eno) - len(other),
                  "lead_hit_rate": round((S1_n - len(eno) - len(other)) / S1_n, 6)}

    with open("/home/t628/projects/ra2-campaign-forge/_r136/sub_deepseek/r136_f24surv.json", "w",
              encoding="utf-8") as g:
        json.dump(out, g, ensure_ascii=False, indent=1)
    # human summary to stdout
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("S2", "S5")}, ensure_ascii=False, indent=1))
    s2 = out["S2"]
    print("S2 same_n=%d same_listed=%d diff_n=%d enoent_n=%d enoent_listed=%d other_n=%d"
          % (s2["same_n"], s2["same_bytes_listed"], s2["diff_n"],
             s2["enoent_n"], s2["enoent_listed_bytes"], s2["other_n"]))
    print("S5", out["S5"]["in_snap_same_bytes"], out["S5"]["in_snap_diff_bytes"], out["S5"]["not_in_snap"])

if __name__ == "__main__":
    main()
