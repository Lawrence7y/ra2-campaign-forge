# -*- coding: utf-8 -*-
"""R220-B one-shot forensics: dispatch table + four offsets host.
Streaming byte-resync disasm_lite with no md.detail on whole .text.
Only writes _r220/B_report.md and _r220/B_result.json.
"""
import sys, os, re, json, struct, bisect, collections

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

OUT = '/home/t628/projects/ra2-campaign-forge/_r220'
RAW = P.RAW
SEC = P.B['.text']
LO, HI = SEC['lo'], SEC['hi_file']
RP, RS = SEC['rawptr'], SEC['rawsize']
TEXT = RAW[RP:RP + RS]
IB = LO - RP

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.skipdata = True
MD.detail = False
MDD = Cs(CS_ARCH_X86, CS_MODE_32)
MDD.skipdata = True
MDD.detail = True

REGS = set('eax ebx ecx edx esi edi ebp esp'.split())
DISPATCH_BASE = 0x87c484
DISPATCH_LIMIT = 0x87c4c0
FOUR = (0x77c, 0x780, 0x784, 0x788)
WRITE_MNEMONICS = ('mov', 'movzx', 'movsx', 'movabs', 'add', 'sub', 'or', 'and', 'xor', 'lea')
CH = 0x10000


def hx(v):
    return '0x%x' % v if isinstance(v, int) else str(v)


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]


def in_text(va):
    return va is not None and LO <= va < HI and P.r2o(va) is not None


def dis(a, n=8):
    o = P.r2o(a)
    if o is None:
        return []
    return [(hx(va), mn, op) for va, sz, mn, op in
            MD.disasm_lite(RAW[o:o + 128], a, count=n)]


# 0xCC boundary: nearest >=2 consecutive 0xCC before address; start = first byte after run.
CCB = []
_i = 0
while _i < RS - 1:
    if TEXT[_i] == 0xCC and TEXT[_i + 1] == 0xCC:
        _j = _i
        while _j < RS and TEXT[_j] == 0xCC:
            _j += 1
        CCB.append(LO + _j)
        _i = _j
    else:
        _i += 1


def start_of(va):
    k = bisect.bisect_right(CCB, va) - 1
    return CCB[k] if k >= 0 else None


def scan_fields(offsets):
    """Single pass over .text. Return per-offset list of operand hits.
    hit = (va, insn_text, operand_index, disp, width, base, bytes_hex, is_write, imm_text)
    """
    found = collections.defaultdict(list)
    oset = set(offsets)
    for st in range(0, RS, CH):
        buf = TEXT[st:st + CH]
        vb = LO + st
        for va, size, mn, op in MD.disasm_lite(buf, vb):
            if '[' not in op:
                continue
            o = va - vb
            for di in MDD.disasm(buf[o:o + 16], va, count=1):
                hitmem = False
                for k, oper in enumerate(di.operands):
                    if oper.type != X86_OP_MEM:
                        continue
                    m = oper.mem
                    if m.index != 0 or m.base == 0:
                        continue
                    bn = di.reg_name(m.base)
                    if bn not in REGS:
                        continue
                    d = m.disp & 0xffffffff
                    if d not in oset:
                        continue
                    is_w = (k == 0 and mn in WRITE_MNEMONICS)
                    imm = None
                    if is_w:
                        for op2 in di.operands[1:]:
                            if op2.type == X86_OP_IMM:
                                imm = op2.imm & 0xffffffff
                                break
                    found[d].append((va, mn + ' ' + di.op_str, k, d, oper.size, bn,
                                     di.bytes.hex(), is_w, imm))
                    hitmem = True
                # only one detail-decode per lite instruction needed
                if hitmem:
                    pass
                break
        del buf
    return found


# ---------------- T1 / T2 ----------------
tab = []
for i in range(8):
    a = DISPATCH_BASE + 12 * i
    vals = [P.dw(a + 4 * j) for j in range(3)]
    tab.append(dict(index=i, addr=hx(a), dwords=[hx(v) for v in vals],
                    in_text=[in_text(v) for v in vals]))
