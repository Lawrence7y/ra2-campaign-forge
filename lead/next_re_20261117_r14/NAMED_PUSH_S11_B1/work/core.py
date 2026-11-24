# -*- coding: utf-8 -*-
"""S11 NAMED-PUSH B1 反汇编核心（本批自建）。
PE 加载 + 线性扫描指令索引 + RTTI/虚表解析 + vtable 安装点/函数边界/dtor 判别。
不修改任何既有产物，只读 gamemd.exe 与 function_atlas.tsv（只读线索）。
"""
import os, sys, json, struct, hashlib
import pefile
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
ATLAS_PATH = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def hx(x):
    return "%08X" % (x & 0xFFFFFFFF)

# ---------------- PE ----------------
_pe = pefile.PE(EXE)
IB = _pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in _pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = IB + s.VirtualAddress
    vsz = s.Misc_VirtualSize
    data = s.get_data()
    SECS.append({"name": nm, "va": va, "vsz": vsz, "data": data})

def sec_of(va):
    for s in SECS:
        if s["va"] <= va < s["va"] + max(s["vsz"], len(s["data"])):
            return s
    return None

def sec_name(va):
    s = sec_of(va)
    return s["name"] if s else None

def read_va(va, n):
    s = sec_of(va)
    if not s:
        return b""
    off = va - s["va"]
    if off < 0 or off >= len(s["data"]):
        return b""
    return s["data"][off:off + n]

def u32(va):
    b = read_va(va, 4)
    return int.from_bytes(b, "little") if len(b) == 4 else None

def cstr(va, maxn=256):
    out = bytearray()
    for i in range(maxn):
        b = read_va(va + i, 1)
        if not b or b[0] == 0:
            break
        out += b
    return out.decode("latin1", "replace")

_ts = next(s for s in SECS if s["name"] == ".text")
TEXT_VA, TEXT_VSZ, TEXT_DATA = _ts["va"], _ts["vsz"], _ts["data"]
TEXT_END = TEXT_VA + TEXT_VSZ

def in_text(va):
    return TEXT_VA <= va < TEXT_END

# ---------------- capstone ----------------
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def dis(va, data):
    return list(md.disasm(data, va)) if data else []

def dis_range(va, n):
    return dis(va, read_va(va, n))

# ---------------- 全 .text 线性指令索引 ----------------
print("[core] sweeping .text ...", file=sys.stderr)
INSNS = dis(TEXT_VA, TEXT_DATA)
INS_BY_ADDR = {}
for i in INSNS:
    INS_BY_ADDR[i.address] = i
IMM_INDEX = {}       # imm32 -> [insn addr]
for i in INSNS:
    if i.id == 0:
        continue
    for op in i.operands:
        if op.type == X86_OP_IMM:
            v = op.imm & 0xFFFFFFFF
            IMM_INDEX.setdefault(v, []).append(i.address)
print("[core] insns=%d immkeys=%d" % (len(INSNS), len(IMM_INDEX)), file=sys.stderr)

# ---------------- atlas（只读线索，用于函数边界） ----------------
import csv
ATLAS = {}
with open(ATLAS_PATH, encoding="utf-8-sig") as f:
    rdr = csv.reader(f, delimiter="\t")
    next(rdr)
    for row in rdr:
        if not row or not row[0].strip():
            continue
        try:
            ATLAS[int(row[0], 16)] = int(row[1])
        except ValueError:
            pass

def atlas_func_of(va):
    best = None
    for ea, size in ATLAS.items():
        if ea <= va < ea + size:
            if best is None or ea > best[0]:
                best = (ea, size)
    return best

# ---------------- vtable / RTTI ----------------
def rtti_of_vtable(vb):
    col = u32(vb - 4)
    if not col:
        return None
    sig = u32(col)
    td = u32(col + 0xC)
    if td is None:
        return None
    name = cstr(td + 8, 200)
    return {"col": col, "sig": sig, "td": td, "name": name}

def resolve_slot(slot_va, maxk=64):
    """从槽地址回扫找 vtable 基址（基址前一个 dword 是合法 COL/type_info 指针）。"""
    out = []
    for k in range(0, maxk + 1):
        vb = slot_va - 4 * k
        r = rtti_of_vtable(vb)
        if r and r["sig"] == 0 and ".?A" in r["name"]:
            out.append({"vtable": vb, "slot_index": k, "slot_va": slot_va, **r})
            break
    return out[0] if out else None

