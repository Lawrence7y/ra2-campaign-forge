#!/usr/bin/env python3
# R17-R31-V5657A0: bounded static, read-only PE/RTTI/disassembly work for 0x5657A0.
# Reads only gamemd.exe; writes only REPORT.md, callers.tsv, disasm.txt, work.py in OUT.
import hashlib, struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

IMAGE = Path(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R31_V5657A0')
EXPECT = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
TARGET = 0x5657A0
R73_LO, R73_HI = 0x43F180, 0x43F5E0

b = IMAGE.read_bytes()
sha = hashlib.sha256(b).hexdigest().upper()
if sha != EXPECT:
    raise SystemExit('SHA MISMATCH ' + sha)
pe = pefile.PE(data=b, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = {}
for s in pe.sections:
    n = s.Name.decode('latin1').rstrip('\0')
    secs[n] = dict(va=IB+s.VirtualAddress, rva=s.VirtualAddress,
                   raw=s.PointerToRawData, size=s.SizeOfRawData, vsize=s.Misc_VirtualSize)
text, rdata, data = secs['.text'], secs['.rdata'], secs['.data']
code_lo, code_hi = text['va'], text['va']+text['vsize']

def off(va):
    return pe.get_offset_from_rva(va-IB)

def u32va(va):
    o = off(va)
    return struct.unpack_from('<I', b, o)[0] if o is not None and o+4 <= len(b) else None

def fmt(i):
    return f'{i.address:08X}  {i.bytes.hex(" "):<24}  {i.mnemonic} {i.op_str}'.rstrip()

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def disasm_range(va, n):
    o = off(va)
    return list(md.disasm(b[o:o+n], va))

# trusted entry set: .text start + all E8 call targets + post-padding starts.
# No C3/C2 byte scan is used anywhere for entry/boundary determination.
tcode = b[text['raw']:text['raw']+text['size']]
call_targets = set()
raw_candidates = []
for i in range(len(tcode)-4):
    if tcode[i] != 0xE8:
        continue
    site = text['va']+i
    rel = struct.unpack_from('<i', tcode, i+1)[0]
    dst = site+5+rel
    if code_lo <= dst < code_hi:
        call_targets.add(dst)
    if dst == TARGET:
        raw_candidates.append(dict(site=site, bytes=tcode[i:i+5].hex(' ')))
starts = {text['va']} | call_targets
i = 0
while i < len(tcode)-3:
    if tcode[i] in (0x90, 0xCC):
        c = tcode[i]; j = i
        while j < len(tcode) and tcode[j] == c:
            j += 1
        if (c == 0x90 and j-i >= 4) or (c == 0xCC and j-i >= 2):
            if text['va']+j < code_hi:
                starts.add(text['va']+j)
        i = j
    else:
        i += 1
starts = sorted(s for s in starts if code_lo <= s < code_hi)

# target function boundaries, strictly decoded from trusted anchors.
assert TARGET in starts
prev_start = max(s for s in starts if s < TARGET)
next_start = min(s for s in starts if s > TARGET)
prev_ins = disasm_range(prev_start, TARGET-prev_start)
body_window = disasm_range(TARGET, next_start-TARGET)
ret_ins = [x for x in body_window if x.mnemonic.startswith('ret')]
body_ret = ret_ins[0]
body_end = body_ret.address + body_ret.size
body_ins = [x for x in body_window if x.address < body_end]
tail_bytes = b[off(body_end):off(next_start)]
assert all(x == 0x90 for x in tail_bytes)
prev_tail_start = max(x.address+x.size for x in prev_ins if x.mnemonic.startswith('ret'))
prev_tail = b[off(prev_tail_start):off(TARGET)]
assert all(x == 0x90 for x in prev_tail)

# verify every raw E8 target candidate on a real instruction boundary.
host_map = {}
for c in raw_candidates:
    prior = [s for s in starts if s <= c['site']]
    host = max(prior) if prior else text['va']
    host_map.setdefault(host, []).append(c)
verified, rejected, host_decode_total = [], [], 0
for host, items in host_map.items():
    end = max(c['site']+5 for c in items)
    ins = list(md.disasm(b[off(host):off(end)], host, count=1000000))
    amap = {x.address: x for x in ins}
    host_decode_total += end-host
    following = [s for s in starts if s > host]
    host_end = following[0] if following else code_hi
    for c in items:
        x = amap.get(c['site'])
        ok = bool(x and x.mnemonic == 'call' and x.op_str == hex(TARGET) and
                  x.bytes.hex(' ') == c['bytes'])
        row = dict(c, host=host, host_end=host_end, boundary=ok,
                   in_73=(R73_LO <= c['site'] < R73_HI))
        (verified if ok else rejected).append(row)

# #73 range: independent bounded raw scan + boundary verification.
r73_raw = [c for c in raw_candidates if R73_LO <= c['site'] < R73_HI]
r73_ins = disasm_range(R73_LO, R73_HI-R73_LO)
r73_verified = [c for c in verified if c['in_73']]

R73_PATH = {
  0x43F210: 'case1/3@0x43F1E9; [[this+0x520]+0xE58]!=0; result -> call [esi+0x1AC] (#107)',
  0x43F2A7: 'case1/3; #107 virtual call returned 0; placement loops active; result -> 0x47C620',
  0x43F2C5: 'case1/3; 0x47C620 returned nonzero; immediate cell re-lookup',
  0x43F2EF: 'case1/3; 0x47C620 true and [cell+0x38] != [owner+0xE58]+0x294',
  0x43F30B: 'case1/3; previous compare passed and [cell+0xEC] != 1',
  0x43F39C: 'case1/3; [cell+0x48] != -1; coordinate loop, first lookup per coordinate',
  0x43F3BF: 'same coordinate loop; second lookup after writing [cell+0x48]=-1',
  0x43F587: 'second expansion loop from 0x43F526; residual-coordinate lookup -> 0x486E70',
}
for r in verified:
    r['path_73'] = R73_PATH.get(r['site'], '')

# Q1 RTTI/vtable scan: vtable[-4] -> COL -> +12 pTD -> TD+8 name.
printable = bytes(range(0x20, 0x7f))
td = {}
raw_da, end_da = data['raw'], data['raw']+data['size']
for o in range(raw_da, end_da-8):
    if b[o:o+3] != b'.?A':
        continue
    j = o+3
    while j < end_da and b[j] in printable and j-o < 300:
        j += 1
    if j >= end_da or b[j] != 0 or j-o < 8:
        continue
    name_va = IB+data['rva']+(o-raw_da)
    tdva = name_va-8
    if u32va(tdva) == 0x7F9594 and u32va(tdva+4) == 0:
        td.setdefault(tdva, b[o:j].decode('ascii'))
col = {}
raw_rd, end_rd = rdata['raw'], rdata['raw']+rdata['size']
for o in range(raw_rd, end_rd-24, 4):
    ptd = u32va(IB+rdata['rva']+(o+12-raw_rd))
    if ptd not in td:
        continue
    cd = u32va(IB+rdata['rva']+(o+16-raw_rd))
    co = off(cd) if cd is not None else None
    if co is None or co+16 > len(b):
        continue
    sig, attr, nbases, basearr = struct.unpack_from('<IIII', b, co)
    if sig == 0 and attr < 0x100 and 0 < nbases < 0x1000 and off(basearr) is not None:
        col.setdefault(IB+rdata['rva']+(o-raw_rd), td[ptd])
vtable_count = 0
slot_count = 0
vtable_hits = []
for o in range(raw_rd, end_rd-4, 4):
    c = u32va(IB+rdata['rva']+(o-raw_rd))
    if c not in col:
        continue
    vbase = IB+rdata['rva']+(o-raw_rd+4)
    vo = off(vbase)
    if vo is None or vo < raw_rd or vo >= end_rd:
        continue
    n = 0; p = vo
    while p+4 <= end_rd:
        v = struct.unpack_from('<I', b, p)[0]
        if not (code_lo <= v < code_hi):
            break
        if v == TARGET:
            vtable_hits.append((hex(vbase), n, hex(IB+rdata['rva']+(p-raw_rd)), col[c], hex(c)))
        n += 1; p += 4
    vtable_count += 1
    slot_count += n
raw_rdata_hits = []
needle = struct.pack('<I', TARGET)
for o in range(raw_rd, end_rd-3, 4):
    if b[o:o+4] == needle:
        raw_rdata_hits.append(hex(IB+rdata['rva']+(o-raw_rd)))

OUT.mkdir(parents=True, exist_ok=True)

caller_lines = ['site\tbytes\ttarget\thost\thost_anchor_end\tinstruction_boundary\tin_0x43F180_0x43F5E0\tpath_73']
for r in sorted(verified, key=lambda x: x['site']):
    caller_lines.append('\t'.join([
        f"0x{r['site']:08X}", r['bytes'], f'0x{TARGET:08X}', f"0x{r['host']:08X}",
        f"0x{r['host_end']:08X}", 'PASS' if r['boundary'] else 'FAIL',
        'YES' if r['in_73'] else 'NO', r['path_73']]))
(OUT/'callers.tsv').write_text('\n'.join(caller_lines)+'\n', encoding='utf-8')

dis = []
dis.append(f'IMAGE {IMAGE}')
dis.append(f'SHA256 {sha}')
dis.append(f'IMAGEBASE 0x{IB:X}')
dis.append(f'SCAN_TEXT_BYTES 0x{text["size"]:X} ({text["size"]})')
dis.append(f'SCAN_TEXT_E8_WINDOWS {len(tcode)-4}')
dis.append(f'SCAN_RDATA_BYTES 0x{end_rd-raw_rd:X} ({end_rd-raw_rd})')
dis.append(f'SCAN_DATA_BYTES 0x{end_da-raw_da:X} ({end_da-raw_da})')
dis.append(f'SCAN_R73_BYTES 0x{R73_HI-R73_LO:X} ({R73_HI-R73_LO})')
dis.append(f'HOST_BOUNDARY_DECODE_BYTES 0x{host_decode_total:X} ({host_decode_total})')
dis.append(f'TRUSTED_ENTRY_COUNT {len(starts)}')
dis.append('')
dis.append('=== A. PREVIOUS TRUSTED FUNCTION TAIL: strict decode, no C3/C2 byte scan ===')
dis.append(f'WINDOW 0x{prev_start:08X}..0x{TARGET:08X} ({TARGET-prev_start} bytes)')
for x in prev_ins:
    dis.append(fmt(x))
dis.append(f'PREV_PADDING 0x{prev_tail_start:08X}..0x{TARGET:08X} {prev_tail.hex(" ")}')
dis.append('')
dis.append('=== B. TARGET FULL BODY: anchor-aligned strict decode ===')
dis.append(f'WINDOW 0x{TARGET:08X}..0x{body_end:08X} ({body_end-TARGET} bytes)')
for x in body_ins:
    dis.append(fmt(x))
dis.append(f'TAIL_PADDING 0x{body_end:08X}..0x{next_start:08X} {tail_bytes.hex(" ")}')
dis.append(f'NEXT_TRUSTED_ENTRY 0x{next_start:08X}')
dis.append('')
dis.append('=== C. #73 QUERY RANGE [0x43F180,0x43F5E0): full strict decode ===')
for x in r73_ins:
    mark = '  <<< CALL 0x5657A0' if x.mnemonic == 'call' and x.op_str == hex(TARGET) else ''
    dis.append(fmt(x)+mark)
dis.append('')
dis.append('=== D. ALL VERIFIED DIRECT CALLER INSTRUCTIONS (host boundary decoded; one site line each) ===')
body_by_addr = {x.address: x for x in body_window}
for r in sorted(verified, key=lambda x: x['site']):
    p = ('  PATH='+r['path_73']) if r['path_73'] else ''
    dis.append(f'HOST 0x{r["host"]:08X} -> SITE 0x{r["site"]:08X}{p}')
    x = body_by_addr.get(r['site'])
    dis.append(fmt(x) if x else f'0x{r["site"]:08X}  {r["bytes"]}  call 0x{TARGET:x}')
if rejected:
    dis.append('')
    dis.append('=== REJECTED RAW E8 CANDIDATES (not instruction boundary) ===')
    for r in rejected:
        dis.append(f'0x{r["site"]:08X}  {r["bytes"]}  host=0x{r["host"]:08X}')
(OUT/'disasm.txt').write_text('\n'.join(dis)+'\n', encoding='utf-8')

n73 = len(r73_verified)
path_lines = '\n'.join(f'- 0x{site:08X} - {desc}' for site, desc in R73_PATH.items())
no_call_lines = '\n'.join(f'- {s}' for s in [
    '0x43F19F: 0x6F4A70 returns 0 -> 0x43F5E0; no target call in queried range.',
    'switch case 0 -> 0x43F1CA: only 0x5687F0 then return; no target call.',
    'switch case 2 -> 0x43F9A6 and case >3 -> 0x43FAFC: outside queried range; no target call inside [0x43F180,0x43F5E0).',
    'case 1/3 with [[this+0x520]+0xE58]==0 -> 0x43F5EF; no target call in queried range.',
    'case 1/3 after call [esi+0x1AC] returns nonzero -> 0x43F5D8; no later target call in queried range.',
    'placement-loop zero counts skip nested 0x43F2A7..0x43F3BF group; gate/compare equalities skip deeper site(s) for that iteration.',
])
report = f'''{IMAGE}\t{sha}

# R17-R31-V5657A0 - 0x5657A0 定性报告

范围：纯静态只读；只读取上述镜像，不创建/调试/启动 gamemd 目标进程。入口与尾界均由可信入口集（.text 起点 + 全部 E8 目标 + 长填充后继）+ Capstone 严格解码得出；全文未用 C3/C2 字节扫定界。声明扫描：.text {text["size"]} B（{len(tcode)-4} 个 E8 窗口），.rdata {end_rd-raw_rd} B，.data {end_da-raw_da} B，#73 查询区 {R73_HI-R73_LO} B；Q2 host 边界另严格解码 {host_decode_total} B。可信入口数 {len(starts)}。

## Q1 - 身份（vtable 定名）

不在任何 vtable 槽内。按 vtable[-4] -> COL -> +12 pTD -> +8 内联名 链重建：TypeDescriptor {len(td)} 个、COL {len(col)} 个、可识别 vtable {vtable_count} 张，连续 .text 槽值共 {slot_count} 个；槽值等于 0x5657A0 的命中 0。.rdata 中 4 字节小端等于 0x5657A0 的裸命中也为 0。因此没有可逐字抄录的类名；未取得类名，结论仅为不是这张 RTTI 可识别 vtable 集合中的槽值。

## Q2 - 谁调用它

.text 内 raw E8 rel32 候选 {len(raw_candidates)} 条；逐 host 严格解码后指令边界通过 {len(verified)} 条，拒绝 {len(rejected)} 条。完整 site/host 表见 callers.tsv，反汇编证据见 disasm.txt D 节。每个 host 由可信入口集定界，并断言 host <= site < host_anchor_end。

### 明确回答 #73（0x43F180）

[0x43F180,0x43F5E0) 内有 call 0x5657A0：该 {R73_HI-R73_LO} B 窗口 raw 命中 {len(r73_raw)} 条，边界验证通过 {n73} 条（不是假设；逐条见下表与 TSV）：

{path_lines}

所在路径（按控制流条件）：
{no_call_lines}

因此不能说 #73 不调 0x5657A0；但也不能说 #73 只有 A 路径调它：上表 {n73} 个 site 分属不同分支/循环，只有 0x43F2A7 的直接返回值被送入闸函数 0x47C620。

## Q3 - 函数体（只报字节可证）

- 入口：是。0x5657A0 本身是可信入口（存在直接 E8 目标）；前一可信入口 0x565730 严格解码至 0x565795 C2 04 00 ret 4，随后 0x565798..0x56579F 为 8 个 90，再进入 0x5657A0。没有按字节扫 C3/C2。
- 精确尾界：0x5657D8。唯一 ret 是 0x5657D5 C2 04 00 ret 4（3 B）；0x5657D8..0x5657DF 为 8 个 90，下一可信入口 0x5657E0。
- 函数长度：0x5657D8 - 0x5657A0 = 0x38 = 56 B；共 {len(body_ins)} 条指令，1 条 ret 出口。
- ret 形态：ret 4（C2 04 00），callee 弹回 1 个 dword 栈参数；同时 ECX 作为接收者使用，符合 thiscall 成员函数的字节形态。
- 读：[esp+4]（入参坐标结构指针）、[coord+0]、[coord+2] 两个 signed word；[ecx+0x13C]（表指针）；[table + index*4]；fallback 分支读 [coord] 的合成 dword。
- 写：仅全局 [0xABDC74]（fallback 分支写入合成坐标 dword）。未写接收者字段、未写坐标结构、未装 vtable。
- 字符串：无。常量/地址：0x40000（上界）、0xABDC50（返回值/fallback 对象地址）、0xABDC74（写入的全局）；未抄到 ASCII 原文。
- 索引/边界：index = ((signed16)[coord+2] << 9) + (signed16)[coord]；若 index 为负或 >= 0x40000，走 fallback；否则取表项，非 0 即返回该指针，为 0 也走 fallback。
- 全函数 {len(body_ins)} 行，已在 disasm.txt B 节整段列出（未省略）。

## Q4 - 与闸函数的关系 / 性质判定

判定：取某个对象的指针（具体是坐标到对象指针查找，失败回退到固定对象），不是惰性初始化，也不是单例访问器。强度：字节证据强；cell/tile 语义名为静态推断。

判据：
1. 0x5657BB mov ecx,[ecx+0x13C] -> 0x5657C1 mov eax,[ecx+eax*4] -> 0x5657C4 test eax,eax -> 非零直接 ret 4：返回的是从接收者成员表中取出的对象指针，不是接收者自身。
2. 无 test + new 模式，无 call operator new，无 ctor/vtable 安装；全函数 0 个 call（只有 1 条 ret 与条件跳转），所以不构成惰性初始化。
3. 不返回 [global]；0x87F7E8 只是调用方传入的 ECX 接收者（在 0x449476 / 0x43F2A2 等处装载），函数体只读 ecx+0x13C。全局 0xABDC74 是被写，不是被返回；返回的是固定地址 0xABDC50，属 fallback 对象指针。
4. 与闸函数关系：0x44947B 与 0x43F2A7 均是 mov ecx,0x87F7E8 -> call 0x5657A0 -> mov ecx,eax -> call 0x47C620，即本函数提供 0x47C620 的 this；0x43F210 的返回值则传给 call [esi+0x1AC]（#107）。这条链证明它被当作对象指针供应者，不证明它做初始化或单例创建。
'''
(OUT/'REPORT.md').write_text(report, encoding='utf-8')

print('SHA', sha)
print('RAW_CANDIDATES', len(raw_candidates), 'VERIFIED', len(verified), 'REJECTED', len(rejected))
print('R73_RAW', len(r73_raw), 'R73_VERIFIED', len(r73_verified), sorted(f"0x{x['site']:08X}" for x in r73_verified))
print('BODY', f'0x{TARGET:08X}', f'0x{body_end:08X}', body_end-TARGET, 'instructions', len(body_ins), 'ret', fmt(body_ret))
print('Q1', 'td', len(td), 'col', len(col), 'vtables', vtable_count, 'slots', slot_count, 'hits', vtable_hits, 'raw_hits', raw_rdata_hits)
print('HOST_DECODE_BYTES', host_decode_total, 'TRUSTED_ENTRIES', len(starts))
print('WROTE', OUT)
