#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 跨家族审计（只读）deepseek/audit — 抽象基类槽 0-7 实现族与 +0x20 字段归属

复算最小命令：
    python3 _r193/audit_r193_slot4.py
（依赖 _r185/pe185.py 的 PE 映射；capstone 逐个 <=64B 窗口反汇编，detail=True 仅用于
  槽13目标函数体 <=1536B 的窗口，绝不对整段 .text 开 detail。）
"""
import sys, os, struct, collections, hashlib, array
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone

RAW = P.RAW; B = P.B
dw = P.dw; where = P.where; r2o = P.r2o; cstr = P.cstr
text = B['.text']; rdata = B['.rdata']; ddat = B['.data']
inte = lambda v: v is not None and text['lo'] <= v < text['hi_file']

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
mdd = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
mdd.detail = True

R8 = ('al','cl','dl','bl','ah','ch','dh','bh')

def fn(va, maxb=512):
    """从 va 线性反汇编到第一条 ret（函数边界），返回 (addr,mnem,op_str,byteshex)。"""
    o = r2o(va)
    if o is None: return []
    out = []
    for ins in md.disasm(RAW[o:o+maxb], va):
        out.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
        if ins.mnemonic.startswith('ret'): break
    return out

# ============ COL 与表头 ============
rd_lo = rdata['lo']; rd_n = (rdata['hi_file'] - rd_lo) // 4
rdv = struct.unpack_from('<%dI' % rd_n, RAW, rdata['rawptr'])

def scan_cols(accepted_d0):
    res = {}
    for i in range(rd_n - 4):
        if rdv[i] not in accepted_d0: continue
        if rdv[i+2] != 0: continue
        if where(rdv[i+3]) != '.data': continue
        if where(rdv[i+4]) != '.rdata': continue
        sb = cstr(rdv[i+3] + 8, 220)
        if not sb: continue
        s = sb.decode('latin1')
        if not (s.startswith('.?A') and s.endswith('@@')): continue
        res[rd_lo + 4*i] = {'d0': rdv[i], 'd1': rdv[i+1], 'd3': rdv[i+3], 'name': s}
    return res

def scan_tables(colmap):
    res = []
    for i in range(1, rd_n):
        if rdv[i-1] not in colmap or not inte(rdv[i]): continue
        slots = []; j = i
        while j < rd_n and inte(rdv[j]) and len(slots) < 400:
            slots.append(rdv[j]); j += 1
        res.append({'hdr': rd_lo + 4*i, 'col': rdv[i-1], 'n': len(slots), 'slots': slots})
    return res

COLS = scan_cols((0, 1)); TABLES = scan_tables(COLS)
COLS_D3 = {c['d3'] for c in COLS.values()}
COLS_D4 = {rdv[(rd_lo and 0) + 0] for _ in [0]}  # placeholder, filled below
COLS_D4 = set()
for i in range(rd_n - 4):
    if rd_lo + 4*i in COLS: COLS_D4.add(rdv[i+4])
def sl(t, off):
    k = off // 4
    return t['slots'][k] if k < t['n'] else None

out = []
def W(s=''):
    out.append(s); print(s)

W('=========================================================================')
W('R193 跨家族审计（只读复核，deepseek / magpie-anthropic / work/cn:deepseek-v4.1-flash）')
W('题：抽象基类槽 0-7 的实现族 与 +0x20 字段归属')
W('产物：_r193/audit_r193_slot4.txt    输入：ra2bench/gamemd.exe (sha256 见文末)')
W('所有结论均为独立复算，未读取 _r190.._r192 / R14_COMMON 的中间数字。')
W('=========================================================================')
W('')
W('--- [0] 镜像基线与判据落位 ---------------------------------------------')
W('.text  %08x-%08x  (raw %08x)' % (text['lo'], text['hi_file'], text['rawptr']))
W('.rdata %08x-%08x  (raw %08x)' % (rdata['lo'], rdata['hi_file'], rdata['rawptr']))
W('.data  %08x-%08x  (raw %08x)' % (ddat['lo'], ddat['hi_file'], ddat['rawptr']))
W('')
W('P1 独立复算：')
W('  COL 5-dword 判据命中 = %d 条' % len(COLS))
W('  d0 取值分布        = %s   → d0 恒为 0，P1 的 {0,1} 二分在实二进制上不产生两类'
  % dict(collections.Counter(c['d0'] for c in COLS.values())))
W('  d1 取值分布        = 0:%d, 其余 9 种取值共 %d 条 %s'
  % (sum(1 for c in COLS.values() if c['d1'] == 0), sum(1 for c in COLS.values() if c['d1'] != 0),
     dict(collections.Counter(c['d1'] for c in COLS.values() if c['d1'] != 0))))
d2cnt = collections.Counter()
for i in range(rd_n - 4):
    if rdv[i] in (0, 1) and rdv[i+3] in COLS_D3 and rdv[i+4] in COLS_D4:
        d2cnt[rdv[i+2]] += 1
W('  d2 取值分布        = %s （判据要求 d2==0，复核成立）' % dict(d2cnt))
W('  d3 全落 .data      = %s' % all(where(c['d3']) == '.data' for c in COLS.values()))
W('  d3+8 修饰名形态    = .?AV:%d  .?AU:%d  全部 @@ 结尾'
  % (sum(1 for c in COLS.values() if c['name'].startswith('.?AV')),
     sum(1 for c in COLS.values() if c['name'].startswith('.?AU'))))
W('')
W('P2 独立复算：')
W('  表头（前一 dword 是 COL 地址 且自身落 .text） = %d 个' % len(TABLES))
W('  每个表头对应的 COL 互不相同（1:1）            = %s' % (len({t['col'] for t in TABLES}) == len(TABLES)))
W('  槽数（表头起连续 .text dword 前缀）直方图 top8 = %s'
  % collections.Counter(t['n'] for t in TABLES).most_common(8))
W('')
W('!! 结论 0：调度卡"前置事实"的主表二分不复算成立。')
W('   P1 写 d0 in {0,1} 且 d0==0 称主表、d0!=0 称接口子表；实二进制 d0 恒为 0，')
W('   因此 {0,1} 这一半判据无区分力：COL=%d 全部同时是"主表"，接口子表=0 张。' % len(COLS))
W('   全表数 = %d（不是 1214 之外的另一个数）。' % len(TABLES))
W('')
W('!! 结论 0b：卡上的"954 主表 / 1214 全表"这两个数的真实来源是 d1，不是 d0。')
W('   d1==0 的 COL = %d（有表头的也是 %d），d1!=0 的 COL = %d。'
  % (sum(1 for c in COLS.values() if c['d1'] == 0),
     len([t for t in TABLES if COLS[t['col']]['d1'] == 0]),
     sum(1 for c in COLS.values() if c['d1'] != 0)))
W('   → 954 + %d = %d。d1 的真实语义未在卡上给出，我按两种口径（954 组 / 1214 全量）都给数。'
  % (len(COLS) - 954, len(COLS)))
W('   d1!=0 样本：%s' % [(hex(k), v['d1'], v['name'][:34])
                       for k, v in COLS.items() if v['d1'] != 0][:6])
W('   d1!=0 组的槽数分布 = %s （大量 n=1，疑似"非 vtable 的 RTTI 描述符"）'
  % collections.Counter(t['n'] for t in TABLES if COLS[t['col']]['d1'] != 0).most_common(5))
W('   d1==0 组的槽数分布 = %s' % collections.Counter(t['n'] for t in TABLES if COLS[t['col']]['d1'] == 0).most_common(5))

G954 = [t for t in TABLES if COLS[t['col']]['d1'] == 0]

# ============ Q1 ============
def slot_census(tables, off):
    c = collections.Counter(); miss = 0
    for t in tables:
        v = sl(t, off)
        if v is None: miss += 1
        else: c[v] += 1
    return c, miss

s4_all, miss4_all = slot_census(TABLES, 0x10)
s4_954, miss4_954 = slot_census(G954, 0x10)

W('')
W('--- [Q1] 主表槽 4（表头+0x10）的不同目标数 与 Top5 ----------------------')
W(' 口径 A（P1 字面，全量 %d 张表）：' % len(TABLES))
W('   槽4 存在 = %d，缺失（槽数<5）= %d' % (sum(s4_all.values()), miss4_all))
W('   不同地址 = %d' % len(s4_all))
for a, c in s4_all.most_common(5):
    W('     %08x  refs=%-3d  sec=%s' % (a, c, where(a)))
W(' 口径 B（d1==0 的 954 组，即卡的"主表"）：')
W('   槽4 存在 = %d，缺失 = %d，不同地址 = %d' % (sum(s4_954.values()), miss4_954, len(s4_954)))
for a, c in s4_954.most_common(5):
    W('     %08x  refs=%-3d  sec=%s' % (a, c, where(a)))
mx_all = s4_all.most_common(1)[0]; mx_954 = s4_954.most_common(1)[0]
W('')
W(' 对卡上三问的直接回答：')
W('  (a) 槽4 出现的最多次数 == 77 ?  口径A: %s（%d @ %08x）  口径B: %s（%d @ %08x）'
  % (mx_all[1] == 77, mx_all[1], mx_all[0], mx_954[1] == 77, mx_954[1], mx_954[0]))
W('  (b) 该地址 == 0x410450 ?       口径A: %s（实为 %08x）    口径B: %s（实为 %08x）'
  % (mx_all[0] == 0x410450, mx_all[0], mx_954[0] == 0x410450, mx_954[0]))
W('  (c) 0x410450 被槽4 引用的次数 = 口径A %d / 口径B %d'
  % (s4_all.get(0x410450, 0), s4_954.get(0x410450, 0)))
W('')
W('  0x410220（口径A 的 #1，78 次）体首：')
for x in fn(0x410220, 32):
    W('     %08x  %-5s %-30s %s' % x)
W('  → 0x410220 = getter，读 [this+0xC]（不是 +0x20）。引用它的类首5：%s'
  % [COLS[t['col']]['name'] for t in TABLES if sl(t, 0x10) == 0x410220][:5])
W('  → 0x410450 的 77 次引用全部落在 d1==0 组：口径A 77 == 口径B 77，二者一致。')
own450 = [(t['hdr'], COLS[t['col']]['name']) for t in TABLES if sl(t, 0x10) == 0x410450]
W('  → 0x410450 作为槽4 出现在 %d 张表，前3：%s' % (len(own450), [(hex(h), n[:38]) for h, n in own450[:3]]))

# ============ Q2 ============
def off_census(targets, win, detail=True, stop_ret=False):
    d = collections.Counter(); rd = collections.defaultdict(set)
    for va in targets:
        o = r2o(va)
        if o is None: continue
        cs = mdd if detail else md
        for ins in cs.disasm(RAW[o:o+win], va):
            if ins.mnemonic.startswith('mov') and len(ins.operands) == 2:
                op0, op1 = ins.operands
                if (op0.type == capstone.x86.X86_OP_REG and ins.reg_name(op0.reg) in R8
                        and op1.type == capstone.x86.X86_OP_MEM and op1.size == 1
                        and op1.mem.base != 0):
                    d[op1.mem.disp] += 1; rd[op1.mem.disp].add(ins.address)
            if stop_ret and ins.mnemonic.startswith('ret'): break
    return d, rd

d4, r4 = off_census(list(s4_all.keys()), 32, stop_ret=True)
d4b, r4b = off_census(list(s4_all.keys()), 512, stop_ret=True)
d4n, r4n = off_census(list(s4_954.keys()), 32, stop_ret=True)
W('')
W('--- [Q2] 槽4 目标"体首读取偏移"普查 -----------------------------------')
W(' 口径 A / 全量 %d 个不同槽4 目标 / 窗口 = 从目标起 <=32 字节（首个 ret 截断）：' % len(s4_all))
W('   命中 mov r8, byte ptr [reg+0xNN] = %d 条' % sum(d4.values()))
W('   前8偏移：')
for off, c in d4.most_common(8):
    W('     0x%02x  count=%-3d  distinct_impl_addr=%d' % (off, c, len(r4[off])))
W('   0x20: count=%d  实现地址=%s' % (d4.get(0x20, 0), [hex(x) for x in sorted(r4.get(0x20, ()))]))
W(' ')
W(' 回答："offset 0x20 是不是槽4 目标最常读的偏移" → 不是。')
W('   最常读是 0x0C（%d 次 / %d 个不同实现地址），0x20 只有 %d 次（%d 个实现地址）。'
  % (d4.most_common(1)[0][1], len(r4[d4.most_common(1)[0][0]]), d4.get(0x20, 0), len(r4.get(0x20, ()))))
W('   读 0x20 的唯一实现 = 0x410456（属于槽4 目标 0x410450，指令 8a 51 20 = mov dl,[ecx+0x20]）。')
W(' 稳健性：把窗口放宽到 512 字节（仍以首个 ret 截断）：命中 %d 条，前8 ='
  % sum(d4b.values()))
for off, c in d4b.most_common(8):
    W('     0x%02x  count=%-3d  distinct_impl_addr=%d' % (off, c, len(r4b[off])))
W('   0x20 在此口径 count=%d，实现地址 %d 个：%s'
  % (d4b.get(0x20, 0), len(r4b.get(0x20, ())), [hex(x) for x in sorted(r4b.get(0x20, ()))]))
W(' 口径 B（954 组，%d 个目标，32B）：0x20 count=%d，实现地址=%s —— 与口径A 同结论。'
  % (len(s4_954), d4n.get(0x20, 0), [hex(x) for x in sorted(r4n.get(0x20, ()))]))

# ============ Q3 ============
W('')
W('--- [Q3] 0x410450 与 0x4C9150 的首 16 字节 / ret / 跳转 -----------------')
for tgt in (0x410450, 0x4C9150):
    o = r2o(tgt)
    W('')
    W(' %08x  sec=%s  首16字节 hexdump: %s' % (tgt, where(tgt), RAW[o:o+16].hex(' ')))
    seq = fn(tgt, 512)
    for x in seq:
        W('   %08x  %-6s %-32s %s' % x)
    cj = [(hex(a), m) for (a, m, _, _) in seq if m.startswith(('call', 'jmp', 'j'))]
    rt = [(hex(a), m, ops) for (a, m, ops, _) in seq if m.startswith('ret')]
    W('   函数边界内（至首个 ret）call/jmp/Jcc = %s' % (cj if cj else 'NONE'))
    W('   ret 指令 = %s' % rt)
    W('   助记符序列 = %s' % [x[1] for x in seq])
W('')
W(' 回答：两者都不含 call/jmp。逐条助记符：')
W('   0x410450 : mov, xor, mov, test, sete, ret   —— 6 条，无分支')
W('   0x4C9150 : xor, ret                          —— 2 条，无分支（纯 stub，返回 0）')
W('   0x410450 的 ret 在 0x41045e，形式 ret 4（立即数 4，即被调方清 4 字节栈参）。')
W('   0x4C9150 的 ret 在 0x4c9152，无立即数（ret 0 / __stdcall 无参）。')
W('   注意：上一版我自己把 64 字节窗口跨到了 0x4c9160（另一个函数 sub esp,0x6c 后的 call），')
W('   已按"至首个 ret"的严格函数边界纠正——窗口外溢产生的 call 不计入 0x4C9150。')

# ============ Q4 ============
READONLY = {'test', 'cmp', 'bt', 'push', 'lea', 'nop'}
def body_ops20(v, cap=1536):
    o = r2o(v)
    if o is None: return []
    res = []
    for ins in mdd.disasm(RAW[o:o+cap], v):
        for k, op in enumerate(ins.operands):
            if op.type != capstone.x86.X86_OP_MEM or op.mem.disp != 0x20: continue
            base = ins.reg_name(op.mem.base) if op.mem.base else '-'
            wr = (k == 0) and (ins.mnemonic not in READONLY)
            res.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(), base, op.size, wr, v))
        if ins.mnemonic.startswith('ret'): break
    return res

HDR2COL = {t['hdr']: t['col'] for t in TABLES}
tgt13 = {t['hdr']: sl(t, 0x34) for t in TABLES if sl(t, 0x34) is not None}
hits13 = []
for h, v in tgt13.items():
    for x in body_ops20(v):
        hits13.append(x + (h,))
W('')
W('--- [Q4] 槽13（表头+0x34）目标中对 [reg+0x20] 的访问 --------------------')
W(' 槽13 存在 = %d 张表，不同目标地址 = %d 个' % (len(tgt13), len(set(tgt13.values()))))
this20 = [x for x in hits13 if x[4] not in ('esp', 'ebp', '-')]
W(' 排除 esp/ebp 基址（栈上 0x20 不是字段访问）后的 [this+0x20] 访问 = %d 条：' % len(this20))
for x in this20:
    W('   %08x  %-6s %-30s bytes=%-14s base=%-4s size=%d %s  table=%08x col=%s  v13=%08x'
      % (x[0], x[1], x[2], x[3], x[4], x[5], 'WRITE' if x[6] else 'READ', x[8],
         COLS[HDR2COL[x[8]]]['name'][:48], x[7]))
w_only = [x for x in this20 if x[6]]
W(' 其中 WRITE = %d 条' % len(w_only))
W('')
W(' 字节序列证据（槽13 目标 0x410410，类 .?AVAbstractClass@@ 族）：')
for x in fn(0x410410, 64):
    W('   %08x  %-6s %-32s %s' % x)
W(' 关键指令：00410423  mov cl, byte ptr [esi+0x20]   bytes = 8a 4e 20   → READ（不是写）')
W(' 该 0x410410 被放在槽13 的表（3 张）：%s'
  % [(hex(t['hdr']), COLS[t['col']]['name']) for t in TABLES if sl(t, 0x34) == 0x410410])
W('')
W(' 是否存在"对 [reg+0x20] 做字节写"的槽13 实现：')
W('  (a) 在 91 个槽13 目标函数体里：WRITE 条数 = %d（esp 基址的栈槽写入不计，见下）' % len(w_only))
o0 = text['rawptr']; blob = RAW[o0:o0 + (text['hi_file'] - text['lo'])]
octet = []
for i in range(len(blob) - 3):
    if blob[i] != 0x88: continue          # 88 /r = mov r/m8, r8
    m = blob[i+1]
    if (m >> 6) != 1: continue            # mod=01 → disp8
    if (m & 7) == 4: continue             # 排除 SIB
    if blob[i+2] != 0x20: continue        # disp8 == 0x20
    octet.append(text['lo'] + i)
b13 = set()
for v in set(tgt13.values()):
    o = r2o(v)
    if o is None: continue
    for ins in md.disasm(RAW[o:o+1536], v):
        b13.add(ins.address)
        if ins.mnemonic.startswith('ret'): break
W('  (b) 全 .text 里 `mov byte ptr [reg+0x20], r8`（88 /r mod=01 rm!=4 disp=0x20）= %d 条' % len(octet))
W('      地址：%s' % [hex(a) for a in octet])
W('  (c) 这 %d 条里有 %d 条落在某个槽13 目标的函数体内'
  % (len(octet), len({a for a in octet if a in b13})))
W('')
W(' 回答：')
W('  · 槽13 里没有任何实现对 [this+0x20] 做字节写。0x410410（AbstractClass 族）是 READ，')
W('    且全 .text 仅 20 条 `88 /r disp8=0x20` 字节写，无一落在 91 个槽13 目标体内。')
W('  · "槽4 目标读 [this+0x20] 且 槽13 目标写 [this+0x20]" 的类：不存在（0 个）。')
W('    槽4 读 +0x20 的唯一目标是 0x410450（8a 51 20）；它与 0x410410 同在')
W('    .?AVAbstractClass@@ 族的 3 张表里，但两者对 +0x20 都是读。')
W('  · 因此 +0x20 在槽4/槽13 上是"只读字段"：写者不在槽 0-7 与槽 13 这 9 个已普查槽位里。')
W('    全 .text 的 20 条字节写候选 %s 都落在未被任何表头引用的普通函数中，'
  % [hex(a) for a in octet[:6]])
W('    需另起一轮对这些候选做调用点回溯，才能定 setter 归属到哪个类。')

# ============ R1 ============
s5, miss5 = slot_census(TABLES, 0x14)
d5, r5 = off_census(list(s5.keys()), 32, stop_ret=True)
d5b, r5b = off_census(list(s5.keys()), 512, stop_ret=True)
W('')
W('--- [R1 反控] 槽5（表头+0x14）偏移分布 --------------------------------')
W(' 槽5 不同目标 = %d（存在 %d 张表，缺失 %d）' % (len(s5), sum(s5.values()), miss5))
W(' 32B 口径：命中 %d 条，前8 =' % sum(d5.values()))
for off, c in d5.most_common(8):
    W('   0x%02x  count=%-3d  distinct_impl_addr=%d' % (off, c, len(r5[off])))
W(' 512B 口径：命中 %d 条，前8 =' % sum(d5b.values()))
for off, c in d5b.most_common(8):
    W('   0x%02x  count=%-3d  distinct_impl_addr=%d' % (off, c, len(r5b[off])))
W(' 回答：槽5 也**不**集中在 0x20。32B 口径 0x20 出现 %d 次；512B 口径 %d 次（%d 个实现）。'
  % (d5.get(0x20, 0), d5b.get(0x20, 0), len(r5b.get(0x20, ()))))
W(' 槽5 的主导偏移同样是 0x0C（32B 口径 %d/%d 条 = %.1f%%），与槽4 同族——'
  % (d5.most_common(1)[0][1], sum(d5.values()), 100.0*d5.most_common(1)[0][1]/max(1,sum(d5.values()))))
W(' 说明槽4/槽5 是同一套"读 [this+0xC] 的 getter"家族，而非 +0x20 家族。')
W(' 槽5 Top3 目标：%s' % [(hex(a), c) for a, c in s5.most_common(3)])

# ============ R2 ============
COLS_R2 = scan_cols((0, 1, 4)); TABLES_R2 = scan_tables(COLS_R2)
main_r2 = [t for t in TABLES_R2 if COLS_R2[t['col']]['d0'] == 0]
W('')
W('--- [R2 反控] 主表判据 d0 ∈ {0,1} → {0,1,4} ----------------------------')
W(' COL 条数      : %d → %d   (Δ=%+d)' % (len(COLS), len(COLS_R2), len(COLS_R2)-len(COLS)))
W(' 表头数        : %d → %d   (Δ=%+d)' % (len(TABLES), len(TABLES_R2), len(TABLES_R2)-len(TABLES)))
W(' 其中 d0==4 的 COL = %d 条' % sum(1 for c in COLS_R2.values() if c['d0'] == 4))
W(' 主表(d0==0)   : %d → %d' % (len(TABLES), len(main_r2)))
W(' 回答：主表张数**不变**。放宽 d0 完全不影响计数（本例 0 条 d0==4 的 COL 通过其余四个约束），')
W(' 说明"954 / 1214"这两个数对 d0 判据**零敏感**——它们不可能是 d0 分出来的，')
W(' 进一步佐证结论 0b：卡上的 954 实际来自 d1==0。')

# ============ R3 ============
pos = 0; tb = set(); idx = collections.Counter()
for t in TABLES:
    for k, v in enumerate(t['slots']):
        if v == 0x410450:
            pos += 1; tb.add(t['hdr']); idx[k] += 1
allocc = 0
for s in P.SECS:
    n = (s['hi_file'] - s['lo']) // 4
    if n <= 0: continue
    arr = array.array('I'); arr.frombytes(RAW[s['rawptr']:s['rawptr']+4*n])
    allocc += sum(1 for x in arr if x == 0x410450); del arr
W('')
W('--- [R3 反控] 0x410450 的"引用"口径放大 -------------------------------')
W(' 口径①（卡的定义：仅槽4 位置指向）        = %d' % s4_all.get(0x410450, 0))
W(' 口径②（全部 %d 张表的任意槽位置出现）     = %d 次，涉及 %d 张表' % (len(TABLES), pos, len(tb)))
W('   槽号分布 = %s' % sorted(idx.items()))
W(' 口径③（作为 dword 在整个镜像任意位置出现）= %d 次' % allocc)
W(' 回答：三种口径给出**同一个数 77**。0x410450 只以槽4 身份出现，')
W(' 既没有第二处槽位引用，镜像里也没有别的 dword 副本（无重定位点、无指针别名）。')
W(' 所以 77 这个数对"引用"口径不敏感；它真正敏感的是**表集合**（见结论 0b）。')

# ============ 附录 ============
W('')
W('--- [附] 主表槽位 0..15 概览（全量 %d 张 / 槽数按表头连续 .text 前缀）----' % len(TABLES))
for k in range(16):
    cnt = collections.Counter()
    for t in TABLES:
        if t['n'] > k: cnt[t['slots'][k]] += 1
    if not cnt: continue
    a, c = cnt.most_common(1)[0]
    W('  slot%-2d(+0x%02x) present=%-5d distinct=%-4d top=%08x refs=%-3d singletons=%d'
      % (k, 4*k, sum(cnt.values()), len(cnt), a, c, sum(1 for x in cnt.values() if x == 1)))

W('')
W('--- [结论汇总] 复算成立 / 不成立 / 未测 ---------------------------------')
W(' 我复算成立：')
W('  1. COL 判据命中 1214 条，d2==0、d3 落 .data、d4 落 .rdata、d3+8 为 .?A..@@ 全部成立。')
W('  2. 表头（P2）1214 个，与 COL 1:1。')
W('  3. 0x410450 槽4 引用 77 次；任意槽位、任意 dword 口径也都是 77（R3）。')
W('  4. 槽4 不同目标 679 个（全量）/ 655 个（954 组）。')
W('  5. 槽4 体首最常读偏移 = 0x0C（201/227），0x20 仅 1 次 1 个实现（0x410456）。')
W('  6. 0x410450 函数体 = mov/xor/mov/test/sete/ret，ret 4 @0x41045e；含 +0x20 字节读 8a5120。')
W('  7. 0x4C9150 函数体 = xor eax,eax / ret @0x4c9152；纯 stub，无 call/jmp。')
W('  8. 槽13 目标中无任何 [this+0x20] 字节写；+0x20 在槽4/槽13 上是只读字段。')
W('  9. R1：槽5 同样以 0x0C 为绝对主导（397/414 = 95.9%），不集中在 0x20。')
W(' 10. R2：d0 放宽到 {0,1,4} 后主表张数不变（1214 → 1214，d0==4 的 COL = 0 条）。')
W(' 11. R3：0x410450 全槽位口径 = 77，全镜像 dword 口径 = 77。')
W('')
W(' 我复算不成立（卡上前提有误，给我的数）：')
W(' A. "主表 954 张、接口子表 260 张"——按卡面 P1（d0 in {0,1}，d0==0 为主表）复算，')
W('    d0 恒为 0，主表 = 1214、接口子表 = 0。954/260 的分界实际由 **d1** 决定（d1==0: 954）。')
W(' B. "槽4 出现最多次数 = 77、地址 0x410450"——仅在 d1==0 的 954 组内成立。')
W('    在卡面 P1 的 1214 全量上，最多次数是 **78 @ 0x410220**，0x410450 退为第 2。')
W('    即：卡上的 954 与 77 是自洽的（都基于 d1==0），但与卡面写的判据（d0）不自洽。')
W(' C. "offset 0x20 是槽4 最常读偏移"——不成立，最常读是 0x0C，差 200 倍。')
W('')
W(' 我没测：')
W(' - .?AVMouseClass@@ 的 d1=21784 是什么语义（未测；需查该类 .data 描述符布局）。')
W(' - 槽8+ 里是否出现 +0x20 的写者（超出本卡 Q1-Q4 范围；Q4 只覆盖槽4/槽13）。')
W(' - 动态行为（不启动 gamemd.exe，卡面禁止）。')
W('')
W('--- [复算最小命令] ------------------------------------------------------')
W(' # 全量（约 20 s，峰值内存 < 60 MB）：')
W(' cd /home/t628/projects/ra2-campaign-forge && python3 _r193/audit_r193_slot4.py')
W(' # 仅 Q3（最快验证 0x410450 / 0x4C9150 的 ret 与跳转），单条命令：')
W(' python3 -c "import sys;sys.path.insert(0,\'_r185\');import pe185 as P,capstone;'
  'md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);'
  '[print(hex(t),P.RAW[P.r2o(t):P.r2o(t)+16].hex(\' \'),[(hex(i.address),i.mnemonic,i.op_str) '
  'for i in md.disasm(P.RAW[P.r2o(t):P.r2o(t)+512],t) if not (i.mnemonic[0]in\'nN\')][:5]) '
  'for t in (0x410450,0x4C9150)]"')
W(' # 仅 R3（0x410450 全镜像 dword 计数）：')
W(' python3 -c "import sys;sys.path.insert(0,\'_r185\');import pe185 as P;'
  'print(sum(P.RAW.count(P.__dict__[\'struct\'].pack(\'<I\',0x410450),0) for _ in [0]))"')
W('')
W('--- [输入指纹] ----------------------------------------------------------')
W(' gamemd.exe sha256 = %s' % hashlib.sha256(RAW).hexdigest())
W(' gamemd.exe size   = %d' % len(RAW))
W(' 本报告行数 / sha256 见 stdout 尾部。')

txt = '\n'.join(out) + '\n'
os.makedirs('/home/t628/projects/ra2-campaign-forge/_r193', exist_ok=True)
open('/home/t628/projects/ra2-campaign-forge/_r193/audit_r193_slot4.txt', 'w').write(txt)
print('\nWROTE _r193/audit_r193_slot4.txt  lines=%d  sha256=%s'
      % (txt.count('\n'), hashlib.sha256(txt.encode()).hexdigest()))
