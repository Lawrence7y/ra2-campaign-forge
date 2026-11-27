#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 M：V557 -> V558，只改 F24.limitations 一处错误指认（2 B 归属）+ 追加一段自错登记。

被改的那句（V557 实测）：
  「2 = raw[913237:913238] 的 calls 收尾 } 与 raw[17624354:17624355] 的文档收尾 } 各 1 B」
错在哪（r175l 25 断言 0 FAIL 钉死）：
  913,237 = len(b'"calls": ') 9 + dumps(calls) 913,228，**已含 raw[913237] 那个 }**；
  故它不可能同时又是「净额之外多出的 2 B」的一员。
正解（两条互斥账）：
  删成员后 913,239 = 913,238 + 1（末字节 }）；净额 913,237 = 913,239 − 2
  ⇒ 多出的 2 B 是 raw[0] 的 { 与 raw[17624354] 的 }。
  等价 14 B 分解：1({) + 12(, "bounds": ) + 1(}) = 14，逐字节 = raw[0:1] + raw[913238:913250] + raw[17624354:17624355]。
"""
import hashlib, io, json, os, sys
from difflib import SequenceMatcher
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
MOM = os.path.join(TIER, 'R17_R128_FACTINDEX_V557/FACT_INDEX.tsv')
DSTDIR = os.path.join(TIER, 'R17_R128_FACTINDEX_V558')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
OUT = os.path.join(ROOT, '_r175/r175m_v558.json')
MOM_SHA = 'fc78f3780ef2f320d9bc86555625aaacc7a5198ea1f8fe62648d5a62bb6bdf07'
MOM_BYTES = 128363
fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = bool(cond)

raw = io.open(MOM, 'rb').read()
ck('G1a 母本 V557 字节 == 128,363', len(raw) == MOM_BYTES, len(raw))
ck('G1b 母本 sha == fc78f378…', hashlib.sha256(raw).hexdigest() == MOM_SHA, hashlib.sha256(raw).hexdigest()[:16])
ck('G1c 母本 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
t = raw.decode('utf-8')
lines = t.split('\n')
if lines and lines[-1] == '': lines = lines[:-1]
rows = {}
for l in lines[1:]:
    f = l.split('\t'); rows[f[0]] = f
ck('G1d 55 行 5 列', len(lines) == 55 and all(len(l.split('\t')) == 5 for l in lines), len(lines))
ck('G2 V558 目录不存在', not os.path.exists(DSTDIR), os.path.exists(DSTDIR))

OLD = ('2 = raw[913237:913238] 的 calls 收尾 } 与 raw[17624354:17624355] 的文档收尾 } 各 1 B，14 = 12 + 2。')
NEW = ('2 = **raw[0] 的 { 与 raw[17624354] 的 }**（**R175 订正**：此处原写「raw[913237] 的 calls 收尾 } 与 '
       'raw[17624354] 的文档收尾 }」，错在 913,237 = 9 + dumps(calls) 913,228 **已含 raw[913237] 那个 }**，'
       '它不可能同时又是净额之外多出的 2 B；两条互斥账钉死：删成员后 913,239 = 913,238 + 1（末字节 }），'
       '净额 913,237 = 913,239 − 2），14 = 12 + 2。**14 B 的逐字节形式**：1({) + 12(, "bounds": ) + 1(}) = 14，'
       '逐字节等于 raw[0:1] + raw[913238:913250] + raw[17624354:17624355]（_r175/r175l 25 断言 0 FAIL）。')
ck('G3a 原句在 limitations 恰 1 次', rows['F24'][4].count(OLD) == 1, rows['F24'][4].count(OLD))
ck('G3b 原句在 statement 0 次', rows['F24'][1].count(OLD) == 0, rows['F24'][1].count(OLD))
ck('G3c 原句在全文件恰 1 次', t.count(OLD) == 1, t.count(OLD))

st, lim = rows['F24'][1], rows['F24'][4]
new_lim = lim.replace(OLD, NEW)
ck('G4a 新句在 new_lim 恰 1 次', new_lim.count(NEW) == 1, new_lim.count(NEW))
ck('G4b 旧句在 new_lim 0 次', new_lim.count(OLD) == 0, new_lim.count(OLD))
ck('G4c statement 未变', new_lim is not None and st == rows['F24'][1], True)
ck('G4d 新句含「raw[0] 的 {」与「913,239 = 913,238 + 1」两条实体', 'raw[0] 的 {' in new_lim and '913,239 = 913,238 + 1' in new_lim, True)
new_rows, units = {}, {}
for fid, f in rows.items():
    f2 = list(f)
    if fid == 'F24':
        f2[4] = new_lim
    units[fid] = [i for i in range(5) if f2[i] != f[i]]
    new_rows[fid] = f2
ck('G5a F24 变化单元恰 {4}', units['F24'] == [4], units['F24'])
ck('G5b 其余 53 行零变化', all(not v for k, v in units.items() if k != 'F24'),
   {k: v for k, v in units.items() if v and k != 'F24'})
ck('G6 反控：把 2 B 改回「两个 }」⇒ 与互斥账冲突（该形态不得出现在 new_lim）',
   new_lim.count('raw[913237:913238] 的 calls 收尾') == 0, new_lim.count('raw[913237:913238] 的 calls 收尾'))
ck('G7 新 limitations 字节 >= 旧 35,453（no-shrink 地板有效）', len(new_lim.encode()) >= 35453, len(new_lim.encode()))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
body = '\n'.join([lines[0]] + ['\t'.join(new_rows[l.split('\t')[0]]) for l in lines[1:]]) + '\n'
ck('G8 新全文 CR == 0', '\r' not in body)
os.makedirs(DSTDIR)
io.open(DST, 'w', encoding='utf-8', newline='\n').write(body)
back = io.open(DST, 'rb').read()
sha = hashlib.sha256(back).hexdigest()
print('   wrote %s bytes=%d sha=%s' % (DST, len(back), sha))
b2 = back.decode('utf-8').split('\n')
if b2 and b2[-1] == '': b2 = b2[:-1]
r2 = {l.split('\t')[0]: l.split('\t') for l in b2[1:]}
ck('H1 回读 55 行 5 列', len(b2) == 55 and all(len(l.split('\t')) == 5 for l in b2), len(b2))
ck('H2 回读 CR == 0', back.count(b'\r') == 0)
ck('H3 回读 sha 与构造一致', sha == hashlib.sha256(body.encode()).hexdigest())
ck('H4 其余 53 行逐字节相同', all(r2[k] == rows[k] for k in rows if k != 'F24'),
   [k for k in rows if k != 'F24' and r2[k] != rows[k]][:5])
ck('H5 母本 V557 一字未改', hashlib.sha256(io.open(MOM, 'rb').read()).hexdigest() == MOM_SHA)
ops = [o for o in SequenceMatcher(None, lim, new_lim, autojunk=False).get_opcodes() if o[0] != 'equal']
print('   lim opcodes=%r' % (ops,))
print('   delta bytes=%d ; lim %d -> %d' % (len(back) - MOM_BYTES, len(lim.encode()), len(new_lim.encode())))
res.update({'dst': DST, 'dst_bytes': len(back), 'dst_sha256': sha, 'delta': len(back) - MOM_BYTES,
            'lim_bytes': [len(lim.encode()), len(new_lim.encode())], 'ops': ops,
            'assertions': n, 'fails': fails})
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
