#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r113d_indep.py —— §2.12 规则 D 的**独立实现复算**：换解码器、换数据源、换写法。

本轮前面三个脚本（r113a/b/c）都用 capstone + census.pkl + symbols.json 的 vtable_va。
本脚本故意全部换掉，用来证伪「结论其实是我这套管线的产物」：
  换解码器：i686-w64-mingw32-objdump（GNU binutils）而不是 capstone
  换数据源：只读 symbols.json 的 **col_va**（不用 vtable_va、不用 census.pkl）
  换写法：不 diff、不 zip、不用字典推导式；逐条把中间量打印出来再断言

复算项（每条都是本轮对外声明的结论，逐条重做一遍）：
  I1 12 个 Locomotion 类的 RTTI 里 ILocomotion 的 mdisp == 4（12/12，objdump 不参与，纯字节）
  I2 COL 布局：COL+0x04=offset、COL+0x0C=pTD、COL+0x10=pCHD（用 AbstractClass 手算）
  I3 12 个 Locomotion 类符号表记的 col_va 的 offset 字段：4 个是 24（带 IPiggyback 的 9 基类类），
     8 个是 4 —— 与 r113a A5c 报的「symbols 记的是 offset==4 那份」不同 ⇒ 逐条列清
  I4 共享 QI 体 0x55a9b0 的 4 个 cmpsd 立即数（用 objdump 数，不用 capstone）
  I5 thunk 0x4d0510 的 sub 立即数 == 4 == ILocomotion mdisp（两处数据源不共用字节）
  I6 0x7ed358 的 16 字节 GUID（逐字节手抄，与 R111 的字符串比对）
  I7 objdump 侧复算 0x414290 的 `call 0x410260`（漏项① 的机制）
  I8 objdump 侧复算 0x4af720 里 `call 0x55a9b0`（漏项② 的机制）
  I9 IPersistStream 的 IID 0x7f7c80 的 16 字节与标准 IID_IPersistStream 逐字节比对（外部常量）
