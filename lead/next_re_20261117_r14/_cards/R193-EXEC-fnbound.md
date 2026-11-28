# 卡 R193 执行（hy4flash）：103 对「96 字节内无 ret」的完整函数边界分析

## 角色与边界
执行员。只读 gamemd.exe，不修改仓库里任何既有文件；只允许在 _r193/exec/ 下新建文件。
禁止碰 R14_COMMON.md / LEAD_LOCK / STATUS_BOARD.md / FACT_INDEX* / R17_LEAD_BASELINE / _r190.._r192。
可用 _r185/pe185.py 作 PE 映射（P.RAW / P.B / P.dw / P.where / P.r2o / P.cstr）。
可用 capstone（python3-capstone 已装）。
OOM 红线：禁止对整段 .text 开 detail=True 的 md.disasm；只对单个目标地址开
md.disasm(code_window, va) 且窗口 <= 512 字节，逐个处理、处理完即释放。

## 要回答的一个问题
R192 记录：1,013 个非 thunk 直接槽里，535 个可与兄弟表同槽号比对的对中，有 103 对
「两侧目标各自从入口起 120 字节窗口内都解不到 ret」（当时用 96 字节判 rslt，判为 inc）。
现在要把这 103 对做完整函数边界分析，给出「真正两侧都没有 ret 的对数」。

## 步骤（按顺序，全部在一个脚本里跑完，一条命令输出全部证据）
S1 复现 535 对。口径（照抄，不要改）：
  - COL 判据：5 连续 dword 满足 d0 in {0,1}、d2 == 0、d3 落 .data、d4 落 .rdata，
    且 d3+8 处是 .?A 开头、@@ 结尾的修饰名串。COL 键为 COL 起始 VA，字段
    [0]=mdisp [1]=pTD [2]=pCHD [3]=name。
  - vtable 判据：某 dword 落 .text 且其前 4 字节是某条 COL 的地址，则该位置是表头。
  - 槽数 = 从表头往后的连续 dword 中落在 .text 里的前缀长度。
  - 兄弟表 = 同一 COL 修饰名（name 字符串逐字节相同）的所有表，取表地址最小的那张。
  - 只取「本表 mdisp != 0 的槽，且该槽号在兄弟表里也存在，且本槽目标不是 thunk」的对。
    thunk 判据：目标起首字节是 E9 或 EB 或 FF 25，或目标只被 1 个槽引用且体 <= 8 字节。
    若你实现的 thunk 判据与此不同，先报你得到的 535 / 1013 / 478 / 525 / 10 这五个数，
    五个数全部对得上才继续；对不上就停下并报你的数，不要硬凑。
  - 对每对记录两侧目标 VA。
S2 对每对两侧各做「完整函数边界分析」：
  - 从目标 VA 起用 capstone 32 位线性反汇编，窗口 512 字节，一次 md.disasm。
  - 遇到下列任一即定边界：
    (a) ret / retn 类指令（含 ret 后带立即数）；
    (b) 连续 2 个以上 0xCC 字节（int3 填充）；
    (c) 连续 2 个以上 0x90 字节（nop 填充）；
    (d) 窗口耗尽。
  - 分类：HAS_RET（(a) 命中）、PAD_CC、PAD_NOP、WINDOW_OUT。
S3 统计：103 对里
  - 两侧都 HAS_RET 的对数；
  - 任一侧非 HAS_RET 的对数；
  - 按 (左类别, 右类别) 的 2x2 计数表；
  - 「两侧都非 HAS_RET」的对数（这是本轮要的正数）。
S4 对「两侧都非 HAS_RET」的每一对，取左侧目标起首 16 字节 hexdump 与右侧起首 16 字节
  hexdump，连同两侧 P.where() 结果，逐对列出（不超过 20 对，超出的只报数）。

## 必须带的自测（正反控）
C1 正控：对 0x410450 跑 S2，必须得到 HAS_RET 且 ret 在 0x41045E（偏移 14），
   函数体为 8B 4C 24 04 33 C0 8A 51 20 84 D2 0F 94 C0 C2 04 00。
C2 正控：对 0x4C9150 跑 S2，必须得到 HAS_RET 且 ret 在 0x4C9152。
C3 反控：把 0x410450 的窗口起点改成 0x41045F（ret 之后），必须得到非 HAS_RET
   且类别落在 PAD_NOP 或 PAD_CC（该处是 90 填充）。
C4 自证：S1 的 535 / 1013 与 R192 一致；若不一致，先报差异再继续。

## 输出
1. 脚本写到 _r193/exec/r193_fnbound.py。
2. 结果写 _r193/exec/r193_fnbound.json，键至少含
   pairs / inc_pairs / both_has_ret / any_not_has_ret / both_not_has_ret / table_2x2 / samples / controls。
3. 最后一行打印 SUMMARY 一行：pairs=... inc=... both_ret=... both_not=... 
4. 明确区分「我实测」与「我没测」。

## 预算
预算 12 分钟，回合上限 14 回合。每条命令一次跑完所有要跑的东西，不要逐条试探。
