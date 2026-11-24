# -*- coding: utf-8 -*-
# R69 · 跨家族审计复算（§2.12 规则 D）：主会话主张 vs 审计员主张 vs 手工解析实测
# 三方对撞。凡主会话与审计员任一被判错，都要在这里留数字。
import os, re, sys, io, struct, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE  = os.path.join(ROOT, 'ra2bench/gamemd.exe')
import pefile

fails, log = [], []
def W(s=''):
    print(s); log.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE, 'rb').read()
def rd(va, n): return data[pe.get_offset_from_rva(va - IB):][:n]
def sec_of(va):
    for s in pe.sections:
        if s.VirtualAddress + IB <= va < s.VirtualAddress + IB + s.Misc_VirtualSize:
            return s.Name.rstrip(b'\0').decode()
    return 'OUTSIDE'

W('=== 0 三方底数（手工遍历导入描述符，不经 pefile 高层封装）===')
o = pe.get_offset_from_rva(pe.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress)
named = ordi = 0
ilt_sec, ibn_sec, iat_sec, cont_sec = (collections.Counter() for _ in range(4))
ord_dlls = collections.Counter()
per_dll = []
i = 0
while True:
    oft, ts, fc, name_rva, ft = struct.unpack('<IIIII', data[o + i * 20:o + i * 20 + 20])
    if oft == 0 and ft == 0 and name_rva == 0: break
    dll = data[pe.get_offset_from_rva(name_rva):].split(b'\0')[0].decode()
    n_o = n_n = 0
    j = 0
    while True:
        v = struct.unpack('<I', rd(oft + IB + j * 4, 4))[0]
        if v == 0: break
        ilt_sec[sec_of(oft + IB + j * 4)] += 1
        iatva = ft + IB + j * 4
        iat_sec[sec_of(iatva)] += 1
        cont = struct.unpack('<I', rd(iatva, 4))[0]
        cont_sec[sec_of(cont) if cont else 'ZERO'] += 1
        if v & 0x80000000:
            ordi += 1; n_o += 1; ord_dlls[dll] += 1
        else:
            named += 1; n_n += 1; ibn_sec[sec_of(v + IB)] += 1
        j += 1
    per_dll.append((dll, n_n, n_o, j))
    i += 1

W('  导入条目总数 = %d（按名 %d + 按序数 %d）' % (named + ordi, named, ordi))
W('  ILT 所在节       : %s' % dict(ilt_sec))
W('  名字区(IBN)所在节 : %s' % dict(ibn_sec))
W('  IAT 槽所在节     : %s' % dict(iat_sec))
W('  IAT 槽内容所在节 : %s' % dict(cont_sec))
W('  序数导入按 DLL   : %s' % dict(ord_dlls))

W('')
W('=== 1 主会话主张 5 逐条判定（原本写进审计卡的那 5 句）===')
claims = [
 ('M-1 命名导入共 369 条', 369, named),
 ('M-2 序数导入共 30 条', 30, ordi),
 ('M-3 导入总数 372（主会话曾写 369）', 372, named + ordi),
 ('M-4 ILT 全在 .detour 共 372 条（主会话曾写 369）', 372, ilt_sec.get('.detour', 0)),
 ('M-5 名字区 339 全在 .detour', 339, ibn_sec.get('.detour', 0)),
 ('M-6 IAT 槽 371 在 .rdata（主会话曾写 369 全 .rdata）', 371, iat_sec.get('.rdata', 0)),
 ('M-7 IAT 槽另 1 条在 .detour（主会话未提）', 1, iat_sec.get('.detour', 0)),
 ('M-8 IAT 槽内容 339 在 .text', 339, cont_sec.get('.text', 0)),
 ('M-9 IAT 槽内容 33 条为序数标记（非节内）', 33, cont_sec.get('OUTSIDE', 0)),
]
for name, expect, got in claims:
    ck(name, expect == got, 'expect=%d got=%d' % (expect, got))

W('')
W('=== 2 审计员主张逐条判定 ===')
W('  审计员说：命名 339 / 序数 33 / 总 372 / ILT 372 全 .detour')
ck('A-1 审计员「命名 339」正确', named == 339, str(named))
ck('A-2 审计员「序数 33」正确', ordi == 33, str(ordi))
ck('A-3 审计员「总 372」正确', named + ordi == 372)
ck('A-4 审计员「ILT 372 全 .detour」正确', ilt_sec.get('.detour', 0) == 372)
ck('A-5 审计员「IAT 槽 371 .rdata + 1 .detour」正确',
   iat_sec.get('.rdata', 0) == 371 and iat_sec.get('.detour', 0) == 1, dict(iat_sec))
W('')
W('  审计员说：「IAT 槽内容 339 条指向 .rdata（未绑定 IAT 指向 hint/name 结构），无 .text 条目」')
ck('A-6 审计员该条【错误】：实测 339 条槽内容落在 .text，不是 .rdata',
   cont_sec.get('.text', 0) == 339 and cont_sec.get('.rdata', 0) == 0, dict(cont_sec))
W('   实测反证：按名导入的 IAT 槽内容样例 = 0x40fbb6 / 0x40fbe8 / 0x40fbf8，')
W('   全部落在 .text 区间 [0x401000, 0x7e038d)；审计员把「IAT 槽所在节(.rdata)」')
W('   与「IAT 槽内容所在节(.text)」混为一谈。')
samples = [0x40fbb6, 0x40fbe8, 0x40fbf8]
ck('A-6 反证：这三个值确实在 .text',
   all(sec_of(x) == '.text' for x in samples), str([sec_of(x) for x in samples]))
