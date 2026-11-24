# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B1 · 执行合并（coverage.tsv / PANEL.md 唯一写者）。

写域：COVERAGE/coverage.tsv（仅 15 行第 4 列）、COVERAGE/PANEL.md（1 处指针 + 1 处插入）、
      产物目录 R16_MERGE_SLOTN_B1/。其余一律只读。
"""
import hashlib, json, os, re, shutil, sys, collections, datetime, subprocess
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B1", "delta.tsv")
OUTD = os.path.join(ROOT, "R16_MERGE_SLOTN_B1")
STRICT_SRC = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

OLD = "R14_COMMON §12.4"
NEW = "R14_COMMON §12.6"
POINTER_OLD = "> 成文位置：`R14_COMMON.md §12.4`。"
POINTER_NEW = "> 成文位置：`R14_COMMON.md §12.6`。"
ANCHOR = "> 📌 **M77 并表实算说明**"

M86_LINES = [
    "> ✅ **M86 补记：43 行 `slotN` 的 ④ 开始成文 —— 批次 1 并入 15 行（D-47(A) 裁决后解封）**",
    "> 依据 **D-47 (A)**（`R14_COMMON §12.6`）：槽位占用即 ④，§12.3 对该形态让位；",
    "> 本批 15 行取自 `PROBE_802\\slotN43.tsv` 数据行 1–15，`col_ok=match` / `install_ext=y` 15/15；",
    "> 每行 ④ 含 vt/COL/offset/RTTI/装表点四元组，并**自带 D-47 披露指针**；",
    "> 审计（异族）判 **PASS 15 / FAIL 0 / 必改 0**，90/90 字节项独立复算为真；",
    "> 「**④ 已成文**」由 **319 / 1,654（19.29%）升至 334 / 1,654（20.19%）**；",
    "> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**；",
    "> 引用纪律：引用这 15 行时须同引 D-47 裁决与本节披露，**不得**表述为「已过 §12.3」。",
]

def sha(b): return hashlib.sha256(b).hexdigest()

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except Exception: return e

def statinfo(p):
    st = os.stat(p); b = open(p, "rb").read()
    iso = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    return dict(path=p, mtime=st.st_mtime, mtime_local=iso, bytes=len(b), sha256=sha(b),
                nlines_lf=b.count(b"\n"), crlf=b.count(b"\r\n"),
                bom=(b[:3] == b"\xef\xbb\xbf"), ends_nl=b.endswith(b"\n"))

def load_atlas():
    s = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip(): s.add(ne(p[0]))
    return s

def cov_metrics(text):
    data = text.splitlines()[1:]
    coldist = collections.Counter(len(ln.split("\t")) for ln in data)
    atlas = load_atlas()
    yz = ina = outa = sih = 0
    for ln in data:
        c = ln.split("\t")
        if len(c) < 8: continue
        if c[4].strip() == "[已证]":
            yz += 1
            if "\u2463" in c[3]: sih += 1
            if ne(c[0]) in atlas: ina += 1
            else: outa += 1
    return dict(data_rows=len(data), coldist=dict((str(k), v) for k, v in coldist.items()),
                yizheng=yz, atlas_in=ina, atlas_out=outa, sih_yizheng=sih)

def main():
    os.makedirs(OUTD, exist_ok=True)

    cov_b = open(COV, "rb").read(); pan_b = open(PANEL, "rb").read(); delta_b = open(DELTA, "rb").read()
    cov_before = statinfo(COV); pan_before = statinfo(PANEL); delta_info = statinfo(DELTA)
    cov_text = cov_b.decode("utf-8"); pan_text = pan_b.decode("utf-8")
    metrics_before = cov_metrics(cov_text)

    shutil.copyfile(COV, os.path.join(OUTD, "coverage.before.bak"))
    shutil.copyfile(PANEL, os.path.join(OUTD, "PANEL.before.bak"))

    drows = [ln.split("\t") for ln in delta_b.decode("utf-8-sig").splitlines()[1:]]
    assert len(drows) == 15, len(drows)
    repl_count = 0; newcol = {}
    for d in drows:
        assert len(d) == 8
        c = d[3]; repl_count += c.count(OLD)
        newcol[ne(d[0])] = c.replace(OLD, NEW)
    assert repl_count == 15, repl_count

    cov_lines = cov_text.splitlines(keepends=True)
    by_entry = {}
    for idx, ln in enumerate(cov_lines):
        core = ln[:-1] if ln.endswith("\n") else ln
        c = core.split("\t")
        if len(c) >= 8: by_entry.setdefault(ne(c[0]), []).append(idx)
    target = []
    for d in drows:
        e = ne(d[0]); idxs = by_entry.get(e, [])
        assert len(idxs) == 1, (e, idxs)
        i = idxs[0]; ln = cov_lines[i]
        core = ln[:-1] if ln.endswith("\n") else ln
        c = core.split("\t")
        assert len(c) == 8, (e, len(c))
        before4 = c[3]; after4 = newcol[e]
        assert after4.startswith(before4), ("strict-prefix FAIL", e)
        for j in [0, 1, 2, 4, 5, 6, 7]:
            assert c[j] == d[j], ("other-col mismatch", e, j)
        assert "\u2463" in after4, ("after missing circled4", e)
        # 部分行改前第4列已含 ④（合同闭合 ③b④ 分类标签里），属原文固有，不是本批追加
        target.append(dict(entry=e, line_index=i, before4=before4, after4=after4,
                           before_has_circled4=("\u2463" in before4),
                           added_bytes=len(after4.encode("utf-8")) - len(before4.encode("utf-8"))))

    for t in target:
        i = t["line_index"]; ln = cov_lines[i]
        nl = "\n" if ln.endswith("\n") else ""
        core = ln[:-1] if nl else ln
        c = core.split("\t"); c[3] = t["after4"]
        cov_lines[i] = "\t".join(c) + nl
    cov_after_text = "".join(cov_lines); cov_after_b = cov_after_text.encode("utf-8")
    assert cov_after_b.count(b"\n") == cov_b.count(b"\n"), "coverage LF count changed"
    assert cov_after_b[:3] != b"\xef\xbb\xbf" and not cov_after_b.endswith(b"\n")

    pan_lines = pan_text.splitlines(keepends=True)
    ptrs = [i for i, ln in enumerate(pan_lines) if POINTER_OLD in ln]
    assert len(ptrs) == 1, ("pointer occurrences", ptrs)
    pi = ptrs[0]
    pan_lines[pi] = pan_lines[pi].replace(POINTER_OLD, POINTER_NEW)
    anchors = [i for i, ln in enumerate(pan_lines) if ln.startswith(ANCHOR)]
    assert len(anchors) == 1, ("anchor occurrences", anchors)
    ai = anchors[0]
    pan_lines[ai:ai] = [s + "\n" for s in M86_LINES]
    pan_after_text = "".join(pan_lines); pan_after_b = pan_after_text.encode("utf-8")
    assert pan_after_b.count(b"\n") == pan_b.count(b"\n") + len(M86_LINES)

    for path, data in [(COV, cov_after_b), (PANEL, pan_after_b)]:
        tmp = path + ".tmp_r16merge"
        with open(tmp, "wb") as f: f.write(data)
        os.replace(tmp, path)

    cov_after = statinfo(COV); pan_after = statinfo(PANEL)
    metrics_after = cov_metrics(cov_after_text)

    before_state = dict(
        coverage=dict(cov_before, metrics=metrics_before,
                      target_rows=[dict(entry=t["entry"], col4_before=t["before4"],
                                        before_has_circled4=t["before_has_circled4"]) for t in target]),
        panel=dict(pan_before, pointer_line=POINTER_OLD, insert_anchor=ANCHOR, inserted_lines=M86_LINES),
        delta=dict(delta_info, nrows=15, replacement_pattern=OLD, replacement_new=NEW,
                   replacement_count=repl_count))
    with open(os.path.join(OUTD, "before_state.json"), "w", encoding="utf-8") as f:
        json.dump(before_state, f, ensure_ascii=False, indent=1)

    slocal = os.path.join(OUTD, "strict_panel_local.py")
    ssrc = open(STRICT_SRC, encoding="utf-8").read()
    newout = 'OUT = os.path.join(ROOT, "R16_MERGE_SLOTN_B1", "strict_out")'
    ssrc2, n = re.subn(r'^OUT\s*=.*$', newout, ssrc, flags=re.M)
    assert n == 1, ("strict OUT replace count", n)
    with open(slocal, "w", encoding="utf-8") as f: f.write(ssrc2)
    r = subprocess.run([sys.executable, slocal], capture_output=True, text=True, encoding="utf-8")
    nominal = re.search(r"名义达标:\s*(\S+)", r.stdout)
    strict = re.search(r"严格达标:\s*(\S+)", r.stdout)
    nominal = nominal.group(1) if nominal else None
    strict = strict.group(1) if strict else None

    after_state = dict(
        coverage=dict(cov_after, metrics=metrics_after),
        panel=dict(pan_after),
        strict=dict(nominal=nominal, strict=strict, returncode=r.returncode,
                    stdout=r.stdout, stderr=r.stderr,
                    script="strict_panel_local.py (copy; only OUT redirected to own dir)",
                    out_dir=os.path.join(OUTD, "strict_out")))
    with open(os.path.join(OUTD, "after_state.json"), "w", encoding="utf-8") as f:
        json.dump(after_state, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUTD, "strict_stdout.txt"), "w", encoding="utf-8") as f:
        f.write(r.stdout + ("\n[STDERR]\n" + r.stderr if r.stderr else ""))

    print("MERGE DONE")
    print("coverage bytes %d -> %d  sha %s -> %s" % (cov_before["bytes"], cov_after["bytes"], cov_before["sha256"][:8], cov_after["sha256"][:8]))
    print("panel    bytes %d -> %d  sha %s -> %s" % (pan_before["bytes"], pan_after["bytes"], pan_before["sha256"][:8], pan_after["sha256"][:8]))
    print("replacements=%d target_rows=%d before_already_has_④=%d" % (
        repl_count, len(target), sum(1 for t in target if t["before_has_circled4"])))
    print("④chengwen before=%d after=%d" % (metrics_before["sih_yizheng"], metrics_after["sih_yizheng"]))
    print("nominal=%s strict=%s strict_rc=%d" % (nominal, strict, r.returncode))
    if r.returncode != 0: print("STRICT STDERR:", r.stderr)

if __name__ == "__main__":
    main()
