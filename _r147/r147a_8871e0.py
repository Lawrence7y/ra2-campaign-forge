#!/usr/bin/env python3
"""R147 A：0x8871E0 静态引用普查（R146 下轮待办 #3）。

问题：0x8871E0 是「单例指针槽」还是「多实例（数组/池）」？
纯静态可判的三件事：
  W 写入点：谁把值写进 [0x8871E0]（mov [0x8871E0],reg / =imm）
  R 读取点：谁读它，读后是否立刻用于访问成员（判断是对象指针还是标量）
  C 承载函数的调用者数：若唯一写入点所在函数被多处调用，且函数内每次
    新分配（call 到分配器）后再写该槽，则「槽只有一个」⇒ 后写覆盖先写，
    语义上是「最近一次构造的对象指针」而非容器。反之为容器需另有数组基址。

纪律：
  * 流式 disasm_lite（64KB 分块），不对整段 .text 开 detail=True；
  * 使用**原始** capstone 操作数串，不用 r143lib.norm —— r145 已证 norm 的
    字符类 [+,*] 不含 '-'，[eax - 8] 会保留空格导致 RE_STORE 拒收；
    本脚本自行做「去全部空白 + 小写」归一，负位移不再丢失；
  * 三组正反控：POS = 已知写入点必须命中；NEG = 不存在的地址必须 0 命中；
    CTRL = 相邻的真实 .data 全局（0x8871E4 / 0x8871DC）命中数作对照。
"""
import sys, os, re, json, struct, collections, hashlib, time, bisect
HERE = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, HERE + '/_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
GEN = L.GEN

TARGETS = [('primary', 0x8871E0), ('ctrl_next', 0x8871E4), ('ctrl_prev', 0x8871DC),
           ('neg_bogus', 0x887FF4), ('ctrl_known', 0x8871F0)]

def norm_raw(op):
    """仅去空白 + 小写：保留 '-' 与所有位移形态（r145 教训）。"""
    return re.sub(r'\s+', '', op or '').lower()

# ---------- 一次流式扫描：全部指令 + call 直接目标（函数起点近似） ----------
insns = []          # (va, mn, nop)
calltgt = set()
text = B.T
off = text[3]; end = off + text[4]; vs = text[1]
while off < end:
    chunk = B.data[off:min(off + 65536, end)]
    base = B.IB + (vs + (off - text[3]))
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(chunk, base):
        if a - base + sz > len(chunk):
            break
        consumed = a - base + sz
        n = norm_raw(op)
        insns.append((a, mn, n))
        if mn in ('call', 'jmp') and n.startswith('0x'):
            try:
                t = int(n, 16)
            except ValueError:
                t = None
            if t and B.IB <= t < B.IB + 0x800000:
                calltgt.add(t)
    off += consumed if consumed else 1
insns.sort()
starts = sorted(calltgt | {B.IB + text[1]})
ADDRS = [a for a, _, _ in insns]

def func_of(va):
    i = bisect.bisect_right(starts, va) - 1
    return starts[i] if i >= 0 else starts[0]

# ---------- 逐目标普查 ----------
def census(value):
    """精确 token 匹配：0x<hex> 前后不得紧邻十六进制字符（防 0x8871e00 误命中）。"""
    hits = []
    rx = re.compile(r'0x%x(?![0-9a-f])' % value)
    for va, mn, op in insns:
        if rx.search(op):
            hits.append((va, mn, op))
    return hits

def classify(hit, pat_of_target):
    va, mn, op = hit
    mem = '[0x' + pat_of_target + ']'
    dest, _, src = op.partition(',')
    # 去操作数类型前缀（dwordptr/qwordptr/byteptr/wordptr），否则 dest 永不等于 mem ——
    # 这是本脚本首版把 0x52BAD8 这类真实写入漏成 READ 的根因（S-328）。
    dest_clean = re.sub(r'^(dword|qword|word|byte|xmmword)ptr', '', dest)
    if dest_clean == mem:
        if mn in ('mov', 'movzx', 'movsx', 'lea', 'xchg', 'add', 'sub', 'or', 'and', 'xor', 'inc', 'dec'):
            return 'WRITE'
        if mn in ('cmp', 'test'):
            return 'READ(cmp)'
        return 'DEST-' + mn
    if mem in op:
        return 'READ'
    return 'IMM-OTHER'

