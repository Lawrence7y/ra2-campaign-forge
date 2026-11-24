# -*- coding: utf-8 -*-
"""_proxy_scan_corpus.py — 语料结构普查（任务 1：counters 字段结构，零真机、只读既有 JSON）。

语料 = out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/ 下全部 measure_w*.json
（编排方指纹三件 measure_w0/w1/w2.json 均在该树 archive_T32/ 内，已另验 SHA256 相符）。

输出：_proxy_scan_corpus_out.txt
  - 每个 distinct counters 键集（不臆造，逐键列出）
  - 每文件一行：verdict / hz_effective / frame_ms_p50 / counters 快照数 / units 有效读数
  - t_rel 采样间隔（对照 harness 注释「1 Hz 计数器副读」）
"""
import json
import os
import sys
from statistics import median

ROOT = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_proxy_scan_corpus_out.txt")


def main():
    lines = []
    say = lines.append
    files = []
    for root, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(fs):
            if f.startswith("measure_w") and f.endswith(".json"):
                files.append(os.path.join(root, f))
    files.sort()
    say("corpus_root = %s" % ROOT)
    say("corpus_count = %d" % len(files))

    keysets = {}      # tuple(keys) -> [relpath...]
    counter_val_keys = ["units", "infantry", "aircraft", "g", "b", "techno",
                        "g_items", "b_items", "ws_kb", "pf_kb", "t_rel"]
    per_file = []
    stats_key_union = set()
    gate_key_union = set()
    for p in files:
        rel = os.path.relpath(p, ROOT)
        try:
            with open(p, "rb") as fh:
                d = json.loads(fh.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            say("PARSE_FAIL %s %r" % (rel, e))
            continue
        cs = d.get("counters")
        cs = cs if isinstance(cs, list) else []
        ks = tuple(sorted({k for c in cs if isinstance(c, dict) for k in c}))
        keysets.setdefault(ks, []).append(rel)
        st = d.get("stats") or {}
        gt = d.get("gate") or {}
        stats_key_union |= set(st)
        gate_key_union |= set(gt)
        units_vals = [c.get("units") for c in cs if isinstance(c, dict)]
        u_valid = [v for v in units_vals if isinstance(v, (int, float))]
        trels = [c.get("t_rel") for c in cs if isinstance(c, dict)
                 and isinstance(c.get("t_rel"), (int, float))]
        dts = [round(b - a, 4) for a, b in zip(trels, trels[1:])]
        per_file.append((
            rel, d.get("verdict"), st.get("hz_effective"), st.get("frame_ms_p50"),
            st.get("fps_avg"), gt.get("units0"), d.get("hz"), len(cs),
            len(u_valid),
            (round(median(dts), 4) if dts else None),
        ))

    say("")
    say("== A. counters 键集（distinct=%d）==" % len(keysets))
    for ks in sorted(keysets, key=lambda k: (-len(keysets[k]), k)):
        say("  n=%3d  keys=%s" % (len(keysets[ks]), list(ks)))
    say("")
    say("== B. stats 顶层键并集（%d 个）==" % len(stats_key_union))
    say("  %s" % sorted(stats_key_union))
    say("== B2. gate 顶层键并集（%d 个）==" % len(gate_key_union))
    say("  %s" % sorted(gate_key_union))
    say("")
    say("== C. 逐文件（relpath | verdict | hz_eff | p50(ms) | fps_avg | units0 | hz | "
        "n_ctr | units有效 | t_rel中位步长(s)) ==")
    for row in per_file:
        say("  %s | %s | %s | %s | %s | %s | %s | %s | %s | %s" % row)

    n_ok = sum(1 for r in per_file if r[1] == "ok")
    n_ok_hz = sum(1 for r in per_file
                  if r[1] == "ok" and isinstance(r[2], (int, float)) and r[2] >= 100)
    say("")
    say("== D. 资格统计 ==")
    say("  verdict==ok           : %d / %d" % (n_ok, len(per_file)))
    say("  verdict==ok & hz>=100 : %d / %d   (§603 同一口径)" % (n_ok_hz, len(per_file)))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("WROTE", OUT, "lines:", len(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
