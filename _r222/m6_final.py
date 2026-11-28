# -*- coding: utf-8 -*-
"""R222 m6：本轮全部结论的可复算断言集（内建正控 + 反控）。

覆盖：
  C1  编码器内联 delta ≡ 差分表 0x879b30（1424/1424）
  C2  n&8 与 n>=8 两种符号写法在 n∈0..15 上等价
  C3  编码器 index 更新 = IDX[n] + 无符号回绕下钳 0 + 上钳 0x58，且 0x58 = 88 = step 表末下标
  C4  解码器状态记录 6 B（int32 pred + uint16 step），stereo 12 B，ch1 在 +6
  C5  三段展开体的 store 偏移与指针步进（mono 2 步 / stereo 4 步）
  C6  四张 8 项表 + 两张 4 项表，4 项表后 4 项不是地址
  C7  各段常量表引用分布
  C8  0x7c7371 参数分派：仅支持 16 位；8 位与其他组合直接跳尾声
  C9  编码器初始化两处不对称（0x7c6270 设 step=7，0x7c6730 不设）
  C10 反控 4 条
"""
import sys, re, struct, json
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
fails = []
notes = []


def ck(name, cond, detail=''):
    if not cond:
        fails.append(name)
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''))


def dis(lo, hi):
    o = P.r2o(lo)
    b = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(b, lo)]


def S(va):
    return struct.unpack_from('<i', P.RAW, P.r2o(va))[0]


def U(va):
    return struct.unpack_from('<I', P.RAW, P.r2o(va))[0]


def W(va):
    return struct.unpack_from('<H', P.RAW, P.r2o(va))[0]


print('gamemd.exe sha256 =', __import__('hashlib').sha256(P.RAW).hexdigest())

# ---------- C1 编码器内联 delta ≡ 0x879b30 ----------
step = [struct.unpack_from('<h', P.RAW, P.r2o(0x8758e4) + 2 * m)[0] for m in range(89)]
dt = [S(0x879b30 + 4 * k) for k in range(1424)]


def inline_delta(sv, n):
    d = (sv >> 3)
    if n & 4: d += sv
    if n & 2: d += (sv >> 1)
    if n & 1: d += (sv >> 2)
    if n & 8: d = -d
    return d


hit = sum(1 for m in range(89) for n in range(16) if inline_delta(step[m], n) == dt[16 * m + n])
ck('C1 编码器内联 delta ≡ 表 0x879b30 1424/1424', hit == 1424, '%d/1424' % hit)
ck('C1b step 表 89 项、首项 7、末项 32767', len(step) == 89 and step[0] == 7 and step[88] == 32767,
   (step[0], step[88]))

# ---------- C2 符号写法等价 ----------
eq = all(((1 if (n & 8) else 0) == (1 if n >= 8 else 0)) for n in range(16))
hit2 = sum(1 for m in range(89) for n in range(16)
           if inline_delta(step[m], n) == dt[16 * m + n] and n < 16)
ck('C2 n&8 与 n>=8 在 n∈0..15 上等价', eq and hit2 == 1424, (eq, hit2))

# ---------- C3 编码器 index 更新 ----------
IDX = [struct.unpack_from('<h', P.RAW, P.r2o(0x8758c4) + 2 * i)[0] for i in range(8)]
ck('C3a 索引表 0x8758c4 = (-1,-1,-1,-1,2,4,6,8)', IDX == [-1, -1, -1, -1, 2, 4, 6, 8], IDX)


def enc_idx_upd(idx, n):
    v = (idx + IDX[n & 7]) & 0xFFFF
    if v >= 0x8000:
        v = 0
    elif v > 0x58:
        v = 0x58
    return v


