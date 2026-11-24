# -*- coding: utf-8 -*-
# _c7v_fp.py — 复核员独立实算：①三产物指纹 ②编排方十件基线 ③写域全文件伪造ID扫描
import hashlib, os, re, sys

ROOT = r"D:\Project\ra2-campaign-forge"
SLOT = os.path.join(ROOT, "lead", "c07_slot_20261109")

PRODUCTS = [
    "_c7_SLOT_PREP.md",
    "_c7_record_template.json",
    "_c7_selfcheck.py",
]

BASELINE = {
    r"lead\pending_factpack_20261108\_fp_N10-C07_Q6.md": "1b63256d22ee367eecf984f8661c9256222afce37582f6bc79711b436d03a450",
    r"lead\pending_factpack_20261108\_fp_INDEX.md": "e827d5ca784f0a194ba3ed509a89b2502ecb14ad7c7830f4a1f09719a74944e2",
    r"lead\d13d14_cards_20261108\DECISION_QUESTIONS.md": "0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f",
    r"lead\perf_repair_n11_20261108\PERF_REPAIR_HANDOFF.md": "7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0",
    r"lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md": "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c",
    r"lead\direction_ruling_20261108\RULING_DIRECTION.md": "0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653",
    r"lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md": "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801",
    r"lead\b2b_yi_supersede_20261108\YI_SUPERSEDE_JIA_BINDING.md": "255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b",
    r"lead\PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
    r"lead\GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
}

def fp(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n

print("== A. 三产物指纹（被核对象）==")
for name in PRODUCTS:
    p = os.path.join(SLOT, name)
    d, n = fp(p)
    print("%s | sha256=%s | bytes=%d" % (name, d, n))

print("== B. 编排方十件基线独立实算 ==")
ok = 0
for rel, expect in BASELINE.items():
    p = os.path.join(ROOT, rel)
    d, n = fp(p)
    m = "MATCH" if d == expect else "MISMATCH(expect=%s)" % expect
    if d == expect:
        ok += 1
    print("%s | bytes=%d | %s" % (rel, n, m))
print("baseline match = %d/10" % ok)

print("== C. 写域伪造ID扫描（所有文件）==")
PAT = [
    ("sess_", re.compile(r"sess[_-][A-Za-z0-9_.\-]{6,}")),
    ("uuid", re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")),
    ("dwfrun", re.compile(r"dwfrun")),
    ("longhex", re.compile(r"[0-9a-f]{24,}")),
    ("runid-date", re.compile(r"2026\d{4}-\d{2,}")),
    ("sess-like-prefix", re.compile(r"\brun_[A-Za-z0-9]{8,}")),
]
PLACEHOLDER_RE = re.compile(r"<[^<>]{1,60}>")

def classify(s):
    # 全大写或含非hex、或明显占位符样式的按占位/字面处理
    return None

for fn in sorted(os.listdir(SLOT)):
    p = os.path.join(SLOT, fn)
    if not os.path.isfile(p):
        continue
    with open(p, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", "replace")
    lines = text.splitlines()
    hits = []
    for i, ln in enumerate(lines, 1):
        for tag, pat in PAT:
            for m in pat.finditer(ln):
                s = m.group(0)
                # 占位符尖括号包裹 → 占位符
                if PLACEHOLDER_RE.fullmatch(s):
                    kind = "PLACEHOLDER"
                elif re.fullmatch(r"[0-9a-f]{24,}", s):
                    kind = "HEXSTRING"  # 指纹行上下文另行判断
                elif s.isupper() or not re.search(r"[0-9a-f]{8}", s.lower()[:8]):
                    kind = "LITERAL?"
                else:
                    kind = "SUSPICIOUS"
                # 脱敏：仅保留前6后4
                masked = (s[:6] + "…" + s[-4:] + " len=%d" % len(s)) if len(s) > 14 else s
                ctx = ln.strip()
                if len(ctx) > 100:
                    j = ctx.find(s)
                    a = max(0, j - 25)
                    ctx = ctx[a:a + 100]
                hits.append((tag, kind, masked, i, ctx))
    if hits:
        print("-- %s (%d hits)" % (fn, len(hits)))
        for tag, kind, masked, i, ctx in hits:
            print("   L%-5d [%s/%s] %s | ctx: %s" % (i, tag, kind, masked, ctx))
    else:
        print("-- %s (0 hits)" % fn)

print("== D. 写域文件清单与字节数 ==")
for fn in sorted(os.listdir(SLOT)):
    p = os.path.join(SLOT, fn)
    if os.path.isfile(p):
        print("%s %d bytes" % (fn, os.path.getsize(p)))
