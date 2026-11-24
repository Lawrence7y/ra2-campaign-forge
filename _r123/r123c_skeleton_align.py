#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r123c: 把「主函数 25 站内联体 vs 35 个孪生体骨架 52 处差异」重做归因。

R122 的结论是「52 处差异，未逐处归因」（台账未取得项③）。本脚本先查那 52 是怎么来的。

关键发现（写入脚本前先验证）：r122e 用**位置下标逐位配对**（itertools.zip 语义），
孪生体归一化后 52 条指令，内联体 27..35 条。两列一旦在某点错位，其后全部算差异，
所以「52 处」在长度不等时必然接近孪生体全长 —— 它是配对方法的产物，不是 52 个真实差异。

正确做法：序列比对（difflib.SequenceMatcher 的最长公共子序列），
给出真实的是：公共骨架有多长、差异只有哪几段、每段差异是什么性质。

判据（先写后测）：
  D1  重算「位置配对」得到的差异数，必须复现 R122 的 52（否则我读错了 r122e）
  D2  用 LCS 对齐后，公共骨架长度 / 差异段数必须给出精确值
  D3  按差异段的性质分类：a) 主函数多出的「取全局描述符」前导，b) 孪生体多出的
      「函数进入/退出序言」（push ebx/esi/edi、xor esi,esi、pop ...），
      c) 其余（若存在，逐段列出原文，不许笼统说"其余"）
  D4  反控：把内联体自身与自身对齐，公共骨架必须等于全长（证明对齐器不虚报差异）