def dword_refs(target, include_text=True):
    """全镜像里 dword==target 的地址。"""
    needle = struct.pack("<I", target & 0xFFFFFFFF)
    res = []
    for s in SECS:
        d = s["data"]
        st = 0
        while True:
            i = d.find(needle, st)
            if i < 0:
                break
            if i % 4 == 0 or True:
                res.append(s["va"] + i)
            st = i + 1
    return res

def vtable_layout(vb, n=40):
    vals = []
    for k in range(n):
        v = u32(vb + 4 * k)
        vals.append(v)
        if v is None:
            break
    return vals

# ---------------- 构造安装点 ----------------
def install_sites(vb):
    """找 .text 中把所有 vb 作为立即数的指令（通常是 mov [reg+disp], vb 或 mov reg, vb）。"""
    sites = []
    for ia in IMM_INDEX.get(vb & 0xFFFFFFFF, []):
        ins = INS_BY_ADDR[ia]
        sites.append(ins)
    return sites

def is_vptr_store(ins, vb):
    """mov dword ptr [reg(+disp)], imm==vb"""
    if ins.id != X86_INS_MOV:
        return False
    ops = ins.operands
    if len(ops) != 2:
        return False
    d, s = ops
    if d.type != X86_OP_MEM:
        return False
    if s.type != X86_OP_IMM or (s.imm & 0xFFFFFFFF) != (vb & 0xFFFFFFFF):
        return False
    return d.size == 4

# operator delete / free 线索
FREE_CALLS = {0x7C8B3D, 0x406060, 0x7C8B3A}

def func_body(start, size):
    return dis(start, read_va(start, size))

def callees_of(func_start, size):
    body = func_body(func_start, size)
    out = []
    for i in body:
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            out.append(i.operands[0].imm & 0xFFFFFFFF)
        elif i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_MEM \
                and i.operands[0].mem.base == X86_REG_INVALID:
            out.append(("mem", i.operands[0].mem.disp & 0xFFFFFFFF))
    return out

def dtor_evidence(func_start, size, vb):
    """判断函数是否析构器：operator delete 调用 / 删除标志 / vptr 重装 + free。"""
    body = func_body(func_start, size)
    ev = {"func": func_start, "size": size, "free_calls": [], "del_flag": [], "vptr_stores": [], "ret_this": False}
    for i in body:
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if t in FREE_CALLS:
                ev["free_calls"].append(hx(i.address) + "->" + hx(t))
        if is_vptr_store(i, vb):
            ev["vptr_stores"].append((hx(i.address), i.op_str))
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[1].type == X86_OP_IMM and (i.operands[1].imm & 0xFF) == 1 \
                and i.operands[0].reg in (X86_REG_DL, X86_REG_AL, X86_REG_BL, X86_REG_CL):
            ev["del_flag"].append(hx(i.address) + " " + i.mnemonic + " " + i.op_str)
    # 末尾 ret 前是否 mov eax,this
    tail = body[-6:] if len(body) >= 6 else body
    for i in tail:
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_REG:
            ev["ret_this"] = i.op_str
    return ev

ATEXIT_VA = 0x7C978A

def is_atexit_registered(func_va):
    sites = []
    for ia in IMM_INDEX.get(func_va, []):
        ins = INS_BY_ADDR[ia]
        if ins.id == X86_INS_PUSH and ins.operands and ins.operands[0].type == X86_OP_IMM:
            for j in range(ia + ins.size, min(ia + ins.size + 0x60, TEXT_END - 6)):
                jins = INS_BY_ADDR.get(j)
                if jins and jins.id == X86_INS_CALL and jins.operands \
                        and jins.operands[0].type == X86_OP_IMM \
                        and (jins.operands[0].imm & 0xFFFFFFFF) == ATEXIT_VA:
                    sites.append((hx(ia), hx(j)))
                    break
    return sites

def dword_ref_count(target):
    return len(dword_refs(target))

if __name__ == "__main__":
    print("sha256:", sha256(EXE), "OK" if sha256(EXE) == EXPECT else "MISMATCH")
    print("text=[%s,%s) vsz=%d" % (hx(TEXT_VA), hx(TEXT_END), TEXT_VSZ))
    print("atlas funcs:", len(ATLAS))
    # 自检：已知阳性（S12_B2 00453E20 的 vtable 007E3EBC 安装点 0x43B71F）
    r = resolve_slot(0x007E3ED0)
    print("selfcheck slot 007E3ED0 ->", r)
    st = [i for i in install_sites(0x007E3EBC) if is_vptr_store(i, 0x007E3EBC)]
    print("selfcheck installs of 007E3EBC ->", [(hx(i.address), i.op_str) for i in st])
