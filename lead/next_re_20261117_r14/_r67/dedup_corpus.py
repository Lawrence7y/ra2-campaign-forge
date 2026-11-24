# -*- coding: utf-8 -*-
# R17-R67 实测：唯一内容体量（SHA256 内容指纹去重）全量实测
# 独立实现，不 import 卡内代码。正控 + 负控齐备。
#
# 正控 P1：sha256 实现对照已知向量
# 正控 P2：4 份已知 68,253 对 calls 文件 —— 清单字节 vs 磁盘字节、四份 calls 内容等值
# 正控 P3：字节级复制件必须并入同一簇（去重器不把相同内容算两份）
# 负控 N1：改动 1 字节的复制件必须落不同簇（去重器不把不同内容算一份）
# 负控 N2：清单 bytes 列与实际 getsize 必须逐行相等（否则全量统计前提不成立）
import os, sys, csv, json, hashlib, io, time, tempfile, shutil

ROOT = r"D:\Project\ra2-campaign-forge\lead"
TSV = os.path.join(ROOT, r"next_re_20261117_r14\R17_R101_TIER_FINAL_4417\tier_final_4417.tsv")
OUTDIR = os.path.join(ROOT, r"next_re_20261117_r14\_r67")
OUT = os.path.join(OUTDIR, "unique_content_4417.tsv")
LOG = os.path.join(OUTDIR, "run.log")

R14 = os.path.join(ROOT, r"next_re_20261117_r14")
CALLS4 = {
    "a2_sites.json": os.path.join(R14, r"D41_SUBST\_audit\EVIDENCE\a2_sites.json"),
    "scan_mine.json": os.path.join(R14, r"S21_DIRECT\_audit\EVIDENCE\scan_mine.json"),
    "e8_sites_audit.json": os.path.join(R14, r"S09_KPROVED7\_audit\EVIDENCE\e8_sites_audit.json"),
    "sweep.json": os.path.join(R14, r"S08_KPROVED2\_audit\EVIDENCE\sweep.json"),
}
CALLS4_A2 = CALLS4["a2_sites.json"]

_buf = []
def P(s=""):
    print(s)
    _buf.append(s)

def sha_file(p, chunk=1 << 22):
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n

fails = []
nck = [0]
def ck(name, cond, detail=""):
    nck[0] += 1
    P(("  PASS " if cond else "  FAIL ") + name + (("  " + detail) if detail else ""))
    if not cond:
        fails.append(name)

# ============ 正控 P1：sha256 已知向量 ============
P("=" * 78)
P("[P1] sha256 实现对照已知向量")
CK = {
    b"": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    b"abc": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    b"The quick brown fox jumps over the lazy dog":
        "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592",
}
for msg, exp in CK.items():
    got = hashlib.sha256(msg).hexdigest()
    ck("P1 vector len=%d" % len(msg), got == exp, got[:16])

# ============ 读权威清单 ============
P("")
P("=" * 78)
P("[0] 读权威清单 " + TSV)
raw = open(TSV, "rb").read()
P("  清单字节 %d / %s / CR=%d LF=%d" % (len(raw), hashlib.sha256(raw).hexdigest()[:16],
                                        raw.count(b"\r"), raw.count(b"\n")))
rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8")), delimiter="\t"))
P("  数据行 %d" % len(rows))
ck("清单行数 = 4417", len(rows) == 4417, str(len(rows)))
sum_decl = sum(int(r["bytes"]) for r in rows)
P("  sum(bytes) = %d" % sum_decl)
ck("清单 sum(bytes) = 737,517,286", sum_decl == 737517286, str(sum_decl))

# ============ 负控 N2：清单 bytes 列 vs 磁盘 getsize ============
P("")
P("=" * 78)
P("[N2 负控] 清单 bytes 列 vs 磁盘 getsize 逐行比对（统计前提）")
mismatch = []
missing = []
for r in rows:
    p = os.path.join(ROOT, r["rel"])
    if not os.path.exists(p):
        missing.append(r["rel"])
        continue
    sz = os.path.getsize(p)
    if sz != int(r["bytes"]):
        mismatch.append((r["rel"], int(r["bytes"]), sz))
P("  缺失 %d 件 / 字节不符 %d 件" % (len(missing), len(mismatch)))
for m in mismatch[:10]:
    P("    MISMATCH %s 清单=%d 磁盘=%d 差=%d" % (m[0], m[1], m[2], m[2] - m[1]))
