#!/usr/bin/env python3
"""R44-T2-EVID：Q4 内容判据（写域约定落地）。
写域约定(来自卡面)：EVIDENCE 是执行器自留的混合工作域，既放对象抄本也放过程输出；
目录名不是可靠声明。故按内容判：前8KiB 中「记录被测对象」的信号 vs「记录测量过程」的信号谁主导。
判不了的单列。不看 why 列。
"""
import csv, os, re

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID")
CM = os.path.join(OUT, "_content_metrics.tsv")
UL = os.path.join(OUT, "_undead_evid.tsv")

ADDR = re.compile(r"0x[0-9A-Fa-f]{6,8}")
VAINLINE = re.compile(r"@VA=|VA=0x|rva=0x|\bva=0x|imagebase=|ImageBase\s*=")
FOFF = re.compile(r"FOFF=")
CTX = re.compile(r"ctx=|\b[0-9a-fA-F]{2}( [0-9a-fA-F]{2}){6,}")
KVDATA = re.compile(r"^\s*/[\w/\[\]0-9]+\s*=")
STRUCTV = re.compile(r"struct\[\s*\d|waypoints=|iso=\(|\brc=\(|\bfnd=\d")
SECT = re.compile(r"(^|\s)(\.text|\.rdata|\.data|\.rsrc|\.detour)\s+(rva|va|raw|vsize)=")
OBJ_PATTERNS = [ADDR, VAINLINE, FOFF, CTX, KVDATA, STRUCTV, SECT]

RUNID = re.compile(r"RUN_ID\s*=")
COMMAND = re.compile(r"COMMAND\s*[:=]|Command\s*[:=]|Get-FileHash|python\s|git\s|^\s*>\s|\bdir\s+/")
TS = re.compile(r"20\d\d[-/]\d\d[-/]\d\d|\[20\d\d-")
EXIT = re.compile(r"exit\s*code|exit=|EXIT\b|returncode|退出码|退出\s*码", re.I)
BANNER = re.compile(r"^\s*(={3,}|-{3,}|#{3,}|\*{3,})")
REPORT = re.compile(r"report|日志|\blog\b|\bcommand\b.*\bexit", re.I)
PROC_PATTERNS_LINE = [COMMAND, TS, EXIT, BANNER, REPORT, RUNID]

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
    oset = set()
    pset = set()
    for i, l in enumerate(lines):
        if any(pt.search(l) for pt in OBJ_PATTERNS):
            oset.add(i)
        if any(pt.search(l) for pt in PROC_PATTERNS_LINE):
            pset.add(i)
    O = len(oset)
    P = len(pset)
    # 附加：RUN_ID 强过程信号记 +2
    if RUNID.search(t):
        P += 2
    if O >= 3 and O > P:
        return "对象抄本", O, P, "objdom"
    if P >= 2 and P >= O:
        return "过程输出", O, P, "procdom"
    return "无法判定", O, P, "tie"

# 人工内容判读标签（依据 _samples20.txt 的 HEAD + peek 深读，不看 why 列）
MANUAL = {
 1:"对象抄本", 2:"对象抄本", 3:"对象抄本", 4:"过程输出", 5:"对象抄本",
 6:"对象抄本", 7:"过程输出", 8:"过程输出", 9:"过程输出", 10:"过程输出",
 11:"对象抄本", 12:"对象抄本", 13:"过程输出", 14:"过程输出", 15:"过程输出",
 16:"过程输出", 17:"过程输出", 18:"过程输出", 19:"过程输出", 20:"过程输出",
}

def main():
    # 样本文件顺序：从 _samples20.txt 解析
    sample_rels = []
    with open(os.path.join(OUT, "_samples20.txt"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\[\d\d\]\s+(.+)", line)
            if m:
                sample_rels.append(m.group(1).strip())
    assert len(sample_rels) == 20, len(sample_rels)
    # 样本准确率
    ok = 0
    lines_out = []
    for i, rel in enumerate(sample_rels, 1):
        j, O, P, why = judge(rel)
        m = MANUAL[i]
        good = (j == m)
        ok += good
        lines_out.append(f"[{i:02d}] {rel}\n     criterion={j} (O={O},P={P},{why}) manual={m} {'OK' if good else 'MISS'}")
    print("SAMPLE_ACCURACY", ok, "/20")
    print("\n".join(lines_out))
    # 全量扫描
    with open(UL, encoding="utf-8", newline="") as f:
        allrows = list(csv.DictReader(f, delimiter="\t"))
    cnt = {}
    detailed = []
    for r in allrows:
        j, O, P, why = judge(r["rel"])
        cnt[j] = cnt.get(j, 0) + 1
        detailed.append((r["rel"], j, O, P, why))
    print("\nFULL_VERDICTS", cnt)
    with open(os.path.join(OUT, "_verdicts.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["rel", "verdict", "O", "P", "reason"])
        for row in detailed:
            w.writerow(row)
    # 分 bnform 统计各裁决
    bn = {r["rel"]: r["bnform"] for r in allrows}
    from collections import defaultdict
    byf = defaultdict(lambda: defaultdict(int))
    for rel, j, O, P, why in detailed:
        byf[bn[rel]][j] += 1
    print("\nBY_BNFORM")
    for fam in ["stdout", "stderr", "_out", "report", "其他"]:
        print(f"  {fam}: {dict(byf[fam])}")
    # 保守区间：严格子集（O>=5&P==0 或 P>=3&O==0 或 empty）作下界；criterion 全量裁决作上界
    strict_resolve = 0
    for rel, j, O, P, why in detailed:
        if why == "empty" or (O >= 5 and P == 0) or (P >= 3 and O == 0):
            strict_resolve += 1
    all_resolve = cnt.get("对象抄本", 0) + cnt.get("过程输出", 0)
    print("STRICT_RESOLVE", strict_resolve, "ALL_RESOLVE", all_resolve, "TIE", cnt.get("无法判定", 0))

if __name__ == "__main__":
    main()
