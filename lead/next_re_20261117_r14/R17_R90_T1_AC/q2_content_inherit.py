#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Q2 复核 · 对 u1_126.tsv 里的每一件，按**内容**（不靠文件名）找它的「现行版本」：
  1) 件内是否自带「当前权威版本 / 已被 X 取代」声明，且声明的路径在盘上存在（content_ref）→ 非孤本
  2) 若没有，在**同一目录**内找「内容承继」关系：
       候选 = 同目录其余文件（不含本件自身）
       关系 = 本件的正文行有 >=INHERIT_RATIO 出现在候选里（候选是后续写者/增加内容的那一份）
              且候选的字节 >= 本件字节（后续版不会比旧版小）
       命中 ⇒ 非孤本（旧版副本，应排）；命中多个取命中率最高的那个
  3) 都不命中 ⇒ 孤本（应留）
承继率用「本件非空行在候选行集合里的命中率」；行级去重不做，因为倒序前插的板面行本身唯一。
输出：u1_126.tsv（重写，追加 verdict_basis 列） + q2_content_inherit.json
"""
from __future__ import annotations
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
UNSURE = os.path.join(R14, "R17_R84_T1_NARRATIVE", "unsure.tsv")
A_TSV = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")
RE_ROLLBACK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)
RE_REF = re.compile(
    r"当前权威版本[^\n]*\n?\s*`?(?:lead[\\/])?((?:next_re_[A-Za-z0-9_]+[\\/])+(?:[^\s`()（）]+\.[A-Za-z0-9]{1,5}))",
    re.M)
INHERIT_RATIO = 0.60   # 本件正文行的 >=60% 在候选里原样出现 ⇒ 内容承继

# ②b 用的显式种子：仅当该备份件的**正文本身**点明「它是 X 的改前快照」时，才把 X 的现行位置列为候选，
# 且最终仍由内容承继率（>=INHERIT_RATIO）裁决，不靠名字下结论。
#   - _before_PANEL.md 正文：「PANEL.md 改前备份 `_hygiene/PANEL.M52.bak`」「仅写 COVERAGE/coverage.tsv
#     与 COVERAGE/PANEL.md」⇒ 现行 = COVERAGE/PANEL.md（倒序前插板面，后插的不会删除旧行）
#   - _before_col4.json 是该卡「第 4 列改前快照」，正文无指向，故不给种子（保持孤本，不硬塞）
SEED_FROM_TEXT = {
    "next_re_20261117_r14/MERGE_M73/_before_PANEL.md":
        ["next_re_20261117_r14/COVERAGE/PANEL.md"],
    "next_re_20261117_r14/MERGE_M73/_before_coverage.tsv":
        ["next_re_20261117_r14/COVERAGE/coverage.tsv"],
}


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


def dp(rel):
    return os.path.join(LEAD, rel.replace("/", os.sep))


def read_lines(rel, cap=4 * 1024 * 1024):
    try:
        with open(dp(rel), "rb") as f:
            blob = f.read(cap)
        return blob.decode("utf-8", "replace").splitlines()
    except OSError:
        return None


def load_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        head = f.readline().rstrip("\r\n").split("\t")
        return [dict(zip(head, line.rstrip("\r\n").split("\t"))) for line in f]


a_rel = set()
with open(A_TSV, encoding="utf-8") as f:
    f.readline()
    for line in f:
        a_rel.add(line.split("\t", 1)[0].replace("\\", "/"))

rows = load_tsv(UNSURE)
out = []
for r in rows:
    rel = r["rel"].replace("\\", "/")
    pb = int(r["bytes"])
    cur_name = strip_rollback(base(rel))
    parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
    cur_rel = f"{parent}/{cur_name}" if parent else cur_name
    on_disk_expected = os.path.isfile(dp(cur_rel))
    in_a_expected = cur_rel in a_rel

    lines = read_lines(rel)
    if lines is None:
        out.append({"rel": rel, "bytes": pb, "sup": "读取失败", "cur": "", "in_a": "N",
                    "verdict": "未取得=>单列", "basis": "file_unreadable", "found": ""})
        continue

    body = [x.strip() for x in lines if x.strip()]
    # ① 件内自带取代声明
    m = RE_REF.search("\n".join(lines))
    text_ref = ""
    if m:
        text_ref = m.group(1).replace("\\", "/")
    if text_ref and (text_ref in a_rel or os.path.isfile(dp(text_ref))):
        ex = "Y" if text_ref in a_rel else "N"
        out.append({"rel": rel, "bytes": pb, "sup": "Y", "cur": text_ref, "in_a": ex,
                    "verdict": "非孤本(旧版副本)=>应排",
                    "basis": f"content_ref_exists={'A' if ex == 'Y' else 'disk'}", "found": text_ref})
        continue

    # ② 同目录内容承继
    cands = []
    d = os.path.dirname(dp(rel))
    try:
        names = os.listdir(d)
    except OSError:
        names = []
    best = None
    for nm in names:
        cpath = os.path.join(d, nm)
        if not os.path.isfile(cpath):
            continue
        crel = (parent + "/" + nm) if parent else nm
        if crel == rel:
            continue
        try:
            csz = os.path.getsize(cpath)
        except OSError:
            continue
        if csz < pb:
            continue
        try:
            with open(cpath, "rb") as f:
                blob = f.read(4 * 1024 * 1024)
            cl = [x.strip() for x in blob.decode("utf-8", "replace").splitlines() if x.strip()]
        except OSError:
            continue
        if not body or not cl:
            continue
        cs = set(cl)
        hit = sum(1 for x in body if x in cs)
        ratio = hit / len(body)
        if ratio >= INHERIT_RATIO:
            cands.append((ratio, crel, csz, hit, len(body)))
    scope = "same_dir"

    # ②b 跨目录内容承继：候选范围**由件内正文点名**（不是文件名），再叠一个窄的显式种子表。
    #     依据：这些备份件的正文里写着「记的是哪一份东西的改前快照」
    #     （如 `_before_PANEL.md` 正文: "PANEL.md 改前备份 `_hygiene/PANEL.M52.bak`"）；
    #     `写域：...` 行给出该卡允许写的目录。只在「正文点名的对象 + 写域目录内的同名对象」里找承继者。
    if not cands:
        scope = "declared_write_domain"
        seeds = set()
        for ln in lines:
            mm = re.search(r"写域[：:\s]*\**[：:]?\s*`([^`]+)`", ln)
            if mm:
                s = mm.group(1).replace("\\", "/").strip("/")
                s = re.sub(r"^lead/", "", s)
                seeds.add(s)
        # 写域目录内、与本件同族（basename 去回滚标记后同 stem 或同 ext 且 stem 前缀相同）的候选
        probe = []
        stem = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", cur_name or "")
        for s in seeds:
            sp = dp(s)
            if os.path.isfile(sp):
                probe.append(s)
            elif os.path.isdir(sp):
                for nm in os.listdir(sp):
                    fp = os.path.join(sp, nm)
                    if not os.path.isfile(fp):
                        continue
                    same_family = nm == cur_name or nm.startswith(stem) or (stem and stem.startswith(nm.split(".")[0]))
                    if same_family:
                        probe.append(f"{s}/{nm}")
        # 件内正文点名的对象（显式种子表）
        for s in SEED_FROM_TEXT.get(rel, []):
            seeds.add(s)
            probe.append(s)
        for crel in dict.fromkeys(probe):
            cpath = dp(crel)
            try:
                csz = os.path.getsize(cpath)
            except OSError:
                continue
            if csz < pb or crel == rel:
                continue
            try:
                with open(cpath, "rb") as f:
                    blob = f.read(8 * 1024 * 1024)
                cl = [x.strip() for x in blob.decode("utf-8", "replace").splitlines() if x.strip()]
            except OSError:
                continue
            if not body or not cl:
                continue
            cs = set(cl)
            hit = sum(1 for x in body if x in cs)
            ratio = hit / len(body)
            if ratio >= INHERIT_RATIO:
                cands.append((ratio, crel, csz, hit, len(body)))

    if not cands:
        # ②c JSON 结构级覆盖：本件是 {key: {entry, val...}} 形态的「改前快照」，
        #     同目录若有 JSON 把本件的每个 key 都承接（按 key 或按 entry 对得上），且对应值原样出现，
        #     则本件是旧版副本。按行算继承率在这种「结构被重写」的场合会低估，故单列这条判据。
        if rel.lower().endswith(".json"):
            try:
                import json as _json
                me = _json.loads(open(dp(rel), encoding="utf-8", errors="replace").read())
            except Exception:
                me = None
            if isinstance(me, dict) and me:
                me_keys = set(me)
                me_entries = {v.get("entry") for v in me.values() if isinstance(v, dict) and v.get("entry")}
                for nm in names:
                    if not nm.lower().endswith(".json") or nm == base(rel):
                        continue
                    crel = (parent + "/" + nm) if parent else nm
                    try:
                        other_raw = open(dp(crel), encoding="utf-8", errors="replace").read()
                        other = _json.loads(other_raw)
                    except Exception:
                        continue
                    if not isinstance(other, dict):
                        continue
                    okeys = set(other)
                    ochg = other.get("changes")
                    o_entries = {x.get("entry") for x in ochg if isinstance(x, dict)} if isinstance(ochg, list) else set()
                    key_cov = len(me_keys & okeys) / len(me_keys)
                    ent_cov = (len(me_entries & o_entries) / len(me_entries)) if me_entries else 0.0
                    cov = max(key_cov, ent_cov)
                    if cov < INHERIT_RATIO:
                        continue
                    # 值级佐证：本件每个 entry 的 payload 原文是否出现在承接者里
                    val_hit = 0
                    for v in me.values():
                        if not isinstance(v, dict) or "entry" not in v:
                            continue
                        pay = v.get("col4") or v.get("value") or ""
                        if pay and str(pay)[:80] in other_raw:
                            val_hit += 1
                    if me_entries and val_hit / len(me_entries) >= INHERIT_RATIO:
                        cands.append((cov, crel, os.path.getsize(dp(crel)), val_hit, len(me_entries)))
                        scope = "json_structural_cover"

    if cands:
        cands.sort(reverse=True)
        ratio, crel, csz, hit, nb = cands[0]
        ex = "Y" if crel in a_rel else "N"
        out.append({"rel": rel, "bytes": pb, "sup": "N", "cur": crel, "in_a": ex,
                    "verdict": "非孤本(旧版副本)=>应排",
                    "basis": f"content_inherit={hit}/{nb}={ratio:.3f};{scope};cand_bytes={csz};cand_in_A={ex}",
                    "found": crel})
    else:
        out.append({"rel": rel, "bytes": pb, "sup": "N", "cur": cur_rel, "in_a": "Y" if in_a_expected else "N",
                    "verdict": "孤本=>应留",
                    "basis": f"no_content_ref;no_same_dir_inheritor;name_expect_exists={on_disk_expected}",
                    "found": ""})

with open(os.path.join(HERE, "u1_126.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("rel\tbytes\tsuperseded_text\tcurrent_ref\texists_in_A\tverdict\tbasis\n")
    for o in out:
        f.write(f"{o['rel']}\t{o['bytes']}\t{o['sup']}\t{o['cur']}\t{o['in_a']}\t{o['verdict']}\t{o['basis']}\n")

keep = [o for o in out if o["verdict"].startswith("孤本")]
drop = [o for o in out if o["verdict"].startswith("非孤本")]
other = [o for o in out if o["verdict"] == "未取得=>单列"]
summary = {
    "total": {"n": len(out), "bytes": sum(o["bytes"] for o in out)},
    "orphan_keep": {"n": len(keep), "bytes": sum(o["bytes"] for o in keep)},
    "copy_drop": {"n": len(drop), "bytes": sum(o["bytes"] for o in drop)},
    "undetermined": {"n": len(other), "bytes": sum(o["bytes"] for o in other)},
    "by_conclusion_path": {
        "content_ref": sum(1 for o in drop if o["basis"].startswith("content_ref")),
        "same_dir_inherit": sum(1 for o in drop if o["basis"].startswith("content_inherit")),
    },
    "orphan_list": [o["rel"] for o in keep],
}
with open(os.path.join(HERE, "q2_content_inherit.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
