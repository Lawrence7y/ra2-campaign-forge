#!/usr/bin/env python3
"""R147 D：写入点归零定性 —— 函数内**正向数据流**（取代 r147c 的基本块回扫）。

为什么必须做数据流（自错 S-332）：
  r147b 线性回扫 ⇒ 把 0x52BAF2 的 pop ebx（另一分支）当成 0x52BAFA 的前置定值，
  于是把「归零写」误判成「非空写」。
  r147c 改成「同基本块内回扫」⇒ 0x52BAFA 判对了，但 0x6BEABD 判错了：它的
  ebx=0 建立在函数入口块 0x6BE1C8，中间隔着 jcc 目标（基本块边界），回扫在边界
  处就停了，够不到上游。两个判据都只在「自己举的例子」上成立。
  正确做法：对写入点所在函数建**指令级 CFG**，对目标寄存器做 ZERO/NONZERO/UNKNOWN
  三格前向数据流，在分支汇合处取**交**（任一路径非零则 NONZERO），再看写入点处
  该寄存器是否 ZERO。格语义保守：只要不能证明为零就不判零。

同时给出 D-1..D-5 五条独立字节事实作互证，并给出两个反控：
  NEG 把 0x52BAFA 的源寄存器换成 eax 必须不再判零（证明判零不是恒真）；
  POS 0x52BAD8 的 eax 是 call 返回值，必须判 NONZERO/UNKNOWN（不是零）。
"""
import sys, re, json, struct, collections, time, bisect
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

tx = [s for s in B.secs if s[0] == '.text'][0]
off = tx[3]; end = off + tx[4]; vs = tx[1]
insns = []; calltgt = set()
while off < end:
    chunk = B.data[off:min(off + 65536, end)]
    base = B.IB + (vs + (off - tx[3])); consumed = 0
    for a, sz, mn, op in md.disasm_lite(chunk, base):
        if a - base + sz > len(chunk):
            break
        consumed = a - base + sz
        n = norm(op)
        insns.append((a, mn, n))
        if mn == 'call' and n.startswith('0x'):
            v = int(n, 16)
            if B.IB <= v < B.IB + 0x900000:
                calltgt.add(v)
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

def writes():
    mem = '[0x%x]' % TGT
    PRE = re.compile(r'^(dword|qword|word|byte|xmmword)ptr')
    rx = re.compile(r'0x%x(?![0-9a-f])' % TGT)
    out = []
    for a, mn, op in insns:
        if not rx.search(op):
            continue
        d, _, s = op.partition(',')
        if PRE.sub('', d) == mem:
            out.append((a, mn, s))
    return out

# ---------- 函数内 CFG + 数据流 ----------
def func_body(fv):
    i = bisect.bisect_right(ADDRS, fv) - 1
    if i < 0:
        i = 0
    body = []
    while i < len(insns) and func_of(insns[i][0]) == fv:
        body.append(insns[i])
        i += 1
    return body

def succs(body, k):
    a, mn, op = body[k]
    n = len(body)
    out = []
    if mn in JCC and op.startswith('0x'):
        t = int(op, 16)
        if t in [x[0] for x in body]:
            out.append(body.index([x for x in body if x[0] == t][0]))
        if k + 1 < n:
            out.append(k + 1)
    elif mn == 'jmp' and op.startswith('0x'):
        t = int(op, 16)
        if t in [x[0] for x in body]:
            out.append(body.index([x for x in body if x[0] == t][0]))
    elif mn == 'ret' or mn == 'iretd':
        pass
    elif k + 1 < n:
        out.append(k + 1)
    return out

def dest_reg(op, mn):
    """只有真正写目的的指令才返回目的寄存器。
    S-333：首版把 push/cmp/test/jcc 的目的也当写入（push ebx 被当成写 ebx），
    于是 0x6BE1C0 里 ebx 被误标 UNKNOWN，0x6BEABD 的归零判定失败。"""
    if mn in ('push', 'cmp', 'test', 'jmp', 'ret', 'call', 'nop', 'int3') or mn in JCC:
        return None
    p = op.split(',')
    if not p:
        return None
    d = p[0]
    d = re.sub(r'^(dword|qword|word|byte|xmmword)ptr', '', d)
    m = re.match(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp|al|bl|cl|dl|ah|bh|ch|dh)$', d)
    return m.group(1) if m else None

# 格：0=ZERO, 1=NONZERO, 2=UNKNOWN
Z, NZ, UN = 0, 1, 2

def transfer(state, mn, op):
    reg = dest_reg(op, mn)
    if reg is None:
        return state
    s = dict(state)
    p = [x for x in op.split(',')]
    if mn in ('xor', 'sub') and len(p) == 2 and p[0] == reg and p[1] == reg:
        s[reg] = Z
    elif mn in ('mov', 'movzx', 'movsx', 'lea', 'pop', 'xchg'):
        s[reg] = UN
    elif mn == 'call':
        pass
    else:
        s[reg] = UN
    return s

