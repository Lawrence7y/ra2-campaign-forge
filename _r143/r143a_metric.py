#!/usr/bin/env python3
"""R143 A1: .text 全段（流式，64KB 分块，capstone lite；仅对命中点开 detail）
取证两件事，都为 vt==[esi] 对象模型这条未取得项服务：
  1) 虚调用惯用法 mov rX,[rY]; call/jmp [rX+4k] 的四定义敏感度 + objdump 起点集交叉验证
  2) .text 内对 [rX + 0]（offset 0）的立即数写普查，按 imm 是否落「虚表地址集合」分类
严禁对整段 .text 开 detail=True；脚本自带 timeout 由外部施加。
"""
import struct, json, subprocess, sys, re, collections
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

P = 'ra2bench/gamemd.exe'
data = open(P, 'rb').read(); N = len(data)
pe = pefile.PE(P, fast_load=True); IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
TEXT = [s for s in secs if s[0] == '.text'][0]
TEXT_LO = IB + TEXT[1]; TEXT_RSZ = TEXT[4]; TEXT_RAW = TEXT[3]; TEXT_HI = TEXT_LO + TEXT[2]

def va2off(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs):
            d = va - lo
            return raw + d if d < rs else None
    return None

def rd(va, l):
    o = va2off(va)
    if o is None or o + l > N: return None
    return data[o:o + l]

def dw(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]

def sec_of(va):
    for nm, ava, vs, raw, rs in secs:
        lo = IB + ava
        if lo <= va < lo + max(vs, rs): return nm
    return None

md_l = Cs(CS_ARCH_X86, CS_MODE_32)          # lite，全程复用
md_d = Cs(CS_ARCH_X86, CS_MODE_32); md_d.detail = True

def stream_text():
    """流式线性扫描 .text；返回 (va, size, mnemonic, op_str)。跨块尾指令重读。"""
    off = TEXT_RAW
    end = TEXT_RAW + TEXT_RSZ
    va = TEXT_LO
    carry = 0
    while off < end:
        chunk = data[off:min(off + 65536, end)]
        base = IB + (TEXT[1] + (off - TEXT_RAW))
        consumed = 0
        for a, sz, mn, op in md_l.disasm_lite(chunk, base):
            if a - base + sz > len(chunk):
                break
            consumed = a - base + sz
            yield a, sz, mn, op
        if consumed == 0:
            off += 1        # 无法解码：单字节步进，保持不丢
        else:
            off += consumed

def one(va):
    b = rd(va, 16)
    if b is None: return None
    for i in md_d.disasm(b, va):
        return i
    return None

# ---------------- 虚表地址集合（与 R140/r140n 同法重算） ----------------
pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings = []
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        for m in pat.finditer(data[raw:raw + rs]):
            strings.append((IB + ava + m.start(), m.group()))
def indata(va): return sec_of(va) in ('.data', '.rdata')
TDs = {s - 8: g for s, g in strings if dw(s - 8) is not None and dw(s - 4) == 0 and indata(dw(s - 8))}
tdset = set(TDs)
cand = set()
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in tdset:
                c = IB + ava + i * 4 - 12
                if dw(c) == 0 and dw(c + 12) == v:
                    cand.add(c)