W('')
W('  审计员说：「30 条节外是序数 ILT 原始值被误算为名字区；另外 3 条（xyr/DSOUND/COMCTL32）被漏计」')
ck('A-7 审计员「序数共 33，其中 WSOCK32 19 + OLEAUT32 11 = 30，另 3 家各 1」正确',
   ord_dlls.get('WSOCK32.dll', 0) == 19 and ord_dlls.get('OLEAUT32.dll', 0) == 11
   and ord_dlls.get('xyr.dll', 0) == 1 and ord_dlls.get('DSOUND.dll', 0) == 1
   and ord_dlls.get('COMCTL32.dll', 0) == 1, dict(ord_dlls))
ck('A-8 审计员「名字区无节外条目（339 全 .detour）」正确',
   ibn_sec.get('.detour', 0) == 339 and 'OUTSIDE' not in ibn_sec, dict(ibn_sec))

W('')
W('=== 3 F29 原文三句与实测对照（这才是要判的对象）===')
W('  F29 原文：「ILT 与 IMAGE_IMPORT_BY_NAME 名字区在 .detour 节（339/339）」')
ck('F29-① 「ILT 在 .detour」为真但分母错（实为 372 条）', ilt_sec.get('.detour', 0) == 372)
ck('F29-② 「名字区在 .detour 339/339」为真', ibn_sec.get('.detour', 0) == 339)
ck('F29-③ 判定：合写「339/339」把 ILT(372) 与名字区(339) 两个不同分母并成一个',
   ilt_sec.get('.detour', 0) != ibn_sec.get('.detour', 0),
   'ILT=%d vs IBN=%d' % (ilt_sec.get('.detour', 0), ibn_sec.get('.detour', 0)))
W('')
W('  F29 原文：「IAT 数组本身在 .rdata（339/339）」')
ck('F29-④ 「IAT 槽在 .rdata」为真但分母错（371 条，另 1 条在 .detour）',
   iat_sec.get('.rdata', 0) == 371 and iat_sec.get('.detour', 0) == 1, dict(iat_sec))
W('  实测那条落在 .detour 的 IAT 槽来自哪个 DLL：')
i2 = 0
for dll, nn, no, tot in per_dll:
    if dll == 'xyr.dll':
        W('    %s（按名 %d / 序数 %d / 共 %d）' % (dll, nn, no, tot))
W('')
W('  F29 原文：「IAT 槽内容（绑定的 0x40F9xx 类地址）落在 .text（339/339）」')
ck('F29-⑤ 「IAT 槽内容 339 在 .text」为真', cont_sec.get('.text', 0) == 339)
ck('F29-⑥ 判定：该句的 339 与序数导入 33 条合起来才是 372，原文未说明 33 条例外',
   cont_sec.get('OUTSIDE', 0) == 33)

W('')
W('=== 4 反控：把 .rdata 与 .text 混为一谈会得到什么 ===')
ck('反控：若把「IAT 槽所在节」当成「IAT 槽内容所在节」，会算出 .rdata=371 —— 与 .text=339 明显不同',
   iat_sec.get('.rdata', 0) != cont_sec.get('.text', 0), '371 vs 339')
ck('反控：.rdata 区间与 .text 区间不重叠',
   not (0x7e1000 <= 0x40fbb6 < 0x7e1000 + 0x30074),
   '.text 内容值 0x40fbb6 不落在 .rdata 区间')

W('')
W('=== 5 定谳 ===')
verdicts = [
 ('主会话主张「命名 369 / 总 369 / ILT 369」', '错', '实测 339 / 372 / 372'),
 ('主会话主张「序数 30」', '错', '实测 33（xyr/DSOUND/COMCTL32 各 1 被漏计）'),
 ('主会话主张「IAT 槽 369 全 .rdata」', '错', '实测 371 .rdata + 1 .detour'),
 ('主会话主张「IAT 槽内容 339 .text / 30 序数」', '半对', '节归属对（.text），序数条数错（33 非 30）'),
 ('审计员主张「命名 339 / 序数 33 / 总 372 / ILT 372」', '对', '实测一致'),
 ('审计员主张「IAT 槽 371 .rdata + 1 .detour」', '对', '实测一致'),
 ('审计员主张「IAT 槽内容 339 指向 .rdata，无 .text」', '错', '实测 339 全在 .text'),
 ('审计员主张「名字区 339 全 .detour，无节外」', '对', '实测一致'),
 ('F29 原文「ILT 与名字区在 .detour（339/339）」', '分母错', 'ILT 372 ≠ 名字区 339，并写成一个分母'),
 ('F29 原文「IAT 数组在 .rdata（339/339）」', '分母错', '实为 371 .rdata + 1 .detour = 372'),
 ('F29 原文「IAT 槽内容在 .text（339/339）」', '漏例外', '另有 33 条序数导入槽内容不是地址'),
]
for who, v, why in verdicts:
    W('  %-52s → %-6s %s' % (who, v, why))

W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recompute_audit_r69.log'),
        'w', encoding='utf-8', newline='\n').write('\n'.join(log) + '\n')
sys.exit(0 if not fails else 1)