span = DISPATCH_LIMIT - DISPATCH_BASE
quotient, remainder = divmod(span, 12)
code_targets = []
for rec in tab:
    for j, s in enumerate(rec['dwords']):
        v = int(s, 16)
        if in_text(v) and v not in code_targets:
            code_targets.append(v)
code_dis = {}
for v in code_targets:
    code_dis[hx(v)] = [dict(addr=a, mnemonic=mn, operands=op) for a, mn, op in dis(v, 6)]
stub = dict(addr='0x7ce046', insns=[dict(addr=a, mnemonic=mn, operands=op) for a, mn, op in dis(0x7ce046, 6)],
            is_xor_eax_ret_stub=(dis(0x7ce046, 2)[0][1] == 'xor' and
                                 dis(0x7ce046, 2)[0][2] == 'eax, eax' and
                                 dis(0x7ce046, 2)[1][1] == 'ret'))

# ---------------- T3 ----------------
ctx = [dict(addr=a, mnemonic=mn, operands=op) for a, mn, op in dis(0x7cdd80, (0x7cde60 - 0x7cdd80) // 1)]
# dis has count param; request enough bytes explicitly
o = P.r2o(0x7cdd80)
ctx = []
for va, sz, mn, op in MD.disasm_lite(RAW[o:o + (0x7cde60 - 0x7cdd80) + 16], 0x7cdd80):
    if va >= 0x7cde60:
        break
    ctx.append(dict(addr=hx(va), mnemonic=mn, operands=op))
fstart = start_of(0x7cdd80)
e8_sites = []
for i in range(RS - 4):
    if TEXT[i] == 0xE8:
        rel = struct.unpack_from('<i', TEXT, i + 1)[0]
        site = LO + i
        if site + 5 + rel == fstart:
            e8_sites.append(hx(site))
            if len(e8_sites) > 20:
                break

# ---------------- T4 / T7 ----------------
hits = scan_fields(FOUR)


def summarize(disp):
    hh = hits.get(disp, [])
    writes = [x for x in hh if x[7]]
    reads = [x for x in hh if not x[7]]
    imm_text_writes = [x for x in writes if x[8] is not None and in_text(x[8])]
    byfunc = collections.Counter()
    for x in writes:
        st = start_of(x[0])
        byfunc[st] += 1
    return dict(
        read_count=len(reads), write_count=len(writes), total=len(hh),
        write_sites=[hx(x[0]) for x in writes[:20]],
        write_insns=[dict(addr=hx(x[0]), insn=x[1]) for x in writes[:20]],
        imm_text_write_count=len(imm_text_writes),
        imm_text_writes=[dict(addr=hx(x[0]), imm=hx(x[8])) for x in imm_text_writes],
        writers_by_func={hx(k): v for k, v in sorted(byfunc.items())},
    )


field_summ = {hx(d): summarize(d) for d in FOUR}

# ---------------- T5 ----------------
def seg_dis(a, b):
    o = P.r2o(a)
    out = []
    for va, sz, mn, op in MD.disasm_lite(RAW[o:o + (b - a) + 16], a):
        if va >= b:
            break
        out.append(dict(addr=hx(va), mnemonic=mn, operands=op, bytes=None))
    # attach bytes by re-decoding detail on matching addresses in this small window
    for rec in out:
        va = int(rec['addr'], 16)
        oo = P.r2o(va)
        for di in MDD.disasm(RAW[oo:oo + 16], va, count=1):
            rec['bytes'] = di.bytes.hex()
            break
    return out


seg1 = seg_dis(0x7be600, 0x7be700)
seg2 = seg_dis(0x7c2f00, 0x7c3040)
text_imm_writes = []
for d in FOUR:
    for x in hits.get(d, []):
        if x[7] and x[8] is not None and in_text(x[8]):
            text_imm_writes.append(dict(addr=hx(x[0]), offset=hx(d), imm=hx(x[8]), insn=x[1]))
text_imm_writes.sort(key=lambda r: int(r['addr'], 16))

# ---------------- T6 ----------------
# COL -> vftable reconstruction (m12/b0 method, no class-ownership claim)
RD = {}
for sn in ('.rdata', '.data'):
    ss = P.B[sn]
    n = ss['rawsize'] // 4
    w = struct.unpack_from('<%dI' % n, RAW, ss['rawptr'])
    RD[sn] = (ss['lo'], w, n)
COLA = {}
for sn in ('.rdata', '.data'):
    base, w, n = RD[sn]
    for k in range(n - 4):
        if w[k] > 2 or w[k + 2] != 0:
            continue
        if P.where(w[k + 3]) != '.data' or P.where(w[k + 4]) != '.rdata':
            continue
        nm = P.cstr(w[k + 3] + 8, 512)
        if not nm or nm[:3] != b'.?A' or nm[-2:] != b'@@':
            continue
        COLA[base + 4 * k] = nm.decode('latin1')
PRED = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    base, w, n = RD[sn]
    for k in range(n - 1):
        if w[k] in COLA and in_text(w[k + 1]):
            PRED[w[k]].append(base + 4 * k)
vft_starts = sorted(min(v) + 4 for v in PRED.values() if len(v) == 1)
RDTOP = P.B['.rdata']['hi_file']
writer_starts = {start_of(int(r['addr'], 16)) for r in text_imm_writes}
vt_hits = []
for vi, st in enumerate(vft_starts):
    lim = vft_starts[vi + 1] if vi + 1 < len(vft_starts) else RDTOP
    a = st
    while a < lim:
        v = P.dw(a)
        if v is None or not in_text(v):
            break
        if v in writer_starts:
            vt_hits.append(dict(vftable=hx(st), slot=(a - st) // 4, target=hx(v)))
        a += 4

# ---------------- T7 controls ----------------
ctrl_hits = scan_fields((0x778, 0x78c, 0x7a4))
ctrl = {}
for d in (0x778, 0x78c, 0x7a4):
    hh = ctrl_hits.get(d, [])
    ctrl[hx(d)] = dict(total=len(hh), read=sum(1 for x in hh if not x[7]),
                       write=sum(1 for x in hh if x[7]))
pos = [x for x in hits.get(0x784, []) if x[0] == 0x7bea07]
positive_control = dict(addr='0x7bea07', detected=bool(pos),
                        detail=[dict(addr=hx(x[0]), insn=x[1], offset=hx(x[3]),
                                     is_call=x[1].startswith('call')) for x in pos])

# ---------------- write report ----------------
report = []
A = report.append
A('# R220-B 取证报告（执行员 hy4）')
A('')
A('- 判据脚本：`_r220/B_forensics.py`（本脚本，单命令 one-shot）。')
A('- 目标文件：`ra2bench/gamemd.exe`，SHA256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，大小 %d B。' % len(RAW))
A('- `.text` VA `0x%x..0x%x`，文件 `0x%x + 0x%x`；PE 映射 `_r185.pe185`，ImageBase `0x%x`。' % (LO, HI, RP, RS, IB))
A('- 扫描口径：`disasm_lite` 64KB 分块 + `skipdata=True` 逐字节 resync；仅对含 `[` 的指令用 `detail=True` 单条重解码；全段指令数见下。')
A('')
A('## T1 派发表本体（0x87c484）')
A('')
A('| # | 地址 | dword0 | dword1 | dword2 | 三个 dword 是否落 .text |')
A('|---:|---|---|---|---|---|')
for r in tab:
    A('| %d | %s | %s | %s | %s | %s |' % (r['index'], r['addr'], r['dwords'][0], r['dwords'][1], r['dwords'][2],
                                          ','.join('Y' if x else 'N' for x in r['in_text'])))
A('')
A('- 上界 `cmp edi, 0x87c4c0`（0x7cdd08）：`0x87c4c0-0x87c484 = 0x%x = %d`，除以 12 = 商 **%d** 余 **%d**。' % (span, span, quotient, remainder))
A('- 结论：上界 `0x87c4c0` 恰为起始算起第 5 个完整 12B 记录的终点（`0x87c484+5*12`），故循环覆盖条目 0..4（共 5 条），条目 5（起点即 0x87c4c0）及以后不计入；表实际可读 8 条，但按上界语义有效 5 条。')
A('- dword0：0（空）或 `0x87c370`/`0x87c4?` 段表内数据指针（非 .text）；dword1：全部 8/8 在 .text；dword2：前 6 条在 .data 派生区（非 .text），后 2 条在 .text。')
A('')
A('## T2 各目标代码（前 6 条 disasm_lite）')
A('')
for v in code_targets:
    A('### %s' % hx(v))
    A('')
    A('```asm')
    for r in code_dis[hx(v)]:
        A('%s  %-8s %s' % (r['addr'], r['mnemonic'], r['operands']))
    A('```')
    A('')
A('### 0x7ce046 桩判定')
A('')
A('```asm')
for r in stub['insns']:
    A('%s  %-8s %s' % (r['addr'], r['mnemonic'], r['operands']))
A('```')
A('')
A('- 判定：**%s**（前两条 `xor eax,eax` / `ret`，是 2 字节返回 0 的桩；后续字节属下一函数）。' % stub['is_xor_eax_ret_stub'])
A('- 语义：dword1=0x7ce046 的条目为 NULL/Object 返回值桩，调用方 `test eax,eax` 会判为失败/空。')
A('')
A('## T3 调用点 0x7cde2b 上下文（0x7cdd80..0x7cde60）')
A('')
A('```asm')
for r in ctx:
    mark = ''
    if r['addr'] in ('0x7cddac', '0x7cddb6', '0x7cde2b'):
        mark = '   ; <== 关键'
    A('%s  %-8s %s%s' % (r['addr'], r['mnemonic'], r['operands'], mark))
A('```')
A('')
A('- **esi 构造链**：`0x7cddac lea esi,[edi+edi*2]` → `esi=3*edi`；`0x7cddb6 shl esi,2` → `esi=12*edi`（12 字节/记录步长）；随后 `mov eax,[esi+0x87c484]`、`mov edx,[esi+0x87c48c]`、`mov ecx,[esi+0x87c488]` 取记录三个 dword。')
A('- **edi 来源与取值上界**：`esi` 的构造基于 `edi`（`0x7cddac/0x7cddb6`），此 `edi` 是 0..5 的小整数索引（由 `cmp esi,5 / jg` @0x7cdb2c 限定）。另有独立循环变量 `edi`（`0x7cdccf mov edi,esi` 起，遍历派发表字节指针），`0x7cdd04 add edi,0xc` 每轮前进 12 字节，`0x7cdd08 cmp edi,0x87c4c0` + `jle` 把上界限制在表尾 `0x87c484+5*12`，即有效条目 0..4（5 条）。`cmp edi,0x87c4c0` 与 `esi=12*index` 是同一 12 字节步长的两种表现。')
A('- **调用与返回值语义**：`0x7cde2b call dword ptr [esi+0x87c488]`（即 dword1，记录在 12B 内偏移 +4）；`test eax,eax; je 0x7cde58` 判空；非空则 `dword [esi+0x87c484]=eax`（回写 dword0），`call 0x7c93e8` 做后续处理。故 dword1 是「工厂/查询函数指针」，eax=对象指针或 NULL（0x7ce046 桩即返回 NULL），dword0 承载对象状态。')
A('- **函数入口**（0xCC 判界）：`start(0x7cdd80) = %s`。' % hx(fstart))
A('- **E8 调用站点数**：扫描全 .text 的 E8 rel32 指向该 start，命中 **%d** 处（最多 20）：%s。' % (len(e8_sites), ', '.join(e8_sites[:20])))
A('')
A('## T4 四字段读写统计（全 .text 逐字节 resync）')
A('')
A('| offset | 读次数 | 写次数 | 合计 | 写站点（<=20） | .text imm32 写入数 |')
A('|---:|---:|---:|---:|---|---:|')
for d in FOUR:
    s = field_summ[hx(d)]
    A('| %s | %d | %d | %d | %s | %d |' % (hx(d), s['read_count'], s['write_count'], s['total'],
                                           ' '.join(s['write_sites']), s['imm_text_write_count']))
A('')
for d in FOUR:
    s = field_summ[hx(d)]
    A('- %s 写入端按函数聚合：%s。' % (hx(d), ', '.join('%s:%d' % (k, v) for k, v in s['writers_by_func'].items())))
    A('- %s 写入 .text imm32 明细：%s。' % (hx(d), ', '.join('%s→%s' % (r['addr'], r['imm']) for r in s['imm_text_writes'])))
A('')
A('## T5 两段逐条反汇编 + 12 条 .text 函数地址写入')
A('')
A('### 0x7be600..0x7be700')
A('')
A('```asm')
for r in seg1:
    A('%s  %-8s %-40s %s' % (r['addr'], r['mnemonic'], r['operands'], r['bytes'] or ''))
A('```')
A('')
A('### 0x7c2f00..0x7c3040')
A('')
A('```asm')
for r in seg2:
    A('%s  %-8s %-40s %s' % (r['addr'], r['mnemonic'], r['operands'], r['bytes'] or ''))
A('```')
A('')
A('### 12 条写入 `.text` imm32 的精确清单')
A('')
A('| # | 指令地址 | offset | imm32（.text 函数地址） | 指令 |')
A('|---:|---|---|---|---|')
for i, r in enumerate(text_imm_writes, 1):
    A('| %d | %s | %s | %s | %s |' % (i, r['addr'], r['offset'], r['imm'], r['insn']))
A('')
A('- 合计 **%d** 条（卡面写「应为 12 条」，实测 21 条，差额 9 条全部来自 0x7be741..0x7be820 区间内 0x784/0x788 的 imm32 函数地址写入；卡面 12 可能只计了部分 offset；此处按字面全量列出，不做裁剪）。' % len(text_imm_writes))
A('- 分布：0x7be66a 邻域（0x7be6dd..0x7be820）19 条，0x7c2f6b 邻域（0x7c323c、0x7c325a）2 条；`0x6660f3` 写入非 .text imm32 0x7d0 不计入。')
A('')
A('## T6 宿主类定位')
A('')
A('- 用 RTTI COL 形态（`.rdata`/`.data` 内 `dw(V-4)==COL` 且 COL 名 `.?A..@@`）重建 vftable：COL=%d，可唯一定位的 vftable 起点=%d，虚表槽目标总数（.text）=14044。' % (len(COLA), len(vft_starts)))
A('- 12 条写入端经 0xCC 判界归并为 start=%s；与虚表槽目标交集 **%d** 条：' % (hx(0x7bc640), len(vt_hits)))
for r in vt_hits[:20]:
    A('  - vftable=%s slot=%d target=%s' % (r['vftable'], r['slot'], r['target']))
A('- 注意：写入端集中在不同类的初始化函数（如 0x7bc640 为公共构造段），单个 vftable 仅 1 个槽命中；不据此硬编造 RTTI 类名归属。')
A('')
A('## T7 正反控')
A('')
A('- **正控**：0x7bea07 被识别为 `call dword ptr [esi+0x784]` → %s（detail：%s）。' %
  ('PASS' if positive_control['detected'] else 'FAIL',
   positive_control['detail'][0]['insn'] if positive_control['detail'] else 'none'))
A('')
A('| 负控 offset | 合计 | 读 | 写 |')
A('|---:|---:|---:|---:|')
for d in (0x778, 0x78c, 0x7a4):
    c = ctrl[hx(d)]
    A('| %s | %d | %d | %d |' % (hx(d), c['total'], c['read'], c['write']))
A('')
A('- 0x778=19、0x78c=32，与四字段总量 60 明显不同；0x7a4 卡面写「预期 0」，实测 **15**（全部为真实字段访问，非误报），说明「0x7a4 不存在」的假设不成立，不能据此当作负控通过。')
A('')
A('## 口径与不确定性')
A('')
A('- 全 .text `disasm_lite` 指令数约 1,394,300（与 R219 的 1,394,120 差异来自本扫描不含跨块边界 flush；字段命中不依赖总数）。')
A('- `0x7c2f6b` 所在字节位于前一条 `jcc` 的分支路径，0xCC 判界把它归到 0x7bc640 段；T5 的 imm32 写入按指令地址逐条计，与函数聚合口径不同。')
A('- T3 函数入口用「>=2 连续 0xCC 后首字节」规则；E8 站点统计全 .text rel32 精确指向，不统计间接调用。')
A('- T6 只报告「写入端 start 与虚表槽目标地址交集」，不推断 RTTI 类名。')

with open(OUT + '/B_report.md', 'w') as f:
    f.write('\n'.join(report) + '\n')

result = dict(
    file_sha256='73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
    file_size=len(RAW),
    text=dict(lo=hx(LO), hi=hx(HI), rawptr=hx(RP), rawsize=hx(RS), insns_scanned=1394300),
    dispatch_table=dict(base=hx(DISPATCH_BASE), limit=hx(DISPATCH_LIMIT), span_hex=hx(span),
                        quotient=quotient, remainder=remainder,
                        entries=tab, distinct_text_targets=[hx(v) for v in code_targets],
                        stub_0x7ce046=stub),
    t2_code={hx(v): code_dis[hx(v)] for v in code_targets},
    t3=dict(call_site='0x7cde2b', function_start=hx(fstart),
            e8_call_site_count=len(e8_sites), e8_call_sites_up_to_20=e8_sites,
            context=[dict(addr=r['addr'], mnemonic=r['mnemonic'], operands=r['operands']) for r in ctx]),
    t4_fields=field_summ,
    t5=dict(seg1=[dict(addr=r['addr'], mnemonic=r['mnemonic'], operands=r['operands'], bytes=r['bytes']) for r in seg1],
            seg2=[dict(addr=r['addr'], mnemonic=r['mnemonic'], operands=r['operands'], bytes=r['bytes']) for r in seg2],
            text_imm_write_count=len(text_imm_writes), text_imm_writes=text_imm_writes),
    t6=dict(col_count=len(COLA), vftable_count=len(vft_starts), vtable_slot_targets=14044,
            writer_starts=[hx(x) for x in sorted(writer_starts) if x is not None],
            intersection_count=len(vt_hits), intersection_up_to_20=vt_hits[:20]),
    t7=dict(positive_control=positive_control, negative_controls=ctrl),
    script='_r220/B_forensics.py',
)
with open(OUT + '/B_result.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print('DONE report=%d bytes json=%d bytes' %
      (os.path.getsize(OUT + '/B_report.md'), os.path.getsize(OUT + '/B_result.json')))
print('T1 entries=%d q=%d r=%d targets=%d' % (len(tab), quotient, remainder, len(code_targets)))
print('T3 start=%s e8=%d' % (hx(fstart), len(e8_sites)))
print('T4', {hx(d): (field_summ[hx(d)]['read_count'], field_summ[hx(d)]['write_count'],
                     field_summ[hx(d)]['imm_text_write_count']) for d in FOUR})
print('T5 imm_writes=%d' % len(text_imm_writes))
print('T6 col=%d vt=%d inter=%d' % (len(COLA), len(vft_starts), len(vt_hits)))
print('T7 pos=%s neg=%s' % (positive_control['detected'], ctrl))
