#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r111d_full_iid.py —— 把 QI 判据扩成三种可机械识别的编码，重算 COM 暴露面全集。

R110 / r111a 只认一种编码：mov ecx,4 ; mov edi,<IID ptr> ; ... ; repe cmpsd。
本轮扫 slot0 时撞到另外两种**真实编码**（不是判据放松）：
  TH   adjustor thunk : sub dword ptr [esp+4], N ; jmp <真实 QI>   （12 个 Locomotion 类，N 全 4）
  ATL  内联比较       : 把 IID 的 16 字节拆成 4 个 dword 直接比，其中 dword1 用
                        mov eax,[reg+4] + test eax,eax 判 0。只有 xxxxxxxx-0000-0000-C000-000000000046
                        这一族能这样编（3 个 ATL sink）。

自错（本轮 L-04/L-05，均由断言当场抓住）：
  L-04 r111d 上一稿用 700 B **裸窗口**抽 cmpsd，没用 HB 边界 ⇒ 窗口溢出到下一个函数，
       ?$VectorCursor@IV?$DynamicVectorClass@I@@ 的析构函数（0x4f3fd0）被误判成第 173 个 QI 类。
       r111a 是对的（用 HB），是我在合并时把边界纪律丢了。本稿所有形态一律 HB 定界。
  L-05 上一稿把 ATL 形态写成「4 个 cmp 齐全」，实测 dword1 是 mov+test 不是 cmp ⇒ ATL 类 0 个。
