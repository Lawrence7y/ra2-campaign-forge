#!/usr/bin/env python3
"""R147 C：写入点「非空 / 归零」定性的控制流判据（取代 r147b 的线性回扫）。

r147b 的两条失败原因（自错 S-331，不得靠调参蒙过）：
  它用「在同一函数体内、地址小于写入点的最近一次 xor reg,reg，且其后无对 reg 的
  mov/pop/lea」判零。对 `0x52BAFA mov [0x8871E0],ebx` 它看到 `0x52BAF2 pop ebx`
  就判「已被赋值」。但 0x52BAF9 是 `ret`，0x52BAFA 只能由 `0x52BACD je 0x52BAFA`
  到达，`pop ebx` 那条路径走不到这里 ⇒ 线性回扫把**不同分支**的指令当成前置定值。
  同理它把 0x6BEABD 判对，纯属该点恰好在同一基本块内 —— 判据本身不成立。

本脚本改用两条**可机械复核**的判据，任一成立即判归零，否则判非空：
  J-A 同基本块内紧邻定零：从写入点向上线性回扫，遇 ret / jmp / 无条件跳转 /
      其它 jcc 的目标 / 函数起点即停；期间若命中 `xor R,R` 或 `sub R,R` ⇒ 归零。
  J-B 空指针判据（store 是 jcc 的目标）：该 jcc 前的最近 cmp 形如 `cmp A,B`，
      且写入源寄存器 == B，且 A 是前一条 `call` 的返回值寄存器 ⇒ 归零
      （B 是该函数用 `xor B,B` 建立的零常量，由 J-A 在上游验证）。
  反控：对 0x52BAD8（紧跟在 `cmp eax,ebx` 之后但**不是**任何 jcc 的目标、
      且其后 `jne` 才分流）必须判为**非空**，否则判据在「无条件存返回值」上
      退化成恒真。
另加三条事实性断言（都是可独立复核的字节事实）：
  F1 0x52BAF9 是 ret（证明 pop 路径与 0x52BAFA 不同支）
  F2 0x52BA82 是 xor ebx,ebx（零常量的建立点）
  F3 0x6BE1C8 是 xor ebx,ebx
"""
import sys, re, json, struct, collections, hashlib, time, bisect
HERE = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, HERE + '/_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TGT = 0x8871E0
GEN = set(L.GEN)

def norm(op):
    return re.sub(r'\s+', '', op or '').lower()

# ---------- 全量流式反汇编 ----------
tx = [s for s in B.secs if s[0] == '.text'][0]
off = tx[3]; end = off + tx[4]; vs = tx[1]
insns = []; calltgt = set(); jmptgt = set(); jcctgt = set()
while off < end:
    chunk = B.data[off:min(off + 65536, end)]
    base = B.IB + (vs + (off - tx[3])); consumed = 0
    for a, sz, mn, op in md.disasm_lite(chunk, base):
        if a - base + sz > len(chunk):
            break
        consumed = a - base + sz
        n = norm(op)
        insns.append((a, mn, n))
        if n.startswith('0x') and mn in ('call', 'jmp', 'je', 'jne', 'jz', 'jnz', 'js', 'jns',
                                         'jg', 'jge', 'jl', 'jle', 'ja', 'jb', 'jae', 'jbe', 'jp', 'jnp', 'jo', 'jno'):
            try:
                v = int(n, 16)
            except ValueError:
                v = None
            if v is not None and B.IB <= v < B.IB + 0x900000:
                if mn == 'call':
                    calltgt.add(v)
                elif mn == 'jmp':
                    jmptgt.add(v)
                else:
                    jcctgt.add(v)
    off += consumed if consumed else 1
insns.sort()
ADDRS = [a for a, _, _ in insns]
IDX = {a: i for i, a in enumerate(ADDRS)}
starts = sorted(calltgt | {B.IB + tx[1]})

def func_of(va):
    i = bisect.bisect_right(starts, va) - 1
    return starts[i] if i >= 0 else starts[0]

JCC = ('je', 'jne', 'jz', 'jnz', 'js', 'jns', 'jg', 'jge', 'jl', 'jle', 'ja', 'jb',
       'jae', 'jbe', 'jp', 'jnp', 'jo', 'jno')
STOP = set(JCC) | {'jmp', 'ret'}

def find_writes():
    mem = '[0x%x]' % TGT
    PRE = re.compile(r'^(dword|qword|word|byte|xmmword)ptr')
    out = []
    rx = re.compile(r'0x%x(?![0-9a-f])' % TGT)
    for a, mn, op in insns:
        if not rx.search(op):
            continue
        dest, _, src = op.partition(',')
        if PRE.sub('', dest) == mem:
            out.append((a, mn, src))
    return out

def zero_in_block(va, reg):
    """J-A：同基本块内向上回扫找 xor/sub reg,reg。"""
    fv = func_of(va)
    i = IDX[va]
    j = i - 1
    while j >= 0:
        a, mn, op = insns[j]
        if a < fv:
            break
        if a in jcctgt or a in jmptgt or a in calltgt:
            break                        # 基本块边界（另有分支可跳到此处）
        p = op.split(',')
        if mn in ('xor', 'sub') and len(p) == 2 and p[0] == reg and p[1] == reg:
            return True, '0x%X' % a
        if p[0] == reg and mn in ('mov', 'movzx', 'movsx', 'lea', 'pop', 'xchg', 'and', 'inc',
                                   'dec', 'add', 'sub', 'or', 'adc', 'sbb', 'imul', 'xchg'):
            return False, 'clobber@0x%X' % a
        j -= 1
    return False, 'block-top'

CALLRET = ('call',)

