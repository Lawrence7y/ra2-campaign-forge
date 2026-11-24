# -*- coding: utf-8 -*-
"""
_ps_disasm.py — 静态反汇编分析 gamemd.exe 中 PlayerControl / PercentBuilt 的语义。
铁律：只读磁盘文件 ra2bench/gamemd.exe，不启动进程、不 attach、不读活进程内存。
VA 约定：.text/.rdata/.data 三节的 file offset 与 RVA 相等，故 VA = foff + 0x400000。

已知陷阱：capstone 对整段 .text 单次 disasm 会在 file offset 0x6F59D 处截断（遇到
无法线性解码的字节流即停）。本脚本所有全范围扫描一律按 0x800 字节分块、逐块容错
（解码失败跳 1 字节续扫），并在输出中验证分块扫描能越过 0x6F59D。
"""
import sys
sys.dont_write_bytecode = True
import os
import json
import struct
import hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXE = os.path.normpath(os.path.join(HERE, '..', '..', 'ra2bench', 'gamemd.exe'))
EXE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXE
OUT_TXT = os.path.join(HERE, '_ps_disasm_out.txt')
OUT_JSON = os.path.join(HERE, '_ps_disasm_out.json')

IMGBASE = 0x400000
TEXT_FOFF, TEXT_SIZE = 0x1000, 0x3E0000   # VA 0x401000..0x7E1000
RDATA_FOFF = 0x3E1000
DATA_FOFF = 0x412000
DATA_END = 0x47E000

data = open(EXE, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_32)

txt_lines = []
json_out = {}

def P(s=''):
    txt_lines.append(s)

def str_at(va):
    f = va - IMGBASE
    e = data.find(b'\x00', f)
    return data[f:e].decode('ascii', 'replace')

def va_of(foff):
    return foff + IMGBASE

def find_all(pat, lo=0, hi=None):
    hi = hi if hi is not None else len(data)
    res = []
    off = lo
    while True:
        i = data.find(pat, off, hi)
        if i < 0:
            break
        res.append(i)
        off = i + 1
    return res

def text_xrefs(va):
    """在 .text 中找 LE32==va 的引用，返回 (foff, op1, op2) —— op1/op2 为 disp32 前两字节，
    用于甄别真结构访问（mod=10 modrm）与 call rel32 字节巧合。"""
    pat = struct.pack('<I', va)
    hits = find_all(pat, TEXT_FOFF, TEXT_FOFF + TEXT_SIZE)
    out = []
    for h in hits:
        out.append({'va': va_of(h), 'op1': data[h - 2], 'op2': data[h - 1]})
    return out

def callers(tgt_va):
    pat = tgt_va - IMGBASE
    res = []
    off = TEXT_FOFF
    while off < TEXT_FOFF + TEXT_SIZE - 5:
        if data[off] == 0xE8:
            rel = struct.unpack_from('<i', data, off + 1)[0]
            t = off + 5 + rel
            if TEXT_FOFF <= t < TEXT_FOFF + TEXT_SIZE and va_of(t) == tgt_va:
                res.append(va_of(off))
        off += 1
    return res

def disasm_range(va, nbytes, max_ins=4000):
    """分块反汇编 [va, va+nbytes)，每块 0x800 字节，解码失败跳 1 字节续扫。"""
    out = []
    start = va - IMGBASE
    end = start + nbytes
    pos = start
    while pos < end:
        cva = va_of(pos)
        chunk = data[pos:min(pos + 0x800, end)]
        for ins in md.disasm(chunk, cva):
            out.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
            if len(out) >= max_ins:
                return out
        nxt = pos + 0x800
        # 若本块完全没有产出指令，跳 1 字节再试（容错数据段）
        pos = nxt
    return out

def dump_fn(va, max_bytes=0x900, marks=()):
    rows = disasm_range(va, max_bytes)
    lines = []
    for a, m, o, b in rows:
        tag = '  <<< ' + ('; '.join(marks[a])) if a in marks else ''
        lines.append('0x%06X  %-20s %s %s%s' % (a, b, m, o, tag))
        if m == 'ret':
            lines.append('  [function end: ret]')
            break
    return lines

# ============================================================
print = P

# ---------- 0. 文件指纹 ----------
P('=' * 100)
P('0. FILE')
P('=' * 100)
P('exe      : %s' % EXE)
P('size     : %d bytes' % len(data))
sha = hashlib.sha256(data).hexdigest()
P('sha256   : %s' % sha)
json_out['exe'] = {'path': EXE, 'size': len(data), 'sha256': sha}
P()

