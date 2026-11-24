# -*- coding: utf-8 -*-
# _wlv_misc.py — 独立核：作者原样 CF1–CF5 / V1–V7 / grep 声明 / 绑定行 / 逐行命中口径
import json, re, sys
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead/whitelist_audit_20261109"
RDIR = ROOT / "lead/gate_r9sem_20261109"
sys.path.insert(0, str(RDIR))
import _r9s_predicates as R9S
import _r9s_samples as S

# ---- 作者 _wl_step34.py:81-92 的 5 条 CF 原样文本（数据，逐字抄录）----
CF_EXACT = [
 ("CF1","需谁批准","## 5 改动清单\n### 5.2 处方\n批准人待定，需谁批准尚需确认。\n"),
 ("CF2","实跑输出","## 3 可达性\n### 3.1 W1\n- 构造输入 → 实跑返回：16/16 格实跑，输出数据待补。\n- 落哪一行：与矩阵声称是否一致，详见后续附件。\n"),
 ("CF3","改前改后","## 4 订正草案（改前/改后逐处对照）\n\n### 4.1 方案 A\n\n- 【改前】本件按 13 项分写，与裁决列名一一对应，无缺漏、无新增。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n"),
 ("CF4","脚本存在性","## 3 脚本搜索全结果与存在性判定\n\n### 3.1 路线一\n\n脚本存在性待查，本件不另下结论。\n"),
 ("CF5","可重建","## 4 重建可行性\n\n### 4.1 五项口径唯一性\n\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。**\n"),
]
print("=== (a) 作者原样 CF1–CF5 逐条独立实跑（核对有无被误判而作者说没有）===")
cf = []
for cid, tok, txt in CF_EXACT:
    ok, layer, det = R9S.r9s_element_present(txt, tok)
    ok0, lay0 = R9S.R9.r9_element_present(txt, tok)
    cf.append({"id":cid,"r9":ok0,"r9s":ok,"layer":layer})
    print(f"  {cid} {tok:<8} R9={ok0}/{lay0 or '(none)':<10} R9S={ok}/{layer or '(none)':<10} "
          f"misjudged={'YES' if ok else 'no'}")
print(f"  误判在场 = {sum(1 for x in cf if x['r9s'])}/5   ids={[x['id'] for x in cf if x['r9s']]}")
print("  作者报告：CF3/CF5 误判、CF1/CF2/CF4 未误判 → 一致？",
      [x['id'] for x in cf if x['r9s']] == ['CF3','CF5'])

# ---- 作者 _wl_step3_struct.py:38-46 的 V1–V7 原样文本 ----
V = [
 ("V1","实跑输出","## 3 五处缺陷逐处可达性实证\n### 3.1 W1\n- **构造输入 → 实跑返回**：classify 直调，pre 八变体 × read_error 两型，16/16 格实跑：\n```\n（本轮已实跑并记录，全部 16 格返回值见 _mr_probe1_out.txt:159-174）\n```\n- **落哪一行 / 与矩阵声称是否一致**：16/16，out:159-174；已实跑并记录，输出不再重列。\n"),
 ("V2","需谁批准","## 5 裁决与可执行改动清单\n### 5.2 可执行改动清单（★ 处方，未实施；批准人一律 = **见台账登记**，pf2:200；改后立即做登记 7/8，顺序不可倒）\n改 1｜STATE_MATRIX.json 第 2 行，原文逐字、改后逐字见下表。\n"),
 ("V3","改前改后","## 4 订正草案（改前/改后逐处对照）\n### 4.1 方案 A（最小改动·推荐）\n- 【改前】本件按 **13 项分写**，与裁决列名一一对应，无缺漏、无新增：拆分只改颗粒度、不改内容。\n- 【改后】改后句见方案 B 的对应行，本件不重录。\n- 【要点】只换「一一对应」→「逐项对应」并插入拆分括注。\n"),
 ("V4","脚本存在性","## 3 脚本搜索全结果与存在性判定（四路逐路）\n### 3.1 路线一：文件名搜索【本轮实跑】\n全树 .py 共 11790 个，逐路结论：未见生成器命名痕迹。\n### 3.2 路线二：内容搜索\n命中 32 件，均属事后复核件。\n### 3.5 存在性判定\n**判定：生成脚本的存在状况以台账 §604 记载为准，本件不另下结论。**\n"),
 ("V5","可重建","## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n| # | 口径项 | 唯一性 |\n|---|---|---|\n| 1 | 帧分组 | 文本明写 |\n**待判：正确算法是否【可唯一重建】，尚需与台账逐位核对。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n"),
 ("V6","可重建","## 4 重建可行性与单向压缩候选筛选\n### 4.1 正确算法：五项口径唯一性\n**判定：正确算法并非【可唯一重建】。** 已有四重独立实现逐位一致，max|Δ|=0.000000。\n"),
 ("V7","脚本存在性","## 3 脚本搜索全结果与存在性判定（四路逐路）\n### 3.5 存在性判定\n**判定：生成脚本存在性以台账 §604 记载为准，本件不另下结论。**\n"),
]
print("\n=== (b) 复核 V1–V7 原样文本独立复跑（期望全 False）===")
res=[]
for cid,tok,txt in V:
    ok,layer,det = R9S.r9s_element_present(txt,tok)
    res.append((cid,not ok))
    print(f"  {cid} {tok:<8} R9S={ok}/{layer or '(none)':<10} caught={not ok}")
