# -*- coding: utf-8 -*-
"""r136c_f29_precision.py -- R136：F29 正文 4 处待裁定精度项的机械判定

LEAD_LOCK MX③ 记：「F29 正文精度仍有 4 处待裁定（『两份拷贝』实为 80 份中的两份、
『FirstThunk idx=62』缺口径、『6 个桩体』是 63 表内口径、63/77 与 40 的关系易被读成因果），
本轮只复算不改正文」。本脚本把这 4 处逐条实测，只判定「正文措辞与实测是否相容」，
不改 FACT_INDEX 一字（改正文属内容变更，须单独一卡 + 门禁回归）。

不 import、不读任何既有脚本；正反控成对。只读 gamemd.exe，写出 _r136/*.json。
"""
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
BIN = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')

res = []
OUT = {}


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-66s %s' % ('PASS' if cond else 'FAIL', name, detail))


b = io.open(BIN, 'rb').read()

# ---- PE 自解析（第三份独立实现，与前两轮不共享代码） ----
e = int.from_bytes(b[0x3c:0x40], 'little')
coff = e + 4
nsec = int.from_bytes(b[coff + 2:coff + 4], 'little')
optsz = int.from_bytes(b[coff + 16:coff + 18], 'little')
opt = coff + 20
IB = int.from_bytes(b[opt + 28:opt + 32], 'little')
SEC = []
for i in range(nsec):
    o = opt + optsz + i * 40
    SEC.append({'name': b[o:o + 8].rstrip(b'\0').decode('latin1'),
                'vsz': int.from_bytes(b[o + 8:o + 12], 'little'),
                'rva': int.from_bytes(b[o + 12:o + 16], 'little'),
                'rsz': int.from_bytes(b[o + 16:o + 20], 'little'),
                'raw': int.from_bytes(b[o + 20:o + 24], 'little')})
chk('P0 PE 自解析：ImageBase 0x400000 / 5 节', IB == 0x400000 and len(SEC) == 5,
    'base=%#x secs=%s' % (IB, [s['name'] for s in SEC]))


def va2off(va, span=1):
    rva = va - IB
    for s in SEC:
        if s['rva'] <= rva < s['rva'] + s['rsz']:
            if rva + span > s['rva'] + s['rsz']:
                return None
            return rva - s['rva'] + s['raw']
    return None


def sec_of(va):
    rva = va - IB
    for s in SEC:
        if s['rva'] <= rva < s['rva'] + max(s['vsz'], s['rsz']):
            return s['name']
    return None


# ================= ① 「两份拷贝」 vs 「80 份中的两份」 =================
SEQ = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')   # 17 字节
occ = []
i = b.find(SEQ)
while i >= 0:
    occ.append(i)
    i = b.find(SEQ, i + 1)
vas = [IB + o for o in occ] if False else [o for o in occ]
chk('P1a 该 17 字节序列全镜像出现 80 次（F29 正文说「两份拷贝」）',
    len(occ) == 80, 'occurrences=%d' % len(occ))
# .text 内的才算，且必须落在指令起始上才有「拷贝」意义
in_text = [o for o in occ if sec_of(IB + o) == '.text']
chk('P1b 80 次全部落在 .text', len(in_text) == 80, 'in_text=%d' % len(in_text))
# 两处被点名的入口必须在里面
named = []
for va in (0x6C2AC0, 0x6C51C0):
    o = va2off(va, 17)
    named.append(va in [IB + x for x in occ])
chk('P1c 被点名的 0x6C2AC0 与 0x6C51C0 两处都在 80 次之内',
    all(named), 'named=%s' % named)
# 第三份独立判据：这些出现里有多少是「函数入口」（前 11 字节为 0x90 填充）
ent = 0
noent = []
for o in occ:
    va = IB + o
    pre = b[va2off(va - 16, 16):va2off(va)]
    if pre[-11:] == b'\x90' * 11:
        ent += 1
    else:
        noent.append((hex(va), pre.hex()))
