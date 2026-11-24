# -*- coding: utf-8 -*-
"""
RESCAN-MOVED — 验证 1,733 是下界：补扫「返回值搬移后比较」形态（只读，只写 RESCAN_MOVED）

卡片: lead/next_re_20261117_r14/_cards/RESCAN-MOVED.md

池 = 与 SURVEY_3B2 同池 = coverage 行 ∧ entry 在 atlas 内 ∧ grade != [已证]

三形态（共用同一套窗口/断链/陷阱/分叉判据）:
  M0  call 后 +1..+3 内 test eax,eax / cmp eax,<imm> / or eax,eax，其后 +1..+2 内 jcc
      —— 逐字节复刻 SURVEY_3B2\survey.py 的 scan_row()，用于与 p3b2 对账
  M1  call 后先 mov r,eax（r ∈ {ebx,ebp,esi,edi,ecx,edx}）或 push eax;…;pop r，
      随后 test r,r / cmp r,<imm>，其后 +1..+2 内 jcc
  M2  call 后 mov [ebp-x],eax / mov [esp+x],eax，随后对该同一栈槽 cmp/test，其后 jcc

三形态共同排除（不放宽）:
  (a) 比较之后、分支之前，被比较的寄存器/栈槽被覆写 ⇒ 不算
  (b) 两条路径动作相同（同一处 call 只差参数）⇒ 不算（沿用 survey.py 的 path_sig）
  (c) 两条路径汇合到同一处（jcc 目标落在 fall-through 窗口内）且只差写入值 ⇒ 不算

输出: rescan.tsv / REPORT.md(手写) / samples.tsv(手写) / 本脚本
"""
import csv
import hashlib
import math
import os
import re
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone.x86 as cx86
from capstone.x86 import (
    X86_INS_CALL, X86_INS_JMP, X86_INS_RET, X86_INS_TEST, X86_INS_OR, X86_INS_CMP,
    X86_INS_MOV, X86_INS_XOR, X86_INS_SUB, X86_INS_AND, X86_INS_XCHG, X86_INS_LEA,
    X86_INS_PUSH, X86_INS_POP,
    X86_OP_REG, X86_OP_IMM, X86_OP_MEM, X86_REG_EAX,
)

# ---------------------------------------------------------------- paths
BASE = os.path.dirname(os.path.abspath(__file__))            # ...\RESCAN_MOVED
R14 = os.path.dirname(BASE)                                  # ...\next_re_20261117_r14
ROOT = os.path.dirname(os.path.dirname(R14))                 # 项目根
COVERAGE_TSV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS_TSV = os.path.join(os.path.dirname(R14), "next_re_20261112_r10",
                         "W130_atlas", "function_atlas.tsv")
SURVEY_TSV = os.path.join(R14, "SURVEY_3B2", "survey.tsv")
HITS_TSV = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EXE_SHA256 = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

SUBS = ["S%02d" % i for i in range(1, 23)]

