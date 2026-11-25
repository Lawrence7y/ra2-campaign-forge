# -*- coding: utf-8 -*-
"""r135b_f29_recompute.py -- R135 主会话对 F29 五组数字的独立复算（规则 D）

不复用 _r135/sub_deepseek 与 _r95/_r109 任何代码；PE 解析、导入遍历、字节搜索全部自写。
每一项自带正控（数字应命中）与反控（把条件改坏看计数是否翻转）。
只读 game md.exe；输出写 _r135/r135b_f29.json。
"""
import io
import os
import re
import sys
import json
import hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
BIN = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
res = []
OUT = {}


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-60s %s' % ('PASS' if cond else 'FAIL', name, detail))


b = io.open(BIN, 'rb').read()
OUT['sha256'] = hashlib.sha256(b).hexdigest()
OUT['size'] = len(b)


# ---------- PE 自解析 ----------
def pe_sections(blob):
    e_lfanew = int.from_bytes(blob[0x3c:0x40], 'little')
    assert blob[e_lfanew:e_lfanew + 4] == b'PE\0\0'
    coff = e_lfanew + 4
    nsec = int.from_bytes(blob[coff + 2:coff + 4], 'little')
    optsz = int.from_bytes(blob[coff + 16:coff + 18], 'little')
    opt = coff + 20
    magic = int.from_bytes(blob[opt:opt + 2], 'little')
    imgbase = int.from_bytes(blob[opt + 28:opt + 32], 'little')
    secoff = opt + optsz
    out = []
    for i in range(nsec):
        o = secoff + i * 40
        nm = blob[o:o + 8].rstrip(b'\0').decode('latin1')
        vsz = int.from_bytes(blob[o + 8:o + 12], 'little')
        rva = int.from_bytes(blob[o + 12:o + 16], 'little')
        rsz = int.from_bytes(blob[o + 16:o + 20], 'little')
        raw = int.from_bytes(blob[o + 20:o + 24], 'little')
        out.append({'name': nm, 'vsz': vsz, 'rva': rva, 'rsz': rsz, 'raw': raw})
    return imgbase, magic, out


imgbase, magic, SEC = pe_sections(b)
chk('P1 PE32 magic 0x10b / ImageBase 0x400000 / 5 节',
    magic == 0x10b and imgbase == 0x400000 and len(SEC) == 5,
    'magic=%#x base=%#x nsec=%d' % (magic, imgbase, len(SEC)))
OUT['sections'] = SEC


def va2off(va, span=1):
    """VA -> 文件偏移；返回 (off, secname) —— 用 [RVA, RVA+rsz) 判据，越界返回 (None, None)。"""
    rva = va - imgbase
    for s in SEC:
        if s['rva'] <= rva < s['rva'] + s['rsz']:
            if rva + span > s['rva'] + s['rsz']:
                return None, 'CROSS:' + s['name']
            return rva - s['rva'] + s['raw'], s['name']
    return None, None


def sec_of_va(va):
    rva = va - imgbase
    for s in SEC:
        if s['rva'] <= rva < s['rva'] + max(s['vsz'], s['rsz']):
            return s['name']
    return None


# 反控 P2：VA 换算必须分辨 .text 与 .data（不是恒等）
o_text, n_text = va2off(0x401000)
o_data, n_data = va2off(0x840f70)
chk('P2 va2off 分辨 .text/.data（非恒等）',
    n_text == '.text' and n_data == '.data' and o_data == 0x440f70,
    '0x401000->%s raw=%#x ; 0x840f70->%s raw=%#x' % (n_text, o_text, n_data, o_data))

# ---------- D1：TClassFactory 名字串 ----------
pat = re.compile(rb'\.\?AV\?\$TClassFactory@V([^@]+?)(@{2,})')
hits = list(pat.finditer(b))
xs = [h.group(1) for h in hits]
chk('D1a 命中 77 次、不同 X 77 个',
    len(hits) == 77 and len(set(xs)) == 77,
    'hits=%d distinct=%d' % (len(hits), len(set(xs))))
tail = {}
for h in hits:
    n = len(h.group(2))
    tail[n] = tail.get(n, 0) + 1
chk('D1b 每个 X 只出现一次', max(xs.count(x) for x in set(xs)) == 1,
    'max_count=%d' % max(xs.count(x) for x in set(xs)))
