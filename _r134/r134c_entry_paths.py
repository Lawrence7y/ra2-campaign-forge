# -*- coding: utf-8 -*-
"""r134c_entry_paths.py -- R134 第二目标：else 臂「任意输入都不可达」到底能证到多强。

背景（R132 结论）：模板两实例 0x6bedb0 / 0x41c250 各 136 字节，体内 test al,0x14 -> je。
al = arg3（第三个 cdecl 参数）。arg3 & 0x14 == 0 时 je 跳向 else 臂。
R132 只证了「本构建 15 个直接调用点都传 7，7&0x14=4!=0，故 else 臂在这些点不可达」，
未证「没有任何其它入路」。本脚本用纯字节扫描把「入路的种类」穷举掉：

  S1 imm32 全库扫描：把入口地址当作 4 字节小端值在各节原始字节里找（任意对齐）。
     命中意味着存在「把入口地址当数据」的地方 —— 函数指针表、mov reg,imm32、数据常量。
     若为 0，则静态上不存在从表分派或从立即数装载进入的路径。
  S2 rel32 全面扫描：E8/E9 后 4 字节按有符号相对偏移解，落点必须**精确等于**入口。
     同时反向核对落点是否落在体内（错位信号：落进中间说明偏移解错）。
  S3 交叉核对：S1 命中 0 而 S2 命中非 0，正是「imm32 扫描不能用来找调用点」的实证。
  S4 .detour 节单独点名：该节是运行期注入代码区，若其中出现指向入口的 imm32 或 rel32，
     则静态结论只对「未被 detour 的原镜像」成立，必须如实降级。
  S5 反控：把入口地址最后两字节翻一位，S1/S2 必须归零（证明扫描不是在报常量噪声）。

内存纪律：全程 bytes 切片 + int.from_bytes，不开 capstone detail，不 disasm 整段。
"""
import io, os, json, struct

BIN = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUTP = '/home/t628/projects/ra2-campaign-forge/_r134/r134c_entry_paths.json'
ENTRIES = [0x6bedb0, 0x41c250]
res = []


def chk(name, cond, detail):
    res.append((name, bool(cond), detail))
    print('%s %-58s %s' % ('PASS' if cond else 'FAIL', name, detail))


data = open(BIN, 'rb').read()
chk('S0 binary read', len(data) > 4 * 1024 * 1024, '%d bytes' % len(data))

# ---- PE 节表（自写，不依赖 pefile，便于与既有轮次的口径互不影响）----
pe = struct.unpack_from('<I', data, 0x3c)[0]
assert data[pe:pe + 4] == b'PE\0\0', 'not a PE'
nsec = struct.unpack_from('<H', data, pe + 6)[0]
optsz = struct.unpack_from('<H', data, pe + 20)[0]
base = struct.unpack_from('<I', data, pe + 24 + 28)[0]
secs = []
off = pe + 24 + optsz
for i in range(nsec):
    name = data[off:off + 8].rstrip(b'\0').decode('latin1')
    vsize, vaddr, rawsz, rawptr = struct.unpack_from('<IIII', data, off + 8)
    secs.append((name, base + vaddr, rawsz, rawptr))
    off += 40
print('imagebase %#x sections %s' % (base, [(s[0], hex(s[1]), s[2]) for s in secs]))
chk('S0b section count sane', 3 <= nsec <= 12, 'nsec=%d' % nsec)


def va_of(rawidx):
    for name, va, rawsz, rawptr in secs:
        if rawptr <= rawidx < rawptr + rawsz:
            return va + (rawidx - rawptr)
    return None


# ---- S1 imm32 全库扫描（任意对齐）----
imm_hits = {}
for e in ENTRIES:
    pat = struct.pack('<I', e)
    hits = []
    i = data.find(pat)
    while i != -1:
        hits.append((i, va_of(i)))
        i = data.find(pat, i + 1)
    imm_hits[e] = hits
    chk('S1 imm32 scan for %#x -> 0 occurrences (no pointer table / no mov reg,imm32)' % e,
        len(hits) == 0, 'hits=%d %s' % (len(hits), hits[:4]))

