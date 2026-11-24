# S05-K1 · DISAGREE.md — 与 KB/台账/coverage 的冲突

> 只列**有字节证据**的冲突；每条引节号/行号。不写主台账。

## D1. 继承链中间层缺失（任务书骨架 vs RTTI CHD）
- 任务书 §2/T1 骨架：`AbstractClass → ObjectClass → TechnoClass → FootClass/...`。
- 实测 CHD（`EVIDENCE/class_chain_core.json`，`COL+0x10 → CHD.base[1]`）：`ObjectClass → MissionClass(0x7EDCC0) → RadioClass(0x7F0508) → TechnoClass`。
- **冲突**：任务书省略 `MissionClass`、`RadioClass` 两层。本卡按 RTTI 实测插入（纪律：类名只认 TD、父类只认 CHD，不按名猜）。
- 处置：CLASS_CHAIN.md 采用 10 类链；不影响 §2.1 四个类 slot73 对比（那张表按 slot 实现分组，非继承邻接）。

## D2. `0x7353C0` = UnitClass 构造器，当前 coverage 归 S18/网络/[未证]
- coverage.tsv 行：`007353C0 S18 sub_007353C0 [未证] 调用图邻居 2 票指向 网络/事件队列/联机（弱信号）`。
- 证据：① 写 `mov [esi],0x7F5C70`（UnitClass vptr）@0x73543A；② `0x449E16 push 0x8E8; call 0x7C8E17; mov ecx,eax(0x449E42); call 0x7353C0(0x449E44)`；③ v[12]=0x8E8 双向闭合。
- 冲突：子系统（S18→S05）、grade（[未证]→[已证]）、语义全错。系"调用图邻居弱信号"误归，违反"调用点数≠语义"纪律 8。
- 处置：coverage_delta.tsv 交 S05 合并；本卡不改 coverage.tsv。

## D3. `0x517A50` = InfantryClass 构造器，当前 coverage 归 S18/CoCreateInstance/[已证]
- coverage.tsv 行：`00517A50 S18 sub_00517A50 [已证] 导入 CoCreateInstance → 网络/事件队列/联机（弱信号）；N_FIX §964 就地提级 low/med→[已证]（有 JMP_THIS 具名构造器；name 更正未执行）`。
- 证据：① 写 `mov [esi],0x7EB058`（InfantryClass vptr）@0x517ACC；② `0x4430C2 push 0x6F0; call 0x7C8E17; mov ecx,eax(0x430DB); call 0x517A50(0x430DD)`；③ v[12]=0x6F0 闭合。
- 冲突：子系统与语义错；注意该行** grade 已是 [已证] 但 name/语义未更正**——正是 N_FIX §964 "name 更正未执行"的实例（本卡补上具名构造器证据）。
- 处置：coverage_delta.tsv 交 S05（S18 原行不必删除，由合并员裁定 ALIAS/迁移）。

## D4. `0x6F2B40` = TechnoClass 构造器，当前 coverage 归 S22 兜底/[未证]
- coverage.tsv 行：`006F2B40 S22 sub_006F2B40 [未证] 无可用静态信号，归 S22 兜底（无法归类）`。
- 证据：写 `mov [esi],0x7F4960`（TechnoClass vptr）@0x6F3130；类属函数 112 条 this 写点全部落 [0xF0,0x2F4]，无越界。
- 冲突：S22 是未定类垃圾桶（PANEL §S22 68.2% 无信息填充），本类有明确 RTTI+vptr 证据，不应留桶。
- 处置：coverage_delta.tsv 交 S05。

## D5. `0x4D31E0` = FootClass 构造器（非 `noinit_t`）
- coverage.tsv 行：`004D31E0 S10 FootClass::noinit_t [已证] FootClass::noinit_t：YRpp/kb 地址名；归属 Mission/单位行为AI（名字已证，语义一行据名推断[未证]）`。
- 证据：写 `mov [esi],0x7E8C94`（FootClass vptr）@0x4D345D；`noinit_t` 是空内联桩无地址（R14_COMMON §8.1⑤ / 纪律 6）。
- 冲突：把委托初始化参数名当真实函数名——正是纪律 6 点名的**整批降级机制**（C09 曾错 15 个）。本卡为**反例**：这里的地址有真实 vptr 写，是真构造器。
- 处置：coverage_delta.tsv 交 S05（grade 保守给 [已证] 于"写 vptr 事实"，name 更正需审计确认）；DISAGREE 记录，不自行改 S10 行。
- ⚠️ 保守说明：本条 name 判别受 §8.1⑤ 机制影响，审计员应优先复核；本卡只把"该地址写 FootClass vptr"作为 [已证] 事实，不宣称 YRpp 原函数名必然正确。

## D6. `vtables_v2.json` 少末槽（已知错，本卡实证复现其后果）
- R14_COMMON §8.1①：`vtables_v2.json` 13,351 槽 vs 实测 14,044 槽 / 1,214 表，794 表各少 1 末槽。
- 本卡实测 10 类槽数（CLASS_CHAIN.md §1）来自 `.rdata` 字节定界；若改用 `vtables_v2.json` 或 atlas 边界会少末槽（如 `TClassFactory` 5 槽坑，§8.1⑦）。
- 处置：本卡所有槽数均从 `.rdata` 定界，**不引用** `vtables_v2.json` 槽数字段。

## D7. `+0x1AC` 的语义口径
- R14 §2.2："can-place `[+0x1AC]` 两处（0x43F218/0x43F678）"。
- 本卡扫描：`call [reg+0x1AC]` 20 处，形态为**虚表槽 107 调用**，非对象数据字段（LAYOUT.md §2）。
- 冲突：措辞"字段 `[+0x1AC]`"易被误当数据成员（本卡初始假设即被自身扫描否证，已撤回）。
- 处置：LAYOUT.md 标 `[静态推断]`（形态），不给字段语义；若 §2.2 原意是虚槽调用，则需把该表述统一为"虚槽 can-place"。
