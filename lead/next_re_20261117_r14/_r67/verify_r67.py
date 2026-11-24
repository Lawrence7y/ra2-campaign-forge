# -*- coding: utf-8 -*-
# R17-R67 独立复算：用「先按字节大小分组、同大小再逐字节比对」的算法，
# 完全不经 sha256 分簇，独立求唯一内容簇数与唯一内容总字节。
# 这是对 dedup_corpus.py 的第二实现交叉验证（§2.71 口径）。
# 正控：构造 3 文件（2 同、1 改 1 字节）必须判 2 簇。
# 负控：把已知不同的两个大文件强制塞进同组，必须判 2 簇（不是按大小误并）。
import os, sys, csv, io, hashlib, tempfile, shutil, time

ROOT = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(ROOT, r"next_re_20261117_r14")
TSV = os.path.join(R14, r"R17_R101_TIER_FINAL_4417\tier_final_4417.tsv")
SRC = os.path.join(R14, r"_r67\unique_content_4417.tsv")

buf = []
def P(s=""):
    print(s); buf.append(s)

fails = []
def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c: fails.append(n)

def same_bytes(p, q, chunk=1 << 22):
    if os.path.getsize(p) != os.path.getsize(q):
        return False
    with open(p, "rb") as a, open(q, "rb") as b:
        while True:
            x = a.read(chunk); y = b.read(chunk)
            if x != y: return False
            if not x: return True

def cluster_by_content(paths):
    """按大小分组 -> 组内逐字节比对 -> 返回簇列表；完全不用哈希。"""
    bysize = {}
    for p in paths:
        bysize.setdefault(os.path.getsize(p), []).append(p)
    clusters = []
    for sz, group in bysize.items():
        reps = []           # 该大小下的代表文件
        members = []        # 与 reps 对齐的成员列表
        for p in group:
            for i, r in enumerate(reps):
                if same_bytes(p, r):
                    members[i].append(p)
                    break
            else:
                reps.append(p); members.append([p])
        clusters.extend(members)
    return clusters

rows = list(csv.DictReader(io.open(TSV, encoding="utf-8"), delimiter="\t"))
P("清单 %d 行" % len(rows))
paths = [os.path.join(ROOT, r["rel"]) for r in rows]
P("全部存在？ %s" % all(os.path.exists(p) for p in paths))

# ---------- 正控 / 负控 ----------
P("")
P("[控] 逐字节比对算法本身")
tmp = tempfile.mkdtemp(prefix="r67_v2_")
try:
    s = os.path.join(tmp, "s")
    shutil.copyfile(TSV, s)
    a = os.path.join(tmp, "a"); b = os.path.join(tmp, "b"); c = os.path.join(tmp, "c")
    shutil.copyfile(s, a); shutil.copyfile(s, b)
    bb = bytearray(open(s, "rb").read()); bb[-1] ^= 0xFF
    open(c, "wb").write(bytes(bb))
    cl = cluster_by_content([a, b, c])
    P("  3 文件（2 同 + 1 改末字节）-> %d 簇，簇大小 %s"
      % (len(cl), sorted(len(x) for x in cl)))
    ck("正控 3 文件判 2 簇", len(cl) == 2, str(len(cl)))
    ck("正控 复制件被并簇", sorted(len(x) for x in cl) == [1, 2])
    ck("负控 同字节数但内容不同不并簇", all(len(x) == 1 for x in cl if c in x))
    # 负控二：同大小前缀相同、仅末字节不同 —— 必须不并簇
    ck("负控 末字节差 0xFF 也能抓出", not same_bytes(a, c))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---------- 全量 ----------
P("")
P("[1] 全量独立分簇（按大小 -> 逐字节比对）")
t0 = time.time()
clusters = cluster_by_content(paths)
el = time.time() - t0
uniq_n = len(clusters)
uniq_bytes = sum(os.path.getsize(c[0]) for c in clusters)
dup_n = len(paths) - uniq_n
total = sum(os.path.getsize(p) for p in paths)
P("  用时 %.1f s" % el)
P("  唯一簇数 = %d" % uniq_n)
P("  唯一内容总字节 = %d" % uniq_bytes)
P("  重复件数 = %d ; 重复字节 = %d ; 总字节 = %d" % (dup_n, total - uniq_bytes, total))

# ---------- 与第一实现对照 ----------
P("")
P("[2] 与 dedup_corpus.py 的 sha256 结果对照（两份实现互证）")
ck("独立实现 总字节 = 754,228,404", total == 754228404, str(total))
ck("独立实现 唯一簇数 = 4087", uniq_n == 4087, str(uniq_n))
ck("独立实现 唯一内容字节 = 615,909,180", uniq_bytes == 615909180, str(uniq_bytes))
ck("独立实现 重复件数 = 330", dup_n == 330, str(dup_n))
ck("独立实现 重复字节 = 138,319,224", total - uniq_bytes == 138319224,
   str(total - uniq_bytes))

# ---------- 与落盘清单对照 ----------
P("")
P("[3] 与 unique_content_4417.tsv 落盘清单对照（逐行簇一致性）")
back = list(csv.DictReader(io.open(SRC, encoding="utf-8"), delimiter="\t"))
ck("清单行数 = 4417", len(back) == 4417, str(len(back)))
ck("清单 sum(bytes) = 754,228,404",
   sum(int(r["bytes"]) for r in back) == 754228404)
