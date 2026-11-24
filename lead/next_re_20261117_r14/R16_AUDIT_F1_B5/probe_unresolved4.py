# -*- coding: utf-8 -*-
"""只读：把 3 个 atlas 漏覆盖写点所在函数的真实起点/签名解出来（从填充后的边界起反汇编）。"""
import sys

sys.dont_write_bytecode = True
HERE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_F1_B5'
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8')
import verify as V

img = V.Img(V.EXE)
ts = V.TextScan(img)

for s in ('0075ED37', '007637E4', '007638C6', '00771F57'):
    va = int(s, 16)
    # 若 va 前 8 字节内出现 ret 后跟 90/nop 填充，则函数起点在填充之后
    print('\n=== site %s ===' % s)
    for ins in ts.insn_at(va - 8, 4):
        print('   %08X %-24s %s %s' % (ins.address, ins.bytes.hex(),
                                       ins.mnemonic, ins.op_str))
    # 从该点向后反汇编，看能否把 site 纳进同一函数（以首个 ret 为界）
    start = None
    for cand in range(va - 7, va + 1):
        ins = ts.insn_at(cand, 1)
        if not ins:
            continue
        # 起点候选：紧接填充之后（前一条是 ret 或 int3/nop 填充）
        prev = ts.insn_at(cand - 1, 1)
        if prev and prev[0].mnemonic.startswith('ret'):
            start = cand
            break
    if start is None:
        # 退化：取 16 字节对齐边界
        start = (va & ~0xF)
    end = V.body_extent(ts, img, start)
    p = V.func_profile(ts, img, start, end)
    at = V.atexit_sites(ts, img, start)
    print('   => func_start=%08X end=%08X covers_site=%s atexit=%s del_dtor=%s '
          'base_ctor=%s base_dtor=%s' % (
              start, end, start <= va < end,
              ['%08X' % x[0] for x in at], p['del_dtor'],
              ('%08X' % p['base_ctor']) if p['base_ctor'] else None,
              ('%08X' % p['base_dtor']) if p['base_dtor'] else None))
