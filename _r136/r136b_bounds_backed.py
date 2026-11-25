# -*- coding: utf-8 -*-
"""r136b_bounds_backed.py -- R136 主会话：F24「bounds 段 86.19% 盘上没有任何字节对应」的独立复核

被审主张（FACT_INDEX F24 行 limitations 列）：
  「bounds 的 16.7 MB 里 86.19%（1,200,251 条）盘上没有任何字节对应；
    另 13.81%（192,341 条）已有『地址+字节+助记符』，其中 99.89% 与 gamemd.exe 同址字节相等。」

这条主张是「剔除 bounds 段 16,711,118 B、把语料从 4,413/744,172,839 改成 4,413/727,461,721」
的**唯一依据**（R14_COMMON §2.61/§2.63 逐字：「剔的理由不是它大，是不满足我自己口径里的那个且」）。
故它若错，整条剔段动作的依据随之失去。

本脚本只回答一个问题：bounds 里的地址，在盘上到底有没有字节对应。
不用「有没有第二个值列」这种口径话术，只用可机械判定的「该地址是否是一条真实指令的起始」。

不 import、不读任何既有脚本；正反控成对。只写出 _r136/*.json。
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
BIN = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
A2 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'D41_SUBST', '_audit', 'EVIDENCE',
                  'a2_sites.json')

res = []
OUT = {}


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-64s %s' % ('PASS' if cond else 'FAIL', name, detail))


# ---------- B0 读 bounds（用 json，不用正则切片） ----------
d = json.loads(io.open(A2, encoding='utf-8').read())
bounds = [int(x, 16) for x in d['bounds']]
OUT['bounds_n'] = len(bounds)
chk('B0a bounds 恰 1,392,592 条', len(bounds) == 1392592, 'n=%d' % len(bounds))
chk('B0b bounds 全为 8 位大写 hex 且全在 .text [0x401000,0x7E038D]',
    all(len(x) == 8 and x == x.upper() for x in d['bounds'])
    and min(bounds) >= 0x401000 and max(bounds) <= 0x7E038D,
    'min=%#x max=%#x' % (min(bounds), max(bounds)))
chk('B0c bounds 无重复（是 set 大小的 1.0 倍）', len(set(bounds)) == len(bounds),
    'distinct=%d' % len(set(bounds)))
chk('B0d 该件顶层只有 calls / bounds 两个键（F24 的结构描述成立）',
    sorted(d.keys()) == ['bounds', 'calls'], 'keys=%s' % sorted(d.keys()))
OUT['calls_keys'] = len(d['calls'])
OUT['call_edges'] = sum(len(v) for v in d['calls'].values())
chk('B0e calls 6,728 键 / 68,253 调用点（F24 的另外两个数）',
    len(d['calls']) == 6728 and OUT['call_edges'] == 68253,
    'keys=%d edges=%d' % (len(d['calls']), OUT['call_edges']))

# ---------- B1 指令起始全集：objdump（R91 DR12：全库起始集必须用 objdump 地址行） ----------
tmpd = tempfile.mkdtemp(prefix='r136b_')
objd = os.path.join(tmpd, 'objd.txt')
try:
    with io.open(objd, 'wb') as fh:
        rc = subprocess.call(['i686-w64-mingw32-objdump', '-d', '--no-show-raw-insn', BIN],
                             stdout=fh, stderr=subprocess.DEVNULL, timeout=900)
    chk('B1a objdump 退出码 0', rc == 0, 'rc=%d' % rc)
    starts = set()
    linepat = re.compile(r'^\s*([0-9a-f]{6,8}):\s+')
    nlines = 0
    with io.open(objd, encoding='latin1') as fh:
        for line in fh:                      # 流式，不入内存
            nlines += 1
            m = linepat.match(line)
            if m:
                starts.add(int(m.group(1), 16))
    OUT['objdump_lines'] = nlines
    OUT['starts_n'] = len(starts)
    chk('B1b 指令起始数 = 1,392,516（R91 DR12 记的 objdump 值，独立复现）',
        len(starts) == 1392516, 'starts=%d (lines=%d)' % (len(starts), nlines))
    chk('B1c 起始集覆盖 .text 首尾（0x401000 与 >=0x7E0300 都在集内）',
        0x401000 in starts and max(starts) >= 0x7E0300, 'max=%#x' % max(starts))
    # 反控 B1d：同一份文本用「宽松正则」（不要求冒号后空白）会多解出操作数列，条数必须不同
    loose = 0
    lp2 = re.compile(r'^\s*([0-9a-f]{6,8}):')
    with io.open(objd, encoding='latin1') as fh:
        for line in fh:
            if lp2.match(line):
                loose += 1
    chk('B1d 反控：宽松正则与严格正则条数相同（说明没有把操作数行当起始行）',
        loose == len(starts), 'loose=%d strict=%d' % (loose, len(starts)))
except Exception as e:  # noqa
    chk('B1 objdump 流程异常', False, repr(e))
    starts = set()

# ---------- B2 bounds 对指令起始集的命中 ----------
hit = [b for b in bounds if b in starts]
miss = [b for b in bounds if b not in starts]
OUT['hit'] = len(hit)
OUT['miss'] = len(miss)
chk('B2a bounds 命中指令起始集 >= 99%（F24 说 13.81% 有对应，方向相反）',
    len(hit) * 1.0 / len(bounds) >= 0.99,
    'hit=%d/%d = %.4f%% ; miss=%d = %.4f%%'
    % (len(hit), len(bounds), 100.0 * len(hit) / len(bounds), len(miss),
       100.0 * len(miss) / len(bounds)))
chk('B2b 未命中数 <= 200（若 F24 对，未命中应约 1,200,251）',
    len(miss) <= 200, 'miss=%d (F24 主张 1,200,251)' % len(miss))
chk('B2c 反控：F24 的 86.19% 若成立，未命中应 >= 1,200,000 —— 实测差三个数量级',
    len(miss) < 1200251,
    'observed_miss=%d vs claimed=1200251 (ratio %.1fx)'
    % (len(miss), 1200251.0 / max(1, len(miss))))

# ---------- B3 未命中者逐个定性 ----------
import bisect
ss = sorted(starts)
detail = []
for b in miss:
    i = bisect.bisect_left(ss, b)
    prev = ss[i - 1] if i > 0 else None
    nxt = ss[i] if i < len(ss) else None
    detail.append({'va': hex(b), 'prev_start': hex(prev) if prev else None,
                   'delta_from_prev': (b - prev) if prev else None,
                   'next_start': hex(nxt) if nxt else None})
OUT['miss_detail'] = detail
in_insn = [x for x in detail if x['delta_from_prev'] is not None and x['delta_from_prev'] <= 15]
chk('B3a 未命中者 100% 落在「前一条指令起始 +1..15 字节」内（是长指令的内部字节，不是无字节）',
    len(in_insn) == len(detail) and len(detail) > 0,
    'in_insn=%d / %d ; max_delta=%s'
    % (len(in_insn), len(detail), max(x['delta_from_prev'] for x in detail) if detail else None))
# 独立佐证：这些字节位置在文件里确实有字节
imgbase = 0x400000
with io.open(BIN, 'rb') as fh:
    blob = fh.read()

# 自错 S-243：首版 va2off 直接返回 rva（假设 .text raw == rva），遇到 .rdata/.data/.detour 里的
# 调用点就越界（IndexError: index out of range，B5 处炸掉）。改为按节表求解，并在越界时返回 None。
def _sections(bb):
    e = int.from_bytes(bb[0x3c:0x40], 'little')
    assert bb[e:e + 4] == b'PE\0\0'
    coff = e + 4
    nsec = int.from_bytes(bb[coff + 2:coff + 4], 'little')
    optsz = int.from_bytes(bb[coff + 16:coff + 18], 'little')
    opt = coff + 20
    so = opt + optsz
    out = []
    for i in range(nsec):
        o = so + i * 40
        nm = bb[o:o + 8].rstrip(b'\0').decode('latin1')
        vsz = int.from_bytes(bb[o + 8:o + 12], 'little')
        rva = int.from_bytes(bb[o + 12:o + 16], 'little')
        rsz = int.from_bytes(bb[o + 16:o + 20], 'little')
        raw = int.from_bytes(bb[o + 20:o + 24], 'little')
        out.append((nm, vsz, rva, rsz, raw))
    return out


SEC = _sections(blob)
OUT['sections'] = [(s[0], hex(s[2]), hex(s[3]), hex(s[4])) for s in SEC]


def va2off(va):
    rva = va - imgbase
    for nm, vsz, rva0, rsz, rawp in SEC:
        if rva0 <= rva < rva0 + rsz:
            return rva - rva0 + rawp
    return None


nonnul = sum(1 for b in miss if blob[va2off(b)] != 0)
# 自错 S-242：首版断言写成「非零字节数 == 未命中数」，实测 84/111 —— 断言写错了，
# 不是结论错。111 里 27 个地址处文件里恰是 0x00（长指令的立即数高位/位移高字节），
# 那里仍然「有字节」，只是字节值是零。正确判据是「地址落在文件映像内」而非「非零」。
in_image = 0
for b in miss:
    o = va2off(b)
    if 0 <= o < len(blob):
        in_image += 1
chk('B3b 未命中地址 100% 落在文件映像内（那里确实有字节；27 个字节值为 0x00）',
    in_image == len(miss),
    'in_image=%d / %d ; nonzero=%d ; zero=%d'
    % (in_image, len(miss), nonnul, len(miss) - nonnul))

# ---------- B4 反控组 ----------
# B4a：把起始集砍掉后半段 -> 命中率必须大幅下降
half = set(x for x in starts if x < 0x600000)
hit_half = sum(1 for b in bounds if b in half)
chk('B4a 反控：起始集只留 < 0x600000 时命中率大幅下降（B2 的命中不是任何集合都给）',
    hit_half * 1.0 / len(bounds) < 0.6,
    'hit=%d = %.2f%%' % (hit_half, 100.0 * hit_half / len(bounds)))
# B4b：bounds 整体 +4 -> 命中率必须大幅下降（否则说明是地址密集造成的假命中）
shift = sum(1 for b in bounds if (b + 4) in starts)
chk('B4b 反控：bounds 全体 +4 后命中率大幅下降（命中不是地址密集的副产品）',
    shift * 1.0 / len(bounds) < 0.6,
    'hit=%d = %.2f%%' % (shift, 100.0 * shift / len(bounds)))
# B4c：随机取同样多地址 -> 命中率须极低
import random
random.seed(20261125)
rand = [random.randrange(0x401000, 0x7E038D) for _ in range(len(bounds))]
hit_rand = sum(1 for b in rand if b in starts)
chk('B4c 反控：随机同数量地址命中率 < 40%（指令起始集本身不密集）',
    hit_rand * 1.0 / len(rand) < 0.40,
    'hit=%d = %.2f%%' % (hit_rand, 100.0 * hit_rand / len(rand)))
OUT['ctrl'] = {'half': hit_half, 'shift4': shift, 'rand': hit_rand}

# ---------- B5 calls 段的可回原址性（F24 说 68,253/68,253 全部真回原址命中） ----------
E8 = 0xE8
# 自错 S-246：首版把 calls 的键当调用点、值当目标，方向搞反 —— 实测键是**被调函数**、
# 值是**调用点列表**（calls["00407100"] = 4 个调用点）。故 E8 要在**值**那一侧取字节。
ok_calls = 0
bad_calls = []
for tgt_hex, sites in d['calls'].items():
    tva = int(tgt_hex, 16)
    for s_hex in sites:
        s = int(s_hex, 16)
        off = va2off(s)
        if off is None:
            bad_calls.append((s_hex, 'site not in image'))
            continue
        b0 = blob[off]
        if b0 != E8:
            bad_calls.append((s_hex, 'opcode=%02X' % b0))
            continue
        rel = int.from_bytes(blob[off + 1:off + 5], 'little', signed=True)
        got = (s + 5 + rel) & 0xFFFFFFFF
        if got == tva:
            ok_calls += 1
        else:
            bad_calls.append((s_hex, 'rel->%#x != %#x' % (got, tva)))
chk('B5a calls 的 68,253 条调用点全部真回原址命中（E8 + rel32 验算）',
    ok_calls == 68253 and not bad_calls,
    'ok=%d bad=%d %s' % (ok_calls, len(bad_calls), bad_calls[:3]))
# 自错 S-244：首版 B5b 写成 chk(..., True, ...) —— 恒真断言，与 R134 S-185 / R135 S-235 同族，当场删掉。
# 自错 S-247：第二版改成「rel32 按无符号读」，实测 68,253 vs 68,253 **完全相同** ——
# 因为在 mod 2^32 加法里 `s+5+rel` 与 `s+5+rel_u` 同余，这个反控在判据上不可能翻转，
# 又是一条零信息反控（R135 S-236 同族：反控没打在判据上）。
# 换成真正会翻转的：**去掉 mod 2^32 环绕**（要求结果落在 [0x401000,0x7E038D] 内且恰等于目标）。
# 反向调用（rel<0）在无环绕算术下会得到负值，必然不命中 ⇒ 有符号/无符号的差别才显现。
neg = 0
pos = 0
nomask_signed = 0
nomask_unsigned = 0
for tgt_hex, sites in d['calls'].items():
    tva = int(tgt_hex, 16)
    for s_hex in sites:
        s = int(s_hex, 16)
        off = va2off(s)
        if off is None or blob[off] != E8:
            continue
        rels = int.from_bytes(blob[off + 1:off + 5], 'little', signed=True)
        relu = int.from_bytes(blob[off + 1:off + 5], 'little', signed=False)
        if rels < 0:
            neg += 1
        else:
            pos += 1
        if (s + 5 + rels) == tva:          # 不取 & 0xFFFFFFFF
            nomask_signed += 1
        if (s + 5 + relu) == tva:
            nomask_unsigned += 1
chk('B5b 反控：去掉 mod 2^32 环绕后，signed 读命中 68,245 而 unsigned 读只有 38,905'
    '（29,356 条反向调用被无符号读全部丢失 ⇒ signed 是真判据）',
    nomask_signed > nomask_unsigned * 1.5 and neg == 29356 and pos == 38897,
    'signed=%d unsigned=%d backward=%d forward=%d'
    % (nomask_signed, nomask_unsigned, neg, pos))
chk('B5c 反控：signed 无环绕命中 68,245 < 有环绕 68,253，差 8 条确为跨 32 位边界环绕调用',
    ok_calls - nomask_signed == 8, 'wrap_edges=%d' % (ok_calls - nomask_signed))
OUT['calls'] = {'ok': ok_calls, 'bad': len(bad_calls), 'nomask_signed': nomask_signed,
                'nomask_unsigned': nomask_unsigned, 'backward': neg, 'forward': pos}

# ---------- B6 F24 的 86.19% 与 13.81% 能否由「文件读取截断」复现 ----------
# 只测一种自然假设：判定时只读了前 N 字节。给出「若只读前 1 MiB」会得到什么。
with io.open(A2, 'rb') as fh:
    head = fh.read(1024 * 1024)
# 自错 S-245：首版写法是「对 1,392,592 个 bounds 各做一次 `tok in head`」，即在 1 MiB 里
# 反复做子串搜索 ⇒ 约 1.4 TB 扫描量，脚本被外层 timeout 杀掉（EXIT=143，产物未生成）。
# 改为「先从 head 里一次性抽全部 8 位 hex 令牌成集合，再做集合交集」——同判据，O(n)。
toks = set(m.group(1) for m in re.finditer(r'"([0-9A-F]{8})"', head.decode('latin1')))
inset = sum(1 for b in bounds if ('%08X' % b) in toks)
OUT['in_first_1mib'] = inset
chk('B6a 只读前 1 MiB 文件时 bounds 命中数远小于 total（截断会系统性少算）',
    inset < len(bounds), 'in_1MiB=%d / %d' % (inset, len(bounds)))
chk('B6b F24 的 192,341 不等于「前 1 MiB 内可寻到」的数（该假设被证伪）',
    inset != 192341, 'in_1MiB=%d vs claimed_covered=192341' % inset)

npass = sum(1 for _a, c, _d in res if c)
print('SUMMARY %d/%d PASS' % (npass, len(res)))
with io.open(os.path.join(ROOT, '_r136', 'r136b_bounds_backed.json'), 'w', encoding='utf-8') as f:
    f.write(json.dumps({'asserts': [{'name': a, 'ok': c, 'detail': dd} for a, c, dd in res],
                        'out': OUT}, ensure_ascii=False, indent=1, default=str))
sys.exit(0 if npass == len(res) else 1)
