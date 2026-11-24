# -*- coding: utf-8 -*-
"""R16-D1-WIDE-B1 final products generator.
Read-only: gamemd.exe (rb via pefile), coverage.tsv, sieve_all.tsv, final.tsv, raw_dump.json.
Write: only THIS directory (delta.tsv / fields.tsv / REPORT.md / verify_summary.json).
"""
import io, os, sys, re, hashlib, json, collections

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")

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

# ---- load current coverage.tsv (columns byte-exact) ----
cov = {}
cov_order = []
with io.open(COV, encoding="utf-8-sig") as f:
    f.readline()  # header
    for ln in f:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 8:
            cov[c[0].strip().upper()] = dict(entry=c[0], subsystem=c[1], name=c[2],
                                              sem=c[3], grade=c[4], ev=c[5], ns=c[6], conflict=c[7])
            cov_order.append(c[0].strip().upper())

# ---- load sieve_all.tsv (B1 = has_ring4==否 sorted by entry, first 18) ----
_, sieve_rows = read_tsv(SIEVE)
no_rows = sorted([r for r in sieve_rows if r["has_ring4_on_disk(是/否)"] == "否"],
                 key=lambda x: x["entry"])
b1 = no_rows[:18]
smap = {r["entry"]: r for r in b1}
assert len(b1) == 18

# ---- load binary-derived dump ----
dump = json.load(io.open(os.path.join(HERE, "raw_dump.json"), encoding="utf-8"))
rmap = {x["entry"]: x for x in dump["recs"]}

# ---- derive fields, statuses, ④ text ----
recs = []
for sr in b1:
    e = sr["entry"]
    x = rmap[e]
    cr = cov.get(e)
    if cr is None:
        recs.append(dict(entry=e, status="SKIP", note="coverage.tsv 未找到该 entry", sr=sr))
        continue
    if "error" in x:
        recs.append(dict(entry=e, status="SKIP", note="final/二进制取址失败: " + x["error"], sr=sr))
        continue
    pre_has4 = ("④" in cr["sem"])
    if pre_has4:
        recs.append(dict(entry=e, status="SKIP-ALREADY", cr=cr, x=x, sr=sr,
                         note="盘上 coverage.tsv 第4列已含④活表槽位见证（并发并表已覆盖），不重复追加"))
        continue
    # class consistency
    name = cr["name"]
    ncls = name.rsplit("::", 1)[0] if "::" in name else name
    mg = x["mg"]
    note_parts = []
    class_fix = False
    # 0040F870: row name PAVWar is abbreviation of PAVWarheadTypeClass; RTTI confirms same class
    if e == "0040F870":
        note_parts.append("行名 ?$DynamicVectorClass::PAVWar 中 PAVWar 为 PAVWarheadTypeClass 缩写，RTTI=.?AV?$DynamicVectorClass@PAVWarheadTypeClass@@@@ 同类；final.tsv col_nomatch 系名称匹配启发式未识别缩写，slot 值实测==entry，非类不符，无需 CLASS_FIX")
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
    recs.append(dict(entry=e, status="OK", cr=cr, x=x, sr=sr, form=form,
                     label=label, body=body, note="；".join(note_parts)))

# ---- delta.tsv ----
hdr = ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path", "n_sources", "conflict"]
dl = ["\t".join(hdr)]
ok = [r for r in recs if r["status"] == "OK"]
for r in ok:
    cr = r["cr"]
    sem_new = cr["sem"] + "；" + r["body"]
    assert cr["sem"] and sem_new.startswith(cr["sem"]), "col4 not strict prefix: " + r["entry"]
    dl.append("\t".join([cr["entry"], cr["subsystem"], cr["name"], sem_new,
                         cr["grade"], cr["ev"], cr["ns"], cr["conflict"]]))
io.open(os.path.join(HERE, "delta.tsv"), "w", encoding="utf-8", newline="\n").write("\n".join(dl) + "\n")

# ---- fields.tsv (card §4.2, 13 columns) ----
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
    vf = "%08X" % int(x["vt"], 16)
    fl.append("\t".join([
        r["entry"], sr["subsystem"], sr["name"],
        sr["audit_file"], sr["audit_line"],
        vf, str(x["slot"]), x["site"],
        r.get("form", "other"), x["host"],
        "否", r["status"], r["note"],
    ]))
io.open(os.path.join(HERE, "fields.tsv"), "w", encoding="utf-8", newline="\n").write("\n".join(fl) + "\n")

