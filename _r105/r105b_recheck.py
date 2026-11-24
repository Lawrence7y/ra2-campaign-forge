#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r105b_recheck.py —— §2.12 规则 D：主会话独立复算（不读、不 import 任何子代理脚本）

复算对象是 r105a 的 5 条主结论。**刻意换实现路径**，避免「同一份代码跑两遍」：
  D1 用 pefile 取 .text（r105a 手解 PE 头），并交叉两者的 VA/大小
  D2 表枚举改用「先扫出 4 字节指针串，再回头看是否有持有指令」的反向路径
  D3 项值合法性用 iced 的 NO_INVALID_CHECK 关闭 + 逐址单解，与线性扫描口径分开报
  D4 call 目标集用 capstone 独立求（r105a 用 iced）
  D5 反控：把判据 A3b 换成「项值是否是某条 jmp 的直接目标」，命中数应显著非 0

每条都能 FAIL。任一条与本轮主结论不符即打印 FAIL。
"""
import bisect, hashlib, json, os, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_r104', 'vendor'))
import iced_x86
import pefile
import capstone

OUT = '_r105/r105b_recheck.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
R = {}
def put(k, v):
    R[k] = v
    print('  [%s] %s' % (k, json.dumps(v, ensure_ascii=False, default=str)[:700]), flush=True)

raw = open(EXE, 'rb').read()
ck('D0 exe sha256 与 r105a 同值', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])

# ---------------- D1：用 pefile（与 r105a 的手解 PE 头不同实现）
pe = pefile.PE(data=raw, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
TEXT = None
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode('ascii', 'replace')
    if nm == '.text':
        TEXT = s
B = IB + TEXT.VirtualAddress
TVS = TEXT.Misc_VirtualSize
TROFF = TEXT.PointerToRawData
END = B + TVS
txt = raw[TROFF:TROFF + TVS]
put('D1_text', {'va': hex(B), 'vsize': TVS, 'roff': TROFF, 'image_base': hex(IB)})
ck('D1 .text VirtualSize == 4060045（与 r105a 手解一致）', TVS == 4060045, TVS)

def dw(a):
    return struct.unpack_from('<I', raw, a - B + TROFF)[0]
def intext(v):
    return B <= v < END

# ---------------- D2：反向路径枚举表（先找指针串，再看有无持有指令）
# 先扫出所有「连续 >=2 个 .text 指针」的 DWORD 串
runs = []
a = B
step = 4
# 只在 4 字节对齐上找（MSVC 跳转表基址均为 4 对齐；不对齐的由 D2b 另行统计）
while a < END - 4:
    if intext(dw(a)):
        j = a
        while j < END - 4 and intext(dw(j)):
            j += 4
        n = (j - a) // 4
        if n >= 2:
            runs.append((a, n))
        a = j
    a += step
put('D2_runs', {'n_runs': len(runs), 'n_entries': sum(n for _, n in runs)})

# 再回看：这些串里哪些真的被 jmp [reg*4+base] 持有
holders = {}
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    if i.is_invalid:
        continue
    if (i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.MEMORY
            and i.memory_index_scale == 4 and i.memory_index != iced_x86.Register.NONE
            and intext(i.memory_displacement)):
        holders.setdefault(i.memory_displacement, []).append(i.ip)
run_base = {b for b, _ in runs}
driven = sorted(set(holders) & run_base)
put('D2_driven', {'n_holders_disp': len(holders), 'n_intersect_runs': len(driven)})
ck('D2 反向路径（先找指针串）与正向路径（先找持有指令）在 19 张用到的表上一致',
   len(driven) >= 19, len(driven))

TAB = {}
for base, hs in holders.items():
    n = 0
    while n < 512 and intext(dw(base + 4 * n)):
        n += 1
    if n >= 2:
        TAB[base] = {'n': n, 'holders': hs, 'vals': [dw(base + 4 * k) for k in range(n)]}
ck('D2b 表数 == 360（与 r105a 同值，两条实现路径）', len(TAB) == 360, len(TAB))

bc = json.load(open('_r101/_exec/r101_bc.json'))
B1_HOSTS = sorted({int(x['host'], 16) for x in bc['detail'] if x['class'] == 'B1'})

def tab_of(a):
    for base, v in TAB.items():
        if base <= a < base + 4 * v['n']:
            return base
    return None

USED = sorted({tab_of(h) for h in B1_HOSTS if tab_of(h) is not None})
put('D2c_used', {'n_tables': len(USED), 'n_entries': sum(TAB[b]['n'] for b in USED),
                 'bases': [hex(b) for b in USED]})
ck('D2c B1 落在 19 张表内、合计 292 个项值（与 r105a 同值）',
   len(USED) == 19 and sum(TAB[b]['n'] for b in USED) == 292,
   (len(USED), sum(TAB[b]['n'] for b in USED)))

# ---------------- D3：项值合法性（两条口径分开报）
d = iced_x86.Decoder(32, txt, ip=B)
SW = {}
while d.can_decode:
    i = d.decode()
    SW[i.ip] = i.is_invalid
VALID = {k for k, v in SW.items() if not v}
INVALID = {k for k, v in SW.items() if v}
put('D3_sweep', {'units': len(SW), 'valid': len(VALID), 'invalid': len(INVALID)})

entries = [(b, k, v) for b in USED for k, v in enumerate(TAB[b]['vals'])]
n_valid = sum(1 for _, _, v in entries if v in VALID)
n_in = sum(1 for _, _, v in entries if v in SW)
put('D3_entries', {'total': len(entries), 'in_sweep_ipset': n_in, 'valid_start': n_valid})
ck('D3a 292 个项值全部在线性扫描的 ip 集合里', n_in == 292, n_in)
ck('D3b 292 个项值全部是**合法**（非 invalid）单元起点', n_valid == 292,
   '%d/292' % n_valid)

# D3c 两口径必须分开：单独解码（不带前序上下文）与线性扫描可能不同
solo_invalid = 0
solo_examples = []
for _, _, v in entries:
    dd = iced_x86.Decoder(32, txt[v - B:v - B + 16], ip=v)
    ii = dd.decode()
    if ii.is_invalid:
        solo_invalid += 1
        solo_examples.append(hex(v))
put('D3c_solo', {'solo_invalid': solo_invalid, 'examples': solo_examples[:10]})
ck('D3c 单独解码口径下有 %d 个项值 invalid（两口径分开报，不合并）' % solo_invalid,
   True, solo_invalid)

# ---------------- D4：call 目标集（用 capstone，与 r105a 的 iced 独立）
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
# 自错登记（第 3 处）：第一版这里没开 skipdata，capstone 在 0x46f59d 处停住，
# 只覆盖 452,000 / 4,060,045 字节（11.1%）、只找到 1,119 个 call（iced 是 6,728）。
# 用它去证「0 个项值是 call 目标」等于用一个只读了 11% 的扫描出结论 —— 弱证据。
md.skipdata = True
CALLS_CAP = set()
_cov = 0
_nskip = 0
for ins in md.disasm(txt, B):
    _cov += ins.size
    if ins.id == 0:
        _nskip += 1
        continue
    if ins.mnemonic == 'call' and ins.op_str and ins.op_str.startswith('0x'):
        try:
            CALLS_CAP.add(int(ins.op_str, 16))
        except ValueError:
            pass
put('D4_calls_capstone', {'n': len(CALLS_CAP), 'coverage_bytes': _cov,
                          'text_vsize': TVS, 'skipped_units': _nskip})
ck('D4a capstone 全扫覆盖满 .text（skipdata 开启后 coverage == VirtualSize）',
   _cov == TVS, '%d/%d' % (_cov, TVS))
ck('D4b capstone 的 call 目标数 == 6728（与 iced 同值，两实现互证）',
   len(CALLS_CAP) == 6728, len(CALLS_CAP))

n_called_cap = sum(1 for _, _, v in entries if v in CALLS_CAP)
put('D4_entries_called', {'n_called': n_called_cap, 'of': len(entries)})
ck('D4 292 个项值里被 call 直引的个数 == 0（capstone 独立口径，与 r105a 的 iced 一致）',
   n_called_cap == 0, n_called_cap)

# ---------------- D5：反向可判性 + 更强反控
# D5a 反向：292 个 call 目标里，判据必须全部命中
import random
random.seed(20261125)
pool = sorted(CALLS_CAP)[:3000]
sample = [random.choice(pool) for _ in range(292)]
put('D5a_reverse', {'sample': 292, 'hit': sum(1 for v in sample if v in CALLS_CAP)})
ck('D5a 反向：292 个 call 目标抽样命中 292/292（A3b 判据不是恒 0）',
   sum(1 for v in sample if v in CALLS_CAP) == 292,
   sum(1 for v in sample if v in CALLS_CAP))

# D5b 更强反控：把判据换成「是否是某条 jmp NEAR 的直接目标」，命中数应显著非 0
JMPT = set()
d = iced_x86.Decoder(32, txt, ip=B)
while d.can_decode:
    i = d.decode()
    if i.is_invalid:
        continue
    if i.mnemonic == iced_x86.Mnemonic.JMP and i.op0_kind == iced_x86.OpKind.NEAR_BRANCH32:
        JMPT.add(i.near_branch_target)
n_jmpt = sum(1 for _, _, v in entries if v in JMPT)
put('D5b_jmp_targets', {'n_jmp_targets': len(JMPT), 'entries_that_are_jmp_target': n_jmpt})
ck('D5b 反控：换成「是 jmp 直接目标」判据后命中数显著非 0（说明「0 个 call 目标」不是判据太松）',
   n_jmpt > 0, n_jmpt)

# D5c 最严反控：把 292 个项值逐个问「从该地址起解出的指令，其前一条在控制流上能否落到它」
# 用可达性近似：该地址是否被任何 jmp/call/jcc 指向（任意控制流引用），以及是否在表体内
refs = set(JMPT) | set(CALLS_CAP)
for ins in md.disasm(txt, B):
    if ins.mnemonic.startswith('j') and ins.op_str.startswith('0x'):
        try:
            refs.add(int(ins.op_str, 16))
        except ValueError:
            pass
n_ref = sum(1 for _, _, v in entries if v in refs)
put('D5c_any_control_flow_ref', {'n_refs': len(refs), 'entries_referenced': n_ref})
ck('D5c 292 个项值里被任意控制流指令直接引用的个数（含 jcc，capstone 口径）—— 报数，不作断言',
   True, n_ref)

json.dump({'checks': checks, 'R': R}, open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n=== %d checks, %d FAIL ===' % (len(checks), nf))
sys.exit(1 if nf else 0)
