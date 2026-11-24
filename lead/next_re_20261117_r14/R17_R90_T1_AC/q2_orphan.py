#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Q2 · C 笔 126 件：是不是「孤本」。
来源：R17_R84_T1_NARRATIVE\unsure.tsv 列 rel/bytes/type/why（type=U1_无法判定, 67 行）
      × R17_R40？否 —— 126 = 「带回滚标记」的 U1 件（见 why 列「名字有滚回标记（→ X）」）。
      67 件里带滚回标记的 = 126 件中的 126？逐件见下（本脚本先数出带标记件）。

判据（卡 §二 Q2）：
  对每件，取「去掉回滚标记后的现行版名」current_ref（取自 why 列的箭头，缺则用同一
  strip_rollback 回退），在同一父目录下查它是否存在（扩展名按现行版名自带，不再尝试别的扩展名）：
    exists = (该 rel 在档 A 表 files_tier_A_snap2.tsv 中)  OR  (该 rel 在盘上存在)
  exists_in_A = 仅 A 表口径（单列，供对照；A 表是 2026-11-22T04:31:10Z 的快照，之后树还在长）
  verdict:
    exists  => 非孤本(旧版副本) => 应排
    ¬exists => 孤本 => 应留
  另设 `superseded_text`：件内是否有「本目录已作废/已被…取代/当前权威版本」这类**内容**级取代声明
  且该声明指向的路径在同一目录下存在 —— 这是独立于文件名的第二条佐证（纪律 23）。
输出 u1_126.tsv 列 rel/bytes/superseded_text/current_ref/exists_in_A/verdict
"""
from __future__ import annotations
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
UNSURE = os.path.join(R14, "R17_R84_T1_NARRATIVE", "unsure.tsv")
A_TSV = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")
RE_ROLLBACK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)
HERE_REL = "R17_R90_T1_AC/"


def base(rel):
    return rel.rsplit("/", 1)[-1]


def strip_rollback(b):
    m = RE_ROLLBACK.search(b)
    if not m:
        return None
    stem, tail = b[:m.start()], b[m.end():]
    ext = tail[tail.index("."):] if "." in tail else ""
    if not ext:
        mm = re.search(r"(\.[A-Za-z0-9]{1,5})$", b)
        ext = mm.group(1) if mm else ""
    return stem + ext


def load_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        out = []
        for line in f:
            p = line.rstrip("\r\n").split("\t")
            out.append(dict(zip(head, p)))
    return out


a_rel = set()
with open(A_TSV, encoding="utf-8") as f:
    f.readline()
    for line in f:
        a_rel.add(line.split("\t", 1)[0].replace("\\", "/"))

rows = load_tsv(UNSURE)
marked = [r for r in rows if strip_rollback(base(r["rel"])) is not None]

RE_REF = re.compile(
    r"当前权威版本[^\n]*\n?\s*`?(?:lead[\\/])?((?:next_re_[A-Za-z0-9_]+[\\/])+(?:[^\s`()（）]+\.[A-Za-z0-9]{1,5}))",
    re.M)


def disk_path(rel):
    return os.path.join(LEAD, rel.replace("/", os.sep))


out = []
for r in marked:
    rel = r["rel"].replace("\\", "/")
    cur_name = strip_rollback(base(rel))
    parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
    cur_rel = f"{parent}/{cur_name}" if parent else cur_name
    # 名字侧推出来的现行版名，只有当它确实存在才算一次命中（不靠名字下结论，只用来定位）
    in_a = cur_rel in a_rel
    on_disk = os.path.isfile(disk_path(cur_rel))
    exists = in_a or on_disk

    # 内容侧：读件，看有没有「已被 X 取代」并指向同目录存在的路径
    sup = "N"
    text_ref = ""
    d = disk_path(rel)
    blob = ""
    try:
        with open(d, "rb") as f:
            blob = f.read(65536).decode("utf-8", "replace")
    except OSError:
        sup = "读取失败"
    if blob:
        lines = blob.splitlines()
        head = lines[:8]
        big = any(k in "\n".join(head) for k in ("本目录已作废", "请勿引用"))
        has_cur = any("当前权威版本" in ln for ln in lines) or "已被" in blob
        if big or has_cur:
            m = RE_REF.search(blob)
            if m:
                text_ref = m.group(1).replace("\\", "/")
                if text_ref in a_rel or os.path.isfile(disk_path(text_ref)):
                    sup = "Y"
                else:
                    sup = "标注了但指向缺失"
            else:
                m2 = re.search(r"已被\s*`?(next_re_[A-Za-z0-9_]+)[`\s]", blob)
                if m2:
                    text_ref = m2.group(1)
                    sup = "标注了无精确路径"

    verdict = "非孤本(旧版副本)=>应排" if exists else "孤本=>应留"
    basis = []
    basis.append(f"name_expect={cur_rel}")
    basis.append(f"in_A={'Y' if in_a else 'N'}")
    basis.append(f"on_disk={'Y' if on_disk else 'N'}")
    if text_ref:
        basis.append(f"content_ref={text_ref}")
    if text_ref and text_ref.lower() != cur_rel.lower():
        basis.append("NOTE_name_vs_content_ref_differ")
    out.append({
        "rel": rel, "bytes": int(r["bytes"]), "superseded_text": sup,
        "current_ref": cur_rel, "exists_in_A": "Y" if in_a else "N",
        "verdict": verdict, "basis": ";".join(basis), "on_disk": on_disk,
    })

out.sort(key=lambda x: x["rel"])
with open(os.path.join(HERE, "u1_126.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("rel\tbytes\tsuperseded_text\tcurrent_ref\texists_in_A\tverdict\tbasis\n")
    for o in out:
        f.write(f"{o['rel']}\t{o['bytes']}\t{o['superseded_text']}\t{o['current_ref']}\t"
                f"{o['exists_in_A']}\t{o['verdict']}\t{o['basis']}\n")

n_keep = [o for o in out if o["verdict"].startswith("孤本")]
n_drop = [o for o in out if o["verdict"].startswith("非孤本")]
summary = {
    "unsure_total": len(rows),
    "marked_total": len(marked),
    "orphan_keep": {"n": len(n_keep), "bytes": sum(o["bytes"] for o in n_keep)},
    "copy_drop": {"n": len(n_drop), "bytes": sum(o["bytes"] for o in n_drop)},
    "total": {"n": len(out), "bytes": sum(o["bytes"] for o in out)},
    "exists_in_A_Y": sum(1 for o in out if o["exists_in_A"] == "Y"),
    "on_disk_Y": sum(1 for o in out if o["on_disk"]),
    "superseded_text_Y": sum(1 for o in out if o["superseded_text"] == "Y"),
    "only_by_content_ref": sum(1 for o in out if o["verdict"].startswith("非孤本") and not o["on_disk"]),
}
with open(os.path.join(HERE, "q2_orphan.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