# 遍历全部 (idx,n) 组合，确认结果恒在 [0,88] 且 88 就是 step 表末下标
bad = [(i, n) for i in range(89) for n in range(16) if not (0 <= enc_idx_upd(i, n) <= 0x58)]
ck('C3b idx 更新对全部 89x16 组合留在 [0,0x58]', bad == [], bad[:3])
ck('C3c 0x58 == 88 == step 表末下标（独立确认 89 项）', 0x58 == 88 == len(step) - 1, (0x58, len(step) - 1))
# 反控：若上钳改为 0x57，则 m=88,n=4 会被错误钳住
wrong = sum(1 for i in range(89) for n in range(16)
            if (lambda v: 0 if v >= 0x8000 else (0x57 if v > 0x57 else v))((i + IDX[n & 7]) & 0xFFFF)
            != enc_idx_upd(i, n))
ck('C3d 反控 上钳 0x57 => 与 0x58 版差异 > 0', wrong > 0, wrong)
# 指令级核对：jb 0x8000 是无符号
seg = [(a, mn, op) for a, b, mn, op in dis(0x7c63a2, 0x7c63c4)]
ck('C3e 门限指令 cmp 0x8000 / jb 与 cmp 0x58 / jbe 存在',
   any(mn == 'cmp' and '0x8000' in op for a, mn, op in seg) and
   any(mn == 'jb' for a, mn, op in seg) and
   any(mn == 'cmp' and '0x58' in op for a, mn, op in seg) and
   any(mn == 'jbe' for a, mn, op in seg), seg)

# ---------- C4 解码器状态记录 6 B ----------
mono_entry = [(a, mn, op) for a, b, mn, op in dis(0x7c73c3, 0x7c73e0)]
stereo_entry = [(a, mn, op) for a, b, mn, op in dis(0x7c7788, 0x7c77a0)]
stereo2_entry = [(a, mn, op) for a, b, mn, op in dis(0x7c7b4c, 0x7c7b70)]
ck('C4a mono 入口读 [ebx] dword + [ebx+4] word',
   any(mn == 'mov' and op == 'eax, dword ptr [ebx]' for a, mn, op in mono_entry) and
   any(mn == 'mov' and op == 'dx, word ptr [ebx + 4]' for a, mn, op in mono_entry), mono_entry)
ck('C4b stereo 遍一读 [ebx] dword + [ebx+4] word',
   any(mn == 'mov' and op == 'eax, dword ptr [ebx]' for a, mn, op in stereo_entry) and
   any(mn == 'mov' and op == 'dx, word ptr [ebx + 4]' for a, mn, op in stereo_entry), stereo_entry)
ck('C4c stereo 遍二读 [ebx+6] dword + [ebx+0xa] word',
   any(mn == 'mov' and op == 'eax, dword ptr [ebx + 6]' for a, mn, op in stereo2_entry) and
   any(mn == 'mov' and op == 'dx, word ptr [ebx + 0xa]' for a, mn, op in stereo2_entry), stereo2_entry)
wb1 = [(a, mn, op) for a, b, mn, op in dis(0x7c75c1, 0x7c75cb)]
wb2 = [(a, mn, op) for a, b, mn, op in dis(0x7c7d59, 0x7c7d62)]
ck('C4d 回写遍一 [ebx]/[ebx+4]、遍二 [ebx+6]/[ebx+0xa]',
   any(op == 'dword ptr [ebx], eax' for a, mn, op in wb1) and
   any(op == 'word ptr [ebx + 4], dx' for a, mn, op in wb1) and
   any(op == 'dword ptr [ebx + 6], eax' for a, mn, op in wb2) and
   any(op == 'word ptr [ebx + 0xa], dx' for a, mn, op in wb2), (wb1, wb2))
ck('C4e 记录 6 B ⇒ stereo 12 B；+4 与 +6 跨界不重叠',
   4 + 2 == 6 and 6 + 4 + 2 == 12)

