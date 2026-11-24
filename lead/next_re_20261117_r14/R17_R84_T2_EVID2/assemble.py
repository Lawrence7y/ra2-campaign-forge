#!/usr/bin/env python3
# 组装 R45-T2-EVID2\REPORT.md：六行交付 + 支撑明细（明细表由已核验文件生成，避免手抄误差）
import os, re
R=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R84_T2_EVID2"
feat=open(os.path.join(R,"q2_sample40_features.txt"),encoding="utf-8").read().splitlines()
verd=open(os.path.join(R,"q2_sample40_verdicts.txt"),encoding="utf-8").read().splitlines()

items=[]; cur=None
for ln in feat:
    m=re.match(r"\[(\d\d)\] (.+)",ln)
    if m:
        cur={"no":int(m.group(1)),"rel":m.group(2).strip()}; items.append(cur); continue
    if cur is None: continue
    if "VA=" in ln and "包装=" in ln: cur["feat"]=ln.strip()
    if "首行=" in ln: cur["first"]=ln.strip()[len("首行="):]
vmap={}
for ln in verd:
    m=re.match(r"\[(\d\d)\] 我判=(\S+) \| (.+)",ln)
    if m: vmap[int(m.group(1))]=(m.group(2),m.group(3))

rows=[]
for it in items:
    no=it["no"]; jd,why=vmap.get(no,("?",""))
    va=re.search(r"VA=([^ ]+)",it.get("feat","")); va=va.group(1) if va else "?"
    wrap=re.search(r"包装=(\S+)",it.get("feat","")); wrap=wrap.group(1) if wrap else "?"
    zh=re.search(r"中文=(\S+)",it.get("feat","")); zh=zh.group(1) if zh else "?"
    first=it.get("first","")[:64]
    rows.append(f"| {no:02d} | {it['rel']} | VA={va} | {wrap} | {zh} | {first} | {jd} |")
detail="\n".join(rows)

q1="Q1 | 266 件冲突类型分布: 名过内象=6件/4084B ; 名象内过=6件/58168B ; 两者都弱=254件/4902957B（合计266件/4965209B ; 源=R17_R78_T1_RECLASS\\files_excluded_prime.tsv 列 rel/label/bytes 取1242 − R17_R81_T2_EVID\\_verdicts.tsv 列 verdict 已裁976 ; 脚本=analyze.py/explore_q1.py） | 主因=绝大多数(254/266=95.5%)并非真正的名-内容对立，而是内容信号本身弱：262/266 件前8KiB行首VA=0、无强过程帧、O/P 双低而平票；名字与内容真正反向的仅12件（6+6）。"

q2="Q2 | 40 件抽样（分层 名过内象10/名象内过6/两者都弱24 ; 前8KiB ; 未看任何 label/why/verdict）: 对象=29 / 过程=10 / 判不了=1 ; 摘要=行首VA几乎全为0%(262/266整体如此)，对象件多靠「地址与字节/虚表/反汇编/字节diff」语义判定而非VA行 ; 明细40行见下方附录与 q2_sample40_features.txt（VA%/包装/中文/首行80字）+ q2_sample40_verdicts.txt（逐件理由）。"

q3="Q3 | 同目录多数派可用: 是（有条件） | 规则=同一 EVIDENCE 父目录内「已裁件」(对象抄本+过程输出)≥3 且同向占比≥75% ⇒ 该目录内的平票件随多数派裁定 ; 留一法校验=663/688=96.4%（只统计触发规则的目录）; 266 件覆盖率=114件/1995960B（余152件/2969249B继续单列 ; 更严的100%一致口径=80件）; 源=R17_R81_T2_EVID\\_verdicts.tsv 列 rel/verdict + _undead_evid.tsv 列 bytes ; 脚本=q3_final.py。"

