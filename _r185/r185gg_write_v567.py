#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 GG：V566 -> V567，继续只在 F01.limitations 追加 R185 第二段（子对象 vtable 语义 + 审计数字复算）。"""
import hashlib,io,os,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
OLD=os.path.join(TIER,'R17_R131_FACTINDEX_V566','FACT_INDEX.tsv')
NEWD=os.path.join(TIER,'R17_R131_FACTINDEX_V567'); NEW=os.path.join(NEWD,'FACT_INDEX.tsv')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
raw=open(OLD,'rb').read(); TXT=raw.decode('utf-8'); L=TXT.split('\n')
ck('X1 旧 V566 138,507 B / sha d3677f92…', len(raw)==138507 and hashlib.sha256(raw).hexdigest().startswith('d3677f92'), (len(raw),hashlib.sha256(raw).hexdigest()[:16]))
ck('X2 旧 CR == 0 / 56 段（55 行）', raw.count(b'\r')==0 and len(L)==56, (raw.count(b'\r'),len(L)))
rows=[l.split('\t') for l in L[:55]]
f01=[r for r in rows if r[0]=='F01'][0]
ck('X3 F01 limitations 7,612 B', len(f01[4].encode())==7612, len(f01[4].encode()))
APP=('**【R185 实测二·symbols.json 的 vtable_va 对这 12 条语义不同，且审计三条全域数字被本判据测反】** '
'`_r185/r185ee_audit_recheck.py`（**14 断言 0 FAIL**）与 `_r185/r185ff_subobj.py`（**6 断言 0 FAIL**）复算跨家族审计 #445 的全部「不符/越界」主张：'
'① 954 条 TD 名前缀实测 **.?AV 952 / .?AU 2**（两条是 `INIEntry@INIClass`、`INISection@INIClass`，属 struct 侧），'
'故「TD 名形如 .?AV<类名>@@」这句必须写成「.?A[VU]」，去前缀时不能只去 `.?AV` —— 只去 `.?AV` 会让这 2 条解出 None；'
'② 审计说「全域 RTTI 形 vtable 有 1215 个、mdisp≠0 共 231、mdisp==4 另 79 个」—— **1215 与 231 两条被本判据测反**：'
'按「`dword[vt]∈.text` ∧ `dword[vt−4]` 是合法 COL」实测全域 **1214**（= 总 COL 数），'
'mdisp≠0 的 vtable 实测 **260**（= 1214 − 954），其中 mdisp==4 的 **91**（= symbols 内 12 + symbols 外 79）；'
'三条里只有「另 79 个、无一是 Locomotion」成立（本判据实测 symbols 外 mdisp==4 恰 **79**，逐个类名全是 Classic 系而非 Locomotion）；'
'③ **本轮最重要的新事实**：那 12 个主 COL.mdisp==4 的 Locomotion 类，`symbols.json` 的 `vtable_va` 指向的是 '
'**ILocomotion 次对象 vtable**（`dword[vt−4]` 的 mdisp **=4**），而每个类还有一张同 pTD 的 `mdisp==0` vtable，'
'两者地址差 **恒为 +0xCC（12/12，无例外）**；两张表的 `.text` 槽数不同（`mdisp==0` 那张 12 个里 11 个是 **10** 槽、'
'TeleportLocomotionClass 是 **12** 槽，而 symbols.json 记 `vfunc_count` **50**）⇒ **12/954 条不能直取 `vtable_va` 当「类的主虚表」**，'
'引用 F29 那条「取 `mdisp==0` 主虚表的 slot1/slot2」规则时必须另取 `mdisp==0` 那张。'
'**边界**：本条仍只在本列追加；statement 与 grade 不动；审计的 1215/231 不复现的原因（虚表判据口径差，'
'例如是否要求 `dword[vt]` 落 `.text` 或是否含 `.data` 命中）本轮未穷举，登记为未取得。')
ck('X4 追加段无 tab / CR / LF / 双引号', '\t' not in APP and '\r' not in APP and '\n' not in APP and '"' not in APP)
ck('X5 追加段以句号结尾、长度 > 1000', APP.endswith('。') and len(APP.encode())>1000, len(APP.encode()))
f01[4]=f01[4]+APP
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
nb=newtxt.encode()
ck('X6 新体量 = 旧 + 追加段', len(nb)==138507+len(APP.encode()), (len(nb),138507+len(APP.encode())))
ck('X7 新 CR == 0', nb.count(b'\r')==0)
NL=nb.decode().split('\n'); NR=[l.split('\t') for l in NL[:55]]
ck('X8 新 55 行 / 5 列', len(NL)==56 and all(len(x)==5 for x in NR))
diff=[i for i in range(55) if NR[i]!=L[i].split('\t')]
ck('X9 变化行恰 F01（索引 1）', diff==[1], diff)
ck('X10 其余 54 行逐字节相同', all(NR[i]==L[i].split('\t') for i in list(range(0,1))+list(range(2,55))))
ck('X11 F01 三列未动', NR[1][1]==L[1].split('\t')[1] and NR[1][2]==L[1].split('\t')[2] and NR[1][3]==L[1].split('\t')[3])
ck('X12 旧段仍是新段前缀', NR[1][4].startswith(L[1].split('\t')[4]))
SHA=hashlib.sha256(nb).hexdigest()
ck('X13 新 sha != 旧 sha', SHA!=hashlib.sha256(raw).hexdigest(), SHA[:16])
if fails:
    print('★ fail-closed：%d 条未过，不写盘'%len(fails)); sys.exit(1)
os.makedirs(NEWD,exist_ok=True)
assert not os.path.exists(NEW)
open(NEW,'wb').write(nb)
ck('X14 回读 sha', hashlib.sha256(open(NEW,'rb').read()).hexdigest()==SHA, SHA[:16])
print('断言 %d / FAIL %d'%(n,len(fails)))
print('V567 = %d B / %s'%(len(nb),SHA))
print('F01 limitations 7612 -> %d (+%d)'%(len(NR[1][4].encode()),len(APP.encode())))
sys.exit(1 if fails else 0)
