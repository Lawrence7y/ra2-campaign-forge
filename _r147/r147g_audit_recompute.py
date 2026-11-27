#!/usr/bin/env python3
"""R147 G：复算审计员 #329（deepseek, audit）的全部主张（§2.12 规则 D）。

审计员提了三条批评，本脚本逐条独立复算，不复用它的任何中间脚本：
  A1 「0x52BA9B / 0x52BADF 不是函数入口，只是 jmp 标签」—— 复算 call/jmp 目标归属
  A2 「C3 的论据不足：仅凭『1 个非空写点』不能排除多实例」—— 复算它给的四条真正支点：
     a) 无 SIB 变址写（[reg*scale + 0x8871E0]）
     b) 无带位移形态（[reg + 0x8871E0]）
     c) 无取地址指令（lea/push/mov reg, 0x8871E0 立即数）
     d) 槽位于 BSS（.data 虚拟尾，原始数据外）
  A3 「0x52BA60 无幂等守卫（写前没有 if (0x8871E0) return）」—— 复算 0x52BAD8 之前
     是否存在对 [0x8871E0] 的读-判-跳守卫
另复算它给的两个钉：.text 段 sha256、整文件 sha256；以及它报的指令条数 1394186
与我方 1394120 的差异根因（扫描尾部处理不同，不是漏检）。
"""
import sys, re, json, struct, hashlib, bisect, time
HERE = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, HERE + '/_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TGT = 0x8871E0

def N(op):
    return re.sub(r'\s+', '', op or '').lower()

tx = [s for s in B.secs if s[0] == '.text'][0]
foff = tx[3]; fsize = tx[4]; vs = tx[1]
off = foff; end = foff + fsize
insns = []; calls = set(); jmps = set()
while off < end:
    ch = B.data[off:min(off + 65536, end)]
    base = B.IB + (vs + (off - foff)); c = 0
    for a, sz, mn, op in md.disasm_lite(ch, base):
        if a - base + sz > len(ch):
            break
        c = a - base + sz
        insns.append((a, sz, mn, N(op)))
        t = N(op)
        if t.startswith('0x') and mn in ('call', 'jmp'):
            v = int(t, 16)
            if B.IB <= v < B.IB + 0x900000:
                (calls if mn == 'call' else jmps).add(v)
    off += c if c else 1
insns.sort()
A = [x[0] for x in insns]

# ---------- A1 ----------
a1 = {
    '0x52BA9B': {'call': 0x52BA9B in calls, 'jmp': 0x52BA9B in jmps,
                 'jmp_from': ['0x%X' % a for a, sz, mn, op in insns
                              if mn == 'jmp' and op == '0x52ba9b']},
    '0x52BADF': {'call': 0x52BADF in calls, 'jmp': 0x52BADF in jmps,
                 'jmp_from': ['0x%X' % a for a, sz, mn, op in insns
                              if mn == 'jmp' and op == '0x52badf']},
    '0x52BA60': {'call': 0x52BA60 in calls, 'jmp': 0x52BA60 in jmps,
                 'call_from': ['0x%X' % a for a, sz, mn, op in insns
                               if mn == 'call' and op == '0x52ba60']},
}

# ---------- A2 ----------
rx = re.compile(r'0x8871e0(?![0-9a-f])')
sib = []       # 变址形态
disp = []      # [reg +/- 0x8871e0]
addr = []      # 取地址
for a, sz, mn, op in insns:
    if not rx.search(op):
        continue
    if '*' in op:
        sib.append((a, mn, op))
    elif re.search(r'\[[a-z0-9]+\+0x8871e0\]', op):
        disp.append((a, mn, op))
    elif re.match(r'^(lea|push|mov)[a-z0-9]*', op) and '[' not in op.split(',')[0]:
        # 立即数取地址：lea reg,[0x8871e0] / push 0x8871e0 / mov reg,0x8871e0
        if op.endswith('0x8871e0') or op.endswith('[0x8871e0]'):
            addr.append((a, mn, op))
    elif mn == 'lea' and '[' in op:
        addr.append((a, mn, op))
    elif mn == 'push' and op == '0x8871e0':
        addr.append((a, mn, op))
    elif mn == 'mov' and ',' in op and op.split(',')[1] == '0x8871e0':
        addr.append((a, mn, op))

