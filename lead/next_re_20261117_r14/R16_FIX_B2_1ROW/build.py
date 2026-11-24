# -*- coding: utf-8 -*-
"""R16-FIX-B2-1ROW product generator.

READ-ONLY inputs:  ra2youli/gamemd.exe, COVERAGE/coverage.tsv,
                   R16_D1_WIDE_B2/{delta,fields}.tsv.
WRITES ONLY this directory: vt16b0_sites.tsv / delta.tsv / fields.tsv /
                   selfcheck18.tsv / REPORT.md.
"""
import hashlib, io, os, re, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
OLD_DELTA = os.path.join(R14, "R16_D1_WIDE_B2", "delta.tsv")
OLD_FIELDS = os.path.join(R14, "R16_D1_WIDE_B2", "fields.tsv")
sys.path.insert(0, HERE)
from host_rule import Image, HostRule, IB, KNOWN_BASE_CTORS, BASE_CTOR, CD_CTOR

import capstone
DISC = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"
VTF = 0x7E16B0
ENTRY = "00473B10"
SLOT = 9
NEW_SITE, NEW_HOST = 0x473A9B, 0x473A80
NEW_INSN = "mov dword ptr [esi], 0x7e16b0"


def sha256(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def w(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def wb(path, data):
    with open(path, "wb") as fh:
        fh.write(data)


im = Image(EXE)
hr = HostRule(im)

# ---------------------------------------------------------------------------
# 1) Independent whole-image enumeration of every 0x7E16B0 imm32 memory store.
# ---------------------------------------------------------------------------
pat = (VTF & 0xFFFFFFFF).to_bytes(4, "little")
stores, regloads = [], []
for o in range(0, len(im.buf) - 4):
    if im.buf[o:o + 4] != pat:
        continue
    vend = IB + o + 4
    decoded = None
    for back in range(0, 17):
        s = IB + o - back
        if s < IB:
            continue
        r = list(im.md.disasm(bytes(im.buf[s - IB:s - IB + 24]), s, count=1))
        if not r:
            continue
        ins = r[0]
        if ins.address + ins.size != vend or ins.mnemonic != "mov" or len(ins.operands) != 2:
            continue
        a, b = ins.operands
        if a.type == capstone.x86.X86_OP_MEM and b.type == capstone.x86.X86_OP_IMM \
                and (b.imm & 0xFFFFFFFF) == VTF:
            decoded = (ins, s)
            break
    if decoded is None:
        prev = im.buf[o - 1] if o else None
        regloads.append(IB + o - 1)
        continue
    ins, s = decoded
    mo = ins.operands[0].mem
    base = im.md.reg_name(mo.base) if mo.base else ""
    stores.append(dict(site=s, ins=ins, base=base, disp=mo.disp & 0xFFFFFFFF))
stores.sort(key=lambda x: x["site"])
assert len(stores) == 185, len(stores)
stack_n = sum(1 for x in stores if x["base"] in ("esp", "ebp"))
assert stack_n == 178, stack_n

# Byte-derived host map for the 7 non-stack stores (see _explore.py/_explore2.py).
# 0x4019A6 is corrected from the audit's 0x401980: the preceding function ends
# with `ret 8` + nop at 0x40199F; 0x4019A0 is a fresh prologue that contains it.
HOSTS = {
    0x4019A6: 0x4019A0,
    0x473A12: 0x4739F0,
    0x473A4F: 0x473A30,
    0x473A9B: 0x473A80,
    0x535A76: 0x535A70,
    0x697A37: 0x697840,
    0x75951E: 0x759510,
}
HOST_EVIDENCE = {
    0x4019A6: "宿主4019A0:写vt后 call 0x431B80 + test byte[esp+8],1 + call 0x7C8B3D + ret 4 → CCFileClass 删除析构，非构造器",
    0x473A12: "宿主4739F0:mov esi,ecx; call 0x47AA30(CDFileClass基类ctor)→mov [esi],0x7E16B0→mov eax,esi;ret 4；写vt=RTTI .?AVCCFileClass@@ → 宿主类=CCFileClass",
    0x473A4F: "宿主473A30:mov esi,ecx; call 0x47AA30→mov [esi],0x7E16B0→mov eax,esi;ret 4；宿主类=CCFileClass",
    0x473A9B: "宿主473A80:push esi;mov esi,ecx;call 0x47AA30;...;mov [esi],0x7E16B0;mov eax,esi;pop esi;ret；宿主类=CCFileClass；最干净44B",
    0x535A76: "宿主535A70:mov esi,ecx;lea ecx,[esi+0x58];写vt后 call 0x43AE50→mov [esi],0x7E1668→call 0x431B80 → 析构序列，无返回this",
    0x697A37: "目标[edi]但宿主仅 mov esi,ecx（edi非ecx载体），宿主内有 call 0x7C8B3D → 非this/析构",
    0x75951E: "宿主759510:mov esi,ecx 后 add esi,4，写[esi]实为[this+4]；写后 call 0x431B80 → 非[this+0]/析构",
}
NOTE_NONSTACK = {
    0x4019A6: "删除析构(scalar deleting dtor)；G3/G4 不过",
    0x473A12: "真构造器；G1-G5 全通（audit 列 this 目标之一）",
    0x473A4F: "真构造器；G1-G5 全通（audit 列 this 目标之一）",
    0x473A9B: "真构造器；G1-G5 全通；审计推荐，选为本行装表点",
    0x535A76: "析构序列；G3/G4/G5 不过（audit 列 this 目标之一）",
    0x697A37: "非this载体(edi)；G2/G3/G4/G5 不过",
    0x75951E: "this+4 内嵌对象+析构；G2/G3/G4/G5 不过",
}

for x in stores:
    s = x["site"]
    x["host"] = HOSTS.get(s)
    if x["host"] is not None:
        x["rule"] = hr.classify(s, VTF, x["host"])
        this_ok = x["rule"]["this_from_ecx"] == "是"
    else:
        x["rule"] = None
        this_ok = False
    if x["base"] in ("esp", "ebp"):
        x["kind"] = "stack"
    elif x["base"] == "":
        x["kind"] = "static"
    elif x["disp"] == 0 and this_ok:
        x["kind"] = "this"
    else:
        x["kind"] = "other"
    x["pass"] = bool(x["rule"] and x["rule"]["host_is_canonical_ctor"] == "是")

kinds = {k: sum(1 for x in stores if x["kind"] == k) for k in ("this", "stack", "static", "other")}
this_sites = [x for x in stores if x["kind"] == "this"]
assert set("%08X" % x["site"] for x in this_sites) == {
    "004019A6", "00473A12", "00473A4F", "00473A9B", "00535A76"}
pass_sites = [x for x in this_sites if x["pass"]]
assert set("%08X" % x["site"] for x in pass_sites) == {"00473A12", "00473A4F", "00473A9B"}
assert any(x["site"] == NEW_SITE for x in pass_sites)
rr_new = hr.classify(NEW_SITE, VTF, NEW_HOST)
assert rr_new["host_is_canonical_ctor"] == "是"

# ---------------------------------------------------------------------------
# 2) vt16b0_sites.tsv -- all 185 stores
# ---------------------------------------------------------------------------
def gate_evidence(r):
    return ("G1非栈=%s;G2this=%s;G3非析构=%s(后序call431B80=%s,sdd=%s);G4基类ctor前序=%s(%s);G5返回this=%s"
            % ("否" if r["target_is_stack"] == "是" or r["target_is_abs"] == "是" else "是",
               r["this_from_ecx"],
               "否" if r["host_is_dtor"] == "是" else "是",
               r["dtor_call_after"], r["sdd_sig"], r["base_ctor_before"],
               r["ctor_call_targets"] or "-", r["returns_this"]))

lines = ["site\tinsn_bytes\ttarget_kind(this|stack|static|other)\tfunc_start\tpass_G1_G5(是/否)\thost_class_evidence\tnote"]
for x in stores:
    r = x["rule"]
    ev = HOST_EVIDENCE.get(x["site"], "栈临时对象/非this目标；G1即淘汰，未进入宿主类判定" if x["kind"] == "stack" else "未取得")
    note = NOTE_NONSTACK.get(x["site"],
        "栈临时对象 [esp/ebp+...]，写后另有 thiscall 使用；非 this，原始 derive_raw.py:160 es[0] 最低地址命中错误即取此类点"
        if x["kind"] == "stack" else "")
    lines.append("\t".join([
        "%08X" % x["site"], x["ins"].bytes.hex(), x["kind"],
        ("%08X" % x["host"]) if x["host"] is not None else "未取得",
        "是" if x["pass"] else "否", ev, note,
    ]))
w(os.path.join(HERE, "vt16b0_sites.tsv"), "\n".join(lines) + "\n")

# ---------------------------------------------------------------------------
# 3) read old B2 rows + coverage bytes
# ---------------------------------------------------------------------------
ofl = io.open(OLD_FIELDS, encoding="utf-8-sig").read().splitlines()
fhdr = ofl[0].split("\t")
old_rows = [dict(zip(fhdr, ln.split("\t"))) for ln in ofl[1:] if ln.strip()]
assert len(old_rows) == 18
old_map = {r["entry"]: r for r in old_rows}
old_row = old_map[ENTRY]
assert old_row["vt"] == "007E16B0" and old_row["slot"] == "9"
assert old_row["install_site"] == "004014AC" and old_row["install_host"] == "004011C0"

cov_lines = open(COV, "rb").read().split(b"\n")
cov_by_entry = {}
for bl in cov_lines:
    c = bl.rstrip(b"\r").split(b"\t")
    if len(c) >= 8:
        cov_by_entry[c[0].decode("ascii", "replace").strip().upper()] = c
ce = cov_by_entry[ENTRY]
assert ce[0].decode("ascii").strip().upper() == ENTRY
assert b"\xe2\x91\xa4" not in ce[3], "coverage.tsv already merged ④ -- STOP"

old_delta_lines = io.open(OLD_DELTA, encoding="utf-8").read().splitlines()
old_delta_row = next(ln.split("\t") for ln in old_delta_lines if ln.split("\t")[0] == ENTRY)
assert len(old_delta_row) == 8
assert old_delta_row[3].startswith(ce[3].decode("utf-8") + "；"), "old delta col4 prefix mismatch"
for i in (1, 2, 4, 5, 6, 7):
    assert old_delta_row[i].encode("utf-8") == ce[i], (i, old_delta_row[i], ce[i])

# ---------------------------------------------------------------------------
# 4) selfcheck18.tsv -- form-aware verdict using the same G1-G5 rule
# ---------------------------------------------------------------------------
sc = ["entry\tdeclared_form\thost_is_ctor(是/否)\tinstall_target_is_stack(是/否)\thost_is_dtor(是/否)\tverdict(OK|SUSPECT)\tnote"]
suspect = []
for r in old_rows:
    e = r["entry"]
    site = int(r["install_site"], 16)
    host = int(r["install_host"], 16)
    vt = int(r["vt"], 16)
    form = r["install_form(ctor_body|mov_abs|reg|other)"]
    rr = hr.classify(site, vt, host)
    if form == "mov_abs":
        ok = rr["target_is_abs"] == "是" and rr["host_is_dtor"] == "否"
    elif form == "ctor_body":
        ok = rr["host_is_ctor"] == "是"
    else:
        ok = False
    verdict = "OK" if ok else "SUSPECT"
    if verdict == "SUSPECT":
        suspect.append(e)
    note = ("实测指令=%s;操作数=%s;失败门=%s;G4基类ctor前序=%s(%s);G5返回this=%s;严格canonical=%s"
            % (rr["ins"], rr["target"], rr["failed_gates"], rr["base_ctor_before"],
               rr["ctor_call_targets"] or "-", rr["returns_this"], rr["host_is_canonical_ctor"]))
    sc.append("\t".join([e, form, rr["host_is_ctor"], rr["target_is_stack"],
                         rr["host_is_dtor"], verdict, note]))
w(os.path.join(HERE, "selfcheck18.tsv"), "\n".join(sc) + "\n")
assert suspect == [ENTRY], suspect

# ---------------------------------------------------------------------------
# 5) delta.tsv -- only the one rewritten row, byte-exact cols 1/2/3/5/6/7/8
# ---------------------------------------------------------------------------
old4 = old_delta_row[3]
m = re.search(r"COL=([0-9A-F]{8}) offset=(\d+)，RTTI=([0-9A-F]{8})→(\S+?)；", old4)
assert m, old4
col_s, off_s, td_s, mg = m.group(1), m.group(2), m.group(3), m.group(4)
label = "CCFileClass::slot%d" % SLOT
body = ("④ 活表槽位见证：%s（vt=%s，槽 %d 值=%s，COL=%s offset=%s，RTTI=%s→%s；"
        "装表点 %08X 位于 %08X 体内，装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 %s），entry 体外） " % (
            label, "007E16B0", SLOT, ENTRY, col_s, off_s, td_s, mg,
            NEW_SITE, NEW_HOST, NEW_INSN))
body += ("④升级句：%s（④ 表属类与行名类一致，均为 CCFileClass；该槽即其 vt=007E16B0 表 slot%d，无归属歧义）" % (label, SLOT))
body += DISC
sem_new = ce[3] + "；".encode("utf-8") + body.encode("utf-8")
newc = [ce[0], ce[1], ce[2], sem_new, ce[4], ce[5], ce[6], ce[7]]
header_line = open(OLD_DELTA, "rb").read().split(b"\n")[0]
wb(os.path.join(HERE, "delta.tsv"), b"\n".join([header_line, b"\t".join(newc)]) + b"\n")

# ---------------------------------------------------------------------------
# 6) fields.tsv -- new/old site/host/form comparison
# ---------------------------------------------------------------------------
rr_old = hr.classify(int(old_row["install_site"], 16), VTF, int(old_row["install_host"], 16))
assert rr_old["verdict"] == "SUSPECT" and rr_old["target_is_stack"] == "是"
fh = ["entry", "subsystem", "name", "old_install_site", "old_form", "old_host",
      "new_install_site", "new_form", "new_host", "form_evidence", "status(OK|SKIP)", "note"]
ev_new = ("实测 %s；G1非栈=%s G2this=%s G3非析构=%s G4基类ctor前序=%s(%s) G5返回this=%s；严格canonical=%s"
          % (NEW_INSN,
             "否" if rr_new["target_is_stack"] == "是" or rr_new["target_is_abs"] == "是" else "是",
             rr_new["this_from_ecx"],
             "是" if rr_new["host_is_dtor"] == "否" else "否",
             rr_new["base_ctor_before"], rr_new["ctor_call_targets"] or "-",
             rr_new["returns_this"], rr_new["host_is_canonical_ctor"]))
note = ("替换 R16_D1_WIDE_B2/delta.tsv 的 ④：旧装表点 004014AC 位于 004011C0 体内，实测 mov dword ptr [esp + 0x20], 0x7e16b0"
        "（栈临时对象，非 this；004014C0 lea ecx,[esp+0x20] 证实作 thiscall 实参，004014CC call 0x431B80 基类析构），"
        "旧装配方式标 ctor_body 错误；新装表点取 CCFileClass 真构造器 00473A80 体内 00473A9B"
        "（mov esi,ecx;call 0x47AA30(CDFileClass基类ctor);mov [esi],0x7e16b0;mov eax,esi;ret）。"
        "同 vt 5 个 this 目标中 3 个过 G1-G5（00473A12/00473A4F/00473A9B），按审计推荐取 00473A9B/00473A80（44B 最干净）。"
        "最小 diff：装表点/宿主/实测指令三处；字节事实(vt/slot/COL/RTTI/grade)未变。")
fl = ["\t".join(fh), "\t".join([
    ENTRY, old_row["subsystem"], old_row["name"],
    old_row["install_site"], old_row["install_form(ctor_body|mov_abs|reg|other)"], old_row["install_host"],
    "%08X" % NEW_SITE, "ctor_body", "%08X" % NEW_HOST, ev_new, "OK", note])]
w(os.path.join(HERE, "fields.tsv"), "\n".join(fl) + "\n")

# ---------------------------------------------------------------------------
# 7) REPORT.md
# ---------------------------------------------------------------------------
cov_sha, exe_sha = sha256(COV), sha256(EXE)
assert cov_sha == "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1", cov_sha
assert exe_sha == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476", exe_sha
R = []
A = R.append
A("# R16-FIX-B2-1ROW 执行报告")
A("")
A("> 角色：执行器（`work/cn:hy4flash-free`）· 卡号 R16-FIX-B2-1ROW · 日期 2026-11-21（R16 第 25 轮）· **1 行**")
A("> 写域：`lead\\next_re_20261117_r14\\R16_FIX_B2_1ROW\\`（仅此目录）；**未写 `COVERAGE\\coverage.tsv`**；`gamemd.exe` 全程只读打开（`open('rb')` + `pefile.PE(..., fast_load=True)`）。")
A("> `R16_D1_WIDE_B2\\` 全程只读；`R16_FIX_B1_2ROWS\\host_rule.py` 只读复用其 G1-G5 结构。")
A("")
A("## 0. 一句话结论")
A("**只重写这 1 行 ④、未改 grade/判定、未并表。** 把 `00473B10` 的装表点从栈临时对象 `004014AC`（宿主 `004011C0`）"
  "改到 CCFileClass 真构造器装表点 `00473A9B`（宿主 `00473A80`）；可执行规则 G1-G5 已落地并复查 B2 全 18 行，"
  "确认除本行外无其他 SUSPECT。")
A("")
A("## 1. 0x7E16B0 写入点枚举与分类")
A("| 项 | 值 |")
A("|---|---:|")
A("| 立即数字节 `b0 16 7e 00` 原始出现 | %d |" % (len(stores) + len(regloads)))
A("| 其中 `mov reg,imm32`（寄存器装载，非写内存） | %d |" % len(regloads))
A("| `mov [mem],0x7E16B0` 内存写入总数 | %d |" % len(stores))
for k in ("this", "stack", "static", "other"):
    A("| ├ target_kind=%s | %d |" % (k, kinds[k]))
A("")
A("枚举方法：全镜像按立即数字节 `b0 16 7e 00` 扫描，capstone 从候选起点解码并要求 `ins.address+ins.size` 恰在 imm 尾，"
  "与审计 `vptr_stores.tsv` 的 185 处一致。分类口径（§2.1）："
  "`this`=`mov [reg+0],vt` 且宿主 prologue `mov reg,ecx`、写前 reg 未被改写；"
  "`stack`=base∈{esp,ebp}；`static`=绝对地址；`other`=其余（edi 非 ecx 载体 / this+4 内嵌对象）。")
A("")
A("## 2. 可执行宿主身份校验规则（G0-G5）")
A("```")
A("G0 site 指令须解码为 mov [base+disp], vt（imm32==vt，end 恰在 imm 尾）")
A("G1 非栈：base ∉ {esp,ebp} 且非绝对地址                       # 排除栈临时对象")
A("G2 this 对象：base∈GPR、disp==0、宿主 prologue 内 mov base,ecx 且写前 base 未被改写")
A("G3 非析构：宿主内 site 之后无 call/jmp 到基类析构 0x431B80；")
A("           且无 test byte [esp+X],1 + call 0x7C8B3D + ret imm 签名")
A("G4 基类构造前序：[host,site) 内有 call 到已知基类 ctor {0x431B20, 0x47AA30}")
A("           或到自身「从 ecx 装 vptr 并返回该寄存器」的 ctor_like 目标   # call <alloc>")
A("G5 返回 this：终止 ret 前 6 条内有 mov eax,base")
A("行级判定=核心 G1∧G2∧G3（与 B1 同口径；G4/G5 仅用于 canonical 选点，状态逐行记入 note）")
A("canonical=G1∧G2∧G3∧G4∧G5")
A("```")
A("")
A("**G4 适配说明**：卡面示例 `0x431B20` 是 Abstract/FileClass 基类 ctor；本行宿主 `00473A80` 的直接基类是 CDFileClass，"
  "其 ctor 为 `0x47AA30`（B1 已证：`call 0x431B20 → mov [esi],0x7E1668 → mov eax,esi;ret`）。"
  "若把 G4 硬编码为仅 `0x431B20`，会错误淘汰审计推荐的 `00473A80`。故 G4 泛化为「已知基类 ctor 集合 ∪ ctor_like 目标」。")
A("")
A("## 3. 5 个 `this` 目标逐点结论")
A("| site | host | G1 | G2 | G3 | G4 | G5 | canonical | 结论 |")
A("|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|")
for sx in this_sites:
    r = sx["rule"]
    def mk(v): return "✓" if v == "是" else "✗"
    g1 = "否" if r["target_is_stack"] == "是" or r["target_is_abs"] == "是" else "是"
    g2, g3, g4, g5 = r["this_from_ecx"], ("否" if r["host_is_dtor"] == "是" else "是"), r["base_ctor_before"], r["returns_this"]
    concl = "真构造器（候选）" if r["host_is_canonical_ctor"] == "是" else ("删除析构/析构序列，非构造器" if r["host_is_dtor"] == "是" else "非构造器")
    A("| `%08X` | `%08X` | %s | %s | %s | %s | %s | %s | %s |" % (
        sx["site"], sx["host"], mk(g1), mk(g2), mk(g3), mk(g4), mk(g5),
        "✓" if r["host_is_canonical_ctor"] == "是" else "✗", concl))
A("")
A("计数：**5 个 `this` 目标中 %d 个过 G1-G5**（`00473A12`/`00473A4F`/`00473A9B`）；"
  "`004019A6`（宿主 `004019A0`，字节证据推翻审计表的 `00401980`）与 `00535A76` 均为析构序列。"
  "另 2 个非栈 reg+0 写入点 `00697A37`(edi)/`0075951E`(this+4) 因 G2 不过归 `other`，"
  "故 7 个非栈 reg+0 中恰 5 个是 `this` 目标，与卡面一致。" % len(pass_sites))
A("")
A("选点：**`site=00473A9B` / `host=00473A80`**（审计推荐）。三者皆过 G1-G5 且宿主类均为 CCFileClass"
  "（同写 `0x7E16B0`、同调基类 ctor `0x47AA30`）；取 44B 最干净的 `00473A80`"
  "（`push esi; mov esi,ecx; call 0x47AA30; …; mov [esi],0x7e16b0; mov eax,esi; pop esi; ret`）。")
A("")
A("## 4. 新旧对照")
A("| entry | 旧装表点 | 旧宿主 | 旧实测指令 | 旧形态 | 新装表点 | 新宿主 | 新实测指令 | 新形态 |")
A("|---|---|---|---|---|---|---|---|---|")
A("| %s | %s | %s | `mov dword ptr [esp + 0x20], 0x7e16b0` | ctor_body(**错**) | `%08X` | `%08X` | `%s` | ctor_body |"
  % (ENTRY, old_row["install_site"], old_row["install_host"], NEW_SITE, NEW_HOST, NEW_INSN))
A("")
A("旧点致命证据（只读回读 `gamemd.exe`）：`004014AC mov [esp+0x20],0x7e16b0` 写栈临时；"
  "`004014C0 lea ecx,[esp+0x20]` 把该临时对象当 thiscall 实参；`004014CC call 0x431B80` 调基类析构。"
  "宿主 `004011C0` 是 1729 条指令的无关函数。根因：`derive_raw.py:160 site=es[0]` 最低地址命中"
  "（185 个点中最低地址恰是栈临时），`generate.py:91 elif op: form='ctor_body'` 无 this/宿主校验。")
A("")
A("## 5. 18 行 G1-G5 复查结果（`selfcheck18.tsv`）")
A("| 项 | 值 |")
A("|---|---:|")
A("| 复查行数 | 18 |")
A("| SUSPECT 行数 | %d |" % len(suspect))
A("| SUSPECT entry | %s |" % ("、".join("`%s`" % e for e in suspect) if suspect else "无"))
A("")
A("逐行点名：")
for ln in sc[1:]:
    c = ln.split("\t")
    A("- `%s`：declared=%s host_is_ctor=%s target_is_stack=%s host_is_dtor=%s → **%s**"
      % (c[0], c[1], c[2], c[3], c[4], c[5]))
A("")
A("结论：审计称只有 `00473B10` 一行 FAIL，独立复算一致：除本行（已重写）外其余 17 行无同类可疑"
  "（13 行 ctor_body 宿主核心规则全通、4 行 mov_abs 写静态 global；本行旧 site 为 SUSPECT，新 site 已过 G1-G5）。")
A("")
A("## 6. 哈希与只读证明")
A("| 项 | 值 |")
A("|---|---|")
A("| coverage.tsv 字节数（未改） | %d |" % os.path.getsize(COV))
A("| coverage.tsv sha256（未改） | `%s` |" % cov_sha)
A("| gamemd.exe sha256（未改，只读打开） | `%s` |" % exe_sha)
A("| B2 是否已并表 | **否**（coverage.tsv `00473B10` 第 4 列无 ④，哈希与上版一致） |")
A("")
A("## 7. 样例 ④（修正后的 `00473B10`）")
A("```")
A(io.open(os.path.join(HERE, "delta.tsv"), encoding="utf-8").read().splitlines()[1].split("\t")[3])
A("```")
A("")
A("## 8. 产物清单")
A("- `vt16b0_sites.tsv`（185 行全部写入点） / `delta.tsv`（仅 1 行，8 列） / `fields.tsv`（1 行） / "
  "`selfcheck18.tsv`（18 行） / `REPORT.md` / `host_rule.py`（可执行规则） / `_test_rule.py`（规则自测）")
A("")
A("**只重写这 1 行 ④、未改 grade/判定、未并表。**")
w(os.path.join(HERE, "REPORT.md"), "\n".join(R) + "\n")

print("OK: vt16b0_sites=%d (this=%d stack=%d static=%d other=%d) pass_this=%d delta=1 fields=1 selfcheck18=18 suspect=%s"
      % (len(stores), kinds["this"], kinds["stack"], kinds["static"], kinds["other"],
         len(pass_sites), suspect))