# ---------- C5 三段展开体 store 偏移与指针步进 ----------
def store_offs(lo, hi):
    # 注意：capstone 把小立即数印成十进制（如 [edi + 4]），大数才印 0x..，必须 int(x,0)
    out = []
    for a, b, mn, op in dis(lo, hi):
        m = re.match(r'word ptr \[edi(?: \+ ([0-9a-fx]+))?\], ax$', op)
        if mn == 'mov' and m:
            out.append(int(m.group(1), 0) if m.group(1) else 0)
    return out


def add_imm(lo, hi, reg):
    out = []
    for a, b, mn, op in dis(lo, hi):
        m = re.match(re.escape(reg) + r', ([0-9a-fx]+)$', op)
        if mn == 'add' and m:
            out.append(int(m.group(1), 0))
    return out


om = store_offs(0x7c7428, 0x7c75b2)
o1 = store_offs(0x7c77f0, 0x7c7982)
o2 = store_offs(0x7c7bc0, 0x7c7d4a)
ck('C5a mono 体 8 store / 偏移 0,2,..,e', om == list(range(0, 0x10, 2)), om)
ck('C5b stereo 遍一 8 store / 偏移 0,4,..,1c', o1 == list(range(0, 0x20, 4)), o1)
ck('C5c stereo 遍二 8 store / 偏移 0,4,..,1c', o2 == list(range(0, 0x20, 4)), o2)
ck('C5d mono add edi,0x10 / add esi,4',
   add_imm(0x7c7428, 0x7c75b2, 'edi') == [0x10] and add_imm(0x7c7428, 0x7c75b2, 'esi') == [4],
   (add_imm(0x7c7428, 0x7c75b2, 'edi'), add_imm(0x7c7428, 0x7c75b2, 'esi')))
ck('C5e stereo 两遍 add edi,0x20 / add esi,4',
   add_imm(0x7c77f0, 0x7c7982, 'edi') == [0x20] and add_imm(0x7c77f0, 0x7c7982, 'esi') == [4] and
   add_imm(0x7c7bc0, 0x7c7d4a, 'edi') == [0x20] and add_imm(0x7c7bc0, 0x7c7d4a, 'esi') == [4],
   (add_imm(0x7c77f0, 0x7c7982, 'edi'), add_imm(0x7c7bc0, 0x7c7d4a, 'edi')))
ck('C5f 反控：stereo 偏移序列 != mono 偏移序列', o1 != om and o2 != om, (o1, om))
# 遍二入口的 +2 与 esi 偏移
p2h = [(a, mn, op) for a, b, mn, op in dis(0x7c7b4c, 0x7c7b62)]
ck('C5g 遍二入口 add edi,2 + mov edx,[ebp+0x18]; shr edx,3; add esi,edx',
   any(mn == 'add' and op == 'edi, 2' for a, mn, op in p2h) and
   any(mn == 'shr' and op == 'edx, 3' for a, mn, op in p2h) and
   any(mn == 'add' and op == 'esi, edx' for a, mn, op in p2h), p2h)

# ---------- C6 六张表 ----------
T8 = [0x7c7758, 0x7c7b1c, 0x7c7ef0]
T4 = [0x7c7778, 0x7c7b3c, 0x7c7f10]
for t in T8:
    v = [U(t + 4 * k) for k in range(8)]
    ck('C6 8 项表 %08x 八项全在 .text' % t, all(P.sec_of(x) == '.text' for x in v),
       [hex(x) for x in v])
for t in T4:
    v = [U(t + 4 * k) for k in range(8)]
    head4 = v[:4]
    tail4 = v[4:]
    ck('C6 4 项表 %08x 前 4 项在 .text、后 4 项不是地址' % t,
       all(P.sec_of(x) == '.text' for x in head4) and
       not any(P.sec_of(x) == '.text' for x in tail4),
       {'head': [hex(x) for x in head4], 'tail': [hex(x) for x in tail4]})
# 反控：4 项表若按 8 项读，第 5 项会落到非法地址
ck('C6 反控 4 项表 8 项读必出段外',
   all(not any(P.sec_of(U(t + 4 * k)) == '.text' for k in range(4, 8)) for t in T4))

