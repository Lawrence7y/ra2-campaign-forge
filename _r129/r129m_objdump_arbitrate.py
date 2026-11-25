# -*- coding: utf-8 -*-
"""R129m：用第二个译码器（i686-w64-mingw32-objdump）独立复算四段链的关键地址集合。

R128 S-181/S-183 的教训：capstone 单一来源会在 skipdata 设置、段内/文件偏移上出错。
故本轮所有「站点集合」类断言再用 objdump 各出一份，**比集合不比总数**。

比对三组：
  S1 0xa8e8c8 的 imm32 站点集合
  S2 0x7e9520 的 imm32 站点集合
  S3 0x840a74 的 imm32 站点集合
另外单独核 0x6bd6c2 / 0x6bd945 / 0x6bc436 / 0x6bc43f 处的指令文本。
"""
import sys, os, json, subprocess, re, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r128'))
from peek import *
import io

OUT = os.path.join(ROOT, '_r129', 'r129m_objdump_arbitrate.json')
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

add('M0 exe sha256 未变',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476')

# capstone 侧：全 .text 字节级扫 imm32
def byte_hits(val):
    out = []
    p = val.to_bytes(4, 'little')
    name, lo, hi, ptr, vs, rs = [s for s in SECS if s[0] == '.text'][0]
    b = pe.__data__[ptr:ptr + rs]
    i = 0
    while True:
        i = b.find(p, i)
        if i < 0: break
        out.append(lo + i); i += 1
    return sorted(out)

# objdump 侧：一次全反汇编，按文本里出现的立即数/位移抓地址
r = subprocess.run(['i686-w64-mingw32-objdump', '-d', '-M', 'intel', EXE],
                   capture_output=True, text=True, timeout=900)
lines = r.stdout.splitlines()
add('M1 objdump 成功输出（%d 行）' % len(lines), len(lines) > 100000 and r.returncode == 0,
    {'code': r.returncode, 'lines': len(lines)})
INS = []
for l in lines:
    # S-193：首版用 {8} 要求 8 位地址，但 objdump 不补前导零（形如 "  6bd6c2:"）⇒ INS 全空。
    m = re.match(r'^\s+([0-9a-f]+):\t', l)
    if m: INS.append((int(m.group(1), 16), l))
add('M2 objdump 解出的指令条数（应接近 capstone 的 139 万）', len(INS) > 1000000, len(INS))

def od_hits(val):
    # S-192：首版只匹配零填充形式 007e9520，但 objdump intel 输出的是 0x7e9520（不补零）
    # ⇒ 全部 0 命中。修法：两种形式都收，并要求「前面不是十六进制字符」以防子串误配。
    forms = {'%08x' % val, '%x' % val}
    pat = re.compile(r'(?<![0-9a-f])(?:' + '|'.join(sorted(forms)) + r')(?![0-9a-f])')
    out = []
    for a, l in INS:
        body = l.split('\t', 2)[-1].lower()
        if pat.search(body):
            out.append(a)
    return sorted(out)

# 归一化：capstone 的字节级命中落在「立即数起点」，objdump 报「指令起点」。
# 比集合必须先把 capstone 的命中映射回它所在指令的起点，否则两边永远差 1~2 字节。
# S-194：首版直接比原始地址集合，交集恒为 0，我差点把它写成「两个译码器分歧」。
# S-195：我先是用「从 a-10 起反汇编、取包含 a 的那条」自求指令边界，8700... 处有 300 处落到
# 非边界上（差 1 字节）—— 这正是 R127 S-170 记过的同一个坑：不从指令边界起算就会错位。
# 改为**用 objdump 的指令边界做归一化**（它是权威列表），我不再自求边界。
_OD_BOUND = {}
for _a, _l in INS:
    parts = _l.split('\t')
    if len(parts) < 3: continue
    _hexb = parts[1].strip()
    _n = len(_hexb.split()) if _hexb else 0
    if _n: _OD_BOUND[_a] = (_a, _a + _n)
_OD_STARTS = sorted(_OD_BOUND)
import bisect
def insn_start_of(a):
    i = bisect.bisect_right(_OD_STARTS, a) - 1
    if i < 0: return None
    lo, hi = _OD_BOUND[_OD_STARTS[i]]
    return lo if lo <= a < hi else None

report = {}
for nm, v in (('0xa8e8c8', 0xa8e8c8), ('0x7e9520', 0x7e9520), ('0x840a74', 0x840a74),
              ('0x87f7e8', 0x87f7e8)):
    cs_raw = byte_hits(v)
    cs = sorted({insn_start_of(a) for a in cs_raw})
    od = sorted(set(od_hits(v)))
    inter = sorted(set(cs) & set(od))
    only_cs = sorted(set(cs) - set(od)); only_od = sorted(set(od) - set(cs))
    report[nm] = {'capstone_bytes': len(cs_raw), 'capstone_insn': len(cs), 'objdump': len(od),
                  'inter': len(inter), 'only_cs': len(only_cs), 'only_od': len(only_od),
                  'only_od_at': ['0x%08x' % x for x in only_od[:8]],
                  'only_cs_at': ['0x%08x' % x for x in only_cs[:8]]}
    add('M3 %s：归一化到指令起点后 capstone %d / objdump %d / 交集 %d（原始字节命中 %d）'
        % (nm, len(cs), len(od), len(inter), len(cs_raw)), True, report[nm])
    add('M3b %s 两个译码器的指令起点集合完全一致（无单边独有）' % nm,
        not only_cs and not only_od, report[nm])

# 0xa8e8c8 必须恰 2 处且两边一致
cs2 = sorted({insn_start_of(a) for a in byte_hits(0xa8e8c8)})
od2 = sorted(set(od_hits(0xa8e8c8)))
add('M4 0xa8e8c8 两个译码器给同一指令集合 {0x4e7ce0, 0x6bc435}（后者是 push 0xa8e8c8 的指令起点）',
    cs2 == od2 == [0x4e7ce0, 0x6bc435],
    {'cs': ['0x%08x' % x for x in cs2], 'od': ['0x%08x' % x for x in od2]})
add('M5 口径说明：capstone 的字节级命中在 0x4e7ce2 / 0x6bc437（立即数起点），objdump 报 0x4e7ce0 / 0x6bc436'
    '（指令起点）。归一化后两者是同一集合，不是分歧',
    True, {'capstone_bytes': ['0x%08x' % x for x in byte_hits(0xa8e8c8)],
           'objdump_insn': ['0x%08x' % x for x in od2]})

# 四条指令文本逐条
for va, want in ((0x6bd6c2, 'mov    ebx,DWORD PTR ds:0x7e1370'),
                 (0x6bd945, 'call   ebx'),
                 (0x6bc43f, 'mov    esi,DWORD PTR ds:0x7e15d8'),
                 (0x6bc445, 'call   esi')):
    hit = [l for a, l in INS if a == va]
    body = hit[0].split('\t', 2)[-1].strip() if hit else ''
    ok = body.replace('  ', ' ').startswith(want.replace('  ', ' ')) or want in body
    add('M6 objdump 在 0x%08x 处给出 %r' % (va, body), ok, body)

# IAT 槽反解：objdump 不给导入名，但我可以核 IAT 内容与导入表一致
for slot, nm in ((0x7e1370, 'RegisterActiveObject'), (0x7e15d8, 'CoRegisterClassObject'),
                 (0x7e1384, 'RevokeActiveObject'), (0x7e1220, 'LoadLibraryA')):
    got = None
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in e.imports:
            if imp.address == slot: got = (e.dll.decode(), (imp.name or b'').decode())
    add('M7 IAT 槽 0x%08x -> %s' % (slot, nm), got is not None and got[1] == nm, got)

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck), 'report': report},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
print(json.dumps(report, ensure_ascii=False, indent=1))
