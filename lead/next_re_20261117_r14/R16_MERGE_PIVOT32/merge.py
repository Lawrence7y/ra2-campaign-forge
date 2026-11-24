# -*- coding: utf-8 -*-
"""
R16-MERGE-PIVOT32 · agent-51 · 2026-11-21
唯一写者：把 R16_FIX_PIVOT32/delta.tsv 的 32 行并入 COVERAGE/coverage.tsv（只改第4列），
PANEL.md 紧接 M95 块之后插入 1 条 M96 披露。

本脚本分两阶段：
  analyze  = 只读目标文件，做全部前置校验与指标实测，构建 pin/before_col4/after_col4 证据，
             生成待写盘内容到本目录（_staged_coverage.tsv / _staged_PANEL.md），不写目标文件。
  commit   = 校验 staged 内容与证据自洽后，写目标文件，然后回读做还原性/不变量闭环。

表头：coverage.tsv 第 1 行逗号分隔；数据行 TAB 分隔 8 列。解析按此处理。
行尾：coverage 数据行全部 LF，末行无换行；PANEL 全部 LF，末行有换行。全程 bytes 操作保持行尾。
"""
import os, sys, csv, json, math, re, hashlib, collections

sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_FIX_PIVOT32", "delta.tsv")
DEF  = os.path.join(ROOT, "R16_FIX_PIVOT32", "defects.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT  = os.path.join(ROOT, "R16_MERGE_PIVOT32")
STAGE_COV = os.path.join(OUT, "_staged_coverage.tsv")
STAGE_PAN = os.path.join(OUT, "_staged_PANEL.md")
PIN_REPORT= os.path.join(OUT, "PIN_AND_RESTORE.json")
REPORT    = os.path.join(OUT, "VERIFY_REPORT.txt")

APPEND = "；§12.6 引用：本行 ④ 属「活 vtable 槽位」形态，按 D-47(A) 裁决 §12.3 对该形态让位（见 R14_COMMON §12.6 与 PANEL M84 披露）"
APPEND_B = APPEND.encode("utf-8")

# 9 行 CLSID None + 1 行错值（006BF810）。来源 defects.tsv（执行器）/ VERDICT.md（审计）逐行一致。
REPLACEMENTS = {
    "006BF810": ("7E9580",     "007E9950"),
    "006C0110": ("CLSID None", "CLSID 007E9750"),
    "006C0290": ("CLSID None", "CLSID 007E9900"),
    "006C0410": ("CLSID None", "CLSID 007E9730"),
    "006C0590": ("CLSID None", "CLSID 007E9850"),
    "006C0710": ("CLSID None", "CLSID 007E98D0"),
    "006C0890": ("CLSID None", "CLSID 007E98E0"),
    "006C0B90": ("CLSID None", "CLSID 007E9870"),
    "006C0D10": ("CLSID None", "CLSID 007E9880"),
    "006C0E90": ("CLSID None", "CLSID 007E9890"),
}

# 达标守护阈值面积的口径（来自 strict_panel.py）: named_S(R14)/named_strict/proved_n/proved_strict
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

def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

def log(lines, s=""):
    lines.append(s)
    print(s)

def parse_coverage_bytes(data):
    """返回 (header_bytes_with_eol, [ (raw_line_bytes_with_eol, cols_list_str, had_eol) ... ])"""
    # 保留行尾：按 b'\n' 切，重建时严格拼接。用 splitlines(keepends=True)。
    lines = data.splitlines(keepends=True)
    header = lines[0]
    rows = []
    for raw in lines[1:]:
        had = raw.endswith(b"\n")
        body = raw[:-1] if had else raw
        if body.endswith(b"\r"):
            body = body[:-1]
        txt = body.decode("utf-8")
        cols = txt.split("\t")
        rows.append({"raw": raw, "body": body, "had_eol": had, "cols": cols})
    return header, rows

def load_atlas():
    s = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                s.add(ne(p[0]))
    return s

def metrics(rows, atlas):
    """按 PANEL.md 与 strict_panel.py 口径实测全部数字。"""
    m = collections.Counter()
    m["data_rows"] = len(rows)
    colcount = collections.Counter()
    for r in rows:
        colcount[len(r["cols"])] += 1
        cols = r["cols"]
        if len(cols) < 8:
            continue
        e = ne(cols[0]); sub = cols[1].strip(); name = cols[2].strip()
        sem = cols[3]; grade = cols[4].strip()
        # 全表 [已证]
        if grade == "[已证]":
            m["proved_total"] += 1
            # 口径 A / B（PANEL.md:271 权威定义）
            if "④" in sem:
                m["cal_A"] += 1
            if "④ 活表槽位见证" in sem:
                m["cal_B"] += 1
            if e in atlas:
                m["proved_atlas"] += 1
                if "[未证]" not in sem:
                    m["proved_strict"] += 1
            else:
                m["proved_out"] += 1
        # §12.6 全表命中（按子串计数：出现次数，与 PANEL 披露的"命中数"一致——先按行计+出现次数两种都给）
        if "§12.6" in sem:
            m["s126_rows"] += 1
            m["s126_hits"] += sem.count("§12.6")
        # CLSID None 字面（全文）
        m["clsid_none_hits"] += sem.count("CLSID None")
        if e not in atlas:
            continue
        m["atlas_rows"] += 1
        if name and not name.startswith("sub_"):
            m["named_L"] += 1
            if not RE_CSUB.search(name):
                m["named_S14"] += 1
                if not RE_SLOT.search(name):
                    m["named_strict"] += 1
        # per-subsystem proved/strict
        d = m["sub_" + sub] if False else None
    m["colcount"] = dict(colcount)
    # 达标判定
    nominal, strict = set(), set()
    subs = collections.Counter()
    for sub in [f"S{i:02d}" for i in range(1, 23)]:
        key_n = "sn_" + sub
        # 需要从行重算，单独走一遍
    # 单独重算 per-S 指标
    perS = collections.defaultdict(collections.Counter)
    for r in rows:
        cols = r["cols"]
        if len(cols) < 8:
            continue
        e = ne(cols[0]); sub = cols[1].strip(); name = cols[2].strip(); sem = cols[3]; grade = cols[4].strip()
        if e not in atlas:
            continue
        c = perS[sub]
        c["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            c["named_L"] += 1
            if not RE_CSUB.search(name):
                c["named_S14"] += 1
                if not RE_SLOT.search(name):
                    c["named_strict"] += 1
        if grade == "[已证]":
            c["proved_n"] += 1
            if "[未证]" not in sem:
                c["proved_strict"] += 1
    m["perS"] = {k: dict(v) for k, v in perS.items()}
    for sub, c in perS.items():
        a = c["atlas_n"]
        tn, tp = math.ceil(0.9*a), math.ceil(0.5*a)
        if c["named_S14"] >= tn and c["proved_n"] >= tp:
            nominal.add(sub)
        if c["named_S14"] >= tn and c["proved_strict"] >= tp:
            strict.add(sub)
    m["nominal"] = sorted(nominal)
    m["strict"] = sorted(strict)
    return m

def analyze():
    L = []
    os.makedirs(OUT, exist_ok=True)
    cov_raw = open(COV, "rb").read()
    pan_raw = open(PANEL, "rb").read()
    delta_raw = open(DELTA, "rb").read()
    def_raw = open(DEF, "rb").read()
    before_cov_sha = sha(cov_raw)
    before_pan_sha = sha(pan_raw)
    log(L, "[0] before sha:")
    log(L, "  coverage.tsv = " + before_cov_sha + "  (REPORT.md 期望 2F498B18...B36E)")
    log(L, "  PANEL.md     = " + before_pan_sha)

    # 表头分隔检查
    assert cov_raw.split(b"\n",1)[0].count(b",") == 7 and cov_raw.split(b"\n",1)[0].count(b"\t") == 0, "coverage 表头非逗号分隔"
    log(L, "[1] coverage 表头逗号分隔 OK；数据行 TAB 分隔（后续逐行核）")

    # 行尾检查
    assert cov_raw.count(b"\r\n") == 0 and cov_raw.count(b"\r") == 0, "coverage 有 CR 混用"
    assert pan_raw.count(b"\r\n") == 0 and pan_raw.count(b"\r") == 0, "PANEL 有 CR 混用"
    log(L, "[2] 行尾：coverage/panel 全 LF、无 CR，OK")

    # 解析
    cov_header, cov_rows = parse_coverage_bytes(cov_raw)
    d_header, d_rows_raw = parse_coverage_bytes(delta_raw)
    # delta 表头是 TAB（第1行），parse_coverage 把 header 单列、rows[1:] 正确
    assert len(cov_rows) == 18498, ("数据行 != 18498", len(cov_rows))
    assert len(d_rows_raw) == 32, ("delta 数据行 != 32", len(d_rows_raw))
    log(L, "[3] coverage 数据行 = %d；delta 数据行 = %d" % (len(cov_rows), len(d_rows_raw)))

    # delta 解析为 dict
    delta = []
    for dr in d_rows_raw:
        c = dr["cols"]
        assert len(c) == 8, ("delta 行非8列", len(c), c[:2])
        delta.append({"entry": c[0], "cols": c, "raw": dr})
    # entry 唯一
    ents = [d["entry"] for d in delta]
    assert len(set(ents)) == 32, "delta entry 非唯一"
    log(L, "[4] delta 32 行 entry 唯一 OK")

    # coverage entry 映射（归一化大写；定位用精确行号）
    cov_by_entry = {}
    for i, r in enumerate(cov_rows):
        c = r["cols"]
        if not c:
            continue
        cov_by_entry.setdefault(c[0].strip(), []).append(i)
    for e in ents:
        idxs = cov_by_entry.get(e, [])
        assert len(idxs) == 1, ("coverage entry 命中数 !=1", e, len(idxs))
    log(L, "[5] 32 entry 在 coverage 均唯一命中 OK")

    # atlas
    atlas = load_atlas()
    log(L, "[6] atlas 载入 %d 个 entry" % len(atlas))

    # 改前指标
    mb = metrics(cov_rows, atlas)
    log(L, "[7] 改前实测：")
    log(L, "    数据行=%d  列数分布=%s" % (mb["data_rows"], mb["colcount"]))
    log(L, "    全表[已证]=%d  atlas内=%d  atlas外=%d" % (mb["proved_total"], mb["proved_atlas"], mb["proved_out"]))
    log(L, "    口径A([已证]且含④)=%d  口径B([已证]且含「④ 活表槽位见证」)=%d" % (mb["cal_A"], mb["cal_B"]))
    log(L, "    §12.6 命中行=%d 命中次数=%d  CLSID None 次=%d" % (mb["s126_rows"], mb["s126_hits"], mb["clsid_none_hits"]))
    log(L, "    名义达标=%s  严格达标=%s" % (",".join(mb["nominal"]), ",".join(mb["strict"])))

    # 校验 defects.tsv 与 REPLACEMENTS 一致
    dl = def_raw.decode("utf-8").splitlines()
    defs = {}
    for line in dl[1:]:
        if not line.strip():
            continue
        p = line.split("\t")
        defs[p[0]] = (p[2], p[3])
    assert defs == REPLACEMENTS, ("defects 与 REPLACEMENTS 不一致", defs)
    log(L, "[8] defects.tsv 10 行 old->new 与脚本 REPLACEMENTS 逐项一致 OK")

    # ---- 逐行构建与验证 ----
    changes = []   # 每行：line_index, entry, kind, old_col4, expected_new_col4, new_col4(delta), pair
    for d in delta:
        e = d["entry"]
        idx = cov_by_entry[e][0]
        oldcols = cov_rows[idx]["cols"]
        newcols = d["cols"]
        assert len(oldcols) == 8 and len(newcols) == 8
        old_col4 = oldcols[3]
        new_col4 = newcols[3]
        # 第1/2/3/5/6/7/8 列逐字节相同
        for k in (0,1,2,4,5,6,7):
            assert oldcols[k] == newcols[k], ("越权改动 col%d" % (k+1), e, repr(oldcols[k])[:80], repr(newcols[k])[:80])
        # 分类
        if e in REPLACEMENTS:
            oldtok, newtok = REPLACEMENTS[e]
            cnt = old_col4.count(oldtok)
            assert cnt == 1, ("替换 token 出现次数 !=1", e, oldtok, cnt)
            expected = old_col4.replace(oldtok, newtok, 1) + APPEND
            kind = "replace"
            pair = (oldtok, newtok)
        else:
            expected = old_col4 + APPEND
            kind = "append"
            pair = None
        assert expected == new_col4, (
            "重建新第4列不等 delta（%s）" % e,
            kind, "expected_len", len(expected), "delta_len", len(new_col4),
            "first_diff", next((i for i,(a,b) in enumerate(zip(expected,new_col4)) if a!=b), min(len(expected),len(new_col4))))
        # 追加句行末、仅一次
        assert new_col4.endswith(APPEND), ("追加句不在行末", e)
        assert new_col4.count(APPEND) == 1, ("追加句重复", e)
        assert "§12.6" not in old_col4, ("原文已含 §12.6", e)
        changes.append({"idx": idx, "entry": e, "kind": kind, "pair": pair,
                        "old_col4": old_col4, "new_col4": new_col4,
                        "old_cov_line": idx + 2})  # +2: header 为第1行，数据 idx0 为第2行
    n_rep = sum(1 for c in changes if c["kind"]=="replace")
    n_app = sum(1 for c in changes if c["kind"]=="append")
    assert n_rep == 10 and n_app == 22, ("分类计数错", n_rep, n_app)
    log(L, "[9] 逐行重建通过：替换 %d 行 / 只追加 %d 行；1/2/3/5/6/7/8 列逐字节相同；追加句行末且仅一次" % (n_rep, n_app))
    log(L, "[9a] 10 行替换对（old -> new，各在旧第4列出现恰好 1 次）：")
    for c in changes:
        if c["kind"] == "replace":
            log(L, "     %s : %r -> %r  (行号 %d)" % (c["entry"], c["pair"][0], c["pair"][1], c["old_cov_line"]))

    # 检查 check18.tsv 给的行号是否与 idx+2 一致（10 行 + 8 抽样）
    ck = open(os.path.join(ROOT,"R16_AUDIT_PIVOT32","check18.tsv"), encoding="utf-8").read().splitlines()
    ckm = {p[0]: int(p[2]) for p in (x.split("\t") for x in ck[1:]) if len(p)>2}
    for c in changes:
        if c["entry"] in ckm:
            assert ckm[c["entry"]] == c["old_cov_line"], ("行号与 audit 不一致", c["entry"], ckm[c["entry"]], c["old_cov_line"])
    log(L, "[10] 行号与 check18.tsv（18 行）逐项一致 OK")

    # ---- 构建 pin + after 内容 ----
    # pin 文件：把 32 行的 col4 用一个唯一 sentinel 替代，其余字节完全同 before。
    SENT = "@@R16PIVOT32_COL4_%04d@@"
    pin_lines = []
    idx2sent = {}
    for k, c in enumerate(changes):
        idx2sent[c["idx"]] = SENT % k
    for i, r in enumerate(cov_rows):
        if i in idx2sent:
            body = "\t".join(r["cols"][:3] + [idx2sent[i]] + r["cols"][4:]).encode("utf-8")
        else:
            body = r["body"]
        raw = body + (b"\n" if r["had_eol"] else b"")
        pin_lines.append(raw)
    pin_bytes = cov_header + b"".join(pin_lines)
    # 断言 pin 结构：sentinel 恰好 32 个
    for k in range(len(changes)):
        assert pin_bytes.count((SENT % k).encode("utf-8")) == 1, ("sentinel 不唯一", k)

    # 重建 before（用 old_col4）
    restore_before = pin_bytes
    for k, c in enumerate(changes):
        restore_before = restore_before.replace((SENT % k).encode("utf-8"), c["old_col4"].encode("utf-8"), 1)
    assert sha(restore_before) == before_cov_sha, ("重建 before sha 不符", sha(restore_before), before_cov_sha)
    log(L, "[11] PIN + before_col4 重建 sha == 改前 sha OK  (%s)" % before_cov_sha)

    # 构建 staged after coverage（用 new_col4）
    after_bytes = pin_bytes
    for k, c in enumerate(changes):
        after_bytes = after_bytes.replace((SENT % k).encode("utf-8"), c["new_col4"].encode("utf-8"), 1)
    assert sha(after_bytes) != before_cov_sha, "after 与 before 相同，未生效"
    log(L, "[12] PIN + after_col4 构建 after，sha = %s" % sha(after_bytes))

    # 改后指标
    _, after_rows = parse_coverage_bytes(after_bytes)
    ma = metrics(after_rows, atlas)
    log(L, "[13] 改后实测：")
    log(L, "    数据行=%d  列数分布=%s" % (ma["data_rows"], ma["colcount"]))
    log(L, "    全表[已证]=%d  atlas内=%d  atlas外=%d" % (ma["proved_total"], ma["proved_atlas"], ma["proved_out"]))
    log(L, "    口径A=%d  口径B=%d  §12.6命中行=%d 命中次数=%d  CLSID None 次=%d" % (
        ma["cal_A"], ma["cal_B"], ma["s126_rows"], ma["s126_hits"], ma["clsid_none_hits"]))
    log(L, "    名义达标=%s  严格达标=%s" % (",".join(ma["nominal"]), ",".join(ma["strict"])))

    # ---- 11 项断言 ----
    # ① 严格前缀（22）
    for c in changes:
        if c["kind"] == "append":
            assert c["new_col4"].startswith(c["old_col4"]), ("非严格前缀", c["entry"])
    log(L, "[14] ① 22 行只追加严格前缀 OK")
    # ② 10 行可解释替换（已在 [9] 逐行证明）
    log(L, "[15] ② 10 行 .replace(old,new,1)+追加句 逐字节成立（见 [9a] 替换对）")
    # ③ 逐字节还原性（[11] 已证明）
    log(L, "[16] ③ PIN+before_col4 重建 sha==改前 OK")
    # ④ 不变量
    for k, expect in [("data_rows",18498),("proved_total",1654),("proved_atlas",1648),("proved_out",6)]:
        assert mb[k]==expect, ("改前不变量不符",k,mb[k],expect)
        assert ma[k]==expect, ("改后不变量不符",k,ma[k],expect)
    assert mb["colcount"]=={8:18498} and ma["colcount"]=={8:18498}, ("列数分布不符", mb["colcount"], ma["colcount"])
    log(L, "[17] ④ 不变量 18498/{8:18498}/[已证]1654/atlas内1648/外6 改前改后均 OK")
    # ⑤ 只有第4列变，其它列未变（[9] 已证明 delta vs cov；再核 after vs before 全表）
    diff_rows = 0
    for i,(br,ar) in enumerate(zip(cov_rows, after_rows)):
        bc, ac = br["cols"], ar["cols"]
        if bc == ac:
            continue
        diff_rows += 1
        assert len(bc)==len(ac)==8
        assert all(bc[k]==ac[k] for k in (0,1,2,4,5,6,7)), ("非第4列改动", i)
    assert diff_rows == 32, ("改动行数 !=32", diff_rows)
    log(L, "[18] ⑤ 全表逐行比对：仅 32 行第4列变，其它 7 列逐字节相同，grade 未变 OK")
    # ⑥ 口径 A/B 不增（实测）
    assert ma["cal_A"] <= mb["cal_A"], ("口径A增加", mb["cal_A"], ma["cal_A"])
    assert ma["cal_B"] <= mb["cal_B"], ("口径B增加", mb["cal_B"], ma["cal_B"])
    log(L, "[19] ⑥ 口径A %d->%d、口径B %d->%d（均不增）OK" % (mb["cal_A"],ma["cal_A"],mb["cal_B"],ma["cal_B"]))
    # ⑦ CLSID None 归零
    assert ma["clsid_none_hits"] == 0, ("CLSID None 未归零", ma["clsid_none_hits"])
    log(L, "[20] ⑦ 全文 CLSID None = %d（归零）OK" % ma["clsid_none_hits"])
    # ⑧ §12.6 +32
    d_rows_hit = ma["s126_rows"] - mb["s126_rows"]
    d_hits_hit = ma["s126_hits"] - mb["s126_hits"]
    assert d_rows_hit == 32, ("§12.6 行增量 !=32", d_rows_hit)
    assert d_hits_hit == 64, ("§12.6 字面命中次数增量 !=64（追加句每处含两次 §12.6）", d_hits_hit)
    log(L, "[21] ⑧ §12.6 命中行 +%d（%d→%d）；字面命中次数 +%d（%d→%d，每句含两次）OK" % (
        d_rows_hit, mb["s126_rows"], ma["s126_rows"], d_hits_hit, mb["s126_hits"], ma["s126_hits"]))
    # ⑩ 达标未翻转
    assert mb["nominal"]==["S15","S16","S17"] and mb["strict"]==["S17"], ("改前达标异常", mb["nominal"], mb["strict"])
    assert ma["nominal"]==mb["nominal"] and ma["strict"]==mb["strict"], ("达标翻转", ma["nominal"], ma["strict"])
    log(L, "[22] ⑩ 达标未翻转：名义 %s / 严格 %s OK" % (",".join(ma["nominal"]), ",".join(ma["strict"])))
    # ⑪ 行尾不混用
    assert after_bytes.count(b"\r")==0, "after 有 CR"
    log(L, "[23] ⑪ after 行尾全 LF 无 CR OK")

    # ---- PANEL M96 披露 ----
    # M95 块 = 行 274..278（1-based），即 lines idx 273..277。插在 idx 278 (行279) 之前。
    pan_lines = pan_raw.splitlines(keepends=True)
    assert pan_lines[273].decode("utf-8").startswith("> ✅ **M95 补记"), ("M95 起始行不符", repr(pan_lines[273][:60]))
    assert pan_lines[277].decode("utf-8").rstrip("\n").endswith("严格仍 S17。"), ("M95 末行不符", repr(pan_lines[277][-60:]))
    assert pan_lines[278].decode("utf-8").startswith("> 📌 **M77 并表实算说明"), ("插入锚点不符", repr(pan_lines[278][:60]))
    log(L, "[24] PANEL M95 块定位 = 行 274-278，插入点在其后（行 279 前）OK")

    pctA_b = 100.0*mb["cal_A"]/mb["proved_total"]
    pctA_a = 100.0*ma["cal_A"]/ma["proved_total"]
    pctB_b = 100.0*mb["cal_B"]/mb["proved_total"]
    pctB_a = 100.0*ma["cal_B"]/ma["proved_total"]
    M96 = [
        "> ✅ **M96 补记：R16-FIX-PIVOT32 并入 32 行（10 行 CLSID 错值替换 + 22 行仅追加 §12.6 引用；全文 CLSID None 归零）**\n",
        "> 本批 32 行取自 `R16_FIX_PIVOT32/delta.tsv`（S22 `TClassFactory::slot3` 同族），改前第 4 列已含 `④ 活 COM 类对象`，全 atlas 内；只改 coverage 第 4 列，第 1/2/3/5/6/7/8 列逐字节相同，grade 未改。\n",
        "> §A 10 行错值替换（`006BF810` `7E9580`→`007E9950`；9 行 `CLSID None`→`CLSID 00xxxxxx`）经 `R16_AUDIT_PIVOT32/VERDICT.md` 判 18/18 PASS、0 必改、有据精确最小；22 行仅追加；32/32 追加句逐字节统一、行末且仅一次。\n",
        "> 数字（口径 A/B 实测，改前→改后）：口径 A（`[已证]` 且第 4 列含字符 `④`）%d / %d（%.2f%%）→ %d / %d（%.2f%%），不增（32 行改前已含 `④`）；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）%d / %d（%.2f%%）→ %d / %d（%.2f%%），不增（追加句不含该子串）。§12.6 全表命中行 +%d（%d→%d；每句含两处 `§12.6` 字面，字面次数 +%d）；全文 `CLSID None` 归零。\n" % (
            mb["cal_A"], mb["proved_total"], pctA_b, ma["cal_A"], ma["proved_total"], pctA_a,
            mb["cal_B"], mb["proved_total"], pctB_b, ma["cal_B"], ma["proved_total"], pctB_a,
            d_rows_hit, mb["s126_rows"], ma["s126_rows"], d_hits_hit),
        "> 判定与计数均未变：coverage 18,498 数据行、全表 `[已证]` 1,654、atlas 内 1,648、atlas 外 6；名义仍 S15/S16/S17、严格仍 S17，**达标判定未翻转**。\n",
    ]
    M96_bytes = "".join(M96).encode("utf-8")
    # 插入
    pan_after = b"".join(pan_lines[:278]) + M96_bytes + b"".join(pan_lines[278:])
    # 还原性：删 M96 块后 sha == 改前
    assert pan_after.replace(M96_bytes, b"", 1) == pan_raw, "PANEL 删块还原失败（非纯插入）"
    assert sha(pan_after.replace(M96_bytes, b"", 1)) == before_pan_sha, "PANEL 还原 sha 不符"
    log(L, "[25] ⑨ PANEL 纯插入 M96 块（%d 字节），删块后 sha == 改前 sha OK" % len(M96_bytes))
    # 既有内容零删除零改字：pan_after 去掉插入块 == pan_raw（上面已证）

    # ---- 写 staged 与证据 ----
    open(STAGE_COV, "wb").write(after_bytes)
    open(STAGE_PAN, "wb").write(pan_after)
    with open(PIN_REPORT, "w", encoding="utf-8") as f:
        json.dump({
            "before_cov_sha": before_cov_sha,
            "after_cov_sha": sha(after_bytes),
            "before_pan_sha": before_pan_sha,
            "after_pan_sha": sha(pan_after),
            "sentinel_template": SENT,
            "pin_kind": "pin = before coverage with 32 target col4 replaced by sentinel; stored implicitly via ledger below",
            "changes": changes,
            "M96_insert_after_line": 278,
            "M96_bytes_len": len(M96_bytes),
            "M96_text": M96_bytes.decode("utf-8"),
            "metrics_before": {k:v for k,v in mb.items() if k!="perS"},
            "metrics_after": {k:v for k,v in ma.items() if k!="perS"},
        }, f, ensure_ascii=False, indent=1)
    # 保存 pin 与 before_col4 的实际文件（用于写盘后自证）
    open(os.path.join(OUT,"_PIN_coverage.tsv"),"wb").write(pin_bytes)
    open(os.path.join(OUT,"_before_col4.json"),"w",encoding="utf-8").write(
        json.dumps({str(c["idx"]):{"entry":c["entry"],"col4":c["old_col4"]} for c in changes}, ensure_ascii=False, indent=1))
    open(REPORT,"w",encoding="utf-8").write("\n".join(L)+"\n")
    print("\n=== ALL PRE-COMMIT CHECKS PASSED ===")
    print("staged coverage:", STAGE_COV, sha(after_bytes))
    print("staged PANEL   :", STAGE_PAN, sha(pan_after))
    return True

if __name__ == "__main__":
    analyze()
