# -*- coding: utf-8 -*-
"""生成 CARD_VERDICTS.tsv / VIOLATIONS.tsv。
行数由文件现算；判定与审计依据来自本目录 PROGRESS.md 记载的逐条核查（见 EVIDENCE\）。
"""
import os, re, json

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT  = os.path.join(ROOT,"RECON_UNMERGED")
CUR  = os.path.join(ROOT,"COVERAGE","coverage.tsv")
ENTRY_RE = re.compile(r"^[0-9A-Fa-f]{8}$")

CARDS = ["S01_KPROVED","S03_C8","S05_KPROVED4","S05_KPROVED5","S05-K2","S07-K2",
"S09_KPROVED2","S10_K11","S10_K14","S10_KPROVED4","S11_DIRECT","S11_K5","S13_DIRECT",
"S13_K11","S13_KPROVED2","S15_K5","S16_N2","S19-K2","S21_KPROVED2","SEMFIX_6",
"SEMFIX_REST","SEMFIX_S10","SEMFIX_SLOTS","SEMFIX_SLOTS2","SEMFIX_SLOTS3","W177_KA"]

def delta_rows(card):
    p=os.path.join(ROOT,card,"coverage_delta.tsv")
    rows=[]
    if not os.path.exists(p): return rows
    for ln in open(p,encoding="utf-8",errors="replace"):
        p0=ln.split("\t")[0].strip()
        if ENTRY_RE.match(p0): rows.append(p0.upper())
    return rows

cur={}
for l in open(CUR,encoding="utf-8",errors="replace"):
    if l.startswith("entry,"): continue
    p=l.rstrip("\n").split("\t")
    if len(p)==8: cur[p[0].strip().upper()]={"grade":p[4],"sem":p[3],"name":p[2],"ev":p[5]}

