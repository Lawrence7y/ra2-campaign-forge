# -*- coding: utf-8 -*-
"""R16-FIX-B1-2ROWS product generator.

Read-only:  ra2youli/gamemd.exe, R16_D1_WIDE_B1/{delta,fields}.tsv,
            COVERAGE/coverage.tsv, audit starts.json / vptr_stores.tsv.
Writes ONLY this directory: vt1668_sites.tsv / delta.tsv / fields.tsv /
            selfcheck18.tsv / REPORT.md (+ rule/test scripts already present).
"""
import io, os, sys, hashlib, json, re
import capstone
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
OLD_DELTA = os.path.join(R14, "R16_D1_WIDE_B1", "delta.tsv")
OLD_FIELDS = os.path.join(R14, "R16_D1_WIDE_B1", "fields.tsv")
STARTS = os.path.join(R14, "R16_AUDIT_D1_WIDE_B1", "starts.json")
VPTR = os.path.join(R14, "R16_AUDIT_D1_WIDE_B1", "vptr_stores.tsv")
sys.path.insert(0, HERE)
from host_rule import Image, HostRule, IB, BASE_CTOR, BASE_DTOR, OP_DELETE

DISC = "（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）"
VTF = 0x7E1668

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

def w(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)

im = Image(EXE)
hr = HostRule(im, STARTS)

# ---------------------------------------------------------------------------
# 1) Independent whole-image enumeration of every 0x7E1668 imm32 memory store.
#    Method: raw-byte search for the imm32 then capstone decode with an exact
#    end-address check; cross-checked against the audit's linear-sweep list.
# ---------------------------------------------------------------------------
pat = (VTF & 0xFFFFFFFF).to_bytes(4, "little")
sites = []           # real mov [mem],imm stores
regload = []         # mov reg,imm (NOT stores) - counted for transparency
for o in range(0, len(im.buf) - 4):
    if im.buf[o:o + 4] != pat:
        continue
    va_end = IB + o + 4
    decoded = None
    for back in range(0, 17):
        s = IB + o - back
        if s < IB:
            continue
        r = list(im.md.disasm(bytes(im.buf[s - IB:s - IB + 24]), s, count=1))
        if not r:
            continue
        ins = r[0]
        if ins.address + ins.size != va_end or ins.mnemonic != "mov" or len(ins.operands) != 2:
            continue
        a, b = ins.operands
        if a.type == capstone.x86.X86_OP_MEM and b.type == capstone.x86.X86_OP_IMM \
                and (b.imm & 0xFFFFFFFF) == VTF:
            decoded = (ins, s)
            break
    if decoded is None:
        # classify the non-store encodings: B8+r (mov reg,imm32)
        prev = im.buf[o - 1] if o > 0 else None
        regload.append((IB + o - 1, "mov reg,0x7e1668" if prev in (0xB8,0xB9,0xBA,0xBB,0xBC,0xBD,0xBE,0xBF) else "other"))
        continue
    ins, s = decoded
    mo = ins.operands[0].mem
    base = im.md.reg_name(mo.base) if mo.base else ""
    sites.append(dict(site=s, ins=ins, base=base, disp=mo.disp & 0xFFFFFFFF,
                      sec=im.sec_of.get(s - IB, "?")))

sites.sort(key=lambda x: x["site"])
stack_sites = [x for x in sites if x["base"] in ("esp", "ebp")]
nons = [x for x in sites if x["base"] not in ("esp", "ebp")]
assert len(stack_sites) == 191, len(stack_sites)   # matches audit
assert len(nons) == 9, len(nons)                    # audit's 8 + 535A60 thunk

# host map for the 9 non-stack sites (host derived by hr.enclosing; 535A60 is
# its own call-target function start)
HOSTS = {}
for x in nons:
    x["host"] = hr.enclosing(x["site"])
    if x["site"] == 0x535A60:
        x["host"] = 0x535A60     # genuine call-target thunk, linear-sweep missed it

# classify each with the executable rule
for x in nons:
    x["rule"] = hr.classify(x["site"], VTF, x["host"])

# ---------------------------------------------------------------------------
# 2) vt1668_sites.tsv
# ---------------------------------------------------------------------------
def evidence(r):
    parts = []
    parts.append("G1非栈=%s" % "否" if r["target_is_stack"] == "是" else "G1非栈=是")
    parts.append("G2this=%s" % r["this_from_ecx"])
    parts.append("G3非析构=%s(析构后序call=%s,sdd=%s)" % ("否" if r["host_is_dtor"] == "是" else "是", r["dtor_call_after"], r["sdd_sig"]))
    parts.append("G4基类构造前序call431B20=%s" % r["base_ctor_before"])
    parts.append("G5返回this=%s" % r["returns_this"])
    return ";".join(parts)

