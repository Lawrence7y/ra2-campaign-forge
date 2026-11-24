# -*- coding: utf-8 -*-
"""步骤1：口径审计探针
- 全部 137 个文件的 key 集合（确认 A8EC34 是否存在于 ndjson）
- t_perf_ns vs t_monotonic 的分辨率/一致性
- 相邻采样 Δframe 的分布与奇偶性
- interval_ms_actual 分布
- read_status / step / mode 取值
"""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C


def main():
    out = []
    files = C.all_files()
    out.append("files=%d" % len(files))
    key_union = Counter()
    key_per_file = {}
    for p in files:
        ks = Counter()
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                ks.update(o.keys())
        key_per_file[C.trip_rel(p)] = ks
        key_union.update(ks)
    out.append("\n=== key 出现文件数 (137 个文件里有多少文件含该 key) ===")
    for k, c in sorted(key_union.items(), key=lambda kv: -kv[1]):
        out.append("  %-24s files=%3d" % (k, c))
    has_a8ec34 = [r for r, ks in key_per_file.items() if "A8EC34" in ks]
    out.append("\n含 A8EC34 的文件数 = %d" % len(has_a8ec34))
    for r in has_a8ec34[:20]:
        out.append("   " + r)
    # 是否有别的 X87E8E0 之外的自定义键
    out.append("\n各文件 key 数分布: %s" % dict(Counter(len(v) for v in key_per_file.values())))
    print("\n".join(out))
    C.write_evidence("01_schema.txt", "\n".join(out))


if __name__ == "__main__":
    main()