for m in missing[:10]:
    P("    MISSING  " + m)
ck("N2 全部文件存在", len(missing) == 0, str(len(missing)))
ck("N2 字节不符件数 = 1（唯一例外 a2_sites.json 的净额行）",
   len(mismatch) == 1, str(len(mismatch)))
ck("N2 例外行确为 a2_sites.json",
   len(mismatch) == 1 and mismatch[0][0].endswith("D41_SUBST/_audit/EVIDENCE/a2_sites.json"),
   mismatch[0][0] if mismatch else "")

# ---- 净额行的口径必须独立闭合，不能只说「不一样」 ----
P("")
P("  [N2-b] 净额行口径闭合核算（§2.71 剔 bounds 段后残留的键足迹）")
a2raw = open(CALLS4_A2, "rb").read()
a2obj = json.loads(a2raw)
a2_c = json.dumps(a2obj["calls"])
a2_b = json.dumps(a2obj["bounds"])
a2_full = json.dumps(a2obj)
P("    磁盘 %d = dumps(全文) %d ? %s" % (len(a2raw), len(a2_full.encode()),
                                        len(a2raw) == len(a2_full.encode())))
P("    dumps(calls) = %d ; dumps(bounds) = %d ; 骨架 = %d"
  % (len(a2_c), len(a2_b), len(a2raw) - len(a2_c) - len(a2_b)))
P("    清单记 %d = len('\"calls\": ') + dumps(calls) = 9 + %d = %d ? %s"
  % (913237, len(a2_c), 9 + len(a2_c), 913237 == 9 + len(a2_c)))
P("    差额 %d = dumps(bounds) + 14 = %d + 14 = %d ? %s"
  % (len(a2raw) - 913237, len(a2_b), len(a2_b) + 14,
     len(a2raw) - 913237 == len(a2_b) + 14))
P("    ⇒ 骨架 23 = 10('{\"calls\": ') + 12(', \"bounds\": ') + 1('}')；"
  "净额把 14('{' + ', \"bounds\": ' + '}') 划给被剔的 bounds 段")
ck("N2-b 913,237 = 9 + dumps(calls)", 913237 == 9 + len(a2_c), str(len(a2_c)))
ck("N2-b 16,711,118 = dumps(bounds) + 14",
   len(a2raw) - 913237 == len(a2_b) + 14)
ck("N2-b 净额 + 差额 = 磁盘字节", 913237 + (len(a2raw) - 913237) == len(a2raw))
ck("N2-b 这解释了上轮未取得的『差 9 B』：9 = len('\"calls\": ')",
   913237 - len(a2_c) == 9)

# ============ 全量 SHA256 ============
P("")
P("=" * 78)
P("[1] 全部 4417 件逐一计算 SHA256（全量，非抽样）")
t0 = time.time()
recs = []
for i, r in enumerate(rows, 1):
    rel = r["rel"]
    p = os.path.join(ROOT, rel)
    h, n = sha_file(p)
    recs.append({"rel": rel, "bytes": n, "decl": int(r["bytes"]), "sha": h,
                 "source": r.get("source", ""), "why": r.get("why_content", "")})
    if i % 500 == 0:
        P("    ... %d/%d  %.1fs" % (i, len(rows), time.time() - t0))
el = time.time() - t0
disk_total = sum(y["bytes"] for y in recs)
P("  完成 %d 件，用时 %.1f s，实测读取（磁盘口径）%d B" % (len(recs), el, disk_total))
ck("实测读取总字节 = 737,517,286 + 16,711,118 = 754,228,404（磁盘口径）",
   disk_total == 754228404, str(disk_total))
ck("磁盘口径 - 清单口径 = 16,711,118（a2 净额行差额）",
   disk_total - 737517286 == 16711118, str(disk_total - 737517286))

# ============ 去重核心 ============
P("")
P("=" * 78)
P("[2] 按 SHA256 分簇（两个口径并列：磁盘口径 / 清单口径）")
clusters = {}
for x in recs:
    clusters.setdefault(x["sha"], []).append(x)
