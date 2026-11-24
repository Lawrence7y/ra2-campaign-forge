# _spec2_fp_all.py — 锚与双件盘点脚本（本轮新增，写域内）
# 1) 枚举 6 个交付写域 + 本锚写域全部文件，实算 sha256/字节数
# 2) 用全部实算指纹在 lead/ 全域做一次跨域检索（单遍扫描，声明边界）
# 3) 复核矩阵域五件 _m_* 升序聚合指纹、台账件指纹
import hashlib, os, sys

ROOT = r"D:\Project\ra2-campaign-forge"
LEAD = os.path.join(ROOT, "lead")
DOMAINS = [
    "a_residual_n1_20261108",
    "perf_repair_n11_20261108",
    "d13d14_cards_20261108",
    "matrix_binding_20261108",
    "slowframe_r3_20261108",
    "criteria_r3_verify_20261108",
    "deliverable_anchor_20261108",
]
SKIP_DIRS = {"__pycache__"}

def sha256_file(p):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n

records = []  # (relpath, sha, bytes)
for d in DOMAINS:
    base = os.path.join(LEAD, d)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
        for fn in sorted(filenames):
            p = os.path.join(dirpath, fn)
            try:
                s, n = sha256_file(p)
            except OSError as e:
                print("READFAIL", p, e)
                continue
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            records.append((rel, s, n))

print("=== PART1 fingerprints (per file) ===")
for rel, s, n in records:
    print(f"{rel}|{s}|{n}")

print("=== PART2 matrix five _m_* ascending-name concatenation ===")
mfiles = sorted([
    os.path.join(LEAD, "matrix_binding_20261108", f) for f in
    ["_m_CHAIN_VERIFY_20261108.md", "_m_DECISION_POINTS_20261108.md",
     "_m_MATRIX_DIFF_20261108.md", "_m_rebuild.py", "_m_rebuild_out.txt"]
])
h = hashlib.sha256()
tot = 0
for p in mfiles:
    with open(p, "rb") as f:
        b = f.read()
    h.update(b)
    tot += len(b)
print(f"agg5_ascending|{h.hexdigest()}|{tot}")

print("=== PART3 ledger files ===")
for f in ["PENDING_DECISIONS.md", "GOAL_THREE_TARGETS_20261018.md"]:
    p = os.path.join(LEAD, f)
    s, n = sha256_file(p)
    print(f"{f}|{s}|{n}")

print("=== PART4 cross-domain search of all PART1 hashes over lead/ (files <2MB) ===")
hashes = {}
for rel, s, n in records:
    hashes[s] = rel
agg_s = h.hexdigest()
hashes[agg_s] = "AGG5(ascending concat)"

scanned = 0
skipped_big = 0
skipped_err = 0
hits = {}  # hash -> list of (rel, lineno)
for dirpath, dirnames, filenames in os.walk(LEAD):
    dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and x != ".mimosa"]
    for fn in sorted(filenames):
        p = os.path.join(dirpath, fn)
        try:
            sz = os.path.getsize(p)
        except OSError:
            skipped_err += 1
            continue
        if sz > 2 * 1024 * 1024:
            skipped_big += 1
            continue
        try:
            with open(p, "rb") as f:
                data = f.read()
        except OSError:
            skipped_err += 1
            continue
        scanned += 1
        for s in hashes:
            if s.encode("ascii") in data:
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                # line numbers
                lns = []
                start = 0
                needle = s.encode("ascii")
                while True:
                    i = data.find(needle, start)
                    if i < 0:
                        break
                    lns.append(data.count(b"\n", 0, i) + 1)
                    start = i + 1
                    if len(lns) >= 6:
                        break
                hits.setdefault(s, []).append((rel, lns))

print(f"# scanned={scanned} skipped_big={skipped_big} skipped_err={skipped_err}")
for s in sorted(hashes):
    hh = hits.get(s)
    if hh:
        print(f"HIT {hashes[s]} | {s}")
        for rel, lns in hh:
            print(f"    -> {rel} lines={lns}")
    else:
        print(f"NOHIT {hashes[s]} | {s}")
print("done")
