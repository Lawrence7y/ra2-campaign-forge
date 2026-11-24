# AUDIT-R110 · 跨家族审计员（hy4）任务卡

## 你的身份与唯一职责

你是 R17 第 110 轮的**跨家族审计员**（家族 hy4）。主会话用另一家族（deepseek）完成了两支实测，你**不复跑脚本、不重做逆向**，只做**逐项数值与逻辑核对**，并把结论写成一份可被主会话用脚本复算的核对清单。

## 环境

- 工作目录：/home/t628/projects/ra2-campaign-forge
- 目标镜像：ra2bench/gamemd.exe（sha256 前 16 位 73201cc021497c95）
- 本轮产物目录：_r110/
- 只读产物，**严禁修改四件套**（R14_COMMON.md / GOAL_THREE_TARGETS_20261018.md / LEAD_LOCK / STATUS_BOARD.md / BOARD_ARCHIVE.md）

## 待审材料

1. _r110/r110a_iidmap.py 与 _r110/r110a_iidmap.json —— 用 slot0 是 QueryInterface 的字节特征，抽出「每个类认哪些 IID」，进而给出本镜像的 COM 暴露面。
2. _r110/r110b_seh.py 与 _r110/r110b_seh.json —— 核验 32 位镜像无 .pdata 时，__try/__except 异常处理表能否充当第二套函数边界。

## 必须逐项核对的 8 条（每条都要给出「一致 / 不一致 / 无法判定」+ 你亲眼在 json 里看到的数值）

A1. r110a 的 S2 报「172/954 = 18.0% 个类的 slot0 具备 QI 头部形态」。核：json 里 n_qi_classes 是否为 172，pct 是否 18.0，954 是否为 vtable 总数。

A2. r110a 的 S3 报「抽到的 IID 指针 0 个落在 .text」。核：judgement 是否真的成立（json 里应无 .text 项）。**特别注意**：一个把 PE 里的 RVA 当 VA 的脚本会让这条假失败，看 json 的 checks 里 S3 是 PASS 还是 FAIL、detail 是否为空列表。

A3. r110a 的 S5 每类 IID 个数分布报 (1,1),(2,92),(3,3),(4,76)，四项之和必须等于 172。你自己加一遍，报出和。

A4. r110a 的 S6 报 distinct IID 按指针 = 17、按内容去重也 = 17。这个相等意味着「没有两个不同指针指向同一 GUID 内容」。核：json 的 iid_classes 与 guid_of_ptr 两个映射的键数是否都 17，且 guid_of_ptr 的值有没有重复。

A5. r110a 报认 IUnknown（指针 0x7f7c90）的类 171 个、不认的 1 个且该 1 个是 AircraftClass。核：json 的 iunk_share 与 without_iunk 字段是否如此。

A6. r110b 的 E1e 报「含成对 SEH 帧操作的函数数 = 6 / 17766 = 0.03%」。核：json 里 seh_funcs 列表长度是否 6、hb 是否 17766。

A7. r110b 的 E2b 报「完整 FuncInfo 形态命中里落在 .text 的 = 0 个」。核：json 的 funcinfo 列表里每一项的节名。

A8. r110b 的 E4 结论是「第二套函数边界不存在」。核：这个结论是否被 E1e（0.03%）、E2a（完整形态 1 条）、E3（引用 3 条）三个数字支撑；若有任一数字与结论矛盾，指出。

## 输出要求

把结果写到 _r110/AUDIT110.md，格式：

    # AUDIT110（hy4 · 跨家族审计员）
    ## A1 一致 | 实测 n_qi_classes=172 pct=18.0
    ## A2 ...
    ...
    ## 总判定
    - 一致 N 条 / 不一致 M 条 / 无法判定 K 条
    ## 我认为主会话错了的地方（若无写 none）

**只允许用 8 项以内的纯文本核对**。禁止做字节级/反汇编级判断（你这一族在这类判断上不可靠），也禁止运行任何反汇编脚本。若某项你无法从 json 直接读出，写「无法判定」并说明缺哪个字段，不要猜。

## 时间与回合

预算 8 分钟。**优先保证 AUDIT110.md 落盘**：即使只核完前 4 条，也先把已核的部分写盘。落盘比核完更重要。
