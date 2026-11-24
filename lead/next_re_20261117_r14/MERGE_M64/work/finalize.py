# -*- coding: utf-8 -*-
"""M64 final verification + deliverable generation.
Reads final disk state, recomputes all numbers, writes:
   MERGE_M64/BEFORE_AFTER.txt, VERIFY.txt, MERGE_LOG.md
"""
import csv, hashlib, json, math, os, sys, datetime
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
WORK = os.path.join(ROOT, "MERGE_M64", "work")
OUT = os.path.join(ROOT, "MERGE_M64")

PASS = ["00691EE0", "00691FA0", "006A4930", "006E87F0", "006E9140",
        "00410C30", "00414290", "0041CFE0", "00524D70", "005F9950"]
PROTECTED = ["006A48A0", "00748190"]
SUBSYS = {e: ("S14" if e in PASS[:5] else "S05") for e in PASS}
DELTA_DIR = {
    "00691EE0": "NAMED_PUSH_S14_B2", "00691FA0": "NAMED_PUSH_S14_B2",
    "006A4930": "NAMED_PUSH_S14_B2", "006E87F0": "NAMED_PUSH_S14_B2",
    "006E9140": "NAMED_PUSH_S14_B2",
    "00410C30": "NAMED_PUSH_S05_B1", "00414290": "NAMED_PUSH_S05_B1",
    "0041CFE0": "NAMED_PUSH_S05_B1",
    "00524D70": "NAMED_PUSH_S05_B2", "005F9950": "NAMED_PUSH_S05_B2",
}
NEW_EVID = "NAMED_PUSH_AUDIT2/VERDICT.md"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


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

    # AFTER state stats
    after = {}
    for name, p in [("coverage.tsv", COV), ("PANEL.md", PANEL)]:
        st = os.stat(p)
        after[name] = {
            "path": p,
            "mtime_iso": datetime.datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(),
            "mtime_epoch_ns": st.st_mtime_ns,
            "bytes": st.st_size,
            "sha256": sha(p),
        }
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
    assert full_proved == 1512 and atlas_proved == 1506 and nonatlas_proved == 6, (
        full_proved, atlas_proved, nonatlas_proved)

    prov_by_s = Counter()
    strict_by_s = Counter()
    for r in rows:
        if ne(r[0]) in atlas:
            if r[4].strip() == "[已证]":
                prov_by_s[r[1].strip()] += 1
                if "[未证]" not in r[3]:
                    strict_by_s[r[1].strip()] += 1
    assert prov_by_s["S14"] == 116 and prov_by_s["S05"] == 170 and prov_by_s["S18"] == 56, dict(prov_by_s)
    assert strict_by_s["S14"] == 103 and strict_by_s["S05"] == 138 and strict_by_s["S18"] == 46, dict(strict_by_s)

    # delta col-4 raw bytes semantics for byte-identical check
    delta_sem = {}
    for e in PASS:
        dp = os.path.join(ROOT, DELTA_DIR[e], "delta.tsv")
        with open(dp, "rb") as f:
            dl = f.read().split(b"\n")
        found = [ln.split(b"\t")[3] for ln in dl
                 if ln and len(ln.split(b"\t")) >= 6
                 and ln.split(b"\t")[0].strip().upper() == e.encode("ascii")]
        assert len(found) == 1
        delta_sem[e] = found[0]

    # index by entry (raw bytes for byte check, csv-parsed for values)
    cov_by_e_raw = {}
    with open(COV, "rb") as f:
        raw_lines = f.read().split(b"\n")
    for ln in raw_lines:
        if not ln:
            continue
        fld = ln.split(b"\t")
        if len(fld) == 8:
            cov_by_e_raw.setdefault(fld[0].strip().upper().decode("ascii", "replace"), []).append(ln)
    for e in PASS + PROTECTED:
        assert len(cov_by_e_raw.get(e, [])) == 1, (e, len(cov_by_e_raw.get(e, [])))

    # 10 PASS rows: verify col4 == delta raw, col5 [已证], col6 new evid, other cols unchanged
    pass_new = {}
    for e in PASS:
        r = cov_by_e_raw[e][0].split(b"\t")
        assert r[3] == delta_sem[e], "sem mismatch " + e
        assert r[4] == "[已证]".encode("utf-8"), "grade mismatch " + e
        assert r[5] == NEW_EVID.encode("ascii"), "evidence mismatch " + e
        assert "[未证]" not in r[3].decode("utf-8"), "unexpected 未证 in " + e
        pass_new[e] = {
            "subsystem": r[1].decode("utf-8"), "grade": r[4].decode("utf-8"),
            "evidence_path": r[5].decode("utf-8"), "atlas_in": ne(e) in atlas,
            "sem_len": len(r[3]),
        }
    # untouched cols vs backup
    bak_lines = open(os.path.join(WORK, "coverage.tsv.bak"), "rb").read().split(b"\n")
    bak_by_e = {}
    for ln in bak_lines:
        if not ln:
            continue
        fld = ln.split(b"\t")
        if len(fld) == 8:
            bak_by_e.setdefault(fld[0].strip().upper().decode("ascii", "replace"), []).append(fld)
    for e in PASS:
        bf = bak_by_e[e][0]
        af = cov_by_e_raw[e][0].split(b"\t")
        for k in (0, 1, 2, 6, 7):
            assert bf[k] == af[k], "untouched col changed %s col%d" % (e, k + 1)
        assert bf[4] == "[静态推断]".encode("utf-8") and af[4] == "[已证]".encode("utf-8")

    # protected rows byte-identical vs backup
    for e in PROTECTED:
        bl = [l for l in bak_lines if l.split(b"\t")[0:1] == [e.encode("ascii")]]
        al = [l for l in raw_lines if l.split(b"\t")[0:1] == [e.encode("ascii")]]
        assert len(bl) == len(al) == 1 and bl[0] == al[0], "PROTECTED row changed: " + e

    # 达标 recompute (nominal: named_n_S(R14)>=ceil(0.9n) AND proved_n>=ceil(0.5n))
    # Use PANEL main table values for named_n_S; proved from prov_by_s.
    panel = open(PANEL, encoding="utf-8").read().split("\n")
    main_named = {}
    for ln in panel[54:77]:  # lines 55..77
        c = ln.split("|")
        if len(c) == 13:
            s = c[1].strip().strip("*")
            if s.startswith("S") and s[1:].isdigit():
                try:
                    main_named[s] = (int(c[2].strip().strip("*")), int(c[5].strip().strip("*")))
                except ValueError:
                    pass
    nominal_ok = []
    for s, (n, named) in main_named.items():
        need_named = math.ceil(0.9 * n)
        need_proved = math.ceil(0.5 * n)
        if named >= need_named and prov_by_s[s] >= need_proved:
            nominal_ok.append(s)
    nominal_ok = sorted(nominal_ok)
    assert nominal_ok == ["S15", "S16", "S17"], nominal_ok
    # strict table 达标 columns unchanged check: only S17 keeps 严格达标=达标
    strict_total = panel[126]
    sc = strict_total.split("|")
    assert sc[8].strip() == "**3/22**" and sc[9].strip() == "**1/22**", strict_total
    strict_ok = []
    for ln in panel[107:127]:  # lines 108..127 (S01..S22 + TOTAL)
        c = ln.split("|")
        if len(c) == 11 and c[9].strip() == "**达标**":
            strict_ok.append(c[1].strip().strip("*"))
    assert strict_ok == ["S17"], strict_ok

    # ---- BEFORE_AFTER.txt ----
    ba = []
    ba.append("M64 BEFORE/AFTER — COVERAGE 两文件 mtime/字节/sha256")
    ba.append("=" * 88)
    for name in ("coverage.tsv", "PANEL.md"):
        b = before[name]
        a = after[name]
        ba.append("[%s]" % name)
        ba.append("  BEFORE: bytes=%d  sha256=%s  mtime=%s" % (b["bytes"], b["sha256"], b["mtime_iso"]))
        ba.append("  AFTER : bytes=%d  sha256=%s  mtime=%s" % (a["bytes"], a["sha256"], a["mtime_iso"]))
        ba.append("  delta_bytes=%+d" % (a["bytes"] - b["bytes"]))
        ba.append("")
    open(os.path.join(OUT, "BEFORE_AFTER.txt"), "w", encoding="utf-8").write("\n".join(ba))

    # ---- VERIFY.txt ----
    v = []
    v.append("M64 VERIFY — 并表审计 PASS 10 行后盘上复算")
    v.append("=" * 88)
    v.append("数据行数: 18498（表头 1 行逗号 8 字段；数据 TAB 8 列，制表符分隔）")
    v.append("全表 [已证]: %d（改前 1,502 → +10）" % full_proved)
    v.append("atlas 内 [已证]: %d（改前 1,496 → +10）" % atlas_proved)
    v.append("atlas 外 [已证]: %d（改前 6，未变）" % nonatlas_proved)
    v.append("S14（atlas 内）proved: %d（改前 111 → +5）" % prov_by_s["S14"])
    v.append("S05（atlas 内）proved: %d（改前 165 → +5）" % prov_by_s["S05"])
    v.append("S18（atlas 内）proved: %d（改前 56，未变）" % prov_by_s["S18"])
    v.append("")
    v.append("10 行新 grade / evidence_path / 语义:")
    for e in PASS:
        x = pass_new[e]
        v.append("  %s  %s  grade=%s  evidence_path=%s  sem=delta原文  atlas内=%s" % (
            e, x["subsystem"], x["grade"], x["evidence_path"], x["atlas_in"]))
    v.append("")
    v.append("2 行保护 — grade 未变、整行逐字节未动:")
    for e in PROTECTED:
        bl = [l for l in bak_lines if l.split(b"\t")[0:1] == [e.encode("ascii")]][0].split(b"\t")
        al = [l for l in raw_lines if l.split(b"\t")[0:1] == [e.encode("ascii")]][0].split(b"\t")
        v.append("  %s  grade=%s（改前 %s）  evidence_path=%s  [原因: %s]" % (
            e, al[4].decode("utf-8"), bl[4].decode("utf-8"), al[5].decode("utf-8"),
            "审计 FAIL" if e == "006A48A0" else "未审不并"))
    v.append("")
    v.append("严格双列表（proved_strict，atlas内 [已证] 且语义不含 [未证]）:")
    v.append("  S14 proved 111→116 strict 98→103；S05 proved 165→170 strict 133→138")
    v.append("  TOTAL proved 1,496→1,506 strict 1,169→1,179（10 行语义均不含「未证」，strict 同增 +10）")
    v.append("  S18 56/46 未变；严格达标仍仅 S17")
    v.append("")
    v.append("达标判定: 名义 S15,S16,S17；严格 S17")
    v.append("有无达标翻转: 无（名义仍 S15/S16/S17，严格仍仅 S17）")
    v.append("")
    v.append("校验: audit PASS=10/FAIL=1 与卡片一致；00748190 不在审计表、未审不并；")
    v.append("      10 行改前 grade 全 [静态推断]（与卡片一致）、全 atlas 内（entry 大写归一）；")
    v.append("      coverage 仅 10 行第4/5/6列改、第1/2/3/7/8列未动；006A48A0 与 00748190 整行未动；")
    v.append("      PANEL 仅 7 行改（17/59/68/77 + 109/118/127）；表头/D-44/达标列/M47 快照未动；")
    v.append("      数据行 18,498 不变、8 列不变；未 git commit；未改其它文件。")
    v.append("额外限定已写入 S14 行备注: 〔模板级低信息量 ③b②：析构体内容器 Find 返 -1 哨兵分支成立；与既有 6 行同型，未收紧口径〕")
    open(os.path.join(OUT, "VERIFY.txt"), "w", encoding="utf-8").write("\n".join(v) + "\n")

    # ---- MERGE_LOG.md ----
    ml = []
    ml.append("# M64 MERGE LOG — 并表 NAMED_PUSH_AUDIT2 审计 PASS 10 行")
    ml.append("")
    ml.append("## 范围与授权")
    ml.append("")
    ml.append("- 本轮唯一 COVERAGE 写者；只写 `COVERAGE/coverage.tsv` 与 `COVERAGE/PANEL.md`，以及本目录 `MERGE_M64/` 交付物。")
    ml.append("- 未 git commit；未碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`。")
    ml.append("")
    ml.append("## 事实来源与交叉核验")
    ml.append("")
    ml.append("- 审计表 `NAMED_PUSH_AUDIT2/verdict.tsv`：表头 8 列（entry/subsystem/verdict/ring2_at/ring3b_form/ring4_at/same_source/reason），数据 11 行；第 3 列 verdict。")
    ml.append("- 按 verdict 核出 PASS **10 行**：S14 00691EE0/00691FA0/006A4930/006E87F0/006E9140 + S05 00410C30/00414290/0041CFE0/00524D70/005F9950，与卡片逐字一致。")
    ml.append("- FAIL 1 行整行拒绝（一个字未改）：`006A48A0`（第 4 列把 `00410320` 流写出写成「流读入」，读写方向反）。")
    ml.append("- 另 1 行不进本次并表：`00748190`（NAMED_PUSH_S05_B3 产出，未经异族审计，留池等下一张审计卡；不在 verdict.tsv 内）。")
    ml.append("- 10 行 delta 语义来源：`NAMED_PUSH_S14_B2/delta.tsv`（S14 5 行）、`NAMED_PUSH_S05_B1/delta.tsv`（00410C30/00414290/0041CFE0）、`NAMED_PUSH_S05_B2/delta.tsv`（00524D70/005F9950），各取第 4 列 `one_line_semantics` 原文照抄。")
    ml.append("")
    ml.append("## 改前前置核验（全部通过，详见 work/before.json）")
    ml.append("")
    ml.append("- 审计表 11 行 8 列、PASS 10 / FAIL 1 与卡片一致；00748190 不在审计表。")
    ml.append("- 10 行改前 grade 全 `[静态推断]`，在 coverage 各唯一；全部在 `function_atlas.tsv`（entry 大写归一）内。")
    ml.append("- 006A48A0 与 00748190 改前均 `[静态推断]`。")
    ml.append("- 改前盘上：数据行 18,498、全表 [已证] 1,502、atlas 内 1,496、atlas 外 6、S18 56、S14 111、S05 165（与卡片一致）。")
    ml.append("- 10 行 delta 语义唯一、均不含「未证」token ⇒ proved_strict 同增。")
    ml.append("")
    ml.append("## 落地改动")
    ml.append("")
    ml.append("- `coverage.tsv` 10 行各只改 3 列：第 4 列 ← delta 第 4 列 `one_line_semantics` 原文；第 5 列 → `[已证]`；第 6 列 → `NAMED_PUSH_AUDIT2/VERDICT.md`。第 1/2/3/7/8 列逐字节未动；数据行仍 18,498、8 列、TAB 分隔。")
    ml.append("- `PANEL.md` 同步 7 行（主面板 17/59/68/77 + 严格双列表 109/118/127）：S14 proved 111→116、S05 proved 165→170；全表 [已证] 1,502→1,512、atlas 内 1,496→1,506、atlas 外仍 6；严格列 S14 98→103、S05 133→138、TOTAL 1,169→1,179；百分比实算重算。备注列追加 M64 说明。表头行 1、D-44 达标声明、达标列（3/22、1/22）、M47 历史快照均未动。")
    ml.append("- S14 行备注追加限定：`〔模板级低信息量 ③b②：析构体内容器 Find 返 -1 哨兵分支成立；与既有 6 行同型，未收紧口径〕`")
    ml.append("- 10 行语义均不含「未证」⇒ strict 同增（S14 +5 / S05 +5 / TOTAL +10）。")
    ml.append("")
    ml.append("## 改后结果")
    ml.append("")
    ml.append("- 数据行 18,498；全表 [已证] 1,512；atlas 内 1,506；atlas 外 6；S14 proved 116；S05 proved 170；S18 proved 56（未变）。")
    ml.append("- 10 行新 grade 全 `[已证]`、evidence_path 全 `NAMED_PUSH_AUDIT2/VERDICT.md`、语义与 delta 第 4 列逐字节一致、全 atlas 内。")
    ml.append("- `006A48A0`（审计 FAIL）与 `00748190`（未审）grade 仍 `[静态推断]`、整行逐字节未变。")
    ml.append("- 达标判定未翻转：名义 S15,S16,S17、严格仍仅 S17。")
    ml.append("- 两文件改前/改后 mtime/字节/sha256 见 `BEFORE_AFTER.txt`；复算见 `VERIFY.txt`。")
    ml.append("- 已知既存差异（非本卡引入，未改）：严格双列表 S22 strict 面板记 2，`strict_panel.py` 口径重算为 12（+10），属 M60 截面差异；本卡只按增量 +10 更新 TOTAL，不重算全表、不碰 S22。")
    open(os.path.join(OUT, "MERGE_LOG.md"), "w", encoding="utf-8").write("\n".join(ml) + "\n")

    # print summary
    print("FINAL_OK")
    print("full=%d atlas=%d nonatlas=%d S14=%d S05=%d S18=%d" % (
        full_proved, atlas_proved, nonatlas_proved, prov_by_s["S14"], prov_by_s["S05"], prov_by_s["S18"]))
    print("strict S14=%d S05=%d S18=%d" % (strict_by_s["S14"], strict_by_s["S05"], strict_by_s["S18"]))
    print("nominal_ok=%s strict_ok=S17" % nominal_ok)
    print("PASS=%d PROTECTED_unchanged=2" % len(PASS))
    print("BEFORE_AFTER sha:", after["coverage.tsv"]["sha256"], after["PANEL.md"]["sha256"])


main()
