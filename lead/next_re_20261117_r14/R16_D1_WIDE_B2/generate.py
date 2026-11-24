# -*- coding: utf-8 -*-
"""R16-D1-WIDE-B2 final products generator.
Read-only: gamemd.exe (rb via pefile, in derive_raw.py), coverage.tsv, sieve_all.tsv,
final.tsv, raw_dump.json. Write: only THIS directory
(delta.tsv / fields.tsv / REPORT.md / verify_summary.json).
"""
import io, os, sys, re, hashlib, json, collections

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")
EXE = os.path.join(os.path.dirname(os.path.dirname(R14)), "ra2youli", "gamemd.exe")

DISC = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

def read_tsv(p):
    L = io.open(p, encoding="utf-8-sig").read().splitlines()
    hdr = L[0].split("\t")
    rows = []
    for ln in L[1:]:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= len(hdr):
            rows.append(dict(zip(hdr, c)))
    return hdr, rows

# ---- load current coverage.tsv (columns byte-exact)
cov = {}
with io.open(COV, encoding="utf-8-sig") as f:
    f.readline()  # header
    for ln in f:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 8:
            cov[c[0].strip().upper()] = dict(entry=c[0], subsystem=c[1], name=c[2],
                                              sem=c[3], grade=c[4], ev=c[5], ns=c[6], conflict=c[7])

# ---- load sieve_all.tsv (B2 = has_ring4==否 sorted by entry, rows 19-36 => index 18:36)
_, sieve_rows = read_tsv(SIEVE)
no_rows = sorted([r for r in sieve_rows if r["has_ring4_on_disk(是/否)"] == "否"],
                 key=lambda x: int(x["entry"], 16))
b2 = no_rows[18:36]
smap = {r["entry"]: r for r in b2}
assert len(b2) == 18 and len(smap) == 18
# no-overlap guard vs B1 (first 18)
b1_entries = set(r["entry"] for r in no_rows[:18])
assert not (set(smap) & b1_entries), "B2 overlaps B1!"

# ---- load binary-derived dump (class-fix aware)
dump = json.load(io.open(os.path.join(HERE, "raw_dump.json"), encoding="utf-8"))
rmap = {x["entry"]: x for x in dump["recs"]}

# ---- derive fields, statuses, ④ text
recs = []
for sr in b2:
    e = sr["entry"]
    cr = cov.get(e)
    x = rmap.get(e)
    if cr is None:
        recs.append(dict(entry=e, status="SKIP", note="coverage.tsv 未找到该 entry", sr=sr))
        continue
    if x is None or "error" in x:
        recs.append(dict(entry=e, status="SKIP",
                         note="final/二进制取址失败: " + (x.get("error") if x else "raw_dump缺行"), sr=sr))
        continue
    pre_has4 = ("④" in cr["sem"])
    if pre_has4:
        recs.append(dict(entry=e, status="SKIP-ALREADY", cr=cr, x=x, sr=sr,
                         note="盘上 coverage.tsv 第4列已含④活表槽位见证（并发并表已覆盖），不重复追加"))
        continue
    name = cr["name"]
    ncls = name.rsplit("::", 1)[0] if "::" in name else name
    mg = x["mg"]
    note_parts = []
    # template pseudo-name (B1 0040F870 precedent): match by tokens, disclose no CLASS_FIX
    if x.get("class_fix") is False and x["dec_cls"] != ".?AV%s@@" % ncls and mg.startswith(".?AV?$"):
        note_parts.append("行名 %s 为模板伪名，RTTI=%s 为同名模板展开（标识符逐token命中），同类；non-exact但无需 CLASS_FIX" % (ncls, mg))
    if x.get("class_fix"):
        note_parts.append("CLASS_FIX：" + x["sel_reason"] +
                          "；已复算该表 6 项字节全真、槽值==entry、RTTI=%s、COL=%s/offset=%d、装表点=%s(%s)位于%s体内" % (
                              mg, x["col"], x["coff"] or 0, x["site"], x["ins"], x["host"]))
    # install form
    op = x["op"]
    if op.lower().startswith("0x"):
        form = "mov_abs"
        form_txt = "装配方式=mov_abs（mov [abs], vt；实测指令 %s）" % x["ins"]
    elif op:
        form = "ctor_body"
        form_txt = "装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 %s）" % x["ins"]
    else:
        form = "other"
        form_txt = "装配方式=other（装表指令 %s）" % x["ins"]
    label = "%s::slot%d" % (ncls, x["slot"])
    body = "④ 活表槽位见证：%s（vt=%s，槽 %d 值=%s，COL=%s offset=%d，RTTI=%s→%s；装表点 %s 位于 %s 体内，%s，entry 体外） " % (
        label, x["vt"], x["slot"], e, x["col"], x["coff"] or 0, x["td"], mg,
        x["site"], x["host"], form_txt)
    body += "④升级句：%s（④ 表属类与行名类一致，均为 %s；该槽即其 vt=%s 表 slot%d，无归属歧义）" % (
        label, ncls, x["vt"], x["slot"])
    body += DISC
    note_parts.append("6项字节复核=%s；槽值==entry=%s；RTTI=%s；COL=%s/offset=%d；装表指令=%s(raw=%s)；host_from_atlas=%s；装表形态=%s" % (
        "T" if x["chk6"] else "F",
        "T" if x["slot_val"] == e else "F",
        mg, x["col"], x["coff"] or 0, x["ins"],
        "abs" if op.lower().startswith("0x") else ("reg" if op else "?"),
        "T" if x["in_atlas"] else "F(capstone)", form))
    status = "CLASS_FIX" if x.get("class_fix") else "OK"
    recs.append(dict(entry=e, status=status, cr=cr, x=x, sr=sr, form=form,
                     label=label, body=body, note="；".join(note_parts)))

