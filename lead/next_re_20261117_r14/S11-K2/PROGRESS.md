# S11-K2 · PROGRESS（Locomotor 类布局 / COM 契约 / GetSize 字节级取证）

> 目标 `gamemd.exe`（SHA `73201CC0…F67476`，ImageBase 0x400000）。静态卡，只读字节通道。
> 交付：`PROGRESS.md` · `LAYOUT.md` · `TARGETS.tsv` · `UNKNOWNS.md` · `DISAGREE.md` · `coverage_delta.tsv` · `EVIDENCE\` · `work\`。
> 前任无 PROGRESS = 无结论交付；本卡全部结论由 `work/fresh_*.py` 独立重取（capstone `skipdata=True`，不依赖 atlas 做发现），半成品数据仅作起点。完成 2026-11-17。

## 结论表

| # | 结论 | 级别 | 证据 |
|---|---|---|---|
| 1 | Locomotor 实现类 **12**（抽象基类 + 11 具体），类名全部 RTTI `COL+0xC→TD+8` 实测（读不到 fail-closed） | [已证] | `EVIDENCE/fresh_core.txt` |
| 2 | 多接口 COM 布局：off0=IPersistStream（10 槽，Teleport=12）、off4=ILocomotion（50 槽）、off24=IPiggyback（8 槽，6 类有）；共 30 表/770 槽，`.rdata` 定界 | [已证] | `EVIDENCE/fresh_core.txt` |
| 3 | **GetSize 在 off0 slot 9**（非 AbstractClass 惯例 slot12）：11 处 `B8 imm32 C3`，基类桩 `004C9150` 已排除 | [已证] | `EVIDENCE/fresh_core.txt`、`fresh_closure.txt` |
| 4 | **GetSize 双向闭合 11/11**：各厂 `push<size>;call 0x7C8E17(new)` 的 size 与该类 off0 slot9 imm 逐类相等；`6A imm8`=10、`68 imm32`=1（§972） | [已证] | `EVIDENCE/fresh_closure.txt` |
| 5 | CLSID 11 项 `.rdata 0x7E9A30..0x7E9ADF`；无静态 {GUID→工厂} 表（穷举 count=0），映射在注册函数 `0x6BB9A0` 代码内 | [已证] | `EVIDENCE/t1_clsid_check.txt` |
| 6 | 4 个 ILocomotion 派发锚点字节复核：槽7/16/17/18 = `ff 51 1c/40/44/48`（Can_Enter_Cell/Process/Move_To/Stop_Moving） | [已证] | `EVIDENCE/fresh_slots.txt` |
| 7 | Drive 类 6 个字段字节级双支撑（写+读，读者≥3）：+0x8/+0x30/+0x38/+0x40/+0x4C(double)/+0x68；高层语义未定名 | [已证] 存在+支撑 / [未证] 语义 | `EVIDENCE/fresh_fields.txt` |
| 8 | 字段扫描剔除虚调用 `call/jmp [reg+disp]` **34** 处，未计入读点 | [已证] | `EVIDENCE/fresh_fields.txt` |
| 9 | 全镜像裸 `B8 imm32 C3`：`.text`=666（全文件 668），落 Locomotion 槽仅 11 ⇒ 裸判据不特异（§969 837/543 口径不符，见 DISAGREE） | [已证] | `EVIDENCE/fresh_baseline.log` |
| 10 | 增量抬 proved：11 GetSize（`[静态推断]→[已证]`）+ 2 ctor（`[未证]→[已证]`），共 13 行 `coverage_delta.tsv`，校验 bad=0 | [已证] | `work/t5_final_delta.log` |

## 核心数字 + 独立复算方法（3 个）

1. **实现类数 12**：`python work/fresh_core.py`。扫全节 `.?AV*LocomotionClass@@\0` → 12 TD（fail-closed 校验 `COL+0xC→TD` + sig=0 + CHD∈.rdata）；`CLASS COUNT=12`。双通道：TD 名模式 + COL 引用计数 + CHD 基类链，三者收敛（非同源互读）。
2. **GetSize 闭合 11/11**：`python work/fresh_closure.py`。A 点=各类 off0 slot9 `B8<imm>C3`；B 点=全 `.text` 扫 `call 0x7C8E17(operator new)`，回溯 `push<size>`（6A/68 全形式），前向找 ctor 写 canonical vtable 定类；逐类 `size==imm` 11/11。复算输出 `CLOSURE=11/11`。
3. **S11 proved 变化（双口径，分母必标）**：起点 atlas 内 **17** / 全表 **18**（`coverage.tsv` 自数；PANEL.md post-M2）；本卡 delta +13 行（12 在 atlas、1 在 atlas 外）⇒ **atlas 17→29 / 全表 18→31**。复算 `python work/t5_final_delta.py`（含校验）。分母口径：A=atlas 12,916（下界）/ B=14,715（14,500–15,300）/ C=≥18,431；引用全镜像百分比必标 A/B/C。

## 双通道声明 / 纪律遵守
- 通道 A（不依赖 atlas）：`pefile` 字节扫 RTTI/CLSID/vtable/B8/C3 + `operator new` E8 rel32 精确目标（`fresh_core/fresh_closure`）。
- 通道 B（不同源）：CHD 基类链定父类 + 工厂 ctor 写 vtable immediate 定类 + 调用点 `ff 51 disp` 定槽（`fresh_closure/fresh_slots`）。非「写两份互读」。
- capstone `skipdata=True`；类名只认 RTTI；字段只标字节事实不定语义；虚调用剔除 34；无 `entry_at_or_before`；未改游戏文件/台账；开关机核验派卡错误（13→18、v12→off0 slot9）均停机留证并经 Lead 裁定（见 `DISAGREE.md`）。
- 方法论（Lead 表扬）：「槽 12 找不到」没有放弃，而是转成「它到底在哪个槽」的实证问题——纪律 18「没找到期待的形式 ≠ 功能不存在」的正面案例。
- S11-K1 增量边界：K1 已交付类族/CLSID/工厂/槽锚（其 VERDICT M2 更正 Jumpjet CI=006C4190）；本卡只做 GetSize 字节闭环、字段双支撑、槽语义与 proved 增量，未重做 K1 结论。
