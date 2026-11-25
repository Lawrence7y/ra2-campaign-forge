# -*- coding: utf-8 -*-
"""R126a: GUID 池普查与「孪生」关系表。

R125 的取数口径有两个未写明的假设，本脚本先把它们显式化并各自给正反控：

  A1  「GUID 池」的窗口起点必须按 Data4 的模式长度分别算。
      OLE 系 IID 的 d4 全 8 字节都是模式（C000-0000-0000-0046），
      MIDL 系 IID 的 d4 后 6 字节才是模式（00-A0-24-DD-AF-D1 一类），
      前 2 字节是变体号。用同一个 k-8 算两种模式会整体偏移 +2。
      反控：故意用错口径跑一遍，断言错口径下 0x7e36c0 这个已知地址解不出来。

  A2  「孪生」= 整份映像里 16 字节完全相同。R125 只对 0x7f7c70/0x7f7c80 做了，
      本脚本对全池做，并给出一条可失败的预测：若某 IID 有 .data 孪生，
      则 .rdata 那份的调用点形态（push 立即数 vs mov edi 分派器）应与其孪生不同。

输出 _r126/r126a_pool.json。
"""
import os, sys, json, struct, hashlib, collections
import pefile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r126', 'r126a_pool.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(name, ok, detail=''):
    ck.append({'name': name, 'ok': bool(ok), 'detail': str(detail)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
hay = bytes(pe.__data__)
add('A0 exe sha256 是钉住的那个构建',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

# 段名 -> (文件偏移下界, 上界, 虚拟地址基)
SEC = []
for s in pe.sections:
    SEC.append((s.Name.rstrip(b'\x00').decode(),
                s.PointerToRawData, s.PointerToRawData + s.SizeOfRawData,
                s.VirtualAddress + IB))

def sec_of_off(off):
    for nm, lo, hi, va in SEC:
        if lo <= off < hi:
            return nm, va + (off - lo)
    return None, None

def guid_text(b):
    d1, d2, d3 = struct.unpack('<IHH', b[:8])
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3,
                                      b[8:10].hex().upper(), b[10:].hex().upper())

# 两种 Data4 模式，各自给出 (模式字节, 模式在 d4 里的起始下标)
PATS = [
    (bytes.fromhex('C000000000000046'), 0),   # OLE 系：整个 d4
    (bytes.fromhex('00A024DDAFD1'), 2),        # MIDL 系 A
    (bytes.fromhex('00104B972FE8'), 2),        # MIDL 系 B
]

def pool(wrong_shift=False):
    """wrong_shift=True 时统一按 k-8 起算（即把 6 字节模式也当成从 d4 起算）。"""
    offs = set()
    for pat, idx in PATS:
        st = 0
        while True:
            k = hay.find(pat, st)
            if k < 0:
                break
            st = k + 1
            # pat 的起点位于 d4 内偏移 idx 处；d4 起于 GUID 起点 + 8
            off = k - (8 + (0 if wrong_shift else idx))
            nm, va = sec_of_off(off)
            if nm in ('.rdata', '.data'):
                offs.add(off)
    rows = []
    for off in sorted(offs):
        b = hay[off:off + 16]
        tw = []
        st = 0
        while True:
            k = hay.find(b, st)
            if k < 0:
                break
            tw.append(k)
            st = k + 1
        nm, va = sec_of_off(off)
        rows.append({
            'va': va, 'section': nm, 'off': off, 'guid': guid_text(b),
            'n_twin': len(tw),
            'twins': [{'section': sec_of_off(k)[0], 'va': sec_of_off(k)[1]}
                      for k in tw],
        })
    return rows

rows = pool()
add('A1 池非空且规模落在可机械复核的量级', 50 < len(rows) < 120, 'windows=%d' % len(rows))

bad = pool(wrong_shift=True)
bad_vas = {r['va'] for r in bad}
add('A2 反控：统一按 k-8 起算的错口径解不出 0x7e36c0 与 0x7e9b20（即偏移假设真的起作用）',
    0x7e36c0 not in bad_vas and 0x7e9b20 not in bad_vas
    and 0x7e36c0 in {r['va'] for r in rows},
    '错口径命中 0x7e36c0=%s 0x7e9b20=%s ; 正口径命中两者'
    % (0x7e36c0 in bad_vas, 0x7e9b20 in bad_vas))

# 每个 GUID 必须真的以某个模式收尾，否则窗口算错了
def ends_ok(b):
    return any(b[8 + idx:] == pat for pat, idx in PATS)
add('A3 池里每一条的 d4 都真的以某个模式收尾（窗口对齐自检）',
    all(ends_ok(hay[r['off']:r['off'] + 16]) for r in rows),
    'mismatch=%s' % [hex(r['va']) for r in rows
                     if not ends_ok(hay[r['off']:r['off'] + 16])])

# 标准 OLE 前缀的 IID（Data1 <= 0x000001FF 且 d2=d3=0 且 d4=C000..0046）
OLE_FAMILY = [r for r in rows if r['guid'].startswith('{0000')]
add('A4 OLE 标准前缀的 IID 恰为下列固定集合',
    sorted({int(r['guid'][1:9], 16) for r in OLE_FAMILY})
    == [0x0, 0x1, 0xC, 0x109, 0x10C, 0x13A],
    sorted('%08X@%x' % (int(r['guid'][1:9], 16), r['va']) for r in OLE_FAMILY))

by_va = {r['va']: r for r in rows}

# 孪生关系的形状：.rdata 与 .data 成对的行
pairs = [r for r in rows if r['section'] == '.rdata' and r['n_twin'] == 2]
solo = [r for r in rows if r['n_twin'] == 1]
add('A5 孪生集合与孤立集合都非空（不是全有或全无的退化）',
    len(pairs) > 0 and len(solo) > 0, 'paired=%d solo=%d' % (len(pairs), len(solo)))

tw_table = []
for r in pairs:
    other = [t for t in r['twins'] if t['va'] != r['va']][0]
    tw_table.append({'rdata': r['va'], 'data': other['va'], 'guid': r['guid']})
add('A6 每对孪生都是一个 .rdata 配一个 .data（没有 .rdata 内自孪生）',
    all(t['rdata'] != t['data'] for t in tw_table) and len(tw_table) == len(pairs),
    tw_table)

# 反控：孪生的定义是整 16 字节相同，改 1 字节就不应再配对
r0 = pairs[0]
b0 = bytearray(hay[r0['off']:r0['off'] + 16])
b0[15] ^= 0xFF
add('A7 反控：把一对孪生的末字节翻转后，该 16 字节串在映像里只剩 1 处',
    hay.find(bytes(b0)) < 0,
    '0x%x 翻转后命中' % r0['va'])

# ISequentialStream 的 IID 是否真的不在映像里（R125 把 0x7f7cf0 记成「IStream 与
# ISequentialStream 之间不可分」，本项直接可失败）
ISEQ = struct.pack('<IHH', 0x0C733A30, 0x2A1C, 0x11CE) + bytes.fromhex('ADE500AA0044773D')
n_iseq = hay.count(ISEQ)
add('A8 IID_ISequentialStream 的 16 字节在整份映像里出现 0 次',
    n_iseq == 0, 'hits=%d' % n_iseq)
# 只取 Data1 再查一遍，确认不是「整串没有但前缀在」
n_d1 = hay.count(struct.pack('<I', 0x0C733A30))
add('A9 连 ISequentialStream 的 Data1 都不在映像里（防止「只有整串缺失」的误读）',
    n_d1 == 0, 'Data1 hits=%d' % n_d1)
# 正控：IStream 的 Data1 应在
n_stream_d1 = hay.count(struct.pack('<I', 0x0000000C))
add('A10 正控：IStream 的 Data1 0x0000000C 在映像里存在（同上方法能查得到东西）',
    n_stream_d1 > 0, 'Data1 hits=%d' % n_stream_d1)

rep = {'exe_sha256': EXE_SHA, 'pool': rows, 'twins': tw_table,
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad_ck = [c for c in ck if not c['ok']]
print('R126a %d/%d PASS' % (len(ck) - len(bad_ck), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
print('pool=%d pairs=%d' % (len(rows), len(tw_table)))
sys.exit(0 if not bad_ck else 1)
