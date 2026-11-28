# R205-EXEC-X1 — 独立重算 RTTI 类块布局（只读，不写台账）

## 背景
主会话本轮在 gamemd.exe 上取得一条新的二进制结构事实（R205 主交付候选）：
每类的 RTTI 信息是一个自包含块，CHD 记录不是 16 字节而是 40 字节，其 +16 起点处嵌着该类主对象视图的 COL 记录。
你的任务是独立重算，不要相信本卡的任何数字，全部自己算。

## 输入（只读）
- /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- 可复用公共映射：/home/t628/projects/ra2-campaign-forge/_r185/pe185.py
  该模块导出 P.B（段表字典）、P.RAW（整个文件字节）、P.dw(va)、P.cstr(va,max)、P.where(va)。

## 必须自己实现的前置（与主会话同判据）
1. 遍历 .rdata 与 .data 的 dword，按以下四条同时成立收集 COL，键为地址：
   sig in (0,1,2)；w[i+2]==0；where(w[i+3])=='.data'；where(w[i+4])=='.rdata'；
   且 cstr(w[i+3]+8,400) 以 .?A 开头、以 @@ 结尾。
2. 收集 vftable 起点：该 dword 落 .text，且 dw(addr-4) 在 COL 集合内。
3. 按 COL 的第 5 个 dword（偏移 +16，即 pCHD 字段）分组，组键集合就是 CHD 地址集合。

## 要实测并逐条给出数字的 8 项

| 编号 | 断言 | 期望值（不要照填，自己算） |
|---|---|---|
| X1 | COL 记录数 | ? |
| X2 | vftable 起点数 | ? |
| X3 | CHD（pCHD 去重）数 | ? |
| X4 | 对每个 CHD 地址 a，以下五条同时成立的个数：dw(a+16)==0；dw(a+20)==0；dw(a+24)==0；where(dw(a+28))=='.data'；dw(a+32)==a | ? |
| X5 | 把 a+16 起的 20 字节当作一条 COL 记录（sig/mdisp/cdOffset/pTD/pCHD 五个 dword）解读时，该地址是否在 X1 的 COL 集合内（个数） | ? |
| X6 | X5 命中的那些内嵌 COL，其 pCHD 字段是否等于宿主 CHD 地址（个数） | ? |
| X7 | 每个 CHD 组内 mdisp==0 的 COL 个数分布（字典形式） | ? |
| X8 | 去重 BCD（BCA 引用的 24 字节记录）中 mdisp==0 的总数；其中 pTD 属于 954 个 CHD 类自有 pTD 的个数；不属于的个数 | ? |

BCD 读取口径：对每个 CHD 地址 a，numBaseClasses=dw(a+8)，pBCA=dw(a+12)；
BCA 第 j 项 = dw(pBCA+4*j)，j 取 0..numBaseClasses-1；每项是一条 BCD 的地址。
BCD 字段：+0 pTD，+4 numContainedBases，+8 mdisp（有符号），+12 pdisp（有符号），+16 vdisp，+20 attributes。
类自有 pTD 取该 CHD 内嵌 COL 的 pTD 字段（即 dw(a+28)）。

## 三项反控（必须做，用来证明判据不是恒真）
- C1：5000 个随机 .rdata 地址，按 X4 的五元判据命中几次？
- C2：把 X4 整体错位 +4 字节（改看 a+20 / a+24 / a+28 / a+32 / a+36）后命中几次？
- C3：X8 中「不属于」的那批，其 pTD 的名字是否出现在 954 个类名集合里？逐条给名字。

## 输出
写到 /home/t628/projects/ra2-campaign-forge/_r205/exec_x1/ ：
- result.json：键名严格用 X1..X8，值就是实测数字（X7 用字典）
- REPORT.md：一张表（编号 / 实测值 / 你的判据一句话）、三项反控结果、以及你不同意主会话判据的地方
- recompute.py：可复跑，全部数字从文件算出

## 纪律
- 只读 gamemd.exe。不许改 R14_COMMON.md、lead/LEAD_LOCK、STATUS_BOARD.md、台账、以及 _r 系列目录下任何既有文件。只写 _r205/exec_x1/。
- 一条命令输出全部证据（检索+统计+校验一次完成），不要拆成多次单点命令。
- 内存红线：不许对整段 .text 开 md.detail=True 全量 disasm；本卡不需要反汇编。
- 结论允许打主会话的脸：若某项算出不同数，如实写你的数。禁止预估，禁止照抄本卡期望值。