NOTE_MAP = {
    0x401953: "删除析构器(CDFileClass scalar deleting dtor;test [esp+8],1+call 7C8B3D+ret4)",
    0x4019BA: "删除析构器(CDFileClass 完整删除析构;同401950同构)",
    0x47A9E3: "真构造器(默认/带参ctor;宿主47A9D0)",
    0x47AA10: "真构造器(带参ctor;宿主47AA00)",
    0x47AA3C: "真构造器(默认ctor;宿主47AA30;严格规则全通,选为本批装表点)",
    0x535A60: "删除析构器thunk(mov [ecx],vt;jmp 431B80);8处call引用证实为真函数起点;线性扫漏检",
    0x535A8A: "析构序列(宿主535A70;写vt后call 431B80基类析构;无返回this)",
    0x697A47: "析构序列(宿主697840大对象析构;edi非ecx传入;写vt后call 431B80)",
    0x759532: "析构序列(宿主759510;写vt后call 431B80基类析构;无返回this)",
}
lines = ["site\tinsn_bytes\toperand\tfunc_start\tis_ctor(是/否)\tctor_evidence\tnote"]
for x in nons:
    r = x["rule"]
    lines.append("\t".join([
        "%08X" % x["site"], x["ins"].bytes.hex(),
        r["target"], "%08X" % x["host"],
        r["host_is_ctor"], evidence(r), NOTE_MAP[x["site"]],
    ]))
w(os.path.join(HERE, "vt1668_sites.tsv"), "\n".join(lines) + "\n")

# ---------------------------------------------------------------------------
# 3) choose canonical CDFileClass ctor site
# ---------------------------------------------------------------------------
canon = [x for x in nons if x["rule"]["host_is_canonical_ctor"] == "是"]
assert len(canon) == 3, [("%08X" % x["site"]) for x in canon]
NEW_SITE, NEW_HOST = 0x47AA3C, 0x47AA30
NEW_INSN = "mov dword ptr [esi], 0x7e1668"
assert any(x["site"] == NEW_SITE for x in canon)

# ---------------------------------------------------------------------------
# 4) read OLD 18 rows (fields.tsv for structured data) + coverage bytes
# ---------------------------------------------------------------------------
ofl = io.open(OLD_FIELDS, encoding="utf-8-sig").read().splitlines()
fhdr = ofl[0].split("\t")
old_rows = [dict(zip(fhdr, ln.split("\t"))) for ln in ofl[1:] if ln.strip()]
assert len(old_rows) == 18

# coverage.tsv byte-exact columns for the 2 target entries (disk is NOT merged)
cov_bytes = open(COV, "rb").read()
cov_lines = cov_bytes.split(b"\n")
cov_by_entry = {}
for bl in cov_lines:
    c = bl.rstrip(b"\r").split(b"\t")
    if len(c) >= 8:
        cov_by_entry[c[0].decode("ascii", "replace").strip().upper()] = c

TARGETS = {"004322A0": 9, "004324B0": 10}
old_map = {r["entry"]: r for r in old_rows}

# ---------------------------------------------------------------------------
# 5) selfcheck18.tsv -- form-aware verdict applying the executable rule
# ---------------------------------------------------------------------------
sc = ["entry\tdeclared_form\thost_is_ctor(是/否)\tinstall_target_is_stack(是/否)\thost_is_dtor(是/否)\tverdict(OK|SUSPECT)\tnote"]
suspect_rows = []
for r in old_rows:
    e = r["entry"]
    site = int(r["install_site"], 16)
    host = int(r["install_host"], 16)
    vt = int(r["vt"], 16)
    form = r["install_form(ctor_body|mov_abs|reg|other)"]
    rr = hr.classify(site, vt, host)
    # form-aware verdict
    if form == "mov_abs":
        ok = (rr["target_is_abs"] == "是" and rr["host_is_dtor"] == "否")
    elif form == "ctor_body":
        ok = (rr["host_is_ctor"] == "是")
    else:
        ok = False
    verdict = "OK" if ok else "SUSPECT"
    if verdict == "SUSPECT":
        suspect_rows.append(e)
    note = ("实测指令=%s;操作数=%s;失败门=%s;G4基类构造前序=%s;G5返回this=%s;严格canonical=%s"
            % (rr["ins"], rr["target"], rr["failed_gates"], rr["base_ctor_before"],
               rr["returns_this"], rr["host_is_canonical_ctor"]))
    sc.append("\t".join([e, form, rr["host_is_ctor"], rr["target_is_stack"],
                          rr["host_is_dtor"], verdict, note]))
