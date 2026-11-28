# R213 EX2 — onlysec TD 的引用面与 vftable 归属复算（role=exec）

工作目录 /home/t628/projects/ra2-campaign-forge
目标 ra2bench/gamemd.exe（PE32，ImageBase 0x400000）
允许写盘路径仅限：_r213/x2.py、_r213/x2.json、_r213/x2_out.txt

## 任务

R207 曾列出「13 个 onlysec pTD」，R211 又数出 34 个，两数不一致。本轮要一次性把 onlysec TD 的口径固定下来，并给出每个 onlysec TD 的引用面。全部自己从字节重算，不要引用历史轮次数字。

可用工具库 _r185/pe185.py：P.RAW 原始字节、P.B[段名] 段表、P.dw(va)、P.where(va)、P.cstr(va)、P.r2o(va)。

## 结构口径（先自行验证，不成立就写 UNKNOWN）

- TD 类型描述符：+0 pVFTable、+4 spare 0、+8 内联名字（.?A 开头、@@ 结尾）
- COL 类头记录 20 字节：+0 signature、+4 mdisp、+8 cdOffset=0、+12 pTD、+16 pCHD
- CHD 16 字节：+0 signature、+4 attributes、+8 numBaseClasses、+12 pBCA；BCA 元素是 BCD（24 字节）
- BCD 布局：+0 pTD、+4 numContainedBases、+8 mdisp、+12 pdisp、+16 vdisp、+20 attributes

## 必须实测并打印 + 写入 JSON

- B1 全部 TD 总数，以及按名字前缀分类：.?AV / .?AU / 其他，三数之和须等于总数
- B2 被至少一条 COL 的 +12 引用的 TD 数（记为 REF）
- B3 onlysec 集 = TD 全集 减 REF，给出条数、按前缀分布
- B4 onlysec 里被 BCA 引用的：给出每条 (TD 地址, 名字, 被 BCA 引用的次数, 引用它的 CHD 个数)
- B5 onlysec 里完全不被 BCA 引用的条数与名单
- B6 对每个 BCA 引用次数为 1 的 onlysec TD，给出那唯一一条 BCD 的完整 6 个 dword 原始值，以及它所属的 CHD 地址与该 CHD 的类名（own 记录名）
- B7 判断口径分歧：如果用「名字前缀 .?AU」当 onlysec 判据会得多少条，如果用「不在 REF」会得多少条，两数各是多少
- B8 正反控一：把 REF 判据放宽为「TD+8 名被任一 COL 名相等」后 onlysec 条数
- B9 正反控二：把 TD 枚举的 +4==0 约束去掉后 TD 总数

## 纪律

1. 一条命令跑完全部条目，stdout 同时 tee 到 _r213/x2_out.txt；每条打出实测值与 PASS/FAIL。
2. 不需要指令级反汇编；严禁对整段 .text 开 md.detail=True。
3. 数字必须实测，禁止预估；算不出写 UNKNOWN 并说明卡点。
4. 回复正文给 B1 到 B9 实测值表。
