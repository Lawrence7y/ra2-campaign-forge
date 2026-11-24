# W177-D · LIVE.md（实测值 vs 静态预测对照）

> 卡号 W177-D｜pid=10724｜全部只读 ReadProcessMemory + 合成输入；未写内存/未注入。

## 对照表

| 静态预测（来源） | 真机实测 | 一致? | 证据 |
|---|---|---|---|
| `0xA8E7AC!=0` ⇒ `0x47C620` 立即返回1（S12-K2 #11 `[静态推断]`） | 高频 409,708 样本/6s + MCV部署期 1,767 样本/4.36s 均恒 `0`、0 跳变；未观察到旁路态 | 预测未触发（无法证伪分支） | `EVIDENCE/globs_hifreq.jsonl`、`globs_hifreq_deploy.jsonl` |
| `byte[0xA8E9A0]==0` ⇒ 跳过 WhatAmI 扫描（S12-K2 #12） | 高频两窗均恒 `1`（与 R14_COMMON §0「A8E9A0 恒1」一致）；扫描开启 | 一致 | `EVIDENCE/globs_hifreq*.jsonl` |
| `byte[0xA8ED6B]==0` ⇒ 进 `0x47C878` 分支（S12-K2 #13） | 高频两窗均恒 `0`，0 跳变 | 一致（分支态） | `EVIDENCE/globs_hifreq*.jsonl` |
| `+0x8C` byte: 0→headA, 非0→headB（S12-K2 #9 `[静态推断]`） | Building/Unit/Infantry 共 222 对象 `+0x8C` 全=0；仅少数 other 类非0（HouseClass=1 等） | 一致：可放置对象全走 head A | `state_bypass_final.jsonl` |
| `0x47C620` 只扫 head A，不扫 head B（S12-K2 #1） | 本卡无法读 EIP；但可放置对象 head B 恒空（由 +0x8C=0 推出），故 head-B 绕过路径不可达 | 静态未直接测，间接支持 | `state_bypass_final.jsonl` |
| 格链是 `[格+0xE4]/[格+0xE8]` 双链表头，元素 +0x30=next（R14 §2.2） | 全图遍历两链均可用；链≥2 只见 head A，head B 恒0 | 一致 | `scan_all_cells_01.txt`、`scan_detail_*.jsonl` |
| 多格建筑逐格校验（R14 §2 can-place + 0x47C620） | NACNST/NAPOWR 均挂入 footprint 所有格 ⇒ 任一相交格都进 head A 扫描 | 一致（部分相交无法绕过） | `footprint_multicell.jsonl` |
| `[+0x81]`=Limbo（S12-K2 #8 / R14） | 在格建筑 `+0x81=0`；下单未落格对象 `+0x81=1` 且 cell=(0,0) | 一致 | `work/dsnap.py` 快照、`PROGRESS #8` |
| RTTI 链 COL+0xC→TD+8（纪律5） | BuildingClass→`.?AVBuildingClass@@`；InfantryClass→`.?AVInfantryClass@@`；TerrainClass→`.?AVTerrainClass@@` 均可读 | 一致 | `rtti_static.txt`、`infantry_stack_detail_*.jsonl` |

## 关键实测数值

- 游戏窗口 2560×1440，client origin (0,0)；菜单/遭遇战设置画在左上 800×600，进局后整窗绘制（与 R14 §5「只画左上800×600」表述**不一致**，见 DISAGREE）。
- 进局按钮经黄色文字连通块定位：單人遊戲 y≈221、遭遇戰 y≈304、開始遊戲 y≈263（x≈720），与 R14 §5 给值一致。
- 遭遇战设置：利比亞 / 簡單的敵人 / 遊戲速度4 / 資金10000 / 部隊數10 / **超級武器未勾**（规避 W177-B/C 的 AI 超武毁基地）。
- 玩家 House `0x10d50d30`（+0x1EC/+0x1ED=1）；frame 从 0 递增至 44025+。
- 链≥2 实例（步兵）：cell(48,89) lenA=3，三节点 RTTI 全 `.?AVInfantryClass@@`、owner `0x10d66df8`(敌)、layer=2、+0x8C=0；cell(37,67) lenA=2 两节点 owner=`0x10d50d30`(玩家)。均为移动单位，非放置产物。
- 链长稳定性：cell(55,75) 在 6 次连续扫描（18:05:56→18:06:01，5 秒）始终 lenA≥2，但节点集合每次不同（单位轮换）；定点 0.6s×7 跟踪时该批单位已移走、链归 0 ⇒ 不满足「同一节点集稳定≥3s」。

## 未做的对照（如实记）

- 未取 EIP/线程上下文去定位 `0x43F180` mode 参数序列或 `0x47C620` 返回值——那需要高频采样且本镜像 EIP 无判别力（R14 §0）；改用只读字段+链快照作观测量。
- 未做「写内存翻转 A8E7AC / 制造 head-B 对象」——需越界，放弃。
