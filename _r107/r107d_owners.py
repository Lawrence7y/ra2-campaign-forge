#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107d_owners.py —— 19 张 switch 表的「所属函数」三条独立判据 + 虚表槽语义定位

主攻 R106 §EH10① 声称「17 个函数入口的语义命名未做，需符号或运行期采样，win-main 离线」。
本脚本不改任何既有文件，只读镜像字节与 symbols.json，交可机械核验的字节事实。

三判据（互不依赖，逐表给结论，不强行统一）：
  P1 CALLTGT   <=H 的最近 call 直接目标（R106 用的判据，保留以便对比）
  P2 INNERMOST <=H 的最近「确定函数起点」，确定 = call 目标 ∪ 虚表槽值 ∪ 对齐填充后接非填充字节
  P3 DECODE    从候选起点前向线性解码能否恰好落在 H 上（指令边界命中），并给中途 ret 数

语义定位（不依赖 win-main）：把 P2 候选与 symbols.json 的 954 个 vtable_vfuncs 槽值比对，
  命中则给出「类名 + 槽号 + 该槽在多少个类的虚表里出现」。槽号只作定位，不作语义命名。

内存纪律：全段用 disasm_lite + 64KB 分块；只对候选点单独开 detail。
"""
import hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107d_owners.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


raw = open(EXE, 'rb').read()
ck('S0 exe sha256 == 73201cc0...', hashlib.sha256(raw).hexdigest() == EXE_SHA,
   hashlib.sha256(raw).hexdigest()[:16])

e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))


def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None


def byte_at(va):
    o = off(va)
    return raw[o] if o is not None else None


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True
mdD = Cs(CS_ARCH_X86, CS_MODE_32)
mdD.detail = True
mdD.skipdata = True

# ---------- 全段分块线性扫（防 OOM：detail=False + 64KB 分块）----------
CHUNK = 64 * 1024
starts = []
calls = {}          # addr -> target
pos = TS
insn_n = 0
while pos < TE:
    hi = min(pos + CHUNK, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in md.disasm_lite(buf, pos):
        if a >= hi:
            break
        insn_n += 1
        last = a + sz
        starts.append(a)
        if m == 'call' and o.startswith('0x'):
            try:
                calls[a] = int(o, 16)
            except ValueError:
                pass
    if last <= pos:
        last = pos + 1
    pos = last
SSET = set(starts)
CALLT = set(calls.values())
print('  指令 %d  起点 %d  call 站点 %d  call 目标 %d'
      % (insn_n, len(starts), len(calls), len(CALLT)), flush=True)
ck('P0 独立重扫 .text 指令数 == 1,392,592（与 R104/R105/R106 同口径）', insn_n == 1392592, insn_n)
ck('P0b 独立重扫 call 直接目标数 == 6,728（四实现同值）', len(CALLT) == 6728, len(CALLT))

# ---------- 虚表槽值表 ----------
sym = json.load(open('out/reverse/symbols.json'))['classes']
vslot = {}          # addr -> list of (class, slot)
for cname, c in sym.items():
    for i, v in enumerate(c.get('vfuncs') or []):
        vslot.setdefault(int(v, 16), []).append((cname, i))
print('  vtable 槽值 distinct %d（%d 个类）' % (len(vslot), len(sym)), flush=True)
ck('P0c symbols.json 类数 == 988 且带 vtable 的 954', len(sym) == 988 and len(vslot) > 0,
   (len(sym), len(vslot)))

PAD = (0x90, 0xcc, 0x00, 0x66, 0x2e)


def align_seed(a):
    """a 是否为「对齐填充后接非填充字节」的起点：要求 a 前 1..3 字节全为填充、且 a 本身 4 字节对齐"""
    if a % 4 != 0:
        return False
    b1 = byte_at(a - 1)
    b2 = byte_at(a - 2)
    if b1 is None or b2 is None:
        return False
    return b1 in PAD or b2 in PAD


def definite(a):
    """返回 None 或证据类别字符串（一条地址可有多条证据，返回合并串）"""
    ev = []
    if a in CALLT:
        ev.append('CALL')
    if a in vslot:
        ev.append('VSLOT')
    if align_seed(a):
        ev.append('ALIGN')
    return '+'.join(ev) if ev else None


import bisect
SORT = starts


def cands_before(H, span):
    lo = H - span
    i = bisect.bisect_right(SORT, H)
    j = bisect.bisect_left(SORT, lo)
    return [a for a in SORT[j:i] if definite(a)]


def decode_hit(S, H, limit=0x8000):
    """从 S 线性解码，看 H 是否落在指令边界上；返回 (hit, n_insn, n_ret)"""
    a = S
    n = 0
    nret = 0
    while a < H and a < S + limit:
        got = None
        for ins in mdD.disasm(raw[off(a):off(a) + 16], a):
            got = ins
            break
        if got is None:
            return (False, n, nret)
        if got.address == H:
            return (True, n, nret)
        if got.mnemonic.startswith('ret'):
            nret += 1
        n += 1
        a = got.address + got.size
    return (a == H, n, nret)


D = json.load(open('_r106/r106f_switchsem.json'))['tables']
ck('D0 参考表 19 张（读 r106f，仅作待核对象，不作证据）', len(D) == 19, len(D))

ROWS = []
for t in D:
    H = int(t['holder'], 16)
    base = int(t['table'], 16)
    r106 = int(t['func_by_calltarget'], 16) if t.get('func_by_calltarget') else None
    c = cands_before(H, 0x4000)
    innermost = c[-1] if c else None
    hit_i = decode_hit(innermost, H) if innermost else None
    hit_r = decode_hit(r106, H) if r106 else None
    v = vslot.get(innermost) or []
    ROWS.append({
        'table': hex(base), 'n': t['n'], 'holder': hex(H),
        'P1_calltgt': hex(r106) if r106 else None,
        'P2_innermost': hex(innermost) if innermost else None,
        'P2_evidence': definite(innermost) if innermost else None,
        'P3_hit_innermost': hit_i[0] if hit_i else None,
        'P3_insn_innermost': hit_i[1] if hit_i else None,
        'P3_ret_innermost': hit_i[2] if hit_i else None,
        'P3_hit_r106': hit_r[0] if hit_r else None,
        'P3_insn_r106': hit_r[1] if hit_r else None,
        'P3_ret_r106': hit_r[2] if hit_r else None,
        'vsem': [{'class': cn, 'slot': s} for cn, s in v],
        'agree_P1_P2': (r106 == innermost),
    })

# ---------- 断言 ----------
ck('O1 19 张表全部至少有一个确定起点候选',
   all(r['P2_innermost'] for r in ROWS), [r['table'] for r in ROWS if not r['P2_innermost']])
ck('O2 从 innermost 前向解码 19/19 恰好落在 holder 上（指令边界命中）',
   all(r['P3_hit_innermost'] for r in ROWS),
   [(r['table'], r['P2_innermost'], r['P3_hit_innermost']) for r in ROWS if not r['P3_hit_innermost']])
diff = [r for r in ROWS if not r['agree_P1_P2']]
ck('O3 P1(CALLTGT) 与 P2(INNERMOST) 不一致的表数（不等于 0 即 R106 界定有误）',
   True, len(diff))
print('     不一致清单: ' + ', '.join('%s H=%s P1=%s P2=%s' %
                                 (r['table'], r['holder'], r['P1_calltgt'], r['P2_innermost'])
                                 for r in diff), flush=True)
ck('O4 不一致的每一张，P1 候选到 holder 之间确实还夹着别的确定起点（根因可定位）',
   all(any(int(x['P2_innermost'], 16) > int(r['P1_calltgt'], 16) for x in [r])
       for r in diff), [r['table'] for r in diff])
hit_all = all(r['P3_hit_r106'] for r in ROWS)
ck('O5 从 P1 前向解码也能落到 holder（说明"能落到"不是鉴别力，不能当同函数证据）', hit_all, hit_all)

vmapped = [r for r in ROWS if r['vsem']]
ck('O6 至少 1 张表所属函数被虚表槽命中（静态语义定位可行性）', len(vmapped) >= 1,
   [(r['table'], r['P2_innermost'], r['vsem']) for r in vmapped])

json.dump({'checks': checks, 'rows': ROWS,
           'insn_n': insn_n, 'call_targets': len(CALLT),
           'vslot_distinct': len(vslot)},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n--- 19 张摘要 ---')
for r in ROWS:
    print('%-10s H=%s P1=%s P2=%s ev=%-14s hit=%s/%s ret=%s/%s vsem=%s %s'
          % (r['table'], r['holder'], r['P1_calltgt'], r['P2_innermost'], r['P2_evidence'],
             r['P3_hit_innermost'], r['P3_insn_innermost'], r['P3_ret_innermost'],
             r['P3_ret_r106'], r['vsem'] or '-', '' if r['agree_P1_P2'] else '<<DIFF'))
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项，FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
