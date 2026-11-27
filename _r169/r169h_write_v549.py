#!/usr/bin/env python3
"""R169 H：FACT_INDEX V548 -> V549（F24 limitations 追加 R169 补段；只改措辞、不改任何计数）。

写入纪律：先在 R17_LEAD_BASELINE/ 用 wx 独占创建备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验。
断言：
  I1 源 = V548 且 sha == ef1716cf… / 113,574 B / CR 0
  I2 输出仍 55 行 × 5 列
  I3 差分行**恰 F24**、变化单元**恰 1 个**（第 5 列）
  I4 剥掉 R169 补段后与 V548 逐字节相同
  I5 F23 / F29 / F35 三行一字未改
  I6 输出 LF-only、CR == 0
  I7 备份文件独占创建成功（wx）且 sha 与源相同
"""
import hashlib, json, os, csv, io
ROOT = '/home/t628/projects/ra2-campaign-forge'
SRC = ROOT + '/lead/next_re_20261117_r14/R17_R120_FACTINDEX_V548/FACT_INDEX.tsv'
DST_DIR = ROOT + '/lead/next_re_20261117_r14/R17_R121_FACTINDEX_V549'
DST = DST_DIR + '/FACT_INDEX.tsv'
BAK = ROOT + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE/FACT_INDEX.tsv.V548.before_r169_20261127.bak'

raw = open(SRC, 'rb').read()
src_sha = hashlib.sha256(raw).hexdigest()
assert src_sha == 'ef1716cfdc76c67235a4996667b4070dba7d6658d701bff6c40651495b2da5c1', src_sha
assert len(raw) == 113574 and raw.count(b'\r') == 0

