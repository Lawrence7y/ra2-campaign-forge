#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 CC：FACT_INDEX V565 -> V566，只在本列（F01.limitations）追加 R185 实测段。
fail-closed：全部断言在写盘之前；不允许 tab / CR / 双引号；其余 53 行逐字节相同。
"""
import hashlib,io,os,sys,time
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
OLD=os.path.join(TIER,'R17_R131_FACTINDEX_V565','FACT_INDEX.tsv')
NEWD=os.path.join(TIER,'R17_R131_FACTINDEX_V566')
NEW=os.path.join(NEWD,'FACT_INDEX.tsv')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
raw=open(OLD,'rb').read()
ck('W1 旧 V565 135,931 B / sha f64d36aa…', len(raw)==135931 and hashlib.sha256(raw).hexdigest().startswith('f64d36aa'), (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
ck('W2 旧 CR == 0', raw.count(b'\r')==0, raw.count(b'\r'))
txt=raw.decode('utf-8')
lines=txt.split('\n')
ck('W3 55 行 × LF 结尾（split 得 56 段、末段空）', len(lines)==56 and lines[-1]=='', len(lines))
rows=[l.split('\t') for l in lines[:55]]
ck('W4 每行 5 列', all(len(r)==5 for r in rows), [i for i,r in enumerate(rows) if len(r)!=5])
f01=[r for r in rows if r[0]=='F01'][0]
ck('W5 F01 statement 458 B / limitations 5,036 B', len(f01[1].encode())==458 and len(f01[4].encode())==5036, (len(f01[1].encode()),len(f01[4].encode())))

APP=('**【R185 实测·F01 两个标志数与两处口径由现盘字节独立复算，statement 不改、只补作用域】** '
'R185 用 `_r185/r185z_colcensus.py`（**11 断言 0 FAIL**）+ `_r185/r185aa_claim.py`（**7 断言 0 FAIL**）+ '
'`_r185/r185bb_257.py`（**7 断言 0 FAIL**）在现盘 `ra2bench/gamemd.exe`（4,825,360 B、sha256 `73201cc0…`）上重算：'
'① TypeDescriptor **988**（`.?AV` 962 / `.?AU` 26）、总 COL **1214**、主 COL（`mdisp==0` 且被 `dword[vt−4]` 指回）**954**、'
'无任何 COL 指向的 TD **34** —— 四个数与 R140 一致；'
'② statement 的 **1201** 与 **1211** 仍不是现盘可复现值：被指回的 distinct COL 实测 **1214**、总 COL 实测 **1214**；'
'1211 只能由「`COL+4 <= 0x1000`」这一事后阈值得到（被剔除的恰 **3** 个、其 `COL+4` 全为 `0x5518`：'
'MouseClass `0x7FA9B8` / TabClass `0x805E48` / ScrollClass `0x809008`），1201 在 R140 已试 30 余种单谓词与 400 余种组合仍不可复现 '
'⇒ 本行 statement 的两个数须按「看板第 7–9 轮段（审计 R13）口径」引用，不得当作现盘重算值；'
'③ 正文「COL 恰 5 dword、无 pSelf 字段」与本列旧记的「257/1211」本轮首次逐数复现：'
'`dword[COL−4]==0` 在 1214 个 COL 上是 **260**、在 1211 子集上是 **257**（260−3，被剔除的 3 个在 `COL−4` 处均为 0）；'
'`dword[COL−0x10]==COL` 在 1214 上 **0** 条；'
'④ 正文括注「每类一个 lowest-VA 主 COL」与 F29 的「`mdisp==0`」两集合**大小同为 954 但对称差 188（94+94）**，'
'机制是多 COL 类（**94** 个）的 COL 按 `mdisp` **严格递减**排列（94 递减 / 0 递增 / 0 全等 / 0 混合）'
'⇒ `mdisp==0` 恒为类内最高 VA、lowest-VA 恒非 `mdisp==0`，两处 954 **不可按数字相等互引**；'
'⑤ COL 全集 1214 个的 `mdisp` 取值恰 **10 种** `{0:954, 4:91, 8:78, 12:78, 24:6, 36:1, 40:1, 44:1, 1728:1, 21784:3}`；'
'**954 个主 COL 的 `mdisp` 分布**为 `{0:942, 4:12}`，那 12 个 `mdisp==4` 的类全为 Locomotion 系'
'（Locomotion + Drive/DropPod/Fly/Hover/Jumpjet/Mech/Rocket/Ship/Teleport/Tunnel/Walk），'
'且这 12 个类的 `CHD→pBaseArray→BCD` 里 ILocomotion 项的 `mdisp` **恒为 4**、`pdisp` 恒为 `0xFFFFFFFF`'
'（`_r185/r185y_iloco.py` **8 断言 0 FAIL**，含把该项 `mdisp` 改 0 的反控）'
'—— 这是 `mdisp==4` 的第二条独立字节证据（BCD 侧），不是从主 COL 反推。'
'**边界**：本条只在本列追加，statement 与 grade 不动；1201 仍登记为不可复现，`coverage.tsv` / `function_atlas.tsv` 仍不可读。')
ck('W6 追加段不含 tab', '\t' not in APP)
ck('W7 追加段不含 CR / 换行', '\r' not in APP and '\n' not in APP)
ck('W8 追加段不含双引号', '"' not in APP)
ck('W9 追加段以句号结尾且长度 > 1200', APP.endswith('。') and len(APP.encode())>1200, len(APP.encode()))
new_lim=f01[4]+APP
ck('W10 新 limitations 只增不减（5036 -> %d）'%len(new_lim.encode()), len(new_lim.encode())>5036)
f01[4]=new_lim
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
nb=newtxt.encode('utf-8')
ck('W11 新体量 = 旧 + 追加段字节', len(nb)==135931+len(APP.encode()), (len(nb),135931+len(APP.encode())))
ck('W12 新 CR == 0', nb.count(b'\r')==0, nb.count(b'\r'))
nl=nb.decode().split('\n')
ck('W13 新 55 行 / 5 列', len(nl)==56 and all(len(l.split('\t'))==5 for l in nl[:55]), len(nl))
nrows=[l.split('\t') for l in nl[:55]]
ors=[l.split('\t') for l in txt.split('\n')[:55]]
diff=[i for i in range(55) if nrows[i]!=ors[i]]
ck('W14 变化行恰 1 行且是 F01（索引 1）', diff==[1], diff)
ck('W15 其余 54 行（含表头）× 5 列逐字节相同', all(nrows[i]==ors[i] for i in list(range(0,1))+list(range(2,55))))
ck('W16 F01 的 statement / grade / evidence_paths 三列未动',
   nrows[1][1]==ors[1][1] and nrows[1][2]==ors[1][2] and nrows[1][3]==ors[1][3])
ck('W17 旧段逐字仍是新段前缀', nrows[1][4].startswith(ors[1][4]))
NEWSHA=hashlib.sha256(nb).hexdigest()
ck('W18 新 sha != 旧 sha', NEWSHA!=hashlib.sha256(raw).hexdigest(), NEWSHA[:16])
if fails:
    print('★ fail-closed：%d 条未过，不写盘'%len(fails)); sys.exit(1)
os.makedirs(NEWD,exist_ok=True)
assert not os.path.exists(NEW), '目标已存在：%s'%NEW
with open(NEW,'wb') as f: f.write(nb)
back=open(NEW,'rb').read()
ck('W19 回读 sha == 新 sha', hashlib.sha256(back).hexdigest()==NEWSHA, NEWSHA[:16])
ck('W20 回读字节数', len(back)==len(nb), len(back))
print('断言 %d 条，FAIL %d 条'%(n,len(fails)))
print('V566 = %d B / sha %s' % (len(nb), NEWSHA))
print('F01 limitations: 5036 -> %d (+%d)' % (len(new_lim.encode()), len(APP.encode())))
sys.exit(1 if fails else 0)
