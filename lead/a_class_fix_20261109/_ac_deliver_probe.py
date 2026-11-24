# -*- coding: utf-8 -*-
# 交付件探针：指纹核验 + 目标行实读 + 改文组合核验 + 关键词基线 + 引用普查
# 只读探针：不写任何文件。运行：python -I -X utf8 <abs path>
import hashlib, os, sys, glob
from collections import defaultdict

BASE = r"D:\Project\ra2-campaign-forge"

def rp(rel):
    return os.path.join(BASE, rel)

EXPECT = [
 ("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md","cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6",27825),
 ("lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md","67d0fc90ceae277f23d43f80484da9445a6385994752a882d04a8517809f10e9",20820),
 ("lead/w2_samecause_20261109/W2_SAME_CAUSE.md","75a0369b97f72f9d615ced86c580c6e63bfcce4f29de1c86bd74e8542aa5c895",19552),
 ("lead/handoff_pack_20261109/APPROVAL_PACK.md","36ee1d6a0d93363ad6004543fa98fb4876e67ac6d7aecac33b3651c376b327f3",40024),
 ("lead/handoff_pack_20261109/_hp_U8.md","c87ef405e0ee8ffeaccf96972287422c3ab23376b4fe2153ef6b44d2afe0079f",3705),
 ("lead/handoff_pack_20261109/_hp_U9.md","90a566c84c5e8dfc1e1782c0fca560cbca8539d71ad06e5a5ca5cc8964a03630",1806),
 ("lead/oldwording_sweep_20261109/_ow_SWEEP_REPORT_20261109.md","7378a419c896a05bafc10d4189769dc248dccb37c548f56d381d6d83209e16dc",16900),
 ("lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md","441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923",25095),
 ("lead/PENDING_DECISIONS.md","3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",52419),
 ("lead/GOAL_THREE_TARGETS_20261018.md","2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",759518),
]

def h(p):
    d = open(p,'rb').read()
    return hashlib.sha256(d).hexdigest(), len(d)

print("== FINGERPRINTS (10) ==")
ok = 0
for rel, eh, eb in EXPECT:
    got, nb = h(rp(rel))
    m = (got == eh and nb == eb)
    ok += int(m)
    print(("OK  " if m else "FAIL"), rel, "sha=", got, "bytes=", nb)
print("FP_MATCH %d/%d" % (ok, len(EXPECT)))

def lines(rel):
    return open(rp(rel),'r',encoding='utf-8',errors='replace').read().splitlines()

def show(rel, ns):
    L = lines(rel)
    for n in ns:
        print("--%s:%d" % (rel, n))
        print(L[n-1])

print("== TARGET LINES ==")
show("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", [90,146,147,154])
show("lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md", [74,112,121,122])
show("lead/handoff_pack_20261109/_hp_U8.md", [9,14])
show("lead/handoff_pack_20261109/_hp_U9.md", [9,14,25,27])

print("== W2 SOURCE 118-124 ==")
show("lead/w2_samecause_20261109/W2_SAME_CAUSE.md", [118,122,124])

print("== COMPOSITION CHECKS ==")
u8 = lines("lead/handoff_pack_20261109/_hp_U8.md")[13]
w2l = lines("lead/w2_samecause_20261109/W2_SAME_CAUSE.md")
print("hp_U8:14 == W2:122 ?", u8 == w2l[121])
print("'不能单独桥接' in hp_U8:14 ?", "不能单独桥接" in u8)
print("'-> read_error 先截' in hp_U8:14 ?", "→ read_error 先截" in u8)
u9 = lines("lead/handoff_pack_20261109/_hp_U9.md")[13]

A5 = "「罕见」仅限**源读面持续阻断**子集（deny-ACE 为环境常量、台账可证伪；AV 持续拦截 ~1e-5–1e-3）；AV 瞬时锁双击 ~1e-6–1e-4、两独立因 ~1e-7–1e-5（均极罕见档；全部为推理、未验）"
print("A5 == hp_U9:14 ?", A5 == u9)

