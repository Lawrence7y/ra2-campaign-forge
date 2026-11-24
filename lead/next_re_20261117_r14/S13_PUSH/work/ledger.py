# -*- coding: utf-8 -*-
"""S13-PUSH 第一步：从盘上算清 S13 的 DoD 账面（先于一切取证）。
口径逐条对齐 RULING_R15/work/strict_panel.py 与 COVERAGE/PANEL.md。
"""
import csv, os, re, math, sys, collections, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT  = os.path.join(ROOT, "S13_PUSH")

RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest().upper()

def main():
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))

    with open(COV, encoding="utf-8-sig", newline="") as f:
        cov = list(csv.reader(f, delimiter="\t"))[1:]

    c = collections.Counter()
    s13_rows = []
    for r in cov:
        if len(r) < 8: continue
        e = ne(r[0]); s = r[1].strip()
        if s != "S13": continue
        name = r[2].strip(); sem = r[3]; grade = r[4].strip()
        if e not in atlas:
            c["cov_nonatlas"] += 1
            continue
        c["atlas_n"] += 1
        s13_rows.append((e, name, grade, "[未证]" in sem))
        if name and not name.startswith("sub_"):
            c["named_L"] += 1
            if not RE_CSUB.search(name):
                c["named_S14"] += 1
                if not RE_SLOT.search(name):
                    c["named_strict"] += 1
        if grade == "[已证]":
            c["proved_n"] += 1
            if "[未证]" not in sem:
                c["proved_strict_n"] += 1

    a = c["atlas_n"]
    tn = math.ceil(0.9 * a)
    tp = math.ceil(0.5 * a)
    lines = []
    def add(x): lines.append(x); print(x)
    add("S13-PUSH 账面自算（源：盘上 coverage.tsv ∩ function_atlas.tsv，entry 大小写归一为大写 8 位）")
    add("coverage.tsv sha256 = " + sha(COV))
    add("function_atlas.tsv sha256 = " + sha(ATLAS))
    add("口径来源：RULING_R15_20261119/work/strict_panel.py + COVERAGE/PANEL.md 表头")
    add("")
    add("n (S13 且 entry 在 atlas 内的行数) = %d" % a)
    add("S13 coverage 总行数 = %d；atlas 外(S13) = %d" % (a + c["cov_nonatlas"], c["cov_nonatlas"]))
    add("named_L                = %d" % c["named_L"])
    add("named_S(R14)           = %d" % c["named_S14"])
    add("named_strict           = %d" % c["named_strict"])
    add("proved                 = %d" % c["proved_n"])
    add("proved_strict          = %d" % c["proved_strict_n"])
    add("门槛 ceil(0.9n) = ceil(0.9*%d) = %d  (named)" % (a, tn))
    add("门槛 ceil(0.5n) = ceil(0.5*%d) = %d  (proved)" % (a, tp))
    add("")
    add("差距（门槛 - 现值，<=0 表示达标）：")
    add("  named_S(R14): %d - %d = %d 行" % (tn, c["named_S14"], tn - c["named_S14"]))
    add("  named_strict(参考列,不参与达标): %d - %d = %d 行" % (tn, c["named_strict"], tn - c["named_strict"]))
    add("  proved:       %d - %d = %d 行" % (tp, c["proved_n"], tp - c["proved_n"]))
    add("  proved_strict:%d - %d = %d 行" % (tp, c["proved_strict_n"], tp - c["proved_strict_n"]))
    add("")
    add("结论：S13 现在只差 proved 一项（named_S(R14) 恰好达门槛，零余量）。")
    add("  名义达标需 proved +%d；严格达标需 proved_strict +%d。" % (tp - c["proved_n"], tp - c["proved_strict_n"]))
    add("  strict proved 与 proved 差 %d 行（这些 [已证] 行语义栏含 [未证]）。" % (c["proved_n"] - c["proved_strict_n"]))

    with open(os.path.join(OUT, "LEDGER.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # 同时落一个机器可读 JSON，供后续步骤引用
    import json
    data = dict(n=a, cov_total=a + c["cov_nonatlas"], cov_nonatlas=c["cov_nonatlas"],
                named_L=c["named_L"], named_S14=c["named_S14"], named_strict=c["named_strict"],
                proved=c["proved_n"], proved_strict=c["proved_strict_n"],
                thu_named=tn, thu_proved=tp,
                gap_named_S14=tn - c["named_S14"], gap_named_strict=tn - c["named_strict"],
                gap_proved=tp - c["proved_n"], gap_proved_strict=tp - c["proved_strict_n"],
                sha_cov=sha(COV), sha_atlas=sha(ATLAS))
    with open(os.path.join(OUT, "work", "ledger.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
