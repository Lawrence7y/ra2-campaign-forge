# -*- coding: utf-8 -*-
"""R219 m5：主会话独立复算 card B 的三项数字（§2.12 规则 D：子代理结论必须主会话复算）。

待复算：
  B-(i)   接受集总数：card B 报 15463(+9 esp) = 15472；R218 报 18930/18935；m2 报 18933。
  B-(ii)  s>=256 位点数：card B 报 744 / distinct 82；R218 报 931 / 91。
  B-(iii) UnitClass 槽域位点：card B 报 739；R218 报 925。
  B-(iv)  925 位点归并出的调用方函数数：card B 报 234（unresolved 436）；须用同一函数边界规则复算。

口径对齐：全部使用 m2 的逐字节 resync 线性 sweep（1394120 条，末指令 0x7e0ffd），
提交给 card B 对照，判定其 sweep 是否被固定 64KB 切块截断（R218 自错 S1 同类）。

正控：0x414471 必须在接受集；0x7bea07 必须在 s>=256 集。
反控 1：若把 sweep 换成「固定 64KB 块、块尾丢弃不完整指令、下一块从头」的坏口径，指令数必须显著小于 1394120。
反控 2：把接受判据放宽到含 esp，计数必须增加且增加量等于 esp 位数。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
T = P.B['.text']; LO, RAWOFF, RAWSZ = T['lo'], T['rawptr'], T['rawsize']

# ---------- good sweep: byte-resync, carry across chunk boundaries ----------
CHUNK = 0x10000
insns = []
cur_va, cur_off, remaining, nch = LO, RAWOFF, RAWSZ, 0
while remaining > 0:
    n = min(CHUNK, remaining)
    buf = P.RAW[cur_off:cur_off + n]
    la, ls = None, 0
    for a, sz, mn, ops in md.disasm_lite(buf, cur_va):
        insns.append((a, mn, ops)); la, ls = a, sz
    if la is None: break
    adv = (la + ls) - cur_va
    if adv <= 0: adv = n
    cur_va += adv; cur_off += adv; remaining -= adv; nch += 1
    del buf
print('[0] good sweep: insns=%d chunks=%d last=%#x (R218: 1394120 / 0x7e0ffd)'
      % (len(insns), nch, insns[-1][0]))

# ---------- bad sweep (反控 1): fixed 64KB, drop tail, restart ----------
bad = 0
for off in range(RAWOFF, RAWOFF + RAWSZ, CHUNK):
    buf = P.RAW[off:off + CHUNK]
    for a, sz, mn, ops in md.disasm_lite(buf, LO + (off - RAWOFF)):
        bad += 1
print('[0b] NEG CONTROL fixed-64KB restart sweep: insns=%d (must be < %d)'
      % (bad, len(insns)))

# ---------- accepted set ----------
MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)
GPR = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp')
POS = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)
NEG = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)\s*-\s*(0x[0-9a-f]+|\d+)$', re.I)
def parse(inner):
    s = inner.strip()
    m = POS.match(s)
    if m:
        return m.group(1).lower(), (int(m.group(2), 0) if m.group(2) else 0)
    m = NEG.match(s)
    if m:
        return m.group(1).lower(), -int(m.group(2), 0)
    return None, None

acc, esp_acc, neg = [], [], []
for a, mn, ops in insns:
    if mn not in ('call', 'jmp'): continue
    mm = MEM_RE.search(ops)
    if not mm: continue
    b, d = parse(mm.group(1))
    if b is None: continue
    if d < 0: neg.append((a, ops, b, d)); continue
    if b == 'esp': esp_acc.append(a); continue
    acc.append((a, b, d))
print('\n[1] accepted [reg+disp] no-index, esp excluded = %d  (m2: 18933 / R218: 18935)' % len(acc))
print('    esp-based excluded = %d  -> incl-esp = %d  (card B: 15463 + 9 = 15472)' % (len(esp_acc), len(acc) + len(esp_acc)))
print('    negative-disp excluded = %d  %s' % (len(neg), [(hex(a), o) for a, o, _, _ in neg]))
print('    POSITIVE CONTROL 0x414471 in set: %s' % any(x[0] == 0x414471 for x in acc))

hi = [x for x in acc if x[2] >= 0x400]
print('\n[2] s>=256 : count=%d distinct_s=%d  (R218: 931/91 ; card B: 744/82)'
      % (len(hi), len(set(x[2] // 4 for x in hi))))
dom = [x for x in hi if 256 <= x[2] // 4 < 344]
print('    UnitClass domain 256<=s<344 : %d  (R218: 925 ; card B: 739)' % len(dom))
print('    POSITIVE CONTROL 0x7bea07 in hi: %s' % any(x[0] == 0x7bea07 for x in hi))
print('    top s:', collections.Counter(x[2] // 4 for x in dom).most_common(6))

# ---------- caller-function grouping (same fixed rule as card B) ----------
def func_start(va, window=256):
    o = P.r2o(va); lo = max(P.r2o(LO), o - window); i = o - 1
    while i > lo:
        if P.RAW[i - 1] == 0xCC and P.RAW[i] == 0xCC:
            j = i
            while j < o and P.RAW[j] == 0xCC: j += 1
            return j + (LO - P.B['.text']['rawptr']), 'cc'
        i -= 1
    i = o - 1
    while i > lo:
        if P.RAW[i] == 0xC3 and P.RAW[i + 1] != 0xCC:
            return i + 1 + (LO - P.B['.text']['rawptr']), 'ret'
        i -= 1
    return None, 'unresolved'

grp = collections.defaultdict(int); kinds = collections.Counter()
for a, b, d in dom:
    f, k = func_start(a)
    kinds[k] += 1
    if f: grp[f] += 1
print('\n[3] caller-function grouping of the %d UnitClass-domain sites' % len(dom))
print('    resolved funcs = %d ; unresolved sites = %d' % (len(grp), kinds['unresolved']))
print('    resolver kinds = %s  (card B: {unresolved:436, ret:303})' % dict(kinds))
print('    top10 funcs:', sorted(grp.items(), key=lambda kv: -kv[1])[:10])
# distinct s per function
per = collections.defaultdict(set)
for a, b, d in dom:
    f, k = func_start(a)
    if f: per[f].add(d // 4)
mx = sorted(((len(v), k) for k, v in per.items()), reverse=True)[:5]
print('    functions with most distinct s:', mx)

# ---------- 反控 2 ----------
print('\n[4] NEG CONTROL 2: incl-esp count %d > esp-excluded %d : %s'
      % (len(acc) + len(esp_acc), len(acc), (len(acc) + len(esp_acc)) > len(acc)))

json.dump(dict(good_insns=len(insns), bad_insns=bad, acc=len(acc), esp=len(esp_acc),
               neg=len(neg), hi=len(hi), hi_s=len(set(x[2] // 4 for x in hi)),
               dom=len(dom), funcs=len(grp), unresolved=kinds['unresolved'],
               kinds=dict(kinds)),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m5.json', 'w'), indent=1)
print('\n[done] -> _r219/m5.json')
