拿到真名 1 条（0053AF40 → PsyDom::Update）

# S21-N2 PROGRESS — 给 S21 补真名（只命名，不动 grade / subsystem）

- 开工 2026-11-18 16:06 +08:00；骨架于开工首步落盘（满足 10 分钟内要求）。
- 目标 ra2youli\gamemd.exe 只读；python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26；未建 venv、未 pip install。
- 写域：本目录 与 _ghidra\S21-N2\；其余只读。

## ⑨ 停机核验（自算）
coverage.tsv S21 精确 132 行；与 W130_atlas/function_atlas.tsv 求交 = **129**；
named = **90**、sub_ = **39** → 与卡面一致。
（3 行 S21 不在 atlas：0046FC00 / 00690C00 / 00690D60，均为 slot 名，非本卡工作面。）

## 交付结果
- 真名 **1** 条：`0053AF40 → PsyDom::Update`（第二条通道 = YRpp/SuperClass.h:191 CALL(0x53AF40) 原文行，class PsyDom）。
- 其余 38 条 sub_ 查无合格第二条通道 → 按规矩交 0，不凑数（见 UNKNOWNS.md）。
- coverage_delta.tsv：8 列、1 数据行；不动 grade / subsystem。

## 关键证据
- E01：YRpp CALL 绑定原文 + class PsyDom 4 个静态成员声明。
- E02：二进制反汇编 —— 0x53AF41/57/B0/E6/1D/54 读写 0xA9FAC0；0x53AF64/C2/F3 读写 0xA9FAC4；0x53B027 写 0xA9FA48；0x53B28C 读 0xA9FAC8；0x53AFBA call 0x53B080(Fire)；唯一 E8 call site 0x53A742。四条全局与 YRpp PsyDom 声明逐一对上。
- E03：⑱ 四源冲突检查 —— coverage / docs\re / re_atlas\kb / 台账 均无同名冲突。
- E04：基础率（7/17≈41.2%，随机 5 条期望误命中≈2）+ 如何避免只靠它 + 全通道清单。

## 已试通道（摘要）
1. YRpp 全库按地址 grep（6/8 位、大小写、0x 变体；YRpp 与 yrpp 两份相同）：39 地址中仅 1 条严格 CALL/JMP_THIS 绑定。
2. YRpp 宏形式枚举（CALL/JMP_THIS/JMP_STD/...）+ 近邻 ±0x60：无其它目标绑定。
3. 镜像内串 / 调用链（out\re_work 同源自记有线索）：禁作第二条通道，仅记 UNKNOWNS。
4. 跨项目独立源：项目内 11 个候选目录 + 外部 5 目录 523 文本文件扫描 = 0；无符号 sidecar。

## 状态
未写 COVERAGE\coverage.tsv、未改 gamemd.exe、未 git commit/push。未放宽判据、未编名。
