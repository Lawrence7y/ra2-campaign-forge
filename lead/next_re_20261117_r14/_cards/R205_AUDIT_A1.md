# R205-AUDIT-A1 — 只读复核 R205 主交付的 6 条主张（跨家族审计）

## 角色
你是只读审计员。任务不是重算全部，而是攻击下面 6 条主张，逐条给 PASS 或 FAIL 加你自己的证据数字。

## 输入（只读）
- /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
- 公共映射 /home/t628/projects/ra2-campaign-forge/_r185/pe185.py（导出 P.B、P.RAW、P.dw、P.cstr、P.where）
- 主会话脚本：可读、可跑，但不得修改
  - /home/t628/projects/ra2-campaign-forge/_r205/m7_final.py （定稿，22 断言）
  - /home/t628/projects/ra2-campaign-forge/_r205/m8_d1i.py （D1i 反例定位）
  - /home/t628/projects/ra2-campaign-forge/_r205/m7_final.json

## 待攻击的 6 条主张

A1（结构级）gamemd.exe 的 CHD 记录是 40 字节：
+0 恒 0；
+4 attributes 取值只在 {0,1,5}；
+8 numBaseClasses；
+12 pBCA 全在 .rdata；
+16 起 20 字节是一条完整 COL 记录（sig==0、mdisp==0、cdOffset==0、pTD 在 .data、pCHD==自身 CHD 地址）。
R204 把 CHD 当 16 字节，是截断。

A2（判据级）该内嵌 COL 就是 1214 个视图 COL 之一，且它是该 CHD 组内唯一 mdisp==0 的视图。
所以「类的 RTTI 块自包含」有了第三条独立证据链（前两条：R203 名字判据、R204 pCHD 指针判据）。

A3（口径级，最容易被推翻的一条）R203 的「954 组头」与 R205 的「954 内嵌主对象 COL」不是同一批 954：
交集仅 860；差的 94 恰是「视图数大于 1 的多视图类」。
原因：组头是组内 mdisp 最大的首视图，内嵌 COL 是 mdisp==0 的末视图。
若这条被你推翻，主会话整段结论要重写 —— 请重点攻。

A4（判据失败，否定结果）COL.sig 字段在本镜像无判别力：1214 条 COL 的 sig 全部为 0。
R203/R204 沿用 sig in (0,1,2) 作为形态约束是保守的、非充分条件。

A5（充要条件）去重 BCD 中 mdisp==0 共 978 条，分解为：
956 条 pTD 属于 954 个 CHD 类自有 pTD（其中 2 个 TD 各有 2 条记录）；
22 条 pTD 不属于任何 954 类，其名字全部不在 954 类名集内，其中 17 条是 .?AU 接口前缀；
且这些 pTD 从不出现在任何 COL 的 pTD 字段（即它们没有 vftable 视图），却在 BCA 中被引用 474 次。

A6（主会话自错，请你判断抓得对不对）主会话已撤回「组内 mdisp 严格递减 954/954」这一说法。
实测 260 个组内相邻对中有 3 个非严格递减，逐条为：
.?AVOverlayClass@@ 地址 0x807598，序列 [12,4,8,0]；
.?AVSmudgeClass@@ 地址 0x809848，序列 [12,4,8,0]；
.?AVTerrainClass@@ 地址 0x80c370，序列 [4,12,8,0]。
请独立复算这三个类名与它们的 mdisp 序列，确认或推翻。这三条是主会话当场抓到的自错，你要判断「抓得对不对」，
并且回答：除了这 3 条，有没有主会话漏掉的其它非递减反例？

## 输出
写到 /home/t628/projects/ra2-campaign-forge/_r205/audit_a1/ ：
- verdict.tsv：制表符分隔，表头为 claim / verdict / my_value / main_value / note，6 行（A1..A6）
- REPORT.md：逐条论证，加你认为主会话最可能错在哪
- 可选 attack.py

## 纪律
- 只读。不许改任何 _r 系列目录、台账、R14_COMMON.md、lead/LEAD_LOCK、STATUS_BOARD.md。只写 _r205/audit_a1/。
- 工具只用于读与算；不要派子代理。
- 你可以直接跑主会话脚本，但必须另写自己的判据再对一次数，不许只跑别人的脚本就下 PASS。
- 3 处以上数字不符才算整体 FAIL；单条不符按条判。
- 卡面与报告里不要使用反引号字符。