# card -> (判定, 并入行数, 审计依据/缺失说明, 并入的 M 卡)
V = {
 "S01_KPROVED":  ("B",0,"delta 0 数据行（仅表头 + 注释 '# 0 data rows'）：无行可并，盘上无本卡痕迹","-"),
 "S03_C8":       ("B",0,"delta 0 数据行（仅表头）：无行可并","-"),
 "S05_KPROVED4": ("B",0,"3 行均未并：盘上 grade 仍 [静态推断]，语义与 delta 不符（3/3 sem_disk=N）","-"),
 "S05_KPROVED5": ("B",0,"delta 0 数据行（表头 + 注释 '# 0 data rows ...'）：无行可并","-"),
 "S05-K2":       ("B",0,"24 行均未并：语义 0/24 落盘（sem_disk=N），grade 仍 [静态推断]","-"),
 "S07-K2":       ("B",0,"2 行均未并：语义 0/2 落盘；00551A30 盘上仍 [未证]、delta 求 [已证]","-"),
 "S09_KPROVED2": ("A",6,"a-S09-KPROVED2（写于共享 _audit\\VERDICT.md，PARTIAL：6 行白名单 / 0069DEB0 黑名单）；M40 按该白名单并 6 行 grade+evidence_path；语义后由 M42 以 SEMFIX_SLOTS 文本落盘（同引该审计）","M40(+M42 语义)"),
 "S10_K11":      ("A",2,"a-S10-K8 判两行 ✔（004DFCB0/004DFE00）+ a-S10-K8F PASS 明令 R1/R2 改字；M11 仅改语义措辞、grade 未变。过程瑕疵：本卡无自身 _audit\\VERDICT.md，台账 §999 已按「无审计⇒只改措辞」登记","M11"),
 "S10_K14":      ("A",1,"M16 并 name+语义（删编造表/幽灵被调，grade 未动、按卡面维持 [静态推断]）；其后 M41 以 S10_KPROVED2/_audit/VERDICT.md#18 升 [已证]，有审计依据","M16(+M41 grade)"),
 "S10_KPROVED4": ("B",0,"delta 0 数据行（仅表头）：无行可并","-"),
 "S11_DIRECT":   ("B",0,"8 行均未并：语义是 delta 从盘上抄的（首次出现于 M6_before，早于 delta mtime 11-18 14:59），grade 盘上仍 [静态推断]、delta 求 [已证] 未采纳","-"),
 "S11_K5":       ("B",0,"11 行均未并：语义 0/11 落盘（sem_disk=N）","-"),
 "S13_DIRECT":   ("B",0,"delta 0 数据行（仅表头）：无行可并","-"),
 "S13_K11":      ("B",0,"9 行均未并：盘上 grade 仍 [静态推断]，语义 0/9 落盘","-"),
 "S13_KPROVED2": ("B",0,"delta 0 数据行（仅表头）：无行可并","-"),
 "S15_K5":       ("B",0,"delta 0 字节（空文件）：无行可并","-"),
 "S16_N2":       ("B",0,"delta 0 数据行（仅表头）：无行可并","-"),
 "S19-K2":       ("B",0,"18 行均未并：盘上 grade 仍 [静态推断]/[未证]，语义 0/18 落盘","-"),
 "S21_KPROVED2": ("B",0,"delta 0 数据行（仅表头）：无行可并","-"),
 "SEMFIX_6":     ("A",6,"AUDIT_SEM_SELF/ROW_VERDICTS.tsv 6/6 行判 P1（③b 成立）；M36 入队。grade 两栏原本就是 [已证]，本卡只重写语义","M36"),
 "SEMFIX_REST":  ("A",41,"AUDIT_SEM_SELF/ROW_VERDICTS.tsv 41/41 行判 P1；M35 入队。grade 未变（绝大多数基线即 [已证]）","M35"),
 "SEMFIX_S10":   ("A",25,"AUDIT_SEM_SELF/ROW_VERDICTS.tsv 25/25 行判 P1；M35 入队。grade 未变","M35"),
 "SEMFIX_SLOTS": ("A",36,"grade 由 M37(a-S08-KPROVED2 6 行)/M40(S03_C5 3 + a-S09-KPROVED2 5)/M41(S09_KPROVED3 4 + S10_KPROVED2 8) 按各自 _audit\\VERDICT 白名单提级；语义由 M42 按 SEMFIX_SLOTS delta 落盘（grade 未变）。36/36 行有审计出处","M37/M40/M41(+M42 语义)"),
 "SEMFIX_SLOTS2":("A",11,"a-S03_C6 4 行 + a-S10_KPROVED3 7 行；M44 组1并入，逐行 cite 该两份 _audit\\VERDICT.md","M44"),
 "SEMFIX_SLOTS3":("A",15,"a-S05_KPROVED3 7 行（PASS 有条件）+ a-S09_KPROVED5 8 行（有条件 PASS）；M45 并入（M44 曾以「组2拦下」拒绝提级，未越权）","M45"),
 "W177_KA":      ("B",0,"delta 0 字节（空文件）：无行可并","-"),
}

lines=["card\tdelta_rows\tmerged_rows\tverdict\taudit_basis_or_missing"]
tot={}
for c in CARDS:
    rows=delta_rows(c)
    v,m,basis,by=V[c]
    tot[v]=tot.get(v,0)+1
    lines.append("%s\t%d\t%d\t%s\t%s"%(c,len(rows),m,v,basis))
open(os.path.join(OUT,"CARD_VERDICTS.tsv"),"w",encoding="utf-8",newline="\n").write("\n".join(lines)+"\n")

# VIOLATIONS.tsv：C 类为空
vi=["entry\tcard\tmerged_by\tmissing_audit"]
VIOL=[]
if VIOL:
    for x in VIOL: vi.append("\t".join(x))
else:
    vi.append("# NO C-CLASS ROWS: 26 张卡的 delta 行中，凡已落盘者均能追到异族审计裁决；未落盘者为 B 类。")
open(os.path.join(OUT,"VIOLATIONS.tsv"),"w",encoding="utf-8",newline="\n").write("\n".join(vi)+"\n")

print("cards:",len(CARDS),"verdicts:",tot)
print("total delta rows:",sum(len(delta_rows(c)) for c in CARDS))
print("total merged rows:",sum(V[c][1] for c in CARDS))
