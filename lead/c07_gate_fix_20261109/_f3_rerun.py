# -*- coding: utf-8 -*-
# _f3_rerun.py — 对指定门禁批量实跑 36 攻样本 + 未填模板基线，转录全文与 exit code。
# 用法：python -I -X utf8 _f3_rerun.py <门禁脚本绝对路径> <转录输出绝对路径> <摘要JSON绝对路径>
# 只读被测门禁与样本；只写本写域的两个输出文件。
import hashlib
import json
import os
import subprocess
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
SDIR = os.path.join(ROOT, "lead", "c07_gate_audit_20261109", "_c7a_samples")
TPL = os.path.join(ROOT, "lead", "c07_slot_20261109", "_c7_record_template.json")


def main(argv):
    if len(argv) < 4:
        print("usage: _f3_rerun.py <gate.py> <transcript.out> <summary.json>")
        return 2
    gate, out_tx, out_js = argv[1], argv[2], argv[3]
    with open(gate, "rb") as f:
        graw = f.read()
    targets = [os.path.join(SDIR, n) for n in sorted(
        x for x in os.listdir(SDIR) if x.endswith(".json"))]
    targets.append(TPL)  # 基线：未填模板
    lines = []
    summary = {}
    lines.append("== RERUN transcript ==")
    lines.append("gate=%s sha256=%s bytes=%d" % (
        gate, hashlib.sha256(graw).hexdigest(), len(graw)))
    lines.append("targets=%d" % len(targets))
    for t in targets:
        proc = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", gate, t],
            capture_output=True, timeout=120)
        out = proc.stdout.decode("utf-8", errors="replace")
        err = proc.stderr.decode("utf-8", errors="replace")
        name = os.path.basename(t)
        summary[name] = proc.returncode
        lines.append("===SAMPLE %s exit=%d===" % (name, proc.returncode))
        lines.append(out.rstrip("\n"))
        if err.strip():
            lines.append("[stderr] " + err.rstrip("\n"))
    with open(out_tx, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    with open(out_js, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("wrote %s (%d samples) and %s" % (out_tx, len(targets), out_js))
    print("exits: " + " ".join("%s=%d" % (k[:-5], v) for k, v in sorted(summary.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
