# -*- coding: utf-8 -*-
"""只读交叉核：对 atlas 未覆盖的装表点，用「call 目标集合」反推函数起点，
再判它是否 atexit 注册的全局析构器 / 删除析构器（补全 ㉓ 写点枚举的定性）。"""
import sys

sys.dont_write_bytecode = True
HERE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_F1_B5'
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8')
import verify as V
import capstone
import bisect

img = V.Img(V.EXE)
ts = V.TextScan(img)
atlas = V.load_atlas()

# 收集全部 call rel32 目标（函数起点的高置信代理）
targets = set()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True
X = capstone.x86
for ins in md.disasm(ts.code, ts.lo):
    if ins.id == 0 or ins.mnemonic != 'call':
        continue
    o = ins.operands[0]
    if o.type == X.X86_OP_IMM:
        t = o.imm & 0xFFFFFFFF
        if V.TEXT_LO <= t < V.TEXT_HI:
            targets.add(t)
tg = sorted(targets)
print('call targets in .text:', len(tg))


def guess_start(va):
    i = bisect.bisect_right(tg, va) - 1
    return tg[i] if i >= 0 else None


SITES = {
    '007F6BF4': ['0075ECAA', '0075ED37', '0075F6A4'],
    '007F6E70': ['007637E4', '007638C6'],
    '007F73B8': ['00771F57'],
}
for vt, sites in SITES.items():
    print('\n=== table %s ===' % vt)
    for s in sites:
        va = int(s, 16)
        f_atlas = V.which_body(
            sorted((int(k, 16), int(k, 16) + v) for k, v in atlas.items() if v), va)
        g = guess_start(va)
        info = {}
        if g is not None:
            end = V.body_extent(ts, img, g)
            info['guess_start'] = '%08X' % g
            info['reaches_site'] = (g <= va < end)
            info['end'] = '%08X' % end
            at = V.atexit_sites(ts, img, g)
            info['atexit'] = ['%08X' % p for p in at]
            p = V.func_profile(ts, img, g, end)
            info['del_dtor'] = p['del_dtor']
            info['base_ctor'] = '%08X' % p['base_ctor'] if p['base_ctor'] else None
        print('  site %s atlas_func=%s %s' % (
            s, ('%08X' % f_atlas) if f_atlas else None, info))