# ---------------------------------------------------------------- helpers
def norm_entry(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    return e


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


JCC_IDS = set()
for _n in dir(cx86):
    if _n.startswith("X86_INS_J") and _n != "X86_INS_JMP":
        _v = getattr(cx86, _n)
        if isinstance(_v, int):
            JCC_IDS.add(_v)
CONTROL_IDS = ({X86_INS_JMP, X86_INS_RET, X86_INS_CALL,
                cx86.X86_INS_LOOP, cx86.X86_INS_LOOPE, cx86.X86_INS_LOOPNE}
               | JCC_IDS)

EAX_IDEMPOTENT = {X86_INS_OR, X86_INS_AND, X86_INS_MOV, X86_INS_XCHG, X86_INS_TEST}


def is_eax(op):
    return op.type == X86_OP_REG and op.reg == X86_REG_EAX


def writes_eax(ins):
    """该指令是否可能覆写 eax（skipdata/未知形态一律按覆写处理，保守）。"""
    if ins.id == X86_INS_CALL:
        return True
    try:
        _, wr = ins.regs_access()
    except Exception:
        return True
    if X86_REG_EAX in wr:
        if (ins.id in EAX_IDEMPOTENT and len(ins.operands) == 2
                and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
            return False
        return True
    return False


def test_kind(ins):
    """M0 指定的三种比较形态（eax 三形态，逐字节复刻 survey.py）。"""
    if (ins.id == X86_INS_TEST and len(ins.operands) == 2
            and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
        return ("TEST_EAX", 0)
    if (ins.id == X86_INS_OR and len(ins.operands) == 2
            and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
        return ("OR_EAX", 0)
    if (ins.id == X86_INS_CMP and len(ins.operands) == 2
            and is_eax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM):
        return ("CMP_IMM", ins.operands[1].imm & 0xFFFFFFFF)
    return None


def path_sig(insns, start_idx, maxn=16):
    """路径动作签名（沿用 SURVEY_3B2 已过审实现，M1/M2 同一把尺，不放宽）:
    直接 call 目标集 / ret 前 eax 常量集 / 是否 ret / 末端 eax 常量。"""
    calls, rets = set(), set()
    has_ret = False
    eax = None
    end_eax = None
    for j in range(start_idx, min(start_idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:
            continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif (ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2
                and is_eax(ins.operands[0]) and is_eax(ins.operands[1])):
            eax = 0
        elif (ins.id == X86_INS_MOV and len(ins.operands) == 2
                and is_eax(ins.operands[0])):
            eax = ((ins.operands[1].imm & 0xFFFFFFFF)
                   if ins.operands[1].type == X86_OP_IMM else None)
        elif ins.id == X86_INS_RET:
            has_ret = True
            if eax is not None:
                rets.add(eax)
            end_eax = eax
            break
        elif ins.id == X86_INS_JMP:
            end_eax = eax
            break
        else:
            end_eax = eax
    return {"calls": sorted(calls), "rets": sorted(rets),
            "has_ret": has_ret, "end_eax": end_eax}


SIG_KEYS = ("calls", "rets", "has_ret", "end_eax")
OUT_OF_BODY_SIG = {"calls": [], "rets": [], "has_ret": False, "end_eax": "OUT_OF_BODY"}

# ---------------------------------------------------------------- M1/M2 helpers
MOV_SRC_REGS = {"ebx": cx86.X86_REG_EBX, "ebp": cx86.X86_REG_EBP,
                "esi": cx86.X86_REG_ESI, "edi": cx86.X86_REG_EDI,
                "ecx": cx86.X86_REG_ECX, "edx": cx86.X86_REG_EDX}
REG_NAME = {v: k for k, v in MOV_SRC_REGS.items()}
# 与 esp/ebp 同族的高 16/8 位切片：写它们同样会毁掉栈槽寻址
SP_BP_FAMILY = set()
for _base in ("X86_REG_ESP", "X86_REG_EBP", "X86_REG_EBX", "X86_REG_ESI",
              "X86_REG_EDI", "X86_REG_ECX", "X86_REG_EDX"):
    for _suf in ("", "H", "L", "X", "I"):
        _v = getattr(cx86, _base + _suf, None)
        if isinstance(_v, int) and _v != 0:
            SP_BP_FAMILY.add(_v)


def reg_name(r):
    if r in REG_NAME:
        return REG_NAME[r]
    for n in ("ecx", "edx", "esi", "edi", "ebx", "ebp", "eax", "esp"):
        if getattr(cx86, "X86_REG_" + n.upper(), None) == r:
            return n
    return "r%d" % r


def writes_reg(ins, reg):
    """该指令是否可能写 reg（保守：未知/skipdata/寄存器别名一律按写处理）。"""
    if ins.id == 0:
        return True
    if ins.id == X86_INS_CALL:
        # callee 可覆写 caller-saved；对 callee-saved 也保守按写处理（只影响 M1 的中间窗口）
        return True
    try:
        _, wr = ins.regs_access()
    except Exception:
        return True
    if reg in wr:
        # mov r,r / or r,r / test r,r 等自身不动值
        if (ins.id in EAX_IDEMPOTENT and len(ins.operands) == 2
                and ins.operands[0].type == X86_OP_REG and ins.operands[0].reg == reg
                and ins.operands[1].type == X86_OP_REG and ins.operands[1].reg == reg):
            return False
        return True
    return False


def slot_key(op):
    """栈槽身份（base, index, disp）；非 [ebp±x]/[esp+x] 返回 None。"""
    if op.type != X86_OP_MEM:
        return None
    b = op.mem.base
    if b not in (cx86.X86_REG_EBP, cx86.X86_REG_ESP):
        return None
    return (b, op.mem.index, op.mem.scale, op.mem.disp)


MEM_WRITE_IDS_NEVER = {X86_INS_CMP, X86_INS_TEST, X86_INS_LEA, X86_INS_PUSH}


def writes_slot(ins, key):
    """该指令是否可能写该栈槽（含写 base 寄存器使寻址失效）。"""
    if key is None:
        return True
    if ins.id == 0 or ins.id == X86_INS_CALL:
        return True
    ops = ins.operands
    if not ops:
        return False
    # base 寄存器被改 ⇒ 寻址基址变了
    if key[0] is not None:
        try:
            _, wr = ins.regs_access()
        except Exception:
            return True
        if key[0] in wr and key[0] != cx86.X86_REG_ESP:
            return True  # ebp 被覆写
    if ops[0].type == X86_OP_MEM and ins.id not in MEM_WRITE_IDS_NEVER:
        if slot_key(ops[0]) == key:
            return True
    return False


def mem_cmp_kind(ins, key):
    """M2: 对该栈槽的 cmp/test。imm 为 None 表示与寄存器比较（无法据此认定多值常量分派）。"""
    ops = ins.operands
    if ins.id not in (X86_INS_CMP, X86_INS_TEST) or len(ops) != 2:
        return None
    for a, b in ((ops[0], ops[1]), (ops[1], ops[0])):
        if slot_key(a) == key and b.type in (X86_OP_IMM, X86_OP_REG):
            return (("CMP_MEM" if ins.id == X86_INS_CMP else "TEST_MEM"),
                    (b.imm & 0xFFFFFFFF) if b.type == X86_OP_IMM else None)
    return None


def reg_cmp_kind(ins, reg):
    """M1: 对搬移后寄存器的 test r,r / cmp r,<imm>。"""
    ops = ins.operands
    if ins.id == X86_INS_TEST and len(ops) == 2:
        if ops[0].type == X86_OP_REG and ops[0].reg == reg \
                and ops[1].type == X86_OP_REG and ops[1].reg == reg:
            return ("TEST_R", 0)
    if ins.id == X86_INS_CMP and len(ops) == 2:
        if ops[0].type == X86_OP_REG and ops[0].reg == reg and ops[1].type == X86_OP_IMM:
            return ("CMP_IMM", ops[1].imm & 0xFFFFFFFF)
    return None


# ---- 可伪证性分层（机械筛，不是语义证实）：
#   布尔口径 {0,1} 与哨兵口径 {-1} 一律不算多值状态码；只有"与 0/1/-1 之外的具体值比较"
#   才可能是多值分派。D-46(A)：布尔返回不算可伪证。
BOOL_IMMS = {0, 1, 0xFFFFFFFF}


def is_value_dispatch(kind_imm):
    """比较是否属于"多值分派"形态（可伪证的最小前提）。
    只认"与具体立即数比较且该立即数不属布尔/哨兵口径"；与寄存器比较、test 一律不算。"""
    if kind_imm is None:
        return False
    kind, imm = kind_imm
    if kind in ("TEST_R", "TEST_MEM"):
        return False          # 空值/布尔检测
    if imm is None:
        return False          # 与寄存器比较：无法认定多值常量分派
    return imm not in BOOL_IMMS


def branch_ok(insns, k, writes_fn):
    """比较在 k，找 +1..+2 内的 jcc；返回 (jcc_idx, tgt, reason)。
    reason: OK / GAP_CLOBBER（比较与分支之间被覆写 ⇒ 陷阱）/ NONE。"""
    for m in range(k + 1, min(k + 3, len(insns))):
        jc = insns[m]
        if jc.id in JCC_IDS:
            gap = insns[k + 1:m]
            bad = any(g.id == 0 or g.id in CONTROL_IDS or writes_fn(g) for g in gap)
            tgt = None
            if jc.operands and jc.operands[0].type == X86_OP_IMM:
                tgt = jc.operands[0].imm & 0xFFFFFFFF
            return m, tgt, ("GAP_CLOBBER" if bad else "OK")
        if jc.id == 0 or writes_fn(jc):
            return None, None, "GAP_CLOBBER"
        if jc.id in CONTROL_IDS:
            return None, None, "NONE"
    return None, None, "NONE"


ACTION_KEYS = ("calls", "rets", "has_ret")
MEM_READ_ONLY_IDS = {X86_INS_CMP, X86_INS_TEST, X86_INS_LEA, X86_INS_PUSH}


def has_side_effect(ins):
    """该指令是否构成"动作"（而非纯寄存器取值）：
    call/ret/控制转移、垃圾字节、写内存、push/pop 一律算动作。"""
    if ins.id == 0:
        return True
    if ins.id in CONTROL_IDS:
        return True
    if ins.id in (X86_INS_PUSH, X86_INS_POP):
        return True
    if ins.operands and ins.operands[0].type == X86_OP_MEM \
            and ins.id not in MEM_READ_ONLY_IDS:
        return True
    return False


def paths_differ(insns, idx_by_addr, m, tgt):
    """(b) 两条路径动作不同 ∧ (c) 不汇合到同一处且只差写入值。返回 (ok, why)。"""
    ti = idx_by_addr.get(tgt) if tgt is not None else None
    # (c) 汇合形态：taken 目标落在 fall-through 前方窗口内 ⇒ 两条路径终将走到同一段代码。
    #     此时判定必须落在"分支到汇合点之间到底做了什么"上：
    #       fall-through 段（m+1 … ti-1）里出现任何动作（call/ret/控制转移/写内存/push…）
    #       ⇒ 一侧执行了该动作、另一侧跳过 ⇒ 动作不同 ⇒ 算；
    #       段内只有寄存器写（纯取值）或段为空 ⇒ 只差写入值 ⇒ 不算。
    if ti is not None and m + 1 <= ti <= m + 16:
        seg = insns[m + 1:ti]
        if not seg:
            return False, "CONVERGE_EMPTY"
        if any(has_side_effect(g) for g in seg):
            return True, "OK"
        return False, "CONVERGE_VALUE_ONLY"
    # 非汇合：沿用 SURVEY_3B2 的 P2 动作签名判据（同一把尺，不放宽）
    sig_t = path_sig(insns, ti) if ti is not None else OUT_OF_BODY_SIG
    sig_f = path_sig(insns, m + 1)
    if tuple(sig_t[x] for x in SIG_KEYS) == tuple(sig_f[x] for x in SIG_KEYS):
        return False, "SIGNATURE_SAME"
    return True, "OK"


# ---------------------------------------------------------------- 1. 输入自校验
print("[1] 输入自校验", flush=True)
exe_hash = sha256(EXE)
ok_hash = exe_hash == EXE_SHA256
print("    gamemd.exe SHA-256 = %s  %s" % (exe_hash, "OK" if ok_hash else "MISMATCH"))
if not ok_hash:
    sys.exit("exe 指纹不符，停止")

atlas = {}
with open(ATLAS_TSV, encoding="utf-8") as f:
    lines = f.read().splitlines()
for ln in lines[1:]:
    if not ln.strip():
        continue
    p = ln.split("\t")
    if len(p) < 3:
        continue
    try:
        atlas[norm_entry(p[0])] = (int(p[1]), int(p[2]))
    except ValueError:
        pass
print("    atlas 行: %d（唯一 entry %d）" % (len(lines) - 1, len(atlas)))

coverage = []
with open(COVERAGE_TSV, encoding="utf-8") as f:
    lines = f.read().splitlines()
malformed = 0
for ln in lines[1:]:
    p = ln.split("\t")
    if len(p) < 8:
        malformed += 1
        continue
    coverage.append({"entry": norm_entry(p[0]), "subsystem": p[1], "name": p[2],
                     "semantics": p[3], "grade": p[4]})
print("    coverage 数据行: %d（畸形 %d）" % (len(coverage), malformed))

# ---------------------------------------------------------------- 2. 池
st = {s: dict(n=0, proved=0, pool=0) for s in SUBS}
pool_rows = []
for r in coverage:
    s = r["subsystem"]
    if s not in st:
        continue
    if r["entry"] not in atlas:
        continue
    st[s]["n"] += 1
    if r["grade"] == "[已证]":
        st[s]["proved"] += 1
        continue
    st[s]["pool"] += 1
    pool_rows.append({"entry": r["entry"], "subsystem": s, "name": r["name"],
                      "grade": r["grade"],
                      "size": atlas[r["entry"]][0],
                      "n_instr": atlas[r["entry"]][1]})
print("    池行合计: %d" % len(pool_rows))

# ---------------------------------------------------------------- 3. 反汇编 + 三形态
print("[2] 三形态判定（skipdata=True）", flush=True)
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text")
TEXT_VA = IB + sec.VirtualAddress
TEXT_DATA = sec.get_data()
TEXT_SIZE = max(sec.Misc_VirtualSize, sec.SizeOfRawData)
print("    ImageBase=0x%08X .text=[0x%X, 0x%X)" % (IB, TEXT_VA, TEXT_VA + TEXT_SIZE))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True


def read_va(va, maxlen):
    off = va - TEXT_VA
    if off < 0 or off >= len(TEXT_DATA):
        return b""
    return TEXT_DATA[off:off + maxlen]


def scan_m0(insns, idx_by_addr):
    """逐字节复刻 SURVEY_3B2\survey.py 的 scan_row()，只保留 n_valid。"""
    n_valid = 0
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        k = None
        for j in range(i + 1, min(i + 4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.id in CONTROL_IDS or writes_eax(mid):
                break
            tk = test_kind(mid)
            if tk:
                k = j
                break
        if k is None:
            continue
        for m in range(k + 1, min(k + 3, len(insns))):
            jc = insns[m]
            if jc.id in JCC_IDS:
                gap = insns[k + 1:m]
                bad_gap = any(g.id == 0 or g.id in CONTROL_IDS or writes_eax(g)
                              for g in gap)
                if bad_gap:
                    break
                tgt = None
                if jc.operands and jc.operands[0].type == X86_OP_IMM:
                    tgt = jc.operands[0].imm & 0xFFFFFFFF
                ti = idx_by_addr.get(tgt) if tgt is not None else None
                sig_t = path_sig(insns, ti) if ti is not None else OUT_OF_BODY_SIG
                sig_f = path_sig(insns, m + 1)
                if tuple(sig_t[x] for x in SIG_KEYS) != tuple(sig_f[x] for x in SIG_KEYS):
                    n_valid += 1
                break
            if writes_eax(jc) or jc.id == 0:
                break
            if jc.id in CONTROL_IDS:
                break
    return n_valid


def scan_m1(insns, idx_by_addr, reasons):
    """call → mov r,eax（或 push eax;…;pop r）→ test r,r / cmp r,<imm> → jcc。
    返回 (n_valid, sites)。"""
    n_valid = 0
    sites = []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        reg = None
        mov_i = None
        # (a) 直接 mov r,eax，窗口 call+1..+3，中间不许写 r、不许控制转移
        for j in range(i + 1, min(i + 4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.id in CONTROL_IDS:
                break
            if (mid.id == X86_INS_MOV and len(mid.operands) == 2
                    and mid.operands[0].type == X86_OP_REG
                    and mid.operands[0].reg in MOV_SRC_REGS.values()
                    and is_eax(mid.operands[1])):
                reg = mid.operands[0].reg
                mov_i = j
                break
            if mid.id == X86_INS_MOV and len(mid.operands) == 2 \
                    and mid.operands[0].type == X86_OP_REG \
                    and mid.operands[0].reg == X86_REG_EAX and writes_eax(mid):
                break  # eax 已被覆写，返回值不在 eax 了
        # (b) push eax; …; pop r
        if reg is None:
            j0 = i + 1
            if j0 < len(insns) and insns[j0].id == X86_INS_PUSH and insns[j0].operands \
                    and is_eax(insns[j0].operands[0]):
                depth = 1
                for j in range(j0 + 1, min(j0 + 6, len(insns))):
                    mid = insns[j]
                    if mid.id == 0 or mid.id in CONTROL_IDS:
                        break
                    if mid.id == X86_INS_PUSH:
                        depth += 1
                        continue
                    if mid.id == X86_INS_POP and mid.operands \
                            and mid.operands[0].type == X86_OP_REG:
                        depth -= 1
                        if depth == 0:
                            if mid.operands[0].reg in MOV_SRC_REGS.values():
                                reg = mid.operands[0].reg
                                mov_i = j
                            break
        if reg is None:
            continue
        # 找比较：mov_i+1..+3 内，中间不许写 reg
        k = None
        for j in range(mov_i + 1, min(mov_i + 4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.id in CONTROL_IDS:
                break
            if reg_cmp_kind(mid, reg):
                k = j
                break
            if writes_reg(mid, reg):
                break
        if k is None:
            reasons["m1_no_cmp"] += 1
            continue
        m, tgt, reason = branch_ok(insns, k, lambda g: writes_reg(g, reg))
        if reason != "OK":
            reasons["m1_" + reason] += 1
            continue
        ok, why = paths_differ(insns, idx_by_addr, m, tgt)
        if ok:
            n_valid += 1
            sites.append((insns[i].address, insns[mov_i].address, insns[k].address,
                          reg_name(reg), insns[m].address, tgt,
                          reg_cmp_kind(insns[k], reg)))
        else:
            reasons["m1_" + why] += 1
    return n_valid, sites


def scan_m2(insns, idx_by_addr, reasons):
    """call → mov [ebp-x],eax / mov [esp+x],eax → cmp/test 同一栈槽 → jcc。"""
    n_valid = 0
    sites = []
    for i, ins in enumerate(insns):
        if ins.id != X86_INS_CALL:
            continue
        key = None
        mov_i = None
        for j in range(i + 1, min(i + 4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.id in CONTROL_IDS:
                break
            if (mid.id == X86_INS_MOV and len(mid.operands) == 2
                    and mid.operands[0].type == X86_OP_MEM
                    and slot_key(mid.operands[0]) is not None
                    and is_eax(mid.operands[1])):
                key = slot_key(mid.operands[0])
                mov_i = j
                break
            if writes_eax(mid):
                break
        if key is None:
            continue
        k = None
        for j in range(mov_i + 1, min(mov_i + 4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.id in CONTROL_IDS:
                break
            if mem_cmp_kind(mid, key):
                k = j
                break
            if writes_slot(mid, key):
                break
        if k is None:
            reasons["m2_no_cmp"] += 1
            continue
        m, tgt, reason = branch_ok(insns, k, lambda g: writes_slot(g, key))
        if reason != "OK":
            reasons["m2_" + reason] += 1
            continue
        ok, why = paths_differ(insns, idx_by_addr, m, tgt)
        if ok:
            n_valid += 1
            sites.append((insns[i].address, insns[mov_i].address, insns[k].address,
                          "slot_%s%+d" % (reg_name(key[0]), key[3]),
                          insns[m].address, tgt, mem_cmp_kind(insns[k], key)))
        else:
            reasons["m2_" + why] += 1
    return n_valid, sites


PSEUDO_RE = re.compile(r"^(sub_|fn_)|::(sub_|fn_)[0-9A-Fa-f]*$")


def is_named(name):
    return bool(name) and not PSEUDO_RE.match(name)


hits = []
reasons = {"m1_no_cmp": 0, "m1_GAP_CLOBBER": 0, "m1_NONE": 0, "m1_SIGNATURE_SAME": 0,
           "m1_CONVERGE_VALUE_ONLY": 0,
           "m2_no_cmp": 0, "m2_GAP_CLOBBER": 0, "m2_NONE": 0, "m2_SIGNATURE_SAME": 0,
           "m2_CONVERGE_VALUE_ONLY": 0}
for idx, row in enumerate(pool_rows):
    ea = int(row["entry"], 16)
    code = read_va(ea, row["size"] or 0)
    row["m0"] = row["m1"] = row["m2"] = 0
    row["m1_sites"] = []
    row["m2_sites"] = []
    if code:
        insns = list(md.disasm(code, ea))
        idx_by_addr = {ins.address: i for i, ins in enumerate(insns)}
        row["m0"] = scan_m0(insns, idx_by_addr)
        n1, s1 = scan_m1(insns, idx_by_addr, reasons)
        n2, s2 = scan_m2(insns, idx_by_addr, reasons)
        row["m1"], row["m2"] = n1, n2
        row["m1_sites"], row["m2_sites"] = s1, s2
    row["named"] = is_named(row["name"])
    # 可伪证分层：该行是否有"多值分派"站点（cmp r/slot, imm 且 imm ∉ {0,1,-1}）
    row["has_vd"] = any(is_value_dispatch(s[6]) for s in row["m1_sites"]) or \
        any(is_value_dispatch(s[6]) for s in row["m2_sites"])
    if row["m0"] or row["m1"] or row["m2"]:
        hits.append(row)
    if (idx + 1) % 2000 == 0:
        print("    ... %d/%d（命中 %d）" % (idx + 1, len(pool_rows), len(hits)), flush=True)

print("    完成: 池 %d 行，M0 %d / M1 %d / M2 %d / 并集 %d" % (
    len(pool_rows),
    sum(1 for r in pool_rows if r["m0"]),
    sum(1 for r in pool_rows if r["m1"]),
    sum(1 for r in pool_rows if r["m2"]),
    len(hits)))

# ---------------------------------------------------------------- 4. 与 SURVEY_3B2 对账
print("[3] 与 SURVEY_3B2 的 p3b2 对账", flush=True)
ref = {}
with open(SURVEY_TSV, encoding="utf-8") as f:
    rd = csv.reader(f, delimiter="\t")
    next(rd)
    for row in rd:
        ref[row[0]] = dict(n=int(row[1]), proved=int(row[3]), p3b2=int(row[5]),
                           p3b2_named=int(row[6]))
ref_hit_entries = set()
with open(HITS_TSV, encoding="utf-8") as f:
    rd = csv.reader(f, delimiter="\t")
    next(rd)
    for row in rd:
        ref_hit_entries.add(norm_entry(row[0]))

drift = []
for s in SUBS:
    mine_m0 = sum(1 for r in pool_rows if r["subsystem"] == s and r["m0"])
    if mine_m0 != ref[s]["p3b2"]:
        drift.append((s, mine_m0, ref[s]["p3b2"]))
    if st[s]["pool"] != ref[s]["n"] - ref[s]["proved"]:
        print("    !! pool 口径差异 %s: 本卡 %d vs 参考 n-proved %d"
              % (s, st[s]["pool"], ref[s]["n"] - ref[s]["proved"]))
print("    m0 与 p3b2 逐子系统对照: %s（差异 %d 处）"
      % ("PASS" if not drift else "FAIL", len(drift)))
for s, a, b in drift:
    print("      DRIFT %s: rescan m0=%d survey p3b2=%d" % (s, a, b))
mine_hit_entries = set(r["entry"] for r in pool_rows if r["m0"])
print("    命中 entry 集合对照: 交集 %d，仅本卡 %d，仅参考 %d" % (
    len(mine_hit_entries & ref_hit_entries),
    len(mine_hit_entries - ref_hit_entries),
    len(ref_hit_entries - mine_hit_entries)))

# --- 漂移对账：把"参考命中但今日已不在池内"的 entry 强行喂进同一个 M0 扫描器
#     若它们全部仍然命中，则 m0 与 p3b2 的差异**全部**来自池漂移（grade 升格），
#     而不是 M0 实现差异。这是本卡的核心可伪证断言。
drifted_out = sorted(ref_hit_entries - mine_hit_entries)
cov_by_entry = {}
for r in coverage:
    cov_by_entry.setdefault(r["entry"], []).append(r)
drift_rows = []
drift_still_hit = 0
for e in drifted_out:
    size = atlas.get(e, (0, 0))[0]
    code = read_va(int(e, 16), size or 0)
    n_valid = 0
    if code:
        insns = list(md.disasm(code, int(e, 16)))
        idx_by_addr = {ins.address: i for i, ins in enumerate(insns)}
        n_valid = scan_m0(insns, idx_by_addr)
    if n_valid:
        drift_still_hit += 1
    cr = cov_by_entry.get(e, [{}])[0]
    drift_rows.append((e, cr.get("subsystem", "?"), cr.get("name", ""),
                       cr.get("grade", "?"), n_valid))
print("    池漂移对账: 参考命中但今日不在池内 %d 行，其中同一 M0 扫描器仍命中 %d 行"
      % (len(drift_rows), drift_still_hit))
if drift_rows:
    out_drift = os.path.join(BASE, "_m0_drift.tsv")
    with open(out_drift, "w", encoding="utf-8", newline="") as f:
        f.write("entry\tsubsystem\tname\tgrade_today\tm0_n_valid_today\n")
        for t in drift_rows:
            f.write("%s\t%s\t%s\t%s\t%d\n" % t)
    print("    写出 %s（漂移明细，审计用）" % out_drift)

# 逐子系统三方对账: m0_today + promoted = p3b2 ?
promoted_by_sub = {}
for (e, s, nm, g, nv) in drift_rows:
    promoted_by_sub[s] = promoted_by_sub.get(s, 0) + (1 if nv else 0)
out_chk = os.path.join(BASE, "_m0_vs_p3b2.tsv")
recon_ok = True
with open(out_chk, "w", encoding="utf-8", newline="") as f:
    f.write("subsystem\tpool_today\tm0_today\tpromoted_out_of_pool\tm0_asof_survey\tp3b2\tdiff\n")
    for s in SUBS:
        m0_today = sum(1 for r in pool_rows if r["subsystem"] == s and r["m0"])
        pr = promoted_by_sub.get(s, 0)
        asof = m0_today + pr
        d = asof - ref[s]["p3b2"]
        if d != 0:
            recon_ok = False
        f.write("%s\t%d\t%d\t%d\t%d\t%d\t%d\n" % (
            s, st[s]["pool"], m0_today, pr, asof, ref[s]["p3b2"], d))
print("    m0 + 漂移出池 = p3b2（逐子系统）: %s" % ("PASS" if recon_ok else "FAIL"))
print("    写出 %s（对账明细）" % out_chk)

print("    M1 站点剔因: " + ", ".join("%s=%d" % (k[3:], v) for k, v in
                                      sorted(reasons.items()) if k.startswith("m1_")))
print("    M2 站点剔因: " + ", ".join("%s=%d" % (k[3:], v) for k, v in
                                      sorted(reasons.items()) if k.startswith("m2_")))

# ---------------------------------------------------------------- 5. 汇总
print("[4] 汇总与产出", flush=True)
agg = {}
for s in SUBS:
    rows_s = [r for r in pool_rows if r["subsystem"] == s]
    m0 = sum(1 for r in rows_s if r["m0"])
    m1 = sum(1 for r in rows_s if r["m1"])
    m2 = sum(1 for r in rows_s if r["m2"])
    uni_rows = [r for r in rows_s if r["m0"] or r["m1"] or r["m2"]]
    uni = len(uni_rows)
    new_rows = [r for r in uni_rows if not r["m0"]]
    agg[s] = dict(pool=len(rows_s), m0=m0, m1=m1, m2=m2, union=uni,
                  new=uni - m0, named_new=sum(1 for r in new_rows if r["named"]),
                  vd_new=sum(1 for r in new_rows if r["has_vd"]),
                  vd_new_named=sum(1 for r in new_rows if r["has_vd"] and r["named"]),
                  proved=st[s]["proved"], n=st[s]["n"],
                  delta_pct=((uni - m0) / m0 * 100.0) if m0 else 0.0)

out = os.path.join(BASE, "rescan.tsv")
with open(out, "w", encoding="utf-8", newline="") as f:
    f.write("subsystem\tpool\tm0\tm1\tm2\tm0m1m2_union\tnew_vs_1733\t"
            "named_in_new\tdelta_pct\n")
    for s in SUBS:
        a = agg[s]
        f.write("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.2f\n" % (
            s, a["pool"], a["m0"], a["m1"], a["m2"], a["union"], a["new"],
            a["named_new"], a["delta_pct"]))
print("    写出 %s（22 行）" % out)

# 附：站点级与样本候选（审计用，不属于卡片要求，留在同目录）
out_sites = os.path.join(BASE, "_m1m2_sites.tsv")
with open(out_sites, "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tname\tform\tcall_at\tmov_at\tcmp_at\twitness\tjcc_at\t"
            "jcc_target\tcmp_kind\tcmp_imm\tvalue_dispatch\n")
    for r in pool_rows:
        for form, sites in (("M1", r["m1_sites"]), ("M2", r["m2_sites"])):
            for (c, mv, cm, wit, jc, tgt, kim) in sites:
                kk, im = (kim if kim else ("", None))
                f.write("%s\t%s\t%s\t%s\t%08X\t%08X\t%08X\t%s\t%08X\t%s\t%s\t%s\t%s\n" % (
                    r["entry"], r["subsystem"], r["name"], form, c, mv, cm, wit, jc,
                    ("%08X" % tgt) if tgt is not None else "OUT_OF_BODY",
                    kk, ("REG" if im is None else "%d" % im),
                    "1" if is_value_dispatch(kim) else "0"))
print("    写出 %s（站点明细）" % out_sites)

# 附：逐行审计（含 m0/m1/m2 标志，供抽样复现）
out_rows = os.path.join(BASE, "_rows.tsv")
with open(out_rows, "w", encoding="utf-8", newline="") as f:
    f.write("entry\tsubsystem\tname\tgrade\tsize\tm0_sites\tm1_sites\tm2_sites\t"
            "hit_any\tnew_vs_m0\tnamed\n")
    for r in pool_rows:
        u = 1 if (r["m0"] or r["m1"] or r["m2"]) else 0
        f.write("%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\n" % (
            r["entry"], r["subsystem"], r["name"], r["grade"], r["size"],
            r["m0"], r["m1"], r["m2"], u, (1 if (u and not r["m0"]) else 0),
            "1" if r["named"] else "0"))
print("    写出 %s（逐行标志，审计用）" % out_rows)

# 可伪证分层审计（不属于卡面 9 列，单独出表，防"用量代质"）
out_vd = os.path.join(BASE, "_falsifiable_layer.tsv")
with open(out_vd, "w", encoding="utf-8", newline="") as f:
    f.write("subsystem\tpool\tm0\tunion\tnew\tnew_named\tnew_value_dispatch\t"
            "new_vd_named\tnew_bool_or_sentinel\n")
    for s in SUBS:
        a = agg[s]
        f.write("%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" % (
            s, a["pool"], a["m0"], a["union"], a["new"], a["named_new"],
            a["vd_new"], a["vd_new_named"], a["new"] - a["vd_new"]))
print("    写出 %s（可伪证分层：多值分派 vs 布尔/哨兵）" % out_vd)

# ---------------------------------------------------------------- 6. 摘要
tot = dict(pool=0, m0=0, m1=0, m2=0, union=0, new=0, named_new=0,
           vd_new=0, vd_new_named=0)
for s in SUBS:
    for k in tot:
        tot[k] += agg[s][k]
print("\n=== 摘要 ===")
print("%-4s %6s %5s %5s %5s %7s %6s %6s %8s  %s" % (
    "S", "pool", "m0", "m1", "m2", "union", "new", "named", "delta%", "proved/门槛"))
for s in SUBS:
    a = agg[s]
    thr = math.ceil(0.5 * a["n"])
    after = a["proved"] + a["m0"] + a["named_new"]
    print("%-4s %6d %5d %5d %5d %7d %6d %6d %8.2f  %d/%d %s" % (
        s, a["pool"], a["m0"], a["m1"], a["m2"], a["union"], a["new"],
        a["named_new"], a["delta_pct"], a["proved"], thr,
        "可闭" if after >= thr else "不可闭"))
print("TOTAL pool=%d m0=%d m1=%d m2=%d union=%d new=%d named_new=%d"
      % (tot["pool"], tot["m0"], tot["m1"], tot["m2"], tot["union"], tot["new"],
         tot["named_new"]))
print("      新增中多值分派形态 %d 行（其中具名 %d 行）；其余 %d 行为布尔/哨兵比较"
      % (tot["vd_new"], tot["vd_new_named"], tot["new"] - tot["vd_new"]))
