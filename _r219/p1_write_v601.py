# -*- coding: utf-8 -*-
"""R219 p1：FACT_INDEX V600 -> V601，只在 F29.limitations 追加 R219 实测段。
fail-closed：全部断言在写盘之前；不许 tab / CR / 双引号；其余 56 行逐字节相同。
证据路径列（第 4 列）不动 ⇒ D7 的 EVID 规范清单不变。
"""
import hashlib, os, json
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = ROOT + '/lead/next_re_20261117_r14'
OLD = TIER + '/R17_R131_FACTINDEX_V600/FACT_INDEX.tsv'
NEWD = TIER + '/R17_R131_FACTINDEX_V601'
NEW = NEWD + '/FACT_INDEX.tsv'
fails = []
def ck(nm, c, d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
h = hashlib.sha256(raw).hexdigest()
ck('W1 旧 V600 280689 B / sha fb513cc8', len(raw) == 280689 and h.startswith('fb513cc8'), (len(raw), h[:16]))
ck('W2 旧 CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
txt = raw.decode('utf-8'); lines = txt.split('\n')
ck('W3 57 行 + 末段空', len(lines) == 58 and lines[-1] == '', len(lines))
rows = [l.split('\t') for l in lines[:57]]
ck('W4 每行 5 列', all(len(r) == 5 for r in rows), [i for i, r in enumerate(rows) if len(r) != 5])
f29 = [r for r in rows if r[0] == 'F29'][0]
L0 = len(f29[4].encode())
ck('W5 F29 lim 当前长度记录', L0 > 47453, L0)

APP = ('**【R219 实测·高槽消费口径与 4 个幻影记录的来源，statement 不改、只补作用域】** '
'R219 用 `_r219/m1_sites6.py` … `_r219/m12_crc.py`（正反控全部内建）在现盘 `ra2bench/gamemd.exe`（sha256 `73201cc0…`）上重算：'
'① **6 处「超 344 槽域」位点全部定性，且都不是虚表槽**：`0x7bea07`=`call dword ptr [esi+0x784]`、`0x7bea0f`=`[esi+0x788]`、'
'`0x7c2f17`/`0x7c301c`=`[esi+0x77c]`、`0x7c37c7`=`[esi+0x780]` —— 这 5 处的 disp 是**对象内函数指针字段偏移**：'
'全 `.text` 对该三个 offset 的引用共 **31** 条，其中「`mov dword ptr [reg+off], imm32` 且 imm32 落 `.text`」的**写入端 12** 条（12/12 目标均在 `.text`），'
'且同一 offset 还被 `fmul qword ptr [reg+0x780]` **2** 次与 `fstp qword ptr [reg+0x780]` **1** 次当 double 使用 ⇒ 判为数据字段而非虚表槽；'
'第 6 处 `0x7cde2b`=`call dword ptr [esi+0x87c488]` 的 `esi` 由 `0x7cddac lea esi,[edi+edi*2]` + `0x7cddb6 shl esi,2` 得 **esi=edi*12**，'
'即 `0x87c488` 起是**步长 12 字节的静态派发表**（首项 `0x87c488: 007ce046 007f97d0 0087c370`，`dw(0x87c488)=0x7ce046` 落 `.text`），'
'上界由 `0x7cdd08 cmp edi,0x87c4c0` 给出；反控：全库 **无** 任何虚表槽数 ≥480（最大 344）⇒ s=479/480/481/482 不可能对应任何槽。'
'② **槽号口径本身成立**：对 931 个 s≥256 位点做前驱数据流分类（窗口 24 条指令），**914 (98.2%)** 的前驱是 `mov base, dword ptr [obj+0]`（读 vftable），'
'余 17 处经 200 条窗口溯源收敛为 `from_vtable_load 6 / from_indirect_ld 2 / from_mem_other 1 / from_pop 2` 加上述 6 处字段/派发表，**无一落入虚表槽语义**'
'⇒ R218「931 位点 / 91 个 s / 925 落 UnitClass 槽域」口径**不需要订正**；主会话逐数复现 931 / 91 / 925 与 top s 309/85/73/58/44 全部一致。'
'③ **「4 个幻影虚表」的真实载体是一张 162 记录 × 16 字节常量表的双份副本**：`0x876ff4..0x877a03` 与 `0x87b170..0x87bb7f` **逐字节相同**'
'（各 2576 B，sha256 同为 `7b724b01…`）；每条记录形态为 `f0 f1 f2 f3`，恒有 `f3 − f2 = 0x00800080`（162/162 记录成立；反控 shift 4/8/12 命中 **0**，'
'其他 delta `0x00800000`/`0x00800100` 在整段 `.data` 窗口命中 **0/0**）；表内为 16 位字递增序列（前几行 `0040 0080 00c0 0100`），'
'`0x00800040` 只是 `lo=0x0040, hi=0x0080` 这对相邻 16 位字被读成 dword 的结果，**恰好等于 DropPodLocomotionClass 的 COL 地址**，'
'这是**数值常量与 COL 地址撞车**，不是虚表。反控：表区间被 `.text` 以 dword 引用 **24** 次，全部指向表首 `0x87b170`（形如 `0x7c742f mov dx, word ptr [edx+0x87b170]`），'
'即代码按**字**访问该表、无任何 `[reg+off]` 形式的槽消费。'
'④ **幻影计数最终值不变**：`dw(V-4) in COL` 且 `dw(V)` 不落 `.text` 的全库候选仍恰为 **4** 个（`0x877000`/`0x877010`/`0x87b17c`/`0x87b18c`，全在 `.data`，'
'`dw(V)=0x010000c0`，`dw(V-4)=0x00800040`）；把整段 `.data 0x870000..0x880000` 排除后真表计数仍为 **1214**（delta 0）⇒ R218 的「1214 真表」结论保持，'
'但其**成因描述**由「16 B 形如 c0000001 … 的幻影记录」订正为「162 记录常量表的 f2 字段撞 COL 地址」。'
'⑤ **`0x4a1ca0` 不是「环缓冲容量 4」而是 CRC-32 累加器**：`cmp eax,4` 判的是**已缓冲字节数凑满 4 字节**；'
'凑满后执行 `not eax` → 逐字节 `xor idx` + `mov ebx,[ebp*4+0x81f7b4]` + `xor eax,ebx` → `not eax` → 存回 `[ecx]` 并把计数清零；'
'`0x81f7b4` 处 256 项 dword 表与 CRC-32 反射多项式 `0xEDB88320` 现场生成表**逐项 256/256 相同**（反控 CRC-32C `0x82F63B78` 仅 1/256、Koopman 1/256）；'
'字段语义 `+0=crc / +4=已缓冲字节数 / +8..+0xb=4 字节缓冲 / +0xc=计数影子`。'
'**行为等价性实测**：按该函数语义实现 `flush4(prev,buf4)` 与 `zlib.crc32(buf, prev)` 在 3×5 组输入上 **15/15 完全一致**（对 12 字节链式输入亦一致）。'
'**边界**：本条仍不改 statement 与 grade；`coverage.tsv` / `function_atlas.tsv` 仍不可读。')
ck('W6 无 tab', '\t' not in APP)
ck('W7 无 CR/换行', '\r' not in APP and '\n' not in APP)
ck('W8 无双引号', '"' not in APP)
ck('W9 以句号结尾且 >2000 B', APP.endswith('。') and len(APP.encode()) > 2000, len(APP.encode()))
newlim = f29[4] + APP
ck('W10 lim 只增不减', len(newlim.encode()) > L0, len(newlim.encode()))
f29[4] = newlim
newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode('utf-8')
ck('W11 新字节 = 旧 + 追加段', len(nb) == len(raw) + len(APP.encode()), (len(nb), len(raw) + len(APP.encode())))
ck('W12 新 CR == 0', nb.count(b'\r') == 0)
ck('W13 除 F29 外 56 行逐字节不变',
   all(lines[i] == '\t'.join(rows[i]) for i in range(57) if rows[i][0] != 'F29'))
ck('W14 F29 第 4 列（证据）未变', f29[3] == [r for r in rows if r[0] == 'F29'][0][3])
if fails:
    print('[ABORT] fails=%r' % fails); raise SystemExit(1)
os.makedirs(NEWD, exist_ok=True)
assert not os.path.exists(NEW)
with open(NEW, 'wb') as f: f.write(nb)
chk = open(NEW, 'rb').read()
assert chk == nb
print('[写入] %s  bytes %d -> %d  sha %s -> %s'
      % (NEW, len(raw), len(chk), h[:16], hashlib.sha256(chk).hexdigest()[:16]))
json.dump(dict(old_sha=h, new_sha=hashlib.sha256(chk).hexdigest(), old_bytes=len(raw),
               new_bytes=len(chk), app_bytes=len(APP.encode())),
          open(ROOT + '/_r219/p1.json', 'w'), indent=1)