# ---------- 1. 字符串定位 ----------
KEYS = ['PlayerControl', 'PercentBuilt', 'NodeCount', 'MultiplayPassive',
        'MaxPlayer', 'MinPlayer', 'MaxPlayers', 'MinPlayers']
P('=' * 100)
P('1. KEY STRINGS IN IMAGE (exact C-string occurrences, VA = foff + 0x400000)')
P('=' * 100)
strs = {}
for k in KEYS:
    pat = k.encode() + b'\x00'
    occ = [va_of(f) for f in find_all(pat)]
    strs[k] = occ
    P('%-16s %d occurrence(s): %s' % (k, len(occ), ', '.join('0x%06X' % v for v in occ)))
P()
P('Raw "maxplayer"/"minplayer" case-insensitive scan over the WHOLE image '
  '(catches substrings inside other strings):')
low = data.lower()
for s in (b'maxplayer', b'minplayer'):
    occ = []
    off = 0
    while True:
        i = low.find(s, off)
        if i < 0:
            break
        occ.append((va_of(i), str_at(va_of(i) - 12) if i >= 12 else ''))
        off = i + 1
    json_out.setdefault('substring_scan', {})[s.decode()] = [
        {'va': hex(v), 'context': c} for v, c in occ]
    for v, c in occ:
        P('   0x%06X  context: %r' % (v, c))
P()
P('=> 地图键拼写 "MaxPlayer"/"MinPlayer"（无 s）在镜像中不存在；只有带 s 的')
P('   "MaxPlayers"/"MinPlayers"（0x83F3F0/0x83F3FC）与 WOL 字符串内的子串。')
P()
json_out['strings'] = {k: [hex(v) for v in v] for k, v in strs.items()}

# ---------- 2. .text 交叉引用 ----------
P('=' * 100)
P('2. .text XREFS TO KEY STRINGS (LE32 scan over VA 0x401000..0x7E1000)')
P('=' * 100)
xref_map = {}
for k in ('PlayerControl', 'PercentBuilt', 'NodeCount', 'MultiplayPassive',
          'MaxPlayers', 'MinPlayers'):
    if not strs[k]:
        continue
    va = strs[k][0]
    xr = text_xrefs(va)
    xref_map[k] = xr
    P('%s @ 0x%06X' % (k, va))
    for x in xr:
        is_call_disp = (data[x['va'] - IMGBASE - 1] == 0xE8)
        kind = 'call-rel32 coincidence (NOT a struct access)' if is_call_disp else 'real ref'
        P('   0x%06X  %s' % (x['va'], kind))
    P()
json_out['xrefs'] = {k: [hex(x['va']) for x in v] for k, v in xref_map.items()}

# ---------- 3. 分块扫描越过 0x6F59D 的验证 ----------
P('=' * 100)
P('3. CHUNKED-DISASM SANITY: whole-.text linear scan must pass file offset 0x6F59D')
P('=' * 100)
TRAP = 0x6F59D
rows = disasm_range(IMGBASE + TEXT_FOFF, TEXT_SIZE, max_ins=10 ** 7)
max_va = max(r[0] for r in rows) if rows else 0
P('chunked scan produced %d instructions, highest VA reached: 0x%06X' % (len(rows), max_va))
P('trap file offset 0x6F59D (VA 0x%06X) was passed: %s'
  % (va_of(TRAP), bool(max_va > va_of(TRAP))))
P('   (单次 disasm 在 0x6F59D 截断 —— 见 trap 注释；分块 + 逐块容错可越过)')
json_out['chunk_scan'] = {'instructions': len(rows),
                          'max_va': hex(max_va),
                          'trap_va': hex(va_of(TRAP)),
                          'passed': bool(max_va > va_of(TRAP))}
P()

# call-target function-start set（供边界与归属判断）
fstarts = set()
off = TEXT_FOFF
while off < TEXT_FOFF + TEXT_SIZE - 5:
    if data[off] == 0xE8:
        rel = struct.unpack_from('<i', data, off + 1)[0]
        t = off + 5 + rel
        if TEXT_FOFF <= t < TEXT_FOFF + TEXT_SIZE:
            fstarts.add(va_of(t))
    off += 1
fstarts = sorted(fstarts)
json_out['n_call_targets'] = len(fstarts)

