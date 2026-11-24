# DOD.md — S10 Mission · PLAN §1 六条对账

> 卡号 S10-K2｜2026-11-17｜分母口径（R14-R15）：A = 12,916（atlas 下界，DoD 第 1 条字面分母）；本卡 S10 atlas 分母 = **513**（`PANEL.md` S10 行），盘上 coverage S10 = **515**（513 atlas + 2 表外新增 `0041B860`/`005B3740`）。
> named 口径（R14-R14）：L = PANEL 字面（非空且非 `sub_` 起头）；S = DoD 判据（再排除 `Class::sub_XXXXXXXX`）。**S10 无 `Class::sub_` 占位 ⇒ L/S 同值**（盘上实测 named L=S=498/513）。
> ⚠️ **派卡前提过期**：卡面写 `[已证] 仅 28（5.46%）`；盘上现值（`PANEL.md` + `coverage.tsv` 自数自洽）= **55/513 = 10.72%**。按纪律 9 停机核验，以盘上为准，不凑 28（同 S11-K2 的 13→17/18 先例）。

## 第 1 条 · ≥90% 有名字与一行语义 且 ≥50% `[已证]`

| 口径 | 基线 | 本卡后（含 delta） | 门槛 | 判定 |
|---|---|---|---|---|
| named L | 498/513 = **97.08%** | 498/513 = 97.08% | （面板口径，非 DoD 判据） | — |
| named **S** | 498/513 = **97.08%** | 498/513 = 97.08% | ≥90%=462 | **达标** |
| proved `[已证]`（盘上基线） | 55/513 = **10.72%** | — | ≥50%=257 | — |
| proved（本卡后，仅计 15 条现 S10 升级） | — | **70/513 = 13.65%** | ≥50%=257 | **未达标**（差 187） |
| proved（若 37 条 delta 全部改判入 S10） | — | 92/513 = 17.94% | ≥50%=257 | 仍未达标（差 165） |

- **结论：S10 未达 DoD 第 1 条** —— named S 达标，但 proved 远未过半。按卡面 28 起算则更差（229 缺口）；按盘上 55 起算仍需 +187 到门槛。**如实写：必然不达标**。
- 卡面写「差 229（28→257）」；盘上真值「差 202（55→257）」；本卡交 37 条 `[静态推断]→[已证]` 证据（15 条现 S10 / 13 现 S05 / 8 现 S12 / 1 现 S08）。

## 第 2 条 · 核心类完整字段布局（偏移/类型/读写者，与 GetSize 一致）

- **部分达成**。本卡确立 MissionClass 族 10 个类的 RTTI 身份（COL+0xC→TD+8，只读名）、off=0 主 vtable 定界（`.rdata`）：MissionClass `0x7EDCC0`(157 槽)/ObjectClass `0x7EF060`(122)/AbstractClass `0x7E1F50`(24)/FootClass `0x7E8C94`(341)/InfantryClass `0x7EB058`(343)/AircraftClass `0x7E22A4`(341)/BuildingClass `0x7E3EBC`(322)/TechnoClass `0x7F4960`(309)/UnitClass `0x7F5C70`(344)/FoggedObjectClass `0x7E8B38`(25)。
- GetSize 双点闭合 5/5 具体类（v[12] imm = 工厂 push size → operator new `0x7C8E17` → ctor 写入该 vtable）；抽象基类 MissionClass/ObjectClass/TechnoClass/FootClass/AbstractClass 的 v[12] 是共用桩 `0x4C9150`（`33 C0 C3`），**非真 GetSize**。
- 11 字段已入账（8 双支撑 + 3 单边）；本卡 T4 增量：+0xB8 补到 1 个字节读点（`0x74431F`, UnitClass::slot128，mission==1/5+有目标上下文，mission 标志语义），+0xCC/+0x6C 未补到可归属本类的另一侧 ⇒ 保留 `[未证]`。**完整每字段 ≥3 读 + 写者表仍需专卡**。

## 第 3 条 · 关键数据流（入口 → 每帧更新 → 销毁/存档）调用链图

- **部分达成（已入账前提 + 本卡复核）**：FootClass::AI `0x4DA530` → TechnoClass::AI `0x6F9E50` → MissionClass::AI `0x5B3060`（v[23]）→ 派发 `jmp [eax*4+0x5B34E8]` @`0x5B30C1` → 32 stub → `call [vptr+0x204..0x270]`（v129..v156）。本卡从字节重取派发表 32 项、后随填充 `0x90909090`，逐 stub 解出 mission→v 槽映射（`EVIDENCE/t2_dispatch.txt`）。
- 销毁链：构造器 `0x5B2DA0`（写 vtable `0x7EDCC0`）、串口 `0x5B3970..0x5B3A99`；GetSize 工厂分配链见第 2 条。
- **缺口**：完整「入口→每帧→销毁/存档」全链图未单列；本卡聚焦虚槽语义。

## 第 4 条 · 涉及的 INI 键与全局变量表

- **部分达成**：本卡触及全局 `0xA8ED84`（frame，Mission 字段 C0/C8 时戳）、派发表 `0x5B34E8`、枚举指针表 `0x816CAC..0x816D2C`、基类共用桩 `0x4C9150`、operator new `0x7C8E17`。未穷举 Mission 相关 INI 键（Mission 调度主要来自 AI/脚本，非 INI 直驱）。列 `UNKNOWNS.md`。

## 第 5 条 · ≥1 张真机卡验证 ≥2 条关键运行时事实（或说明不适用理由）

- **未做（本卡为静态 K 卡，不适用）**。Mission 派发/虚槽/GetSize/字段偏移皆为静态可判定字节结构，已由双通道字节复核；运行时「某帧具体派发哪个 Mission」需真机注入地图/AI 状态，属 L 卡范畴。本卡不申请真机。

## 第 6 条 · `KB\Sxx_<名称>.md` 交付并通过异族审计；台账对应结题节

- **未创建 KB 文件（按派卡指令，写域仅 S10-K2\）**。本卡产出（37 条 `[静态推断]→[已证]` 的 entry/语义/证据 + 28 槽逐槽表 + GetSize 5/5 闭合 + 字段增量）为将来 `S10_Mission.md` 提供素材。未写台账、未派异族审计（由 Lead 统一调度）。