w(os.path.join(HERE, "selfcheck18.tsv"), "\n".join(sc) + "\n")
assert suspect_rows == ["004322A0", "004324B0"], suspect_rows

# ---------------------------------------------------------------------------
# 6) new delta.tsv (2 rows) -- byte-exact columns 1/2/3/5/6/7/8 + original col4
# ---------------------------------------------------------------------------
def col4_prefix(entry):
    c = cov_by_entry[entry]
    assert c[0].decode("ascii").strip().upper() == entry
    return c  # list of bytes for all 8 columns

hdr_line = open(OLD_DELTA, "rb").read().split(b"\n")[0]
dl = [hdr_line]
NEW_FORM_TXT = ("装配方式=ctor_body（构造器体内 mov [reg], vt；实测指令 %s）" % NEW_INSN)
for e, slot in sorted(TARGETS.items()):
    c = col4_prefix(e)
    sem = c[3]                      # byte-exact original col4 from disk
    assert b"\xe2\x91\xa4" not in sem, (e, sem)   # no ④ on disk => not merged
    old = old_map[e]
    vt = old["vt"]
    # pull COL/offset/TD/mangled from the OLD ④ text (byte facts unchanged)
    old4 = io.open(OLD_DELTA, encoding="utf-8").read().splitlines()
    oldrow = next(ln.split("\t") for ln in old4 if ln.split("\t")[0] == e)
    m = re.search(r"COL=([0-9A-F]{8}) offset=(\d+)，RTTI=([0-9A-F]{8})→(\S+?)；", oldrow[3])
    assert m, oldrow[3]
    col_s, off_s, td_s, mg = m.group(1), m.group(2), m.group(3), m.group(4)
    label = "CDFileClass::slot%d" % slot
    body = ("④ 活表槽位见证：%s（vt=%s，槽 %d 值=%s，COL=%s offset=%s，RTTI=%s→%s；"
            "装表点 %08X 位于 %08X 体内，%s，entry 体外） " % (
                label, vt, slot, e, col_s, off_s, td_s, mg,
                NEW_SITE, NEW_HOST, NEW_FORM_TXT))
    body += ("④升级句：%s（④ 表属类与行名类一致，均为 CDFileClass；该槽即其 vt=%s 表 slot%d，无归属歧义）" % (
                label, vt, slot))
    body += DISC
    sem_new = sem + "；".encode("utf-8") + body.encode("utf-8")
    newc = [c[0], c[1], c[2], sem_new, c[4], c[5], c[6], c[7]]
    dl.append(b"\t".join(newc))
with open(os.path.join(HERE, "delta.tsv"), "wb") as f:
    f.write(b"\n".join(dl) + b"\n")

# ---------------------------------------------------------------------------
# 7) fields.tsv
# ---------------------------------------------------------------------------
fh = ["entry", "subsystem", "name", "old_install_site", "old_form", "old_host",
      "new_install_site", "new_form", "new_host", "form_evidence", "status(OK|SKIP)", "note"]
fl = ["\t".join(fh)]
for e, slot in sorted(TARGETS.items()):
    old = old_map[e]
    rr_new = hr.classify(NEW_SITE, VTF, NEW_HOST)
    rr_old = hr.classify(int(old["install_site"], 16), int(old["vt"], 16), int(old["install_host"], 16))
    g1_new = "是" if rr_new["target_is_stack"] == "否" else "否"
    evidence_new = ("实测 %s；G1非栈=%s G2this=%s G3非析构=%s G4call431B20=%s G5返回this=%s；严格canonical=%s"
                    % (NEW_INSN, g1_new, rr_new["this_from_ecx"],
                       "是" if rr_new["host_is_dtor"] == "否" else "否",
                       rr_new["base_ctor_before"], rr_new["returns_this"],
                       rr_new["host_is_canonical_ctor"]))
    note = ("替换上一版 R16_D1_WIDE_B1/delta.tsv 的 ④：旧装表点 %s 位于 %s 体内，"
            "实测 mov dword ptr [esp + 0x20], 0x7e1668（栈临时对象，非 this；与 004019A0 删除析构体同构，"
            "写 vt 时对象正在析构），旧装配方式标 ctor_body 错误；"
            "新装表点取 CDFileClass 真构造器 47AA30 体内 47AA3C（call 431B20→mov [esi],vt→mov eax,esi;ret）。"
            "最小 diff：装表点 004014C4→0047AA3C；宿主 004011C0→0047AA30；实测指令 "
            "[esp + 0x20]→[esi]；装配方式判定证据由「操作数形态」改为「宿主身份规则全通」。"
            "字节事实(vt/slot/COL/RTTI/grade)未变。"
            % (old["install_site"], old["install_host"]))
    fl.append("\t".join([e, old["subsystem"], old["name"],
                         old["install_site"], old["install_form(ctor_body|mov_abs|reg|other)"],
                         old["install_host"], "%08X" % NEW_SITE, "ctor_body", "%08X" % NEW_HOST,
                         evidence_new, "OK", note]))