# 备份：wx 独占
fd = os.open(BAK, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
bak_sha = hashlib.sha256(open(BAK, 'rb').read()).hexdigest()

APPEND = (
 '**【R169 补·R168 那段的三处更正与一处新增，全部 4 字节/对齐口径实测】** '
 '① **R168 写的「`0x7d0cb0` 处有一张真 4 字节跳转表（首槽 `0x007d0cf7`）」半错，必须带方向读。** '
 '实测：从 `0x7d0cb0` 按 **+4** 步进只有 **1** 个有效条目（`0x7d0cf7`），第 2 槽 `0x7d0cb4` 的值 `0x1c8e448b` 不落 `.text` 就停；'
 '但唯一引用点 `0x7d0be2` 的**前一条指令**是 `0x7d0be0` 的 `f7 d9`（`neg ecx`），索引被取负 ⇒ 表是往**低地址**展开的。'
 '按 **-4** 步进实测 **9** 槽落 `.text`，其中最末一槽 `0x7d0c90` 的 4 字节里含一个指令起点 `0x7d0c91`（跨指令边界），'
 '剔除后**真条目 8**、表体 **`[0x7d0c94, 0x7d0cb4)`**、值序列 `0x7d0cf7 / 0x7d0ce4 / 0x7d0cdc / 0x7d0cd4 / 0x7d0ccc / 0x7d0cc4 / 0x7d0cbc / 0x7d0cb4`（步长 8×7、末步 +19）。'
 '⇒ 正确措辞是「`0x7d0cb0` 是这张反向索引表的**最高槽**，表首是 `0x7d0c94`」，**不得**写「首槽 `0x007d0cf7`」；'
 '「正向只有 1 条」与「共 8 条」两说**并存、须标方向**。孪生表 `0x7ca320`（引用点 `0x7ca252`，前有 `0x7ca250` 的 `neg ecx`）同构：表体 `[0x7ca304,0x7ca324)`、8 条目。'
 '② **R168 的表普查只做了 +4 单向延展，漏掉 2 张反向索引表 ⇒ 表数 358 应为 360（带方向口径）。** '
 '520 个站点里「正向 `>=2`」去重得 **358** 张（R168 原值，逐数复现）；把反向口径（-4 延展且相邻差众数出现 `>=3` 次）并进来得 **360** 张，'
 '新增恰是 `0x7d0cb0` 与 `0x7ca320` 两张；这 2 个站点在正向口径下条目数恰好都是 **1**，正是被漏的原因。'
 '**反控**：随机 2,000 个 `.text` 4 字节对齐地址做 -4 延展，落 `.text` 达 8 槽的 **0/2000 = 0.000%**；正向 2,000 个做 `>=2` 的 **6/2000 = 0.30%**。'
 '③ **`0x7d0cba` 的邻域归属本轮定死（R168 待办①）**：它**不**落在任何一条**线性解码**指令的字节区间内（0/65，R166 口径不变），'
 '但落在**真**指令 `0x7d0cb8`（4 B，`89 44 8f 1c` = `mov [edi+ecx*4+0x1c], eax`）内部、相对偏移 **2**；'
 '该指令正是反向表条目 `0x7d0cb4` 的后继，可由 `ecx = -6` 经 `jmp [ecx*4+0x7d0cb0]` 到达。'
 '它自身首字节 `8f`（`POP r/m32`，要求 `modrm.reg == 0`）而其后 `modrm = 0x1c` 的 `reg = 3` ⇒ 恒不可解码，这是 `8f` 的 opcode 约束，不是数据缺陷。'
 '⇒ **正确措辞**：「`0x7d0cba` 是 `case 0x7d0cb4` 拷贝体第 2 条指令的 SIB 字节，落在 `8f` 的非法 modrm 上」；'
 '「不落在任何指令内部」这句**只在**线性扫描对齐口径成立，**不得**脱口径写。'
 '**口径边界（本轮新增，必须与 0/65 同引）**：换对齐种子（360 张表的 2,325 个可解码槽值各自向下续解 64 条，得 145,636 条指令区间）后，'
 '65 条洞里落在真指令内部的 **1** 条（就是 `0x7d0cba`）；**反控基线**：随机 65,536 个 `.text` 地址在同一判据下命中 **2,070 = 3.159%** ⇒ 该 1 条不是「随便一个地址都会中」。'
 '④ **「65」这个数对相位口径稳健。** 起点集合 S 有两口径：连续相位（续解点 = 本块最后一条完整指令末尾）**1,392,527**、'
 '64KB 边界强制重置 **1,392,568**（差 **+41**，逐数复现；RAW 上界下同差 +41：1,394,120 vs 1,394,161）。'
 '洞的生成器在两口径下各跑一遍：连续相位 **65**（与 R167/R168 落盘**逐条相同**）、边界重置 **138**，'
 '两口径**交集恰 65**、边界重置**多出 73** 条且**全部贴着 64KB 边界 ±64 B**（逐条实测）'
 '⇒ 「65」是**两口径交集**，不是某一口径的偶然值；引用 65 时须写「连续相位口径，且为两口径交集」。'
 '⑤ **站点 520 的分解（供跨口径引用）**：`ff 24`/`ff 14` + 7 种 modrm + disp32 = **384**；`8b` + 8 种 modrm + `8d` + disp32 = **136**；合计 **520**。'
 '只读 `ff` 侧的实现会得 384，两者都对、只是口径不同。'
)

rows = list(csv.reader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
assert len(rows) == 55 and all(len(r) == 5 for r in rows), (len(rows), {len(r) for r in rows})
idx = [i for i, r in enumerate(rows) if r[0] == 'F24']
assert len(idx) == 1
i = idx[0]
new_rows = [list(r) for r in rows]
new_rows[i][4] = rows[i][4] + APPEND
out = '\n'.join('\t'.join(r) for r in new_rows) + '\n'
assert '\r' not in out
os.makedirs(DST_DIR, exist_ok=True)
open(DST, 'w', encoding='utf-8', newline='').write(out)

# 回读校验
r2 = open(DST, 'rb').read()
sha549 = hashlib.sha256(r2).hexdigest()
rows2 = list(csv.reader(io.StringIO(r2.decode('utf-8')), delimiter='\t'))
diff = [rows2[k][0] for k in range(len(rows2)) if rows2[k] != rows[k]]
cells = []
for k in range(len(rows2)):
    for c in range(5):
        if rows2[k][c] != rows[k][c]:
            cells.append((rows2[k][0], c + 1))
strip = r2.decode('utf-8').replace(APPEND, '')
A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('I1 源 = V548 / ef1716cf… / 113,574 B / CR 0',
    src_sha.startswith('ef1716cf') and len(raw) == 113574 and raw.count(b'\r') == 0,
    {'sha': src_sha[:16], 'bytes': len(raw)})
chk('I2 输出 55 行 × 5 列', len(rows2) == 55 and all(len(x) == 5 for x in rows2), len(rows2))
chk('I3 差分行恰 F24、变化单元恰 1（第 5 列）', diff == ['F24'] and cells == [('F24', 5)],
    {'rows': diff, 'cells': cells})
chk('I4 剥掉 R169 补段后与 V548 逐字节相同', strip == raw.decode('utf-8'),
    {'len_strip': len(strip.encode()), 'len_src': len(raw)})
chk('I5 F23/F29/F35 三行一字未改',
    all(rows2[k] == rows[k] for k in range(55) if rows[k][0] in ('F23', 'F29', 'F35')), 'ok')
chk('I6 输出 LF-only、CR == 0', r2.count(b'\r') == 0, r2.count(b'\r'))
chk('I7 备份 wx 独占创建且 sha 与源相同', bak_sha == src_sha, {'bak': os.path.basename(BAK), 'sha': bak_sha[:16]})

outj = {'src_sha': src_sha, 'src_bytes': len(raw), 'dst_sha': sha549, 'dst_bytes': len(r2),
        'dst_lines': len(rows2), 'append_bytes': len(APPEND.encode()), 'append_chars': len(APPEND),
        'diff_rows': diff, 'diff_cells': cells, 'backup': BAK,
        'f24_stmt_bytes': len(rows2[i][1].encode()), 'f24_lim_bytes': len(rows2[i][4].encode()),
        'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(outj, open(ROOT + '/_r169/r169h_write_v549.json', 'w'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', outj['fail'])
print('V549 sha =', sha549)
print('V549 bytes =', len(r2), ' append =', len(APPEND.encode()), 'B')
print('F24 floors -> (%d, %d)' % (outj['f24_stmt_bytes'], outj['f24_lim_bytes']))
