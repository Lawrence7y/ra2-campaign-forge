# -*- coding: utf-8 -*-
"""R221 p6：FACT_INDEX V602 -> V603，只在 F29.limitations 追加 R221 实测段。"""
import hashlib, os, json
ROOT='/home/t628/projects/ra2-campaign-forge'; TIER=ROOT+'/lead/next_re_20261117_r14'
OLD=TIER+'/R17_R131_FACTINDEX_V602/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V603'; NEW=NEWD+'/FACT_INDEX.tsv'
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
raw=open(OLD,'rb').read(); h=hashlib.sha256(raw).hexdigest()
ck('W1 旧 V602 290024 B / sha 87ed9228', len(raw)==290024 and h.startswith('87ed9228'), (len(raw),h[:16]))
ck('W2 旧 CR == 0', raw.count(b'\r')==0)
txt=raw.decode('utf-8'); lines=txt.split('\n')
ck('W3 57 行 + 末段空', len(lines)==58 and lines[-1]=='', len(lines))
rows=[l.split('\t') for l in lines[:57]]
ck('W4 每行 5 列', all(len(r)==5 for r in rows))
f29=[r for r in rows if r[0]=='F29'][0]
L0=len(f29[4].encode()); ck('W5 F29 lim > 59000 B', L0>59000, L0)
APP=('**【R221 实测·ADPCM 编解码常量区全解：两块 9056 B 镜像同一 + 双解码器纯地址重定位 + 律 D/律 S 双双 1424/1424；statement 与 grade 均不改】** '
'R221 用 `_r221/m2_final.py`（**36 断言 / 0 FAIL**，输出 `_r221/m2_out.txt`，正反控内建）在现盘 `ra2bench/gamemd.exe`（sha256 `73201cc0…f3fcf67476`）上重算：'
'① **常量区是「一套 ADPCM 解码常量表整块复制两份」**：块1 `[0x8759b4,0x877d14)` 与块2 `[0x879b30,0x87be90)` 各 **9056 B** '
'（差分表 D **5696** + 状态表 S **2848** + 抖动表 A **256** + 抖动表 B **256**）**逐字节相同**；块间 `[0x877d14,0x879b30)` 共 **7708 B 全 `0x00`**；'
'块1 尾后 16 B 全 0，块2 尾后为 `94957f00000000002e3f415674797065`（`.` 起 `?AVtype_` 即 RTTI 名串）。'
'块1 的 A/B 分别与块2 的 `0x87bc90`/`0x87bd90` **逐字节相同**。⇒ R220 只发现了块2 一侧，本轮补齐块1 并证明二者同源。'
'② **律 D / 律 S 双双 1424/1424 闭合，R220「余 22 块未解」关闭**：索引口径为**字节偏移 `S = 32m | 2n`**（m=0..88 为 step 下标、n=0..15 为 nibble）。'
'律 D `dword[16m+n] = ±((s>>3) + [n&4]s + [n&2](s>>1) + [n&1](s>>2))`（`s=IMA[m]`，`n>=8` 取负）⇒ **1424/1424、0 残留**；'
'律 S `word[16m+n] = 32*clamp(m+ADJ[n&7],0,88)`（`ADJ=(-1,-1,-1,-1,2,4,6,8)`）⇒ **1424/1424、0 残留**，min `0` / max `2816`(=32×88) / 全部 32 的倍数。'
'两副本同值：律 S@`0x876ff4` = 1424/1424、律 D@`0x8759b4` = 1424/1424。'
'③ **R220 的「floor 式只命中 44/89、余 22 块」是口径错，不是数据缺失**：R220 用的 `floor(s*(2a+1)/8)`（整体乘除）在差分表命中 **1020/1424**，'
'而移位式命中 **1424/1424**；floor 式**精确块数 = 44/89** 与 R220 记的 44 一致（数字没算错，是口径不对）。'
'代数判据：设 `s=8q+r`、`2a+1 = 1 + 8[a>=4] + 4[(a>>1)&1] + 2[a&1]`，则两式对全 8 个 `a` 相等 ⟺ '
'`floor(r(2a+1)/8) == [a>=4]r + [(a>>1)&1](r>>1) + [a&1](r>>2)` ⟺ **`r = s%8 ∈ {0,1,2,4}`**；'
'实测该判据与「逐块 8 项全等」**89/89 判决一致**；失配 residue 分布 `r=3`:**11** / `r=5`:**10** / `r=6`:**13** / `r=7`:**11**，合计 **45 = 89−44**。'
'⇒ R220 待办①「余 22 块的舍入口径」**作废**（22 是 floor 式放宽口径下的余数，与移位式无关）。'
'④ **打包索引 `S=32m|2n` 的结构性证明（6 条内建）**：`32m|2n == 32m+2n` 全域成立；反控 `33m|2n` **必进位冲突** ⇒ 乘数 32 是结构性必需；'
'字索引 `S/2 = 16m+n`、dword 索引 `2S/4 = 16m+n`；状态值 `32m` **低 5 位恒 0** ⇒ `or dl,2n` 不破坏 m 部；'
'解码器 `mov eax,dword[ebx]`(+0) / `mov dx,word[ebx+4]`(+4) 读 `S`，`or dl,byte[ebx+0x87bc90]` / `[ebx+0x87bd90]` 写回 bit1..4，'
'`0x7c75b4 pop ecx / 0x7c75b5 shr ecx,1 / 0x7c75b7 and ecx,7 / 0x7c75ba jmp [ecx*4+0x7c7758]` 为 8 分支 nibble 取值。'
'⑤ **双解码器 `0x7c6808`（块1）vs `0x7c7428`（块2）：逐字节差 = 纯表地址重定位**：长度 **428 / 427 B**、差分段 **26**；'
'其中 **25 个 2 字节段** = 4 组表地址重定位，计数 **8/8/4/4**（`0x59b4→0x9b30` / `0x6ff4→0xb170` / `0x7b14→0xbc90` / `0x7c14→0xbd90`）'
'+ 第 **25** 个为**跳转表地址** `0x6b38→0x7758`，其偏移 **0xc20** 恰等于**函数体偏移** `0x7c7428−0x7c6808 = 0xc20`，且两跳转表 8/8 项逐项差 **0xc20**；'
'剩 1 个 **15 字节段**（`0x7c69a4` vs `0x7c77bd`）为尾声不同（块1 版 `5b5d89431466895322 8b450c 5a595b5f5ec9c3` 写回状态，块2 版 `8d4900 83ed0c 55` 进对齐分支）。'
'归属：块1 解码器引用块1 表 **8+8+7+8**、块2 解码器引用块2 表 **24+24+21+24**，**交叉引用 0 条**。'
'⑥ **抖动表是一对互转置表（非单表）**：A=`0x87bc90` 满足 `A[i]==2*(i&15)` **256/256** ⇒ **低半字节出口**（decoder `mov bl,cl`）；'
'B=`0x87bd90` 满足 `B[i]==2*(i>>4)` **256/256** ⇒ **高半字节出口**（decoder `shr ecx,0x10` / `mov bl,ch`）；'
'`B == A 转置`、`A != B`、逐项差 **240/256**（对角 16 项相同）。⇒ R220 的「第 r 行全 2r」只描述了 B 表的一半视角。'
'⑦ **引用计数补齐（R220 只记块2）**：`0x8758c4`=**3** / `0x8758d4`=**0**（未被引用的重复常量） / `0x8758e4`=**3** / `0x8759b4`=**8** / '
'`0x876ff4`=**8** / `0x877b14`=**7** / `0x877c14`=**8** / `0x879b30`=**24** / `0x87b170`=**24** / `0x87bc90`=**21** / `0x87bd90`=**24**；'
'`.text` 逐字节 resync 共 **1,394,186** 条（rawsize 口径）。块1:块2 = 1:3，因块2 解码器循环体被编译器**展开 3 份**'
'（`0x7c7428` / `0x7c77f0` / `0x7c7bc0` 三段同构），块1 只 1 份 —— R220 的 24/24/21/24 与块1 的 8/8/7/8 因此不是矛盾。'
'⑧ **反控 5 条**：I1 律 S 倍数 32→8 ⇒ <1424；I2 基址右移 2（`0x87b172`）⇒ **564/1424**；I3 clamp 上界 88→87 ⇒ **1376/1424**；'
'I4 律 D 符号改按 `(n&7)>=4` ⇒ **713/1424**；I5 符号阈值 `n>=7` ⇒ **1335/1424**。'
'⑨ **跨家族 / 自错**：card A `#578`（hy4 exec **9 回合 / 4.65′**，无超时）9 组全项与主会话数值一致；'
'审计 `#579`（deepseek audit **12 回合 / 4.87′** succeeded）3 条差异**全部成立并已采纳**：'
'P1 卡面第 9 项写 `0x8759b4=0`（实测 **8**，主会话笔误，与同卡第 2/3/5 项自相矛盾）；'
'P2 K2 的 12 依赖未写明的「倍数 32→8」（712 项模型倍数 32 命中 **12**、1424 项模型命中 **60**、倍数 8 时两模型皆 **12**）⇒ 该控制作废；'
'P3 3360 B 块 = 状态表 2848 + A 256 + B 256，抖动表**在块内**，当纯状态表会多算 512 B（本轮按 9056 B 整块表述）。'
'另审计独立指出 `.rdata` 上界 `0x812000` 与 `.data` 起点**零间隙相接**，闭区间判断会把常量区错判进 `.rdata`；本项目 `_r185/pe185.py` 用半开区间，实测正确。'
'自错 5 条 **0 条进结论**：E1 `m1_pack.py` 断言「2 字节段 24 个」实为 **25**（第 25 个是跳转表 `0x6b38→0x7758`）；'
'E2 `ADJ=IDX[4:]` 只取 4 项致 `ADJ[n&7]` 越界抛 `IndexError`；E3 B4 判据把 q 部也放进残差比较致 35 块误判；'
'E4 C3 钳下界项数预期 4 实为 **8**（`m=0` 且 `n&7∈0..3`，即 n∈{0,1,2,3,8,9,10,11}）；E5 同 P1。'
'**边界**：本条不改 F29 的 statement 与 grade；`coverage.tsv` / `function_atlas.tsv` 仍不可读；'
'编码器 nibble 选择律、`0x7c7371` 参数字义、块2 三段展开的精确边界仍未取得。')
ck('W6 无 tab', '\t' not in APP)
ck('W7 无 CR/换行', '\r' not in APP and '\n' not in APP)
ck('W8 无双引号', '"' not in APP)
ck('W9 以句号结尾且 >4000 B', APP.endswith('。') and len(APP.encode())>4000, len(APP.encode()))
newlim=f29[4]+APP
ck('W10 lim 只增不减', len(newlim.encode())>L0, len(newlim.encode()))
f29[4]=newlim
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'; nb=newtxt.encode('utf-8')
ck('W11 新字节 = 旧 + 追加段', len(nb)==len(raw)+len(APP.encode()), (len(nb),len(raw)+len(APP.encode())))
ck('W12 新 CR == 0', nb.count(b'\r')==0)
ck('W13 除 F29 外 56 行逐字节不变', all(lines[i]=='\t'.join(rows[i]) for i in range(57) if rows[i][0]!='F29'))
if fails: print('[ABORT] %r'%fails); raise SystemExit(1)
os.makedirs(NEWD,exist_ok=True); assert not os.path.exists(NEW)
open(NEW,'wb').write(nb); chk=open(NEW,'rb').read(); assert chk==nb
print('[写入] %s bytes %d -> %d sha %s -> %s'%(NEW,len(raw),len(chk),h[:16],hashlib.sha256(chk).hexdigest()[:16]))
json.dump(dict(old_sha=h,new_sha=hashlib.sha256(chk).hexdigest(),old_bytes=len(raw),new_bytes=len(chk)),
          open(ROOT+'/_r221/p6.json','w'),indent=1)
