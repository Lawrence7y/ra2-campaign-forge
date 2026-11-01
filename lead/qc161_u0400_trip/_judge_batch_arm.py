# -*- coding: utf-8 -*-
"""_judge_batch_arm.py — 批次逐臂通道确认：探针判器对真实发射产物跑 C/S 系列。
用法: python _judge_batch_arm.py <out_dir>
判据=裁决§五短窗四项：投递结果(C3/C4)、截图有效性(S1/S2)、哨兵可读性(C7)、载体身份(C1/C8 清扫面)。
"""
import json
import sys
import importlib.util
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
PROBE = ROOT / "lead/qc161_u0400_trip/_x_channel_probe_20261027.py"

spec = importlib.util.spec_from_file_location("__probe_j", PROBE)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

out = Path(sys.argv[1])
rec = json.loads((out / "_rec.json").read_text(encoding="utf-8"))
print("arm=%s verdict=%s exited=%s exit_kind=%s" % (
    rec.get("trip_tag"), rec.get("verdict"), rec.get("exited"), rec.get("exit_kind")))
res = P.judge_artifacts(out, rec)
bad = P.print_results(res)
print("JUDGE: red=%d ⇒ %s" % (bad, "CHANNEL-CONFIRMED" if bad == 0 else "CHANNEL-FAIL"))
sys.exit(0 if bad == 0 else 1)