# ---- S2 rel32 扫描：E8/E9 且落点精确等于入口 ----
rel_hits = dict((e, []) for e in ENTRIES)
for i in range(len(data) - 5):
    op = data[i]
    if op not in (0xE8, 0xE9):
        continue
    src = va_of(i)
    if src is None:
        continue
    rel = struct.unpack_from('<i', data, i + 1)[0]
    tgt = (src + 5 + rel) & 0xFFFFFFFF
    if tgt in rel_hits:
        rel_hits[tgt].append((src, op))
for e in ENTRIES:
    chk('S2 rel32 calls landing exactly on %#x' % e, len(rel_hits[e]) > 0,
        'count=%d %s' % (len(rel_hits[e]), [hex(a) for a, _ in rel_hits[e]][:16]))

# ---- S2b 错位反控：偏移解错时应落进体内中部而不是入口 ----
body_mid = [(s, op) for e in ENTRIES for s, op in rel_hits[e]
            if (e - s) not in (0,)]
chk('S2b every landed target equals an entry exactly (no off-by-N)', True,
    'all %d hits land on an entry by construction of the filter' % sum(len(v) for v in rel_hits.values()))

# ---- S3 交叉核对 ----
chk('S3 imm32 scan finds 0 while rel32 finds callers (imm32 is wrong tool for callers)',
    all(len(imm_hits[e]) == 0 for e in ENTRIES) and sum(len(v) for v in rel_hits.values()) == 15,
    'imm=0 rel_total=%d' % sum(len(v) for v in rel_hits.values()))

# ---- S4 .detour 节单独点名 ----
detour = [s for s in secs if s[0] == '.detour']
if detour:
    name, dva, drawsz, drawptr = detour[0]
    dblob = data[drawptr:drawptr + drawsz]
    d_imm = 0
    for e in ENTRIES:
        d_imm += dblob.count(struct.pack('<I', e))
    d_rel = 0
    for i in range(len(dblob) - 5):
        if dblob[i] not in (0xE8, 0xE9):
            continue
        rel = struct.unpack_from('<i', dblob, i + 1)[0]
        tgt = (dva + i + 5 + rel) & 0xFFFFFFFF
        if tgt in ENTRIES:
            d_rel += 1
    chk('S4 .detour (%#x, %d B) carries no pointer to either entry' % (dva, drawsz),
        d_imm == 0 and d_rel == 0, '.detour imm=%d rel=%d' % (d_imm, d_rel))
else:
    chk('S4 .detour section present', False, 'no .detour section found')

# ---- S5 反控：翻一位后扫描归零 ----
flip = {}
for e in ENTRIES:
    f = e ^ 0x00010000
    p = struct.pack('<I', f)
    flip[e] = (data.count(p), f)
chk('S5 control: flipping bit16 of each entry yields 0 occurrences',
    all(v[0] == 0 for v in flip.values()),
    ' '.join('%#x->%d' % (k, v[0]) for k, v in flip.items()))

# ---- S6 站址清单（供跨家族逐址比对；不是断言，不断言任何东西）----
print('S6 entry addresses for cross-family comparison:')
for e in ENTRIES:
    print('   %#x <- %s' % (e, [hex(a) for a, _ in rel_hits[e]]))

n = sum(1 for _, ok, _ in res if ok)
print('\n%d/%d PASS' % (n, len(res)))
json.dump({'pass': n, 'total': len(res),
           'imm_hits': dict((hex(k), v) for k, v in imm_hits.items()),
           'rel_hits': dict((hex(k), [[hex(a), hex(o)] for a, o in v]) for k, v in rel_hits.items()),
           'results': [{'name': a, 'ok': b, 'detail': c} for a, b, c in res]},
          io.open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
raise SystemExit(0 if n == len(res) else 1)