w(os.path.join(HERE, "fields.tsv"), "\n".join(fl) + "\n")

# ---------------------------------------------------------------------------
# 8) REPORT.md
# ---------------------------------------------------------------------------
cov_sha = sha256(COV); exe_sha = sha256(EXE)
cov_bytes_n = os.path.getsize(COV)
n_ctor = sum(1 for x in nons if x["rule"]["host_is_ctor"] == "是")
n_canon = len(canon)
R = []
R.append("# R16-FIX-B1-2ROWS 执行报告")
R.append("")
R.append("> 角色：执行器（`work/cn:hy4flash-free`）· 卡号 R16-FIX-B1-2ROWS · 日期 2026-11-21（R16 第 24 轮）· 2 行")
R.append("> 写域：`lead\\next_re_20261117_r14\\R16_FIX_B1_2ROWS\\`（仅此目录）；**未写 `COVERAGE\\coverage.tsv`**；`gamemd.exe` 仅只读打开（`pefile.PE(..., fast_load=True)` + `open('rb')`）。")
R.append("> `R16_D1_WIDE_B1\\` 全程只读（复核旧 delta/fields 与 REPORT/审计）。")
R.append("")
R.append("## 0. 一句话结论")
R.append("**只重写这 2 行 ④、未改 grade/判定、未并表。** 把 `004322A0`/`004324B0` 的装表点从栈临时对象"
         " `004014C4`（宿主 `004011C0`，删除析构同构）改到 CDFileClass 真构造器装表点 `0047AA3C`（宿主 `0047AA30`）；"
         " 写一个可执行宿主身份规则并据此重跑 B1 全 18 行，确认其余 16 行无同类可疑。")
R.append("")
R.append("## 1. 0x7E1668 全镜像写入点枚举")
R.append("| 项 | 值 |")
R.append("|---|---:|")
R.append("| 立即数字节 `68 16 7E 00` 原始出现 | %d |" % (len(sites) + len(regload)))
R.append("| 其中 `mov reg,imm32`（寄存器装载，**非写内存**） | %d |" % len(regload))
R.append("| `mov [mem],0x7E1668` 内存写入总数 | %d |" % len(sites))
R.append("| ├ 栈目标（base=esp/ebp） | %d |" % len(stack_sites))
R.append("| └ 非栈目标（base≠esp/ebp） | %d |" % len(nons))
R.append("| 非栈写入点中 **真构造器**（核心规则） | %d |" % n_ctor)
R.append("| 非栈写入点中 **严格 canonical 构造器** | %d |" % n_canon)
R.append("")
R.append("说明：审计 `vptr_stores.tsv` 用全 `.text` 线性反汇编得 199 处（191 栈 + 8 非栈）。"
         "本卡独立按立即数字节扫描 + capstone 精确解码，另检出 `%08X`（`mov [ecx],0x7e1668; jmp 0x431B80`，"
         "8 处 `call` 引用证实为真函数起点，线性反汇编因对齐漏检），故真实内存写入为 %d 处、非栈 %d 处。"
         "该站点是删除析构 thunk，不是构造器；不影响 2 行修法。"
         % (0x535A60, len(sites), len(nons)))
R.append("")
R.append("严格 canonical 规则（本卡交付的可执行规则，见 `host_rule.py`）五门全通站点："
         + "、".join("`%08X`(宿主 `%08X`)" % (x["site"], x["host"]) for x in canon) + "。")
