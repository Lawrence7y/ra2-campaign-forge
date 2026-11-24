# -*- coding: utf-8 -*-
# 交付探针2：改文文本 vs 草案件逐字比对 + A4 拼接结构 + A1 词汇溯源 + 源③/普查引证行
import os
BASE = r"D:\Project\ra2-campaign-forge"
def rp(rel): return os.path.join(BASE, rel)
def lines(rel): return open(rp(rel),'r',encoding='utf-8',errors='replace').read().splitlines()

draft = open(rp("lead/a_class_fix_20261109/_ac_A1A4A5_FIX_DRAFT_20261109.md"),'r',encoding='utf-8').read()

A1 = "源读面持续阻断（ACL 拒读〔目录继承 deny-ACE，跨文件重建仍持续——写域探针实证〕/AV 对该路径持续拦截）横跨 pre/post 两时点，可一次造成两半；游戏句柄〔T0 未启动、term 成功即句柄随进程终止被内核关闭〕与磁盘满〔仅写侧〕均只在收尾时点成立，不能单独桥接。"
A4 = "2. **W2**：pre 侧 make_pre 在 :6623 对载体 except.txt 采集抛异常（源读面持续阻断：ACL 拒读〔目录继承 deny-ACE，跨文件重建仍持续——写域探针实证〕/AV 对该路径持续拦截 → error 态；AV 瞬时锁非持续根因，双时点命中需两次独立竞态；路径异常在 py3.12.10 实测〔非法字符/ENOTDIR/超长〕均被 exists() 吞为 absent_confirmed，不产 error 态）+ 同趟收尾复制对同一源路径再失败（同一 ACE/拦截持续 ⇒ 一因双时点；游戏句柄〔T0 未启动、term 成功即句柄随进程终止被内核关闭〕与磁盘满〔仅写侧〕均只在收尾时点成立，不能单独桥接）。源读面持续阻断横跨 pre 与 post 两个时点，可一次造成两半。**评级：罕见**。"
A5 = "「罕见」仅限**源读面持续阻断**子集（deny-ACE 为环境常量、台账可证伪；AV 持续拦截 ~1e-5–1e-3）；AV 瞬时锁双击 ~1e-6–1e-4、两独立因 ~1e-7–1e-5（均极罕见档；全部为推理、未验）"

print("A1 text in draft file:", A1 in draft)
print("A4 text in draft file:", A4 in draft)
print("A5 text in draft file:", A5 in draft)

u8 = lines("lead/handoff_pack_20261109/_hp_U8.md")[13]
i = u8.find("→ read_error 先截")
u8nt = u8[:i].rstrip()
A1ORIG = "同一持续根因（句柄/ACL 横跨两时点）可一次造成两半。"
A4ORIG = "2. **W2**：pre 侧 make_pre 在 :6623 对载体 except.txt 采集失败（AV 瞬时锁 / ACL / 路径异常 ⇒ P4 所证 error 态）+ 同趟收尾复制又失败。同一持续根因（句柄被占/ACL 损坏横跨 pre 与 post 两个时点）可一次造成两半。**评级：罕见**。"
CONCL = "。源读面持续阻断横跨 pre 与 post 两个时点，可一次造成两半。"
print("A4 == prefix + U8:14去尾链 + 结论句段 + 评级 :", A4 == "2. **W2**：pre 侧 " + u8nt + CONCL + "**评级：罕见**。")
mrL = lines("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md")
print("A1ORIG tail of MATRIX:90 :", mrL[89].endswith(A1ORIG))
mrE = lines("lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md")
print("A4ORIG == _mr:112 :", A4ORIG == mrE[111])
print("A5 == hp_U9:14 :", A5 == lines("lead/handoff_pack_20261109/_hp_U9.md")[13])

print("== A1 vocabulary sources in hp_U8:14 ==")
for frag in ["源读面持续阻断","ACL 拒读〔目录继承 deny-ACE，跨文件重建仍持续——写域探针实证〕","AV 对该路径持续拦截","游戏句柄〔T0 未启动、term 成功即句柄随进程终止被内核关闭〕","磁盘满〔仅写侧〕","均只在收尾时点成立，不能单独桥接"]:
    print(" ", frag in u8, "::", frag[:24])
print("'横跨 pre/post 两时点' in MATRIX:154(旧):", "横跨 pre/post 两时点" in mrL[153])
print("'可一次造成两半' in MATRIX:90:", "可一次造成两半" in mrL[89])

print("== W2_SAME_CAUSE R 行实读 ==")
w2 = lines("lead/w2_samecause_20261109/W2_SAME_CAUSE.md")
for n in [73,74,77,78,94,96]:
    print("--W2:%d" % n)
    print(w2[n-1][:300])

print("== _uf 拼接口径注记（U8 条）实读 ==")
uf = lines("lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md")
hits = [(i+1,l) for i,l in enumerate(uf) if "拼接口径" in l]
for n,l in hits[:6]:
    print("UF", n, l[:240])
