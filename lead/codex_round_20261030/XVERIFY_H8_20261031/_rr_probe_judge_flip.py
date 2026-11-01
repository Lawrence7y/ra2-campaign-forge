# -*- coding: utf-8 -*-
"""RR-P7：母本判档器 vs 副本判档器 —— 同一输入的**退出码翻转**（Y-1 复验）。

自建只读副本（不改动前任/他人合成的 synth_*，保链上取证）：
  rr_fx_ok_v1sha    = synth_ok，harness_sha16 改回 v1（e29a9a07e17fdd7f）
  rr_fx_ok_v2sha    = synth_ok，harness_sha16 = v2（dd5459fe0cf3461c）
  rr_fx_overrun_v2  = synth_overrun（v2 sha）
  rr_fx_timeout_v2  = synth_timeout（v2 sha）
两判档器都跑，只比 EXIT 与 harness 白名单条目。零真机。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = Path(__file__).resolve().parent
MASTER_J = ROOT / "lead/qc161_u0400_trip/_judge_l1_20261023.py"
COPY_J = ROOT / "lead/goal1_harness8_20261031/_judge_h8_20261031.py"
V1_SHA = "e29a9a07e17fdd7f"
V2_SHA = "dd5459fe0cf3461c"


def mkfx(src_name, dst_name, sha):
    d = HERE / dst_name
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(HERE / src_name, d)
    lr = json.loads((d / "_launch_result.json").read_text(encoding="utf-8"))
    lr["harness_sha16"] = sha
    (d / "_launch_result.json").write_text(
        json.dumps(lr, ensure_ascii=False, indent=2), encoding="utf-8")
    return d


def run(judge, fx):
    r = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(judge),
                        "--trip-dir", str(fx)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    lines = r.stdout.splitlines()
    wl = [l.strip() for l in lines if "harness 在已知清单内" in l]
    sc = [l.strip() for l in lines if "设计内短路" in l or "既非短路集" in l]
    return {"exit": r.returncode, "whitelist_line": wl[:1], "shortcircuit_line": sc[:2],
            "verdict_line": [l.strip() for l in lines if l.strip().startswith("w0.verdict")][:1]}


def main():
    res = {"fixtures": {}, "runs": {}}
    fx = {
        "ok_v1sha": mkfx("synth_ok", "rr_fx_ok_v1sha", V1_SHA),
        "ok_v2sha": mkfx("synth_ok", "rr_fx_ok_v2sha", V2_SHA),
        "overrun_v2sha": mkfx("synth_overrun", "rr_fx_overrun_v2sha", V2_SHA),
        "timeout_v2sha": mkfx("synth_timeout", "rr_fx_timeout_v2sha", V2_SHA),
        "overrun_v1sha": mkfx("synth_overrun", "rr_fx_overrun_v1sha", V1_SHA),
        "timeout_v1sha": mkfx("synth_timeout", "rr_fx_timeout_v1sha", V1_SHA),
    }
    for k, p in fx.items():
        res["fixtures"][k] = str(p)
    for k, p in fx.items():
        res["runs"][k] = {"master_judge": run(MASTER_J, p),
                          "copy_judge": run(COPY_J, p)}
    flip = {}
    for k in fx:
        flip[k] = {"master_exit": res["runs"][k]["master_judge"]["exit"],
                   "copy_exit": res["runs"][k]["copy_judge"]["exit"],
                   "changed": res["runs"][k]["master_judge"]["exit"] !=
                             res["runs"][k]["copy_judge"]["exit"]}
    res["flip_table"] = flip
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    (HERE / "rr_p7_judge_flip.stdout.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