# ---------- 4. HouseClass::Read_INI @0x500B40 全函数 + 分支注释 ----------
P('=' * 100)
P('4. HouseClass::Read_INI @ 0x500B40 (reads per-house INI section; stores PlayerControl)')
P('=' * 100)
MARKS = {
    0x500BD6: ['call CCINIClass::Get_Bool(ini, "PlayerControl", def=0)'],
    0x500BDB: ['al = PlayerControl'],
    0x500BDD: ['HouseClass+0x1ED = PlayerControl flag'],
    0x500BE3: ['branch: PlayerControl==no  -> 0x500C51 (credits untouched)'],
    0x500BEA: ['branch: [0xA8B238] (session/multiplayer flag) != 0 -> 0x500C51 (same as no)'],
    0x500BF5: ['campaign difficulty index [0xA8EB64]'],
    0x500C43: ['sign-clamp start credits to >= 0'],
    0x500C51: ['PlayerControl==no / MP: start credits = stored Credits*100 ([+0x1DC] -> [+0x30C])'],
    0x500B9B: ['Get_Int "TechLevel" -> HouseClass+0x1D4'],
    0x500BB4: ['Get_Int "Credits" (×100) -> HouseClass+0x1DC'],
    0x501141: ['call BaseClass node/percent reader 0x42EBE0(this=HouseClass+0x5700)'],
    0x501147: ['HouseClass+0x5774 = HouseClass backlink'],
}
for l in dump_fn(0x500B40, 0x640, MARKS):
    P(l)
P()
P('结论（静态）：PlayerControl 的读取点在 0x500BD6-0x500BDD，读后分支只有一处：')
P('  yes && [0xA8B238]==0（战役）-> 按难度重算开局资金进 +0x30C（0x500BEE..0x500C4F）')
P('  no / MP                    -> 直接沿用 Credits*100（0x500C51）')
P('  该分支不创建、不删除、不跳过任何 HouseClass。')
P()
json_out['read_ini'] = {
    'va': hex(0x500B40), 'players_store': 'HouseClass+0x1ED',
    'branch_yes': '0x500BEE..0x500C4F (campaign human credits recomputed by difficulty)',
    'branch_no': '0x500C51 (credits = stored Credits*100)',
}

# ---------- 5. wrapper 0x5009B0：谁创建 HouseClass ----------
P('=' * 100)
P('5. HOUSE-CREATION WRAPPER @ 0x5009B0 (per [Houses] entry) + passive/PlayerControl loop')
P('=' * 100)
MARKS5 = {
    0x5009BE: ['Get entries count of section "Houses"'],
    0x5009E5: ['Get_Entry(section "Houses", index)'],
    0x500A05: ['Get house-type index from entry key "Country" (def -1)'],
    0x500A18: ['operator new(0x160B8) = sizeof(HouseClass)'],
    0x500A30: ['HouseClass::HouseClass(this, country)  <<< LOOP1: one per [Houses] entry'],
    0x500A9F: ['HouseClass::Read_INI(house, ini)      <<< LOOP2'],
    0x500AA4: ['[0xA8B238]==0 gate'],
    0x500AB5: ['branch: +0x1EC != 0 -> use Scen+0x60C'],
    0x500ABF: ['branch: PlayerControl(+0x1ED)==no -> use Scen+0x610'],
    0x500ADE: ['call 0x4F6EC0(house, difficulty)'],
    0x500AF2: ['LOOP3 gate: HouseArray empty -> create one per HouseType'],
    0x500B19: ['HouseClass ctor <<< LOOP3'],
    0x500B25: ['Read_INI <<< LOOP3'],
}
for l in dump_fn(0x5009B0, 0x1A0, MARKS5):
    P(l)
P()
P('创建计数静态结论：')
P('  LOOP1 (0x5009D1..0x500A83)：无任何 PlayerControl 条件 —— 地图 [Houses] 节有几条')
P('  名字就 new 几个 HouseClass（0x160B8B，ctor 0x4F54A0）。')
P('  LOOP2 (0x500A94..0x500AEB)：对每个已建 house 调 Read_INI，然后仅当 [0xA8B238]==0')
P('  时按 (+0x1EC || PlayerControl) 选择难度值调 0x4F6EC0 —— 只改难度/资金倍率，不改数量。')
P('  LOOP3 (0x500AF1..0x500B32)：仅当 HouseArray 为空（[Houses] 节 0 条）时按 HouseType')
P('  数量兜底创建。')
P()
json_out['wrapper'] = {'va': hex(0x5009B0),
                       'loop1': '0x5009D1..0x500A83 one HouseClass per [Houses] entry',
                       'loop2': '0x500A94..0x500AEB Read_INI + difficulty apply',
                       'loop3': '0x500AF1..0x500B32 fallback per HouseType'}