R.append("")
R.append("## 2. 可执行宿主身份校验规则")
R.append("```")
R.append("G0 site 指令必须是 mov [base+disp], vt（imm32==vt）")
R.append("G1 非栈：base ∉ {esp,ebp} 且非绝对地址          # 排除栈临时对象")
R.append("G2 this 对象：base∈GPR 且 disp==0 且宿主 prologue 内 mov base,ecx")
R.append("G3 非析构：宿主内无 call/jmp 到基类析构 0x431B80 于 site 之后；")
R.append("           且无 test byte [esp+X],1 + call 0x7C8B3D + ret imm 签名   # 排除 scalar deleting dtor 同构")
R.append("G4 基类构造前序：宿主内 [host,site) 有 call 0x431B20       # call <alloc>")
R.append("G5 返回 this：终止 ret 前 6 条内有 mov eax,base")
R.append("核心判定(行自查)=G1∧G2∧G3；严格 canonical(选装表点)=G1∧G2∧G3∧G4∧G5")
R.append("```")
R.append("")
R.append("## 3. 2 行新旧装表点/形态对照")
R.append("| entry | 旧装表点 | 旧宿主 | 旧实测指令 | 旧形态 | 新装表点 | 新宿主 | 新实测指令 | 新形态 |")
R.append("|---|---|---|---|---|---|---|---|---|")
for e, slot in sorted(TARGETS.items()):
    old = old_map[e]
    R.append("| %s | %s | %s | `mov dword ptr [esp + 0x20], 0x7e1668` | ctor_body(**错**) | `%08X` | `%08X` | `%s` | ctor_body |"
             % (e, old["install_site"], old["install_host"], NEW_SITE, NEW_HOST, NEW_INSN))
R.append("")
R.append("旧点致命证据：`004014AC mov [esp+0x20],0x7e16b0; call 0x43ae50; 004014C4 mov [esp+0x20],0x7e1668; "
         "call 0x431b80; mov eax,ebp; ret` —— 写栈临时、写后调基类析构 0x431B80、返回堆结构 ebp 而非 this；"
         "与 `004019A0` 的 `test byte [esp+8],1 + call 0x7C8B3D + ret 4` 删除析构体逐指令同构。")
R.append("")
R.append("## 4. 18 行自查结果（`selfcheck18.tsv`）")
R.append("| 项 | 值 |")
R.append("|---|---:|")
R.append("| 自查行数 | 18 |")
R.append("| SUSPECT 行数 | %d |" % len(suspect_rows))
R.append("| SUSPECT entry | %s |" % ("、".join("`%s`" % x for x in suspect_rows) if suspect_rows else "无"))
R.append("")
R.append("逐行点名：")
for ln in sc[1:]:
    c = ln.split("\t")
    R.append("- `%s`：declared=%s host_is_ctor=%s target_is_stack=%s host_is_dtor=%s → **%s**"
             % (c[0], c[1], c[2], c[3], c[4], c[5]))
R.append("")
R.append("结论：除本批要修的 `004322A0`/`004324B0` 外，其余 16 行均无同类可疑"
         "（8 行 mov_abs 写静态 global、8 行 ctor_body 宿主核心规则全通）。")
R.append("")
R.append("## 5. 哈希与只读证明")
R.append("| 项 | 值 |")
R.append("|---|---|")
R.append("| coverage.tsv 字节数（未改） | %d |" % cov_bytes_n)
R.append("| coverage.tsv sha256（未改） | `%s` |" % cov_sha)
R.append("| gamemd.exe sha256（未改，只读打开） | `%s` |" % exe_sha)
R.append("| B1 是否已并表 | **否**（coverage.tsv 两 entry 第4列无 ④，哈希与上版一致） |")
R.append("")
R.append("## 6. 样例 ④（修正后的 `004322A0`）")
R.append("```")
sample = next(bl for bl in open(os.path.join(HERE, "delta.tsv"), "rb").read().split(b"\n")
              if bl.startswith(b"004322A0\t"))
R.append(sample.decode("utf-8").split("\t")[3])
R.append("```")
R.append("")
R.append("## 7. 产物清单")
R.append("- `vt1668_sites.tsv`（9 行非栈写入点） / `delta.tsv`（仅 2 行，8 列） / `fields.tsv`（2 行） / "
         "`selfcheck18.tsv`（18 行） / `REPORT.md` / `host_rule.py`（可执行规则） / `_test_rule.py`（规则自测）")
R.append("")
R.append("**只重写这 2 行 ④、未改 grade/判定、未并表。**")
w(os.path.join(HERE, "REPORT.md"), "\n".join(R) + "\n")

# ---------------------------------------------------------------------------
# 9) final assertions
# ---------------------------------------------------------------------------
assert sha256(COV) == "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1"
assert sha256(EXE) == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
print("OK: wrote vt1668_sites(%d) delta(2) fields(2) selfcheck18(18) REPORT; sites=%d stack=%d nons=%d ctor=%d canon=%d suspect=%s" %
      (len(nons), len(sites), len(stack_sites), len(nons), n_ctor, n_canon, suspect_rows))
