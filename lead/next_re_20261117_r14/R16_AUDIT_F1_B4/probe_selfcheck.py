# -*- coding: utf-8 -*-
"""自检：atexit 检测器 / 删除析构器检测器 是否非空转。"""
import io, os, sys, bisect
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify as V

img = V.Image(V.EXE)
code = V.Code(img)
sizes = V.load_atlas()
ranges = V.body_ranges(sizes)

tgt = V.ATEXIT_CALL
sites = code.calls.get(tgt, [])
print('call sites to 0x%08X (atexit): %d' % (tgt, len(sites)))

# 统计：这些 call 前面 12 字节内的 push imm32 -> 被注册的函数集合
reg = set()
for cs in sites:
    for back in range(0, 13):
        i = code.decode_one(cs - back)
        if i is None:
            continue
        if i.mnemonic == 'push' and i.op_str:
            try:
                reg.add(int(i.op_str, 16))
            except ValueError:
                pass
print('push-imm 注册目标候选（去重前）=%d' % len(reg))
in_text = [x for x in reg if V.TEXT_LO <= x < V.TEXT_HI]
print('落在 .text 的注册目标=%d' % len(in_text))
print('样例: %s' % ' '.join('%08X' % x for x in sorted(in_text)[:10]))

# 这些注册目标里有多少在 atlas 有函数体、多少个是删除析构器
n_body = sum(1 for x in in_text if V.which_body(ranges, x) == x)
print('在 atlas 中作为函数体起点=%d / %d' % (n_body, len(in_text)))

# 已知实例：§13.5 提到 004E6B20、0040D1B0、0043C098 等应被识别
for a in ('004E6B20', '0040D1B0', '0043C073'):
    v = int(a, 16)
    print('  registered(%s) = %s' % (a, V.is_atexit_registered(img, code, v)))

# 全表写点里，落在 atexit 注册函数体内的写点数
n_atexit_writes = 0
n_free_writes = 0
for imm, ws in code.writes.items():
    for (site, disp, asm) in ws:
        fn = V.which_body(ranges, site)
        if fn is None:
            continue
        d = V.classify_write(img, code, ranges, sizes, site, 0, 0, imm)
        if d.get('atexit_reg'):
            n_atexit_writes += 1
        if d.get('delfree_sig'):
            n_free_writes += 1
print('全镜像 vt 写点中：atexit 函数体内=%d，删除析构器体内=%d'
      % (n_atexit_writes, n_free_writes))

# scan_dd 命中 vs fields 声明
B4 = V.B4
rows = []
for n, ln in enumerate(io.open(os.path.join(B4, 'delta.tsv'), encoding='utf-8-sig')):
    if n:
        rows.append(ln.rstrip('\r\n').split('\t'))
fields = {}
for n, ln in enumerate(io.open(os.path.join(B4, 'fields.tsv'), encoding='utf-8-sig')):
    c = ln.rstrip('\r\n').split('\t')
    if n:
        fields[c[0]] = c
print()
print('scan_dd hits vs fields "hit=XXXX":')
for r in rows:
    e = r[0]
    hits = V.scan_dd(img, int(e, 16))
    src = fields[e][4]
    import re
    m = re.search(r'hit=([0-9A-F]{8})', src)
    claim = int(m.group(1), 16) if m else None
    print('  %s hits=%s claim=%s in_hits=%s'
          % (e, ' '.join('%08X' % h for h in hits),
             ('%08X' % claim) if claim else None, claim in hits))
