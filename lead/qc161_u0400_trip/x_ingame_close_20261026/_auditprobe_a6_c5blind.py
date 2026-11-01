# -*- coding: utf-8 -*-
"""_auditprobe_a6_c5blind.py — A6 盲区扩展实验：C5 对「任意 ≥6 行截尾 + 计数同步」是否可检。

另验：行时间跨度/密度口径（watch_s、closed_at_s、rows 时间戳）——探针完全不用。
"""
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

PROBE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_x_channel_probe_20261027.py")
spec = importlib.util.spec_from_file_location("_p6", str(PROBE))
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

root = Path(tempfile.mkdtemp(prefix="aud_c5_"))


def trunc_keep(o, r, keep):
    tl = json.loads((o / "timeline.json").read_text(encoding="utf-8"))
    full = tl["close_rows"]
    tl["close_rows"] = full[-keep:]
    (o / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    r["close_rows_n"] = keep
    return full


def main():
    print("== 截尾规模扫描：rows 原 40，截到 keep 行且 close_rows_n 同步 ==")
    for keep in (5, 6, 7, 10, 20, 39):
        out, rec = P._fixture(root / ("k%d" % keep))
        trunc_keep(out, rec, keep)
        rr = {c: ok for c, _, ok, _ in P.judge_artifacts(out, rec)}
        print("   keep=%2d ⇒ C5=%s  (red=%s)  全表=%s" % (
            keep, "绿" if rr.get("C5") else "红", not rr.get("C5"),
            {k: v for k, v in rr.items() if not v}))
    print()
    print("== 时间跨度盲区：保留全部 40 行但删光中段（仅存首尾），计数谎报 40 ==")
    out, rec = P._fixture(root / "span")
    tl = json.loads((out / "timeline.json").read_text(encoding="utf-8"))
    rows = tl["close_rows"]
    tl["close_rows"] = rows[:2] + rows[-2:]
    (out / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    rec["close_rows_n"] = 40   # 谎报与原始一致；但行数=4<6 ⇒ C5 应红（>=6 不满足）
    rr = {c: ok for c, _, ok, _ in P.judge_artifacts(out, rec)}
    print("   4 行+谎报40 ⇒ C5=%s" % ("绿" if rr.get("C5") else "红"))
    # 再造 8 行稀疏（>=6）谎报 40 ⇒ 应红（8≠40）
    out, rec = P._fixture(root / "span8")
    tl = json.loads((out / "timeline.json").read_text(encoding="utf-8"))
    tl["close_rows"] = tl["close_rows"][::5][:8]
    (out / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    rec["close_rows_n"] = 40
    rr = {c: ok for c, _, ok, _ in P.judge_artifacts(out, rec)}
    print("   8 行稀疏+谎报40 ⇒ C5=%s（计数不符被抓）" % ("绿" if rr.get("C5") else "红"))
    # 关键盲区：截到 >=6 行且把计数同步改小 ⇒ 上面 keep 已覆盖，这里验「计数同步」口径
    print()
    print("== 密度盲区：0.1s 名义节奏 vs 实际时间戳（watch_s/closed_at_s 完全未被 C5 使用）==")
    out, rec = P._fixture(root / "dense")
    tl = json.loads((out / "timeline.json").read_text(encoding="utf-8"))
    for i, row in enumerate(tl["close_rows"]):
        row["t"] = 1000.0 + i * 0.1          # 原样（fixture 本以此节奏）
    tl["close_rows"] = tl["close_rows"][-30:]  # 截尾 30 行
    (out / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    rec["close_rows_n"] = 30
    rec["watch_s"] = 40.0                     # v2 rec 本就带 watch_s
    rr = {c: ok for c, _, ok, _ in P.judge_artifacts(out, rec)}
    print("   截 30/40 计数同步=30 且 rec.watch_s=40 ⇒ C5=%s（无时间-计数交叉验）"
          % ("绿" if rr.get("C5") else "红"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(root, ignore_errors=True)
