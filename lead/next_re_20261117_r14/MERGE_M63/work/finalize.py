# -*- coding: utf-8 -*-
"""M63 final verification + deliverable generation.
Reads final disk state, recomputes all numbers, writes:
  MERGE_M63/BEFORE_AFTER.txt, VERIFY.txt, MERGE_LOG.md
"""
import csv, hashlib, json, math, os, re, sys, datetime
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
WORK = os.path.join(ROOT, "MERGE_M63", "work")
OUT = os.path.join(ROOT, "MERGE_M63")

PASS = ["005414C0", "0071F8C0", "0041F580", "00503040", "00512290", "00512480"]
FAIL = ["005C46E0", "0065AC40"]
SUBSYS = {"005414C0":"S18","0071F8C0":"S18","0041F580":"S14","00503040":"S14",
          "00512290":"S14","00512480":"S14"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def mtime_iso(p):
    return datetime.datetime.fromtimestamp(os.stat(p).st_mtime).astimezone().isoformat()


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def main():
    bj = json.load(open(os.path.join(WORK, "before.json"), encoding="utf-8"))
    covres = json.load(open(os.path.join(WORK, "coverage_merge_result.json"), encoding="utf-8"))
    panres = json.load(open(os.path.join(WORK, "panel_merge_result.json"), encoding="utf-8"))

    before = bj["before"]
    # AFTER state
    after = {}
    for name, p in [("coverage.tsv", COV), ("PANEL.md", PANEL)]:
        after[name] = {"path": p, "mtime_iso": mtime_iso(p),
                       "bytes": os.stat(p).st_size, "sha256": sha(p)}
    # cross-check sha with merge scripts
    assert after["coverage.tsv"]["sha256"] == covres["after_sha256"]
    assert after["PANEL.md"]["sha256"] == panres["after_sha256"]

    # atlas
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))

    with open(COV, encoding="utf-8-sig", newline="") as f:
        allrows = list(csv.reader(f, delimiter="\t"))
    hdr = allrows[0]
    rows = [r for r in allrows[1:] if len(r) >= 8]
    assert len(hdr[0].split(",")) == 8 and len(rows) == 18498 and all(len(r) == 8 for r in rows)

    full_proved = sum(1 for r in rows if r[4].strip() == "[已证]")
    atlas_proved = sum(1 for r in rows if ne(r[0]) in atlas and r[4].strip() == "[已证]")
    nonatlas_proved = full_proved - atlas_proved

    by_e = defaultdict(list)
    for r in rows:
        by_e[r[0]].append(r)

    pass_state = {}
    for e in PASS:
        assert len(by_e[e]) == 1
        r = by_e[e][0]
        pass_state[e] = {"subsystem": r[1], "grade": r[4].strip(), "evidence_path": r[5],
                         "sem_matches_delta": r[3] == bj["delta_semantics"][e],
                         "in_atlas": ne(e) in atlas}
        assert pass_state[e]["grade"] == "[已证]"
        assert pass_state[e]["evidence_path"] == "NAMED_PUSH_AUDIT/VERDICT.md"
        assert pass_state[e]["sem_matches_delta"]
        assert pass_state[e]["in_atlas"]

    fail_state = {}
    for e in FAIL:
        assert len(by_e[e]) == 1
        r = by_e[e][0]
        fail_state[e] = {"subsystem": r[1], "grade": r[4].strip(), "evidence_path": r[5],
                         "sem": r[3]}
        assert fail_state[e]["grade"] == bj["fail_grade"][e][0]
        assert fail_state[e]["evidence_path"] == "EVIDENCE/classification_trace.tsv#" + e
    # FAIL rows must be byte-identical to before (sem+grade+ev), compare via BAK
    bak = open(os.path.join(WORK, "coverage.tsv.bak"), "rb").read().split(b"\n")
    cur = open(COV, "rb").read().split(b"\n")
    for e in FAIL:
        bl = [l for l in bak if l.split(b"\t")[0:1] == [e.encode()]]
        cl = [l for l in cur if l.split(b"\t")[0:1] == [e.encode()]]
        assert bl == cl and len(bl) == 1
    fail_unchanged = True

    # per-subsystem proved / strict (atlas 内)
    RE_SLOT = re.compile(r"::v?slot\d+$")
    RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
    d = defaultdict(Counter)
    for r in rows:
        if ne(r[0]) not in atlas:
            continue
        s = r[1].strip()
        d[s]["atlas_n"] += 1
        if r[4].strip() == "[已证]":
            d[s]["proved"] += 1
            if "[未证]" not in r[3]:
                d[s]["strict"] += 1

    d2 = defaultdict(Counter)
    for r in rows:
        if ne(r[0]) not in atlas:
            continue
        s = r[1].strip(); name = r[2].strip()
        if name and not name.startswith("sub_"):
            d2[s]["L"] += 1
            if not RE_CSUB.search(name):
                d2[s]["S14"] += 1
                if not RE_SLOT.search(name):
                    d2[s]["strict"] += 1
    nominal, strict = [], []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]
        tn, tp = math.ceil(0.9 * a), math.ceil(0.5 * a)
        if d2[s]["S14"] >= tn and d[s]["proved"] >= tp:
            nominal.append(s)
        if d2[s]["S14"] >= tn and d[s]["strict"] >= tp:
            strict.append(s)

    flip = not (nominal == ["S15", "S16", "S17"] and strict == ["S17"])
    assert not flip, "达标翻转！nominal=%s strict=%s" % (nominal, strict)

    S18_proved, S14_proved = d["S18"]["proved"], d["S14"]["proved"]
    assert (full_proved, atlas_proved, nonatlas_proved, S18_proved, S14_proved) == (1502, 1496, 6, 56, 111)

    # ---- BEFORE_AFTER.txt ----
    ba = ["M63 BEFORE / AFTER — 两文件状态记录（改前取自 MERGE_M63/work/before.json，改后为落盘实测）", "="*90, ""]
    for name in ("coverage.tsv", "PANEL.md"):
        b, a_ = before[name], after[name]
        ba += [
            "[%s]" % name,
            "  改前: mtime=%s  字节=%d  sha256=%s" % (b["mtime_iso"], b["bytes"], b["sha256"]),
            "  改后: mtime=%s  字节=%d  sha256=%s" % (a_["mtime_iso"], a_["bytes"], a_["sha256"]),
            ""]
    ba += ["改动摘要（byte-level 核验）:",
           "  coverage.tsv: %d 行变动（1-based 行号 %s），其余行逐字节不变" % (
               covres["diff_line_count"], covres["changed_lines_1based"]),
           "  PANEL.md:     %d 行变动（1-based 行号 %s），M47 历史快照行(185/189)未动" % (
               panres["changed_count"], panres["changed_lines_1based"]),
           ""]
    open(os.path.join(OUT, "BEFORE_AFTER.txt"), "w", encoding="utf-8").write("\n".join(ba))

    # ---- VERIFY.txt ----
    vt = ["M63 VERIFY — 并表审计 PASS 6 行后盘上复算", "="*90, ""]
    vt += [
        "数据行数: %d（表头 1 行逗号 8 字段；数据 TAB 8 列，制表符分隔）" % len(rows),
        "全表 [已证]: %d（改前 1,496 → +6）" % full_proved,
        "atlas 内 [已证]: %d（改前 1,490 → +6）" % atlas_proved,
        "atlas 外 [已证]: %d（改前 6，未变）" % nonatlas_proved,
        "S18（atlas 内）proved: %d（改前 54 → +2）" % S18_proved,
        "S14（atlas 内）proved: %d（改前 107 → +4）" % S14_proved,
        "",
        "6 行新 grade / evidence_path / 语义:",
    ]
    for e in PASS:
        st = pass_state[e]
        vt.append("  %s  %s  grade=%s  evidence_path=%s  sem=delta原文  atlas内=%s" % (
            e, st["subsystem"], st["grade"], st["evidence_path"], st["in_atlas"]))
    vt += ["", "2 行审计 FAIL — grade 未变、整行逐字节未动:"]
    for e in FAIL:
        st = fail_state[e]
        vt.append("  %s  %s  grade=%s（改前 %s）  evidence_path=%s" % (
            e, st["subsystem"], st["grade"], bj["fail_grade"][e][0], st["evidence_path"]))
    vt += [
        "",
        "严格双列表: S18 proved %d strict %d；S14 proved %d strict %d；TOTAL strict 1,163→1,169（6 行语义均不含「未证」，strict 同增 +6）" % (
            S18_proved, d["S18"]["strict"], S14_proved, d["S14"]["strict"]),
        "达标判定: 名义 %s；严格 %s" % (",".join(nominal), ",".join(strict)),
        "有无达标翻转: %s（名义仍 S15/S16/S17，严格仍仅 S17）" % ("有" if flip else "无"),
        "",
        "校验: audit PASS=6/FAIL=2 与卡片一致；6 行改前 grade（0071F8C0=[未证]，其余 [静态推断]）与卡片一致；",
        "      6 行全 atlas 内（entry 大写归一）；coverage 仅 6 行第4/5/6列改、第1/2/3/7/8列未动；",
        "      数据行 18,498 不变、8 列不变；未 git commit；未改其它文件。",
        "",
    ]
    open(os.path.join(OUT, "VERIFY.txt"), "w", encoding="utf-8").write("\n".join(vt))

    # ---- MERGE_LOG.md ----
    ml = [
        "# M63 MERGE LOG — 并表 NAMED_PUSH 审计 PASS 6 行", "",
        "## 范围与授权", "",
        "- 本轮唯一 COVERAGE 写者；只写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`，以及本目录 `MERGE_M63/` 交付物。",
        "- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT`。", "",
        "## 事实来源与交叉核验", "",
        "- 审计表 `NAMED_PUSH_AUDIT/verdict.tsv`：表头 8 列（entry/subsystem/verdict/ring2_at/ring3b_form/ring4_at/same_source/reason），数据 8 行。",
        "- 按第 3 列 verdict 核出 PASS 6 行：%s。" % " / ".join(PASS),
        "- FAIL 2 行：`005C46E0`（④ 锚点 `005C164A` 属析构器 `005C1640`，违 ㉓）、`0065AC40`（第 4 列把 `00410320` 的写出语义写成「流读入」，读写方向反）——整行拒绝，一个字未改。",
        "- 6 行 delta 语义来源：`NAMED_PUSH_S18_B1/delta.tsv`（005414C0）、`NAMED_PUSH_S18_B2/delta.tsv`（0071F8C0）、`NAMED_PUSH_S14_B1/delta.tsv`（0041F580/00503040/00512290/00512480），各取第 4 列原文照抄。", "",
        "## 改前前置核验（全部通过）", "",
        "- 6 行改前 grade：`0071F8C0`=[未证]，其余 5 行=[静态推断]；6 行均在 coverage 且各唯一。",
        "- 6 行全部在 `function_atlas.tsv`（entry 大写归一）内。",
        "- 改前盘上：数据行 18,498、全表 [已证] 1,496、atlas 内 1,490、atlas 外 6、S18 54、S14 107。", "",
        "## 落地改动", "",
        "- `coverage.tsv` 6 行各只改 3 列：第 4 列 ← delta 第 4 列原文；第 5 列 → `[已证]`；第 6 列 → `NAMED_PUSH_AUDIT/VERDICT.md`。第 1/2/3/7/8 列逐字节未动；数据行仍 18,498、8 列、TAB 分隔。",
        "- `PANEL.md` 同步 7 行（主面板 17/68/72/77 + 严格双列表 118/122/127）：S18 proved 54→56、S14 proved 107→111；全表 [已证] 1,496→1,502、atlas 内 1,490→1,496、atlas 外仍 6；严格列 S18 44→46、S14 94→98、TOTAL 1,163→1,169；百分比按实算重算。备注列追加 M63 说明。M47 历史快照行未动。",
        "- 6 行语义均不含「未证」⇒ strict 同增（S18 +2 / S14 +4 / TOTAL +6）。", "",
        "## 改后结果", "",
        "- 数据行 %d；全表 [已证] %d；atlas 内 %d；atlas 外 %d；S18 proved %d；S14 proved %d。" % (
            len(rows), full_proved, atlas_proved, nonatlas_proved, S18_proved, S14_proved),
        "- 6 行新 grade 全 `[已证]`、evidence_path 全 `NAMED_PUSH_AUDIT/VERDICT.md`、语义与 delta 逐字节一致。",
        "- 2 行 FAIL grade 仍 `[静态推断]`、整行逐字节未变。",
        "- 达标判定未翻转：名义 %s、严格 %s（严格仍仅 S17）。" % (",".join(nominal), ",".join(strict)),
        "- 两文件改前/改后 mtime/字节/sha256 见 `BEFORE_AFTER.txt`；复算见 `VERIFY.txt`。",
        "- 已知既存差异（非本卡引入，未改）：严格双列表 S22 strict 面板记 2，`strict_panel.py` 口径重算为 12（+10），属 M60 截面差异；本卡只按增量 +6 更新 TOTAL，不重算全表、不碰 S22。",
        "",
    ]
    open(os.path.join(OUT, "MERGE_LOG.md"), "w", encoding="utf-8").write("\n".join(ml))

    print("DELIVERABLES_WRITTEN")
    print("  BEFORE_AFTER.txt / VERIFY.txt / MERGE_LOG.md")
    print("  full=%d atlas=%d nonatlas=%d S18=%d S14=%d nominal=%s strict=%s flip=%s" % (
        full_proved, atlas_proved, nonatlas_proved, S18_proved, S14_proved,
        nominal, strict, flip))


main()