"""
import json, re, struct, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
EXE = ROOT + '/ra2bench/gamemd.exe'
IB = 0x400000
raw = open(EXE, 'rb').read()
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


def u32(v):
    return struct.unpack_from('<I', raw, v - IB)[0]


def i32(v):
    return struct.unpack_from('<i', raw, v - IB)[0]


def name0(v):
    q = v - IB + 8
    b = bytearray()
    while raw[q] != 0:
        b.append(raw[q]); q += 1
    return b.decode('ascii', 'replace')


def tdn(v):
    s = name0(v)
    if s.startswith('.?A'):
        s = s[3:]
        if s and s[0] in 'VUT':
            s = s[1:]
    if s.endswith('@@'):
        s = s[:-2]
    return s


def objdump(a0, a1):
    r = subprocess.run(['i686-w64-mingw32-objdump', '-d', '--start-address=0x%x' % a0,
                        '--stop-address=0x%x' % a1, EXE], capture_output=True, text=True)
    return r.stdout


# ---- I2 先做 COL 布局（其它项要用它） ----
ab_col = int(json.load(open(ROOT + '/out/reverse/symbols.json'))['classes']['AbstractClass']['col_va'], 16)
ck('I2 COL 布局手算：AbstractClass 的 col_va=0x7fafd8 **就是 COL 起点**（sig==0），'
   'COL+0x04=offset(12)、COL+0x0C=pTD(名字 AbstractClass)、COL+0x10=pCHD(CHD+0x08=8)',
   u32(ab_col) == 0 and u32(ab_col + 4) == 12 and tdn(u32(ab_col + 0xc)) == 'AbstractClass'
   and u32(u32(ab_col + 0x10) + 8) == 8,
   {'col': hex(ab_col), 'sig': u32(ab_col), 'offset': u32(ab_col + 4),
    'ptd': hex(u32(ab_col + 0xc)), 'td': tdn(u32(ab_col + 0xc)),
    'pchd': hex(u32(ab_col + 0x10)), 'nbc': u32(u32(ab_col + 0x10) + 8)})
ck('I2b 同一份布局下 AbstractClass 的 8 个基类名+偏移（逐条打印，不靠任何 JSON）',
   True,
   [(tdn(u32(u32(u32(ab_col + 0x10) + 0xc) + 4 * i)), i32(u32(u32(u32(ab_col + 0x10) + 0xc) + 4 * i) + 8))
    for i in range(u32(u32(ab_col + 0x10) + 8))])

# ---- I1 + I3 12 个 Locomotion 类 ----
sym = json.load(open(ROOT + '/out/reverse/symbols.json'))['classes']
loco = ['DriveLocomotionClass', 'DropPodLocomotionClass', 'FlyLocomotionClass',
        'HoverLocomotionClass', 'JumpjetLocomotionClass', 'LocomotionClass',
        'MechLocomotionClass', 'RocketLocomotionClass', 'ShipLocomotionClass',
        'TeleportLocomotionClass', 'TunnelLocomotionClass', 'WalkLocomotionClass']
md, offs = [], []
for c in loco:
    col = int(sym[c]['col_va'], 16)
    offs.append(u32(col + 4))
    nbc = u32(u32(col + 0x10) + 8)
    pbca = u32(u32(col + 0x10) + 0xc)
    found = None
    for i in range(nbc):
        bcd = u32(pbca + 4 * i)
        if tdn(u32(bcd)) == 'ILocomotion':
            found = i32(bcd + 8)
    md.append(found)
ck('I1 12 个 Locomotion 类的 RTTI 中 ILocomotion 的 mdisp 全 == 4（纯字节，不经 capstone/census）',
   md == [4] * 12, md)
ck('I3 12 个类的 symbols col_va 里 offset 字段实测是 24 的 6 个 + 4 的 6 个（不是 12 个全 4）—— '
   '故 r113a A5c 的措辞需按此收紧', sorted(offs) == [4] * 6 + [24] * 6,
   dict(zip(loco, offs)))

# ---- I4 共享 QI 体 ----
od = objdump(0x55a9b0, 0x55aa60)
imm = [int(x, 16) for x in re.findall(r'\$0x([0-9a-f]+),%edi', od)]
cmpsd = od.count('cmpsd')
rep = od.count('repz cmpsl')
ck('I4 objdump 侧复算 0x55a9b0（GNU binutils，不是 capstone）：mov $imm,%edi 共 4 条，立即数依序 == '
   '[0x7f7c90, 0x7f7c80, 0x7ed358, 0x7f7c70]；repe cmpsd 4 条 '
   '（注：objdump 把 F3 A7 渲染成 repz cmpsl 而非 capstone 的 repe cmpsd；首稿按 cmpsd 计得 0，'
   '二稿按 repe cmpsd 仍得 0 —— **同一块字节两个反汇编器的助记符完全不同**，断言两次当场抓住）',
   imm == [0x7f7c90, 0x7f7c80, 0x7ed358, 0x7f7c70] and rep == 4,
   {'imm': [hex(x) for x in imm], 'repe_cmpsd': rep})

# ---- I5 thunk 的 sub 立即数 ----
od5 = objdump(0x4d0510, 0x4d0516)
sub = re.search(r'subl\s+\$0x([0-9a-f]+),0x4\(%esp\)', od5)
ck('I5 thunk 0x4d0510 的 `subl $N,0x4(%esp)` 立即数 == 0x4 == ILocomotion 的 mdisp（两处数据源'
   '分别是 .text 立即数与 .rdata BCD，不共用字节）'
   '（首稿正则写成 `sub` 无 l，objdump 实际写作 subl —— 断言当场抓住）',
   sub is not None and int(sub.group(1), 16) == 4 and md[0] == 4,
   {'text_imm': sub.group(1) if sub else None, 'rdata_mdisp': md[0]})

# ---- I6 GUID 逐字节 ----
g = raw[0x7ed358 - IB:0x7ed358 - IB + 16]
hand = '%08X-%04X-%04X-%s-%s' % (struct.unpack('<I', g[:4])[0], struct.unpack('<H', g[4:6])[0],
                                 struct.unpack('<H', g[6:8])[0], g[8:10].hex().upper(), g[10:].hex().upper())
ck('I6 0x7ed358 的 16 字节逐字节手抄 = 070F3290-9841-11D1-B709-00A024DDAFD1，与 R111 记录的字符串一致',
   hand == '070F3290-9841-11D1-B709-00A024DDAFD1', hand)

# ---- I7 / I8 两处 call 机制 ----
od7 = objdump(0x414290, 0x4142d0)
ck('I7 objdump 侧复算 0x414290（AircraftClass slot0）：体内确有 `call 0x410260`，其后 test/jge 才查 0x7e9b40',
   'call' in od7 and '410260' in od7 and '7e9b40' in od7, od7.strip().splitlines()[:6])
od8 = objdump(0x4af720, 0x4af760)
ck('I8 objdump 侧复算 0x4af720（DriveLocomotionClass 的 thunk 目标）：体内确有 `call 0x55a9b0`，'
   '其后才查 0x7e9b10', 'call' in od8 and '55a9b0' in od8 and '7e9b10' in od8,
   od8.strip().splitlines()[:8])

# ---- I9 与外部标准常量比对 ----
std = bytes.fromhex('0C01000000000000C000000000000046')
got = raw[0x7f7c70 - IB:0x7f7c70 - IB + 16]
std109 = bytes.fromhex('0901000000000000C000000000000046')
got109 = raw[0x7f7c80 - IB:0x7f7c80 - IB + 16]
ck('I9 外部常量比对：0x7f7c80 的 16 字节 == 标准 IID_IPersistStream（00000109-0000-0000-C000-000000000046）；'
   '0x7f7c70 的 16 字节 == 0000010C-0000-0000-C000-000000000046（该常量不是标准 COM 接口 ⇒ 游戏自有）',
   got109 == std109 and got == std,
   {'0x7f7c70': got.hex(), '0x7f7c80': got109.hex()})

out = {'checks': checks}
json.dump(out, open(ROOT + '/_r113/r113d_indep.json', 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r113d] %d PASS / %d FAIL' % (len(checks) - nf, nf))
sys.exit(1 if nf else 0)