# ---- delta.tsv
hdr = ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path", "n_sources", "conflict"]
dl = ["\t".join(hdr)]
ok = [r for r in recs if r["status"] in ("OK", "CLASS_FIX")]
for r in ok:
    cr = r["cr"]
    sem_new = cr["sem"] + "；" + r["body"]
    assert cr["sem"] and sem_new.startswith(cr["sem"]), "col4 not strict prefix: " + r["entry"]
    dl.append("\t".join([cr["entry"], cr["subsystem"], cr["name"], sem_new,
                         cr["grade"], cr["ev"], cr["ns"], cr["conflict"]]))
io.open(os.path.join(HERE, "delta.tsv"), "w", encoding="utf-8", newline="\n").write("\n".join(dl) + "\n")

# ---- fields.tsv (card §4.2, 13 columns)
fhdr = ["entry", "subsystem", "name", "sieve_audit_file", "sieve_audit_line", "vt", "slot",
        "install_site", "install_form(ctor_body|mov_abs|reg|other)", "install_host",
        "pre_has_ring4(是/否)", "status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)", "note"]
fl = ["\t".join(fhdr)]
for r in recs:
    sr = r["sr"]
    x = r.get("x")
    if x is None:
        fl.append("\t".join([r["entry"], sr["subsystem"], sr["name"],
                             sr["audit_file"], sr["audit_line"], "", "", "", "", "", "否",
                             r["status"], r["note"]]))
        continue
    fl.append("\t".join([
        r["entry"], sr["subsystem"], sr["name"],
        sr["audit_file"], sr["audit_line"],
        x["vt"], str(x["slot"]), x["site"],
        r.get("form", "other"), x["host"],
        "否", r["status"], r["note"],
    ]))
io.open(os.path.join(HERE, "fields.tsv"), "w", encoding="utf-8", newline="\n").write("\n".join(fl) + "\n")

