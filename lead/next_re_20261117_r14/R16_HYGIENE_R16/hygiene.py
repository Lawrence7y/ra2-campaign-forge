#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R16-HYGIENE-R16 · coverage.tsv 全表一致性普查（只读输入，只写本目录）

输入：lead/next_re_20261117_r14/COVERAGE/coverage.tsv
      表头逗号分隔；数据行 TAB 分隔；18,498 数据行。
      列：0 entry | 1 subsystem | 2 name | 3 one_line_semantics | 4 grade |
          5 evidence_path | 6 n_sources | 7 conflict
输出（本目录）：
      findings.tsv   check<TAB>entry<TAB>subsystem<TAB>grade<TAB>detail
      counts.txt     每子项计数（含口径定义）
      candidates.txt 抽样候选行原文（供人工判读，未做判断）

本脚本不修改任何输入文件。
"""

import io
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "COVERAGE", "coverage.tsv")

CANON4 = "④ 活表槽位见证"          # 规范 ④ 形态（含空格，实测无「④活表」变体）
S126 = "§12.6"
GRADES = ("[已证]", "[静态推断]", "[未证]")
REF_RE = re.compile(r"[A-Za-z0-9_\-./]*\.(?:tsv|txt|json|jsonl|md|csv|log|bin|py)")
MARK_RE = re.compile(r";(M\d+)")


def load():
    rows = []
    with io.open(SRC, encoding="utf-8") as f:
        header = f.readline().rstrip("\r\n").split(",")
        for lineno, ln in enumerate(f, start=2):
            ln = ln.rstrip("\r\n")
            if ln == "":
                continue
            rows.append({"lineno": lineno, "f": ln.split("\t"), "raw": ln})
    return header, rows


def main():
    header, rows = load()
    findings = []       # (check, entry, subsystem, grade, detail)
    out = []            # counts.txt 行

    def add(check, r, detail):
        f = r["f"]
        findings.append((check, f[0], f[1], f[4], detail))

    out.append("== 表结构 ==")
    out.append("header\t%s" % ",".join(header))
    out.append("data_rows\t%d" % len(rows))
    out.append("")

    # ---------------- H4 · entry 唯一性与格式 ----------------
    ncol = collections.Counter(len(r["f"]) for r in rows)
    bad_ncol = [r for r in rows if len(r["f"]) != 8]
    for r in bad_ncol:
        add("H4c", r, "field_count=%d" % len(r["f"]))

    enames = collections.Counter(r["f"][0] for r in rows)
    dups = {k: v for k, v in enames.items() if v > 1}
    for r in rows:
        if r["f"][0] in dups:
            add("H4a", r, "duplicate entry x%d (line %d)" % (dups[r["f"][0]], r["lineno"]))

    HEX8 = re.compile(r"^[0-9A-F]{8}$")
    bad_entry = [r for r in rows if not HEX8.match(r["f"][0])]
    for r in bad_entry:
        e = r["f"][0]
        why = []
        if len(e) != 8:
            why.append("len=%d" % len(e))
        if e.lower().startswith("0x") or "0x" in e.lower():
            why.append("has_0x")
        if any(c.islower() for c in e):
            why.append("has_lowercase")
        if not why:
            why.append("not_hex_or_nonA-F")
        add("H4b", r, "entry=%r %s" % (e, ",".join(why)))

    gset = collections.Counter(r["f"][4] for r in rows)
    for r in rows:
        if r["f"][4] not in GRADES:
            add("H4d", r, "grade=%r not in 3-value set" % r["f"][4])

    out.append("== H4 · entry 唯一性与格式 ==")
    out.append("H4-列数分布\t%s" % dict(sorted(ncol.items())))
    out.append("H4c-列数非8行数\t%d" % len(bad_ncol))
    out.append("H4a-重复 entry 个数\t%d" % len(dups))
    out.append("H4a-重复 entry 涉及行数\t%d" % sum(dups.values()))
    out.append("H4a-重复 entry 分布(entry:行数)\t%s" % dict(sorted(dups.items())))
    out.append("H4b-entry 非 8 位大写十六进制行数\t%d" % len(bad_entry))
    out.append("H4d-grade 取值集合(值:行数)\t%s" % dict(sorted(gset.items())))
    out.append("H4d-越界 grade 行数\t%d" % sum(1 for r in rows if r["f"][4] not in GRADES))
    out.append("")

    # ---------------- H1 · §12.6 披露与 ④ 形态配对 ----------------
    s126 = [r for r in rows if S126 in r["f"][3]]
    canon = [r for r in rows if CANON4 in r["f"][3]]
    # H1b: 引 §12.6 但无规范 ④ 形态
    h1b = [r for r in s126 if CANON4 not in r["f"][3]]
    # H1c: 有规范 ④ 形态但未引 §12.6（欠引）
    h1c = [r for r in canon if S126 not in r["f"][3]]
    # 诊断量（不单列为缺陷）：H1b 里有「活 vtable 槽位」等价措辞的行 / ④ 为其它形态的行
    def h1b_tag(s):
        if "活 vtable 槽位" in s:
            return "has_vtable_wording"
        if "④ direct call" in s:
            return "direct_call_form1"
        if "④ 活 COM 类对象" in s:
            return "live_com_object"
        return "no_form_marker"

    h1b_vt = [r for r in h1b if "活 vtable 槽位" in r["f"][3]]
    for r in h1b:
        add("H1b", r, "%s | sem=%s" % (h1b_tag(r["f"][3]), r["f"][3]))
    for r in h1c:
        add("H1c", r, "sem=%s" % r["f"][3])

    out.append("== H1 · §12.6 与 ④ 形态配对 ==")
    out.append("H1a-第4列含 §12.6 的行数\t%d" % len(s126))
    out.append("H1-第4列含规范「%s」的行数\t%d" % (CANON4, len(canon)))
    out.append("H1a-含 §12.6 且不含规范 ④ 的行数(H1b)\t%d" % len(h1b))
    out.append("H1b-其中带「活 vtable 槽位」等价措辞的行数\t%d" % len(h1b_vt))
    out.append("H1b-其中不含该措辞的行数(④ 为其它形态)\t%d" % (len(h1b) - len(h1b_vt)))
    out.append("H1b-其中真正无任何 ④ 形态标记的行数\t%d"
               % sum(1 for r in h1b if h1b_tag(r["f"][3]) == "no_form_marker"))
    out.append("H1b-按子系统分布\t%s" % dict(sorted(collections.Counter(r["f"][1] for r in h1b).items())))
    out.append("H1b-按 grade 分布\t%s" % dict(sorted(collections.Counter(r["f"][4] for r in h1b).items())))
    out.append("H1b-按 ④ 措辞分布\t%s"
               % dict(sorted(collections.Counter(
                   "活COM类对象" if "④ 活 COM 类对象" in r["f"][3]
                   else ("direct call 形态1" if "④ direct call" in r["f"][3] else "无 ④ 形态标记")
                   for r in h1b).items())))
    out.append("H1c-有规范 ④ 但未引 §12.6 的行数(欠引)\t%d" % len(h1c))
    out.append("H1c-按子系统分布\t%s" % dict(sorted(collections.Counter(r["f"][1] for r in h1c).items())))
    # 欠引严重度：是否至少在正文里提到 §12.3 / D-47 / PANEL（提了冲突但漏引 §12.6 = 纯引用遗漏）
    h1c_mention = [r for r in h1c if ("§12.3" in r["f"][3] or "D-47" in r["f"][3] or "PANEL" in r["f"][3])]
    out.append("H1c-其中正文已提 §12.3/D-47/PANEL(纯漏引)的行数\t%d" % len(h1c_mention))
    out.append("H1c-其中正文完全未提冲突背景的行数\t%d" % (len(h1c) - len(h1c_mention)))
    out.append("H1-参考:引 §12.6 但未提 PANEL 的行数\t%d"
               % sum(1 for r in s126 if "PANEL" not in r["f"][3]))
    out.append("")

    # ---------------- H2 · grade 与 ④ 错配 ----------------
    has4 = [r for r in rows if "④" in r["f"][3]]
    h2a = [r for r in has4 if r["f"][4] == "[已证]"]
    h2b = [r for r in canon if r["f"][4] != "[已证]"]
    h2c = [r for r in h2a if "[未证]" in r["f"][3]]
    for r in h2b:
        add("H2b", r, "grade=%s but has canonical ④ | sem=%s" % (r["f"][4], r["f"][3]))
    for r in h2c:
        add("H2c", r, "grade=[已证] + ④ + literal [未证] | sem=%s" % r["f"][3])

    out.append("== H2 · grade 与 ④ 错配 ==")
    out.append("H2a-[已证] 且第4列含 ④ 的行数(口径A)\t%d" % len(h2a))
    out.append("H2a-第4列含 ④ 的总行数(任意 grade)\t%d" % len(has4))
    out.append("H2b-非[已证] 但含规范 ④ 的行数\t%d" % len(h2b))
    out.append("H2b-按 grade 分布\t%s" % dict(sorted(collections.Counter(r["f"][4] for r in h2b).items())))
    out.append("H2b-按子系统分布\t%s" % dict(sorted(collections.Counter(r["f"][1] for r in h2b).items())))
    out.append("H2c-[已证] 且含 ④ 且含字面 [未证] 的行数\t%d" % len(h2c))
    out.append("")

    # ---------------- H3 · 同格两条 ④ ----------------
    def c4(s):
        return s.count("④")

    # 「实质 ④ 形态」= 一条独立证据链。词表按全表实测（见 counts.txt 附录「④ 后随措辞词表」）。
    # 逐处 ④ 判型（不是整格包含判定），避免同一处措辞被两个族同时命中而虚增「两条链」。
    # 编号标签（④升级句 / ④ 表属类… / ②④ 不同源 / ④ 锚点… / ④ 属「活 vtable 槽位」形态）不算证据链。
    FAM = [
        ("SLOT", re.compile(r"④ 活表槽位见证")),
        ("LIVE_COM", re.compile(r"④ 活 COM 类对象")),
        ("CF", re.compile(r"③b[①②]?\+?④|环④")),
        ("VTDISP", re.compile(r"④\s?活\s?vtable\s?派发|④ 活虚表派发|④活vtable派发")),
        ("DIRECT", re.compile(r"④\s?(?:direct|\d+ 个 E8 直调)")),
        ("VT_INSTALL", re.compile(
            r"④\s?活\s?vt|④\s?(?:活表构造安装点|构造安装点|构造器安装点|构造器写点|构造器[0-9A-Fa-f]{6,8}"
            r"|行外 ctor|非 atexit 构造|ctor [0-9A-Fa-f]{6,8}@[0-9A-Fa-f]{6,8} 装活表)")),
        ("CF_IO", re.compile(r"④ 完整(?:循环 I/O|数组环|链表遍历)")),
    ]

    def _occ_family(s, i):
        ctx = s[max(0, i - 4):i + 34]
        for k, p in FAM:
            if p.search(ctx):
                return k
        return None

    def subst_forms(s):
        found = set()
        for m in re.finditer("④", s):
            k = _occ_family(s, m.start())
            if k:
                found.add("CF" if k == "CF_IO" else k)
        return tuple(sorted(found))

    def cause(s):
        f = subst_forms(s)
        n_can = s.count(CANON4)
        if n_can >= 2:
            return "TWO_CANON_SLOT(两条活表槽位见证)"
        if len(f) >= 2:
            return "TWO_CHAINS(%s)" % "+".join(f)
        if len(f) == 1:
            return "ONE_CHAIN(%s)+重复编号标签" % f[0]
        return "NO_CHAIN(未匹配任何形态族)"

    h3a = [r for r in rows if r["f"][4] == "[已证]" and c4(r["f"][3]) >= 2]
    for r in h3a:
        n_all = c4(r["f"][3])
        n_can = r["f"][3].count(CANON4)
        add("H3a", r, "④ x%d (canonical x%d) cause=%s" % (n_all, n_can, cause(r["f"][3])))
    h3b = [r for r in h3a if r["f"][3].count(CANON4) >= 2]
    for r in h3b:
        add("H3b", r, "canonical ④ x%d" % r["f"][3].count(CANON4))

    h3s = [r for r in rows if r["f"][4] == "[已证]" and len(set(subst_forms(r["f"][3]))) >= 2]
    for r in h3s:
        add("H3c", r, "two ④ chains: %s | ④ x%d" % ("+".join(subst_forms(r["f"][3])), c4(r["f"][3])))
    h3_nofam = [r for r in rows if "④" in r["f"][3] and not subst_forms(r["f"][3])]
    for r in h3_nofam:
        add("H3d", r, "④ present but no form family matched (classifier limit) | sem=%s" % r["f"][3][:160])

    out.append("== H3 · 同一格并存两条 ④ ==")
    out.append("H3a-[已证] 且 ④ 字面出现≥2 的行数\t%d" % len(h3a))
    out.append("H3a-④ 字面出现次数分布\t%s" % dict(sorted(collections.Counter(c4(r["f"][3]) for r in h3a).items())))
    out.append("H3a-按成因分类\t%s" % dict(sorted(collections.Counter(cause(r["f"][3]) for r in h3a).items())))
    out.append("H3b-其中「两条都是 ④ 活表槽位见证」的行数\t%d" % len(h3b))
    out.append("H3s-[已证] 且含≥2 条「实质 ④ 证据链」的行数(去标签口径)\t%d" % len(h3s))
    out.append("H3s-证据链组合分布\t%s"
               % dict(sorted(collections.Counter("+".join(subst_forms(r["f"][3])) for r in h3s).items())))
    out.append("H3s-按子系统分布\t%s" % dict(sorted(collections.Counter(r["f"][1] for r in h3s).items())))
    out.append("H3s-按 grade 分布\t%s" % dict(sorted(collections.Counter(r["f"][4] for r in h3s).items())))
    out.append("H3d-含 ④ 但未匹配任何形态族的行数(分类器局限,非缺陷)\t%d" % len(h3_nofam))
    out.append("H3-参考：含 ④ 的行数(全表)\t%d" % sum(1 for r in rows if "④" in r["f"][3]))
    out.append("H3-参考：全表 ④ 字面≥2 的行数(不区分 grade)\t%d"
               % sum(1 for r in rows if c4(r["f"][3]) >= 2))
    out.append("H3-参考：单条 ④ 证据链的行数(全表)\t%d"
               % sum(1 for r in rows if len(subst_forms(r["f"][3])) == 1))
    out.append("H3-参考：无任何 ④ 证据链的行数(全表)\t%d"
               % sum(1 for r in rows if len(subst_forms(r["f"][3])) == 0))
    out.append("")
    # 附录：④ 后随措辞实测词表（供复核分类器口径）
    pref = collections.Counter()
    for r in rows:
        s = r["f"][3]
        for m in re.finditer("④", s):
            nxt = s[m.start() + 1:m.start() + 13]
            key = re.split(r"[。；;：:，,（(]", nxt)[0][:12]
            prev = s[max(0, m.start() - 1):m.start()]
            pref[(prev, key)] += 1
    out.append("== 附录 · ④ 后随措辞词表（前 30） ==")
    for (p, k), v in pref.most_common(30):
        out.append("%d\tprev=%r\t%s" % (v, p, k))
    out.append("")

    # ---------------- H5 · evidence_path 形态 ----------------
    ev = [r["f"][5] for r in rows]
    empty = [r for r in rows if r["f"][5].strip() == ""]
    for r in empty:
        add("H5a", r, "empty evidence_path")

    ct_contains = [r for r in rows if "classification_trace" in r["f"][5]]
    # 「只含」三个口径，全部给出，避免 802/892 式混淆
    def primary_part(s):
        return MARK_RE.split(s)[0]

    only_v1 = []   # 严格：首个 ;M 注记之前只有单个路径，且该路径是 classification_trace
    only_v2 = []   # refs 口径：全部文件引用都指向 classification_trace
    only_v3 = []   # 裸等：值恰为 classification_trace
    for r in rows:
        s = r["f"][5]
        if "classification_trace" not in s:
            continue
        p = primary_part(s)
        if ";" not in p and "classification_trace" in p:
            only_v1.append(r)
        refs = REF_RE.findall(s)
        if refs and all("classification_trace" in x for x in refs):
            only_v2.append(r)
        if s.strip() == "classification_trace":
            only_v3.append(r)

    mk = collections.Counter()
    mk_rows = collections.defaultdict(list)
    for r in rows:
        for m in set(MARK_RE.findall(r["f"][5])):
            mk[m] += 1
            mk_rows[m].append(r)

    out.append("== H5 · evidence_path 形态 ==")
    out.append("H5a-第6列为空的行数\t%d" % len(empty))
    out.append("H5b-第6列「含」classification_trace 的行数\t%d" % len(ct_contains))
    out.append("H5c-第6列「只含」classification_trace 的行数(严格口径v1:首个;M前单路径且为ct)\t%d" % len(only_v1))
    out.append("H5c'-「只含」口径 v2(全部文件引用均为ct)\t%d" % len(only_v2))
    out.append("H5c''-「只含」口径 v3(值恰为 classification_trace)\t%d" % len(only_v3))
    out.append("H5c-参考:含但条目里同时引了非 ct 文件的行数\t%d" % (len(ct_contains) - len(only_v2)))
    out.append("H5d-含 ;M 注记的行数(去重行)\t%d"
               % sum(1 for r in rows if MARK_RE.search(r["f"][5])))
    for m in sorted(mk):
        out.append("H5d-注记 %s 的行数\t%d" % (m, mk[m]))
    out.append("H5d-注记分组归类: ;M8x 行数(去重)\t%d"
               % sum(1 for r in rows if any(x.startswith("M8") for x in MARK_RE.findall(r["f"][5]))))
    out.append("H5d-注记分组归类: ;M9x 行数(去重)\t%d"
               % sum(1 for r in rows if any(x.startswith("M9") for x in MARK_RE.findall(r["f"][5]))))
    # 附注（卡面未列，但与 H5 直接相关）：R14_COMMON §12.5 规定 ct 为唯一 evidence_path 的行，
    # 其 [已证] 只按现行口径计分、不构成「有证据」声明。这里量化这批行。
    ct_only = [r for r in ct_contains if ";" not in primary_part(r["f"][5])]
    out.append("H5e[附注]-ct 为唯一 evidence_path 的行数\t%d" % len(ct_only))
    out.append("H5e[附注]-其中 grade 分布\t%s" % dict(sorted(collections.Counter(r["f"][4] for r in ct_only).items())))
    out.append("H5e[附注]-其中 [已证] 行数(按 §12.5 不构成「有证据」声明)\t%d"
               % sum(1 for r in ct_only if r["f"][4] == "[已证]"))
    out.append("")

    # ---------------- 汇总 ----------------
    cnt = collections.Counter(f[0] for f in findings)
    out.append("== findings.tsv 条数按 check ==")
    for k in sorted(cnt):
        out.append("%s\t%d" % (k, cnt[k]))
    out.append("total\t%d" % len(findings))
    out.append("")

    # 写 findings.tsv
    with io.open(os.path.join(HERE, "findings.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("check\tentry\tsubsystem\tgrade\tdetail\n")
        for t in findings:
            f.write("\t".join(x.replace("\t", " ") for x in t) + "\n")

    with io.open(os.path.join(HERE, "counts.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")

    # 抽样候选（原文，供人工判读）
    with io.open(os.path.join(HERE, "candidates.txt"), "w", encoding="utf-8", newline="\n") as f:
        def dump(title, rs, limit=20):
            f.write("\n===== %s (total %d, showing %d) =====\n" % (title, len(rs), min(limit, len(rs))))
            for r in rs[:limit]:
                f.write("[line %d] %s | %s | %s\n  grade=%s\n  sem=%s\n  ev=%s\n"
                        % (r["lineno"], r["f"][0], r["f"][1], r["f"][2], r["f"][4], r["f"][3], r["f"][5]))
        dump("H1b §12.6 无规范④", h1b)
        dump("H1c 规范④ 无§12.6", h1c)
        dump("H2b 非已证但有规范④", h2b)
        dump("H2c 已证+④+[未证]", h2c, 10)
        dump("H3a 已证且④≥2", h3a)
        for c in sorted(set(cause(r["f"][3]) for r in h3a)):
            dump("H3a 成因=" + c, [r for r in h3a if cause(r["f"][3]) == c], 3)
        for c in sorted(set("+".join(subst_forms(r["f"][3])) for r in h3s)):
            dump("H3c 两条链=" + c, [r for r in h3s if "+".join(subst_forms(r["f"][3])) == c], 2)
        if dups:
            f.write("\n===== H4a 重复 entry =====\n")
            for k, v in sorted(dups.items()):
                f.write("%s x%d\n" % (k, v))
                for r in rows:
                    if r["f"][0] == k:
                        f.write("  [line %d] %s | %s | %s | grade=%s\n"
                                % (r["lineno"], r["f"][0], r["f"][1], r["f"][2], r["f"][4]))

    print("\n".join(out))
    print("wrote findings.tsv (%d), counts.txt, candidates.txt" % len(findings))


if __name__ == "__main__":
    main()
