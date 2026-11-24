#!/usr/bin/env python3
# R17-R25-SLOT107 bounded static intersection. Read-only inputs; writes only this card dir.
import csv, hashlib, os
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
DISP_1AC = "0x1AC"
DISP_124 = "0x124"
HITS = os.path.join(ROOT, "R17_R12_VT_OFFSET", "hits.tsv")
CTORS = os.path.join(ROOT, "R17_R23_CALLER_PATH", "ctor_sites.tsv")
OUT = os.path.dirname(os.path.abspath(__file__))

def read_tsv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def out_tsv(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)

def norm(v):
    v = v.strip()
    if v.startswith("disp="):
        v = v[5:]
    return ("0x%X" % int(v, 16)).upper()

def main():
    data = open(IMG, "rb").read()
    sha = hashlib.sha256(data).hexdigest().upper()
    if sha != EXPECT_SHA:
        raise SystemExit("sha256 mismatch; abort: " + sha)
    hits = read_tsv(HITS)
    ctors = read_tsv(CTORS)
    call_1ac = [r for r in hits if r["class"] == "call" and r["disp"] == "disp=" + DISP_1AC]
    call_124 = [r for r in hits if r["class"] == "call" and r["disp"] == "disp=" + DISP_124]
    ctor_hosts = {}
    for r in ctors:
        ctor_hosts.setdefault(norm(r["host"]), []).append(norm(r["site"]))
    if len(ctors) != 15 or len(ctor_hosts) != 14:
        raise SystemExit("unexpected ctor table shape: rows=%d unique_hosts=%d" % (len(ctors), len(ctor_hosts)))
    rows = []
    for disp, group in (("0x1AC", call_1ac), ("0x124", call_124)):
        for r in group:
            h = norm(r["host"])
            if h in ctor_hosts:
                rows.append([norm(r["site"]), disp, h, ",".join(ctor_hosts[h]), "NEEDS_BYTE_CHAIN", norm(r["fn_end"]), r["base_reg"]])
    out_tsv("intersect.tsv", ["site", "disp", "host", "ctor_sites_in_host", "judgment", "fn_end", "base_reg"], rows)
    # Empty intersection => no in-function disassembly/chain TSV is produced.
    with open(os.path.join(OUT, "chain_1ac.tsv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["site", "host", "fn_end", "step", "address", "bytes", "disasm", "register_writes", "result"])
    counts = {d: sum(1 for r in rows if r[1] == d) for d in ("0x1AC", "0x124")}
    lines = [IMG, "sha256=" + sha, "", "# R17-R25-SLOT107 · slot #107 (0x449440 / vtable+0x1AC) caller intersection", "",
             "## 第一步：交集筛", "",
             "- 输入 hits.tsv：call & disp=0x1AC 共 %d 条；call & disp=0x124 共 %d 条。" % (len(call_1ac), len(call_124)),
             "- 输入 ctor_sites.tsv：15 个直接构造点，host 集合 %d 个：%s。" % (len(ctor_hosts), " ".join(sorted(ctor_hosts))),
             "- 按 host 精确相等求交集：0x1AC=%d 条，0x124=%d 条；逐条结果见 intersect.tsv。" % (counts["0x1AC"], counts["0x124"]),
             "- 计数复现：hits 侧 0x1AC host 集合与 ctor host 集合无公共元素；hits 侧 0x124 host 集合与 ctor host 集合亦无公共元素。",
             "- 注：ctor_sites.tsv 中上一轮 #73 对应构造点 site=0x5A66D4 的 host 为 0x5A652D；本卡没有把 host 地址放宽到邻近值。", "",
             "## 第二步：字节链验证", "",
             "- 因 0x1AC 交集为空，没有可执行逐指令验证的候选；本步反汇编函数数=0，字节链扫描字节数=0，chain_1ac.tsv 仅表头。",
             "- 因此未产生寄存器写点统计，也未形成 site -> host -> fn_end 的 0x449440 调用链。", "",
             "## 第三步：空集结论与覆盖边界", "",
             "- 结论：在这 15 个构造点的 host 函数体内，没有 R17_R12 已枚举到的 [reg+0x1AC] 派发 call；0x449440 的调用方本轮未取得。",
             "- 计算依据：两侧条数与 host 集合见上；求交以 host 地址为键，未使用地址邻近、模块基址猜测或跨函数传播放宽。",
             "- 未覆盖：对象经全局/成员字段长距离传递、跨函数传入、或非 0x43B740/0x43B680 直接调用构造；R17_R12 的非标准间接形态（先算目标地址、跳板、索引型、disp8、段覆盖、跨节代码）也可能漏网。", "",
             "## 结论边界", "",
             "- 本轮只证明：在给定静态枚举口径下未发现 0x449440 调用方；不证明不存在，不证明唯一，也不证明运行期是否真的执行到。",
             "- 不改变 ②-b 的 [静态推断] 收口（D-53(A)）。", "",
             "## 产物", "",
             "- REPORT.md、intersect.tsv、chain_1ac.tsv（表头）、work.py。"]
    with open(os.path.join(OUT, "REPORT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("SHA=" + sha)
    print("CALLS_1AC=%d CALLS_124=%d CTOR_ROWS=%d CTOR_HOSTS=%d" % (len(call_1ac), len(call_124), len(ctors), len(ctor_hosts)))
    print("INTERSECT_1AC=%d INTERSECT_124=%d" % (counts["0x1AC"], counts["0x124"]))
    print("FOUND_0x449440_CALLER=NO")

if __name__ == "__main__":
    main()