"""
import hashlib, json, os, random, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda v: v - IB
checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() ==
   '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
   hashlib.sha256(raw).hexdigest()[:16])

pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
SECT = [(s.Name.decode().strip('\x00'), IB + s.VirtualAddress,
         IB + s.VirtualAddress + s.Misc_VirtualSize) for s in pe.sections]
DATA = [(a, b) for n, a, b in SECT if n != '.text']
in_data = lambda v: any(a <= v and v + 16 <= b for a, b in DATA)
sym = json.load(open('out/reverse/symbols.json'))['classes']
VT = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
ck('S1 vtable 954', len(VT) == 954, len(VT))

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True

# ---------- HB 边界（r109e 同构造），全脚本唯一定界来源 ----------
def build_hb():
    starts, rets = [], []
    pos = TS
    while pos < TE:
        hi = min(pos + 65536, TE); last = pos
        for a, sz, m, o in md.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
            if a >= hi: break
            last = a + sz; starts.append(a)
            if m.startswith('ret'): rets.append(a)
        if last <= pos: last = pos + 1
        pos = last
    SS = set(starts)
    def rsz(r):
        q = fo(r)
        while raw[q] in (0x66, 0x67, 0xf2, 0xf3, 0x2e, 0x3e, 0x26, 0x36, 0x64, 0x65): q += 1
        return (q - fo(r)) + (3 if raw[q] in (0xc2, 0xca) else 1)
    HB = set()
    for r in sorted(rets):
        q = r + rsz(r); n = 0
        while q < TE and raw[fo(q)] in (0x90, 0xcc) and n < 64: q += 1; n += 1
        if n and q % 4 == 0 and q in SS: HB.add(q)
    return starts, sorted(HB)
STARTS, HBS = build_hb(); HS = set(HBS)
ck('S2 HB == 17766（全脚本唯一定界；不用裸窗口，自错 L-04）', len(HBS) == 17766, len(HBS))

def fn(f, cap=2500, win=1536):
    """HB 定界的函数体指令序列。
    两个上界：HB 边界（语义）与 win 字节（性能）。win=1536 远大于任何实测 QI 体
    （最长实测 0x4f6830 = 223 B；Locomotion 共享体 0x55a9b0 < 500 B），
    故 win 不改变结论，只把反控从 20000×64KB 降到 20000×1.5KB。"""
    hi = min(f + win, TE)
    out = []
    for g in md.disasm_lite(raw[fo(f):fo(hi) + 16], f):
        a = g[0]
        if a >= hi or len(out) >= cap: break
        if a != f and a in HS: break
        out.append(g)
    return out

RE_TH = re.compile(r'^dword ptr \[esp \+ 4\], (0x[0-9a-f]+|\d+)$')
RE_EDI = re.compile(r'^edi, (0x[0-9a-f]+)$'); RE_ECX4 = re.compile(r'^ecx, 4$')
# 自错 L-07：值部分是十进制 0（cmp dword ptr [edi], 0），原正则只认 0x 前缀 ⇒ 第 1 段永远抽不到。
RE_CMPM = re.compile(r'^dword ptr \[([a-z]{2,4})(?: \+ (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+|\d+)$')
# 自错 L-08：基址用 [a-z]{2,4} 限定为寄存器，否则绝对地址 [0x7f76a0] 会被 \w+ 当成基址。
RE_MOVL = re.compile(r'^(\w+), dword ptr \[([a-z]{2,4})(?: \+ (0x[0-9a-f]+|\d+))?\]$')

def thunk_at(f):
    g = fn(f)[:3]
    if len(g) < 2 or g[0][2] != 'sub': return None
    m = RE_TH.match(g[0][3])
    if not m or g[1][2] != 'jmp' or not g[1][3].startswith('0x'): return None
    return int(m.group(1), 0), int(g[1][3], 16)

def cmpsd_iids(lits):
    out, pend, ecx4 = [], None, False
    for a, sz, m, o in lits:
        if m == 'mov':
            mo = RE_EDI.match(o)
            if mo: pend = int(mo.group(1), 16); continue
            if RE_ECX4.match(o): ecx4 = True; continue
        if 'cmpsd' in m:
            if pend is not None and ecx4: out.append(pend)
            pend = None; ecx4 = False
    return [p for p in out if in_data(p)]

def atl_iids(lits):
    """ATL 内联比较：同一基址上四段齐全即可反解 16 字节 IID：
         cmp dword [reg+0], d0
         mov r,[reg+4] + test r,r   （判 d1 == 0，编译器用 test 不用 cmp）
         cmp dword [reg+8], 0xc0
         cmp dword [reg+0xc], 0x46000000
    自错 L-06（本轮）：上一稿在**每条指令**后都执行 ctx[reg] = {}，累加器永远攒不到 4 段，
    于是 ATL 类恒为 0 —— 断言 F1/F3 当场抓住。正确行为：只在**命中一次并消费掉**之后才清空。"""
    res = []; ctx = defaultdict(dict)
    for i, (a, sz, m, o) in enumerate(lits):
        hitreg = None
        if m == 'cmp':
            mm = RE_CMPM.match(o)
            if mm:
                reg = mm.group(1)
                ctx[reg][0 if mm.group(2) is None else int(mm.group(2), 0)] = int(mm.group(3), 0)
                hitreg = reg
        elif m == 'mov':
            mm = RE_MOVL.match(o)
            if mm and i + 1 < len(lits):
                r, base, disp = mm.group(1), mm.group(2), mm.group(3)
                nxt = lits[i + 1]
                if nxt[2] == 'test' and nxt[3].replace(' ', '') == '%s,%s' % (r, r):
                    ctx[base][0 if disp is None else int(disp, 0)] = 0
                    hitreg = base
        if hitreg is not None:
            g = ctx[hitreg]
            if {0, 4, 8, 0xc} <= set(g):
                if g[8] == 0xC0 and g[0xc] == 0x46000000:
                    res.append(struct.pack('<IIII', g[0], g[4], g[8], g[0xc]))
                ctx[hitreg] = {}
    return res

FORM, IIDS, DETAIL = {}, {}, {}
for vt, k in sorted(VT.items()):
    s0 = struct.unpack_from('<I', raw, fo(vt))[0]
    if not (TS <= s0 < TE): continue
    t = thunk_at(s0)
    if t:
        FORM[k] = 'TH'; IIDS[k] = sorted(set(cmpsd_iids(fn(t[1]))))
        DETAIL[k] = {'N': t[0], 'target': t[1]}; continue
    g = cmpsd_iids(fn(s0))
    if g:
        FORM[k] = 'CMPSD'; IIDS[k] = sorted(set(g)); continue
    a = atl_iids(fn(s0))
    if a:
        FORM[k] = 'ATL'; IIDS[k] = sorted(set(a)); DETAIL[k] = {'raw': [x.hex() for x in sorted(set(a))]}

fc = Counter(FORM.values())
ck('F1 三种编码类数 = %s，合计 %d（互斥：每类只归一种；r111a 的 172 只是 CMPSD 这一支）'
   % (dict(fc), len(FORM)), fc == Counter({'CMPSD': 172, 'TH': 12, 'ATL': 3}) and len(FORM) == 187,
   dict(fc))

# 正向断言：r111a 的 172 类必须全在 CMPSD 支里，且 CMPSD 支不得多出（自错 L-04 的检查点）
A111 = json.load(open('_r111/r111a_iidmap2.json'))['classes']
CM = set(k for k in FORM if FORM[k] == 'CMPSD')
ck('F1b CMPSD 支 == r111a 的 172 类（集合相等；上一稿多出 ?$VectorCursor@... 是 700 B 裸窗口溢出，自错 L-04）',
   CM == set(A111), {'extra': sorted(CM - set(A111)), 'missing': sorted(set(A111) - CM)})
ck('F1c 三支两两不相交', len(CM) + fc['TH'] + fc['ATL'] == len(FORM), len(FORM))

atl_classes = sorted(k for k in FORM if FORM[k] == 'ATL')
atl_raw = sorted(set(x for k in atl_classes for x in IIDS[k]))
ck('F3 ATL 类 %s 反解 %d 个 distinct IID：%s'
   % (atl_classes, len(atl_raw), [x.hex() for x in atl_raw]), len(atl_raw) == 1, [x.hex() for x in atl_raw])
ck('F3b ATL 反解 IID 尾 8 字节必为 C000000000000046（编码前提，也是它的盲区）',
   all(x[8:] == bytes.fromhex('C000000000000046') for x in atl_raw),
   [x[8:].hex() for x in atl_raw])

# ---------- F4 合并全集（指针类与内容类分开计，不混算） ----------
# ATL 支抽到的是 **16 字节立即数内容**，不是 .rdata 指针；混进同一张表会导致 hex() 类型错
# （本轮 L-09：上一稿就是这么炸的）。故分两栏：ptr 支（CMPSD + TH，都是指针）与 content 支（ATL）。
ptr_cnt = Counter()
for k, v in IIDS.items():
    if FORM[k] == 'ATL': continue
    for p in v: ptr_cnt[p] += 1
content_set = set(x for k in FORM if FORM[k] == 'ATL' for x in IIDS[k])
cmpsd_set = set(p for k in CM for p in IIDS[k])
new_th = sorted(set(p for k in FORM if FORM[k] == 'TH' for p in IIDS[k]) - cmpsd_set)
ck('F2 thunk 穿透后新增 distinct IID = %s（cmpsd 链看不见）'
   % [hex(p) for p in new_th], len(new_th) == 2, [hex(p) for p in new_th])

def gt(b):
    d1, d2, d3 = struct.unpack('<IHH', b[:8])
    return '%08X-%04X-%04X-%s-%s' % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())
r110 = set(int(p, 16) for p in json.load(open('_r110/r110a_iidmap.json'))['iid_classes'])
ck('F4 ptr 支 distinct IID: cmpsd 链 %d → 加 TH 后 %d（R110 报 17）'
   % (len(cmpsd_set), len(ptr_cnt)), len(ptr_cnt) == 20,
   {'cmpsd': len(cmpsd_set), 'ptr_merged': len(ptr_cnt)})
ck('F4b R110 的 17 个 ⊆ 本轮 ptr 支；本轮新增 %d 个 = %s'
   % (len(set(ptr_cnt) - r110), sorted(hex(p) for p in set(ptr_cnt) - r110)),
   r110 <= set(ptr_cnt) and len(set(ptr_cnt) - r110) == 3,
   sorted(hex(p) for p in set(ptr_cnt) - r110))
ck('F4c ATL content 支 = %s，与 IUnknown 的 16 字节逐字节相等 ⇒ ATL 那 3 类认的就是 IUnknown'
   % [gt(x) for x in sorted(content_set)],
   content_set == {struct.pack('<IIII', 0, 0, 0xC0, 0x46000000)},
   [gt(x) for x in sorted(content_set)])
ck('F4d 总量：ptr 支 %d + content 支 %d = %d 个 distinct IID 语义（R110 报 17；本轮的 20 里 IUnknown '
   '已经在 ptr 支）' % (len(ptr_cnt), len(content_set), len(ptr_cnt | content_set) if False else len(ptr_cnt)),
   len(content_set) == 1, {'ptr': len(ptr_cnt), 'content': len(content_set)})

# ---------- F5 反控 ----------
random.seed(111)
samp = random.sample(STARTS, 20000)
def any_form(s):
    if thunk_at(s): return 'TH'
    if cmpsd_iids(fn(s)): return 'CMPSD'
    if atl_iids(fn(s)): return 'ATL'
    return None
hit = Counter(any_form(s) for s in samp)
n_hit = sum(v for k, v in hit.items() if k)
base = n_hit / len(samp) * 100
rate = len(FORM) / len(VT) * 100
ck('F5 反控：随机 20000 起点「任一形态」命中 %d（%.3f%%）= %s；slot0 里 %d/954 = %.2f%% ⇒ 富集 %.1f 倍'
   % (n_hit, base, {k: v for k, v in hit.items() if k}, len(FORM), rate,
      rate / base if base else float('inf')), base < 3.0,
   {'hit': {k: v for k, v in hit.items() if k}, 'base_pct': round(base, 4),
    'enrich': round(rate / base, 2) if base else None})

json.dump({'form': FORM,
           'iids': {k: [hex(x) if isinstance(x, int) else x.hex() for x in v] for k, v in IIDS.items()},
           'detail': {k: {kk: (hex(vv) if isinstance(vv, int) else vv) for kk, vv in v.items()}
                      for k, v in DETAIL.items()},
           'form_counts': dict(fc), 'ptr_iid': {hex(p): c for p, c in ptr_cnt.items()},
           'content_iid': [gt(x) for x in sorted(content_set)],
           'new_from_thunk': [hex(p) for p in new_th], 'atl_guids': [gt(x) for x in atl_raw],
           'negctl': {'n': len(samp), 'hit': {k: v for k, v in hit.items() if k},
                      'base_pct': round(base, 4)}, 'checks': checks},
          open('_r111/r111d_full_iid.json', 'w'), indent=1)
print('\n--- %d checks, FAIL %d ---' % (len(checks), sum(1 for c in checks if not c['ok'])))
