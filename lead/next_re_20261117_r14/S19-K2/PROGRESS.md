# S19-K2 · PROGRESS（结论表 · 核心数字 · 复算）

> 卡号 S19-K2｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476` 亲测一致｜写域仅本卡 + `_ghidra\S19-K2\`
> 凡本卡面给出的 coverage/PANEL 数字，一律以盘上现值为准；不一致按纪律 9 停下报告，不许凑数（本卡 D1：卡面 362 与盘上 357 不符，已上报并用盘上值）。

## 结论表

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | T1 统一大小写后 `S19 ∩ atlas = 357`（非卡面 362）；盘上 PANEL 自洽：named_L 46(12.89%)/named_S 40(11.20%)/proved 21(5.88%)。距 50%(179) 差 **158** proved | `[已证]`(盘上复算) | `EVIDENCE/numeric_summary.txt`、`work/t1_targets.py`、`TARGETS.tsv` |
| 2 | T2 批量定名 **18 条**：12 EVA 触发函数（串引用+`call 0x752700` 锚点）+ 5 Bink IAT 包装 + 1 taunt 加载器。17 `[已证]`/1 `[静态推断]`；全部当前为 `sub_`，属首次定名 | `[已证]`×17、`[静态推断]`×1 | `NAMES.md`、`EVIDENCE/t2_naming_evidence.txt`、`coverage_delta.tsv` |
| 3 | T3 `VocClass 0x148`（已入账，GetSize）核验一致；**新证 WaveClass=0x240**：RTTI `TD 0x847EB0`→主COL `0x80D418`→vtable `0x7F6BF4`，slot12 imm=0x240，3 处 `push 0x240`→operator new 双点闭合。槽 12 靠双点闭合选中（反例 slot35/36 已排除），非假定 | `[已证]` | `LAYOUT.md`、`EVIDENCE/numeric_summary.txt`、`work/wave_vt.py` |
| 4 | 其它音频类（Mixer/Stream/Theme/EVA manager）无独立 RTTI TD，按纪律 5 fail-closed **不可定名/不可定 GetSize**；`AudioController::sub_406xxx` 6 条无特异依据保持 `sub_` | `[已证]`(否定性已查全 RTTI) | `LAYOUT.md`、`UNKNOWNS.md` U3/U4 |
| 5 | T4 调度链通：EVA 事件串→`0x752700`→索引表→`0x752480`→`0x752760`→`0x407B60`（F1 四跳）；音效/音乐全局播放 `PlayGlobal 0x750920` 直接被调者 **8 个**（VoiceAlloc/0x4052F0/5×AudioController/_ftol）；116 调用点/69 调用者函数（69 引用 §968，不重数） | `[已证]` | `EVIDENCE/numeric_summary.txt`、`DISAGREE.md` D2 |
| 6 | `BinkMovieLoop 0x432C70` 机理（自持泵+4 回边→0x432CB8）成立；按 §968 更正："阻塞主循环"降 `[静态推断]`、删"期间主循环不推进"绝对表述 | 机理`[已证]`/阻塞`[静态推断]` | `DISAGREE.md` D3、`EVIDENCE/numeric_summary.txt` |
| 7 | 停机核验三项全符：`VocClass 0x148` / `PlayGlobal 116` / 音量 `0xA8EB98/9C/A0`；无 STOP | `[已证]` | `work/baseline_check.py`、`DISAGREE.md` 末行 |

## 1–3 核心数字及复算方法

**数字 1：T2 定名 18 条 → named_L 46→64、named_S 40→58、proved 21→38（若 M 卡按 delta 全额合入）**
复算：`python work/t1_targets.py` 得盘上基线（46/40/21）；`coverage_delta.tsv` 18 行中 17 行 `[已证]`、1 行 `[静态推断]`。18 条当前全为 `sub_`（11 `[未证]`+7 `[静态推断]`），故 named_L +18、named_S +18；proved +17（11 `[未证]`→`[已证]` + 6 `[静态推断]`→`[已证]`；第 18 条 taunt 仅 `[静态推断]` 不计）。每条依据见 `EVIDENCE/t2_naming_evidence.txt`。

**数字 2：`S19 ∩ atlas` = 357，距 50%(179) 差 158 proved**
复算：`python work/t1_targets.py`（大小写归一后集合交集，STATUS_BOARD §990 坑）。卡面 362/12.71%/5.80% 与盘上 PANEL.md 不符，见 `DISAGREE.md` D1。

**数字 3：`PlayGlobal 0x750920` = 116 调用点 / 69 调用者函数 / 8 直接被调者**
复算：调用点 `python work/baseline_check.py`（byte E8 rel32 = 116，capstone skipdata 交叉集合全等 = 116）；直接被调者 `work/gather_evidence.py` 得 8 个（与 atlas `n_callees=8` 一致）；69 调用者函数 **引用 §968 已入账值，不重数**（66 作废）。

## 交付清单
`PROGRESS.md` / `TARGETS.tsv` / `NAMES.md` / `LAYOUT.md` / `UNKNOWNS.md` / `DISAGREE.md` / `coverage_delta.tsv` / `EVIDENCE\{numeric_summary,t2_naming_evidence}.txt` / `work\*.py`。未改 `COVERAGE\coverage.tsv`/台账/游戏文件；未 git commit；未跑真机。