q4="Q4 | _audit 写域约定 3 处: a-S15S16-3B2.md:42:「- `S15S16_3B2\\_audit\\VERDICT.md`：逐行一节，含上述四件事的地址与字节 + 最终判定」 ; a-SEMFIX-BATCH.md:48:「- `<批次目录>\\_audit\\VERDICT.md`：逐行一节，含上述五件事的地址与字节 + 判定」 ; a-S09-KPROVED8.md:51:「- 每行一节：entry、你的 PASS / FAIL 判定、上述 5 个核查点的地址与字节、一句结论。」 ; C′ 中 _audit=540件/67129511B（按目录段「_audit」计 ; 若按路径含子串「audit」则868件/74089751B，多出的是 c07_gate_audit 等卡名非 _audit 目录）, P1a 占=527件/66864593B=97.59%(件)/99.61%(字节) | 结论=必须逐件判。"

q5="Q5 | 正控: 法1(Python posctrl_py.py)=Q1 1242−976=266(direct/ reason_tie 亦=266) ; Q4 _audit 540件/67129511B(P1a 527件/66864593B) ; 法2(PowerShell posctrl_ps.ps1)=Q1 266 ; Q4 540件/67129511B(P1a 527件) | 一致。"

overall="OVERALL | 两块都能再收一档、但都不能整体归边：EVIDENCE 的266件里真冲突仅12件、254件是内容信号弱，用「同目录多数派」可再裁114件（留一法96.4%），未决可从266降到152；_audit 是「地址与字节+判定」的混合审计写域，C′ 内97.6%件P1a对象抄本（应留）、但同目录段排除集另有1111件过程/元记录（应排），故按内容逐件判、不整体划到过程侧。"

six="\n".join([q1,q2,q3,q4,q5,overall])

