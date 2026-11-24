# -*- coding: utf-8 -*-
"""只读交叉核：把 4 个 atlas 未覆盖装表点前后的字节打出来，判它们的函数边界。"""
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
    print('\n--- site %s  前 24B / 指令 ---' % s)
    for ins in ts.insn_at(va - 24, 8):
        mark = '  <== SITE' if ins.address == va else ''
        print('   %08X  %-28s %s%s' % (ins.address,
                                       ins.bytes.hex(), ins.mnemonic + ' ' + ins.op_str, mark))