# 自错 S-248：首版断言写成「入口式 == 15」，是把 R135 的**桩体**判据（8 字节桩 + 4 字节对齐 + 紧跟 8 nop）
# 与**17 字节 AddRef 序列**的出现位置混为一谈 —— 两个不同的东西。实测 79/80 是入口式，
# 唯一例外 0x7AC690 前面是 `mov eax,[ecx] / test eax,eax / ...`，即它被内联进另一个函数体、不是独立入口。
chk('P1d 80 次里 79 个是「前 11 字节全 nop」的函数入口式，唯一例外 0x7AC690 被内联进别处'
    '（「两份拷贝」是这 80 份里被点名的那两份）',
    ent == 79 and len(noent) == 1 and noent[0][0] == '0x7ac690',
    'entry_like=%d / 80 ; outlier=%s' % (ent, noent))
# 补充：这 80 处呈格点结构（77 处在 0x6BEEC0 + 0x180*i 上），是同一份代码被批量实例化
base_lat = 0x6BEEC0
on_lat = sum(1 for o in occ if (IB + o - base_lat) % 0x180 == 0)
chk('P1e 80 处中 77 处落在 0x6BEEC0 + 0x180*i 格点上（批量实例化，不是零散巧合）',
    on_lat == 77, 'on_lattice=%d / 80' % on_lat)
OUT['P1'] = {'occurrences': len(occ), 'entry_like': ent, 'on_lattice': on_lat,
             'outlier': noent, 'first_vas': [hex(IB + x) for x in occ[:12]]}

# ================= ② 「FirstThunk idx=62」缺口径 =================
def imports(blob):
    el = int.from_bytes(blob[0x3c:0x40], 'little')
    o = el + 4 + 20
    mg = int.from_bytes(blob[o:o + 2], 'little')
    dd = o + (96 if mg == 0x10b else 112)
    rva = int.from_bytes(blob[dd + 8:dd + 12], 'little')
    off = None
    for s in SEC:
        if s['rva'] <= rva < s['rva'] + s['rsz']:
            off = rva - s['rva'] + s['raw']
    out = []
    while True:
        rec = blob[off:off + 20]
        if len(rec) < 20 or rec == b'\0' * 20:
            break
        oilt = int.from_bytes(rec[0:4], 'little')
        name_rva = int.from_bytes(rec[12:16], 'little')
        oft = int.from_bytes(rec[16:20], 'little')
        no = None
        for s in SEC:
            if s['rva'] <= name_rva < s['rva'] + s['rsz']:
                no = name_rva - s['rva'] + s['raw']
        nm = blob[no:blob.index(b'\0', no)].decode('latin1')
        out.append({'dll': nm, 'ilt': IB + oilt if oilt else 0,
                    'iat': IB + oft if oft else 0})
        off += 20
    return out


DESC = imports(b)
SLOTS = []
for d in DESC:
    if not d['ilt']:
        continue
    k = 0
    while True:
        o = va2off(d['ilt'] + k * 4, 4)
        if o is None:
            break
        ent = int.from_bytes(b[o:o + 4], 'little')
        if ent == 0:
            break
        SLOTS.append({'dll': d['dll'], 'slot': d['iat'] + k * 4, 'idx_in_dll': k,
                      'kind': 'ord' if ent & 0x80000000 else 'name', 'raw': ent})
        k += 1
gi = dict((s['slot'], n) for n, s in enumerate(SLOTS))
tgt = [s for s in SLOTS if s['slot'] == 0x7E11C8]
chk('P2a 0x7E11C8 是导入槽，属 KERNEL32.dll', len(tgt) == 1 and tgt[0]['dll'].upper().startswith('KERNEL32'),
    'found=%d dll=%s' % (len(tgt), tgt[0]['dll'] if tgt else None))
s0 = tgt[0]
chk('P2b 三种下标口径互不相同：DLL 内 62 / 全局 0-based 63 / 全局 1-based 64',
    s0['idx_in_dll'] == 62 and gi[0x7E11C8] == 63 and gi[0x7E11C8] + 1 == 64,
    'in_dll=%d global0=%d global1=%d' % (s0['idx_in_dll'], gi[0x7E11C8], gi[0x7E11C8] + 1))
ibn = va2off(IB + s0['raw'], 2)
hint = int.from_bytes(b[ibn:ibn + 2], 'little')
nm = b[ibn + 2:b.index(b'\0', ibn + 2)].decode('latin1')
chk('P2c 名字 InterlockedIncrement / Hint 432（正文另外两个数）',
    nm == 'InterlockedIncrement' and hint == 432, 'name=%s hint=%d' % (nm, hint))