uniq_n = len(clusters)
uniq_bytes = sum(v[0]["bytes"] for v in clusters.values())
dup_n = len(recs) - uniq_n
dup_bytes = disk_total - uniq_bytes
# 清单口径（沿用 §2.71 / F24 的净额记账：a2 只记 913,237）
uniq_bytes_decl = sum(v[0]["decl"] for v in clusters.values())
dup_bytes_decl = 737517286 - uniq_bytes_decl
P("  【磁盘口径】唯一 SHA256 簇数 = %d；唯一内容总字节 = %d" % (uniq_n, uniq_bytes))
P("  【磁盘口径】重复文件数 = %d；重复字节总量 = %d" % (dup_n, dup_bytes))
P("  【磁盘口径】语料总字节 = %d（去重率 件 %.2f%% / 字节 %.2f%%）"
  % (disk_total, dup_n * 100.0 / len(recs), dup_bytes * 100.0 / disk_total))
P("  【清单口径】唯一内容总字节 = %d；重复字节总量 = %d；语料 737,517,286"
  % (uniq_bytes_decl, dup_bytes_decl))
P("  【两口径差】唯一字节：清单口径 − 磁盘口径 = %d（= −16,711,118，因为 a2 是唯一簇代表，"
  "磁盘计 17,624,355、清单计 913,237）；重复字节差 %d"
  % (uniq_bytes_decl - uniq_bytes, dup_bytes_decl - dup_bytes))
ck("唯一簇数 + 重复件数 = 4417", uniq_n + dup_n == 4417)
ck("磁盘口径：唯一 + 重复 = 总字节", uniq_bytes + dup_bytes == disk_total)
ck("清单口径：唯一 + 重复 = 737,517,286", uniq_bytes_decl + dup_bytes_decl == 737517286)
ck("两口径唯一字节差恰为 a2 净额差额", uniq_bytes_decl - uniq_bytes == -16711118)
ck("两口径重复字节相等（a2 未被复制，故重复侧不受净额影响）",
   dup_bytes == dup_bytes_decl)

# ============ 正控 P3 / 负控 N1：去重器本身的双向验证 ============
P("")
P("=" * 78)
P("[P3/N1] 去重器双向验证（在临时目录内构造，不触碰语料）")
tmp = tempfile.mkdtemp(prefix="r67_dedup_")
try:
    src = os.path.join(R14, r"R17_R101_TIER_FINAL_4417\tier_final_4417.tsv")
    a = os.path.join(tmp, "a.bin")
    b = os.path.join(tmp, "b.bin")          # 字节级复制件
    c = os.path.join(tmp, "c.bin")          # 改 1 字节
    shutil.copyfile(src, a)
    shutil.copyfile(src, b)
    buf = bytearray(open(src, "rb").read())
    buf[-1] ^= 0x01
    open(c, "wb").write(bytes(buf))
    hs = [sha_file(p) for p in (a, b, c)]
    P("    a=%s  b=%s  c=%s" % (hs[0][0][:16], hs[1][0][:16], hs[2][0][:16]))
    syn = [{"rel": os.path.basename(p), "bytes": hs[i][1], "sha": hs[i][0]}
           for i, p in enumerate((a, b, c))]
    cl = {}
    for x in syn:
        cl.setdefault(x["sha"], []).append(x)
    ck("P3 字节级复制件并入同一簇（3 件 -> 2 簇）", len(cl) == 2, "clusters=%d" % len(cl))
    ck("P3 复制件确被识别为重复（dup=1）", len(syn) - len(cl) == 1,
       "dup=%d" % (len(syn) - len(cl)))
    ck("N1 改 1 字节者落不同簇", len(cl[hs[2][0]]) == 1 and hs[2][0] not in (hs[0][0],))
    ck("N1 改 1 字节者字节数不变但哈希变",
       hs[2][1] == hs[0][1] and hs[2][0] != hs[0][0])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ============ 正控 P2：4 份已知 68,253 对 calls 文件 ============
P("")
P("=" * 78)
P("[P2] 4 份已知 68,253 对 calls 文件 —— 字节校验 + 内容等值")
P("  %-22s %12s %12s %-20s" % ("file", "disk_bytes", "tsv_bytes", "sha256[:16]"))
decl = {r["rel"]: int(r["bytes"]) for r in rows}
info = {}
for name, p in CALLS4.items():
    h, n = sha_file(p)
    info[name] = {"p": p, "bytes": n, "sha": h}
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    dv = decl.get(rel)
    P("  %-22s %12d %12s %-20s" % (name, n, str(dv) if dv is not None else "NOT-IN-LIST", h[:16]))
    ck("P2 %s 在 4417 清单内" % name, dv is not None, rel)
    if dv is not None:
        if name == "a2_sites.json":
            ck("P2 a2 清单为净额行（913,237 = 9 + dumps(calls)），非磁盘字节；差额已闭合",
               dv == 913237 and n - dv == 16711118, "%d vs %d" % (dv, n))
        else:
            ck("P2 %s 清单字节 = 磁盘字节" % name, dv == n, "%d vs %d" % (dv, n))