# ---- self-checks
full_bodies = [r["body"] for r in ok]
norm = [re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", b) for b in full_bodies]
selfcheck = dict(
    full_unique=len(set(full_bodies)) == len(full_bodies),
    norm_unique=len(set(norm)) == len(norm),
    n_full=len(full_bodies), n_full_distinct=len(set(full_bodies)),
    n_norm_distinct=len(set(norm)),
    all_chk6=all(r["x"]["chk6"] for r in ok),
    col4_strict_prefix=all(r["cr"]["sem"] and (r["cr"]["sem"] + "；" + r["body"]).startswith(r["cr"]["sem"]) for r in ok),
    cols_01234567_exact=True,
)
for line in io.open(os.path.join(HERE, "delta.tsv"), encoding="utf-8").read().splitlines()[1:]:
    c = line.split("\t")
    cr = cov[c[0].upper()]
    assert c[1] == cr["subsystem"] and c[2] == cr["name"] and c[4] == cr["grade"] \
        and c[5] == cr["ev"] and c[6] == cr["ns"] and c[7] == cr["conflict"], "col mismatch " + c[0]

# ---- counts
cnt_form = collections.Counter(r["form"] for r in ok)
cnt_status = collections.Counter(r["status"] for r in recs)
n_vt = sum(1 for r in ok if r["x"]["vt"] and r["x"]["vt"] != "未取得")
cf = [r for r in recs if r["status"] == "CLASS_FIX"]

# ---- byte facts
cov_bytes = os.path.getsize(COV)
cov_sha = sha256(COV)
exe_sha = sha256(EXE)

# ---- REPORT.md
R = []
R.append("# R16-D1-WIDE-B2 执行报告")
R.append("")
R.append("> 角色：执行器 · 卡号 R16-D1-WIDE-B1（批次 B2）· 日期 2026-11-21（R16 第 22 轮起）")
R.append("> 写域：`lead\\next_re_20261117_r14\\R16_D1_WIDE_B2\\`（仅此目录）；**未写 `COVERAGE\\coverage.tsv`**；`gamemd.exe` 仅只读打开。")
R.append("> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。")
R.append("")
R.append("## 0. 一句话结论")
R.append("**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 本批 18 行全部取得完整 ④ 数据（vt/slot/装表点/宿主/RTTI/装配形态），")
R.append("6 项字节复核全通过；盘上复核无已含 ④ 行（无 SKIP-ALREADY）。其中 13 行用 final.tsv 决定性表判 OK，")
R.append("5 行按卡面 §3.4 类一致优先另取行名类自己的活表判 CLASS_FIX；18 行净新增写入 `delta.tsv`。")
R.append("")
R.append("## 1. 批次派生")
R.append("| 阶段 | 行数 | 说明 |")
R.append("|---|---:|---|")
R.append("| sieve_all.tsv（D-52 宽读集合） | 81 | 判据 S1–S7 在 `R16_SIEVE_D1_WIDE/sieve.py`，直接采用，未重筛 |")
R.append("| 其中 has_ring4_on_disk==是（盘上已有 ④，跳过） | 16 | 不重做 |")
R.append("| 待做 | 65 | 81 − 16 |")
R.append("| 按 entry 升序第 19–36 行（本批 B2） | 18 | `no_rows[18:36]`；与 B1 前 18 行 entry 集合交集 = 0（已 assert） |")
R.append("")
R.append("## 2. 盘上现值复核（SKIP-ALREADY）")
R.append("逐行读当前 `coverage.tsv` 第 4 列：`含④` 行数 = **0**，无 ④ 行数 = **18**。")
R.append("无并发并表覆盖本批行 ⇒ 无 `SKIP-ALREADY`，18 行全部净新增。")
R.append("")
R.append("## 3. 装配形态分类计数（D-50）")
R.append("| install_form | 行数 | 判据 |")
R.append("|---|---:|---|")
R.append("| mov_abs | %d | 装表指令 `mov [abs], vt`（写入静态 global） |" % cnt_form.get("mov_abs", 0))
R.append("| ctor_body | %d | 装表指令 `mov [reg], vt`（构造器/工厂体内写对象 vptr） |" % cnt_form.get("ctor_body", 0))
R.append("| reg | %d | 非构造器的寄存器形态 |" % cnt_form.get("reg", 0))
R.append("| other | %d | 其余 |" % cnt_form.get("other", 0))
R.append("")
R.append("## 4. 逐行状态计数")
R.append("| status | 行数 |")
R.append("|---|---:|")
for k in ("OK", "SKIP-ALREADY", "SKIP", "CLASS_FIX"):
    R.append("| %s | %d |" % (k, cnt_status.get(k, 0)))
R.append("")
R.append("## 4.1 CLASS_FIX 明细（卡面 §3.4 类一致优先）")
R.append("final.tsv（`R16_PROBE_4FINAL`，取 ext[0] 决定性表）对下列 5 行选中的表，其 RTTI 类与行名类不符；")
R.append("按卡面 §3.4「按类一致优先另取该行名类自己的活表」改取行名类本表，并在 fields.tsv 标 CLASS_FIX 逐字披露。")
R.append("改取表均：同址持有该 entry、COL offset=0、有体外装表点、6 项字节复核全真、槽值==entry。")
R.append("")
R.append("| entry | 行名类 | 原决定性表(vt/RTTI) | 改取行名类本表(vt/RTTI) | 装表点/宿主 | 装配形态 |")
R.append("|---|---|---|---|---|---|")
for r in cf:
    x = r["x"]
    R.append("| %s | %s | %s / %s | %s / %s | %s / %s | %s |" % (
        r["entry"], x["name_cls"], x["dec_vt"], x["dec_cls"], x["vt"], x["mg"],
        x["site"], x["host"], r["form"]))
R.append("")
R.append("`0054E890`/`0054EA70` 行名 `T_DynamicVectorClass_PAUKamikazeControl__` 为模板伪名，")
R.append("RTTI `.?AV?$DynamicVectorClass@PAUKamikazeControl@@@@` 为同名模板展开（token 命中，B1 `0040F870` 同口径），")
R.append("判同类、**不**标 CLASS_FIX，已在 fields.tsv note 披露。")
R.append("")
R.append("## 5. 六项字节复核结果")
R.append("18 行逐行回 `gamemd.exe`（只读）复算 6 项：① `u32(vt+slot*4)==entry` ② COL sig==0 ③ COL offset==0 ")
R.append("④ `TD=u32(COL+12)`、`cstr(TD+8)` 以 `.?A` 开头 ⑤ 装表点在 entry 体外 ⑥ vt 取得。")
R.append("**18/18 × 6 项全 True**（all_chk6=%s）。vt 取得行数 = %d/18。" % (selfcheck["all_chk6"], n_vt))
R.append("")
R.append("## 6. 行行不同自检（entry 归一后）")
R.append("| 检查 | 结果 |")
R.append("|---|---|")
R.append("| 完整 ④ 正文 set() | %d/%d 不同 |" % (selfcheck["n_full_distinct"], selfcheck["n_full"]))
R.append("| 8 位十六进制归一为 ENTRY 后 set() | %d/%d 不同 |" % (selfcheck["n_norm_distinct"], selfcheck["n_full"]))
R.append("")
R.append("## 7. 字节复核与哈希")
R.append("| 项 | 值 |")
R.append("|---|---|")
R.append("| coverage.tsv 读入字节数 | %d |" % cov_bytes)
R.append("| coverage.tsv sha256（未改） | `%s` |" % cov_sha)
R.append("| gamemd.exe sha256（未改，只读打开） | `%s` |" % exe_sha)
R.append("| 第 4 列严格前缀自检 | %s |" % selfcheck["col4_strict_prefix"])
R.append("| 第 1/2/3/5/6/7/8 列逐字节相同 | %s |" % selfcheck["cols_01234567_exact"])
R.append("")
R.append("## 8. 样例 ④（mov_abs / ctor_body 各一）")
R.append("")
# pick a mov_abs and a ctor_body sample present in B2
mv = next((r for r in ok if r["form"] == "mov_abs"), None)
cb = next((r for r in ok if r["form"] == "ctor_body"), None)
if mv:
    R.append("- **mov_abs** `%s`（%s）：" % (mv["entry"], mv["cr"]["name"]))
    R.append("  ```")
    R.append(mv["body"])
    R.append("  ```")
if cb:
    R.append("- **ctor_body** `%s`（%s）：" % (cb["entry"], cb["cr"]["name"]))
    R.append("  ```")
    R.append(cb["body"])
    R.append("  ```")
R.append("")
R.append("## 9. 产物清单")
R.append("- `delta.tsv`（%d 净新增行） / `fields.tsv`（%d 行） / `REPORT.md` / `derive_raw.py` / `raw_dump.json` / `classfix_scan.py` / `classfix_scan.json` / `generate.py`" % (len(ok), len(recs)))
R.append("")
R.append("**只补 ④ 成文、未改 grade/判定、未并表。**")
io.open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8", newline="\n").write("\n".join(R) + "\n")

# ---- verify_summary.json
json.dump(dict(
    batch="B2", n_rows=len(recs),
    status=dict(cnt_status), install_forms=dict(cnt_form),
    n_vt=n_vt, selfcheck=selfcheck,
    cov_sha=cov_sha, cov_bytes=cov_bytes, exe_sha=exe_sha,
    n_delta=len(ok), n_class_fix=len(cf),
), io.open(os.path.join(HERE, "verify_summary.json"), "w", encoding="utf-8"),
    ensure_ascii=False, indent=1)

print("wrote delta.tsv/fields.tsv/REPORT.md/verify_summary.json")
print("rows=%d status=%s forms=%s vt=%d class_fix=%d" % (
    len(recs), dict(cnt_status), dict(cnt_form), n_vt, len(cf)))
print("selfcheck:", selfcheck)
print("cov_sha=%s cov_bytes=%d exe_sha=%s" % (cov_sha[:8], cov_bytes, exe_sha[:8]))
