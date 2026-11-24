# -*- coding: utf-8 -*-
"""_tpv_d2_probe.py — 复核员独立实现协议 §4-D2 判据基线检索。
三探针：V1 合成 ID、V1 合成任务号、真实已登 ID 段（r2）。
范围：先 lead/ 树 *.md/*.json/*.py/*.txt（与作者演示同口径，便于比对计数），
再全仓（lead 之外）扫三探针以独立查越树痕迹。只读；归一化口径同 _f3_c7check.py:153-156。
"""
import os, sys, unicodedata, re

BASE = r"D:\Project\ra2-campaign-forge"
LEAD = os.path.join(BASE, "lead")
EXTS = {".md", ".json", ".py", ".txt"}

def normalize(s):
    t = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in t if not ch.isspace() and unicodedata.category(ch) != "Cf").casefold()

PROBES = {
    "P1_V1合成ID段(deadbeef-1234-4abc-8def-0123456789ab)": "deadbeef-1234-4abc-8def-0123456789ab",
    "P2_V1合成任务号(TASK-20261108-C07-01)": "TASK-20261108-C07-01",
    "P3_真实已登ID段(324c613e-fb0e-42f5-9883-805fef5b80de)": "324c613e-fb0e-42f5-9883-805fef5b80de",
}

def domain_of(rel):
    parts = rel.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "lead":
        return parts[0] + "/" + parts[1]
    return parts[0] if parts else "?"

def scan(root, ext_filter):
    """yield (relpath, normalized_text) ；跳过 reparse/不可读。"""
    for dirpath, dirnames, filenames in os.walk(root):
        pruned = []
        for d in dirnames:
            full = os.path.join(dirpath, d)
            try:
                if os.stat(full, follow_symlinks=False).st_file_attributes & 0x400:  # FILE_ATTRIBUTE_REPARSE_POINT
                    continue
            except OSError:
                continue
            pruned.append(d)
        dirnames[:] = pruned
        for fn in filenames:
            if ext_filter is not None:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in ext_filter:
                    continue
            full = os.path.join(dirpath, fn)
            try:
                with open(full, "rb") as f:
                    data = f.read()
                text = data.decode("utf-8", errors="ignore")
            except OSError:
                continue
            try:
                rel = os.path.relpath(full, BASE)
            except ValueError:
                continue
            yield rel, normalize(text)

def run(scan_name, root, ext_filter):
    print("=== %s ===" % scan_name)
    # 每探针：命中文件数、写域分布
    hits = {k: [] for k in PROBES}
    nfiles = 0
    for rel, ntext in scan(root, ext_filter):
        nfiles += 1
        for k, probe in PROBES.items():
            if normalize(probe) in ntext:
                hits[k].append(rel)
    print("filesScanned=%d" % nfiles)
    for k in PROBES:
        doms = {}
        for rel in hits[k]:
            d = domain_of(rel)
            doms[d] = doms.get(d, 0) + 1
        print("%s -> %d 件；写域分布：%s" % (k, len(hits[k]), sorted(doms.items())))
        for rel in hits[k]:
            if rel.startswith("lead\\c07_truth_protocol"):
                print("    [truth_protocol 域命中明细] %s" % rel)
    print()

def main():
    run("A) lead/ 树 4 扩展名（与作者演示同口径）", LEAD, EXTS)
    # B) 全仓（含 lead 外）：查三探针是否有 lead 之外的痕迹
    run("B) 全仓（无扩展名过滤，剪枝 reparse）", BASE, None)

if __name__ == "__main__":
    main()