sm = json.load(open(CALLS4["scan_mine.json"], encoding="utf-8"))
e8 = json.load(open(CALLS4["e8_sites_audit.json"], encoding="utf-8"))
sw = json.load(open(CALLS4["sweep.json"], encoding="utf-8"))
a2 = json.load(open(CALLS4["a2_sites.json"], encoding="utf-8"))
P("  条数：sm.calls=%d  e8=%d  sw.e8=%d  a2.calls(目标键)=%d  对数合计 a2=%d"
  % (len(sm["calls"]), len(e8), len(sw["e8"]), len(a2["calls"]),
     sum(len(v) for v in a2["calls"].values())))
ck("P2 sm.calls 68,253 条", len(sm["calls"]) == 68253, str(len(sm["calls"])))
ck("P2 e8 68,253 条", len(e8) == 68253, str(len(e8)))
ck("P2 sw.e8 68,253 条", len(sw["e8"]) == 68253, str(len(sw["e8"])))
ck("P2 a2.calls 展开 68,253 对", sum(len(v) for v in a2["calls"].values()) == 68253)
ck("P2 a2.calls 目标键 6,728", len(a2["calls"]) == 6728, str(len(a2["calls"])))

pair_sm = [(int(s), int(t)) for s, t in sm["calls"]]
pair_e8 = [(int(s), int(t)) for s, t in e8]
pair_sw = [(int(s), int(t)) for s, t in sw["e8"]]
pair_a2 = sorted((int(s, 16), int(t, 16)) for t, v in a2["calls"].items() for s in v)
pair_a2_fmt = sorted((int(t, 16), int(s, 16)) for t, v in a2["calls"].items() for s in v)
ck("P2 三份列表 calls 逐元素完全相同（sm==e8）", pair_sm == pair_e8)
ck("P2 三份列表 calls 逐元素完全相同（e8==sw）", pair_e8 == pair_sw)
sel = set(pair_e8)
a2_sel = set(pair_a2)
P("  a2 以 (site,target) 解读：与 e8 同集=%s；以 (target,site) 解读：同集=%s"
  % (a2_sel == sel, set(pair_a2_fmt) == sel))
ck("P2 a2.calls 与列表 calls 内容同集（方向 site,target）", a2_sel == sel,
   "|a2|=%d |list|=%d" % (len(a2_sel), len(sel)))

# ---- 负控 N3：比较器必须能抓出「只改一对」----
P("  [N3 负控] 对 calls 比较器做篡改检测（只改 1 对，必须判不等）")
tampered = list(pair_e8)
tampered[0] = (tampered[0][0], tampered[0][1] ^ 0x10)
ck("N3 改 1 对后 e8 != sm", tampered != pair_sm)
ck("N3 改 1 对后集合 != 原集合", set(tampered) != sel)
tampered2 = list(pair_e8)
tampered2.pop()
ck("N3 删 1 对后长度不等", len(tampered2) != len(pair_e8))
# a2 的十六进制键解析方向若写反，必须判不等（N3 对 a2 方向判定的反证）
ck("N3 a2 若按 (target,site) 解读必须判不等（方向敏感）",
   set(pair_a2_fmt) != sel)
ck("N3 e8 列表里确实存在 site != target 的对（否则方向判定无区分力）",
   sum(1 for s, t in pair_e8 if s != t) == len(pair_e8),
   "diff=%d/%d" % (sum(1 for s, t in pair_e8 if s != t), len(pair_e8)))

# 四份文件的 sha256 关系
P("  四份 sha256 两两相同？ %s" % ((len({v["sha"] for v in info.values()}) == 1)))
P("  不同 sha256 个数 = %d" % len({v["sha"] for v in info.values()}))
ck("P2 四份磁盘字节两两不同（序列化不同 -> 哈希不同）",
   len({v["bytes"] for v in info.values()}) == 4)