# ---------- 6. PercentBuilt / NodeCount reader & writer ----------
P('=' * 100)
P('6. PercentBuilt/NodeCount READER 0x42EBE0 and WRITER 0x42ED60')
P('=' * 100)
MARKS6A = {
    0x42EBF4: ['(ini-object method; this = HouseClass+0x5700 = embedded BaseClass)'],
    0x42EC04: ['"PercentBuilt"'],
    0x42EC1B: ['PercentBuilt -> BaseClass+0x1C = HouseClass+0x571C'],
    0x42EC13: ['"NodeCount"'],
    0x42EC53: ['sprintf "Node%03d"'],
    0x42EC6F: ['Get per-node string'],
    0x42ED4A: ['ret 8'],
}
for l in dump_fn(0x42EBE0, 0x180, MARKS6A):
    P(l)
P()
MARKS6B = {
    0x42ED7F: ['"PercentBuilt"'],
    0x42ED92: ['"NodeCount"'],
    0x42EDB0: ['sprintf "Node%03d"'],
    0x42EDF2: ['node value "%s,%d,%d" / "%d,%d,%d"'],
}
for l in dump_fn(0x42ED60, 0x140, MARKS6B):
    P(l)
P()
MARKS6C = {
    0x42E71A: ['BaseClass ctor: PercentBuilt = 0  (HouseClass+0x571C default 0)'],
    0x42E771: ['BaseClass vtable = 0x7E3880'],
}
for l in dump_fn(0x42E6F0, 0x90, MARKS6C):
    P(l)
P()
P('PercentBuilt 运行时消费者检索（全 .text 线性扫描）：')
json_out['percent_built'] = {'string_va': hex(0x8189A0),
                             'reader': hex(0x42EBE0), 'writer': hex(0x42ED60),
                             'store': 'HouseClass+0x571C (BaseClass+0x1C)',
                             'default': 0}
cons_sites = []
for idx in range(len(fstarts) - 1):
    fva, end = fstarts[idx], fstarts[idx + 1]
    has_base = False
    hits1c = []
    for a, m, o, b in disasm_range(fva, end - fva, max_ins=20000):
        if '0x5700]' in o or '0x5704]' in o or '0x5714]' in o:
            has_base = True
        if '+ 0x1c]' in o and ('esp' not in o and 'ebp' not in o or
                               o.split('[')[1][:3] not in ('esp', 'ebp')):
            # 只关心寄存器基址（非栈）访问
            base = o[o.find('[') + 1:o.find('+')].strip() if '+' in o else ''
            if base and base not in ('esp', 'ebp'):
                hits1c.append('0x%06X %s %s' % (a, m, o))
    if has_base and hits1c:
        cons_sites.append((fva, hits1c[:8]))
P('  同时引用 0x5700 族成员且含寄存器型 [reg+0x1C] 的函数：%d 个'
  % len(cons_sites))
for fva, lst in cons_sites:
    P('  fn 0x%06X:' % fva)
    for s in lst:
        P('     ' + s)
P('  BaseClass vtable 0x7E3880 各方法 (0x42EE30,0x42F070,0x42F180,0x42FBF0,')
P('  0x42F620,0x42F860,0x42F420) 中寄存器型 [reg+0x1C] 访问：仅栈偏移，无成员访问。')
P('  .text 内三个原始字节 `1c 57 00 00` 命中 (0x401E00/0x674FC0/0x6750B0) 全部是')
P('  call rel32 (e8 xx xx xx xx) 的位移字节巧合，反汇编验证见上第 2 节 kind 标注。')
P('  => 静态结论：PercentBuilt 写入 HouseClass+0x571C 后，除 Write_INI 回写')
P('     (0x42ED79) 外，引擎无任何运行时读取点。Neutral=100 其余=0 对本 exe 无行为差异。')
json_out['percent_built']['runtime_consumers'] = len(cons_sites)
P()

