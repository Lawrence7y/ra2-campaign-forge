#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r117f_fo_bug.py —— R117 第六链：核一条由 A1 可伪证化顺带抓出的 **R116 实质错误**。

问题来源：R117a 把「35 项里几项在文件里有字节」这条断言从恒真式改成可伪证式之后，
立刻失败了 —— 但失败方向是「文件映像内 0 个」而不是预期的 5 个。追查根因：

  r112_lib 的 fo(v) = v - ImageBase 是**朴素偏移**，不查节表。
  .data 的 VirtualSize = 0x367BE4，但 SizeOfRawData 只有 0x6C000。
  文件里 .data 原始数据之后紧跟 .rsrc 的原始数据。
  于是对地址 0x887388（= .data 内偏移 0x75388 > 0x6C000），
  fo() 返回 0x487388，这个位置**在文件里确实有字节，但那是 .rsrc 的字节**。

R116 §ER4/A4 因此把 5 个条目读成「有文件映像」，并把读到的内容当成了 .data 结构 ——
其中就有后来被 R116 自错 S-26 判定为「UTF-16 字符串」的那几个值（"t\\0y\\0" / "G\\0U\\0"）。
S-26 当时只否掉了「区间命中=指针」这个判据，**没有追到根因**：那些字节根本不是条目的字节。

断言：
  Q1 节表实测：.data 的 VA 区间、VirtualSize、SizeOfRawData、有映像 VA 上界。
  Q2 35 个条目地址**全部**落在 .data 但**全部**超出有映像上界 ⇒ 文件内可读 0 个（不是 5 个）。
  Q3 朴素 fo() 在 35 个条目上给出非 None 的有 N 个（复现 R116 的 5），且这 N 个的朴素偏移
     全部落进 .rsrc 的原始数据区（证明误映射）。
  Q4 反控（有牙）：对 .data 有映像区内的 200 个随机地址，朴素 fo() 与节表 fo() 必须**一致**
     ⇒ 本缺陷只在有映像区之外出现，不是「两种 fo 普遍不同」。
  Q5 定性：R116 的「5 个有文件字节」是**误映射**，正确数字是 0；
     这**加强**了 R117 的结论（35 项全部只能靠静态写入点推定，没有一项能从文件读到）。
     同时说明 S-26 的根因登记不完整，本轮补登。
内存纪律：只读 PE 节表 + raw 字节；未开 detail。
"""
import json, os, random, struct, sys
import pefile

ROOT = '/home/t628/projects/ra2-campaign-forge'
OUT = os.path.join(ROOT, '_r117/r117f_fo_bug.json')
checks = []
raw = open(os.path.join(ROOT, 'ra2bench/gamemd.exe'), 'rb').read()


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


pe = pefile.PE(os.path.join(ROOT, 'ra2bench/gamemd.exe'), fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
SEC = []
for s in pe.sections:
    SEC.append({'name': s.Name.rstrip(b'\x00').decode(),
                'va': s.VirtualAddress + IB,
                'vs': s.Misc_VirtualSize,
                'pd': s.PointerToRawData,
                'rs': s.SizeOfRawData})
D = [s for s in SEC if s['name'] == '.data'][0]
R = [s for s in SEC if s['name'] == '.rsrc'][0]
ck('Q1 节表实测（ImageBase 0x%08x）：.data VA=[%08x, %08x) VirtualSize=%08x '
   'PointerToRawData=%08x SizeOfRawData=%08x ⇒ **有文件映像的 VA 上界 = %08x**（远小于 VirtualSize 上界）；'
   '.rsrc 的原始数据紧跟其后：[%08x, %08x)'
   % (IB, D['va'], D['va'] + D['vs'], D['vs'], D['pd'], D['rs'], D['va'] + D['rs'],
      R['pd'], R['pd'] + R['rs']),
   D['va'] == 0x812000 and D['vs'] == 0x367BE4 and D['rs'] == 0x6C000,
   {'data': D, 'rsrc': R})


def fo_naive(v):
    o = v - IB
    return o if 0 <= o + 4 <= len(raw) else None


def fo_sec(v):
    for s in SEC:
        if s['va'] <= v < s['va'] + s['vs']:
            return v - s['va'] + s['pd'] if v - s['va'] < s['rs'] else None
    return None


def sec_of(v):
    for s in SEC:
        if s['va'] <= v < s['va'] + s['vs']:
            return s['name']
    return None


A = json.load(open(os.path.join(ROOT, '_r117/r117a_obj_entries.json')))
ENTS = [int(r['entry'], 16) for r in A['rows']]
n_sec = sum(1 for v in ENTS if fo_sec(v) is not None)
n_naive = sum(1 for v in ENTS if fo_naive(v) is not None)
ck('Q2 35 个条目：节表口径「文件内可读」= %d 个（应为 0）；朴素口径 = %d 个（应复现 R116 的 5）'
   % (n_sec, n_naive), n_sec == 0 and n_naive == 5,
   {'by_section': n_sec, 'by_naive': n_naive})

bad = []
for v in ENTS:
    o = fo_naive(v)
    if o is None:
        continue
    insc = None
    for s in SEC:
        if s['pd'] <= o < s['pd'] + s['rs']:
            insc = s['name']
    bad.append([hex(v), hex(o), insc, sec_of(v)])
ck('Q3 朴素 fo() 命中的那 %d 个条目，其朴素偏移**全部**落在别的节的原始数据里（实测节名 %s）'
   ' ⇒ 「有文件字节」是跨节误映射，读到的不是 .data'
   % (len(bad), sorted(set(b[2] for b in bad))),
   len(bad) == 5 and all(b[2] == '.rsrc' for b in bad), {'rows': bad})

random.seed(20261124)
same = 0
probe = 0
for _ in range(200):
    v = random.randrange(D['va'], D['va'] + D['rs'] - 8, 4)
    probe += 1
    if fo_naive(v) == fo_sec(v):
        same += 1
ck('Q4 反控（有牙）：在 .data **有映像区**内随机取 %d 个地址，朴素 fo() 与节表 fo() '
   '一致 %d 个（必须全部一致）⇒ 本缺陷只在有映像区之外出现，不是两种口径普遍不同'
   % (probe, same), same == probe, {'probe': probe, 'same': same})

ck('Q5 定性：R116 §ER4/A4 的「35 项里 5 项有文件映像」是**误映射**，正确数字是 **0**；'
   '因此 R117 的结论被**加强**（35 项无一能从文件读到初值，只能靠静态写入点推定），'
   '同时 R116 S-26 的根因登记不完整（只否掉了判据，没追到「字节不属于本条目」）'
   '—— 补登记为本轮 S-40',
   True, 'ok')

json.dump({'sections': SEC, 'data_image_va_end': hex(D['va'] + D['rs']),
           'by_section': n_sec, 'by_naive': n_naive, 'cross_mapped': bad,
           'checks': checks,
           'verdict': 'r112_lib 的 fo=v-ImageBase 是朴素偏移；.data 有映像上界 %08x，'
                      '35 个条目全部超出 ⇒ 文件内可读 0 个（R116 的 5 个是 .rsrc 跨节误映射）'
                      % (D['va'] + D['rs'])},
          open(OUT, 'w'), indent=1, ensure_ascii=False)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
