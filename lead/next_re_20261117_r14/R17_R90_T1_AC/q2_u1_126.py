#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Q2 · C 笔 126 件「带回滚标记 + 当前版名不在档 A 表」逐件硬判「是不是孤本」。

126 件的定义（可复算，不是拍的数）：
  R17_R84_T1_NARRATIVE\narrative_candidates.tsv（4,493 行）里 basename 命中回滚标记正则
  RE_ROLLBACK = (\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)
  = 126 件 / 138,439,370 B
  其中 67 件上一轮落 unsure.tsv（U1），59 件上一轮已被 T2b 内容指纹判为旧版副本。
  本卡对 126 件**全部**用同一判据重判，不继承旧结论。

判据（卡 §二 Q2）：「它们所指的现行版本在盘上存在吗？」
  exists   ⇒ 非孤本（旧版副本）⇒ 应排
  ¬exists  ⇒ 孤本 ⇒ 应留（唯一记载）
「现行版本」不靠文件名认定，按三级证据依次找，任一级成立即为 exists：
  E1 件内自带取代声明：正文「当前权威版本」给出的路径在盘上存在
  E2 同目录内容承继：同目录某文件 >= 本件字节，本件 >=60% 正文行原样出现在它里面
  E3 写域目录内同族承继（跨目录备份）+ JSON 改前快照的结构覆盖判据
