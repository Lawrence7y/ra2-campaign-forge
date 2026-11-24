#!/usr/bin/env python3
"""R44-T2-EVID：Q3 内容特征(前8KiB VA占比/横幅) + 分层抽样20件 + Q4 全量判据扫描。
只读 lead\；写只写本目录。判定不看 why 列。
"""
import csv, os, re, collections

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = os.path.join(LEAD, "next_re_20261117_r14", "R17_R81_T2_EVID")
UL = os.path.join(OUT, "_undead_evid.tsv")

VA_RE = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}")
VA_STRICT_RE = re.compile(r"^0x[0-9A-Fa-f]{6,8}")
TS_RE = re.compile(r"20\d\d[-/]\d\d[-/]\d\d[ T]\d\d:\d\d|20\d\d-\d\d-\d\d")
BANNER_RE = re.compile(r"^\s*(={3,}|-{3,}|#{3,}|\*{3,}|RUN_ID\s*=|===|\[.*\]\s*$|Shell|PS>|cmd>|C:\\|Copyright|\[?运行|\[?命令|开始时间|结束时间)")
RUNID_RE = re.compile(r"RUN_ID\s*=")
CMD_ECHO_RE = re.compile(r"(^\s*\$ |>|\.\\\\|python |Get-|capstone|pefile|Exit code|exit code|returncode|\[.*\].*ls|dir /)")

def load():
    with open(UL, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def first_8k(path):
    try:
        with open(path, "rb") as f:
            return f.read(8192).decode("utf-8", errors="replace")
    except Exception as e:
        return None

def analyze(r):
    rel = r["rel"]
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    txt = first_8k(p)
    if txt is None:
        return dict(rel=rel, ok=0, err="unreadable", va=0, nlines=0, varatio=0.0, banner=0, runid=0, ts=0, cmdecho=0, head="")
    lines = txt.splitlines()
    nonempty = [l for l in lines if l.strip()]
    n = len(nonempty) if nonempty else 1
    va = sum(1 for l in nonempty if VA_RE.match(l))
    vas = sum(1 for l in nonempty if VA_STRICT_RE.match(l))
    banner = sum(1 for l in nonempty[:20] if BANNER_RE.match(l))
    runid = 1 if RUNID_RE.search(txt) else 0
    ts = 1 if TS_RE.search(txt) else 0
    cmdecho = sum(1 for l in nonempty if CMD_ECHO_RE.search(l))
    head = " | ".join(l.strip()[:90] for l in nonempty[:6])
    return dict(rel=rel, ok=1, err="", va=va, vas=vas, nlines=len(nonempty),
                varatio=round(va/n, 4), banner=banner, runid=runid, ts=ts,
                cmdecho=cmdecho, head=head)

def main():
    rows = load()
    res = [analyze(r) for r in rows]
    with open(os.path.join(OUT, "_content_metrics.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rel", "ok", "err", "va", "vas", "nlines", "varatio", "banner", "runid", "ts", "cmdecho", "head"], delimiter="\t")
        w.writeheader()
        for x in res:
            w.writerow(x)
    # 合并 bnform
    bn = {r["rel"]: r["bnform"] for r in rows}
    ext = {r["rel"]: r["ext"] for r in rows}
    # 分层抽样：stdout 6, stderr 4, _out 2, report 2, 其他 6 = 20（result=0）
    quota = {"stdout": 6, "stderr": 4, "_out": 2, "report": 2, "其他": 6}
    byf = collections.defaultdict(list)
    for x in res:
        byf[bn[x["rel"]]].append(x)
    rng_seed = 20261122
    sample = []
    for fam in ["stdout", "stderr", "_out", "report", "其他"]:
        pool = sorted(byf[fam], key=lambda x: x["rel"])
        k = quota[fam]
        # 均匀取 k 件（步长），保证跨路径分散；其他族尽量跨 ext
        if fam == "其他":
            # 按 ext 分层：json/log/md/tsv/txt 各取，再补足
            byext = collections.defaultdict(list)
            for x in pool:
                byext[ext[x["rel"]]].append(x)
            picks = []
            order = ["json", "log", "md", "tsv", "txt"]
            for e in order:
                if byext[e]:
                    picks.append(byext[e][len(byext[e])//2])
            # 补足到 k
            for x in pool:
                if len(picks) >= k: break
                if x not in picks:
                    picks.append(x)
            picks = picks[:k]
        else:
            if len(pool) <= k:
                picks = pool
            else:
                step = len(pool)/k
                picks = [pool[int(i*step)] for i in range(k)]
        sample.extend(picks)
    # 写出样本明细（供人工阅读，不含 why）
    with open(os.path.join(OUT, "_samples20.txt"), "w", encoding="utf-8") as f:
        for i, x in enumerate(sample, 1):
            f.write(f"[{i:02d}] {x['rel']}\n")
            f.write(f"     bnform={bn[x['rel']]} ext={ext[x['rel']]} bytes={dict((r['rel'],r['bytes']) for r in rows)[x['rel']]}\n")
            f.write(f"     VA={x['va']}/{x['nlines']}={x['varatio']:.1%} VAstrict={x['vas']} banner_lines={x['banner']} RUN_ID={x['runid']} TS={x['ts']} cmdecho={x['cmdecho']}\n")
            f.write(f"     HEAD: {x['head'][:400]}\n\n")
    print("SAMPLES", len(sample))
    print("WROTE _content_metrics.tsv and _samples20.txt")
    # 打印全量统计摘要（供 Q4）
    n = len(res)
    high_va = sum(1 for x in res if x["varatio"] >= 0.10)
    mid_va = sum(1 for x in res if 0.02 <= x["varatio"] < 0.10)
    low_va = sum(1 for x in res if x["varatio"] < 0.02)
    has_banner = sum(1 for x in res if x["banner"] > 0 or x["runid"] or x["ts"])
    empty = sum(1 for x in res if x["nlines"] == 0)
    print(f"FULL n={n} highVA(>=10%)={high_va} midVA(2-10%)={mid_va} lowVA(<2%)={low_va} bannerOrTSorRunid={has_banner} empty={empty}")

if __name__ == "__main__":
    main()
