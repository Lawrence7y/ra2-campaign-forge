# -*- coding: utf-8 -*-
# R69 · F29 / F49 字节级复核 + 导入布局复查（只读 PE，不运行 exe）
# 目标：判定 F29 statement 里两处措辞精度问题
#   ① 「.detour 节（VA=0x793000/raw=0x497000）」—— 0x793000 实为 VirtualAddress(RVA)
#   ② 「ILT 与名字区在 .detour（339/339）」—— 分母只覆盖按名导入，序数导入 33 条未计入
import os, re, sys, io, struct

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE  = os.path.join(ROOT, 'ra2bench/gamemd.exe')
import pefile

fails, log = [], []
def W(s=''):
    print(s); log.append(s)
def ck(n, c, d=''):
    W(('  PASS ' if c else '  FAIL ') + n + (('  ' + d) if d else ''))
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

W('=== 0 基线 ===')
W('  ImageBase = %#x' % IB)
for s in pe.sections:
    nm = s.Name.rstrip(b'\0').decode()
    W('  %-8s VirtualAddress=%#010x VA=%#010x PointerToRawData=%#010x'
      % (nm, s.VirtualAddress, s.VirtualAddress + IB, s.PointerToRawData))

W('')
W('=== 1 F29 主张①：.detour 节的「VA=0x793000」措辞 ===')
det = [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.detour']
ck('.detour 节存在且唯一', len(det) == 1, str(len(det)))
d = det[0]
W('  .detour VirtualAddress(节表字段) = %#x' % d.VirtualAddress)
W('  .detour PointerToRawData          = %#x' % d.PointerToRawData)
W('  .detour 绝对 VA = ImageBase + RVA = %#x' % (d.VirtualAddress + IB))
ck('正控：raw 字段 = 0x497000（F29 该半句为真）', d.PointerToRawData == 0x497000, hex(d.PointerToRawData))
ck('正控：节表字段 = 0x793000（F29 读的就是这个字段）', d.VirtualAddress == 0x793000, hex(d.VirtualAddress))
ck('判定：0x793000 是 RVA 而非 VA（VA 应为 0xB93000）',
   d.VirtualAddress != d.VirtualAddress + IB and (d.VirtualAddress + IB) == 0xB93000,
   'VA=%#x' % (d.VirtualAddress + IB))
ck('反控：若把它当 VA，则该「VA」不落在 .detour 自身区间内',
   not (d.VirtualAddress + IB <= d.VirtualAddress < d.VirtualAddress + IB + d.Misc_VirtualSize))

W('')
W('=== 2 F29 主张②：导入布局三件（339/339 的分母）===')
tot = byname = byord = 0
ilt_sec, ibn_sec, iat_sec, cont_sec = {}, {}, {}, {}
def bump(dic, k): dic[k] = dic.get(k, 0) + 1
ord_names = []
for e in pe.DIRECTORY_ENTRY_IMPORT:
    ilt = e.struct.OriginalFirstThunk
    for i, imp in enumerate(e.imports):
        tot += 1
        iltva = ilt + IB + i * 4
        bump(ilt_sec, sec_of(iltva))
        raw = struct.unpack('<I', rd(iltva, 4))[0]
        bump(iat_sec, sec_of(imp.address))
        cont = struct.unpack('<I', rd(imp.address, 4))[0]
        bump(cont_sec, sec_of(cont))
        if raw & 0x80000000:
            byord += 1
            ord_names.append((e.dll.decode(), raw & 0xFFFF,
                              imp.name.decode(errors='replace') if imp.name else None))
        else:
            byname += 1
            bump(ibn_sec, sec_of(raw + IB))

W('  导入条目总数 = %d（按名 %d + 按序数 %d）' % (tot, byname, byord))
W('  ILT 所在节      : %s' % ilt_sec)
W('  名字区(IBN)所在节: %s' % ibn_sec)
W('  IAT 槽所在节    : %s' % iat_sec)
W('  IAT 槽内容所在节: %s' % cont_sec)
W('')
W('  F29 原文三句的分母核对：')
ck('正控：「名字区 339 全在 .detour」为真（按名导入子集）',
   ibn_sec.get('.detour', 0) == 339 and byname == 339, str(ibn_sec.get('.detour')))
ck('正控：「IAT 槽内容 339 在 .text」为真（同一子集）',
   cont_sec.get('.text', 0) == 339, str(cont_sec.get('.text')))
ck('判定：「ILT 在 .detour 339/339」分母不足——ILT 实为 %d 条全在 .detour' % tot,
   ilt_sec.get('.detour', 0) == tot and tot != 339, '%d vs 339' % ilt_sec.get('.detour', 0))
ck('判定：339 只是「按名导入」子集，序数导入 %d 条被漏计' % byord,
   byord > 0 and byname + byord == tot, '%d+%d=%d' % (byname, byord, tot))
ck('反控：若 339 是全集则 byord 必为 0（事实相反，说明缺陷真实存在）', byord != 0)
W('')
W('  序数导入明细（%d 条）：' % byord)
from collections import Counter
W('    按 DLL: %s' % dict(Counter(x[0] for x in ord_names)))
W('    其中 pefile 仍给出名字的: %d 条（这些是「名字已知但 ILT 用序数寻址」）'
  % sum(1 for x in ord_names if x[2]))
for x in ord_names[:6]:
    W('      %-14s ord=%-4d name=%s' % (x[0], x[1], x[2]))

W('')
W('=== 3 F49 主张：「全文件另有 32 处 b8 imm32 c2 04 00 的 imm≠1」===')
text = [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text'][0]
blob = data[text.PointerToRawData:text.PointerToRawData + text.SizeOfRawData]
pat = re.compile(rb'\xb8(....)\xc2\x04\x00', re.S)
hits = [(text.VirtualAddress + IB + m.start(), struct.unpack('<I', m.group(1))[0])
        for m in pat.finditer(blob)]
eq1 = [h for h in hits if h[1] == 1]
neq = [h for h in hits if h[1] != 1]
W('  b8 imm32 c2 04 00 全文件 %d 处；imm==1 有 %d 处；imm!=1 有 %d 处'
  % (len(hits), len(eq1), len(neq)))
ck('正控：0x00410300 / 0x00410310 两处 imm==1 必须被找到',
   any(a == 0x410300 for a, _ in eq1) and any(a == 0x410310 for a, _ in eq1))
ck('判定：F49 的「32 处 imm≠1」实测复核', len(neq) == 32, '实测 %d' % len(neq))
ck('反控：把判据改成 imm==1 得到 40 处，与 32 不同（说明该计数有判别力）',
   len(eq1) != len(neq), '%d vs %d' % (len(eq1), len(neq)))

W('')
W('=== 4 桩字节被 .rdata 引用数（§13.3 的 74/74）===')
rd_sec = [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.rdata'][0]
rb = data[rd_sec.PointerToRawData:rd_sec.PointerToRawData + rd_sec.SizeOfRawData]
for tgt in (0x410300, 0x410310):
    tp = struct.pack('<I', tgt)
    n4 = sum(1 for i in range(0, len(rb) - 3, 4) if rb[i:i + 4] == tp)
    W('  %#x 在 .rdata 的 4 字节对齐引用数 = %d' % (tgt, n4))
    ck('§13.3 的 74 引用复核 %#x' % tgt, n4 == 74, str(n4))

W('')
W('RESULT ' + ('ALL-PASS' if not fails else 'FAIL: ' + ','.join(fails)))
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verify_f29_bytes_r69.log'),
        'w', encoding='utf-8', newline='\n').write('\n'.join(log) + '\n')
sys.exit(0 if not fails else 1)
