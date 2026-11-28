# -*- coding: utf-8 -*-
"""R218 p1：FACT_INDEX V599 -> V600，只在 F29.limitations 追加 R218 实测段。
fail-closed：全部断言在写盘之前；不许 tab / CR / 双引号；其余 56 行逐字节相同。
证据路径列（第 4 列）不动 ⇒ D7 的 EVID 规范清单不变。
"""
import hashlib,os,json
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
OLD=TIER+'/R17_R131_FACTINDEX_V599/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V600'
NEW=NEWD+'/FACT_INDEX.tsv'
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
raw=open(OLD,'rb').read()
h=hashlib.sha256(raw).hexdigest()
ck('W1 旧 V599 277566 B / sha 616a86e2', len(raw)==277566 and h.startswith('616a86e2'),(len(raw),h[:16]))
ck('W2 旧 CR == 0', raw.count(b'\r')==0, raw.count(b'\r'))
txt=raw.decode('utf-8'); lines=txt.split('\n')
ck('W3 57 行 + 末段空', len(lines)==58 and lines[-1]=='', len(lines))
rows=[l.split('\t') for l in lines[:57]]
ck('W4 每行 5 列', all(len(r)==5 for r in rows), [i for i,r in enumerate(rows) if len(r)!=5])
f29=[r for r in rows if r[0]=='F29'][0]
ck('W5 F29 stmt 12751 / lim 47453', len(f29[1].encode())==12751 and len(f29[4].encode())==47453,
   (len(f29[1].encode()),len(f29[4].encode())))
APP=('**【R218 实测·虚表口径二分与高槽归因，statement 不改、只补作用域】** '
'R218 用 `_r218/m11_final_ctl.py`（**34 断言 0 FAIL**）+ `_r218/m21_freeze.py` 在现盘 `ra2bench/gamemd.exe`（sha256 `73201cc0…`）上重算：'
'① **「1218 张虚表」不是同质集合**：`dw(V-4)==COL` 的候选 1218 个中，仅 **1214** 个的 `dw(V)` 落在 `.text`；'
'余 4 个 `0x877000`/`0x877010`/`0x87b17c`/`0x87b18c` 全在 `.data`、槽数 **0**、在 `.text` 内被 dword 引用 **0** 次（正控 `0x7e8278` 4 次、`0x7e1f50` 5 次）'
'⇒ 这 4 个是**幻影记录**（16 B 形如 `c0000001 00000000 00000000 00800040`，`+0xc` 才是 COL `0x800040`），'
'故 1214 张真虚表与 1214 条 COL **双射**（单射与满射同时成立），「共用 COL 一例」在真虚表口径下**不存在**；'
'因果链：视图级 `mdisp!=0` 视图 **264**（含幻影）vs COL 记录级 **260**（真虚表口径）之差 **4** 即此 4 个幻影，而非「同一 COL 被 5 张真表共用」。'
'② **总槽数 14044 与主视图 9958 不受幻影影响**：幻影 0 槽；族数 954 / 主视图 954 / 主视图 slot≥3 **9958** / 全表 slot≥3 **10814** 与 R217 逐数一致（正控通过）。'
'③ **6 张 >256 表的父类用 BCD 数组后继项判定，6/6 PASS**：Unit/Infantry/Aircraft→Foot、Foot/Building→Techno、Techno→Radio。'
'**自错 E6**：BCD 记录是 **24 B**（pTD/ncb/PMD 三 int/attrs），此前把 `+0x18` 当作 pCHD 字段，实测那是**下一条记录的 +0**（`+0` 为合法 pTD 的比例 94/94，改按 0x1c 步长则为 0/94）；'
'pBCA 是 **4 B 指针数组**、元素本身即 BCD 地址，「内联记录」写法作废。'
'④ **464 个 slot≥256 槽的归因**（相对直接父类同槽）：**cov 294 / diff 67 / oob 103**，父类范围内覆盖率 **294/361 = 81.44%**；'
'oob 恰等于 `sum(max(0, n − max(par_n,256)))`（校验 PASS），即超出父类槽数的尾部必为本类新增；'
'464 个目标去重 **170**、全部落 `.text`、在本表低 256 槽内重复仅 **1** 个，且与全部 1214 张表的任意子段做最大公共前缀搜索得 **0 条 ≥12 的拼接候选**（反控：随机 10 对无关表最大公共前缀 0）'
'⇒ 高槽段**不是**把另一张 vftable 拼接进来，也不是父类表整体复制。'
'⑤ **disp 扫描定稿口径**：全 `.text` 线性 sweep（遇非法字节前进 1 B）解码 **1,394,120** 条指令（末端 `0x7e0ffd`），'
'`call/jmp` 且 `[reg+disp]`（无索引、排除 esp）位点 **18,930**；`disp==0x2c` **1114**、`disp==0` **819**、`disp==0x48` **930**；'
'slot≥256（`disp≥0x400`）**931** 位点 / **91** 个不同 s / 非 4 对齐 **0**；其中 **925** 落在 UnitClass 槽域（<344），**6** 个 s∈{479,480,481,482,2224418} 超出最大槽数 344 须另行定性；'
'正控 `0x41021a`（`call dword ptr [edx+0x2c]`）命中。**口径警告**：`s≥256 位点 931` 与 R215 的「931 处 +0x48 消费位点」是**巧合**（`disp==0x48` 本轮实测 930），两数不可互引。'
'**边界**：本条仍不改 statement 与 grade；`coverage.tsv` / `function_atlas.tsv` 仍不可读。')
ck('W6 无 tab', '\t' not in APP)
ck('W7 无 CR/换行', '\r' not in APP and '\n' not in APP)
ck('W8 无双引号', '"' not in APP)
ck('W9 以句号结尾且 >1200 B', APP.endswith('。') and len(APP.encode())>1200, len(APP.encode()))
newlim=f29[4]+APP
ck('W10 lim 只增不减', len(newlim.encode())>47453, len(newlim.encode()))
f29[4]=newlim
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
nb=newtxt.encode('utf-8')
ck('W11 新字节 = 旧 + 追加段', len(nb)==len(raw)+len(APP.encode()), (len(nb),len(raw)+len(APP.encode())))
ck('W12 新 CR == 0', nb.count(b'\r')==0)
ck('W13 除 F29 外 56 行逐字节不变',
   all(lines[i]=='\t'.join(rows[i]) for i in range(57) if rows[i][0]!='F29'))
ck('W14 F29 第 4 列（证据）未变', rows[[i for i,r in enumerate(rows) if r[0]=='F29'][0]][3]==f29[3])
if fails:
    print('[ABORT] fails=%r'%fails); raise SystemExit(1)
os.makedirs(NEWD,exist_ok=True)
assert not os.path.exists(NEW)
with open(NEW,'wb') as f: f.write(nb)
chk=open(NEW,'rb').read()
assert chk==nb
print('[写入] %s  bytes %d -> %d  sha %s -> %s'%(NEW,len(raw),len(chk),h[:16],hashlib.sha256(chk).hexdigest()[:16]))
json.dump(dict(old_sha=h,new_sha=hashlib.sha256(chk).hexdigest(),old_bytes=len(raw),new_bytes=len(chk),
  app_bytes=len(APP.encode())),open(ROOT+'/_r218/p1.json','w'),indent=1)