三级都不成立 ⇒ 孤本。
输出 u1_126.tsv：rel / bytes / superseded_text / current_ref / exists_in_A / verdict / basis
"""
from __future__ import annotations
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
NAR = os.path.join(R14, "R17_R84_T1_NARRATIVE")
A_TSV = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")
RE_ROLLBACK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)
RE_REF = re.compile(
    r"当前权威版本[^\n]*\n?\s*`?(?:lead[\\/])?((?:next_re_[A-Za-z0-9_]+[\\/])+(?:[^\s`()（）]+\.[A-Za-z0-9]{1,5}))",
    re.M)
INHERIT_RATIO = 0.60

# E4 判据的候选母版：全树唯一最大的同族叙述体（4,556,815 B）。
# 依据：`lead\*.md` 里 GOAL-3T 谱系只有这一份是最大最高版本（另一份 *GOAL_THREE_TARGETS*.md.bak_*
# 仅 1,740,903 B，是更小的备份）。是否承继仍由内容承继率裁决。
MASTER_FAMILY = ["GOAL_THREE_TARGETS_20261018.md"]

# E3 补充：这些备份件的**正文自己**点明了它记的是哪份东西的改前快照，
# 但现行版在另一目录，故给一条精确 seed（仍由内容承继率裁决，不靠名字）。
SEED_FROM_TEXT = {
    "next_re_20261117_r14/MERGE_M73/_before_PANEL.md": ["next_re_20261117_r14/COVERAGE/PANEL.md"],
    "next_re_20261117_r14/MERGE_M73/_before_coverage.tsv": ["next_re_20261117_r14/COVERAGE/coverage.tsv"],
}


def base(rel):
    return rel.rsplit("/", 1)[-1]


def dp(rel):
    return os.path.join(LEAD, rel.replace("/", os.sep))


def read(rel, cap=8 * 1024 * 1024):
    try:
        with open(dp(rel), "rb") as f:
            return f.read(cap).decode("utf-8", "replace")
    except OSError:
        return None


def body_lines(text):
    return [x.strip() for x in text.splitlines() if x.strip()]


def inherit(text, cand_text):
    b = body_lines(text)
    c = set(body_lines(cand_text))
    if not b or not c:
        return None
    hit = sum(1 for x in b if x in c)
    return hit / len(b), hit, len(b)


a_rel = set()
with open(A_TSV, encoding="utf-8") as f:
    f.readline()
    for line in f:
        a_rel.add(line.split("\t", 1)[0].replace("\\", "/"))

cand = []
with open(os.path.join(NAR, "narrative_candidates.tsv"), encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\r\n").split("\t")
        if len(p) >= 2 and RE_ROLLBACK.search(base(p[0])):
            cand.append((p[0].replace("\\", "/"), int(p[1])))

prior = {}
with open(os.path.join(NAR, "unsure.tsv"), encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\r\n").split("\t")
        prior[p[0].replace("\\", "/")] = "U1"
with open(os.path.join(NAR, "should_exclude.tsv"), encoding="utf-8") as f:
    f.readline()
    for line in f:
        p = line.rstrip("\r\n").split("\t")
        prior.setdefault(p[0].replace("\\", "/"), p[2])

out = []
for rel, pb in sorted(cand):
    parent = rel.rsplit("/", 1)[0] if "/" in rel else ""
    rec = {"rel": rel, "bytes": pb, "prior": prior.get(rel, "")}
    text = read(rel)
    if text is None:
        rec.update({"sup": "读取失败", "cur": "", "in_a": "N",
                    "verdict": "未取得=>单列", "basis": "file_unreadable"})
        out.append(rec)
        continue
    lines = text.splitlines()

    # E1 件内自带取代声明
    m = RE_REF.search(text)
    if m:
        ref = m.group(1).replace("\\", "/")
        if ref in a_rel or os.path.isfile(dp(ref)):
            rec.update({"sup": "Y", "cur": ref, "in_a": "Y" if ref in a_rel else "N",
                        "verdict": "非孤本(旧版副本)=>应排",
                        "basis": f"E1_content_ref_exists={'A' if ref in a_rel else 'disk'}"})
            out.append(rec)
            continue

    hit_found = None
    d = os.path.dirname(dp(rel))
    try:
        names = os.listdir(d)
    except OSError:
        names = []

    # E2 同目录内容承继
    for nm in names:
        crel = (parent + "/" + nm) if parent else nm
        cpath = os.path.join(d, nm)
        if crel == rel or not os.path.isfile(cpath):
            continue
        if os.path.getsize(cpath) < pb:
            continue
        ct = read(crel)
        if not ct:
            continue
        r = inherit(text, ct)
        if r and r[0] >= INHERIT_RATIO and (hit_found is None or r[0] > hit_found[0]):
            hit_found = (r[0], crel, "E2_same_dir_inherit", r[1], r[2])

    # E3 写域目录内同族承继（跨目录备份）
    if hit_found is None:
        # 同族 stem 必须先去回滚标记（否则 PHASE_BY_BOOT.before_erratum_164434 永远匹配不上）
        mm_rb = RE_ROLLBACK.search(base(rel))
        cur_stem = base(rel)[:mm_rb.start()] if mm_rb else base(rel)
        cur_stem = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", cur_stem)
        probe = []
        for ln in lines:
            mm = re.search(r"写域[：:\s]*\**[：:]?\s*`([^`]+)`", ln)
            if not mm:
                continue
            s = re.sub(r"^lead/", "", mm.group(1).replace("\\", "/").strip("/"))
            if os.path.isfile(dp(s)):
                probe.append(s)
            elif os.path.isdir(dp(s)):
                for nm in os.listdir(dp(s)):
                    if not os.path.isfile(os.path.join(dp(s), nm)):
                        continue
                    # 写域目录通常只有几十个文件，全部纳入候选由内容承继率裁决；
                    # 名字只用来排序，不作判据（纪律 23）。
                    nstem = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", nm)
                    if nm == base(rel) or (cur_stem and (nm.startswith(cur_stem) or nstem.startswith(cur_stem))):
                        probe.insert(0, f"{s}/{nm}")
                    else:
                        probe.append(f"{s}/{nm}")
        probe.extend(SEED_FROM_TEXT.get(rel, []))
        for crel in dict.fromkeys(probe):
            if crel == rel:
                continue
            cpath = dp(crel)
            if not os.path.isfile(cpath) or os.path.getsize(cpath) < pb:
                continue
            ct = read(crel)
            if not ct:
                continue
            r = inherit(text, ct)
            if r and r[0] >= INHERIT_RATIO and (hit_found is None or r[0] > hit_found[0]):
                hit_found = (r[0], crel, "E3_write_domain_inherit", r[1], r[2])

    # E3b JSON 改前快照的结构覆盖
    if hit_found is None and rel.lower().endswith(".json"):
        try:
            me = json.loads(text)
        except Exception:
            me = None
        if isinstance(me, dict) and me:
            me_entries = {v.get("entry") for v in me.values() if isinstance(v, dict) and v.get("entry")}
            for nm in names:
                if not nm.lower().endswith(".json") or nm == base(rel):
                    continue
                crel = (parent + "/" + nm) if parent else nm
                raw = read(crel)
                if not raw:
                    continue
                try:
                    other = json.loads(raw)
                except Exception:
                    continue
                if not isinstance(other, dict):
                    continue
                ochg = other.get("changes")
                o_entries = {x.get("entry") for x in ochg if isinstance(x, dict)} if isinstance(ochg, list) else set()
                cov = len(me_entries & o_entries) / len(me_entries) if me_entries else 0.0
                if cov < INHERIT_RATIO:
                    continue
                vhit = 0
                for v in me.values():
                    if not isinstance(v, dict) or "entry" not in v:
                        continue
                    pay = v.get("col4") or v.get("value") or ""
                    if pay and str(pay)[:80] in raw:
                        vhit += 1
                if me_entries and vhit / len(me_entries) >= INHERIT_RATIO:
                    hit_found = (cov, crel, "E3b_json_struct_cover", vhit, len(me_entries))

    # E4 全树唯一最大的同族叙述体：这类「编号轮次快照」的备份件（GOAL-3T 谱系的
    #    GOAL_backup_before_NNN.md / GOAL_before_NNN.md）同目录内没有更大的后继，
    #    但全树有一份唯一最高版本（lead\GOAL_THREE_TARGETS_20261018.md，4,556,815 B，
    #    同族内唯一且最大）。只有当该最高版**内容承继**本件(>=60% 正文行)时才成立。
    if hit_found is None:
        for crel in MASTER_FAMILY:
            if crel == rel:
                continue
            cpath = dp(crel)
            if not os.path.isfile(cpath) or os.path.getsize(cpath) < pb:
                continue
            ct = read(crel, cap=32 * 1024 * 1024)
            if not ct:
                continue
            r = inherit(text, ct)
            if r and r[0] >= INHERIT_RATIO:
                hit_found = (r[0], crel, "E4_master_family", r[1], r[2])

    if hit_found:
        ratio, crel, path, hit, nb = hit_found
        rec.update({"sup": "N", "cur": crel, "in_a": "Y" if crel in a_rel else "N",
                    "verdict": "非孤本(旧版副本)=>应排",
                    "basis": f"{path}={hit}/{nb}={ratio:.3f};cand_bytes={os.path.getsize(dp(crel))}"})
    else:
        cur_name_path = parent + "/" + base(rel) if parent else base(rel)
        rec.update({"sup": "N", "cur": "(未找到现行版)", "in_a": "N",
                    "verdict": "孤本=>应留",
                    "basis": "E1/E2/E3/E3b 均无一成立"})
    out.append(rec)

with open(os.path.join(HERE, "u1_126.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("rel\tbytes\tsuperseded_text\tcurrent_ref\texists_in_A\tverdict\tbasis\tprior_verdict\n")
    for o in out:
        f.write(f"{o['rel']}\t{o['bytes']}\t{o['sup']}\t{o['cur']}\t{o['in_a']}\t{o['verdict']}\t{o['basis']}\t{o['prior']}\n")

keep = [o for o in out if o["verdict"].startswith("孤本")]
drop = [o for o in out if o["verdict"].startswith("非孤本")]
undet = [o for o in out if o["verdict"] == "未取得=>单列"]
summary = {
    "total": {"n": len(out), "bytes": sum(o["bytes"] for o in out)},
    "orphan_keep": {"n": len(keep), "bytes": sum(o["bytes"] for o in keep)},
    "copy_drop": {"n": len(drop), "bytes": sum(o["bytes"] for o in drop)},
    "undetermined": {"n": len(undet), "bytes": sum(o["bytes"] for o in undet)},
    "by_prior": {},
    "by_path": {},
    "orphan_list": [o["rel"] for o in keep],
}
for o in out:
    k = o["prior"] or "(none)"
    summary["by_prior"].setdefault(k, {"n": 0, "bytes": 0})
    summary["by_prior"][k]["n"] += 1
    summary["by_prior"][k]["bytes"] += o["bytes"]
    p = o["basis"].split("=")[0]
    summary["by_path"].setdefault(p, {"n": 0, "bytes": 0})
    summary["by_path"][p]["n"] += 1
    summary["by_path"][p]["bytes"] += o["bytes"]

with open(os.path.join(HERE, "q2_u1_126.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
