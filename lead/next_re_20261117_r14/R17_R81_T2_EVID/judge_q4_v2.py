#!/usr/bin/env python3
"""R44-T2-EVID：Q4 最终内容判据（v2）。
写域约定：EVIDENCE 是执行器自留的混合工作域，既放对象抄本也放过程输出；目录名不是可靠声明。
按内容判：前8KiB「记录被测对象」信号 vs「记录测量过程」信号谁主导。强过程帧头直接判过程。
不看 why 列。
"""
import csv, os, re

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID")
UL = os.path.join(OUT, "_undead_evid.tsv")

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

def first8k(path):
    try:
        with open(path, "rb") as f:
            return f.read(8192).decode("utf-8", errors="replace")
    except Exception:
        return None

def judge(rel):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    t = first8k(p)
    if t is None:
        return "无法判定", 0, 0, "unreadable"
    lines = [l for l in t.splitlines() if l.strip()]
    if not lines:
        return "过程输出", 0, 1, "empty"
    head10 = "\n".join(lines[:10])
    strong = bool(RUNID_EQ.search(head10) or COMMAND_EQ.search(head10) or RUNAT.search(head10) or PYVER.search(head10) or BUILDRPT.search(head10))
    oset, pset = set(), set()
    for i, l in enumerate(lines):
        if any(pt.search(l) for pt in OBJ_PATTERNS):
            oset.add(i)
        if any(pt.search(l) for pt in PROC_PATTERNS_LINE):
            pset.add(i)
    O, P = len(oset), len(pset)
    if strong:
        return "过程输出", O, P, "strong-proc-frame"
    if O >= 3 and O > P:
        return "对象抄本", O, P, "objdom"
    if O == 0 and P >= 1:
        return "过程输出", O, P, "proc-only"
    if len(lines) <= 5 and O == 0:
        return "过程输出", O, P, "tiny-status"
    return "无法判定", O, P, "tie"

MANUAL = {
 1:"对象抄本", 2:"对象抄本", 3:"对象抄本", 4:"过程输出", 5:"对象抄本",
 6:"对象抄本", 7:"过程输出", 8:"过程输出", 9:"过程输出", 10:"过程输出",
 11:"对象抄本", 12:"对象抄本", 13:"过程输出", 14:"过程输出", 15:"过程输出",
 16:"过程输出", 17:"过程输出", 18:"过程输出", 19:"过程输出", 20:"过程输出",
}

def main():
    sample_rels = []
    with open(os.path.join(OUT, "_samples20.txt"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\[\d\d\]\s+(.+)", line)
            if m:
                sample_rels.append(m.group(1).strip())
    ok = 0
    for i, rel in enumerate(sample_rels, 1):
        j, O, P, why = judge(rel)
        m = MANUAL[i]
        good = (j == m)
        ok += good
        print(f"[{i:02d}] {j} (O={O},P={P},{why}) manual={m} {'OK' if good else 'MISS'} {rel}")
    print("SAMPLE_ACCURACY", ok, "/20")
    with open(UL, encoding="utf-8", newline="") as f:
        allrows = list(csv.DictReader(f, delimiter="\t"))
    cnt, detailed = {}, []
    for r in allrows:
        j, O, P, why = judge(r["rel"])
        cnt[j] = cnt.get(j, 0) + 1
        detailed.append((r["rel"], j, O, P, why))
    print("FULL_VERDICTS", cnt)
    with open(os.path.join(OUT, "_verdicts.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t"); w.writerow(["rel","verdict","O","P","reason"])
        for row in detailed: w.writerow(row)
    from collections import defaultdict
    bn = {r["rel"]: r["bnform"] for r in allrows}
    byf = defaultdict(lambda: defaultdict(int))
    for rel, j, O, P, why in detailed:
        byf[bn[rel]][j] += 1
    for fam in ["stdout", "stderr", "_out", "report", "其他"]:
        print("BY_BNFORM", fam, dict(byf[fam]))
    strict = sum(1 for rel,j,O,P,why in detailed if why in ("empty","tiny-status") or (O>=5 and P==0) or (P>=3 and O==0))
    allres = cnt.get("对象抄本",0)+cnt.get("过程输出",0)
    print("STRICT_RESOLVE", strict, "ALL_RESOLVE", allres, "TIE", cnt.get("无法判定",0))

if __name__ == "__main__":
    main()