secs1 = {}
for h in hits:
    s = sec_of_va(imgbase + h.start())
    secs1[s] = secs1.get(s, 0) + 1
chk('D1c 全在 .data', secs1 == {'.data': 77}, 'dist=%s' % secs1)
# 反控 D1d：把 @{2,} 收紧成恰好 4 个 @ 后仍应 77（证明尾部形态一致，不是靠松弛凑数）
pat4 = re.compile(rb'\.\?AV\?\$TClassFactory@V([^@]+?)@@@@')
chk('D1d 反控：尾部恰好 4 个 @ 时仍 77 命中', len(pat4.findall(b)) == 77,
    'strict4=%d' % len(pat4.findall(b)))
# 反控 D1e：把模板名改一个字 -> 0（证明不是任何 V...@@ 都能中）
chk('D1e 反控：模板名改一字 -> 0 命中',
    len(re.findall(rb'\.\?AV\?\$TClassFactorX@V([^@]+?)@@@@', b)) == 0,
    'mutated=%d' % len(re.findall(rb'\.\?AV\?\$TClassFactorX@V([^@]+?)@@@@', b)))
OUT['D1'] = {'hits': len(hits), 'distinct': len(set(xs)), 'tail_at': tail, 'secs': secs1}

# ---------- D2：8 字节桩 B8 01 00 00 00 C2 04 00 ----------
STUB = bytes.fromhex('B801000000C20400')
occ = []
i = b.find(STUB)
while i >= 0:
    occ.append(i)
    i = b.find(STUB, i + 1)
secs2 = {}
for off in occ:
    s = sec_of_va(imgbase + off)
    secs2[s] = secs2.get(s, 0) + 1
chk('D2a 全镜像 40 次', len(occ) == 40, 'count=%d' % len(occ))
chk('D2b 全在 .text（0 次在数据节）', secs2 == {'.text': 40}, 'dist=%s' % secs2)
# 反控 D2c：重叠计数用 i+1 步进，验证「无重叠命中」（用 i+8 步进应得同样 40）
occ2 = []
i = b.find(STUB)
while i >= 0:
    occ2.append(i)
    i = b.find(STUB, i + 8)
chk('D2c 反控：按 i+8 不重叠步进仍 40（无自重叠命中）', len(occ2) == 40, 'nonoverlap=%d' % len(occ2))
# 反控 D2d：前 5 字节截断（B8 01 00 00 00）会远多于 40，证明这 40 不是「指令前缀计数」
c2 = b.count(bytes.fromhex('B801000000'))
chk('D2d 反控：仅 mov eax,1 前缀计数 != 40（桩计数有分辨力）', c2 != 40, 'prefix_count=%d' % c2)
OUT['D2'] = {'count': len(occ), 'secs': secs2, 'prefix_b8_1': c2}

# ---------- D3：0x6C2AC0 与 0x6C51C0 的 17 字节 ----------
SEQP = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')
got = {}
for va in (0x6C2AC0, 0x6C51C0):
    off, sn = va2off(va, len(SEQP))
    got[va] = {'off': off, 'sec': sn, 'bytes': b[off:off + len(SEQP)] if off is not None else None}
chk('D3a 两处都能落在 .text 且读得到 17 字节',
    all(v['sec'] == '.text' and v['bytes'] and len(v['bytes']) == 17 for v in got.values()),
    'secs=%s' % {hex(k): v['sec'] for k, v in got.items()})
chk('D3b 两处 17 字节逐字节相同',
    got[0x6C2AC0]['bytes'] == got[0x6C51C0]['bytes'],
    'sha_a=%s sha_b=%s' % (
        hashlib.sha256(got[0x6C2AC0]['bytes']).hexdigest()[:16],
        hashlib.sha256(got[0x6C51C0]['bytes']).hexdigest()[:16]))
chk('D3c 两处字节等于 F29 声称的序列', all(v['bytes'] == SEQP for v in got.values()),
    'claim=%s' % SEQP.hex().upper())
# 反控 D3d：同一 17 字节序列在全镜像出现几次（若远多于 2，则「两份拷贝」是计数下限不是精确数）
alloce = []
i = b.find(SEQP)
while i >= 0:
    alloce.append(i)
    i = b.find(SEQP, i + 1)
