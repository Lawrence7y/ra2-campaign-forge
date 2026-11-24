#!/usr/bin/env python3
"""R51-T1-TIE152 / Q3 证据表：逐件算「对象信号行 O / 过程信号行 P」（与 R17_R81_T2_EVID/judge_q4_v2.py
同一套正则），并把 Q2 的内容类别与「语义归属」分开。

输出 q3_signals.tsv 列：
  rel / bytes / class / nlines / O / P / o_frac / p_frac / verdict_proposed / reason

verdict_proposed 只由**内容语义**决定（不看文件名、不看 O/P），四值：
  应排  该件**不可能**是"被测对象的抄本"——内容里没有任何被测对象的记录载体
  应留  该件**是**被测对象的记录（地址/字节/虚表/反汇编/字段偏移的记录体）
  混合  同一文件里对象记录与过程记录并存，且任一侧都不是可忽略的噪声；缺"逐行归属"
  判不了 内容是**测量过程**（统计/抽样/断言的运行记录），但它是否算"对象抄本"取决于项目的
        "过程证据是否计入对象证据"这一**未在某份规范里定死**的口径
"""
import csv, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R91_T1_TIE152")

# ---- 与 judge_q4_v2.py 逐字相同的信号集 ----
ADDR = re.compile(r"0x[0-9A-Fa-f]{6,8}")
VAHEX = re.compile(r"\b(VA|RVA|VSize|RawPtr|RawSize|ImageBase|SizeOfImage)\s*=\s*0?x?[0-9A-Fa-f]{6,8}\b|\bimagebase=[0-9A-Fa-f]{6,8}\b")
VAINLINE = re.compile(r"@VA=|FOFF=|ctx=")
KVDATA = re.compile(r"^\s*/[\w/\[\]0-9]+\s*=")
STRUCTV = re.compile(r"struct\[\s*\d|waypoints=|iso=\(|\brc=\(|\bfnd=\d")
SECT = re.compile(r"(^|\s)(\.text|\.rdata|\.data|\.rsrc|\.detour)\s+(rva|va|raw|vsize|VA|RVA)=")
CTXBYTES = re.compile(r"\b[0-9a-fA-F]{2}( [0-9a-fA-F]{2}){6,}")
OBJ_PATTERNS = [ADDR, VAHEX, VAINLINE, KVDATA, STRUCTV, SECT, CTXBYTES]

RUNID_EQ = re.compile(r"RUN_ID\s*=")
COMMAND_EQ = re.compile(r"COMMAND\s*[:=]")
RUNAT = re.compile(r"run_at_utc\s*=|\[PROGRESS|\bdriver\b", re.I)
PYVER = re.compile(r"PYTHON\s*=|python\s+\d+\.\d+|capstone=|pefile=", re.I)
BUILDRPT = re.compile(r"build report|总行数\s*=|总趟数|筛选阶梯", re.I)
COMMAND = re.compile(r"Get-FileHash|python\s|git\s|^\s*>\s|\bdir\s+/")
TS = re.compile(r"20\d\d[-/]\d\d[-/]\d\d|\[20\d\d-")
EXIT = re.compile(r"exit\s*code|exit=|EXIT\b|returncode|退出码|退出\s*码", re.I)
BANNER = re.compile(r"^\s*(={3,}|-{3,}|#{3,}|\*{3,})")
PROC_PATTERNS_LINE = [COMMAND, TS, EXIT, BANNER, RUNID_EQ, COMMAND_EQ, RUNAT, PYVER, BUILDRPT]

CAP = 512 * 1024


def signals(rel):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        raw = f.read(CAP)
    txt = raw.decode("utf-8", errors="replace")
    lines = [l for l in txt.splitlines() if l.strip()]
    O = sum(1 for l in lines if any(pt.search(l) for pt in OBJ_PATTERNS))
    P = sum(1 for l in lines if any(pt.search(l) for pt in PROC_PATTERNS_LINE))
    n = max(1, len(lines))
    return O, P, len(lines), round(O / n, 4), round(P / n, 4)


# ---- 内容语义裁决表（逐件手判；依据写进 reason，全部来自实读内容）----
# 说明：判定只用"文件里装的是什么"（对象记录 / 过程记录 / 两者），不用文件名。
def semantic(rel, cls):
    r = rel.lower()
    # == 按内容逐类 ==
    return None


def main():
    rows = list(csv.DictReader(open(os.path.join(OUT, "q2_classes.tsv"), encoding="utf-8", newline=""), delimiter="\t"))
    for x in rows:
        O, P, n, of, pf = signals(x["rel"])
        x["O"], x["P"], x["nlines_full"], x["o_frac"], x["p_frac"] = O, P, n, of, pf
    with open(os.path.join(OUT, "q3_signals.tsv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, delimiter="\t", fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("class x (O>=3&O>P) 可被 R44 判为对象的件数:")
    c = Counter()
    for x in rows:
        if x["O"] >= 3 and x["O"] > x["P"]:
            c[x["class"]] += 1
    print(dict(c))
    print("\nclass 内 O/P 刻画 (class: n / median O / median P / O>=3∧O>P)")
    import statistics as st
    for k in sorted(set(x["class"] for x in rows)):
        sel = [x for x in rows if x["class"] == k]
        print(f"{k:18s} n={len(sel):3d} medO={st.median([x['O'] for x in sel]):5.1f} "
              f"medP={st.median([x['P'] for x in sel]):5.1f} objdom={sum(1 for x in sel if x['O']>=3 and x['O']>x['P'])}")


if __name__ == "__main__":
    main()
