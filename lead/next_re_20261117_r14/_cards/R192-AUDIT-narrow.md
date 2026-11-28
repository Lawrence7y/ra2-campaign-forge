# 卡 R192 跨家族审计（窄卡，只读复核，deepseek）

## 角色与边界
只读复核，最多 14 回合，不要跑满。不得修改任何文件。
禁止碰 R14_COMMON.md / LEAD_LOCK / STATUS_BOARD.md / FACT_INDEX* / R17_LEAD_BASELINE。
可用 _r185/pe185.py（RAW / B / dw / where / r2o / cstr）。
项目根 /home/t628/projects/ra2-campaign-forge，二进制 ra2bench/gamemd.exe 只读。
OOM 红线：不要对整段 .text 开 detail 的 disasm。

## 枚举口径（已多轮复核，直接用）
COL：.rdata/.data 两段里连续 5 dword 满足 d0 in {0,1}、d2 == 0、d3 落 .data、d4 落 .rdata、
且 d3+8 是 .?A 开头 @@ 结尾的修饰名。字段 COL[0]=mdisp COL[1]=pTD COL[2]=pCHD COL[3]=name。
应得 1214 条。vtable：某 dword 落 .text 且其前 4 字节是 COL 地址 ⇒ 表头，应得 1214 张。
槽数 = 从表头起连续 dword 落 .text 的前缀长度，合计 14044。按名分组 954 组。

## 只审两条（各一次命令跑完）
A1 非主表（COL.mdisp != 0，共 260 张）的槽合计 1318，其中「调整器」= 起始 4 字节
   83 6C 24 04 或 81 6C 24 04，其余为「直接槽」，应得 305 + 1013。
   请自己数这三个数，并说明你数出什么。
A2 这 1013 个直接槽里，逐个找「同 COL 名、不同表、且该槽号在兄弟表里也存在」的兄弟，
   取表地址最小的那张；分类为：
   NOSIB（无兄弟表有该槽号）/ SAME（值相同）/ 其余（值不同）。
   主会话实测 = NOSIB 478、SAME 0、其余 535。
   请给出你的三个数，并对「其余」那 535 个再做一步：把两边的目标地址各自跟随
   无条件跳转（E9 rel32 / EB rel8 / FF 25 绝对间址，最多 8 跳）后，有多少对落到同一地址。
   主会话实测 = 0 对。请给你的数。

## 一条反控
R1 把「同 COL 名」换成「同 pTD 名字相同」作为兄弟判据，A2 的三个数各变成多少？
   （说明：pTD 是 COL 的第二个 dword；同一个 pTD 会被同一类的多个层共用。）

## 输出
- 写 _r192/audit_r192_narrow.txt，文本里分「成立 / 不成立（给数）/ 没测（给原因）」三档。
- 结论里必须给出你自己跑出的三组数，不要引用我给的数。