chk('D3d 反控：该 17 字节序列全镜像出现次数 >= 2（「两份拷贝」可能低估）',
    len(alloce) >= 2, 'total_occurrences=%d' % len(alloce))
OUT['D3'] = {'equal': got[0x6C2AC0]['bytes'] == got[0x6C51C0]['bytes'],
             'seq_occurrences_total': len(alloce),
             'seq_occurrences_vas': [hex(imgbase + x) for x in alloce][:12]}

# ---------- D4：导入表手工遍历 ----------
def imports(blob, base, secs):
    e_lfanew = int.from_bytes(blob[0x3c:0x40], 'little')
    opt = e_lfanew + 4 + 20
    magic = int.from_bytes(blob[opt:opt + 2], 'little')
    dd = opt + (96 if magic == 0x10b else 112)
    imp_rva = int.from_bytes(blob[dd + 8:dd + 12], 'little')

    def off_of(rva):
        for s in secs:
            if s['rva'] <= rva < s['rva'] + s['rsz']:
                return rva - s['rva'] + s['raw']
        return None

    def cstr(o):
        e = blob.index(b'\0', o)
        return blob[o:e].decode('latin1')

    descs = []
    o = off_of(imp_rva)
    while True:
        rec = blob[o:o + 20]
        if len(rec) < 20 or rec == b'\0' * 20:
            break
        # IMAGE_IMPORT_DESCRIPTOR：+0 OriginalFirstThunk(ILT) / +0xC Name / +0x10 FirstThunk(IAT)
        # 自错 S-234：首版把 +0xC 当 FirstThunk、+0x10 当 Name，两者换位，
        # 于是 DLL 名读成 FirstThunk 指向的 IAT 字节（输出里那些乱码名），372 条全落 .detour。
        oilt = int.from_bytes(rec[0:4], 'little')
        oft = int.from_bytes(rec[16:20], 'little')
        name = cstr(off_of(int.from_bytes(rec[12:16], 'little')))
        descs.append({'dll': name, 'ilt': base + oilt if oilt else 0,
                      'iat': base + oft if oft else 0, 'iat_off': off_of(oft) if oft else None})
        o += 20
    return descs


DESC = imports(b, imgbase, SEC)
chk('D4a 导入描述符个数 > 0 且首项有名字', len(DESC) > 0 and DESC[0]['dll'],
    'ndesc=%d first=%s' % (len(DESC), DESC[0]['dll'] if DESC else 'none'))

# 遍历每个描述符的 ILT 与 IAT，收集 (dll, slot_va, kind, hint, name, iat_index)
SLOTS = []
for d in DESC:
    ilt_off = va2off(d['ilt'])[0] if d['ilt'] else None
    k = 0
    if ilt_off is None:
        continue
    while True:
        ent = int.from_bytes(b[ilt_off + k * 4:ilt_off + k * 4 + 4], 'little')
        if ent == 0:
            break
        slot_va = d['iat'] + k * 4
        if ent & 0x80000000:
            SLOTS.append({'dll': d['dll'], 'slot': slot_va, 'kind': 'ord',
                          'ord': ent & 0xffff, 'hint': None, 'name': None, 'idx_in_dll': k})
        else:
            ibn = va2off(imgbase + ent)[0]
            hint = int.from_bytes(b[ibn:ibn + 2], 'little')
            nm = b[ibn + 2:b.index(b'\0', ibn + 2)].decode('latin1')
            SLOTS.append({'dll': d['dll'], 'slot': slot_va, 'kind': 'name',
                          'ord': None, 'hint': hint, 'name': nm, 'idx_in_dll': k})
        k += 1
by_slot = dict((s['slot'], s) for s in SLOTS)
chk('D4b 0x7E11C8 是某个导入槽', 0x7E11C8 in by_slot,
    'present=%s' % (0x7E11C8 in by_slot))
s = by_slot.get(0x7E11C8, {})
chk('D4c 该槽属于 KERNEL32.dll、名字 InterlockedIncrement、Hint 432',
    s.get('dll', '').upper().startswith('KERNEL32') and s.get('name') == 'InterlockedIncrement'
    and s.get('hint') == 432,
    'dll=%s name=%s hint=%s idx_in_dll=%s kind=%s' % (s.get('dll'), s.get('name'),
                                                     s.get('hint'), s.get('idx_in_dll'), s.get('kind')))
