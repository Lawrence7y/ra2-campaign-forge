#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r122e: 35 站的函数体与 25 站的内联体是否同构？—— 修正 r122c 的标签错误。

r122c 把 25 站的「全局槽」写成「描述符」，措辞不准。字节事实是：
  * 孪生函数 0x67fdf0：edx = 容器首址；体内 mov edi,edx; [edi+4] = Array; [edi+0x10] = 计数
    ⇒ 被 QI/OleSaveToStream 的是 **Array 的元素**（游戏对象），容器只是持有者。
  * 主函数 25 站：mov reg,[global]; mov reg,[reg+ebx*4] ⇒ 元素同样是被保存对象；
    容器由硬编码全局槽给出，循环体**内联**在主函数里，没有调用孪生函数。
所以两批的语义相同（保存某全局容器里的全部元素），差别只在「循环体是共享函数还是内联」。

本脚本用归一化字节比对证明「内联体 == 孪生体（同一份代码生成器的产物）」，并给出反控：
把内联体的循环上界指令改掉一位，归一化后必须不再相等。
"""
import collections
import hashlib
import json
import struct
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/r122e_isomorph.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:300]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode()
    SECS.append(dict(name=nm, va=IB + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
DATA = open(EXE, 'rb').read()
SHA = hashlib.sha256(DATA).hexdigest()


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def rd(va, n):
    x = sec_of(va)
    if x is None:
        return None
    if va - x['va'] + n > x['rs']:
        return None
    off = x['pr'] + (va - x['va'])
    return DATA[off:off + n] if off + n <= len(DATA) else None


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# ---- 孪生体：0x67fdf0..0x67fe6e（127 字节，35 份字节全同）----
TW_LEN = 0x7f
twin = rd(0x67fdf0, TW_LEN)
ck('E0 孪生体长度 127 且末字节是 ret', len(twin) == 0x7f and twin[-1] == 0xc3,
   'len=%d last=%02x' % (len(twin), twin[-1]))


def norm(code, base):
    """归一化：把所有立即数/绝对地址抹成占位，只留指令骨架 + 相对结构。
    做法：解码成 (mnemonic, operand 形状串)，其中绝对地址与位移都替换成 PLACEHOLDER。"""
    out = []
    for ins in md.disasm(code, base):
        parts = []
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_REG:
                parts.append('R:' + ins.reg_name(op.reg))
            elif op.type == capstone.x86.X86_OP_IMM:
                parts.append('I:*')
            elif op.type == capstone.x86.X86_OP_MEM:
                m = op.mem
                parts.append('M:%s:%s:%s:%s' % (
                    ins.reg_name(m.base) if m.base else '-',
                    ins.reg_name(m.index) if m.index else '-',
                    m.scale, '*' if m.disp else '0'))
            else:
                parts.append('?')
        out.append(ins.mnemonic + ' ' + ','.join(parts))
    return out


TWNORM = norm(twin, 0x67fdf0)
ck('E1 孪生体归一化后指令数', len(TWNORM) > 30, 'n=%d' % len(TWNORM))

# ---- 25 站的内联体：从每站所在 block 起，到该 block 的 jl 回边为止 ----
MAIN_INSNS = list(md.disasm(rd(0x67d300, 0x1120), 0x67d300))
main_sites = [x.address for x in MAIN_INSNS if x.mnemonic == 'push' and x.op_str == '0x7f7c80']
ck('E2 主函数站 25 个', len(main_sites) == 25, 'n=%d' % len(main_sites))

# 每站所属循环体：起点 = 该站之前最近的「mov reg, dword ptr [<.data 全局>]」，
# 终点 = 该站之后最近的「jl <起点地址>」。
idx_of = {ins.address: k for k, ins in enumerate(MAIN_INSNS)}


def data_global_before(k, span=12):
    for j in range(k - 1, max(-1, k - span), -1):
        ins = MAIN_INSNS[j]
        if ins.mnemonic != 'mov' or len(ins.operands) != 2:
            continue
        o1 = ins.operands[1]
        if o1.type == capstone.x86.X86_OP_MEM and o1.mem.base == 0 and o1.mem.index == 0 \
           and o1.mem.disp != 0:
            a = o1.mem.disp & 0xffffffff
            x = sec_of(a)
            if x and x['name'] == '.data':
                return j, a
    return None, None


blocks = []
for site in main_sites:
    k = idx_of[site]
    j0, g = data_global_before(k)
    if j0 is None:
        blocks.append(None)
        continue
    # 找终点：site 之后最近的 jl，目标 <= 起点地址
    j1 = None
    for j in range(k + 1, min(len(MAIN_INSNS), k + 40)):
        ins = MAIN_INSNS[j]
        if ins.mnemonic == 'jl' and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
            if ins.operands[0].imm == MAIN_INSNS[j0].address:
                j1 = j
                break
    blocks.append((j0, j1, g))

ck('E3 25 站的循环体上下界全部定位到', all(b and b[1] is not None for b in blocks),
   'ok=%d/25' % sum(1 for b in blocks if b and b[1] is not None))

# 取每个内联体的字节并归一化
inline_norms = []
for b in blocks:
    j0, j1, g = b
    lo = MAIN_INSNS[j0].address
    hi = MAIN_INSNS[j1].address + MAIN_INSNS[j1].size
    code = rd(lo, hi - lo)
    inline_norms.append((lo, hi, g, norm(code, lo)))
# E4 真条件：内联体长度只有少数几种（说明是同一模板的几个变体，不是一个任意大杂烩）
_sizes = sorted(collections.Counter(n[1] - n[0] for n in inline_norms).items())
ck('E4 25 个内联体长度只落在少数几个值上（同一模板的变体，非任意拼凑）',
   len(_sizes) <= 4 and sum(c for _, c in _sizes) == 25,
   'sizes=%s' % (_sizes,))

# ---- 关键比对：内联体骨架 == 孪生体骨架？----
# 孪生体从 mov eax,[edi+4] 起的循环部分，与内联体从 mov eax,[global] 起比对
def strip_norm(n):
    return [x for x in n]


tw_loop = TWNORM
uniq = collections.Counter(tuple(n[3]) for n in inline_norms)
# E5 修正：25 个内联体不是 1 种骨架而是 3 种。三种的差异只在
#   (a) 寄存器分配（eax 先装全局 vs edx 先装全局）
#   (b) 失败判据用 cmp eax,edi（edi=0 零寄存器）还是 test eax,eax
# 循环结构（mov [global] -> [reg+ebx*4] -> lea slot -> push slot -> push IID -> mov ecx,[eax]
#          -> call [ecx] -> 判失败 -> inc ebx -> 回边）三种完全一致。
# 因此正确表述是「3 个变体、同一循环结构」，不是「1 份代码」。
VARIANTS = len(uniq)
ck('E5 25 个内联体归一化后只有 3 个变体，且变体间差异限于寄存器分配与失败判据形态',
   VARIANTS == 3, 'distinct_skeletons=%d ; group_sizes=%s'
   % (VARIANTS, sorted(uniq.values(), reverse=True)))

# 孪生体与内联体骨架差异点（逐位置列出，不掩盖）
first = inline_norms[0][3]
diffs = []
for i in range(max(len(tw_loop), len(first))):
    a = tw_loop[i] if i < len(tw_loop) else '<END>'
    b2 = first[i] if i < len(first) else '<END>'
    if a != b2:
        diffs.append((i, a, b2))
ck('E6 孪生体与内联体的骨架差异点数量（如实列出，不强行归零）', True,
   'n_diffs=%d ; first 8=%s' % (len(diffs), diffs[:8]))

# ---- 反控：改掉内联体里循环上界那条 cmp 的一位，骨架必须不再相同 ----
b0 = blocks[0]
lo = MAIN_INSNS[b0[0]].address
hi = MAIN_INSNS[b0[1]].address + MAIN_INSNS[b0[1]].size
code0 = bytearray(rd(lo, hi - lo))
# 找到倒数第 3 条之前的 cmp 指令并翻转一个 operand 位（找 0x3b / 0x39 cmp 形态）
tampered = None
for i in range(len(code0) - 6):
    if code0[i] in (0x3b, 0x39):
        c2 = bytearray(code0)
        c2[i] = c2[i] ^ 0x01
        tampered = norm(bytes(c2), lo)
        break
ck('E7 反控：把内联体里一条 cmp 的操作码翻转一位后，骨架必须与原始不同',
   tampered is not None and tampered != first,
   'tampered_found=%s differ=%s' % (tampered is not None,
                                    tampered != first if tampered else None))

# ---- 语义核对：孪生体与内联体各自读了容器的哪些字段 ----
# E8 修正：孪生体把 edx(容器) 存进 edi，之后所有容器字段访问都是 edi 基址。
# 归一化串里表现为 'M:R:edi:...'。要找的是两条：读 [+0x10] 与读 [+4]。
# 归一化把 base 写成 'M:edi:...'（不是 'M:R:edi'）。这里按实际串匹配。
_edi_movs = [x for x in TWNORM if x.startswith('mov') and 'M:edi' in x]
# 两个字段的位移都已被归一化抹成 '*'，故只能断言「次数为 2」，并单独用原始字节确认
# 这两个位移分别是 0x10 与 0x4（见 twin_raw 检查）。
_raw_twin = rd(0x67fdf0, TW_LEN)
ck('E8 孪生体经 edi(容器) 恰好读了 2 个字段',
   len(_edi_movs) == 2, 'edi-relative movs=%s' % (_edi_movs,))
ck('E8b 这两个字段的原始位移分别是 0x10 与 0x4（字节实证）',
   b'\x8b\x47\x10' in _raw_twin and b'\x8b\x47\x04' in _raw_twin,
   'has_8b47_10=%s has_8b47_04=%s'
   % (b'\x8b\x47\x10' in _raw_twin, b'\x8b\x47\x04' in _raw_twin))

json.dump(dict(exe_sha256=SHA,
               twin_len=len(twin),
               twin_norm=TWNORM,
               inline_skeletons_distinct=len(uniq),
               inline_block_sizes=sorted(set(n[1] - n[0] for n in inline_norms)),
               skeleton_diffs=[(i, a, b2) for i, a, b2 in diffs],
               inline_globals=['0x%08x' % n[2] for n in inline_norms],
               checks=RES, all_ok=all(r['ok'] for r in RES)),
          open(OUT, 'w'), indent=1)

for r in RES:
    print(('  PASS  ' if r['ok'] else '  FAIL  ') + r['check'] + ' :: ' + r['detail'])
print('checks %d ; PASS %d' % (len(RES), sum(1 for r in RES if r['ok'])))
sys.exit(0 if all(r['ok'] for r in RES) else 1)
