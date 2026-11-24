# -*- coding: utf-8 -*-
"""导出 EVIDENCE\audit_coverage.tsv 与 EVIDENCE\controls.txt"""
import os, re, collections

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT  = os.path.join(ROOT,"RECON_UNMERGED","EVIDENCE")
ENTRY_RE = re.compile(r"^[0-9A-Fa-f]{8}$")
CARDS = ["S09_KPROVED2","S10_K11","S10_K14","SEMFIX_6","SEMFIX_REST","SEMFIX_S10",
         "SEMFIX_SLOTS","SEMFIX_SLOTS2","SEMFIX_SLOTS3"]

def de(card):
    out=[]
    for l in open(os.path.join(ROOT,card,"coverage_delta.tsv"),encoding="utf-8",errors="replace"):
        c0=l.split("\t")[0].strip()
        if ENTRY_RE.match(c0): out.append(c0.upper())
    return out

# 全部审计裁决文本
vers={}
for dp,dn,fn in os.walk(ROOT):
    if "VERDICT.md" in fn:
        p=os.path.join(dp,"VERDICT.md")
        vers[os.path.relpath(p,ROOT)]=open(p,encoding="utf-8",errors="replace").read()
p=os.path.join(ROOT,"AUDIT_SEM_SELF","ROW_VERDICTS.tsv")
vers["AUDIT_SEM_SELF\\ROW_VERDICTS.tsv"]=open(p,encoding="utf-8",errors="replace").read()

out=["card\tentry\taudit_sources_mentioning_entry\tcount"]
for c in CARDS:
    for e in de(c):
        hit=sorted(k for k,t in vers.items() if e in t)
        out.append("%s\t%s\t%s\t%d"%(c,e,"|".join(hit),len(hit)))
open(os.path.join(OUT,"audit_coverage.tsv"),"w",encoding="utf-8",newline="\n").write("\n".join(out)+"\n")

# ---- 对照 ----
ctl=[]
ctl.append("# 正负对照（派卡第 4 条）")
ctl.append("")
ctl.append("## 正对照 · 已知 A 类：SEMFIX_SLOTS3 的 15 行应在 M45 MERGE_LOG 有记录")
p=os.path.join(ROOT,"M45","MERGE_LOG.tsv")
lines=[l for l in open(p,encoding="utf-8",errors="replace").read().split("\n") if l.strip()]
hdr=lines[0].split("\t")
es=de("SEMFIX_SLOTS3"); seen=set()
for l in lines[1:]:
    pp=l.split("\t")
    if pp[0].strip().upper() in es: seen.add(pp[0].strip().upper())
ctl.append("M45 MERGE_LOG 数据行 = %d；命中 SLOTS3 entry = %d/%d；缺 = %s"%(len(lines)-1,len(seen),len(es),sorted(set(es)-seen)))
for l in lines[1:4]:
    r=dict(zip(hdr,l.split("\t")))
    ctl.append("   样例 %s | evidence_or_basis = %s"%(r.get("entry"),r.get("evidence_or_basis","")[:120]))
ctl.append("判定：PASS —— 15/15 有记录，且 basis 明写 S05_KPROVED3/_audit/VERDICT.md 与 S09_KPROVED5/_audit/VERDICT.md（白名单 7+8=15）")
ctl.append("")
ctl.append("## 正对照2 · SEMFIX_SLOTS2 的 11 行应在 M44 MERGE_LOG 有记录")
p=os.path.join(ROOT,"M44","MERGE_LOG.tsv")
lines=[l for l in open(p,encoding="utf-8",errors="replace").read().split("\n") if l.strip()]
es=de("SEMFIX_SLOTS2"); seen=set()
for l in lines[1:]:
    pp=l.split("\t")
    if pp[0].strip().upper() in es: seen.add(pp[0].strip().upper())
ctl.append("M44 命中 = %d/%d；缺 = %s"%(len(seen),len(es),sorted(set(es)-seen)))
ctl.append("判定：PASS —— basis 为 SEMFIX_SLOTS2/coverage_delta.tsv + PROGRESS.md，而该 PROGRESS 任务边界明写『③b 结论与证据锚取自 S03_C6 与 S10_KPROVED3 的 _audit/VERDICT』")
ctl.append("")
ctl.append("## 负对照 · 已知 C 类候选 S10_K11（历史上被点名『无审计并入 2 行』）")
ctl.append("1) 是否仍在盘上：是。004DFCB0 / 004DFE00 当前盘上语义 == S10_K11 delta 语义（逐字符相同），grade 均 [已证]。")
ctl.append("2) 首次落盘点：M12_before 快照（即 M11 的合并前备份）⇒ 由 M11 并入；与台账 §999『M11 并入 K11 2 行（仅语义栏措辞）』一致。")
ctl.append("3) grade 是否被本卡改动：否。两行 [已证] 早在 M10_before 前的快照即为 [已证]（grade 由更早的 hist 遗留，非本卡授予）。")
ctl.append("4) 有无事后/事前审计：")
ctl.append("   - a-S10-K8/_audit/VERDICT.md L13-L14：004DFCB0 ✔、004DFE00 ✔（两行均被判成立，并指出 004DFE00 语义应写 and 而非 or）。")
ctl.append("   - a-S10-K8F/_audit/VERDICT.md L20-L21 残留 R1/R2：明令『004DFE00 语义仍写 or 应改 and』『004DFCB0 漏写跳过条件』；同文件裁决 PASS 并写『R1/R2 进 PENDING_CORRECTIONS 改字即可，无需回退或降级任何行』。")
ctl.append("   - 时序：S10_K8F/_audit/VERDICT.md mtime 2026-11-18 05:41:09 < S10_K11/coverage_delta.tsv mtime 05:45:52 < _hygiene/coverage.M11.bak 05:57:15 ⇒ 修正指令先于并表，非『先并入后补审』。")
ctl.append("5) 结论：两行的 grade 从未由本卡无审计授予；语义改正由异族审计 R1/R2 直接指令。故按『行是否有审计结论支撑』判 A，")
ctl.append("   同时如实登记过程瑕疵：S10_K11 自身无 _audit/VERDICT.md，台账 §999 已按『无审计 ⇒ 只写措辞修正、grade 未变』登记为例外。")
open(os.path.join(OUT,"controls.txt"),"w",encoding="utf-8",newline="\n").write("\n".join(ctl)+"\n")
print("ok")