ck("清单 sum(decl_bytes) = 737,517,286",
   sum(int(r["decl_bytes"]) for r in back) == 737517286)
ck("清单唯一 sha256 数 = 4087", len({r["sha256"] for r in back}) == 4087)
ck("清单簇大小平方和 = 逐行 cluster_size 之和（自证列语义）",
   sum(int(r["cluster_size"]) for r in back) ==
   sum(int(r["cluster_size"]) ** 2 for r in back if r["cluster_rep"] == r["rel"]),
   "sum=%d 平方和=%d" % (sum(int(r["cluster_size"]) for r in back),
                        sum(int(r["cluster_size"]) ** 2 for r in back
                            if r["cluster_rep"] == r["rel"])))
ck("清单按簇去重后 cluster_size 之和 = 4417",
   sum(int(r["cluster_size"]) for r in back if r["cluster_rep"] == r["rel"]) == 4417,
   str(sum(int(r["cluster_size"]) for r in back if r["cluster_rep"] == r["rel"])))

# 逐行：清单里的 cluster_rep 分组，必须与独立实现的逐字节分簇一一对应
byrephash = {}
for r in back:
    byrephash.setdefault(r["sha256"], set()).add(r["rel"])
indep = {}
for c in clusters:
    key = frozenset(os.path.relpath(p, ROOT).replace("\\", "/") for p in c)
    indep[key] = True
declared = {}
for sha, rels in byrephash.items():
    declared[frozenset(rels)] = sha
P("  独立实现的簇集合 大小 = %d；清单声明的簇集合 大小 = %d"
  % (len(indep), len(declared)))
ck("两份实现的簇集合完全相同（frozenset 逐簇比对）",
   set(indep.keys()) == set(declared.keys()))
ck("簇数一致（%d）" % uniq_n, len(indep) == len(declared) == uniq_n)

# 重复簇数与 Top 明细一致性
dup_decl = [(sha, rels) for sha, rels in byrephash.items() if len(rels) > 1]
P("  含重复的簇：清单 %d" % len(dup_decl))
ck("含重复簇数 = 184", len(dup_decl) == 184, str(len(dup_decl)))
ck("簇大小分布 2件/3件/>=4件 = 140/22/22",
   (sum(1 for _, r in dup_decl if len(r) == 2),
    sum(1 for _, r in dup_decl if len(r) == 3),
    sum(1 for _, r in dup_decl if len(r) >= 4)) == (140, 22, 22),
   str((sum(1 for _, r in dup_decl if len(r) == 2),
        sum(1 for _, r in dup_decl if len(r) == 3),
        sum(1 for _, r in dup_decl if len(r) >= 4))))
ck("最大簇 42 件（except.txt 备份族）",
   max(len(r) for _, r in dup_decl) == 42,
   str(max(len(r) for _, r in dup_decl)))
ck("单簇最大浪费字节 = 73,899,177（_oo_disasm_out.txt 双份）",
   max(os.path.getsize(os.path.join(ROOT, next(iter(r)))) * (len(r) - 1)
       for _, r in dup_decl) == 73899177,
   str(max(os.path.getsize(os.path.join(ROOT, next(iter(r)))) * (len(r) - 1)
           for _, r in dup_decl)))

# 清单里四份 calls 是否各自成簇（独立实现必须同样判 1）
CALLS4_REL = [
    "next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json",
    "next_re_20261117_r14/S21_DIRECT/_audit/EVIDENCE/scan_mine.json",
    "next_re_20261117_r14/S09_KPROVED7/_audit/EVIDENCE/e8_sites_audit.json",
    "next_re_20261117_r14/S08_KPROVED2/_audit/EVIDENCE/sweep.json",
]
d_by_rel = {r["rel"]: r for r in back}
ck("四份 calls 文件在清单里 cluster_size 全 = 1（各自成簇）",
   all(int(d_by_rel[k]["cluster_size"]) == 1 for k in CALLS4_REL),
   str([int(d_by_rel[k]["cluster_size"]) for k in CALLS4_REL]))
ck("四份 calls 文件各自 cluster_rep = 自己",
   all(d_by_rel[k]["cluster_rep"] == k for k in CALLS4_REL))
ck("四份 calls 的 sha256 两两不同",
   len({d_by_rel[k]["sha256"] for k in CALLS4_REL}) == 4)

P("")
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))
P("")
P("[附] 三口径并列（引用时必须带口径，纪律 31）")
P("  A 清单净额口径（§2.71 / F24 现行）：4,417 件 / 737,517,286 B")
P("  B 磁盘口径（实测 getsize 全量）：     4,417 件 / 754,228,404 B")
P("  C SHA256 唯一内容（磁盘侧）：         4,087 簇 / 615,909,180 B")
P("  D SHA256 唯一内容（清单侧）：         4,087 簇 / 599,198,062 B")
P("  E 内容等值唯一（跨序列化再扣 3 份）：  4,084 簇 / 611,813,919 B")
P("  重复侧一致：330 件 / 138,319,224 B（B 与 D 两口径下重复字节相同）")
open(os.path.join(R14, r"_r67\verify_r67.log"), "w", encoding="utf-8",
     newline="\n").write("\n".join(buf) + "\n")
sys.exit(0 if not fails else 1)
