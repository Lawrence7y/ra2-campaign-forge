#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181c_c19_probe.py —— 在动手改 check_disc.py 之前，先把 C19 拟采用的多条判据
各自是否「真能 FAIL」实测一遍（正反控），避免又造一条永远通过子项。

判据候选（全部从盘上现算，不抄结论）：
 A) facts_floors.py 源码 CUR_SHA256 字面量 == 现盘 V563/FACT_INDEX.tsv sha256
 B) facts_floors.py 源码 TOTAL_BYTES 字面量 == 现盘该文件字节数
 C) check_disc.py 自身嵌入 facts_floors.py 的 sha256 == 现盘 facts_floors.py sha256
 D) FACT_INDEX_CURRENT.md sha256 字段 == 现盘 V563/FACT_INDEX.tsv sha256
 E) FACT_INDEX_CURRENT.md 字节数字段 == 现盘字节数

每条都做三件事：现盘绿 / 沙箱改目标 / 沙箱改常量（同改两侧）—— 同改两侧那一栏如实记录
是否仍绿（这是所有指纹类门禁的共同上限，不粉饰）。
"""
import ast, hashlib, io, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
GATE = os.path.join(TIER, 'check_disc.py')
FACTS = os.path.join(ROOT, '_r160', 'facts_floors.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V563', 'FACT_INDEX.tsv')

fails, oks = [], []
def ck(name, cond, detail=''):
    (oks if cond else fails).append(name)
    print(('  PASS  ' if cond else '  FAIL  ') + name + (('  ' + str(detail)) if detail else ''))
    return cond

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def ast_consts(p):
    tree = ast.parse(open(p, encoding='utf-8').read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and isinstance(node.value, ast.Constant):
                out[t.id] = node.value.value
    return out

print('--- A/B：facts_floors 常量 vs 现盘实物 ---')
fc = ast_consts(FACTS)
ck('A1 facts CUR_SHA256 从 ast 取到', 'CUR_SHA256' in fc, repr(fc.get('CUR_SHA256'))[:20])
ck('A2 facts TOTAL_BYTES 从 ast 取到', 'TOTAL_BYTES' in fc, fc.get('TOTAL_BYTES'))
cursha = sha(CUR)
curlen = os.path.getsize(CUR)
ck('A3 CUR_SHA256 == 现盘 V563 sha', fc.get('CUR_SHA256') == cursha, (fc.get('CUR_SHA256', '')[:16], cursha[:16]))
ck('A4 TOTAL_BYTES == 现盘 V563 字节', fc.get('TOTAL_BYTES') == curlen, (fc.get('TOTAL_BYTES'), curlen))

print('--- D/E：指针字段 vs 现盘实物 ---')
pt = io.open(PTR, encoding='utf-8', newline='').read()
ms = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', pt)
mb = re.search(r'\| 字节数 \| (\d+) \|', pt)
ck('D0 指针 sha 字段可解析', bool(ms))
ck('E0 指针 字节 字段可解析', bool(mb))
if ms and mb:
    ck('D1 指针 sha == 现盘 V563 sha', ms.group(1) == cursha, (ms.group(1)[:16], cursha[:16]))
    ck('E1 指针 字节 == 现盘 V563 字节', int(mb.group(1)) == curlen, (mb.group(1), curlen))
print('--- 指针声明的版本目录名 vs 现盘路径 ---')
mdir = re.search(r'\| 版本目录 \| (\S+) \|', pt)
ck('F1 指针版本目录名 == 实际所在目录名', bool(mdir) and mdir.group(1) == os.path.basename(os.path.dirname(CUR)),
   (mdir.group(1) if mdir else None, os.path.basename(os.path.dirname(CUR))))

print('--- C：check_disc 里是否已有 facts_floors 的 sha 常量（预期 0 ⇒ C 项是新增面）---')
gtxt = open(GATE, encoding='utf-8').read()
gc = ast_consts(GATE)
fsha = sha(FACTS)
pin_hits = [k for k, v in gc.items() if isinstance(v, str) and v == fsha]
ck('C1 现盘 check_disc 尚未嵌 facts_floors sha（新增面确认）', not pin_hits, pin_hits)
ck('C2 check_disc 对 facts_floors 子串出现 0 次', gtxt.count('facts_floors') == 0, gtxt.count('facts_floors'))
ck('C3 check_disc 对 FACT_INDEX 子串出现 0 次', gtxt.count('FACT_INDEX') == 0, gtxt.count('FACT_INDEX'))
ck('C4 正控：facts_floors 自身出现子串 FACT_INDEX 次数 > 0（计数法没坏）',
   open(FACTS, encoding='utf-8').read().count('FACT_INDEX') > 0,
   open(FACTS, encoding='utf-8').read().count('FACT_INDEX'))
ck('C5 正控：gate_runner 出现 facts_floors 次数 > 0',
   open(os.path.join(ROOT, '_r161', 'gate_runner.py'), encoding='utf-8').read().count('facts_floors') > 0)

print('--- G：破坏性反控（沙箱，绝不碰生产）---')
tmpd = tempfile.mkdtemp(prefix='r181c_')
try:
    # G1：改沙箱副本台账一个字节 ⇒ A3/A4(重算) 必须不等
    sand_cur = os.path.join(tmpd, 'FACT_INDEX.tsv')
    shutil.copy2(CUR, sand_cur)
    b = bytearray(open(sand_cur, 'rb').read())
    b[100] = (b[100] + 1) % 256
    open(sand_cur, 'wb').write(bytes(b))
    ck('G1 沙箱台账改 1 字节 ⇒ sha 与常量不等（判据有分辨力）',
       hashlib.sha256(bytes(b)).hexdigest() != fc.get('CUR_SHA256'))
    # G2：沙箱指针把 sha 末位改掉 ⇒ D1 判据必须不等
    sand_ptr = os.path.join(tmpd, 'FACT_INDEX_CURRENT.md')
    pt2 = pt.replace(ms.group(1), ms.group(1)[:-1] + ('0' if ms.group(1)[-1] != '0' else '1'))
    open(sand_ptr, 'w', encoding='utf-8', newline='').write(pt2)
    pt2txt = io.open(sand_ptr, encoding='utf-8', newline='').read()
    ms2 = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', pt2txt)
    ck('G2 沙箱指针 sha 末位改 ⇒ 与现盘不等（末位篡改可见）', ms2.group(1) != cursha,
       (ms2.group(1)[-8:], cursha[-8:]))
    # G3：同改两侧上限 —— 沙箱台账与沙箱指针一起改，A3/D1 都仍相等
    sand_cur2 = os.path.join(tmpd, 'CUR2.tsv')
    shutil.copy2(sand_cur, sand_cur2)
    sha2 = sha(sand_cur2)
    pt3 = pt.replace(ms.group(1), sha2).replace(mb.group(1), str(os.path.getsize(sand_cur2)))
    open(os.path.join(tmpd, 'PTR2.md'), 'w', encoding='utf-8', newline='').write(pt3)
    pt3txt = io.open(os.path.join(tmpd, 'PTR2.md'), encoding='utf-8', newline='').read()
    ck('G3 共同上限如实登记：同时改台账与指针 ⇒ 指针一致性判据仍相等（指纹类共同天花板）',
       re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', pt3txt).group(1) == sha2)
finally:
    shutil.rmtree(tmpd, ignore_errors=True)

print('--- H：C 项（嵌 facts_floors sha）的代价实测 ---')
# 若 C 落地，则每次改 facts_floors.py 都要同时改 check_disc.py 里那个常量 ⇒ 代价 = 1 处/次
ck('H1 facts_floors.py 的常量个数（改它需要重钉的常量数，供估算代价）', True, len(fc))
print('--- 汇总 ---')
print('PASS %d / FAIL %d' % (len(oks), len(fails)))
if fails:
    print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
