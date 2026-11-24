from pathlib import Path
import hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

IMAGE = Path(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R30_SLOT107_BODY')
EXPECT = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'

data = IMAGE.read_bytes()
sha = hashlib.sha256(data).hexdigest().upper()
if sha != EXPECT:
    raise SystemExit('SHA mismatch: ' + sha)
pe = pefile.PE(data=data, fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def off(va):
    return pe.get_offset_from_rva(va - BASE)

def read(va, n):
    o = off(va)
    return data[o:o+n]

def insns(va, n):
    return list(md.disasm(read(va, n), va))

def fmt(i):
    return f'{i.address:08X}  {i.bytes.hex(" "):<24}  {i.mnemonic} {i.op_str}'.rstrip()

WINDOWS = [
    ('A. tail of previous function, padding, 0x449440 full body, tail padding, next entry', 0x4493FC, 0xCC),
    ('B. #73 direct call to 0x6F4A70 (contrast only)', 0x43F198, 0x08),
    ('C. #73 vtable slot +0x1AC call (slot #107) and adjacent bytes', 0x43F210, 0x10),
    ('D. #73 0x47C620 gate-call construction and call', 0x43F294, 0x21),
    ('E. direct callee entry 0x5657A0 (first 0x1B bytes only)', 0x5657A0, 0x1B),
    ('F. direct callee entry 0x47C620 (first 0x20 bytes only)', 0x47C620, 0x20),
]
decode_total = sum(n for _, _, n in WINDOWS)

dis_lines = []
dis_lines.append(f'IMAGE {IMAGE}')
dis_lines.append(f'SHA256 {sha}')
dis_lines.append(f'IMAGEBASE {BASE:#x}')
dis_lines.append(f'DECODE_TOTAL_BYTES 0x{decode_total:X} ({decode_total})')
for title, va, n in WINDOWS:
    dis_lines.append('')
    dis_lines.append('=== ' + title + ' ===')
    dis_lines.append(f'WINDOW {va:08X}+{n:02X}')
    for i in insns(va, n):
        dis_lines.append(fmt(i))
(OUT / 'disasm.txt').write_text('\n'.join(dis_lines) + '\n', encoding='utf-8')

call_rows = [
    ('0044947B', 'E8 20 C3 11 00', 'direct E8', '0x5657A0', 'receiver ecx=0x87F7E8; five stack argument slots; result goes to eax'),
    ('00449482', 'E8 99 31 03 00', 'direct E8', '0x47C620', 'ecx=eax from 0x5657A0; same gate-call construction as 0x43F2AE'),
    ('004494A3', 'FF 92 A8 00 00 00', 'indirect call [edx+0xA8]', 'not unique', 'edx=[eax]; eax=[this+0x520]; vtable slot +0xA8; target not unique'),
]
calls = ['address\tbytes\tkind\ttarget\tnotes'] + ['\t'.join(r) for r in call_rows]
(OUT / 'calls.tsv').write_text('\n'.join(calls) + '\n', encoding='utf-8')

report = f'''{IMAGE}\t{sha}

# R17-R30-SLOT107-BODY 报告

范围声明：纯静态只读；未创建/调试/启动 gamemd 目标进程。PE 哈希读取全文件 {len(data)} 字节；指令解码仅下列有界窗口，共 0x{decode_total:X} ({decode_total}) 字节：0x4493FC+0xCC、0x43F198+0x08、0x43F210+0x10、0x43F294+0x21、0x5657A0+0x1B、0x47C620+0x20。入口/边界按指令边界线性解码，未用 C3/C2 字节扫描。

## Q1 · 结构与边界

- 入口判定：是函数入口（强）。锚点链（指令边界）：前函数 0x4493FC..0x449403 以 00449403 C2 08 00 ret 8 结束；0x449406..0x44940F 为 10 个 90 nop；00449410 56 push esi 是前一函数入口；该函数在 0044943D C3 ret 结束，0x44943E..0x44943F 为 2 个 90 nop；随后 00449440 8B 44 24 04 mov eax,[esp+4] 才是本函数入口。所有边界来自 Capstone 指令边界，不是字节扫 C3/C2。
- 精确尾界：0x4494B5（最后一条指令之后的首字节）。最后一条指令为 004494B2 C2 14 00 ret 0x14，占 0x4494B2..0x4494B4。0x4494B5..0x4494BF 为 11 个 90 nop 填充；下一个函数入口为 004494C0 56 push esi。
- 函数长度：0x4494B5 - 0x449440 = 0x75 = 117 字节（不含尾部填充）。
- ret 出口：2 条。00449490 C2 14 00 ret 0x14；004494B2 C2 14 00 ret 0x14。
- 栈约定：两条出口均为 ret 0x14，即 callee-pop 5 个 dword 栈参数；同时 ECX 被当作 this（[ecx+0x520]、[ecx+0x74]、[ecx+0x21C]），符合 MSVC x86 thiscall 成员函数的字节形态。直接读取的入栈参数只有 arg0=[esp+4]；[esp+8..0x14] 未见函数体直接读取。
- 循环/跳表：无。两条条件跳转 00449459 je 0x449493、00449460 je 0x449493 都向前汇合；无向后跳转、无 jmp [table]、无间接跳表。

## Q2 · 全部调用与数据访问（字节可证）

### call 清单（共 3 条；详见 calls.tsv）

| 地址 | 字节 | 形态 | 目标 |
|---|---|---|---|
| 0x44947B | E8 20 C3 11 00 | 直接 E8 | 0x5657A0 |
| 0x449482 | E8 99 31 03 00 | 直接 E8 | 0x47C620 |
| 0x4494A3 | FF 92 A8 00 00 00 | 间接 call [edx+0xA8] | 目标不唯一；edx=[eax]，eax=[this+0x520]，即子对象 vtable 槽 +0xA8 |

### this / 参数读取

- ECX-as-this 读取：[ecx+0x520]（0x449447）、[ecx+0x74]（0x44945B）、[ecx+0x21C]（0x449462、0x449493）。
- 经 this+0x520 子对象读取：[obj+0x408]（0x449451）、[obj+0x67C]（0x449468）、[obj+0x0] 即 vtable 指针（0x449499）；间接 call 读取 [vtable+0xA8] 的函数指针（0x4494A3）。
- 参数读取：[esp+4] → arg0（0x449440），再读 [arg0+0x24]（0x449444）；该值被写回原 [esp+4] 槽（0x44944D），随后以 lea eax,[esp+0xC] 作为 0x5657A0 的坐标指针参数之一。入口其余 4 个 dword 参数槽未直接读取。
- 调用内部可能读写的字段不归因到本函数；以上仅列本函数体内字节可证的访问。

### 写

- 非栈显式写：无（0 条）。未见对 [ecx+...]、[this+...] 或其它全局/堆地址的 mov/store。未装 vtable、未改 this 字段、未写全局对象。
- 栈显式写：0x44944D mov [esp+4],edx（覆盖入参 arg0 槽）；0x44946E push ecx、0x44946F push eax、0x449474 push edx、0x449475 push eax、0x44949B push ecx、0x4494A0 push ecx。三条 call 自身的压返回地址属 ISA 隐式栈效果，不单列为数据写。

### 字符串 / 常量

- 无字符串字面量引用。
- 唯一静态地址常量：0x449476 mov ecx,0x87F7E8（字节 B9 E8 F7 87 00）；读得 dword [0x87F7E8] = 0x00310030，作为 0x5657A0 的 ECX receiver。另有返回变换常量 0xF9、7 和 ret 0x14；未抄到任何 ASCII 原文。

## Q3 · 与 0x43F180 (#73) 的关系

- 不存在互相互接 direct call。0x449440 全函数体内无 E8 指向 0x43F180，也无任何可证指向 0x43F180 的间接 call；反向则见下一条。
- 0x43F180 体内有对主 vtable +0x1AC 的虚调用：0043F218 FF 96 AC 01 00 00 call dword ptr [esi+0x1AC]；其上游 0043F1FD mov esi,[edi]、0043F216 mov ecx,edi（同一 BuildingClass this），入参来自紧邻的 call 0x5657A0 返回值。按钉死的 BuildingClass 主 vtable 映射，+0x1AC = #107 = 0x449440，故存在 #73 → #107 的 vtable-slot 调用路径（间接调用本质目标不唯一；若派生覆盖则另论）。反向 0x449440 → 0x43F180 未取得。结论：不是互相直接调用；仅单方向虚调用路径。
- 指定地址的直接 E8 检查：
  - 0x43F180：无
  - 0x47C620：有，00449482 E8 99 31 03 00 call 0x47C620
  - 0x47C3D0：无
  - 0x6F4A70：无（对照：0x43F198 有 E8 ... call 0x6F4A70，但那在 #73 体内）
- 与 0x43F2AE call 0x47C620 的同源同参核对：
  - 本函数：00449476 B9 E8 F7 87 00、0044947B E8 20 C3 11 00（call 0x5657A0）、00449480 8B C8、00449482 E8 99 31 03 00（call 0x47C620）。
  - #73：0043F2A2 B9 E8 F7 87 00、0043F2A7 E8 F4 64 12 00（call 0x5657A0）、0043F2AC 8B C8、0043F2AE E8 6D D3 03 00（call 0x47C620）。
  - 判读：同源成立——两处都是先以 ecx=0x87F7E8 调 0x5657A0，再把返回 eax 直接送入 ecx 调 0x47C620。参数形态同构——两处 0x5657A0 的 5 个参数槽均含 [this+0x21C]、子对象 [this+0x520]、子对象 [+0x67C] 及坐标指针；但坐标指针所指内容来源不同（本函数指回被覆盖的入参槽 [arg0+0x24]，#73 指其内部算出的局部坐标），所以不能表述为逐值完全同一。

## Q4 · 性质判定（带判据 / 强度）

- 构造器：否（强）。判据：体内无 mov [this], offset vtable 或等价 vtable 安装，也无任何非栈 this 字段写入；反而是读取 this+0x520/+0x74/+0x21C。
- 析构器：否（强）。判据：无删除签名（ret 0x14、5 个显式栈参数，不是典型 ~T() 形态），无 vtable 重装、无 operator delete 直接或间接可证调用。
- 派发函数：否（强）。判据：无循环、无跳表、无 jmp [table]；只有两个向前条件汇合与一次固定槽虚调用。
- 普通成员方法：是（强，字节证据）。判据：ECX-as-this 读取多个 this 字段，MSVC thiscall/callee-pop ret 0x14，无 this 写。
- 语义层：[静态推断 / 中强] 该函数像“占格/放置状态查询的结果映射 helper”：依子对象 +0x408 与 this+0x74 分流，一路经 0x5657A0 → 0x47C620，另一路走子对象 vtable +0xA8；末尾 neg/sbb/and 0xF9/add 7 把布尔结果映射为 0（真）/7（假）。该语义不作为事实。

## Q5 · 与 ②-b 的关系

本函数体内确有 0x47C620 调用（0x449482），所以“若体内不含 0x47C620 调用，则对两路径共用同一闸核不构成反例”的条件句未触发。即便如此，本卡不据此翻案或升格：②-b 已按 D-53(A) 以 [静态推断] 收口（R14_COMMON §2.9），定谳句与书面限制 a–e 不可拆。本报告只给字节与局部性质，不改变该定谳强度。
'''
(OUT / 'REPORT.md').write_text(report, encoding='utf-8')
print('WROTE', OUT)
print('SHA', sha)
print('DECODE_TOTAL', decode_total)