# ============ JSON 内部等值但序列化不同 ============
P("")
P("=" * 78)
P("[3] JSON 内部等值但序列化不同：量化（纪律 31 口径标注）")
def compact(obj):
    return json.dumps(obj, separators=(",", ":"))
def default(obj):
    return json.dumps(obj)
for nm, obj in (("a2.calls", a2["calls"]), ("sm.calls", sm["calls"]),
                ("e8", e8), ("sw.e8", sw["e8"]), ("sw.installs", sw["installs"])):
    dc = len(compact(obj).encode())
    dd = len(default(obj).encode())
    P("  %-12s 紧凑口径 %10d B / 默认口径 %10d B / 差 %8d B (%.2f%%)"
      % (nm, dc, dd, dd - dc, (dd - dc) * 100.0 / dd))
# a2 的 calls 是 16 进制字符串 + 目标->站点列表；列表口径是十进制 + [site,target]
a2_plain = [[s, t] for (t, v) in a2["calls"].items() for s in v]
P("  a2.calls 盘上序列化（hex 字符串、目标->站点字典，默认口径）%d B" % len(default(a2["calls"]).encode()))
P("  同一内容的「十进制 [site,target] 列表」形态（默认口径）            %d B" % len(default(e8).encode()))
ck("P2/3 同一批 68,253 对在两种序列化下字节不同（故哈希不同）",
   len(default(a2["calls"]).encode()) != len(default(e8).encode()))
# 验证 a2 盘上字节口径（纪律 31：与盘上字节等式）
raw_a2 = open(CALLS4["a2_sites.json"], "rb").read()
ck("口径 a2 = json.dump 默认分隔符（逐字节相等）", raw_a2 == default(a2).encode())
raw_sw = open(CALLS4["sweep.json"], "rb").read()
ck("口径 sweep = json.dump 默认分隔符（逐字节相等）", raw_sw == default(sw).encode())
raw_e8 = open(CALLS4["e8_sites_audit.json"], "rb").read()
ck("口径 e8 = json.dump 默认分隔符（逐字节相等）", raw_e8 == default(e8).encode())
raw_sm = open(CALLS4["scan_mine.json"], "rb").read()
ck("口径 scan_mine = json.dump 默认分隔符（逐字节相等）", raw_sm == default(sm).encode())

# ============ 第三口径：跨序列化的「内容等值」去重 ============
P("")
P("=" * 78)
P("[4b] 跨序列化内容等值口径 —— SHA256 文件级去重抓不到的那一块")
P("  SHA256 是「字节指纹」，序列化不同即不同簇。已确认四份 calls 文件"
  "在 [4] 里 cluster_size 全 = 1（各自成簇）")
for nm, p in CALLS4.items():
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    rec = next(x for x in recs if x["rel"] == rel)
    P("    %-20s cluster_size=%d  sha256=%s" % (nm, len(clusters[rec["sha"]]), rec["sha"][:16]))
ck("四份 calls 文件在 SHA256 口径下各自成簇（去重抓不到它们之间的冗余）",
   all(len(clusters[next(x for x in recs
                          if x["rel"] == os.path.relpath(p, ROOT).replace("\\", "/"))["sha"]]) == 1
       for p in CALLS4.values()))

def canon_pairs(obj):
    """把「同一批调用对」规约成与表示无关的规范串：排序后的十进制 (site,target)。"""
    if isinstance(obj, dict):          # a2 形态：target(hex str) -> [site(hex str), ...]
        ps = sorted((int(s, 16), int(t, 16)) for t, v in obj.items() for s in v)
    else:                              # 列表形态：[[site, target], ...]
        ps = sorted((int(a), int(b)) for a, b in obj)
    return "\n".join("%08X\t%08X" % p for p in ps), len(ps)

canon = {}
for nm, obj in (("a2_sites.calls", a2["calls"]), ("scan_mine.calls", sm["calls"]),
                ("e8_sites_audit", e8), ("sweep.e8", sw["e8"])):
    s, n = canon_pairs(obj)
    canon[nm] = hashlib.sha256(s.encode()).hexdigest()
    P("    规范串 %-16s 对=%-6d len=%-8d sha256=%s" % (nm, n, len(s), canon[nm][:16]))
ck("四份规范串哈希完全相同（内容等值）", len(set(canon.values())) == 1,
   str(len(set(canon.values()))))