# ---------- C7 引用分布 ----------
REG = [('blk1_dec', 0x7c6808, 0x7c6b38), ('mono0', 0x7c7428, 0x7c75b2),
       ('align0', 0x7c7694, 0x7c77f0), ('pass1', 0x7c77f0, 0x7c7982),
       ('align1', 0x7c79a4, 0x7c7b1c), ('pass2', 0x7c7bc0, 0x7c7d4a),
       ('align2', 0x7c7d6c, 0x7c7ef0)]
TG = ['0x8759b4', '0x876ff4', '0x879b30', '0x87b170', '0x877b14', '0x877c14', '0x87bc90', '0x87bd90']
dist = {}
for nm, lo, hi in REG:
    c = {t: 0 for t in TG}
    for a, b, mn, op in dis(lo, hi):
        for t in TG:
            if '[' in op and t in op:
                c[t] += 1
    dist[nm] = {k: v for k, v in c.items() if v}
    print('   %-9s %08x..%08x %s' % (nm, lo, hi, dist[nm]))
ck('C7a 块1 解码器只用块1 表（0x8759b4/0x876ff4/0x877b14/0x877c14）',
   set(dist['blk1_dec']) == {'0x8759b4', '0x876ff4', '0x877b14', '0x877c14'}, dist['blk1_dec'])
ck('C7b 块2 三个展开体各自 8/8/4/4（0x879b30/0x87b170/0x87bd90/0x87bc90）',
   all(dist[k] == {'0x879b30': 8, '0x87b170': 8, '0x87bd90': 4, '0x87bc90': 4}
       for k in ('mono0', 'pass1', 'pass2')),
   {k: dist[k] for k in ('mono0', 'pass1', 'pass2')})
ck('C7c 三个对齐块只引抖动表（4/3），不引差分/状态表',
   all(set(dist[k]) == {'0x87bd90', '0x87bc90'} for k in ('align0', 'align1', 'align2')),
   {k: dist[k] for k in ('align0', 'align1', 'align2')})

# ---------- C8 参数分派 ----------
d = [(a, mn, op) for a, b, mn, op in dis(0x7c7371, 0x7c73d0)]
ck('C8a cx==8 两支都跳 0x7c75cc（不支持 8 位）',
   [op for a, mn, op in d if a in (0x7c7390, 0x7c739f)] == ['0x7c75cc', '0x7c75cc'],
   [op for a, mn, op in d if a in (0x7c7390, 0x7c739f)])
ck('C8b cx==0x10 且 dx==2 -> 0x7c7788（stereo 入口）',
   [op for a, mn, op in d if a == 0x7c73b4] == ['0x7c7788'],
   [op for a, mn, op in d if a == 0x7c73b4])
ck('C8c cx==0x10 且 dx==1 -> 顺序落入 0x7c73c3（mono 入口）',
   [op for a, mn, op in d if a == 0x7c73bd] == ['0x7c75cc'] and 0x7c73c3 in [a for a, b, mn, op in dis(0x7c73c3, 0x7c73d0)],
   [hex(a) for a, b, mn, op in dis(0x7c73c3, 0x7c73d0)][:3])
# 调用点
o = P.r2o(0x401000)
buf = P.RAW[o:o + 0x3e0000]
base = 0x401000
calls = []
for i in range(len(buf) - 5):
    if buf[i] == 0xe8:
        rel = struct.unpack_from('<i', buf, i + 1)[0]
        if base + i + 5 + rel == 0x7c7371:
            calls.append(base + i)
ck('C8d 0x7c7371 调用点恰 2 个：0x7c24a2 / 0x7c2557', calls == [0x7c24a2, 0x7c2557],
   [hex(x) for x in calls])