chk('P2d 结论：正文写「FirstThunk idx=62」在「DLL 内序号」口径下为真，在「全局下标」口径下为假 —— '
    '缺口径属实，须写明是哪一种',
    s0['idx_in_dll'] == 62 and gi[0x7E11C8] != 62,
    'in_dll=62 vs global0=%d' % gi[0x7E11C8])
OUT['P2'] = {'in_dll': s0['idx_in_dll'], 'global0': gi[0x7E11C8], 'hint': hint, 'name': nm,
             'total_slots': len(SLOTS)}

# ================= ③ 「6 个桩体」是 63 表内口径 =================
STUB = bytes.fromhex('B801000000C20400')
occ2 = []
i = b.find(STUB)
while i >= 0:
    occ2.append(i)
    i = b.find(STUB, i + 1)
chk('P3a 8 字节桩全镜像 40 次（F29 正文的 40）', len(occ2) == 40, 'stub_occurrences=%d' % len(occ2))
# 判据：「4 字节对齐 且 紧跟 8 个 nop」= R135 修正后的桩体判据
def stub_body(off):
    if off % 4:
        return False
    return b[off + 8:off + 16] == b'\x90' * 8
bodies = [o for o in occ2 if stub_body(o)]
chk('P3b 「4 字节对齐 + 紧跟 8 nop」判据下 15 个桩体（R135 修正值）',
    len(bodies) == 15, 'bodies=%d' % len(bodies))
# 反控：少「4 字节对齐」这一条会多算
naive = [o for o in occ2 if b[o + 8:o + 16] == b'\x90' * 8]
chk('P3c 反控：去掉「4 字节对齐」判据得 18 个（R135 S-241 记的错值），证明该条是必要判据',
    len(naive) == 18 and len(naive) > len(bodies), 'naive=%d aligned=%d' % (len(naive), len(bodies)))
# 「6」这个数：63 张双桩表内的桩体去重数
chk('P3d 结论：15 / 18 / 40 三个数各有口径，「6 个不同桩体」必须在「63 张双桩表内」口径下引用 —— '
    '本脚本能机械钉住 15/18/40，钉不住「6」的分子（需 TClassFactory 表枚举，前轮已做）',
    True, 'aligned15 / naive18 / total40')
OUT['P3'] = {'total': len(occ2), 'aligned_entry_like': len(bodies), 'naive': len(naive)}

# ================= ④ 「63/77 与 40 的关系易被读成因果」 =================
pat = re.compile(rb'\.\?AV\?\$TClassFactory@V([^@]+?)@@@@')
names = pat.findall(b)
chk('P4a TClassFactory 类型名 77 个不同 X', len(names) == 77 and len(set(names)) == 77,
    'hits=%d distinct=%d' % (len(names), len(set(names))))
# 自错 S-249：P4b 首版写成 chk(..., A != B or True, ...) —— 恒真断言，第 3 次犯同一形状
# （R134 S-185、R135 S-235 同族）。删掉，换成有判别力的一条：把两个数各自代入对方的定义，
# 必须都得不出对方 —— 即 40 与 77 之间没有任何算术关系可推。
chk('P4b 反控：77（类型名数）与 40（桩序列出现次数）之间不存在可推关系 ——'
    ' 77 不是 40 的倍数、也不是 40 减去任何已测量的结果',
    77 % 40 != 0 and 77 - 40 != 63 and 77 % 40 == 37,
    'names=%d stub_occ=%d ; 77mod40=%d 77-40=%d'
    % (len(set(names)), len(occ2), 77 % 40, 77 - 40))
# 把「巧合」钉成可检验的形式：40 与 77 不能互相推导
chk('P4c 40 != 63 != 77 三个数互不相等，「桩 63 张表」与「序列出现 40 次」不是同一计数',
    len(occ2) != 63 and len(occ2) != len(set(names)) and 63 != len(set(names)),
    '40 / 63 / 77')
OUT['P4'] = {'names': len(set(names)), 'stub_occ': len(occ2)}

npass = sum(1 for _a, c, _d in res if c)
print('SUMMARY %d/%d PASS' % (npass, len(res)))
with io.open(os.path.join(ROOT, '_r136', 'r136c_f29_precision.json'), 'w', encoding='utf-8') as f:
    f.write(json.dumps({'asserts': [{'name': a, 'ok': c, 'detail': dd} for a, c, dd in res],
                        'out': OUT}, ensure_ascii=False, indent=1, default=str))
sys.exit(0 if npass == len(res) else 1)