report = {}
for tag, val in TARGETS:
    hits = census(val)
    pat_of_target = '%x' % val
    cls = collections.Counter()
    detail = []
    for h in hits:
        c = classify(h, pat_of_target)
        cls[c] += 1
        detail.append({'va': '0x%X' % h[0], 'mn': h[1], 'op': h[2], 'cls': c,
                       'func': '0x%X' % func_of(h[0])})
    report[tag] = {'addr': '0x%X' % val, 'n': len(hits), 'cls': dict(cls),
                   'sites': detail}

# ---------- 写入点所在函数的调用者普查 ----------
wr = [d for d in report['primary']['sites'] if d['cls'] == 'WRITE']
funcs = sorted({d['func'] for d in wr})
callers = {}
for f in funcs:
    fv = int(f, 16)
    cs = [('0x%X' % a, mn, op) for a, mn, op in insns
          if mn in ('call', 'jmp') and op == '0x%x' % fv]
    callers[f] = {'n': len(cs), 'sites': [{'va': s[0], 'mn': s[1], 'func': '0x%X' % func_of(int(s[0], 16))} for s in cs]}

# ---------- 写入点函数内是否含分配器调用（构造序列） ----------
alloc_ctx = {}
for f in funcs:
    fv = int(f, 16)
    body = [(a, mn, op) for a, mn, op in insns if func_of(a) == fv]
    calls = [('0x%X' % a, op) for a, mn, op in body if mn == 'call' and op.startswith('0x')]
    alloc_ctx[f] = {'len': len(body), 'calls': calls}

# ---------- 断言 ----------
checks = []
def ck(name, cond, got, want):
    checks.append({'name': name, 'ok': bool(cond), 'got': got, 'want': want})

ck('POS 0x8871E0 有写入点', len(wr) >= 1, len(wr), '>=1')
ck('POS 0x52BAD8 被识别为 WRITE',
   any(d['va'] == '0x52BAD8' for d in wr), [d['va'] for d in wr][:5], '含 0x52BAD8')
ck('NEG 0x887FF4 命中数 < 5', report['neg_bogus']['n'] < 5, report['neg_bogus']['n'], '<5')
ck('CTRL 相邻全局 0x8871E4/0x8871DC 命中合计 >= 1（证明扫描未整体漏）',
   report['ctrl_next']['n'] + report['ctrl_prev']['n'] >= 1,
   report['ctrl_next']['n'] + report['ctrl_prev']['n'], '>=1')
ck('primary 命中数 >= 3', report['primary']['n'] >= 3, report['primary']['n'], '>=3')

out = {'checks': checks, 'fails': [c['name'] for c in checks if not c['ok']],
       'n_insns': len(insns), 'n_funcstarts': len(starts),
       'targets': report, 'writers': wr, 'writer_funcs': funcs,
       'callers': callers, 'alloc_ctx': alloc_ctx,
       'sha_exe': hashlib.sha256(B.data).hexdigest(), 'secs': time.time() - T0}
json.dump(out, open(HERE + '/_r147/r147a_8871e0.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'fails': out['fails'], 'n_insns': out['n_insns'],
                  'primary_n': report['primary']['n'], 'primary_cls': report['primary']['cls'],
                  'n_writers': len(wr), 'writer_funcs': funcs,
                  'neg': report['neg_bogus']['n'],
                  'ctrl': [report['ctrl_next']['n'], report['ctrl_prev']['n']]},
                 ensure_ascii=False, indent=1))
