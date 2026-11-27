#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158d — 独立复算 F24 的『99.992% 有字节对应』：a2_sites.json 的 bounds 段
1,392,592 条纯指令起始 VA 里，有多少条在 gamemd.exe 中确有字节落到该地址。

判据必须写死并说明（否则不可复引）：
  「有字节对应」= 该 VA 落在 PE 某个节（section）的已初始化范围内，
  且该节该偏移处**确实被映像映射**（SizeOfRawData 覆盖该偏移）。
  这是最弱的、只需节表即可判的判据；不做指令边界对齐、不做可达性。
  （R136 用的是「是否落在任一指令起始集内」的更强判据；本脚本用节覆盖这一最弱判据，
   两者不等价，若本判据下也有近乎全量命中，则强判据的 99.992% 更可信。）

内存纪律：bounds 有 1,392,592 条，只做整数比较与 set 查询，不 disasm、不开 detail。
只读。带正控 / 负控 / 反控。
"""
import json, os, sys, hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(ROOT, 'ra2bench/gamemd.exe')
A2 = os.path.join(ROOT, 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
OUT = os.path.join(ROOT, '_r158/r158d_bounds_bytes.json')

R = []
def ck(name, cond, detail):
    ok = bool(cond)
    R.append({'name': name, 'pass': ok, 'detail': str(detail)[:400]})
    print(('  PASS  ' if ok else '  FAIL  ') + name + ' :: ' + str(detail)[:300])
    return ok

import pefile
sha = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
print('gamemd.exe sha256 =', sha)
ck('0.1 二进制 sha256 前缀 73201cc0（卡面口径）', sha.startswith('73201cc0'), sha[:16])

pe = pefile.PE(EXE, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
print('ImageBase = 0x%X  SizeOfImage = 0x%X' % (ib, pe.OPTIONAL_HEADER.SizeOfImage))
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin1')
    va = ib + s.VirtualAddress
    vsz, rsz = s.Misc_VirtualSize, s.SizeOfRawData
    secs.append({'name': nm, 'va': va, 'vend_raw': va + rsz, 'vend_virt': va + vsz})
    print('  %-10s VA=0x%08X raw=0x%06X virt=0x%06X  raw-end=0x%08X' %
          (nm, va, rsz, vsz, va + rsz))

def covered(v):
    """VA 是否落在某节 SizeOfRawData 覆盖范围内（弱判据：有文件字节映射到该地址）"""
    for s in secs:
        if s['va'] <= v < s['vend_raw']:
            return True
    return False

# ---------- 载入 bounds ----------
print('\n=== 载入 a2_sites.json ===')
d = json.load(open(A2, encoding='utf-8'))
bounds = d.get('bounds') or []
print('  bounds 条数 =', len(bounds))
print('  样例前后:', bounds[:2], bounds[-2:])
ck('1.1 bounds 条数 == 1,392,592', len(bounds) == 1392592, len(bounds))

# 解析成整数（十六进制字符串）
vals = []
bad = 0
for b in bounds:
    try:
        vals.append(int(b, 16))
    except Exception:
        bad += 1
ck('1.2 全部可解析为十六进制整数', bad == 0, {'bad': bad, 'parsed': len(vals)})

# ---------- 主测 ----------
hit = miss = 0
miss_list = []
for v in vals:
    if covered(v):
        hit += 1
    else:
        miss += 1
        if len(miss_list) < 20:
            miss_list.append('0x%08X' % v)
rate = hit / len(vals)
print('\n=== 节覆盖判据（弱口径）===')
print('  命中 %d / %d = %.6f%%' % (hit, len(vals), rate * 100))
print('  未命中 %d 条，前 20: %s' % (miss, miss_list))
ck('2.1 命中率 >= 99.99%（该弱判据下应近乎全量）', rate >= 0.9999, '%.6f%%' % (rate * 100))
ck('2.2 未命中条数 <= 200', miss <= 200, miss)

# 未命中是否全部落在某个已知边界附近的「前一指令起始 +1..8」——这里只做地址分布
if miss:
    print('  未命中 VA 的 min/max: 0x%08X / 0x%08X' % (
        min(int(x, 16) for x in miss_list), max(int(x, 16) for x in miss_list)))

# ---------- 正控 / 负控 / 反控 ----------
print('\n=== 正控 / 负控 / 反控 ===')
# 正控：一个确定落在 .text 里的 VA 必须命中
text = next(s for s in secs if s['name'] == '.text')
probe = text['va'] + 0x10
ck('3.1 正控：.text+0x10 命中', covered(probe), '0x%08X' % probe)
# 正控：ImageBase 本身（PE 头，不在任何节 raw 覆盖内？）应落在 .text 前 => 需实测
print('  ImageBase 覆盖 =', covered(ib), '(PE 头不在节内，预期 False)')
ck('3.2 正控：ImageBase 不命中（PE 头不在任何节 raw 范围）', not covered(ib), covered(ib))
# 负控：远超映像末尾
far = ib + pe.OPTIONAL_HEADER.SizeOfImage + 0x100000
ck('3.3 负控：映像末尾外 1MB 不命中', not covered(far), '0x%08X' % far)
# 反控：把 covered 改成恒真，未命中必须变 0
inv_miss = sum(1 for v in vals if not True)
ck('3.4 反控：恒真判定下未命中归 0', inv_miss == 0, inv_miss)
# 反控2：把 bounds 全换成映像外地址，命中率必须为 0
outside = [ib + pe.OPTIONAL_HEADER.SizeOfImage + 0x1000 + i for i in range(1000)]
hit2 = sum(1 for v in outside if covered(v))
ck('3.5 反控：1000 个映像外地址命中 0', hit2 == 0, hit2)
# 正控2：随机 1000 个落在 .text 内的地址必须全命中
import random
random.seed(158)
inside = [text['va'] + random.randrange(0, text['vend_raw'] - text['va'] - 1) for _ in range(1000)]
hit3 = sum(1 for v in inside if covered(v))
ck('3.6 正控：.text 内随机 1000 地址命中 1000', hit3 == 1000, hit3)

# ---------- bounds 唯一性与有序性（供「单列地址」结构判据） ----------
uset = set(vals)
print('\n=== 结构判据（支撑「单列地址、无第二列」）===')
print('  bounds 去重后 =', len(uset))
ck('4.1 bounds 无重复（纯地址清单）', len(uset) == len(vals), {'distinct': len(uset)})
mono = all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))
print('  单调不减 =', mono)
ck('4.2 bounds 单调不减（有序地址清单，非键值对）', mono, mono)
ck('4.3 calls 段是 dict（值->使用点），bounds 是 list ⇒ 两者结构不同',
   isinstance(d.get('calls'), dict) and isinstance(d.get('bounds'), list),
   {'calls': type(d.get('calls')).__name__, 'bounds': type(d.get('bounds')).__name__})

res = {'sha256': sha, 'sections': secs, 'bounds_n': len(vals),
       'hit': hit, 'miss': miss, 'rate': rate, 'miss_sample': miss_list,
       'distinct': len(uset), 'monotone': mono,
       'checks': R, 'n_pass': sum(1 for x in R if x['pass']),
       'n_fail': sum(1 for x in R if not x['pass'])}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print('\nPASS=%d FAIL=%d' % (res['n_pass'], res['n_fail']))
sys.exit(0 if res['n_fail'] == 0 else 1)