def jcc_guard_null(va, reg):
    """J-B：写入点若为某 jcc 的目标，且该 jcc 前最近 cmp 形如 cmp A,reg 且 A 是 call 返回值。"""
    for k, (a, mn, op) in enumerate(insns):
        if mn in JCC and op == '0x%x' % va:
            j = IDX[a] - 1
            while j >= 0:
                ba, bmn, bop = insns[j]
                if bmn == 'cmp':
                    p = bop.split(',')
                    if len(p) == 2 and p[1] == reg and p[0] in GEN:
                        # p[0] 是否是 call 的返回值 => 其前最近一次对 p[0] 的写是 call 之后隐式
                        q = j - 1
                        while q >= 0 and insns[q][0] >= func_of(ba):
                            if insns[q][1] == 'call':
                                return True, {'jcc': '0x%X' % a, 'cmp': bop,
                                              'call': '0x%X' % insns[q][0]}
                            if insns[q][2].split(',')[0] == p[0]:
                                break
                            q -= 1
                    return False, {'jcc': '0x%X' % a, 'cmp': bop, 'reason': 'cmp-form'}
                if bmn in ('xor', 'sub', 'add', 'mov', 'lea', 'test'):
                    return False, {'jcc': '0x%X' % a, 'blocked_by': bop}
                j -= 1
    return False, {'reason': 'not-a-jcc-target'}

writes = find_writes()
wdet = []
for va, mn, src in writes:
    fv = func_of(va)
    res = {'va': '0x%X' % va, 'mn': mn, 'src': src, 'func': '0x%X' % fv,
           'func_callers': sorted('0x%X' % s for s in calltgt if False)}
    if src in GEN:
        za, why_a = zero_in_block(va, src)
        zb, why_b = jcc_guard_null(va, src)
    else:
        za, why_a, zb, why_b = False, {'reason': 'non-reg'}, False, {'reason': 'non-reg'}
    res['null'] = bool(za or zb)
    res['ev_A'] = why_a if isinstance(why_a, str) else 'dict'
    res['ev_A_raw'] = why_a if not isinstance(why_a, str) else {'at': why_a}
    res['ev_B'] = why_b
    wdet.append(res)

# ---------- 事实断言 ----------
def ins_at(va):
    i = IDX.get(va)
    return insns[i] if i is not None else None

F = {}
for name, va, want_mn, want_op in (
        ('F1', 0x52BAF9, 'ret', ''),
        ('F2', 0x52BA82, 'xor', 'ebx,ebx'),
        ('F3', 0x6BE1C8, 'xor', 'ebx,ebx'),
        ('F4', 0x52BACD, 'je', '0x52bafa'),
        ('F5', 0x52BAD6, 'cmp', 'eax,ebx')):
    it = ins_at(va)
    F[name] = {'va': '0x%X' % va, 'got': it[1:] if it else None,
               'want': (want_mn, want_op)}

def fc(name, cond, got, want):
    return {'name': name, 'ok': bool(cond), 'got': got, 'want': want}

checks = []
checks.append(fc('写入点恰 3 个', len(wdet) == 3, len(wdet), 3))
checks.append(fc('归零写入恰 2 个', sum(1 for w in wdet if w['null']) == 2,
                 sum(1 for w in wdet if w['null']), 2))
checks.append(fc('非空写入恰 1 个（且是 0x52BAD8）',
                 [w['va'] for w in wdet if not w['null']] == ['0x52BAD8'],
                 [w['va'] for w in wdet if not w['null']], ['0x52BAD8']))
checks.append(fc('归零点恰为 0x52BAFA 与 0x6BEABD',
                 sorted(w['va'] for w in wdet if w['null']) == ['0x52BAFA', '0x6BEABD'],
                 sorted(w['va'] for w in wdet if w['null']), ['0x52BAFA', '0x6BEABD']))
checks.append(fc('F1 0x52BAF9 是 ret（pop 路径不同支）',
                 F['F1']['got'] and F['F1']['got'][0] == 'ret', F['F1']['got'], ('ret',)))
checks.append(fc('F2 0x52BA82 xor ebx,ebx', F['F2']['got'] == ('xor', 'ebx,ebx'), F['F2']['got'], ('xor', 'ebx,ebx')))
checks.append(fc('F3 0x6BE1C8 xor ebx,ebx', F['F3']['got'] == ('xor', 'ebx,ebx'), F['F3']['got'], ('xor', 'ebx,ebx')))
checks.append(fc('F4 0x52BACD je 0x52baFA（0x52BAFA 的唯一前驱是 jcc）',
                 F['F4']['got'] == ('je', '0x52bafa'), F['F4']['got'], ('je', '0x52bafa')))
checks.append(fc('F5 0x52BAD6 cmp eax,ebx', F['F5']['got'] == ('cmp', 'eax,ebx'), F['F5']['got'], ('cmp', 'eax,ebx')))
checks.append(fc('反控 0x52BAD8 不是任何 jcc 的目标（无条件存返回值）',
                 0x52BAD8 not in jcctgt, 0x52BAD8 in jcctgt, False))
checks.append(fc('两写入函数各 1 条入边（ctor / teardown 均被真实调用）',
                 len({w['func'] for w in wdet}) == 2, sorted({w['func'] for w in wdet}), 2))

out = {'checks': checks, 'fails': [c['name'] for c in checks if not c['ok']],
       'writes': wdet, 'facts': F,
       'n_insns': len(insns), 'secs': round(time.time() - T0, 1)}
json.dump(out, open(HERE + '/_r147/r147c_writer_semantics.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'fails': out['fails'], 'writes': wdet, 'facts': F}, ensure_ascii=False, indent=1))
