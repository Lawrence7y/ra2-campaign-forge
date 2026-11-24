# -*- coding: utf-8 -*-
"""NAMED_PUSH_S17_B1 自建核心库：PE 加载 + RTTI/虚表 + ③b② 预筛 + direct caller。
只读目标 gamemd.exe；capstone 5.0.7 skipdata=True + pefile 2024.8.26。
遵守 D-40：RTTI pTD/pCHD 绝对 VA；TD+8 内联串；②④不同源；㉓ 析构器写点排除。
"""
import csv, json, os, struct, hashlib, pefile
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE  = os.path.join(BASE, r"ra2youli\gamemd.exe")
ATLAS= os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def sha256_exe():
    h = hashlib.sha256()
    with open(EXE, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()

def hx(x): return "%08X" % (x & 0xFFFFFFFF)

_pe = pefile.PE(EXE)
IB = _pe.OPTIONAL_HEADER.ImageBase
_SECS = []
for s in _pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = IB + s.VirtualAddress
    sz = max(s.Misc_VirtualSize, s.SizeOfRawData)
    _SECS.append((nm, va, s.Misc_VirtualSize, s.get_data()[:sz]))

_text = next(s for s in _pe.sections if s.Name.rstrip(b"\x00") == b".text")
TEXT_VA = IB + _text.VirtualAddress
TEXT_DATA = _text.get_data()
TEXT_SIZE = _text.Misc_VirtualSize   # 0x3DF38D

def in_text(va): return TEXT_VA <= va < TEXT_VA + TEXT_SIZE

def va_in(va):
    for nm, v0, vsz, data in _SECS:
        if v0 <= va < v0 + vsz: return nm
    return None

def va_read(va, n):
    for nm, v0, vsz, data in _SECS:
        if v0 <= va < v0 + vsz:
            off = va - v0
            return data[off:off + n]
    return b""

def u32(va):
    b = va_read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None

def read_cstr(va, maxn=256):
    out = bytearray()
    for i in range(maxn):
        b = va_read(va + i, 1)
        if not b or b[0] == 0: break
        out += b
    return out.decode("latin1", "replace")

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def disasm(va, data): return list(_md.disasm(data, va)) if data else []

def disasm_body(va, size): return disasm(va, va_read(va, size if size else 512))

# ---- atlas ----
def load_atlas():
    a = {}
    with open(ATLAS, encoding="utf-8-sig") as f:
        rdr = csv.reader(f, delimiter="\t"); next(rdr)
        for row in rdr:
            if not row or not row[0].strip(): continue
            try:
                a[hx(int(row[0], 16))] = dict(size=int(row[1]), n_instr=int(row[2]))
            except (ValueError, IndexError):
                pass
    return a
ATLAS = load_atlas()

def containing_atlas_func(va):
    best = None
    for e, info in ATLAS.items():
        ea = int(e, 16)
        if ea <= va < ea + info["size"]:
            if best is None or ea > best[0]:
                best = (ea, e, info["size"])
    return best

# ---- RTTI / vtable ----
def find_dword_refs(target, skip_text=True):
    needle = struct.pack("<I", target & 0xFFFFFFFF)
    refs = []
    for nm, v0, vsz, data in _SECS:
        if skip_text and nm == ".text": continue
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0: break
            refs.append((v0 + i, nm)); st = i + 1
    return refs

def parse_col(col_va):
    sig = u32(col_va); td = u32(col_va + 0xC); chd = u32(col_va + 0x10)
    if sig is None: return None
    return {"col": col_va, "sig": sig, "td": td, "chd": chd}

def parse_td(td_va):
    if not td_va or not va_in(td_va): return None
    # TD+0 = pVFTable, TD+4 = spare, TD+8 = inline decorated name (NOT a pointer)
    return {"td": td_va, "vfptr": u32(td_va), "name_va": td_va + 8,
            "name": read_cstr(td_va + 8, 256)}

def resolve_slot(refva, kmax=48):
    """slot VA 回扫 k=0..kmax 找 COL(sig=0, TD 名 .?AV)，得 vtable_base/slot_off/RTTI。"""
    for k in range(0, kmax + 1):
        vb = refva - 4 * k
        c = u32(vb - 4)
        if not c: continue
        ci = parse_col(c)
        if not ci or ci["sig"] != 0: continue
        tdi = parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return {"vtable_base": vb, "slot_off": 4 * k, "slot_idx": k,
                    "col": ci["col"], "td": ci["td"], "chd": ci["chd"],
                    "name_va": tdi["name_va"], "rtti_name": tdi["name"]}
    return None

def resolve_slot_by_vt(vt_base, slot_off):
    """已知 vtable base + slot offset 时直接取 RTTI（vt-4 -> COL）。"""
    c = u32(vt_base - 4)
    if not c: return None
    ci = parse_col(c)
    if not ci or ci["sig"] != 0: return None
    tdi = parse_td(ci["td"])
    if not tdi: return None
    return {"vtable_base": vt_base, "slot_off": slot_off, "slot_idx": slot_off // 4,
            "col": ci["col"], "td": ci["td"], "chd": ci["chd"],
            "name_va": tdi["name_va"], "rtti_name": tdi["name"]}

# ---- .text 扫描 ----
def find_direct_calls(target):
    calls = []
    for off in range(0, len(TEXT_DATA) - 5):
        if TEXT_DATA[off] != 0xE8: continue
        rel = struct.unpack_from("<i", TEXT_DATA, off + 1)[0]
        dest = (TEXT_VA + off + 5 + rel) & 0xFFFFFFFF
        if dest == (target & 0xFFFFFFFF):
            calls.append(TEXT_VA + off)
    return calls

def find_vtable_writes(vtable_addr):
    """找 .text 中把 vtable_addr 当立即数写入的站点，辨认 C7 05 / C7 r/m / B8+r。"""
    writes = {"global": [], "regdisp": [], "imm_load": []}
    for off in range(6, len(TEXT_DATA) - 4):
        imm = struct.unpack_from("<I", TEXT_DATA, off)[0]
        if imm != (vtable_addr & 0xFFFFFFFF): continue
        va = TEXT_VA + off
        if TEXT_DATA[off-6] == 0xC7 and TEXT_DATA[off-5] == 0x05:
            absv = struct.unpack_from("<I", TEXT_DATA, off-4)[0]
            writes["global"].append({"write_va": hx(TEXT_VA + off - 6), "global": hx(absv)})
        elif TEXT_DATA[off-2] == 0xC7:
            writes["regdisp"].append(hx(TEXT_VA + off - 2))
        if 0xB8 <= TEXT_DATA[off-1] <= 0xBF:
            writes["imm_load"].append(hx(TEXT_VA + off - 1))
    return writes

ATEXIT_VA = 0x7C978A   # atexit / _atexit 注册器（与既有卡一致）

def is_atexit_registered(func_va, window=0x60):
    """func_va 作为 push imm32 出现在某 call atexit 之前 window 内 => atexit 全局析构器。"""
    needle = b"\x68" + struct.pack("<I", func_va & 0xFFFFFFFF)
    sites = []
    st = 0
    while True:
        i = TEXT_DATA.find(needle, st)
        if i < 0: break
        for j in range(i + 5, min(i + 5 + window, len(TEXT_DATA) - 5)):
            if TEXT_DATA[j] == 0xE8:
                rel = struct.unpack_from("<i", TEXT_DATA, j + 1)[0]
                if (TEXT_VA + j + 5 + rel) & 0xFFFFFFFF == ATEXIT_VA:
                    sites.append((hx(TEXT_VA + i), hx(TEXT_VA + j)))
                    break
        st = i + 1
    return sites

def find_indirect_dispatch(reg_off, maxn=5000):
    """统计 .text 中 ff 5x <reg_off> 形态的 call [reg+off] 站点（抽样+计数）。
       reg_off 为 disp8（<0x80）。返回 (count, [samples])；仅统计 call(FF /2) 非 jmp。"""
    samples = []; count = 0
    if reg_off < 0 or reg_off > 0x7F: return (0, [])
    for off in range(0, len(TEXT_DATA) - 3):
        b0 = TEXT_DATA[off]
        if b0 != 0xFF: continue
        modrm = TEXT_DATA[off+1]
        # mod=00, reg=010 (call), rm=reg ; disp8 only if mod=01 -> modrm 0x5x with mod=01
        if (modrm & 0xC7) == 0x54 and TEXT_DATA[off+2] == reg_off:  # 01 010 100 = 0x54: call [reg+disp8]
            count += 1
            if len(samples) < maxn: samples.append(hx(TEXT_VA + off))
    return (count, samples)

# ---- ③b② 预筛 ----
JCC_IDS = set()
for _cn in dir():
    if _cn.startswith("X86_INS_J") and _cn != "X86_INS_JMP":
        JCC_IDS.add(globals()[_cn])

def is_eax(op): return op.type == X86_OP_REG and op.reg == X86_REG_EAX

def test_kind(ins):
    if ins.id == X86_INS_TEST and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
        return ("TEST_EAX", 0)
    if ins.id == X86_INS_OR and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
        return ("OR_EAX", 0)
    if ins.id == X86_INS_CMP and len(ins.operands) == 2 and is_eax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM:
        return ("CMP_IMM", ins.operands[1].imm & 0xFFFFFFFF)
    return None

def is_falsifiable(v, strict=False):
    # strict: 多值状态码/Find -1 下标约定算；{0,1} 布尔不算
    if v == 0xFFFFFFFF: return True
    if 0x80000000 <= v <= 0x8FFFFFFF: return True
    if 0xC0000000 <= v <= 0xDFFFFFFF: return True
    if strict: return False
    if v in (0, 1): return True
    return False

def path_sig(insns, start_idx, maxn=20):
    if start_idx is None or start_idx < 0 or start_idx >= len(insns):
        return {"calls": [], "rets": [], "has_ret": False, "end_eax": "OOB"}
    calls, rets = set(), set(); has_ret = False; eax = None
    for j in range(start_idx, min(start_idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0: continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
            eax = 0
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2 and is_eax(ins.operands[0]):
            b = ins.operands[1]
            eax = (b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else None
        elif ins.id == X86_INS_RET:
            has_ret = True
            if eax is not None: rets.add(eax)
            break
        elif ins.id == X86_INS_JMP:
            break
    return {"calls": sorted(hx(c) for c in calls), "rets": sorted(hx(r) for r in rets),
            "has_ret": has_ret, "end_eax": hx(eax) if isinstance(eax, int) else None}

def channel_A(insns, strict=False):
    idx = {ins.address: i for i, ins in enumerate(insns)}
    sites = []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL: continue
        for k in range(i + 1, min(i + 6, len(insns))):
            tk = test_kind(insns[k])
            if not tk: continue
            for m in range(k + 1, min(k + 4, len(insns))):
                jc = insns[m]
                if jc.id not in JCC_IDS: continue
                tgt = jc.operands[0].imm if jc.operands and jc.operands[0].type == X86_OP_IMM else None
                ti = idx.get(tgt)
                sig_t = path_sig(insns, ti)
                sig_f = path_sig(insns, m + 1)
                key = ("calls", "rets", "has_ret", "end_eax")
                if tuple(sig_t[x] for x in key) == tuple(sig_f[x] for x in key):
                    continue
                falsy = None
                if tk[0] == "CMP_IMM" and is_falsifiable(tk[1], strict): falsy = tk[1]
                elif tk[0] in ("TEST_EAX", "OR_EAX") and jc.id == X86_INS_JE and not strict: falsy = 0
                sites.append({
                    "call_addr": hx(ins.address),
                    "test_addr": hx(insns[k].address), "test_kind": tk[0],
                    "test_imm": hx(tk[1]) if tk[1] is not None else None,
                    "jcc_addr": hx(jc.address), "jcc": jc.mnemonic,
                    "jcc_target": hx(tgt) if tgt is not None else None,
                    "falsy": hx(falsy) if falsy is not None else None,
                    "sig_taken": sig_t, "sig_fallthrough": sig_f,
                })
                break
    return sites

if __name__ == "__main__":
    print("core OK sha=%s text=[%08X,%08X) atlas=%d" % (sha256_exe(), TEXT_VA, TEXT_VA + TEXT_SIZE, len(ATLAS)))
