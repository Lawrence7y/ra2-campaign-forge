# -*- coding: utf-8 -*-
"""R221 p4：STATUS_BOARD 第 221 轮（CR 保持 0，行数 <= 300，>= 260 则先归档）。"""
import os, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'; BASE=ROOT+'/R17_LEAD_BASELINE'
T=ROOT+'/lead/next_re_20261117_r14'
P=T+'/STATUS_BOARD.md'; A=T+'/BOARD_ARCHIVE.md'
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r221_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted')
b0=bak(P,'BOARD'); a0=bak(A,'ARCH')
assert b0.count(b'\r')==0 and a0.count(b'\r')==2952
n0=b0.count(b'\n'); print('board lines before =',n0)
assert n0<260, n0
SEC="""
## 第 221 轮（2026-11-28）ADPCM 常量区全解：两块 9056 B 镜像完全同一 + 双解码器差 = 纯表地址重定位 + 律 D/律 S 双双 1424/1424（R220「余 22 块」关闭）

- **常量区 = 两块 9056 B 完全同一（本轮结构主证）**：块1 `[0x8759b4,0x877d14)`、块2 `[0x879b30,0x87be90)` 各 **9056 B** = 差分表 D 5696 + 状态表 S 2848 + 抖动表 A 256 + 抖动表 B 256，**逐字节相同**；块间 `[0x877d14,0x879b30)` 共 **7708 B 全 0x00**；块1 尾后 16 B 全 0，块2 尾后为 `94957f00000000002e3f415674797065`（`.` 起 `?AVtype_` RTTI 名串）。块1 的 A/B 与块2 的 `0x87bc90`/`0x87bd90` 逐字节相同。⇒ 同一套 ADPCM 解码常量表**整块复制两份**、各配一个同构解码器；R220 只发现块2 一侧。
- **律 D / 律 S 双双 1424/1424**：索引口径 **字节偏移 `S = 32m | 2n`**（m=0..88 为 step 下标、n=0..15 为 nibble）。律 D：`dword[16m+n] = ±((s>>3) + [n&4]s + [n&2](s>>1) + [n&1](s>>2))`，`s=IMA[m]`，`n>=8` 取负 ⇒ **1424/1424、0 残留**；律 S：`word[16m+n] = 32*clamp(m+ADJ[n&7],0,88)`，`ADJ=(-1,-1,-1,-1,2,4,6,8)` ⇒ **1424/1424、0 残留**，min 0 / max 2816(=32×88) / 全部 32 的倍数；两副本同值（律 S@`0x876ff4`、律 D@`0x8759b4` 皆 1424/1424）。
- **R220「floor 式只命中 44/89、余 22 块未解」= 口径错，不是数据缺失**：floor 式 `floor(s*(2a+1)/8)` 在差分表命中 **1020/1424**，移位式 **1424/1424**；floor 式**精确块数 44/89** 与 R220 记的 44 一致（数字没算错，是口径不对）。代数判据：设 `s=8q+r`，`2a+1 = 1 + 8[a>=4] + 4[(a>>1)&1] + 2[a&1]`，两式对全 8 个 a 相等 ⟺ `floor(r(2a+1)/8) == [a>=4]r + [(a>>1)&1](r>>1) + [a&1](r>>2)` ⟺ **`r = s%8 ∈ {0,1,2,4}`**；实测该判据与「逐块 8 项全等」**89/89 判决一致**；失配 residue 分布 r=3:11 / r=5:10 / r=6:13 / r=7:11，合计 **45 = 89−44**。⇒ R220 待办①**关闭**。
- **打包索引 `S=32m|2n` 结构性证明（6 条）**：`32m|2n == 32m+2n` 全域成立；反控 `33m|2n` 必进位冲突 ⇒ 乘数 32 结构性必需；字索引 `S/2 = 16m+n`、dword 索引 `2S/4 = 16m+n`；状态值 `32m` 低 5 位恒 0 ⇒ `or dl,2n` 不破坏 m 部；解码器 `mov eax,dword[ebx]`(+0) / `mov dx,word[ebx+4]`(+4) 读 S，`or dl,byte[ebx+0x87bc90]` / `[ebx+0x87bd90]` 写回 bit1..4，`0x7c75b4 pop ecx / 0x7c75b5 shr ecx,1 / 0x7c75b7 and ecx,7 / 0x7c75ba jmp [ecx*4+0x7c7758]` 为 8 分支 nibble 取值。
- **双解码器 `0x7c6808`（块1）vs `0x7c7428`（块2）：逐字节差 = 纯表地址重定位**：长度 **428 / 427 B**、差分段 **26**；**25 个 2 字节段** = 4 组重定位计数 **8/8/4/4**（`0x59b4→0x9b30` / `0x6ff4→0xb170` / `0x7b14→0xbc90` / `0x7c14→0xbd90`）+ 第 **25** 个为**跳转表地址** `0x6b38→0x7758`，其偏移 **0xc20** 恰等于函数体偏移 `0x7c7428−0x7c6808`，且两跳转表 8/8 项逐项差 **0xc20**；剩 1 个 **15 字节段**（`0x7c69a4` vs `0x7c77bd`）为尾声不同。归属：块1 解码器引用块1 表 **8+8+7+8**、块2 解码器引用块2 表 **24+24+21+24**，**交叉引用 0 条**。
- **抖动表是一对互转置表（非单表）**：A=`0x87bc90` 满足 `A[i]==2*(i&15)` 256/256 ⇒ **低半字节出口**；B=`0x87bd90` 满足 `B[i]==2*(i>>4)` 256/256 ⇒ **高半字节出口**；`B == A 转置`、`A != B`、逐项差 **240/256**（对角 16 项相同）。R220 的「第 r 行全 2r」只描述了 B 表的一半视角。
- **引用计数补齐（R220 只记块2）**：`0x8758c4`=3 / `0x8758d4`=**0** / `0x8758e4`=3 / `0x8759b4`=**8** / `0x876ff4`=8 / `0x877b14`=**7** / `0x877c14`=**8** / `0x879b30`=24 / `0x87b170`=24 / `0x87bc90`=21 / `0x87bd90`=24；`.text` 逐字节 resync **1,394,186** 条（rawsize 口径）。块1:块2 = 1:3，因块2 解码器循环体被**展开 3 份**（`0x7c7428` / `0x7c77f0` / `0x7c7bc0` 三段同构），块1 只 1 份。
- **反控 5 条**：I1 律 S 倍数 32→8 ⇒ <1424；I2 基址右移 2（`0x87b172`）⇒ **564/1424**；I3 clamp 上界 88→87 ⇒ **1376/1424**；I4 律 D 符号改按 `(n&7)>=4` ⇒ **713/1424**；I5 符号阈值 `n>=7` ⇒ **1335/1424**。
- **跨家族**：card A `#578`（hy4 exec **9 回合 / 4.65′**，无超时）9 组全项与主会话一致；审计 `#579`（deepseek audit **12 回合 / 4.87′** succeeded）3 条差异**全部成立并已采纳**：P1 卡面第 9 项写 `0x8759b4=0`（实测 **8**，主会话笔误）、P2 K2 的 12 依赖未写明的「倍数 32→8」⇒ 该控制作废、P3 3360 B 块 = 状态 2848 + A 256 + B 256（抖动表在块内，当纯状态表会多算 512 B）。审计另指出 `.rdata` 上界 `0x812000` 与 `.data` 起点零间隙，闭区间判断会把常量区错判进 `.rdata`；本项目半开区间实测正确。
- **自错 5 条（0 条进结论）**：E1「2 字节段 24 个」实为 **25**（第 25 个是跳转表 `0x6b38→0x7758`）；E2 `ADJ=IDX[4:]` 只取 4 项致越界；E3 B4 判据把 q 部放进残差比较致 35 块误判；E4 C3 钳下界项数预期 4 实为 **8**；E5 同 P1。
- **收口**：R14 §2.229 CR **1081**（1949638→1957889 B）、GOAL §1279 CR **337**（5479361→5485245 B）、本段 QX CR **137**（1522365→1527799 B）、本段 CR **0**（244→%d 行，**< 260 不触发归档**）。判据脚本 `_r221/m2_final.py`（**36 断言 / 0 FAIL**）、`_r221/m1_pack.py`（19 断言，2 FAIL 已定性为口径错）。
"""
new=b0+SEC.encode('utf-8')
new=new.replace(b'244\xe2\x86\x92%d', b'244\xe2\x86\x92') # placeholder guard, replaced below
# 行数占位符替换
body=b0+SEC.encode('utf-8')
assert body.count(b'\r')==0
nl=body.count(b'\n')
body=body.replace(b'244\xe2\x86\x92%d', ('244\xe2\x86\x92%d'%nl).encode())
assert body.count(b'\n')==nl
assert nl<=300, nl
open(P,'wb').write(body); chk=open(P,'rb').read()
assert chk.startswith(b0) and chk==body and chk.count(b'\r')==0
print('[OK] BOARD %d -> %d lines, CR=%d, ARCH CR=%d'%(n0,chk.count(b'\n'),chk.count(b'\r'),open(A,'rb').read().count(b'\r')))
