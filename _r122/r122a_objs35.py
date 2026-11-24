#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r122a: 目标① —— 35 个 edx 实参各指向什么结构（R121 未取得项）。

R121 遗留问题：35 个字节全同的孪生函数体被 35 个不同调用点以 35 个不同 edx 调用，
只测到「35 个不同地址」，内容未解。

本脚本的回答路径（全部静态、全部本机可复算）：
  S1  35 个 edx 实参落在哪个节的哪个区（file-backed vs BSS 虚拟区）
  S2  这 35 个地址在 .text 里被哪些指令写过（c7 05 <addr>, <imm32> = mov dword ptr [addr], imm32）
  S3  写入的 imm32 是 vftable 指针；用 MSVC RTTI 布局反查类名
  S4  逐对象报告：写入次数、vptr 基类/派生类次序、RTTI 名
  S5  反控：把 edx 平移到相邻地址、把 vtable 指针加 4，必须解不出名

内存纪律：全程 disasm_lite / 单指令 disasm，不对整段 .text 开 detail=True。
"""
import hashlib
import json
import struct
import subprocess
import sys

import capstone
import pefile

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r122/r122a_objs35.json'
RES = []


def ck(name, cond, detail=''):
    RES.append({'check': name, 'ok': bool(cond), 'detail': str(detail)[:220]})
    return bool(cond)


# ---------------- 基础：PE 映射 ----------------
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SECS = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode()
    SECS.append(dict(name=nm, va=IB + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     pr=s.PointerToRawData, rs=s.SizeOfRawData))
DATA = open(EXE, 'rb').read()
FILE_SHA = hashlib.sha256(DATA).hexdigest()


def sec_of(va):
    for x in SECS:
        if x['va'] <= va < x['va'] + x['vs']:
            return x
    return None


def region(va):
    """返回 ('RAW'|'BSS'|'NONE', 节名)。BSS = 有虚拟空间但无文件字节。"""
    x = sec_of(va)
    if x is None:
        return 'NONE', None
    return ('RAW' if va < x['va'] + x['rs'] else 'BSS'), x['name']


def rd(va, n):
    x = sec_of(va)
    if x is None:
        return None
    off = x['pr'] + (va - x['va'])
    if va - x['va'] + n > x['rs']:
        return None            # 越到 BSS 不给字节，绝不读别的节的原始字节
    if off + n > len(DATA):
        return None
    return DATA[off:off + n]


def u32(va):
    b = rd(va, 4)
    return None if b is None else struct.unpack('<I', b)[0]


# ---------------- S1/S2：找 35 个调用点及其 edx ----------------
# 调用点来自 R121 已落盘的 r121c（60 站里的 35 个孪生站），但这里不信任它：
# 自己重扫 .text 找 call rel32 指向 [0x67fdf0, 0x680f80) 且函数体入口在 0x80 步长上的站点。
TXT = [x for x in SECS if x['name'] == '.text'][0]
TDATA = DATA[TXT['pr']:TXT['pr'] + TXT['rs']]
TBASE = TXT['va']

calls = {}
for i in range(len(TDATA) - 5):
    if TDATA[i] != 0xe8:
        continue
    rel = struct.unpack_from('<i', TDATA, i + 1)[0]
    va = TBASE + i
    tgt = va + 5 + rel
    if 0x67fdf0 <= tgt <= 0x680f80:
        calls.setdefault(tgt, []).append(va)

ck('S2a 孪生函数被 call rel32 指向的入口数', len(calls) == 36,
   'measured=%d (R121 报 35 个孪生 + 1 个 0x680f70 共 36 个入口)' % len(calls))

# 0x680f70 有两站（0x67d193, 0x67e62b），其余每站一入口 => 总站点 37
total_sites = sum(len(v) for v in calls.values())
ck('S2b 站点总数', total_sites == 37, 'measured=%d' % total_sites)

# R121 的 35 站集合（60 站减去主函数 25 站）
R121_TWINS = sorted([0x67df0f, 0x67df29, 0x67df43, 0x67df5d, 0x67df77, 0x67df91, 0x67dfab,
                     0x67dfc5, 0x67dfdf, 0x67dff9, 0x67e013, 0x67e02d, 0x67e047, 0x67e061,
                     0x67e07b, 0x67e095, 0x67e0af, 0x67e0c9, 0x67e0e3, 0x67e0fd, 0x67e117,
                     0x67e1e7, 0x67e201, 0x67e21b, 0x67e235, 0x67e24f, 0x67e28f, 0x67e2a9,
                     0x67e2c3, 0x67e2dd, 0x67e2f7, 0x67e311, 0x67e32b, 0x67e390, 0x67e3aa])
CK_SITES = sorted([s for v in calls.values() for s in v])
ck('S2c R121 的 35 站全在本次重扫结果里', set(R121_TWINS) <= set(CK_SITES),
   'missing=%s' % sorted(set(R121_TWINS) - set(CK_SITES)))
ck('S2d 多出的 2 站', sorted(set(CK_SITES) - set(R121_TWINS)) == [0x67d193, 0x67e62b],
   'extra=%s' % [hex(x) for x in sorted(set(CK_SITES) - set(R121_TWINS))])

# 每个站点前两条指令必须是 mov edx,imm32 ; mov ecx,esi（ba imm32 / 8b ce）
# 站点 -7 = 0xba，站点 -2..-1 = 8b ce（实机 disasm 实测形态，见 0x67df08/0x67df0d/0x67df0f）
cands = []
bad_shape = []
for site in R121_TWINS:
    b = rd(site - 7, 7)
    if b is None or b[0] != 0xba or b[5:7] != b'\x8b\xce':
        bad_shape.append((hex(site), b.hex() if b else None))
        continue
    cands.append((site, struct.unpack_from('<I', b, 1)[0]))
ck('S2e 35 站前置指令全为 mov edx,imm32', len(cands) == 35 and not bad_shape,
   'ok=%d bad=%s' % (len(cands), bad_shape[:3]))

EDX = [e for _, e in cands]
ck('S2f 35 个 edx 互不相同', len(set(EDX)) == 35, 'distinct=%d' % len(set(EDX)))

# ---------------- S1：这 35 个地址的节/区 ----------------
regs = [region(a) for a in EDX]
ck('S1a 35 个 edx 全在 .data 节', all(r[1] == '.data' for r in regs),
   'regions=%s' % {repr(k): v for k, v in
                   __import__('collections').Counter(regs).items()})
ck('S1b 35 个 edx 全在 .data 的 BSS（无文件字节）区', all(r[0] == 'BSS' for r in regs),
   'BSS count=%d / 35' % sum(1 for r in regs if r[0] == 'BSS'))
ds = [x for x in SECS if x['name'] == '.data'][0]
BSS_LO, BSS_HI = ds['va'] + ds['rs'], ds['va'] + ds['vs']
ck('S1c BSS 区边界', all(BSS_LO <= a < BSS_HI for a in EDX),
   '[%08x,%08x) size=%d' % (BSS_LO, BSS_HI, BSS_HI - BSS_LO))
# S1d（原为假反控，已改）：不再断言 rd() 对 BSS 返回 None（那只是自家 helper 行为）。
# 改成二进制事实断言：这些地址必须落在 .data 的「无文件字节」侧，即
# 地址本身 >= va+SizeOfRawData，且该地址换算出的文件偏移必须越过文件尾或不在该节 raw 内。
ds_pr, ds_rs = ds['pr'], ds['rs']


def _no_file_bytes(va):
    off = ds_pr + (va - ds['va'])
    return va >= ds['va'] + ds_rs and (off >= len(DATA) or va - ds['va'] >= ds_rs)


ck('S1d 35 个 edx 在二进制上确实无文件字节（不是 helper 行为）',
   all(_no_file_bytes(a) for a in EDX),
   'no_file_bytes=%d/35 ; .data raw=[%08x,+%d)' % (
       sum(1 for a in EDX if _no_file_bytes(a)), ds['va'], ds_rs))

# ---------------- S2 全量：所有 c7 05 写 BSS 的站点 ----------------
writes = {}
i = 0
n = len(TDATA)
while i < n - 10:
    if TDATA[i] == 0xc7 and TDATA[i + 1] == 0x05:
        t = struct.unpack_from('<I', TDATA, i + 2)[0]
        if BSS_LO <= t < BSS_HI:
            writes.setdefault(t, []).append(TBASE + i)
    i += 1
ck('S2g c7 05 写 BSS 的目标总数 == 1159 且站点数 == 1777（精确值，非 >1000）',
   len(writes) == 1159 and sum(len(v) for v in writes.values()) == 1777,
   'targets=%d sites=%d' % (len(writes), sum(len(v) for v in writes.values())))
ck('S2h 35 个目标全被 c7 05 写过', all(a in writes for a in EDX),
   'covered=%d/35' % sum(1 for a in EDX if a in writes))
import collections
per = collections.Counter(len(writes[a]) for a in EDX)
ck('S2i 35 个目标每个恰好被写 2 次', list(per.items()) == [(2, 35)], 'hist=%s' % dict(per))
# S2j 真条件：全库里「恰好写 2 次」的目标占少数，故 35 个整齐的 2 次不是扫描口径的产物
GLOBAL_HIST = collections.Counter(len(v) for v in writes.values())
n_two = GLOBAL_HIST.get(2, 0)
ck('S2j 全库里恰好 2 次写入的目标 < 总数的 25%（故 35 个整齐的 2 次不是口径假象）',
   0 < n_two < 0.25 * len(writes),
   'n_two=%d / targets=%d = %.1f%%' % (n_two, len(writes), 100.0 * n_two / len(writes)))

# ---------------- S3：vptr -> MSVC RTTI -> 类名 ----------------
def name_of_vtable(vt):
    """MSVC x86 RTTI: [vtable-4] = CompleteObjectLocator。
    COL: +0 signature, +4 offset, +8 cdOffset, +12 pTypeDescriptor, +16 pClassDescriptor, +20 pSelf
    TypeDescriptor: +0 pVFTable, +4 spare, +8 mangled name (char[])"""
    col = u32(vt - 4)
    if col is None:
        return None, 'no-COL'
    b = rd(col, 0x18)
    if b is None:
        return None, 'no-COL-body'
    sig, off, cd, td, chd, selfv = struct.unpack('<IIIIII', b)
    if sig != 0 or td == 0:
        return None, 'bad-COL(sig=%d,td=%08x)' % (sig, td)
    s = rd(td + 8, 0x100)
    if s is None:
        return None, 'no-TD'
    nm = s.split(b'\0')[0].decode('ascii', 'replace')
    if not nm.startswith('.?AV'):
        return None, 'not-a-class-name:%r' % nm[:30]
    return nm, 'ok'


objs = []
for (site, e) in cands:
    st = sorted(writes[e])
    vs = []
    for s in st:
        b = rd(s, 10)
        vs.append((s, struct.unpack_from('<I', b, 6)[0]))
    named = [(s, v) + name_of_vtable(v) for s, v in vs]
    objs.append(dict(obj='0x%08x' % e, call_site='0x%08x' % site,
                     writes=[{'site': '0x%08x' % s, 'vptr': '0x%08x' % v,
                              'name': nm, 'why': w} for s, v, nm, w in named]))

ck('S3a 70 次 vptr 写入全部解析出 RTTI 类名', all(w['name'] for o in objs for w in o['writes']),
   'unresolved=%s' % [(o['obj'], w) for o in objs for w in o['writes'] if not w['name']][:3])
ck('S3b 70 个类名互不相同（基类/派生类各一份）',
   len({w['name'] for o in objs for w in o['writes']}) == 70,
   'distinct=%d' % len({w['name'] for o in objs for w in o['writes']}))

# 审计必修 #7：显式断言每对象恰 2 站，后面 S3c/S3d/S3e 才允许依赖 w[0]/w[1]
ck('S3p 每个对象恰有 2 个写入站点（使后续 w[0]/w[1] 访问合法）',
   all(len(o['writes']) == 2 for o in objs),
   'hist=%s' % dict(__import__('collections').Counter(len(o['writes']) for o in objs)))


def is_dyn(nm):
    return 'DynamicVectorClass@' in (nm or '')


def is_vec(nm):
    return bool(nm) and 'DynamicVectorClass@' not in nm and 'VectorClass@' in nm


# 每个对象：按名字集合判定（不依赖排序假设）恰 1 Dynamic + 1 Vector
name_ok = sum(1 for o in objs
              if sum(1 for w in o['writes'] if is_dyn(w['name'])) == 1
              and sum(1 for w in o['writes'] if is_vec(w['name'])) == 1)
# 站点 VA 排序下的次序（按字节实证报告，不改称执行序）
low_first_dyn = 0
pairs = []
for o in objs:
    ws = sorted(o['writes'], key=lambda w: int(w['site'], 16))
    a, b2 = ws[0]['name'], ws[1]['name']
    if is_dyn(a) and is_vec(b2):
        low_first_dyn += 1
    pairs.append((o['obj'], a, b2))
ck('S3c 每个对象恰 1 个 Dynamic 名 + 1 个 Vector 名（按名字集合判定，非排序）',
   name_ok == 35,
   'name_ok=%d/35 ; sample=%r' % (name_ok, pairs[0]))
ck('S3d 35 个对象中「低址站点写 Dynamic、高址站点写 Vector」的个数'
   '（字节实证，不代表执行序）', low_first_dyn == 35, 'count=%d/35' % low_first_dyn)
# S3e：遍历全部名字，不只看前两站（审计必修 #7）
same_elem = 0
for o in objs:
    es = {w['name'].split('VectorClass@')[1].split('@@@')[0]
          for w in o['writes'] if w['name']}
    if len(es) == 1:
        same_elem += 1
ck('S3e 同一对象内全部 vtable 的元素类型相同（遍历全部站点，非只看前两站）',
   same_elem == 35, 'same=%d/35' % same_elem)

# S3f/S3g：对全部 70 个名字解析元素类型（审计必修 #8，原只取第二站）
all_elems = sorted({w['name'].split('VectorClass@')[1].split('@@@')[0]
                    for o in objs for w in o['writes'] if w['name']})
obj_elems = sorted({o['writes'][0]['name'].split('VectorClass@')[1].split('@@@')[0]
                    for o in objs if o['writes'][0]['name']})
ck('S3f 全部 70 个类名的元素类型全为 PAV*（非只取第二站）',
   len(all_elems) == 35 and all(e.startswith('PAV') for e in all_elems),
   'distinct_elems=%d elems=%s' % (len(all_elems), all_elems[:6]))
ck('S3g 35 个对象各自元素类型互不相同（物件侧去重后 n==35）',
   len(obj_elems) == 35, 'n=%d' % len(obj_elems))

# ---------------- S5 反控 ----------------
# 反控 1（原为假反控，已重做）：原写法 name_of_vtable(u32(edx+1) or 0) 对 BSS 恒返回
# None→0，验证的是 helper 而不是错位解析。改成对真实 vptr 做 +1 错位（与 S5b 的 +4 平行）。
c1 = [name_of_vtable(int(o['writes'][1]['vptr'], 16) + 1) for o in objs[:10]]
ck('S5a 反控：真实 vptr+1 当 vtable 起点解不出合法类名', all(x[0] is None for x in c1),
   'ok_names=%d/10' % sum(1 for x in c1 if x[0]))
# 反控 2（原为假反控，已重做）：vptr+4 落在本案里恰好解不出名，但那只是数据集性质，
# 不能把「None」当作解析器正确性的证据。改成两条独立可证伪的断言：
#   (a) vptr+4 必须仍在 .rdata 内（说明它不是节外乱地址，而是真实的 vtable 槽位）
#   (b) 若 vptr+4 能解出名，该名必须不同于原类名（若不能解出，也不构成矛盾）
c2 = []
for o in objs[:10]:
    v = int(o['writes'][0]['vptr'], 16)
    nm_next, _ = name_of_vtable(v + 4)
    c2.append((v + 4, nm_next, o['writes'][0]['name']))
ck('S5b 反控：真实 vptr+4 仍落在 .rdata 内，且若解出类名必须与原类名不同',
   all(sec_of(a) is not None and sec_of(a)['name'] == '.rdata' for a, _, _ in c2)
   and all(n is None or n != orig for _, n, orig in c2),
   'in_rdata=%d/10 ; diff_or_none=%d/10 ; sample=%r'
   % (sum(1 for a, _, _ in c2 if sec_of(a) and sec_of(a)['name'] == '.rdata'),
      sum(1 for _, n, o in c2 if n is None or n != o), c2[:2]))
# 反控 3：正控 —— 真实 vptr 必须解得出，且加 0x40（跳进另一个对象）名字不同
c3 = [name_of_vtable(int(o['writes'][1]['vptr'], 16)) for o in objs[:10]]
ck('S5c 正控：真实 vptr 解得出类名', all(x[0] for x in c3),
   'ok=%d/10' % sum(1 for x in c3 if x[0]))

# ---------------- S4 汇总 ----------------
summary = dict(
    exe_sha256=FILE_SHA,
    n_call_sites=len(CK_SITES),
    n_r121_twins=len(R121_TWINS),
    n_edx=len(EDX),
    distinct_edx=len(set(EDX)),
    region_all='BSS:.data',
    bss_lo='0x%08x' % BSS_LO, bss_hi='0x%08x' % BSS_HI,
    bss_targets_written=len(writes),
    writes_per_obj=dict(per),
    n_distinct_class_names=len({w['name'] for o in objs for w in o['writes']}),
    elem_types=obj_elems,
)
json.dump(dict(summary=summary, objects=objs, checks=RES,
               all_ok=all(r['ok'] for r in RES)),
          open(OUT, 'w'), indent=1)

for r in RES:
    print(('  PASS  ' if r['ok'] else '  FAIL  ') + r['check'] + ' :: ' + r['detail'])
print('checks %d ; PASS %d' % (len(RES), sum(1 for r in RES if r['ok'])))
sys.exit(0 if all(r['ok'] for r in RES) else 1)
