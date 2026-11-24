# -*- coding: utf-8 -*-
"""_tpv_scan_identity.py — 复核员独立扫描三件 _tp_ 产出件：
是否含真实身份值（运行态 sessionId 形、合成样本值、任务号、64hex）。
区分：文件指纹 64hex（绑定行，允许）vs 身份值（不允许）。
"""
import re, os, hashlib

FILES = [
    r"D:\Project\ra2-campaign-forge\lead\c07_truth_protocol_20261109\_tp_C07_TRUTH_PROTOCOL.md",
    r"D:\Project\ra2-campaign-forge\lead\c07_truth_protocol_20261109\_tp_TP_ATTESTATION_TEMPLATE.md",
    r"D:\Project\ra2-campaign-forge\lead\c07_truth_protocol_20261109\_tp_TP_VERIFIER_CHECKLIST.md",
]

SESSION_REAL = re.compile(r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")
SESSION_SHAPE = re.compile(r"sess_dwf-dwfrun-<UUID>-actor_<n>_<m>")
UUID_SEG = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
TASK_ID = re.compile(r"TASK-\d{8}")
HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
SYNTH = re.compile(r"deadbeef|0123456789ab", re.IGNORECASE)

for fp in FILES:
    with open(fp, "rb") as f:
        data = f.read()
    text = data.decode("utf-8")
    lines = text.splitlines()
    print("== %s (%d B)" % (os.path.basename(fp), len(data)))
    for name, rx in (("真实形sessionId", SESSION_REAL), ("形制占位描述", SESSION_SHAPE),
                     ("UUID段", UUID_SEG), ("TASK号", TASK_ID), ("64hex", HEX64), ("合成样本痕迹", SYNTH)):
        n = 0
        samples = []
        for i, ln in enumerate(lines, 1):
            for m in rx.finditer(ln):
                n += 1
                if len(samples) < 4:
                    frag = ln[max(0, m.start()-30):m.end()+20]
                    samples.append("L%d …%s…" % (i, frag))
        print("  %-14s 命中=%d %s" % (name, n, ("｜" + " ｜ ".join(samples)) if samples else ""))
    print()