# 负控 N4：规范串必须对「改一对」敏感
bad = list(pair_e8)
bad[0] = (bad[0][0], bad[0][1] ^ 1)
s_bad, _ = canon_pairs(bad)
ck("N4 规范串对改 1 对敏感", hashlib.sha256(s_bad.encode()).hexdigest() != canon["e8_sites_audit"])
# 负控 N5：规范串必须对「删一对」敏感
ck("N5 规范串对删 1 对敏感",
   hashlib.sha256(canon_pairs(list(pair_e8)[:-1])[0].encode()).hexdigest()
   != canon["e8_sites_audit"])

# 内容等值口径的唯一体量：3 份列表 calls 的 e8 字节 + a2 的 calls 字节 → 只算 1 份
list_calls_bytes = len(json.dumps(e8).encode())
a2_calls_bytes = len(json.dumps(a2["calls"]).encode())
uniq_bytes_ceq = uniq_bytes - 2 * list_calls_bytes - a2_calls_bytes
P("  内容等值口径：从磁盘口径唯一体量 %d 扣掉 2 份重复列表 calls（2×%d）"
  " 与 a2 的 calls 部分（%d）" % (uniq_bytes, list_calls_bytes, a2_calls_bytes))
P("    => 内容等值唯一体量 = %d B" % uniq_bytes_ceq)
P("    唯一件数（内容等值口径）= 4087 − 3 = %d" % (uniq_n - 3))
ck("内容等值唯一体量 = 615,909,180 − 2×1,365,087 − 913,228 = 611,813,919",
   uniq_bytes_ceq == 615909180 - 2 * 1365087 - 913228, str(uniq_bytes_ceq))
ck("内容等值唯一体量 < 磁盘口径唯一体量（扣减为正）",
   uniq_bytes_ceq < uniq_bytes, "%d < %d" % (uniq_bytes_ceq, uniq_bytes))
ck("内容等值口径扣减量 = 3,643,402", uniq_bytes - uniq_bytes_ceq == 3643402,
   str(uniq_bytes - uniq_bytes_ceq))

# ============ Top 15 重复簇 ============
P("")
P("=" * 78)
P("[4] 重复簇明细")
dups = [(sha, v) for sha, v in clusters.items() if len(v) > 1]
dups.sort(key=lambda kv: (-(len(kv[1]) - 1) * kv[1][0]["bytes"], -len(kv[1])))
P("  含重复的簇数 = %d；其中 2 件 %d / 3 件 %d / >=4 件 %d"
  % (len(dups),
     sum(1 for _, v in dups if len(v) == 2),
     sum(1 for _, v in dups if len(v) == 3),
     sum(1 for _, v in dups if len(v) >= 4)))
P("  Top 15（按浪费字节 = 单件字节 x (份数-1) 排序）：")
P("  %-3s %10s %4s %12s  %s" % ("#", "bytes", "n", "wasted", "sha256[:16] / 路径"))
for i, (sha, v) in enumerate(dups[:15], 1):
    waste = v[0]["bytes"] * (len(v) - 1)
    P("  %-3d %10d %4d %12d  %s" % (i, v[0]["bytes"], len(v), waste, sha[:16]))
    for x in v[:4]:
        P("       - " + x["rel"])
    if len(v) > 4:
        P("       - ... 另 %d 件" % (len(v) - 4))

# 2 件簇按浪费字节排序 Top 若干（另附，便于核对）
P("")
P("  Top 10 按份数（同内容份数最多）：")
dups_n = sorted(dups, key=lambda kv: -len(kv[1]))
for i, (sha, v) in enumerate(dups_n[:10], 1):
    P("  %-3d n=%d bytes=%d %s  %s" % (i, len(v), v[0]["bytes"], sha[:16], v[0]["rel"]))

# ============ 落盘清单 ============
P("")
P("=" * 78)
P("[5] 落盘 " + OUT)
rep_of = {}
for sha, v in clusters.items():
    rep = v[0]["rel"]
    for x in v:
        rep_of[x["rel"]] = (rep, len(v))
order = {r["rel"]: i for i, r in enumerate(rows)}
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["rel", "bytes", "decl_bytes", "sha256", "cluster_size",
                "cluster_wasted", "cluster_rep"])
    for x in sorted(recs, key=lambda y: order[y["rel"]]):
        rep, n = rep_of[x["rel"]]
        w.writerow([x["rel"], x["bytes"], x["decl"], x["sha"], n,
                    x["bytes"] * (n - 1), rep])
