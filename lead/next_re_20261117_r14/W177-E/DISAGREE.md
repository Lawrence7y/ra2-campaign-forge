# W177-E · DISAGREE

本卡对既有结论的异议/更正，逐条给出依据。

| # | 对象 | 异议 | 依据 |
|---|---|---|---|
| D1 | a-W177-D ★B/结论③"head B 对可放置对象恒空 → head B 绕过路径不可用" | **不推翻，但限定**：本卡静态确认 `0x47C620` 全程 0 次读 `+0xE8`（只读 `+0xE4` 5 次），所以"head B 绕过"从占用校验角度根本不是一条路径——不是"因恒空而不可用"，而是**校验器不看 head B**。head B 的用途在挂链端 `0x47E8A0`（`[esp+8]!=0`→`+0xE8`）。 | `EVIDENCE/static_verify.txt` 0x47C620/0x47E8A0 反汇编；live 6 次采样 headB 恒 null |
| D2 | a-W177-D ★A.4"部署是否算一次过 0x47C620 的放置＝未证" | **本卡部分补齐**：T1 的 6 次采样是在"点图标拿起 ghost 后→点击落格"前后 2 s 内高频采的（click_t=0.35/0.40 s），每行带 frame 与链长/RTTI；`EVIDENCE/T2_try2_48_97_result.json` 等有对应 credit 扣款与落格对象。**但**这些落格均非目标步兵格，且 `0xA8E7AC` 帧内 µs 级 inc/dec 仍可能错过（见 U5），故只补"放置事实已落盘"，不补"零跳变⇒无旁路"。 | `EVIDENCE/T2_try1_48_97.jsonl`、`T2_try2..final2*_hifreq.jsonl`、`T2_*_result.json` |
| D3 | "建筑落步兵格字节上可行 ⇒ 真机应能构造" | **同意方向，反对据此宣布可构造**：本卡 5 次实际放置全落邻接格、0 次同格；静态放行只说明 `0x47C620` 不拒步兵，不保证合成输入能稳定命中多格 footprint。结论应是"未证 + 路径未被证伪"，不是"已证可行"。 | `EVIDENCE/T2_*_result.json`、`precondition_cells.jsonl` |
| D4 | 上一卡"采样率覆盖事件窗口"做法（405/s） | **明确不足**：本卡实测 11,382–28,263/s、2 s 全量落盘；但即便 28k/s（35 µs）仍不等于 µs 级帧内窗口的充分覆盖。任何"零跳变⇒不存在"的表述必须带采样率限定。 | `EVIDENCE/T2_final2_hifreq.jsonl`（56,529 样本/2 s） |
| D5 | 本卡自身一次误判：把 campaign 侧栏 (2328,480) 当 NAPOWR | **记录纠正**：遭遇战该图标是 NAPOWR（成功下单扣 600 + limbo），但战役地图侧栏布局不同，同坐标点了 NAREFN，credit 因矿车持续上涨掩盖扣款。故 `T2_final1/final2` 不计入"成功建筑放置次数"。 | `EVIDENCE/T2_final1_result.json`、`T2_final2_result.json`（new_napowr=[]） |
| D6 | coverage_delta 旧卡 6 行非法 entry（字段偏移/数据地址当函数入口） | **本卡遵守**：只写真实 hex8 函数入口（`0x0047C620`/`0x0047E8A0`/`0x00459EC0`/`0x00523340`），字段偏移与全局量只写在语义列，不占 entry 列。 | 本卡 `coverage_delta.tsv` |