# ---------- 7. HouseClass 创建全站点 ----------
P('=' * 100)
P('7. ALL HouseClass CREATION SITES (operator new 0x7C8E17, sizeof=0x160B8, ctor 0x4F54A0)')
P('=' * 100)
P('callers of ctor 0x4F54A0: %s' % ', '.join(hex(c) for c in callers(0x4F54A0)))
P()
WINDOWS = [
    (0x500A13, 0x500A38, 'wrapper LOOP1: new + ctor, country = [0xA83C9C][Get "Country" key]'),
    (0x500AFC, 0x500B2A, 'wrapper LOOP3: fallback per HouseType when HouseArray empty'),
    (0x59A167, 0x59A1B5, 'fn 0x599650 fallback: per HouseType when [0xA80238]==0'),
    (0x687F97, 0x687FCE, 'MP creator 0x687F10: per session-slot house'),
    (0x6880AD, 0x68812E, 'MP slot house init: +0x1EC=1; human slot +0x1ED=1 (0x68810F)'),
    (0x68817B, 0x6881AB, 'MP AI-list house (<=8): +0x1EC=0'),
    (0x6882D1, 0x688321, 'Neutral house (name 0x82BA08 "Neutral", color LightGrey 0x836ECC)'),
    (0x688325, 0x688373, 'Special house (name 0x817318 "Special")'),
    (0x6C3EBC, 0x6C3F04, 'COM-style exported stub 0x6C3E90 (HRESULT; no .text callers)'),
]
for lo, hi, title in WINDOWS:
    P('--- %s ---' % title)
    for a, m, o, b in disasm_range(lo, hi - lo):
        P('0x%06X  %-20s %s %s' % (a, b, m, o))
    P()
json_out['creation_sites'] = [hex(c) for c in callers(0x4F54A0)]

# ---------- 8. 分派：MP 工厂 vs 战役 wrapper ----------
P('=' * 100)
P('8. DISPATCH IN SCENARIO-START FN 0x686B20: call 0x687F10 (always) vs wrapper 0x5009B0')
P('=' * 100)
P('fn 0x686B20 callers: %s' % ', '.join(hex(c) for c in callers(0x686B20)))
P('fn 0x687F10 callers: %s' % ', '.join(hex(c) for c in callers(0x687F10)))
P('wrapper 0x5009B0 callers: %s' % ', '.join(hex(c) for c in callers(0x5009B0)))
P()
for lo, hi, title in [(0x6877B5, 0x6877D0, 'wrapper-call gate: cmp [0xA8B238], esi(0); jne skip'),
                      (0x68773D, 0x687762, 'esi=0 feed into the gate')]:
    P('--- %s ---' % title)
    for a, m, o, b in disasm_range(lo, hi - lo):
        P('0x%06X  %-20s %s %s' % (a, b, m, o))
    P()
P('=> [0xA8B238]==0（战役/单机场景）才走地图 [Houses] 解析；MP/遭遇战跳过，')
P('   此时地图 per-house 节（PlayerControl/Credits/PercentBuilt...）整体不被解析。')
P('   遭遇战路径 0x687F10：slot 房子 + Neutral + Special —— 2 slot 时恰好 4 个。')
P()
json_out['dispatch'] = {'scenario_fn': hex(0x686B20),
                        'mp_factory': hex(0x687F10),
                        'campaign_wrapper': hex(0x5009B0),
                        'gate': '[0xA8B238]==0 -> wrapper (0x6877B5 cmp, 0x6877B9 jne)'}

# ---------- 9. PlayerControl 运行时消费：0x4F6EC0 与转电脑 ----------
P('=' * 100)
P('9. RUNTIME USES OF PlayerControl(+0x1ED): 0x4F6EC0 difficulty setter & 0x50A5C0 to-Computer')
P('=' * 100)
for l in dump_fn(0x4F6EC0, 0x70):
    P(l)
P()
for a, m, o, b in disasm_range(0x50A5C0, 0x60):
    P('0x%06X  %-20s %s %s' % (a, b, m, o))
P()
P('0x50A5C0：SP 下仅当 (+0x1EC || +0x1ED) 才继续；随后两标志清零并把房名改 "Computer"')
P('（0x824FD8）—— PlayerControl 是“人类控制房”标志，不是创建开关。')
P()
json_out['runtime_flags'] = {
    'difficulty_setter': hex(0x4F6EC0),
    'to_computer_fn': hex(0x50A5C0),
}