def zero_dom(fv, target_va, reg):
    """返回 (是否在 target_va 处证明 reg==0, 该点的格值, 支撑点)"""
    body = func_body(fv)
    if not body:
        return False, None, 'empty'
    n = len(body)
    addr2k = {x[0]: k for k, x in enumerate(body)}
    IN = [None] * n
    IN[0] = {r: UN for r in GEN}
    work = collections.deque([0])
    it = 0
    while work and it < 200000:
        it += 1
        k = work.popleft()
        st = IN[k]
        if st is None:
            continue
        nxt = transfer(st, body[k][1], body[k][2])
        for s in succs(body, k):
            if IN[s] is None:
                IN[s] = dict(nxt)
                work.append(s)
            else:
                merged = dict(IN[s])
                changed = False
                for r, v in nxt.items():
                    # meet：相等则保留，否则 UNKNOWN
                    if merged.get(r, UN) != v:
                        if merged.get(r, UN) != UN:
                            merged[r] = UN
                            changed = True
                if changed:
                    IN[s] = merged
                    work.append(s)
    k = addr2k.get(target_va)
    if k is None:
        return False, None, 'not-in-body'
    st = IN[k]
    if st is None:
        return False, None, 'unreachable'
    v = st.get(reg, UN)
    return v == Z, v, 'dataflow'

# ---------- 主流程 ----------
wr = writes()
wdet = []
for va, mn, src in wr:
    fv = func_of(va)
    if src in GEN:
        ok, lv, how = zero_dom(fv, va, src)
    else:
        ok, lv, how = False, None, 'non-reg'
    # 该写入函数被谁调用
    inbound = [k for k, (a, m2, o2) in enumerate(insns) if m2 == 'call' and o2 == '0x%x' % fv]
    wdet.append({'va': '0x%X' % va, 'mn': mn, 'src': src, 'func': '0x%X' % fv,
                 'proved_zero': ok, 'lattice': {0: 'ZERO', 1: 'NONZERO', 2: 'UNKNOWN'}.get(lv, lv),
                 'via': how,
                 'callers': ['0x%X' % insns[k][0] for k in inbound],
                 'caller_funcs': sorted({'0x%X' % func_of(insns[k][0]) for k in inbound})})

# ---------- 反控 ----------
neg = None
for w in wdet:
    if w['va'] == '0x52BAFA':
        fv = int(w['func'], 16)
        ok_other, lv_other, _ = zero_dom(fv, int(w['va'], 16), 'eax')
        neg = {'site': '0x52BAFA', 'reg': 'eax', 'proved_zero': ok_other,
               'lattice': {0: 'ZERO', 1: 'NONZERO', 2: 'UNKNOWN'}.get(lv_other, lv_other)}
pos = None
for w in wdet:
    if w['va'] == '0x52BAD8':
        pos = {'site': '0x52BAD8', 'reg': 'eax', 'proved_zero': w['proved_zero'],
               'lattice': w['lattice']}

# ---------- 字节事实 ----------
def ins_at(va):
    i = IDX.get(va)
    return insns[i] if i is not None else None

FACTS = {}
for nm, va in (('D1_ret_52BAF9', 0x52BAF9), ('D2_xor_52BA82', 0x52BA82),
               ('D3_xor_6BE1C8', 0x6BE1C8), ('D4_je_52BACD', 0x52BACD),
               ('D5_cmp_52BAD6', 0x52BAD6)):
    it = ins_at(va)
    FACTS[nm] = {'va': '0x%X' % va, 'got': list(it[1:]) if it else None}

def fc(n, c, got, want):
    return {'name': n, 'ok': bool(c), 'got': got, 'want': want}

checks = [
    fc('写入点恰 3 个', len(wdet) == 3, len(wdet), 3),
    fc('非空写入恰 1 个且为 0x52BAD8',
       [w['va'] for w in wdet if not w['proved_zero']] == ['0x52BAD8'],
       [w['va'] for w in wdet if not w['proved_zero']], ['0x52BAD8']),
    fc('归零写入恰 2 个且为 0x52BAFA/0x6BEABD',
       sorted(w['va'] for w in wdet if w['proved_zero']) == ['0x52BAFA', '0x6BEABD'],
       sorted(w['va'] for w in wdet if w['proved_zero']), ['0x52BAFA', '0x6BEABD']),
    fc('D1 0x52BAF9 = ret', FACTS['D1_ret_52BAF9']['got'][0] == 'ret', FACTS['D1_ret_52BAF9']['got'], 'ret'),
    fc('D2 0x52BA82 = xor ebx,ebx', FACTS['D2_xor_52BA82']['got'] == ['xor', 'ebx,ebx'],
       FACTS['D2_xor_52BA82']['got'], ['xor', 'ebx,ebx']),
    fc('D3 0x6BE1C8 = xor ebx,ebx', FACTS['D3_xor_6BE1C8']['got'] == ['xor', 'ebx,ebx'],
       FACTS['D3_xor_6BE1C8']['got'], ['xor', 'ebx,ebx']),
    fc('D4 0x52BACD = je 0x52bafa', FACTS['D4_je_52BACD']['got'] == ['je', '0x52bafa'],
       FACTS['D4_je_52BACD']['got'], ['je', '0x52bafa']),
    fc('NEG 反控：0x52BAFA 的 eax 不判零', neg and neg['proved_zero'] is False,
       neg, 'False'),
    fc('POS 反控：0x52BAD8 的 eax 不判零（call 返回值）', pos and pos['proved_zero'] is False,
       pos, 'False'),
    fc('两写入函数各至少 1 条入边',
       all(len(w['callers']) >= 1 for w in wdet),
       {w['va']: len(w['callers']) for w in wdet}, '>=1 each'),
]

out = {'checks': checks, 'fails': [c['name'] for c in checks if not c['ok']],
       'writes': wdet, 'facts': FACTS, 'neg': neg, 'pos': pos,
       'n_insns': len(insns), 'secs': round(time.time() - T0, 1)}
json.dump(out, open(HERE + '/_r147/r147d_writer_dataflow.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'fails': out['fails'], 'writes': wdet, 'neg': neg, 'pos': pos,
                  'secs': out['secs']}, ensure_ascii=False, indent=1))