# 反控 D4d：「62」这个数按两种起点会给出不同的数 —— 口径分歧必须可见，不能只说 62
# 自错 S-235：本断言初稿写成 `A != B or True`，即恒真。恒真断言无论测量结果如何都不携带信息
# （与 R134 删掉的两条同族），故改为直接钉住两个实测值本身。
glob_idx = {}
for n, sl in enumerate(SLOTS):
    glob_idx[sl['slot']] = n
chk('D4d 反控：全局序号(从 0 起) = 63 而 DLL 内序号 = 62（「62」必须带起点口径）',
    glob_idx.get(0x7E11C8) == 63 and s.get('idx_in_dll') == 62
    and glob_idx.get(0x7E11C8) != s.get('idx_in_dll'),
    'global_idx0=%s inDLL_idx=%s' % (glob_idx.get(0x7E11C8), s.get('idx_in_dll')))
OUT['D4'] = {'found': s, 'global_idx0': glob_idx.get(0x7E11C8),
             'in_dll_idx': s.get('idx_in_dll'), 'nslots': len(SLOTS)}

# ---------- D5：导入总数 / ILT 与 IAT 的节分布 ----------
n_named = sum(1 for x in SLOTS if x['kind'] == 'name')
n_ord = sum(1 for x in SLOTS if x['kind'] == 'ord')
chk('D5a 导入共 372 条 = 按名 339 + 按序数 33',
    len(SLOTS) == 372 and n_named == 339 and n_ord == 33,
    'total=%d named=%d ord=%d' % (len(SLOTS), n_named, n_ord))
ilt_secs = {}
iat_secs = {}
for d in DESC:
    if not d['ilt']:
        continue
    k = 0
    while True:
        o_ilt = va2off(d['ilt'] + k * 4)[0]
        if o_ilt is None:
            break
        if int.from_bytes(b[o_ilt:o_ilt + 4], 'little') == 0:
            break
        sn = sec_of_va(d['ilt'] + k * 4)
        ilt_secs[sn] = ilt_secs.get(sn, 0) + 1
        k += 1
for x in SLOTS:
    sn = sec_of_va(x['slot'])
    iat_secs[sn] = iat_secs.get(sn, 0) + 1
chk('D5b ILT 372 条全在 .detour', ilt_secs == {'.detour': 372}, 'ilt=%s' % ilt_secs)
chk('D5c IAT 371 条在 .rdata、1 条在 .detour',
    iat_secs.get('.rdata') == 371 and iat_secs.get('.detour') == 1,
    'iat=%s' % iat_secs)
odd = [x for x in SLOTS if sec_of_va(x['slot']) == '.detour']
chk('D5d 那条在 .detour 的 IAT 槽属于 xyr.dll 且是按序数导入',
    len(odd) == 1 and odd[0]['dll'].lower().startswith('xyr') and odd[0]['kind'] == 'ord',
    'odd=%s' % ([(x['dll'], x['kind'], x['ord'], hex(x['slot'])) for x in odd],))
# 反控 D5e：把节归属判据改成 [rva, rva+vsz) 重算 IAT 分布 —— 若与 rsz 判据不同，说明边界敏感
def sec_of_va_vsz(va):
    rva = va - imgbase
    for s in SEC:
        if s['rva'] <= rva < s['rva'] + s['vsz']:
            return s['name']
    return None
iat2 = {}
for x in SLOTS:
    sn = sec_of_va_vsz(x['slot'])
    iat2[sn] = iat2.get(sn, 0) + 1
chk('D5e 反控：改用 vsz 判据后 IAT 分布不变（结论对边界口径不敏感）',
    iat2 == iat_secs, 'iat_vsz=%s' % iat2)
OUT['D5'] = {'total': len(SLOTS), 'named': n_named, 'ord': n_ord,
             'ilt_secs': ilt_secs, 'iat_secs': iat_secs, 'iat_secs_vsz': iat2}

npass = sum(1 for _, c, _ in res if c)
print('SUMMARY %d/%d PASS' % (npass, len(res)))
io.open(os.path.join(ROOT, '_r135', 'r135b_f29.json'), 'w', encoding='utf-8').write(
    json.dumps({'asserts': [{'name': n, 'ok': c, 'detail': d} for n, c, d in res],
                'out': OUT}, ensure_ascii=False, indent=1, default=str))
sys.exit(0 if npass == len(res) else 1)