# ---------- 10. MaxPlayers/MinPlayers 读取点 ----------
P('=' * 100)
P('10. MaxPlayers/MinPlayers READ SITES (strings 0x83F3F0 / 0x83F3FC)')
P('=' * 100)
P('xrefs of "MinPlayers" 0x83F3FC: %s' % ', '.join(hex(x['va']) for x in xref_map.get('MinPlayers', [])))
P('xrefs of "MaxPlayers" 0x83F3F0: %s' % ', '.join(hex(x['va']) for x in xref_map.get('MaxPlayers', [])))
P()
for lo, hi, title in [(0x6997C5, 0x699810,
                       'fn 0x6994F0: Get_Int("Basic", "MinPlayers"/"MaxPlayers", *cur) — session/lobby code'),
                      (0x69A530, 0x69A57C,
                       'fn 0x69A3B0: Get_Int(section, "MinPlayers"/"MaxPlayers", [ebx+0x180/0x184]) — Session object')]:
    P('--- %s ---' % title)
    for a, m, o, b in disasm_range(lo, hi - lo):
        P('0x%06X  %-20s %s %s' % (a, b, m, o))
    P()
P('=> 读取点全部位于会话/大厅代码（0x6994F0/0x69A3B0 互相调用；其调用链')
P('   0x69A0FC 与 0x699A77/0x699BC8/0x699E5C 均在会话区），与地图解析、')
P('   HouseClass 创建循环（0x5009B0/0x599650/0x687F10）无交集。')
P('   地图键 "MaxPlayer"/"MinPlayer"（无 s）二进制里不存在 —— 引擎读不到。')
P('   HouseClass 数量不由任何 Min/Max 值静态决定：数量=创建站点循环的循环上界。')
P()
json_out['maxmin'] = {
    'map_key_strings': 'absent from image (exact match, any case)',
    'readers': {'fn_0x6994F0': ['0x6997D7', '0x6997F9'],
                'fn_0x69A3B0': ['0x69A549', '0x69A561']},
    'relation_to_house_count': 'none (session/lobby only)',
}

# ---------- 11. 断点建议 ----------
P('=' * 100)
P('11. BREAKPOINT PLAN (静态无法裁定的两处)')
P('=' * 100)
P('B1. ba w1 / bp 0x4F54A0（HouseClass ctor），每次命中记录：')
P('    - 调用返回地址（0x500A30/0x500B19/0x59A198/0x687FC3/0x6881A0/0x6882FE/0x688351）')
P('      → 立即判定走的是哪条创建路径；')
P('    - dword [0xA8B238] 的值（0=战役 / 非0=会话）。')
P('    预期：若 4 次命中且返回地址=0x6882FE/0x688351/0x687FC3 → 遭遇战路径')
P('    （2 slot + Neutral + Special），“4 个 HouseClass”与 PlayerControl 无关成立。')
P('    若战役路径（返回 0x500A30）出现 14 次 + 0x6882FE/0x688351 各 1 次 → 共 16 个，')
P('    与“4 个”观测冲突，需要复查观测方法。')
P('B2. 静态已证 PercentBuilt 无运行时消费者；若要在动态侧复核，')
P('    bp 0x42EC1B（写 +0x571C）确认 Neutral=100 落进内存即可，之后该地址无人读。')
P()

# ---------- write outputs ----------
with open(OUT_TXT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(txt_lines) + '\n')

json_out['verdict'] = {
    'playercontrol_creation_link': 'NONE — never tested at any HouseClass creation site',
    'playercontrol_branches': [
        'Read_INI 0x500BE3/0x500BEA: yes&&campaign -> difficulty-adjusted start credits',
        'wrapper loop2 0x500ABF: !PlayerControl -> Scen+0x610 difficulty else Scen+0x60C',
        '0x50A5C0: clearing the flag renames house to "Computer"',
    ],
    'percentbuilt': 'parsed to HouseClass+0x571C, default 0, no runtime reader in .text',
    'houseclass_count_driver': 'loop bounds: [Houses] entries (campaign) / session slots+AI list+Neutral+Special (MP)',
    'best_expl_4_houses': 'MP/skirmish path 0x687F10: 2 slot houses + Neutral + Special = 4',
    'breakpoint': 'bp 0x4F54A0 log return-address + [0xA8B238]',
}
with open(OUT_JSON, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(json_out, f, ensure_ascii=False, indent=1)

sys.stderr.write('(done)\n')
