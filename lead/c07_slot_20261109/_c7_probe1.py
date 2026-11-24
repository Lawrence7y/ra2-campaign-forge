# -*- coding: utf-8 -*-
# _c7_probe1.py — C07 落点准备：全仓 ACCEPTANCE_RECORDS.json 现盘实查 + N-1 结构 + 编排方指纹复算
# 只读探查；写域外零改动。python -I -X utf8 运行。
import hashlib, json, os

ROOT = r"D:\Project\ra2-campaign-forge"

def sha256_bytes(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

print("== A. 全仓 rglob ACCEPTANCE_RECORDS.json（os.walk 复查，不采信编排方转述） ==")
hits = []
dirs_visited = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirs_visited += 1
    for fn in filenames:
        if fn == "ACCEPTANCE_RECORDS.json":
            p = os.path.join(dirpath, fn)
            try:
                n = os.path.getsize(p)
                h = sha256_bytes(p)
            except OSError as e:
                n, h = -1, "ERR:" + str(e)
            hits.append((os.path.relpath(p, ROOT).replace("\\", "/"), n, h))
for rel, n, h in sorted(hits):
    print("HIT %s bytes=%d sha256=%s" % (rel, n, h))
print("dirsVisited=%d" % dirs_visited)

print()
print("== B. NEXT:23 指定物理路径是否存在 ==")
p_next = os.path.join(ROOT, "lead", "nextstep_plan_20261106", "ACCEPTANCE_RECORDS.json")
print("lead/nextstep_plan_20261106/ACCEPTANCE_RECORDS.json exists =", os.path.exists(p_next))

print()
print("== C. N-1 现存件结构 lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json ==")
p_n1 = os.path.join(ROOT, "lead", "a_residual_n1_20261108", "ACCEPTANCE_RECORDS.json")
with open(p_n1, "rb") as f:
    raw = f.read()
print("bytes=%d sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))
obj = json.loads(raw.decode("utf-8"))
print("topType =", type(obj).__name__)
if isinstance(obj, dict):
    for k in obj.keys():
        v = obj[k]
        if isinstance(v, (str, int, float, bool)) or v is None:
            print("  %s = %r" % (k, v))
        else:
            print("  %s : <type %s, len %s>" % (k, type(v).__name__, len(v) if hasattr(v, "__len__") else "?"))
recs = obj.get("records", []) if isinstance(obj, dict) else []
print("recordsCount =", len(recs))
for i, r in enumerate(recs):
    if isinstance(r, dict):
        print("  rec[%d].itemId = %r" % (i, r.get("itemId")))
        print("  rec[%d].reviewerRole = %r" % (i, r.get("reviewerRole")))
        print("  rec[%d].reviewerSessionId = %r" % (i, r.get("reviewerSessionId")))
        print("  rec[%d].sourceTaskId = %r" % (i, r.get("sourceTaskId")))
        print("  rec[%d].keys = %s" % (i, sorted(r.keys())))
    else:
        print("  rec[%d] : <type %s>" % (i, type(r).__name__))

print()
print("== D. 旧件 lead/a_residual_20261106/ACCEPTANCE_RECORDS.json 结构摘要 ==")
p_old = os.path.join(ROOT, "lead", "a_residual_20261106", "ACCEPTANCE_RECORDS.json")
with open(p_old, "rb") as f:
    raw3 = f.read()
print("bytes=%d sha256=%s" % (len(raw3), hashlib.sha256(raw3).hexdigest()))
obj3 = json.loads(raw3.decode("utf-8"))
print("topType =", type(obj3).__name__)
if isinstance(obj3, dict):
    print("topKeys =", list(obj3.keys()))
    recs3 = obj3.get("records", [])
    print("recordsCount =", len(recs3))
    for i, r in enumerate(recs3[:6]):
        if isinstance(r, dict):
            print("  rec[%d].itemId = %r reviewerSessionId=%r sourceTaskId=%r" % (
                i, r.get("itemId"), r.get("reviewerSessionId"), r.get("sourceTaskId")))
    if len(recs3) > 6:
        print("  ... 共 %d 条" % len(recs3))

print()
print("== E. 编排方指纹复算（hashlib，10 件） ==")
fp = {
    "lead/pending_factpack_20261108/_fp_N10-C07_Q6.md": "1b63256d22ee367eecf984f8661c9256222afce37582f6bc79711b436d03a450",
    "lead/pending_factpack_20261108/_fp_INDEX.md": "e827d5ca784f0a194ba3ed509a89b2502ecb14ad7c7830f4a1f09719a74944e2",
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md": "0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f",
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md": "7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md": "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c",
    "lead/direction_ruling_20261108/RULING_DIRECTION.md": "0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653",
    "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md": "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801",
    "lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md": "255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b",
    "lead/PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
    "lead/GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
}
ok = 0
for rel, exp in sorted(fp.items()):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as f:
            data = f.read()
        got = hashlib.sha256(data).hexdigest()
        m = "MATCH" if got == exp else "MISMATCH"
        if m == "MATCH":
            ok += 1
        print("%-64s bytes=%7d %s" % (rel, len(data), m))
    except OSError as e:
        print("%-64s ERROR %s" % (rel, e))
print("fingerprintMatch=%d/%d" % (ok, len(fp)))

print()
print("== F. 本写域现状 ==")
p_self = os.path.join(ROOT, "lead", "c07_slot_20261109")
if os.path.isdir(p_self):
    for fn in sorted(os.listdir(p_self)):
        fp2 = os.path.join(p_self, fn)
        print("  EXIST %s bytes=%d" % (fn, os.path.getsize(fp2) if os.path.isfile(fp2) else -1))
else:
    print("  lead/c07_slot_20261109/ 尚不存在（本次由探针脚本落点创建）")
