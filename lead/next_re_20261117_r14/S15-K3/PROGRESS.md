# S15-K3 · PROGRESS（触发器子系统 · 静态 K 卡 · 卡号 S15-K3）

## 结论表（分母 = `coverage.tsv` subsystem=S15 ∩ `function_atlas.tsv` = 158）

| 指标 | 基线(盘上,已入账) | 本卡 delta | 本卡后 | DoD 门槛 | 达标? |
|---|---:|---:|---:|---:|---|
| named(S)（排除 `sub_` 前缀与 `Class::sub_` 形式） | 137/158 = 86.71% | **+2** | **139/158 = 87.97%** | ≥90% (143) | **否，仍差 4** |
| proved `[已证]` | 95/158 = 60.13% | **+2** | **97/158 = 61.39%** | ≥50% (79) | **是** |

- 本卡只交 **2 条**真的能定的名字（`006E2A10` DeleteTrigger、`006E2AA0` ForceTrigger），
  双通道硬证（YRpp ACTION_FUNC 精确地址 + 本卡字节级反汇编复核）。其余 4 个名字**不可定**，
  如实交差，不编名（见 `UNKNOWNS.md`）。
- 未达 DoD named 线（139 < 143）。按派卡"如实交差 N 个比编名字有价值"执行。

## 给审计员的 3 个核心数字及复算方法

1. **分母 158、named(S) 137、proved 95 全部盘上复现**（T1，`EVIDENCE/t1_recompute_stdout.txt`）：
   `python work/t1_recompute.py`；取 `coverage.tsv` 行 `subsystem==S15` ∩ `function_atlas.tsv`（entry 小写归一），
   S15 全表 159 行 − 表外 `006E6080` = atlas 158；named_L=named_S=137（S15 无 `Class::sub_`，strict/broad 两判据同为 137）；
   proved=95；need=`ceil(0.9*158)=143`，shortfall=6。与 PANEL 行 S15 `158|137|86.71|95|60.13` 逐值吻合，无 DISAGREE。
2. **当前不够 named(S) 的 21 行**（T1 全列）：`006D0F00,006D6070,006E1830,006E2A10,006E2AA0,006E4790,006E47C0,006E6310,006EA3E0,006F1920,0070F120,0071FA30,00721270,00726910,00727AA0,0072DDB0,0072DEF0,00751590,00752460,00763610,00763690`，全为 `sub_` 前缀 + `[未证]`。本卡命名其中 2 条（`006E2A10`/`006E2AA0`），剩 19 条未具名。
3. **2 条命名的证据链**（`EVIDENCE/naming_evidence.md`）：通道 A = `YRpp\TActionClass.h:176/178` 的
   `ACTION_FUNC(DeleteTrigger,0x6E2A10)` / `ACTION_FUNC(ForceTrigger,0x6E2AA0)`（外部权威 VTable/方法地址表，
   同文件邻项 `0x6E2AF0=EnableTrigger` 与 coverage 已入账名吻合，证其对本二进制有效）；通道 B = 本卡
   capstone 反汇编：两条都遍历全局触发器表 `[0xA8EAEC]`/Count `[0xA8EAF8]`，按 `[this+0x50]` 编号匹配
   `[trig+0x24]`，分别 `call 0x726720`(TriggerClass::Destroy) / `call 0x7265C0`(TriggerClass::FireActions)，
   两条被调名本身是 coverage 已证 S15 条目。字节语义与名逐字吻合。

## T3 · proved 稳固性抽查（5/5 字节级充分）

`work/t3_verify.py` / `EVIDENCE/t3_verify_stdout.txt`：
- `006E4630` GetSize = `B8 94 00 00 00 C3`；`006E4640` WhatAmI = `B8 2F 00 00 00 C3`（0x2F=47=AbstractType::Action）✓
- `0071E940` HasOccured：派发 `FF 24 95 18 F2 71 00`，L1/L2 表逐值复现 ✓
- `006E01C0` WakeupSelf：ID81 handler `0x6DDB67` 唯一 call 直指；全 .text xref 恰 1 处 ✓
- `006E4DE0` TagClass::TagClass：入口写 4 个 vptr + `call 0x410170` 基类 ctor ✓
- 承重墙 25 动作：容错仍是最多推翻 16 条（95−16=79 达标）；全否 25 条 ⇒ 70/158 FAIL，至少需 9 条（S15-K2 实测 25/25）。本卡 +2 仅加固，不动此结论。

## 纪律与写域
- 目标 SHA-256 `73201CC0…F67476` / 4,825,360 B 实测一致；capstone `skipdata=True`。
- 字节通道（YRpp 地址表/反汇编）不依赖 atlas entry+size；atlas 只作分母与交叉表（纪律 1）。
- 只写本卡目录；未改 `COVERAGE/`，未写台账，未改游戏文件，未 git commit。
- 交付：`TARGETS.tsv`/`coverage_delta.tsv`（各 2 行）、`UNKNOWNS.md`、`DISAGREE.md`、`EVIDENCE/`、`work/`。
