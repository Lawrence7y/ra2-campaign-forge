# -*- coding: utf-8 -*-
"""W162 step 0: 全语料 key 并集 + 两套 schema 判定 + 计数器分布。
流式读，不建大对象。"""
import json, os, sys, collections

FILES = [l.strip() for l in open(
    os.path.join(os.path.dirname(__file__), "run_files.txt"), encoding="utf-8") if l.strip()]

COUNTERS = ["A8ED50", "B0CE88", "A8E9A0", "87E8E0", "X87E8E0", "ABCD58",
            "g1", "g2", "g3", "g4"]


def main():
    keys = collections.Counter()
    nlines = 0
    nbad = 0
    schema = {}
    per_file = []
    for p in FILES:
        n = 0
        nA = nB = nNull_mono = 0
        for line in open(p, "r", encoding="utf-8", buffering=1 << 20):
            n += 1
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                nbad += 1
                continue
            for k in o:
                keys[k] += 1
            if "t_mono_ns" in o and "mode_A8B238" in o:
                nB += 1
            elif "t_monotonic" in o and "mode" in o:
                nA += 1
            if o.get("t_monotonic") is None:
                nNull_mono += 1
        nlines += n
        per_file.append((p, n, nA, nB, nNull_mono))
        s = "A" if nA >= nB else "B"
        schema[s] = schema.get(s, 0) + 1

    print("=== key union (137 files) ===")
    for k, c in sorted(keys.items(), key=lambda kv: -kv[1]):
        print(f"  {k:24s} {c}")
    print(f"\ntotal lines = {nlines}   bad json = {nbad}")
    print(f"schema counts = {schema}")
    print("\n=== per-file schema ===")
    for p, n, nA, nB, nNull in per_file:
        tag = "A" if nA >= nB else ("B" if nB else "?")
        print(f"{tag}  lines={n:7d} nA={nA:7d} nB={nB:7d} null_t_monotonic={nNull:7d}  {p}")
    print("\n=== counter key presence ===")
    for c in COUNTERS:
        print(f"  {c:10s} present_in_samples = {keys.get(c,0)}")


if __name__ == "__main__":
    main()