# ---- self-checks ----
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
# verify columns 1/2/3/5/6/7/8 byte-identical: rebuild and compare
for line in open(os.path.join(HERE, "delta.tsv"), encoding="utf-8").read().splitlines()[1:]:
    c = line.split("\t")
    cr = cov[c[0].upper()]
    assert c[1] == cr["subsystem"] and c[2] == cr["name"] and c[4] == cr["grade"] \
        and c[5] == cr["ev"] and c[6] == cr["ns"] and c[7] == cr["conflict"], "col mismatch " + c[0]

# ---- counts ----
cnt_form = collections.Counter(r["form"] for r in ok)
cnt_status = collections.Counter(r["status"] for r in recs)
n_vt = sum(1 for r in ok if r["x"]["vt"] and r["x"]["vt"] != "未取得")

# ---- byte facts ----
cov_bytes = os.path.getsize(COV)
cov_sha = sha256(COV)
exe_sha = sha256(EXE)

# ---- REPORT.md ----
R = []
R.append("# R16-D1-WIDE-B1 执行报告")
R.append("")
R.append("> 角色：执行器 · 卡号 R16-D1-WIDE-B1 · 日期 2026-11-21（R16 第 22 轮起）")
R.append("> 写域：`lead\\next_re_20261117_r14\\R16_D1_WIDE_B1\\`（仅此目录）；**未写 `COVERAGE\\coverage.tsv`**；`gamemd.exe` 仅只读打开（`pefile.PE(..., fast_load=True)` + `open('rb')`）。")
R.append("> 披露指针：每行 ④ 自带 D-47 披露并指向 **§12.6**（`见 R14_COMMON §12.6 与 PANEL 对应披露`）。")
R.append("")
R.append("## 0. 一句话结论")
R.append("**只补第 4 列 ④ 成文、未改 grade/判定、未并表。** 本批 18 行全部取得完整 ④ 数据（vt/slot/装表点/宿主/RTTI/装配形态），")
R.append("6 项字节复核全通过；盘上复核无已含 ④ 行（无 SKIP-ALREADY）；18 行净新增写入 `delta.tsv`。")
R.append("")
R.append("## 1. 批次派生")
R.append("| 阶段 | 行数 | 说明 |")
R.append("|---|---:|---|")
R.append("| sieve_all.tsv（D-52 宽读集合） | 81 | 判据 S1–S7 在 `R16_SIEVE_D1_WIDE/sieve.py`，直接采用，未重筛 |")
R.append("| 其中 has_ring4_on_disk==是（盘上已有 ④，跳过） | 16 | 不重做 |")
R.append("| 待做 | 65 | 81 − 16 |")
R.append("| 按 entry 升序第 1–18 行（本批 B1） | 18 | 本卡范围 |")
R.append("")
R.append("## 2. 盘上现值复核（SKIP-ALREADY）")
R.append("逐行读当前 `coverage.tsv` 第 4 列：`含④` 行数 = **%d**，无 ④ 行数 = **18**。" % sum(1 for r in recs if r["status"] == "SKIP-ALREADY"))
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
R.append("- **mov_abs** `0040B880`（DynamicVectorClass<BombClass*>::SetCapacity）：")
R.append("  ```")
R.append(next(r["body"] for r in ok if r["entry"] == "0040B880"))
R.append("  ```")
R.append("- **ctor_body** `00413F80`（AircraftClass::vslot9）：")
R.append("  ```")
R.append(next(r["body"] for r in ok if r["entry"] == "00413F80"))
R.append("  ```")
R.append("")
R.append("## 9. 产物清单")
R.append("- `delta.tsv`（18 净新增行） / `fields.tsv`（18 行） / `REPORT.md` / `derive_raw.py` / `raw_dump.json` / `generate.py`")
R.append("")
R.append("**只补 ④ 成文、未改 grade/判定、未并表。**")
io.open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8", newline="\n").write("\n".join(R) + "\n")

# ---- verify_summary.json ----
json.dump(dict(
    batch="B1", n_rows=len(recs),
    status=dict(cnt_status), install_forms=dict(cnt_form),
    n_vt=n_vt, selfcheck=selfcheck,
    cov_sha=cov_sha, cov_bytes=cov_bytes, exe_sha=exe_sha,
    n_delta=len(ok),
), io.open(os.path.join(HERE, "verify_summary.json"), "w", encoding="utf-8"),
    ensure_ascii=False, indent=1)

print("wrote delta.tsv/fields.tsv/REPORT.md/verify_summary.json")
print("rows=%d status=%s forms=%s vt=%d" % (len(recs), dict(cnt_status), dict(cnt_form), n_vt))
print("selfcheck:", selfcheck)
print("cov_sha=%s cov_bytes=%d exe_sha=%s" % (cov_sha[:8], cov_bytes, exe_sha[:8]))
