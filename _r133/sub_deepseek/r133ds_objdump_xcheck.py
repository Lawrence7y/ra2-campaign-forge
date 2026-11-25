#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R133 sub_deepseek — 跨解码器复核（GNU objdump / i686-w64-mingw32-objdump）
不依赖 capstone 的任何结论，独立重做三项：(1) 直接调用点枚举；(2) 前三条 push；(3) 编码形态。

运行：timeout 300 python3 _r133/sub_deepseek/r133ds_objdump_xcheck.py
"""
import json
import os
import re
import struct
import subprocess
import sys

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUTDIR = '/home/t628/projects/ra2-campaign-forge/_r133/sub_deepseek'
OUT = os.path.join(OUTDIR, 'r133ds_objdump_xcheck.json')
TARGETS = [0x6bedb0, 0x41c250]
TEXT_LO, TEXT_HI = 0x401000, 0x7e038d

R = {'tool': 'i686-w64-mingw32-objdump', 'asserts': []}


def chk(n, c, d=''):
    R['asserts'].append({'assert': n, 'pass': bool(c), 'detail': str(d)})
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  [' + str(d) + ']') if d != '' else ''))


txt = subprocess.run(
    ['i686-w64-mingw32-objdump', '-d',
     '--start-address=%#x' % TEXT_LO, '--stop-address=%#x' % TEXT_HI, EXE],
    capture_output=True, text=True, timeout=280, check=True).stdout
lines = txt.splitlines()
R['objdump_lines'] = len(lines)

ipat = re.compile(r'^\s*([0-9a-f]+):\t')
insns = []
for L in lines:
    m = ipat.match(L)
    if not m:
        continue
    f = L.split('\t')
    insns.append((int(m.group(1), 16), f[2].strip() if len(f) > 2 else ''))
R['insn_count'] = len(insns)
byva = {}
for va, asm in insns:
    byva.setdefault(va, asm)
print('[objdump] %d 行, %d 条指令，起始 VA %#x 结束 VA %#x'
      % (len(lines), len(insns), insns[0][0], insns[-1][0]))

# ---- (1) 直接调用点：objdump 语义解码的 call/jmp 目标
calls = {t: [] for t in TARGETS}
jmps = {t: [] for t in TARGETS}
for va, asm in insns:
    for t in TARGETS:
        if re.fullmatch(r'call\s+%#x' % t, asm):
            calls[t].append(va)
        if re.fullmatch(r'jmp\s+%#x' % t, asm):
            jmps[t].append(va)
R['calls'] = {hex(t): [hex(x) for x in v] for t, v in calls.items()}
R['jmps'] = {hex(t): [hex(x) for x in v] for t, v in jmps.items()}
print('\n[objdump][1] call 站点：', {hex(t): [hex(x) for x in v] for t, v in calls.items()})
print('[objdump][1] jmp  站点：', {hex(t): [hex(x) for x in v] for t, v in jmps.items()})

# ---- (3) 每个调用点前最后三条 push（按 objdump 已解码的指令序列回溯）
sites = sorted(x for t in TARGETS for x in calls[t])
idx = {va: i for i, (va, _) in enumerate(insns)}
recs = []
for s in sites:
    i = idx[s]
    prev = insns[:i]
    pushes = [x for x in reversed(prev) if x[1].startswith('push')][:3]   # 由近及远
    # 连续性：前三条 push 必须紧邻且其间无非 push 的 esp 调整（此处显式列出中间指令）
    span = insns[idx[pushes[-1][0]]:i] if len(pushes) == 3 else []
    third = pushes[-1] if len(pushes) == 3 else None
    # esp 模拟：从最早那条 push 起维护 esp 相对 E（E = call 时的 esp）的偏移，
    # 精确判定"三条 push 之后是否还有指令改动 esp 或写进参数槽 [E+0..E+8]"。
    sim = []
    if len(pushes) == 3:
        esp_off = 8          # 执行完三条 push 后 esp == E；开始时 esp == E+8
        for (va, asm) in span:
            mn = asm.split()[0] if asm else ''
            ops = [o.strip() for o in asm.split(None, 1)[1].split(',')] if ' ' in asm else []
            dest = ops[-1] if ops else ''
            note = None
            if mn in ('push', 'pushal', 'pusha', 'pushf', 'pushfd'):
                esp_off -= 4 if mn == 'push' else 32
                note = 'esp-=4 (push)'
            elif mn in ('pop', 'leave', 'enter', 'popal', 'popa'):
                note = 'esp 改变 (%s)' % mn
                esp_off = None
            elif dest == '%esp':
                note = '直接改写 esp'
                esp_off = None
            else:
                m = re.search(r'(0x[0-9a-f]+)?\(%esp\)$', dest)
                if m and esp_off is not None:
                    disp = int(m.group(1), 16) if m.group(1) else 0
                    eff = disp + esp_off
                    if eff in (0, 4, 8):
                        note = '写进参数槽 E+%#x' % eff
            sim.append({'va': hex(va), 'asm': asm, 'esp_off_after': esp_off, 'note': note})
    clamp = [s for s in sim if s['note']]
    recs.append({'site': hex(s), 'target': hex(next(t for t in TARGETS if s in calls[t])),
                 'push_near_to_far': [p[1] for p in pushes],
                 'third_arg_asm': third[1] if third else None,
                 'third_arg_va': hex(third[0]) if third else None,
                 'insns_between_oldest_push_and_call': [a for _, a in span],
                 'esp_sim': sim,
                 'esp_or_argslot_clobber': clamp})
R['sites'] = recs
print('\n[objdump][3] 每个调用点前最后三条 push（近->远）：')
for r in recs:
    print('    %-10s -> %-10s  %s   3rd=%s' % (r['site'], r['target'],
                                               ' | '.join(r['push_near_to_far']), r['third_arg_asm']))

# ---- 前三条 push 之后是否还有指令改动 esp / 写进参数槽
bad = [(r['site'], c['asm']) for r in recs for c in r['esp_or_argslot_clobber']]
R['esp_adjust_between'] = bad
print('\n[objdump] 三条 push 之后改动 esp 或写参数槽的指令：', bad if bad else '无')

# ---- (2) 编码形态：直接从原始字节确认 E8/E9 与 rel32
raw = open(EXE, 'rb').read()
R['encoding'] = []
for s in sites:
    off = s - TEXT_LO + 0x1000       # .text RawPtr = 0x1000
    op = raw[off]
    rel = struct.unpack_from('<i', raw, off + 1)[0]
    dst = s + 5 + rel
    R['encoding'].append({'site': hex(s), 'opcode': hex(op), 'rel32': rel, 'dst': hex(dst)})
for e in R['encoding']:
    print('    %s: op=%s rel32=%d -> %s' % (e['site'], e['opcode'], e['rel32'], e['dst']))

# ---- imm32 出现次数（GNU/字节层面独立复核）
hexs = raw.hex()
R['imm32_hex'] = {hex(t): hexs.count(struct.pack('<I', t).hex()) for t in TARGETS}
print('\n[objdump][2] imm32 全文件 hex 子串计数：', R['imm32_hex'])

# ------------------------------------------------------------ 断言
chk('X1 objdump 语义解码的 call 站点总数 == 15', len(sites) == 15, len(sites))
chk('X2 每个站点原始字节都是 E8（call rel32）', all(e['opcode'] == '0xe8' for e in R['encoding']),
    [e['opcode'] for e in R['encoding']])
chk('X3 每个站点的 rel32 解析后目标就是入口',
    all(int(e['dst'], 16) in TARGETS for e in R['encoding']))
chk('X4 objdump 未发现任何 E9(jmp rel32) 形式', sum(len(v) for v in jmps.values()) == 0,
    {hex(t): len(v) for t, v in jmps.items()})
chk('X5 每个站点前最后三条 push 里的第三条都是立即数 0x7',
    all(r['third_arg_asm'] and re.fullmatch(r'push\s+\$0x7', r['third_arg_asm']) for r in recs),
    sorted({r['third_arg_asm'] for r in recs}))
chk('X6 三条 push 之后无指令改动 esp 或写进参数槽 E+0/4/8', not bad, bad)
chk('X7 imm32 全文件出现次数对两个入口都是 0',
    all(v == 0 for v in R['imm32_hex'].values()), R['imm32_hex'])

R['pass'] = sum(1 for a in R['asserts'] if a['pass'])
R['total'] = len(R['asserts'])
os.makedirs(OUTDIR, exist_ok=True)
json.dump(R, open(OUT, 'w'), indent=1, ensure_ascii=False)
print('\n[written] ' + OUT)
print('[final] objdump xcheck %d/%d' % (R['pass'], R['total']))
sys.exit(0 if R['pass'] == R['total'] else 1)