tail = "→ read_error 先截"
i = u8.find(tail)
print("tail idx in hp_U8:14:", i)
if i >= 0:
    u8nt = u8[:i].rstrip()
    A4_MID = "make_pre 在 :6623 对载体 except.txt 采集抛异常（源读面持续阻断：ACL 拒读〔目录继承 deny-ACE，跨文件重建仍持续——写域探针实证〕/AV 对该路径持续拦截 → error 态；AV 瞬时锁非持续根因，双时点命中需两次独立竞态；路径异常在 py3.12.10 实测〔非法字符/ENOTDIR/超长〕均被 exists() 吞为 absent_confirmed，不产 error 态）+ 同趟收尾复制对同一源路径再失败（同一 ACE/拦截持续 ⇒ 一因双时点；游戏句柄〔T0 未启动、term 成功即句柄随进程终止被内核关闭〕与磁盘满〔仅写侧〕均只在收尾时点成立，不能单独桥接）。源读面持续阻断横跨 pre 与 post 两个时点，可一次造成两半。"
    print("A4 mid == hp_U8:14 minus tail ?", A4_MID == u8nt)
    if A4_MID != u8nt:
        print("len A4_MID =", len(A4_MID), " len u8nt =", len(u8nt))
        for k,(x,y) in enumerate(zip(A4_MID,u8nt)):
            if x != y:
                print("first diff at", k, "A4:", repr(A4_MID[max(0,k-15):k+15]), "U8:", repr(u8nt[max(0,k-15):k+15]))
                break

print("== KEYWORD BASELINE (two target files) ==")
for rel in ["lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md","lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md"]:
    L = lines(rel)
    for kw in ["同一持续根因","同根因双时点","源读面"]:
        hits = [i+1 for i,l in enumerate(L) if kw in l]
        print(kw, "@", os.path.basename(rel), "->", hits)

print("== DRAFT FILE HASH ==")
dh, db = h(rp("lead/a_class_fix_20261109/_ac_A1A4A5_FIX_DRAFT_20261109.md"))
print("draft sha256 =", dh, "bytes =", db)

print("== OLDWORDING ==")
ow = glob.glob(rp("lead/oldwording_sweep_20261109/OLD_WORDING_SWEEP.md"))
print("OLD_WORDING_SWEEP.md exists:", bool(ow))
if ow:
    OL = lines("lead/oldwording_sweep_20261109/OLD_WORDING_SWEEP.md")
    print("--OLD_WORDING_SWEEP.md:99")
    print(OL[98])
REP = lines("lead/oldwording_sweep_20261109/_ow_SWEEP_REPORT_20261109.md")
hits = [(i+1,l) for i,l in enumerate(REP) if "A4" in l]
print("== _ow_SWEEP_REPORT lines containing 'A4' (first 10) ==")
for n,l in hits[:10]:
    print(n, l[:220])

print("== BY-NAME REFERENCE CENSUS (files containing 'MATRIX_DEFECT_REACHABILITY') ==")
cnt = defaultdict(int); det = defaultdict(list)
for root, dirs, fs in os.walk(rp("lead")):
    for f in fs:
        if not f.lower().endswith((".md",".json",".py",".txt")):
            continue
        p = os.path.join(root,f)
        try:
            t = open(p,'r',encoding='utf-8',errors='ignore').read()
        except Exception:
            continue
        if "MATRIX_DEFECT_REACHABILITY" in t:
            rel2 = os.path.relpath(p, BASE).replace("\\","/")
            parts = rel2.split("/")
            grp = parts[1] if len(parts) > 2 else "(lead root)"
            cnt[grp] += 1
            det[grp].append(rel2)
for g in sorted(cnt):
    print(g, cnt[g])
    for x in sorted(det[g]):
        print("   ", x)
