你是 RA2 Campaign Forge 的**独立复核卡 W51**。任务：**核对 W31 与 W33 两张卡的判定链是否真的"互证"**。

工作目录：`D:\Project\ra2-campaign-forge`。**第一件事：立刻建目录 `lead\next_re_20261112_r02\W51_chain_equivalence_check\` 并写 `STARTED.txt`（带时间戳）。**

## 为什么派你
Lead 曾宣布「W31 + W33 两卡独立互证，根因已定谳」。但 W43 的交叉审计（`REVIEW\agy_w43_handoff.md` BLOCKER-4）指出：**两卡只是结论相同，中间判定链并不等价**，且两卡各自都犯了同一个错（把 `0x7B5B30` 的归一化方向说成"转大写"，实为转小写，直到 W34 才发现）。这条 Lead 没有深查。

## 要核的
逐条比对这两份报告的**中间步骤**（地址、分支、调用点、结论）：
- `W31_map_start_failure\WHY_MAP_FAILS.md`（从 CSF 标签 `MSG:UnableMapSelect` 反推）
- `W33_nextscenario_dataflow\NEXTSCENARIO_FLOW.md`（从 `NextScenario` 数据流正推）
- 参照 `REVIEW\LEAD_VERDICT_map_start_root_cause.md`（Lead 的合图）与 `W34_mapselmd\MAPSELMD_SPEC.md`（后来的更正）

要回答：
1. 两卡对**同一条判定链**（`GUI:Continue` → `SkipMapSelect` 分派 → `MapSelect::Init` → 阶段表反查 → 弹窗）给出的**地址与分支是否一致**？列出所有不一致处。
2. Lead 的合图是否把两条**不同的失败出口**（`SkipMapSelect=no` 与 `=yes`）合并成了一条？若是，正确应怎么分开写？
3. 两卡各自有哪些**已被后续纠正**的中间结论（例如"转大写"、`0xFBE0D09D` 的来历、`s09` 误判文件缺失）？这些在合图里是否被清理？
4. 结论：「两卡互证」这个说法**在什么范围内成立、在什么范围内不成立**？

## 纪律
- 纯离线只读：不启动游戏、不 attach、不写 `ra2youli`、不改仓库、不动 `W21`–`W50`、git 只读
- **不要取 `.game_instance.lock`**（真机卡在持锁）
- 分级：`[本次实测]`/`[本次读码]`/`[静态推断]`/`[转引]`/`[待运行验证]`
- 你**不必重新反汇编整个函数**：以文本比对 + 抽查关键地址为准；抽查时给出 VA/RVA/FOFF 与原始字节
- 发现问题直接说，这份复核的价值就在挑错

## 交付（只写这个目录）
`W51_chain_equivalence_check\`：`STARTED.txt`、`CHAIN_EQUIVALENCE.md`（四问逐答 + 不一致清单 + 「互证范围」结论）、`UNKNOWNS.md`