body=f"""# R45-T2-EVID2 · 收敛 EVIDENCE 那 266 件平票 + 定 _audit 归属

执行员：t2-evid2　日期：2026-11-22（本地）
写目标：lead\\next_re_20261117_r14\\R17_R84_T2_EVID2\\（唯一写目标）
只读 lead\\；未运行 mev675.py；未写 lead\\ 下任何既有目录。

---

## 一 · 六行交付（严格照卡 §四格式）

```
{six}
```

---

## 二 · 源与口径（纪律 1/3/4）

- **266 件的来源**：R17_R78_T1_RECLASS\\files_excluded_prime.tsv（6011 行，列 rel/ext/bytes/label/why/family）。取 label=UNDECIDED 且 rel 含 EVIDENCE（大小写不敏感）=1242 件（含 1 件小写 evidence 路径 `next_re_20261112_r03/W86_render_channel/evidence/recon_stdout.txt`）。上一轮已裁 976 件见 R17_R81_T2_EVID\\_verdicts.tsv 列 verdict∈{{对象抄本(732), 过程输出(244)}}；1242−976=266，与该文件 verdict=无法判定/reason=tie 的 266 行集合逐一相同。266 件合计 4,965,209 B。
- **Q1 冲突类型判据**（名字信号只看 basename 词、内容倾向只看 O/P 行计数，均不使用 label/why）：
  - 名字说过程 = basename 含 stdout/stderr/_out/report/log/selftest/check/probe/status/summary/verdict/exit/cmd/gen_/build/validat/reject/perf 等 ; 名字说对象 = 含 row_/disasm/bytes/addr/site/table/vtable/struct/insn/dump/map/ref/fact/index/rtti 等 ; 两类皆含或皆不含 = 弱。
  - 内容倾向 = O>P 记对象、P>O 记过程、O==P 记平（O/P 为 R17_R81_T2_EVID\\judge_q4_v2.py 在前8KiB 统计的"对象信号行/过程信号行"计数）。
  - 名过内象 = 名字过程 ∧ 内容对象 ; 名象内过 = 名字对象 ∧ 内容过程 ; 其余 = 两者都弱。
  - 交叉表（件/字节）：名过×内象 6/4084 ; 名过×内过程 14/199336 ; 名过×平 28/35795 ; 名对象×内对象 74/304475 ; 名对象×内过程 6/58168 ; 名对象×平 60/2115301 ; 名弱×内对象 19/971769 ; 名弱×内过程 10/120896 ; 名弱×平 49/1155385。
- **Q2 抽样**：40 件，按 Q1 三类配额 10/6/24，每类内按 rel 字典序等距取；对歧义件实读前 1500 B 佐证。全程未读任何既有 label/why/verdict 作判据。判定按卡 §一写域约定：记被测对象（地址/字节/虚表/反汇编/字节diff/hash 等）=对象抄本；记测量过程（RUN_ID/横幅/时间戳/selftest 断言/perf/实验清单/构建日志/统计命中率）=过程输出；两者相当=判不了。
- **Q3 同目录多数派**：目录=rel 的父目录（多为 .../EVIDENCE）。分母只用已裁件（对象+过程），与卡例"8 件里 6 件对象抄本 ⇒ 其余 2 件也算对象"同口径。留一法（隐藏一件已裁件的 verdict、用同目录其余已裁件多数派回测）在触发规则的目录上 663/688=96.4%；全量已裁件口径 784/919=85.3%。
- **Q4 _audit 统计**：R17_R78_T1_RECLASS\\files_tier_Cprime.tsv（C′，18712 行/1,363,708,720 B）。按 rel 路径**目录段**严格等于 `_audit` 计 540 件/67,129,511 B；P1a = why 前缀 `P1a_对象抄本`（内容有地址，见上一轮 R17_R78_T1_RECLASS\\REPORT.md 判据表）=527 件/66,864,593 B。按子串 "audit" 宽松计 868 件/74,089,751 B，多出的 328 件是 c07_gate_audit、_lead_audit、dlc_capability_audit 等**卡名/目录名**含 audit 但非 `_audit` 目录（见 find 脚本）。
- **Q4 结论依据**：三处写域约定均指向 `_audit\\VERDICT.md` = "逐行一节，含…地址与字节 + 判定"，即审计员自留的"对象事实 + 过程判定"混合域（与 EVIDENCE 同类）。事实佐证：C′ 内 540 件 97.6%(件)/99.6%(字节) 是 P1a 带地址对象抄本（应留），但同口径排除集 files_excluded_prime.tsv 里另有 1111 件 `_audit` 被判过程/元记录（EXCL 840：E3_元记录目录 567、E1_工具流出物 189、E2_包壳脚本流出物 84 等 ; UNDECIDED 271）。故不是整体过程区也不是整体对象区，须逐件判。
- **Q5 正控**：两实现互不复用代码——法1 Python csv.DictReader，法2 PowerShell 逐行 Split；对 Q1 的 266 与 Q4 的 540 件/67,129,511 B 各项完全一致。

---

## 三 · Q2 40 件抽样明细（对应六行第 2 行）

| # | 路径 | VA | 包装 | 中文 | 首行原文(截断) | 我判 |
|---|---|---|---|---|---|---|
{detail}

逐件判定理由见 q2_sample40_verdicts.txt；原始特征（VA 占比/包装/中文/首行80字）见 q2_sample40_features.txt。

---

## 四 · 产物清单

- 主分析与中间结果：analyze.py、explore_q1.py、find_discrep.py、dump_tie.py、peek_ambig.py、q1_tie_detail.tsv、q1_summary.txt、q3_summary.txt、q3_summary2.txt、q3_final.py、q3_final.txt、q2_verdicts_and_q3b.py、q2_sample40_features.txt、q2_sample40_verdicts.txt、posctrl_py.py、posctrl_ps.ps1、assemble.py、REPORT.md。
- 判不了/未取得：Q2 中 1 件（w173_selfaudit.txt，过程自检与对象地址混合）判不了，已单列计数，未硬塞；本次所有需要的数均取得，无"未取得"项。
"""
open(os.path.join(R,"REPORT.md"),"w",encoding="utf-8").write(body)
print("wrote REPORT.md; detail rows",len(rows))
print("=== SIX LINES ===")
print(six)
