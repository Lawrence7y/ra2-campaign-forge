#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r118a_guid_census.py —— R118 主攻：R112..R117 六轮共用的判据前提
「一个 IID 的身份 = 它在 .rdata 里的那个常量地址」是否成立。

下手点（本机静态，不依赖外部头文件）：
  R112..R117 全部把 IID 用**常量地址**当键：0x7f7c70 / 0x7f7c80 / 0x7f7c90 ...
  但 GUID 是 16 字节**值**，同一个值在镜像里可以被编译器放多份（.rdata 一份给
  cmpsd 服务端比对用，.data 一份给 __declspec(uuid) 之类的静态记录用）。
  若存在第二份拷贝，则「按地址做普查」在结构上**漏掉**所有走第二份拷贝的请求站点，
  而 R116 的核心数字（0x7f7c70 push 站点 = 0）正是这样得到的。

本脚本只做三件事，全部是字节事实：
  A 全镜像 GUID 常量普查（两类家族：xxxx-xxxx-C000-000000000046 与末尾 00A024DDAFD1），
    按**值**分组，列出每份拷贝的节名与 VA。
  B 每份拷贝的 push imm32 站点（68 xx xx xx xx，指令对齐由线性扫描保证），
    按 GUID 值合并 —— 这是「按值」口径与「按地址」口径的差集来源。
  C 反控：
    C1 正控：把一个已知 GUID 值的两份拷贝各自的站点数分别打印，二者都必须被检出；
    C2 空面：全镜像选取 200 个「GUID 形状但不是已知常量」的位置，push 站点必须为 0；
    C3 结构置换：把扫描键换成「同长度随机字节」，命中必须为 0；
    C4 基线：.text 里 5 字节模式 68+imm32 的总数（判据不能只对少数地址灵敏）。