# 回读校验
back = list(csv.DictReader(open(OUT, encoding="utf-8"), delimiter="\t"))
back_sum = sum(int(r["bytes"]) for r in back)
back_decl = sum(int(r["decl_bytes"]) for r in back)
back_uniq = len({r["sha256"] for r in back})
back_uniq_bytes = sum(int(r["bytes"]) for r in back if r["cluster_rep"] == r["rel"])
back_uniq_decl = sum(int(r["decl_bytes"]) for r in back if r["cluster_rep"] == r["rel"])
P("  回读行数 = %d（期望 4417）" % len(back))
P("  回读 sum(bytes) 磁盘口径 = %d（期望 754,228,404）" % back_sum)
P("  回读 sum(decl_bytes) 清单口径 = %d（期望 737,517,286）" % back_decl)
P("  回读唯一 sha256 簇数 = %d（期望 %d）" % (back_uniq, uniq_n))
P("  回读唯一内容字节 磁盘口径 = %d（期望 %d）" % (back_uniq_bytes, uniq_bytes))
P("  回读唯一内容字节 清单口径 = %d（期望 %d）" % (back_uniq_decl, uniq_bytes_decl))
ck("回读行数 = 4417", len(back) == 4417, str(len(back)))
ck("回读 sum(bytes) 磁盘口径 = 754,228,404", back_sum == disk_total, str(back_sum))
ck("回读 sum(decl_bytes) 清单口径 = 737,517,286", back_decl == 737517286, str(back_decl))
ck("回读唯一簇数一致", back_uniq == uniq_n, "%d vs %d" % (back_uniq, uniq_n))
ck("回读唯一内容字节 磁盘口径一致", back_uniq_bytes == uniq_bytes,
   "%d vs %d" % (back_uniq_bytes, uniq_bytes))
ck("回读唯一内容字节 清单口径一致", back_uniq_decl == uniq_bytes_decl,
   "%d vs %d" % (back_uniq_decl, uniq_bytes_decl))
ck("回读重复字节 = 总 − 唯一（磁盘口径）", back_sum - back_uniq_bytes == dup_bytes,
   str(back_sum - back_uniq_bytes))
ck("唯一簇数 + 重复件数 = 4417", uniq_n + dup_n == 4417)

# ============ 扩展名维度（旁证） ============
P("")
P("=" * 78)
P("[6] 扩展名维度（件数/总字节/唯一字节）")
byext = {}
for x in recs:
    e = os.path.splitext(x["rel"])[1].lower() or "(none)"
    d = byext.setdefault(e, {"n": 0, "b": 0, "u": 0})
    d["n"] += 1
    d["b"] += x["bytes"]
    if rep_of[x["rel"]][0] == x["rel"]:
        d["u"] += x["bytes"]
for e, d in sorted(byext.items(), key=lambda kv: -kv[1]["b"]):
    P("  %-8s n=%4d  总 %12d  唯一 %12d  重复 %12d"
      % (e, d["n"], d["b"], d["u"], d["b"] - d["u"]))

# ============ 汇总 ============
P("")
P("=" * 78)
P("[7] 汇总（两口径并列，纪律 31：引用必须带口径）")
P("  §2.71 / F24 语料值（清单净额口径）：4,417 件 / 737,517,286 B")
P("  磁盘口径实测                     ：4,417 件 / %d B（差 %d = a2 净额行）"
  % (disk_total, disk_total - 737517286))
P("  唯一内容体量（SHA256 去重，磁盘口径）：%d 簇 / %d B" % (uniq_n, uniq_bytes))
P("  唯一内容体量（SHA256 去重，清单口径）：%d 簇 / %d B" % (uniq_n, uniq_bytes_decl))
P("  重复（同一内容多份落盘，磁盘口径）  ：%d 件 / %d B" % (dup_n, dup_bytes))
P("  重复（同一内容多份落盘，清单口径）  ：%d 件 / %d B" % (dup_n, dup_bytes_decl))
P("  含重复的簇                          ：%d" % len(dups))
P("  自测项 %d，FAIL %d" % (nck[0], len(fails)))
P("")
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))

open(LOG, "w", encoding="utf-8", newline="\n").write("\n".join(_buf) + "\n")
sys.exit(0 if not fails else 1)