COL = {c for c in cand if dw(c + 16) != 0}
vtset = set(); vt_list = []
for nm, ava, vs, raw, rs in secs:
    if nm in ('.data', '.rdata'):
        blob = data[raw:raw + rs]
        for i in range(len(blob) // 4):
            v = struct.unpack_from('<I', blob, i * 4)[0]
            if v in COL:
                vt = IB + ava + i * 4 + 4
                if dw(vt - 4) == v:
                    vtset.add(vt); vt_list.append(vt)
td_ok = sum(1 for t in vtset if dw(t - 4) in COL)

# ---------------- 单遍扫描：惯用法 + col0 立即数写 ----------------
GEN = {'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi'}
last_def = {}          # reg -> ('load', src_reg, disp, va) | ('other', va)
idiom = []             # 同寄存器数据流命中
callsites = []         # 所有 call/jmp [reg+disp]
col0_stores = []       # mov dword [reg + 0], imm32
n_ins = 0
starts_missing = 0
for a, sz, mn, op in stream_text():
    n_ins += 1
    # 解析目标寄存器写入（lite 文本级）
    if op:
        op = re.sub(r'\s*([+,])\s*', r'\1', op)
        head, _, rest = op.partition(',')
        dst = head.strip()
        if dst in GEN:                       # 写通用寄存器
            if mn == 'mov' and rest.strip().startswith('dword ptr ['):
                inner = rest[rest.index('[') + 1:rest.index(']')]
                src = inner.split('+')[0].split('-')[0].strip()
                last_def[dst] = ('load', src, inner, a)
            else:
                last_def[dst] = ('other', a)
    if mn == 'mov' and op and ', dword ptr [' in op:
        # col0 立即数写: mov dword ptr [rX], imm32  (disp 必须为 0)
        m2 = re.match(r'^dword ptr \[([a-z0-9]+)\](?:, ?(0x[0-9a-f]+|-?\d+))?$', op)
        if m2:
            imm = m2.group(2)
            if imm is not None:
                iv = int(imm, 16) if imm.startswith('0x') else int(imm)
                col0_stores.append((a, m2.group(1), iv & 0xFFFFFFFF))
    if mn in ('call', 'jmp'):
        m3 = re.match(r'^dword ptr \[([a-z0-9]+)(\+0x[0-9a-f]+|-\d+)?\]$', op)
        if m3:
            reg = m3.group(1); disp = m3.group(2)
            callsites.append((a, mn, reg, disp))
            ld = last_def.get(reg)
            if ld and ld[0] == 'load':
                idiom.append({'va': a, 'mn': mn, 'reg': reg, 'disp': disp,
                              'load_va': ld[3], 'load_src': ld[1], 'load_mem': ld[2]})

# ---------------- objdump 起点集交叉验证 ----------------
try:
    starts = set(int(x,16) for x in open('_r140/obj_starts.txt').read().split())
    SRC = '_r140/obj_starts.txt'
except Exception as e:
    starts = set(); SRC = 'UNAVAILABLE %s' % e

def cls_starts(seq):
    return sum(1 for v in seq if v in starts)

# ---------------- 分类 ----------------
col0_vt = [s for s in col0_stores if s[2] in vtset]
def in_text_range(x): return TEXT_LO <= x < TEXT_HI
col0_text = [s for s in col0_stores if (s[2] not in vtset) and in_text_range(s[2])]
col0_zero = [s for s in col0_stores if s[2] == 0]
col0_other = [s for s in col0_stores if s[2] not in vtset and not in_text_range(s[2]) and s[2] != 0]

idiom_disp = collections.Counter(s['disp'] for s in idiom)
res = {
    'exe_sha256': subprocess.run(['sha256sum', P], capture_output=True, text=True).stdout.split()[0],
    'exe_bytes': N,
    'instructions': n_ins,
    'td': len(TDs), 'col': len(COL), 'vt_distinct': len(vtset), 'vt_occurrences': len(vt_list),
    'vt_with_col_backref': td_ok,
    'callsites_mem_indirect': len(callsites),
    'idiom_same_reg': len(idiom),
    'idiom_mn': dict(collections.Counter(s['mn'] for s in idiom)),
    'idiom_reg_load_is_base': dict(collections.Counter(s['load_src'] for s in idiom)),
    'idiom_disp_is4k': sum(1 for s in idiom if s['disp'] is None or s['disp'] == ''),
    'idiom_disp4_mult': sum(1 for s in idiom if s['disp'] and re.match(r'^\+0x[0-9a-f]+$', s['disp']) and int(s['disp'][3:], 16) % 4 == 0),
    'idiom_disp_top': idiom_disp.most_common(12),
    'idiom_in_starts': cls_starts([s['va'] for s in idiom]),
    'idiom_load_in_starts': cls_starts([s['load_va'] for s in idiom]),
    'col0_stores': len(col0_stores),
    'col0_imm_in_vtset': len(col0_vt),
    'col0_imm_text': len(col0_text),
    'col0_imm_zero': len(col0_zero),
    'col0_imm_other': len(col0_other),
    'col0_distinct_vt_installed': len({s[2] for s in col0_vt}),
    'col0_other_sample': [hex(s[2]) for s in col0_other[:15]],
    'col0_vt_sample': [(hex(s[0]), hex(s[2])) for s in col0_vt[:10]],
    'starts_src': SRC, 'starts_n': len(starts),
    'ins_in_starts': cls_starts([a for a, sz, mn, op in md_l.disasm_lite(data[TEXT_RAW:TEXT_RAW+65536], TEXT_LO)]),
}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('_r143/r143a_metric.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'idiom': idiom[:200], 'col0_vt': col0_vt[:200]}, open('_r143/r143a_samples.json', 'w'), ensure_ascii=False, indent=1)
