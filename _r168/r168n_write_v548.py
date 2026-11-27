#!/usr/bin/env python3
"""R168 N：FACT_INDEX V547 -> V548（F24 limitations 追加一段，只改措辞不改计数）。"""
import hashlib, json, os, csv, io
ROOT = '/home/t628/projects/ra2-campaign-forge'
SRC = ROOT + '/lead/next_re_20261117_r14/R17_R119_FACTINDEX_V547/FACT_INDEX.tsv'
DST_DIR = ROOT + '/lead/next_re_20261117_r14/R17_R120_FACTINDEX_V548'
DST = DST_DIR + '/FACT_INDEX.tsv'
os.makedirs(DST_DIR, exist_ok=True)

raw = open(SRC, 'rb').read()
src_sha = hashlib.sha256(raw).hexdigest()
assert src_sha == '919263cf03f51bd4ec933ec8ad1d07ee599e93cc4b9b6362d33e5442328b2ec9', src_sha
assert len(raw) == 109220 and raw.count(b'\r') == 0

APPEND = (
 '**【R168 补·R167 那段的两处更正：56/65 应为 58/65；「3 字节条目表」是相位缺陷的人为产物】** '
 'R167 段末把 65 条定成「56 条在代码指针表内 + 6 条在字节查找表内 + 3 条未归类」，本轮换**代码驱动**的独立判据重做，'
 '并把 R167 的一处实现缺陷复现出来：'
 '① **判据换成「有代码引用」而不是「值看起来像表」**。R167 用的是「节内 4 字节网格 + 相位 0..3，条目值都是 .text 地址 ⇒ 表」（>= 3 条）；'
 '本卡改用**引用站点**入手：全 .text 扫三种入口形态 —— ff 24 后跟 7 种 modrm（0x8d/0x85/0x95/0x9d/0xa5/0xb5/0xbd）再加 4 字节 disp32（jmp）、'
 'ff 14 后跟同 7 种 modrm 再加 disp32（call）、8b 后跟 8 种 modrm（0x04/0x0c/0x14/0x1c/0x24/0x2c/0x34/0x3c）再加 8d 与 disp32（mov）—— '
 '共 **520** 个站点；从 disp32 起按 4 字节步进延展、槽值仍落 .text 就继续，**>= 2 条**即记一表 ⇒ **358 张表（按 disp32 去重）**、'
 '**2,842 个槽值**，其中 **2,830（99.58%）恰是线性扫描认定的指令起点**（R167 用它的口径得 1,600/1,616 = 99.01%，两个口径同向）。'
 '② **65 条按引用型表重分桶：58 / 4 / 1 / 1 / 1**：落在引用型 4 字节跳转表内 **58**；'
 '同一段 16 字节严格 +1 递增样本（fe ff 00 01 f7 f8 fa fb fc fd fe ff 00 01 02 03，'
 '该样本在镜像内**只出现 2 次**，分别在 0x7c5d92 与 0x7c80f2）的**四个落点** 0x7c5d92／0x7c5d9c／0x7c80f2／0x7c80fc 为**字节查表 4 条**；'
 '0x723e27 邻域 32 字节全在 0x01..0x20（游程 18）为**小整数索引表 1 条**；'
 '0x793455 是 fe ff 两字节后紧跟 c3（**短填充 1 条**，游程 0）；0x7d0cba **1 条**为 R167 缺陷产物（见 ③）。**五桶互斥、和为 65**。'
 '③ **R167「3 字节条目表」是它自己实现里的相位缺陷，不是事实**。'
 '问题在 _r167/r167d_holes_semantics_final.py 的 best_table（**行 140–162**）：'
 'for w in (4, 3) 只把**读取宽度**改成 3，其余四处**全部硬写 4** —— 相位 ((v - LO - p) % 4)、覆盖窗 b <= v < b + 4、'
 '回退 a = lo - 4、推进 hi += 4、条目数 k = (hi - lo) // 4。'
 '⇒ w=3 分支读的是「**4 字节槽位上的低 3 字节**」。逐字重放得 R167 原值（**56/65、35 张表、1,616 槽**，三项全等）；'
 '把步进改成等于宽度后，那 3 条 w=3 命中（0x48db25 k=15、0x62fe4c k=6、0x7d0cba k=14）的**3 字节表全部消失**（k 变 1／1／0）；'
 '按「是否仍落在任意表内」计则只有 0x7d0cba 掉出去（另两条在 4 字节口径下本就成表）。'
 '⇒ R167 的「3 条未归类」里 **2 条（0x71f9e0／0x71f9e4）其实是 2 条目跳转表**（0x71f9d3 的 jmp [ecx*4+0x71f9e0]），'
 '第 3 条 0x793455 是短填充；R167 的「6 条字节查找表」里 0x71f77c 同属 2 条目表。'
 '**正确措辞**：那 65 条 = 「线性解码在 .text 内**被代码引用的跳转表（58）**／字节查表（4）／小整数索引表（1）／短填充（1）**上踩到不可解码字节**、只能前进 1 字节」的位置，'
 '外加 R167 缺陷产物 1 条；**不得**再写「56/65」「6 条字节查找表」「3 条未归类」。'
 '④ **判别量不是几何占比**。表区间去重叠后仅 **10,296 B**（占 .text **0.2536%**），'
 '拿它当基线会算出 352× 的「富集」，那是**几何恒等式**（表小 ≠ 富集），不得引用。'
 '真判别量是**同为不可解码位**的两族转化率：表内不可解码位 **126** 个、其中 **58** 个成洞（**46.03%**）；'
 '表外不可解码位 **57,891** 个（= 58,017 − 126）、其中 **7** 个成洞（**0.0121%**）⇒ 比值 **3,807×**。'
 '**反控**：同字节数（10,296 B）的随机区段内不可解码位 **125** 个（与表内 126 同阶，说明表内字节并不特别容易解不出），但成洞 **0** 个。'
 '⑤ **口径边界（必须同引）**：本轮起点数 **1,392,527** 与 65 这个数，在多种独立实现下逐条相同；'
 '另有一份实现给出 **1,390,966**，差 **1,561** 已定位为**该实现的 VA 基址写成 tva 加文件偏移、又用 end_va 过滤**，'
 '等价于少扫末 **4,096 B**（末 4,096 B 内起点恰 **1,561** 个），两口径下 65 个重对齐点**逐条相同**。'
 '**本条计数一字未改**（1,392,592 / 1,392,527 / 65 / 1,593 全为原值）。'
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
open(DST, 'w', encoding='utf-8', newline='').write(out)
raw2 = open(DST, 'rb').read()
sha2 = hashlib.sha256(raw2).hexdigest()
assert hashlib.sha256(open(SRC, 'rb').read()).hexdigest() == src_sha, 'V547 被改'

rows2 = list(csv.reader(io.StringIO(raw2.decode('utf-8')), delimiter='\t'))
drift = [j for j in range(55) if rows[j] != rows2[j]]
cells = [(j, c) for j in range(55) for c in range(5) if rows[j][c] != rows2[j][c]]
same_prefix = new_rows[i][4][:len(rows[i][4])] == rows[i][4]

def rb(rows_, j, cols): return '\t'.join(rows_[j][:cols]).encode()
A = []
A.append({'id': 'A0 V547 sha 与字节数复核', 'ok': src_sha.startswith('919263cf') and len(raw) == 109220})
A.append({'id': 'A1 新件 55 行 / 5 列 / LF-only', 'ok': len(rows2) == 55 and all(len(r) == 5 for r in rows2) and raw2.count(b'\r') == 0})
A.append({'id': 'A2 差分行恰 F24', 'ok': drift == [i], 'detail': repr([rows2[j][0] for j in drift])})
A.append({'id': 'A3 变化单元恰 1 个且为第 5 列', 'ok': cells == [(i, 4)], 'detail': repr(cells)})
A.append({'id': 'A4 剥掉追加段后与 V547 该单元逐字节相同', 'ok': same_prefix})
A.append({'id': 'A5 其余 54 行 × 5 列逐字节相同',
          'ok': all(rows[j] == rows2[j] for j in range(55) if j != i)})
A.append({'id': 'A6 前四列逐字节不变', 'ok': rb(rows, i, 4) == rb(rows2, i, 4)})
# S-552 登记：首版写成「出现次数不变」⇒ 恒 FAIL（追加段自带那几个数，与 R167 S-537 同族）。
# 正确判据：旧文本里的出现次数不变（= A4 前缀逐字节相同）＋ 新增次数恰等于 APPEND 里的次数。
_counts = ('1,392,592', '1,392,527', '1,593', '58,017')
A.append({'id': 'A7 增量恰等于 APPEND 内的出现次数（旧文本部分由 A4 保证不变）',
          'ok': all(new_rows[i][4].count(s) - rows[i][4].count(s) == APPEND.count(s) for s in _counts),
          'detail': repr({s: (rows[i][4].count(s), new_rows[i][4].count(s), APPEND.count(s)) for s in _counts})})
A.append({'id': 'A8 追加字节数 == 实测差', 'ok': len(raw2) - len(raw) == len(APPEND.encode('utf-8')),
          'detail': '%d vs %d' % (len(raw2) - len(raw), len(APPEND.encode('utf-8')))})
A.append({'id': 'A9 反控：F23/F29/F35 三行一字未改（本轮不碰）',
          'ok': all(rows[j] == rows2[j] for j, r in enumerate(rows) if r[0] in ('F23', 'F29', 'F35'))})
out_json = {'v547_sha': src_sha, 'v547_bytes': len(raw), 'v548_sha': sha2, 'v548_bytes': len(raw2),
            'append_bytes': len(APPEND.encode('utf-8')), 'append_chars': len(APPEND),
            'drift': [rows2[j][0] for j in drift], 'cells': len(cells),
            'path': DST, 'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out_json, open(ROOT + '/_r168/r168n_write_v548.json', 'w'), ensure_ascii=False, indent=1)
print('V547 %s %d B -> V548 %s %d B (+%d B / +%d chars)'
      % (src_sha[:16], len(raw), sha2[:16], len(raw2), len(raw2) - len(raw), len(APPEND)))
print('drift=%s cells=%d' % ([rows2[j][0] for j in drift], len(cells)))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', ''))