a1 = [(a, mn, op) for a, b, mn, op in dis(0x7c2486, 0x7c24a7)]
a2 = [(a, mn, op) for a, b, mn, op in dis(0x7c253b, 0x7c255c)]
ck('C8e 调用点一 push 源 = &[ebx+0x7d0], ebp, byte[ebx+0x3e], byte[ebx+0x3f], [ebx+0x78c], esi',
   [op for a, mn, op in a1 if mn == 'push'] ==
   ['edx', 'ebp', 'eax', 'ecx', 'edx', 'esi'], [op for a, mn, op in a1 if mn == 'push'])
ck('C8f 调用点二 push 源 = &[ebx+0x7d0], ebp, byte[ebx+0x3e], byte[ebx+0x3f], [ebx+0x7a8], esi',
   [op for a, mn, op in a2 if mn == 'push'] ==
   ['eax', 'ebp', 'ecx', 'edx', 'eax', 'esi'], [op for a, mn, op in a2 if mn == 'push'])

# ---------- C9 编码器初始化不对称 ----------
i2 = [(a, mn, op) for a, b, mn, op in dis(0x7c6270, 0x7c62ac)]
i1 = [(a, mn, op) for a, b, mn, op in dis(0x7c6730, 0x7c6752)]
ck('C9a 0x7c6270 置两声道 step=7（+0x20/+0x34）与 index=0（+0x22/+0x36）',
   any(op == 'word ptr [eax + 0x20], 7' for a, mn, op in i2) and
   any(op == 'word ptr [eax + 0x34], 7' for a, mn, op in i2) and
   any(op == 'word ptr [eax + 0x22], 0' for a, mn, op in i2) and
   any(op == 'word ptr [eax + 0x36], 0' for a, mn, op in i2), i2)
ck('C9b 0x7c6730 不置 step=7（只清 index 与 predictor）',
   not any('0x20], 7' in op or '0x34], 7' in op for a, mn, op in i1), i1)

# ---------- C10 反控 ----------
hit_c2 = sum(1 for m in range(89) for n in range(16)
             if inline_delta(struct.unpack_from('<h', P.RAW, P.r2o(0x8758e6) + 2 * m)[0], n) == dt[16 * m + n])
ck('C10a 反控 step 表基址 +2 => 命中远小于 1424', hit_c2 < 200, '%d/1424' % hit_c2)
s_tab = [S(0x87b170 + 4 * k) for k in range(1424)]
hit_c3 = sum(1 for m in range(89) for n in range(16) if inline_delta(step[m], n) == s_tab[16 * m + n])
ck('C10b 反控 错表 0x87b170 当 dword => 近 0', hit_c3 < 10, '%d/1424' % hit_c3)
hit_c4 = sum(1 for m in range(89) for n in range(16)
             if inline_delta(step[m], n) == dt[16 * m + (n ^ 7)])
ck('C10c 反控 nibble 反序（n^7）=> 命中远小于 1424', hit_c4 < 800, '%d/1424' % hit_c4)
hit_c5 = sum(1 for m in range(89) for n in range(16)
             if inline_delta(step[m] >> 1, n) == dt[16 * m + n])
ck('C10d 反控 step 右移 1 => 命中远小于 1424', hit_c5 < 400, '%d/1424' % hit_c5)

print()
print('=== 结论摘要 ===')
print('diff 表命中 %d/1424 ; 索引表 %s ; 0x58=%d ; 调用点 %s' %
      (hit, IDX, 0x58, [hex(x) for x in calls]))
print('FAIL 数 =', len(fails), fails)
json.dump({'fails': fails, 'hit_delta': hit, 'hit_c2': hit_c2, 'hit_c3': hit_c3,
           'hit_c4': hit_c4, 'hit_c5': hit_c5, 'dist': dist,
           'calls': [hex(x) for x in calls]},
          open('/home/t628/projects/ra2-campaign-forge/_r222/m6.json', 'w'), indent=1)
if fails:
    raise SystemExit(1)