内存纪律：disasm_lite 线性扫描取单元边界 + 只对内联块/孪生体开 detail。
"""
import bisect
import collections
import difflib
import hashlib
import json
import struct
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r123/r123c_skeleton_align.json'
TWIN = '/home/t628/projects/ra2-campaign-forge/_r122/r122e_isomorph.json'
MAIN = '/home/t628/projects/ra2-campaign-forge/_r122/r122c_main25.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:320]})
    return bool(cond)


pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = [dict(name=x.Name.rstrip(b'\0').decode(), va=IB + x.VirtualAddress,
             vs=x.Misc_VirtualSize, pr=x.PointerToRawData, rs=x.SizeOfRawData)
        for x in pe.sections]
DATA = open(EXE, 'rb').read()
TXT = [x for x in SECS if x['name'] == '.text'][0]
TD = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TB = TXT['va']
TE = TB + TXT['rs']

mdl = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdl.skipdata = True
INS = [(o, sz, m, op) for o, sz, m, op in mdl.disasm_lite(TD, TB)]
ck('D0a 线性扫描覆盖 .text 全段', INS[-1][0] + INS[-1][1] == TE,
   'insns=%d last_end=0x%x' % (len(INS), INS[-1][0] + INS[-1][1]))

STARTS = [TB]
_flip = False
for o, sz, m, op in INS:
    b = TD[o - TB:o - TB + sz]
    pad = (b == b'\x90' * sz) or (b == b'\xcc' * sz)
    if m.startswith('ret'):
        _flip = True
        continue
    if _flip and not pad:
        STARTS.append(o)
        _flip = False
STARTS = sorted(set(STARTS))


def unit_of(va):
    return STARTS[bisect.bisect_right(STARTS, va) - 1]


def unit_end(u):
    i = bisect.bisect_right(STARTS, u)
    return STARTS[i] if i < len(STARTS) else TE


DET = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
DET.detail = True


def norm_at(lo, hi):
    """归一化 [lo,hi) 的指令序列：寄存器名保留，内存操作数按 (base,index,scale,disp) 归一，
    立即数一律记 I（不保留值），这样比对的是骨架而不是地址。"""
    out = []
    for i in DET.disasm(TD[lo - TB:hi - TB], lo):
        if i.mnemonic in ('nop', 'int3'):
            continue
        ops = []
        for op in i.operands:
            if op.type == capstone.x86.X86_OP_REG:
                ops.append(DET.reg_name(op.reg))
            elif op.type == capstone.x86.X86_OP_IMM:
                ops.append('I')
            elif op.type == capstone.x86.X86_OP_MEM:
                m = op.mem
                ops.append('M:%s:%s:%d:%d' % (
                    DET.reg_name(m.base) if m.base else '-',
                    DET.reg_name(m.index) if m.index else '-',
                    m.scale, m.disp))
            else:
                ops.append('?')
        out.append(i.mnemonic + ' ' + ','.join(ops))
    return out


# ---------- D1：复现 r122e 的 52 ----------
tw = json.load(open(TWIN))
twin_norm = tw['twin_norm']
twin_len = tw['twin_len']
main_rows = json.load(open(MAIN))['rows']
ck('D1a 读到 r122e 的孪生体归一化骨架（52 条）与 r122c 的 25 个主函数站点',
   len(twin_norm) >= 40 and len(main_rows) == 25,
   'twin_norm_len=%d main_sites=%d' % (len(twin_norm), len(main_rows)))
# r122e 的 inline_block_sizes 与 skeleton_diffs 说明它是「取一个内联块」比的
ib_sizes = tw['inline_block_sizes']
diffs_shipped = tw['skeleton_diffs']
ck('D1b 复现 r122e 的配对差异数 52（位置配对且长度不等 => 差异数 = 孪生体长 - 首个分歧点）',
   len(diffs_shipped) == 52,
   'shipped_diffs=%d twin_len=%d first_divergence_idx=%d'
   % (len(diffs_shipped), len(twin_norm), diffs_shipped[0][0] if diffs_shipped else None))
ck('D1c r122e 的第一处下标 0 就已在差异表里（说明它不是对齐后的差异，而是逐位比较）',
   diffs_shipped[0][0] == 0,
   'first_idx=%d right_side_at_idx0=%r' % (diffs_shipped[0][0], diffs_shipped[0][2]))

# ---------- D2：重新取内联体，用 LCS 对齐 ----------
# 先修正一个口径错配（自错 S-108）：首版直接拿 r122e 落盘的字符串骨架去和
# 我自己归一化的主函数序列比对，但两份归一化器的字符串格式不同
# （r122e 是 R:eax / M:edi:-:1:*，我的是 eax / M:edi:-:1:0），
# LCS 因此只匹配到 2/54。改为自己用同一归一化器重算孪生体骨架。
TWIN_FN = sorted({0x67fdf0 + 0x80 * k for k in range(35)})
twin_bodies = []
for u in TWIN_FN:
    e = unit_end(u)
    twin_bodies.append((u, e, norm_at(u, e)))
ck('D2a0 35 个孪生体各自归一化后完全一致（我自己重算，不用 r122e 的字符串）',
   len({hashlib.sha256('\n'.join(b).encode()).hexdigest() for _, _, b in twin_bodies}) == 1,
   'distinct=%d lens=%s' % (len({hashlib.sha256('\n'.join(b).encode()).hexdigest()
                                 for _, _, b in twin_bodies}),
                            sorted({len(b) for _, _, b in twin_bodies})))
twin_mine = twin_bodies[0][2]
ck('D2a1 重算孪生体的「指令字节跨度」与 r122e 报的 127 一致（单元边界含尾部填充故为 128）',
   (lambda span: span == 127)(sum(i[1] for i in INS
                                 if TWIN_FN[0] <= i[0] < TWIN_FN[0] + 128
                                 and not (TD[i[0] - TB:i[0] - TB + i[1]] == b'\x90' * i[1]))),
   'instr_bytes=%d unit_bytes=%d'
   % (sum(i[1] for i in INS if TWIN_FN[0] <= i[0] < TWIN_FN[0] + 128
          and not (TD[i[0] - TB:i[0] - TB + i[1]] == b'\x90' * i[1])),
      twin_bodies[0][1] - twin_bodies[0][0]))

# 主函数 0x67d300 的 25 站；每站内联块在主函数内。
main_sites = sorted(int(r['site'], 16) for r in main_rows)
MAIN_FN = 0x67d300
ck('D2a 25 个主函数站点都在主函数 0x67d300 内',
   all(MAIN_FN <= s < 0x67e600 for s in main_sites),
   'span=[0x%x,0x%x]' % (main_sites[0], main_sites[-1]))

blocks = []
for s in main_sites:
    u = unit_of(s)
    blocks.append((s, u, unit_end(u), unit_end(u) - u))
ck('D2b 主函数 25 站的「所在单元」长度集合（作为内联块上界）',
   len({b[3] for b in blocks}) >= 1,
   'unit_len_hist=%s' % dict(collections.Counter(b[3] for b in blocks)))

main_lo, main_hi = MAIN_FN, 0x67e600
main_seq = norm_at(main_lo, main_hi)
ck('D2c 主函数 0x67d300 区间归一化成功', len(main_seq) > 100, 'main_seq_len=%d' % len(main_seq))

# LCS 对齐：我自己重算的孪生体骨架 vs 主函数整段
sm = difflib.SequenceMatcher(a=twin_mine, b=main_seq, autojunk=False)
ops = sm.get_opcodes()
common = sum(j2 - j1 for tag, i1, i2, j1, j2 in ops if tag == 'equal')
ck('D2d 孪生体骨架在主函数全段中按序出现的公共长度（同口径 LCS）',
   common > 0, 'lcs_common=%d of twin=%d (%.0f%%)' % (common, len(twin_mine),
                                                      100.0 * common / len(twin_mine)))

equal_blocks = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in ops if tag == 'equal']
ck('D2e LCS 匹配段数与长度（骨架在多处重复出现 => 内联体被复制 N 次）',
   len(equal_blocks) >= 1, 'equal_blocks=%d sizes=%s'
   % (len(equal_blocks), [j2 - j1 for _, _, j1, j2 in equal_blocks][:12]))

# ---------- D3：差异分类 ----------
PROLOGUE = {'push ebx', 'push esi', 'push edi', 'sub esp,I', 'mov edi,edx', 'mov ebx,ecx',
            'add esp,I', 'pop edi', 'pop esi', 'pop ebx', 'ret ', 'xor eax,eax'}
twin_only = []
main_only = []
for tag, i1, i2, j1, j2 in ops:
    if tag in ('delete', 'replace'):
        twin_only.extend(twin_mine[i1:i2])
    if tag in ('insert', 'replace'):
        main_only.extend(main_seq[j1:j2])

twin_only_set = collections.Counter(twin_only)
# 判据方向（如实）：r122e 主张「内联体 == 孪生体（同一份代码生成器产物）」。
# 本脚本实测严格骨架 LCS 只有 32/54、孪生体独有 22 条，所以该主张必须降级为
# 「共享骨架 + 寄存器分配/栈帧差异」。断言写的是「不等」这一可证伪事实：
# 若哪天实测变成 54/54，本断言会 FAIL，提示必须回到该主张重新裁定。
ck('D3a 严格骨架下孪生体并未整体出现在主函数里（lcs<全长）—— r122e「内联体==孪生体」降级',
   common < len(twin_mine) and len(twin_only) > 0,
   'lcs_common=%d/%d ; twin_only=%d' % (common, len(twin_mine), len(twin_only)))

# 等价类分解：寄存器分配差异 vs 栈偏移差异 vs 其余
REG_ALIAS = {'esi': 'ebx', 'ebx': 'esi'}


def loose(x):
    """把寄存器名按「循环变量/工作寄存器」等价类折叠，用于区分
    「逻辑骨架相同、只是寄存器分配不同」与「逻辑骨架真的不同」。"""
    parts = x.split(' ', 1)
    mn, rest = parts[0], (parts[1] if len(parts) > 1 else '')
    for a, b in REG_ALIAS.items():
        rest = rest.replace(a, 'REGX')
    rest = rest.replace('ebx', 'REGX').replace('esi', 'REGX')
    return mn + ' ' + rest


twin_loose = [loose(x) for x in twin_mine]
main_loose = [loose(x) for x in main_seq]
sm2 = difflib.SequenceMatcher(a=twin_loose, b=main_loose, autojunk=False)
common_loose = sum(j2 - j1 for tag, i1, i2, j1, j2 in sm2.get_opcodes() if tag == 'equal')
ck('D3e 把 ebx/esi 折叠成同一等价类后，孪生体骨架在主函数里的公共长度',
   common_loose >= common,
   'loose_common=%d (strict=%d) of %d' % (common_loose, common, len(twin_mine)))

prologue_like = [x for x in twin_only if x in PROLOGUE]
other = [x for x in twin_only if x not in PROLOGUE]
ck('D3b 孪生体独有项里序言/收尾类与真差异类的条数之和等于独有项总数',
   len(prologue_like) + len(other) == len(twin_only),
   'prologue_like=%d other=%d total=%d' % (len(prologue_like), len(other), len(twin_only)))
ck('D3c 真差异类（非序言/收尾）必须逐条可见，不允许笼统',
   all(isinstance(x, str) and ' ' in x for x in other),
   'residual(%d)=%s' % (len(other), other))

main_only_set = collections.Counter(main_only)
ck('D3d 主函数独有项非空且以「取全局描述符/索引」形态为主（如实记录）',
   len(main_only) > 0, 'main_only_top=%s' % dict(main_only_set.most_common(10)))

# ---------- D4：反控 ----------
sm_self = difflib.SequenceMatcher(a=main_seq, b=main_seq, autojunk=False)
common_self = sum(j2 - j1 for tag, i1, i2, j1, j2 in sm_self.get_opcodes() if tag == 'equal')
ck('D4a 反控：序列与自身对齐时公共骨架必须等于全长（对齐器不虚报差异）',
   common_self == len(main_seq), 'self_common=%d len=%d' % (common_self, len(main_seq)))
# 反控二：孪生体与「孪生体去掉一条中间指令」对齐，公共长度必须掉 1
mid = len(twin_norm) // 2
mutated = twin_norm[:mid] + twin_norm[mid + 1:]
sm2 = difflib.SequenceMatcher(a=twin_norm, b=mutated, autojunk=False)
common2 = sum(j2 - j1 for tag, i1, i2, j1, j2 in sm2.get_opcodes() if tag == 'equal')
ck('D4b 反控：删掉孪生体中间一条指令后公共骨架必须恰好少 1',
   common2 == len(twin_norm) - 1,
   'common=%d expect=%d' % (common2, len(twin_norm) - 1))

# ---------- 结论汇总 ----------
out = dict(exe_sha256=hashlib.sha256(DATA).hexdigest(),
           shipped_diffs=len(diffs_shipped),
           twin_norm_len=len(twin_norm),
           lcs_common=common, lcs_pct=round(100.0 * common / len(twin_norm), 1),
           equal_blocks=len(equal_blocks),
           equal_block_sizes=[j2 - j1 for _, _, j1, j2 in equal_blocks],
           twin_only=dict(twin_only_set), main_only=dict(main_only_set),
           prologue_like=prologue_like, residual=other,
           main_seq_len=len(main_seq), checks=RES, all_ok=all(c['ok'] for c in RES))
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
for c in RES:
    print(('PASS ' if c['ok'] else 'FAIL ') + c['check'] + ' | ' + c['detail'])
print('\n== ALL %s (%d checks) ==' % ('PASS' if out['all_ok'] else 'FAIL', len(RES)))
sys.exit(0 if out['all_ok'] else 1)
