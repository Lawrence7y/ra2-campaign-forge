# _verify_fp.py — 复核员指纹实算（只读）
import hashlib, os, sys

BASE = "D:/Project/ra2-campaign-forge"

orch = [
    "lead/direction_ruling_20261108/RULING_DIRECTION.md",
    "lead/r2_unclosed_cd_20261108/CD_BREAKPOINTS.md",
    "lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
    "lead/dtrigger_round2_20261107/_dC_recompute.py",
    "lead/dtrigger_round2_20261107/_dC_out.txt",
    "lead/r2_final_grade_20261108/R2_FINAL_GRADE.md",
]

print("== 六件编排方指纹 ==")
for rel in orch:
    p = os.path.join(BASE, rel)
    b = open(p, "rb").read()
    print(f"{rel}  sha256={hashlib.sha256(b).hexdigest()}  bytes={len(b)}")

print("== 被核回件三件交付 ==")
for name in ["_c97_scope_recheck.md", "_c97_check.py", "_c97_check_out.txt", "_c97_check_stderr.txt"]:
    p = os.path.join(BASE, "lead/c97_scope_recheck_20261108", name)
    b = open(p, "rb").read()
    print(f"{name}  sha256={hashlib.sha256(b).hexdigest()}  bytes={len(b)}")

print("== 被核回件 JSON 文本副本 ==")
p = os.path.join(BASE, "lead/c97_scope_recheck_20261108/_verify_reply.json")
b = open(p, "rb").read()
print(f"reply_json  sha256={hashlib.sha256(b).hexdigest()}  bytes={len(b)}")

print("== supplement 原件 ==")
p = os.path.join(BASE, "lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt")
b = open(p, "rb").read()
print(f"_dtrigger_supplement_out.txt  sha256={hashlib.sha256(b).hexdigest()}  bytes={len(b)}")
sys.exit(0)
