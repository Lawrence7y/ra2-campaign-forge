# _verify_b_morehash.py — N-9 / SED / DQ 指纹定位
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"

def sha(p):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b); n += len(b)
    return h.hexdigest(), n

# 1) 已知候选
cands = [
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\d13d14_cards_20261108\DECISION_QUESTIONS.md",
]
for rel in cands:
    p = os.path.join(BASE, rel)
    if os.path.isfile(p):
        d, n = sha(p)
        print(f"[OK] {rel}\n     sha256={d}\n     bytes={n}")
    else:
        print(f"[MISS] {rel}")

# 2) 全 lead 树内找 sha256 前缀 5b933fe2（N-9 自述值）与 ed8951e7（SED 自述值）
want = ("5b933fe2", "ed8951e7")
lead = os.path.join(BASE, "lead")
hits = 0
for root, dirs, files in os.walk(lead):
    for fn in files:
        if not fn.lower().endswith((".md", ".txt", ".py")):
            continue
        p = os.path.join(root, fn)
        try:
            d, n = sha(p)
        except OSError:
            continue
        if d.startswith(want):
            print(f"[HIT] {os.path.relpath(p, BASE)}\n     sha256={d}\n     bytes={n}")
            hits += 1
print(f"[DONE] prefix hits = {hits}")