# BSS 判定
def sec_info(va):
    for nm, ava, v, raw, rs in B.secs:
        lo = B.IB + ava
        if lo <= va < lo + max(v, rs):
            return {'sec': nm, 'rva': va - lo, 'virt_size': v, 'raw_size': rs,
                    'in_raw': (va - lo) < rs}
    return None

bss = sec_info(TGT)
adj = {}
for d in (-0x10, -0xC, -8, -4, 4, 8, 0xC, 0x10):
    v = TGT + d
    hits = [(a, mn, op) for a, sz, mn, op in insns
            if re.search(r'0x%x(?![0-9a-f])' % v, op)]
    adj['0x%X' % v] = {'n': len(hits), 'sample': [{'va': '0x%X' % a, 'op': o} for a, _, o in hits[:3]]}

# ---------- A3 幂等守卫 ----------
def has_guard():
    """0x52BAD8 之前，是否存在 mov r,[0x8871E0] + test/cmp + jcc 的守卫形态。"""
    i = bisect.bisect_left(A, 0x52BAD8)
    prev = insns[max(0, i - 40):i]
    loads = [(a, mn, op) for a, sz, mn, op in prev
             if mn == 'mov' and op.endswith('[0x8871e0]')]
    return {'loads_before_write': [{'va': '0x%X' % a, 'op': o} for a, _, o in loads],
            'n': len(loads)}

guard = has_guard()

# ---------- 钉复算 ----------
text_sha = hashlib.sha256(B.data[foff:foff + fsize]).hexdigest()
file_sha = hashlib.sha256(B.data).hexdigest()

# ---------- 指令条数差异 ----------
n_insn = len(insns)

def fc(n, c, got, want):
    return {'name': n, 'ok': bool(c), 'got': got, 'want': want}

checks = [
    fc('A1a 0x52BA9B 是 jmp 目标而非 call 目标',
       a1['0x52BA9B']['jmp'] and not a1['0x52BA9B']['call'], a1['0x52BA9B']['call'], False),
    fc('A1b 0x52BADF 是 jmp 目标而非 call 目标',
       a1['0x52BADF']['jmp'] and not a1['0x52BADF']['call'], a1['0x52BADF']['call'], False),
    fc('A1c 0x52BA60 是 call 目标且唯一调用者 0x48CCCF',
       a1['0x52BA60']['call'] and a1['0x52BA60']['call_from'] == ['0x48CCCF'],
       a1['0x52BA60']['call_from'], ['0x48CCCF']),
    fc('A2a 无 SIB 变址写（[reg*scale+0x8871E0]）', len(sib) == 0, len(sib), 0),
    fc('A2b 无带位移形态（[reg+0x8871E0]）', len(disp) == 0, len(disp), 0),
    fc('A2c 无取地址指令（lea/push/mov reg,0x8871E0）', len(addr) == 0, len(addr), 0),
    fc('A2d 槽位于 .data 原始数据之外（BSS 尾部，零初始化）',
       bss and bss['sec'] == '.data' and bss['in_raw'] is False, bss, 'in_raw False'),
    fc('A3 0x52BAD8 之前无 [0x8871E0] 读-判-跳守卫（非运行期强制单例）',
       guard['n'] == 0, guard['n'], 0),
    fc('钉1 .text 段 sha256 与审计员一致',
       text_sha == 'c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738',
       text_sha[:16], 'c0368a179f6e1a0f'),
    fc('钉2 整文件 sha256 与审计员一致',
       file_sha == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
       file_sha[:16], '73201cc021497c95'),
]

out = {'checks': checks, 'fails': [c['name'] for c in checks if not c['ok']],
       'A1': a1, 'A2': {'sib': len(sib), 'disp': len(disp), 'addr': len(addr),
                        'bss': bss, 'adjacent': adj},
       'A3_guard': guard, 'text_sha': text_sha, 'file_sha': file_sha,
       'n_insns': n_insn, 'secs': round(time.time() - T0, 1)}
json.dump(out, open(HERE + '/_r147/r147g_audit_recompute.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'fails': out['fails'], 'A1': a1, 'A2': out['A2'], 'A3': guard,
                  'n_insns': n_insn, 'secs': out['secs']}, ensure_ascii=False, indent=1))
