# W83c UNKNOWNS（未覆盖 / 待运行验证 / 未定谳）

分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。

- **U1 · Hunt 忽略无武装建筑的引擎机制** `[本次实测 + 静态推断]`
  v1 臂（3× GAPOWR，无武装）40 辆 Hunt 坦克 154 游戏秒纹丝不动（t10/t30/t60 截图逐字节相同）。现象钉死，但机制（threat 值为 0 不进目标表？TargetSelection 过滤？）未反汇编验证。工程结论已可用：**造"摧毁建筑"实验必须给建筑武装（如 ATESLA）或换触发方式**。

- **U2 · frame 90 空胜的精确评估点** `[本次实测 + 静态推断]`
  ATSLA（不存在型号）被加载器丢弃 → 英军 0 建筑 → event 10 空真 → frame 90 判胜。90 与 W79 的 survive 截距 +90、W80/W82 的"second 15 frames"研究是否同源（触发器首次评估延迟？）未做。**工程签名已可用：开局 ~frame 90 即胜 = 编译产物的 win 条件空真（典型原因：目标型号无效被丢弃）。**

- **U3 · tag 挂在单位上的 `destroy_building`** `[待运行验证]`
  本卡只测了结构 tag（编译层 `structure_tag` 引用 structures[].tag）。单位 tag 能否同样挂接 `DestroyedByAny` 触发未测。

- **U4 · "非我方摧毁"是否也计数** `[待运行验证]`
  `DestroyedByAny` 语义按编译层推断对任何来源的摧毁都触发（含卖出/自毁/友军误伤）。本卡未构造该情形。

- **U5 · docs/DESIGN.md 型号表与游戏 rules 的全面差异** `[本次实测（局部）]`
  rules probe 只核了 12 个候选名：`ATSLA` 无 section（文档错），`ATESLA/GAPILL/GAPOWR/TESLA/GACNST/NACNST/GAGAP/NASAM/NABNKR` 有，`GAWTHR/GCANON` 无（后者真名 `GTGCAN`）。`GAWEAP` 等其余型号未核。

- **U6 · destroy_all_buildings 对"敌方持续新建建筑"的行为** `[待运行验证]`
  本卡敌方是静态布局、无建造能力。若敌方 AI 会重建/新建建筑，event 10 是否要求"同时清零"未测。

- **U7 · 重复性** `[静态推断]`
  每臂单趟（时间盒 140 min 内完成 ①②③全臂优先）。判胜 frame 的确定性由同引擎 `survive` 规律（915 两次逐点复现 W79）间接支撑；314/201 的跨趟复现未做。

- **U8 · `hunt_wave` 事件的实际生效时刻** `[本次实测（间接）]`
  trip7 t15 截图敌步兵已不在阵前、坦克阵完好，与 at_second=3 后 E1 被 40 坦克速歼一致；但未逐帧确认 AllToHunt 的生效 frame（`13,0,3` 事件按 survive 规律应在 frame ~135 附近触发）。
