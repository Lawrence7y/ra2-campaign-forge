# W89_adversarial · PROGRESS

> 任务：R03 W85 (`PRESSURE.md`) 离线对抗性复核
> 写域：`lead/next_re_20261112_r04/W89_adversarial/`
> 硬纪律：只读其余路径；不修改/运行游戏、不注入/附加调试器；需分析的文件先复制到本卡目录再处理。

## 进度看板

- [x] 启动与骨架落盘 (`PROGRESS.md`)
- [x] 复制待核样本与检查环境/工具链
- [x] 检查 1：坐标越界（W85 pressure/control JSON + MAP 全量解析，0 越界）
- [x] 检查 2：同格堆叠（密度与最大堆叠统计，Unit-Unit 0 堆叠）
- [x] 检查 3：建筑与单位重叠（Struct-Unit 0 重叠，但发现 NAPOWR 3x2 / NACNST 4x4 建筑间严重底座重叠：10~14 格）
- [x] 检查 4：与 W84 df 稳定先例逐字段结构对照（最小差集已落 `EVIDENCE/check_1_2_3_4_geom.stdout.txt`）
- [x] 检查 5：`0xA8ED50` 语义核查与替代时序锚（`EVIDENCE/check_5_7_ndjson_and_crewed.stdout.txt` + `card_00A8ED50.md`）
- [x] 检查 6：`0x0051C2D3` 所属函数完整静态反汇编与虚表槽/类定位（`EVIDENCE/disasm_51C2D3.stdout.txt` + `check_6_*.stdout.txt`）
- [x] 检查 7：静态对照等价性批判（Guard vs Hunt 移动/寻路路径）与最小判别实验（`EVIDENCE/check_5_7_ndjson_and_crewed.stdout.txt`）
- [x] 整理 `UNKNOWNS.md`、`DISAGREE.md`、`ADVERSARIAL.md`
- [x] 自检写域隔离与交接核验（100% 完成）