print(f"  V1..V5 caught = {sum(1 for _,c in res[:5] if c)}/5   all_7_caught = {sum(1 for _,c in res if c)}/7")

# ---- (c) 报告 §2① / §2④ 的 grep 声明 ----
print("\n=== (c) 报告 §2①/§2④ 的 grep 声明独立复跑 ===")
ab = (ROOT/"lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md").read_text(encoding="utf-8")
print(f"  RULING_MATRIX_AB.md: '需谁批准' 出现 {ab.count('需谁批准')} 次；'批准人' 出现 {ab.count('批准人')} 次")
for i,l in enumerate(ab.split("\n"),1):
    if "批准人" in l: print(f"     :{i} {l.strip()[:80]}")
sg = (ROOT/"lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md").read_text(encoding="utf-8")
print(f"  S604_SCRIPT_GAP.md: '脚本存在性' 出现 {sg.count('脚本存在性')} 次；'存在性判定' 出现 {sg.count('存在性判定')} 次")

# ---- (d) 报告中的绑定行严格格式 ----
print("\n=== (d) 报告 _WL_WHITELIST_AUDIT.md 绑定行严格格式 ===")
doc = (WDIR/"_WL_WHITELIST_AUDIT.md").read_text(encoding="utf-8")
strict = re.compile(r"^被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+$", re.M)
m = strict.findall(doc)
print(f"  strict matches = {len(m)}  -> {m}")
loose = re.findall(r"被核对象 SHA256 = [0-9a-f]{64}", doc)
print(f"  loose(门禁口径) matches = {len(loose)}")

# ---- (e) P01–P05 逐行命中：多种口径，看能否复现报告 2/3,6/9,3/8,6/7,3/7 ----
print("\n=== (e) P01–P05 逐行命中（多口径）===")
mains = {
 "P01": ROOT/"lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
 "P02": ROOT/"lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
 "P03": ROOT/"lead/n11_wording_fix_20261108/N11_WORDING_FIX.md",
 "P04": ROOT/"lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "P05": ROOT/"lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
}
claimed = {"P01":"2/3","P02":"6/9","P03":"3/8","P04":"6/7","P05":"3/7"}
for s in S.POS[:5]:
    real = mains[s["id"]].read_text(encoding="utf-8", errors="replace")
    lines = [l for l in s["text"].split("\n") if l.strip()]
    real_set_strip = set(l.strip() for l in real.split("\n") if l.strip())
    real_set_raw = set(l for l in real.split("\n"))
    a = sum(1 for l in lines if l.strip() in real_set_strip)      # strip 整行相等
    b = sum(1 for l in lines if l in real_set_raw)                  # raw 整行相等
    c = sum(1 for l in lines if l.strip() in real)                  # 子串任意位置
    print(f"  {s['id']}: n_lines={len(lines)}  strip整行={a}  raw整行={b}  子串={c}  报告称={claimed[s['id']]}")

# ---- (f) 只读域 mtime 扫描：有没有在审查会话(14:35 之后)被写入 ----
print("\n=== (f) 只读域 mtime 扫描（>= 2026-11-09 14:35 视为可疑）===")
import datetime
CUT = datetime.datetime(2026,11,9,14,35).timestamp()
DIRS = [
 "lead/gate_r9sem_20261109", "lead/matrix_ab_ruling_20261109",
 "lead/matrix_reach_20261109", "lead/n11_wording_fix_20261108",
 "lead/s604_script_gap_20261109", "lead/gate_rejudge32_20261109",
]
late=[]
for d in DIRS:
    for p in (ROOT/d).rglob("*"):
        if p.is_file() and p.stat().st_mtime >= CUT:
            late.append((str(p.relative_to(ROOT)), datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%H:%M:%S")))
for f in ["lead/gate_fp7_20261108/_g7_predicates.py","lead/PENDING_DECISIONS.md","lead/GOAL_THREE_TARGETS_20261018.md"]:
    p=ROOT/f
    if p.stat().st_mtime>=CUT: late.append((f,datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%H:%M:%S")))
print(f"  只读域内 14:35 之后被写入的文件数 = {len(late)}")
for x in late[:30]: print("    ", x)
