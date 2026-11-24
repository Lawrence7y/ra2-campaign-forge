# _fdv_fingerprint.py — 复核员指纹核验：十件被核对象 SHA256 + 字节数
# 用法: python -I -X utf8 _fdv_fingerprint.py <out_path>
import hashlib, os, sys

BASE = r"D:/Project/ra2-campaign-forge"
FILES = [
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/fp_pattern_20261109/FP_PATTERN_ANALYSIS.md",
    "lead/fp_pattern_20261109/_fp_recompute_out.json",
    "lead/dg_adversarial_20261109/_dga_adversarial_out.json",
    "lead/dg_adversarial_20261109/DG_ADVERSARIAL.md",
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/dneg_generative_20261109/_dg_core.py",
    "lead/dneg_generative_20261109/DNEG_GENERATIVE.md",
    "lead/h5_governance_20261109/_h5_pasteable.py",
]

out_path = sys.argv[1] if len(sys.argv) > 1 else None
lines = []
for rel in FILES:
    p = os.path.join(BASE, rel)
    with open(p, "rb") as f:
        b = f.read()
    h = hashlib.sha256(b).hexdigest()
    lines.append("[%s]\n被核对象 SHA256 = %s，字节数 = %d" % (rel, h, len(b)))

text = "\n".join(lines)
print(text)
if out_path:
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