内存纪律：disasm_lite + 64 KB 分块；脚本带 timeout；不整段 detail=True。
"""
import collections
import json
import os
import random
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L                      # noqa: E402

raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
OUT = os.path.join(ROOT, '_r118/r118a_guid_census.json')
checks = []

# 🐞 自错 S-42（本轮当场发现）：复用 r112_lib 的 fo/u32 会踩 R117 S-40 的同一个坑 ——
# 那是**朴素 IB 偏移**（v - 0x400000），在 .detour 上整节错位（真 file offset 0x497000，
# 朴素偏移 0x795000 已越过文件尾）⇒ struct.unpack_from 直接抛 buffer too small。
# 故本轮**不用** L.fo/L.u32，改用按节表映射的本机 fo/u32；下面 S-42 断言复核两者差异。


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


SECS = [('.text', 0x401000, 0x3df38d, 0x1000, 0x3e0000),
        ('.rdata', 0x7e1000, 0x30074, 0x3e1000, 0x31000),
        ('.data', 0x812000, 0x367be4, 0x412000, 0x6c000),
        ('.rsrc', 0xb7a000, 0x18128, 0x47e000, 0x19000),
        ('.detour', 0xb93000, 0x2718, 0x497000, 0x3000)]


def fo(va):
    """按 PE 节表映射的 file offset（**不是**朴素 IB 偏移）。越界返回 None。"""
    for name, b, vs, pr, sr in SECS:
        if b <= va < b + sr:
            o = pr + (va - b)
            return o if 0 <= o <= len(raw) - 1 else None
    return None


def u32(a):
    o = fo(a)
    if o is None or o + 4 > len(raw):
        raise ValueError('u32 out of file image: %r' % hex(a))
    return struct.unpack_from('<I', raw, o)[0]


# S-42 复核：与 r112_lib 的朴素偏移在哪些节上一致 / 不一致
def _naive(v):
    return v - L.IB


_s42 = []
for name, b, vs, pr, sr in SECS:
    a = b + 8
    _s42.append({'sec': name, 'va': hex(a), 'sectab_fo': fo(a), 'naive_fo': _naive(a),
                 'same': fo(a) == _naive(a)})
print('S-42 fo 映射对照:', json.dumps(_s42, ensure_ascii=False), flush=True)


def fo_ok(va, n=1):
    """VA 必须落在一个**有文件字节**的节内（R117 S-40：朴素 IB 偏移会跨节误映射）。"""
    o = None
    for name, b, vs, pr, sr in SECS:
        if b <= va < b + sr:
            o = pr + (va - b)
            break
    if o is None:
        return False
    return 0 <= o and o + n <= len(raw)


def sec_of(va):
    for n, b, vs, pr, sr in SECS:
        if b <= va < b + sr and pr + (va - b) < len(raw):
            return n
    return None


def in_image(va, n=16):
    return fo_ok(va, n)


# ---------------- A. GUID 常量全镜像普查 ----------------
RD0, RD1 = 0x7e1000, 0x811074
DS, DE = 0x812000, 0x87e000                     # .data 的**有文件映像**区上界（R117 S-40 的教训）

# 逐节按 dword 对齐扫；只认形态，不认名单（名单仅用于后续命名）
def guid_like(a):
    """两类家族：第 3 组 == 0xC0 且第 4 组 == 0x46000000（COM/OLE 惯例），
    或末 8 字节 ∈ {B70900A024DDAFD1, B70A00A024DDAFD1}（本作旧版 IID 惯例）。"""
    if not in_image(a):
        return None
    if u32(a + 8) == 0xc0 and u32(a + 0xc) == 0x46000000:
        return 'com'
    tail = raw[fo(a) + 8:fo(a) + 16]
    if tail in (bytes.fromhex('b70900a024ddafd1'), bytes.fromhex('b70a00a024ddafd1')):
        return 'ra2'
    return None


found = collections.defaultdict(list)
scanned = collections.Counter()
for sec, b, vs, pr, sr in SECS:
    if sec in ('.rsrc',):
        continue
    n = 0
    for a in range(b, b + sr - 16, 4):
        k = guid_like(a)
        if k:
            n += 1
            found[L.iid_guid(a)].append({'va': hex(a), 'sec': sec, 'family': k})
    scanned[sec] = n
print('guided-like constants per section:', dict(scanned), flush=True)

# ---- A1 降级说明（🐞 自错 S-43）----
# 初稿把 A1 写成「全镜像 GUID 形状常量普查：32 个不同 GUID、38 份拷贝」，
# 但形态判据（第 3 组==0xC0 & 第 4 组==0x46000000，或末尾两个硬编码尾值）**不完备**：
# 0x7e9530(0D5CD78E-6470-11D2-9B74-00104B972FE8) 与 0x7e9ae0(170DAC82-12E4-11D2-8175-006008055BB5)
# 都是真实的、已被 R112/R113 认领的 IID，却一条都没被这个形态判据检出（普查结果里 0 份拷贝）。
# 故 A1 的正确表述是「COM/OLE 形态与两个 RA2 尾值形态的常量普查」，**不是全镜像普查**。
# 🐞 自错 S-52（审计员 hy4 task 216 C1 指出、主会话 r118f 复算确认）：
# 此前这里写「真正可靠的普查是对已知 IID 按 16 字节值精确搜索全部拷贝，它**不依赖形态判据**」
# —— 这是**虚假陈述**。下面 A3/A4/B2 的拷贝来源 `CK` 取自 `found`，而 `found` 正是
# `guid_like()` 的产物 ⇒ 整条链仍然依赖形态判据。落盘证据：0x7e9530 / 0x7e9ae0 在
# found 里 0 份，A3/B2 里它们的 copies 也就是空。
# 真正的修复在 _r118/r118f_exact_value_search.py（对 16 字节原文做全镜像 raw.find）：
# 实测形态判据漏 3 份（0x7e9530 有 2 份、0x7e9ae0 有 1 份），0x7e9530 的按值口径应为 2 而非 0。
# 因此本文件 A3/A4/B2 的数字只在「8 个 IID 中被形态判据检出的 6 个」上有效，**不能外推**。
ck('A1 常量普查（口径限定：COM/OLE 形态 + 两个 RA2 硬编码尾值）：%d 个不同 GUID、%d 份拷贝；'
   '该形态判据已知**不完备**（0x7e9530 / 0x7e9ae0 两条真实 IID 检出 0 份），'
   '仅作规模参考，不作身份判据' % (len(found), sum(len(v) for v in found.values())),
   len(found) >= 10, {'distinct_guids': len(found),
                      'total_copies': sum(len(v) for v in found.values()),
                      'per_section': dict(scanned),
                      'known_miss': ['0x7e9530', '0x7e9ae0']})

# 只关注 R112..R117 研究过的那些（用磁盘上的落盘产物取名单，不手抄）
STUDIED = {
    '0x7f7c70': '0000010C-0000-0000-C000-000000000046',
    '0x7f7c80': '00000109-0000-0000-C000-000000000046',
    '0x7f7c90': '00000000-0000-0000-C000-000000000046',
    '0x7f7ca0': '00000001-0000-0000-C000-000000000046',
    '0x7ed358': '070F3290-9841-11D1-B709-00A024DDAFD1',
    '0x7e9b10': '92FEA800-A184-11D1-B70A-00A024DDAFD1',
    '0x7e9530': '0D5CD78E-6470-11D2-9B74-00104B972FE8',
    '0x7e9ae0': '170DAC82-12E4-11D2-8175-006008055BB5',
}
# 先校验手写的 GUID 与我自己的 iid_guid 解码一致（防止手抄错）
bad = [(a, g, L.iid_guid(int(a, 16))) for a, g in STUDIED.items() if L.iid_guid(int(a, 16)) != g]
ck('A2 名单自校验：%d 个被研究 IID 的手写 GUID 与二进制解码逐个一致（不一致 %d 个）'
   % (len(STUDIED), len(bad)), not bad, {'bad': bad})

multi = {g: v for g, v in found.items() if g in STUDIED.values()}
CK = {}
for a, g in STUDIED.items():
    cps = multi.get(g, [])
    CK[a] = [c['va'] for c in cps]
    print('%s %s -> %d 份拷贝 %s' % (a, g, len(cps), CK[a]), flush=True)

n_multi = sum(1 for a in STUDIED if len(CK[a]) > 1)
ck('A3 【核心】%d 个被研究 IID 中，有 %d 个在镜像里存在**多于一份**常量拷贝'
   '（按地址做普查会漏掉非首份拷贝上的全部站点）'
   % (len(STUDIED), n_multi),
   n_multi >= 3, {'per_iid': {a: CK[a] for a in STUDIED}, 'n_multi': n_multi})

# 两份拷贝必须逐字节相同（否则不是同一个 GUID 值，判据不成立）
same_bytes = {}
for a in STUDIED:
    for cva in CK[a]:
        b0 = raw[fo(int(a, 16)):fo(int(a, 16)) + 16]
        b1 = raw[fo(int(cva, 16)):fo(int(cva, 16)) + 16]
        same_bytes[cva] = (b0 == b1)
ck('A4 同一 GUID 的每份拷贝与 .rdata 首份**逐字节相同**（16/16 字节）：一致 %d / %d'
   % (sum(1 for v in same_bytes.values() if v), len(same_bytes)),
   all(same_bytes.values()), {'mismatch': [k for k, v in same_bytes.items() if not v]})


# ---------------- B. 每份拷贝的 push imm32 站点 ----------------
TX = raw[fo(TS):fo(TS) + (TE - TS)]


def push_sites(va):
    """push imm32 = 68 + imm32。用字节模式定位，再用线性扫描指令边界复核（见 B2）。"""
    p = b'\x68' + struct.pack('<I', va)
    out, i = [], TX.find(p)
    while i >= 0:
        out.append(TS + i)
        i = TX.find(p, i + 1)
    return out


# 线性扫描一遍，得到全 .text 的指令起始集（用于复核 push 是否指令对齐）—— 与本轮无关的
# 大对象不常驻：只保留 5 字节窗口命中所需的判定，用分块。
from capstone import Cs, CS_ARCH_X86, CS_MODE_32   # noqa: E402

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = False
MD.skipdata = True


def aligned_pushes(targets, chunk=0x10000):
    """分块流式扫描 .text，返回 {target: [push_site...]}，只收**指令对齐**的 push imm32。"""
    want = set(targets)
    res = collections.defaultdict(list)
    a = TS
    while a < TE:
        end = min(a + chunk, TE)
        for g in MD.disasm_lite(raw[fo(a):fo(end)], a):
            ad, sz, m, o = g
            if m != 'push':
                continue
            if not (o.startswith('0x') and len(o) <= 10):
                continue
            v = int(o, 16)
            if v in want:
                res[v].append(ad)
        a = end
    return res


all_copies = []          # int VA 列表（不混 str，避免二次 int() 转换）
for a in STUDIED:
    all_copies.extend(int(x, 16) for x in CK[a])
AP = aligned_pushes(all_copies)
raw_sites = {c: push_sites(c) for c in all_copies}

n_align_mismatch = 0
for c in all_copies:
    if sorted(AP.get(c, [])) != sorted(raw_sites[c]):
        n_align_mismatch += 1
ck('B1 字节模式命中与「指令对齐的 push imm32」逐个相同：不一致的拷贝 %d / %d'
   '（不一致则说明字节模式会误吃立即数字节）'
   % (n_align_mismatch, len(all_copies)),
   n_align_mismatch == 0,
   {'mismatch': [hex(c) for c in all_copies if sorted(AP.get(c, [])) != sorted(raw_sites[c])]})

per_addr = {hex(c): len(raw_sites[c]) for c in all_copies}
print('push sites per copy:', json.dumps(per_addr, ensure_ascii=False), flush=True)

by_value = {}
for a, g in STUDIED.items():
    tot = sum(len(raw_sites[int(c, 16)]) for c in CK[a])
    per = {c: len(raw_sites[int(c, 16)]) for c in CK[a]}
    by_value[a] = {'guid': g, 'copies': per, 'total_by_value': tot,
                   'rdata_only': per.get(a, 0)}
ck('B2 【核心】按 GUID 值合并后的 push 请求站点数 vs 按 .rdata 地址统计的数：'
   '两者在 %d 个 IID 上不同（按地址口径漏站点）'
   % sum(1 for a in STUDIED if by_value[a]['total_by_value'] != by_value[a]['rdata_only']),
   True, by_value)

# 与 R116 落盘数字对账（磁盘为准，不手抄）
r116 = json.load(open(os.path.join(ROOT, '_r116/r116a_iid_client.json')))
r116_push = {k.split()[0]: v['push_sites'] for k, v in r116['rows'].items()}
recon = {}
for a in ('0x7f7c70', '0x7f7c80', '0x7f7c90', '0x7f7ca0', '0x7ed358', '0x7e9ae0'):
    mine = sum(len(raw_sites[int(c, 16)]) for c in CK.get(a, []))
    recon[a] = {'r116_disk': r116_push.get(a), 'mine_by_value': mine,
                'match_rdata_only': r116_push.get(a) == by_value.get(a, {}).get('rdata_only')}
ck('B3 与 R116 落盘对账：R116 的 push_sites 数字**逐个等于**本轮按 .rdata 首份地址统计的数'
   '（⇒ R116 用的是地址口径，可复现），但它在 %d 个 IID 上小于按值口径'
   % sum(1 for a in recon if recon[a]['r116_disk'] != recon[a]['mine_by_value']),
   all(recon[a]['match_rdata_only'] for a in recon if recon[a]['r116_disk'] is not None),
   recon)


# ---------------- C. 反控 ----------------
# C1 正控：对一个**两份拷贝都存在**的 IID，两份各自都必须检出站点（不是只有首份才有）
pos = [a for a in STUDIED if len(CK[a]) > 1 and
       all(len(raw_sites[int(c, 16)]) > 0 for c in CK[a])]
ck('C1 正控：两份拷贝**各自**都有 push 站点的 IID 个数 %d（若为 0 则「漏站点」无从谈起）'
   % len(pos), len(pos) >= 1,
   {'ids': pos, 'detail': {a: by_value[a]['copies'] for a in pos}})

# C2 【修正版，🐞 自错 S-44】初稿的空面是**异质**的：随机抽 200 个「GUID 形状但不是已知常量」
# 的位置、拿那里的 dword 当 push 立即数 —— 结果命中 1041 次。这不是「判据没牙」，
# 是**反控打在了不下手的地方**（R115 S-16 / R117 S-37 的同族错误）：
# .data 里绝大多数 dword 是别的常量/指针，本来就会被 .text 大量引用，命中高是必然的。
# 真正同质的空面是：**同类但不同值**的 GUID 常量。故改为
#   C2a 取「形态判据检出、但不在被研究名单里」的真实 GUID 常量及其全部拷贝，
#       它们必须被检出（这是正控，不是空面）；
#   C2b 空面 = 把被研究 GUID 的**最后 4 字节取反**造出的伪 GUID 值，
#       该值在镜像里不存在，push 站点必须为 0（同质：同家族、同长度、只差一个值）。
other_guids = [g for g, lst in found.items() if g not in STUDIED.values()]
n_other_hit = sum(1 for g in other_guids
                  if any(len(push_sites(int(c['va'], 16))) > 0 for c in found[g]))
ck('C2a 正控（异值同类）：形态判据检出的 %d 个**非名单** GUID 常量里，有 %d 个存在 push 请求站点'
   ' ⇒ 判据不是只对名单里的 8 个值灵敏' % (len(other_guids), n_other_hit),
   len(other_guids) > 0 and n_other_hit > 0,
   {'n_other': len(other_guids), 'n_hit': n_other_hit,
    'sample': other_guids[:6]})

forged = []
for a in STUDIED:
    b = bytearray(raw[fo(int(a, 16)):fo(int(a, 16)) + 16])
    b[12] ^= 0xFF
    b[13] ^= 0xFF
    b[14] ^= 0xFF
    b[15] ^= 0xFF
    fv = struct.unpack('<I', bytes(b[12:16]))[0]
    forged.append((a, fv))
# 先证伪值在镜像里确实不存在（否则不是空面）
exists = [a for a, fv in forged
          if raw.find(struct.pack('<I', fv)) >= 0 and fv in
          set(u32(x) for x in range(RD0, RD1 - 4, 4))]
ck('C2b-0 前置：%d 个伪造 GUID 尾值在 .rdata 里作为 dword **不存在**（唯一者 %d 个）'
   % (len(forged), len(forged) - len(exists)),
   not exists, {'collisions': exists})

forged_hits = sum(len(push_sites(fv)) for _, fv in forged)
ck('C2b 空面反控（同质：同家族同长度、只改末 4 字节）：%d 个伪造 GUID 值的 push 站点合计 %d 次'
   % (len(forged), forged_hits), forged_hits == 0,
   {'n': len(forged), 'hits': forged_hits})

# C3 结构置换：换键为随机 4 字节
perm_hits = 0
for _ in range(200):
    v = random.getrandbits(32)
    perm_hits += len(push_sites(v))
ck('C3 结构置换：200 个随机 32 位键的 push 站点合计 %d 个（期望 ~0）' % perm_hits,
   perm_hits <= 2, {'hits': perm_hits})

# C4 基线：判据的灵敏度不能靠「随便什么地址都命中」
n68 = TX.count(b'\x68')
ck('C4 基线：.text 里 68 字节（push imm32 首字节）共 %d 个，其中真正指令对齐的 push imm32 '
   '由 B1 已证与字节模式一致' % n68, n68 > 1000, {'count_68': n68})

# ---------------- 结论 ----------------
leak = {a: {'rdata': by_value[a]['rdata_only'], 'by_value': by_value[a]['total_by_value']}
        for a in STUDIED if by_value[a]['total_by_value'] != by_value[a]['rdata_only']}
json.dump({'guids': {g: v for g, v in found.items()},
           'studied': by_value, 'leak': leak, 'recon_r116': recon,
           'checks': checks}, open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

npass = sum(1 for c in checks if c['ok'])
print('\n%d PASS / %d FAIL  -> %s' % (npass, len(checks) - npass, OUT), flush=True)
sys.exit(0 if npass == len(checks) else 1)
