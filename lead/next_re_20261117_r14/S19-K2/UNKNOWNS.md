# S19-K2 · UNKNOWNS.md

| # | 未知项 | 为何不可定 | 下一步 |
|---|---|---|---|
| U1 | 派卡面 `S19 atlas 362 / named 46 (12.71%) / proved 21 (5.80%)` 与盘上 PANEL.md 不一致 | STATUS_BOARD「凡卡面 coverage/PANEL 数字以盘上现值为准」：盘上 `PANEL.md` 与 `coverage.tsv` 自数自洽均为 **atlas_n 357 / named_L 46 (12.89%) / named_S 40 (11.20%) / proved 21 (5.88%)**，`coverage.tsv` 全表 S19 行 358（1 行不在 atlas）。卡面 362 为过期截面 | 见 `DISAGREE.md` D1；本卡一律用盘上值 |
| U2 | `VocClass` 24 字段中 `+0xB4`/`+0x134` 的写者全集 | §968 已更正 `+0x9C/+0x11C`→`+0xB4/+0x134`，但本卡锚定方法内未枚举到 `[reg+eax*4+0xB4]` 的精确写点地址（前序 VERDICT 报 8 处索引式读） | 另卡用全 `.text` 索引式寻址穷举 + 槽位锚定 |
| U3 | Mixer/Stream/Theme/EVA "manager" 的 RTTI 类名与 GetSize 槽 | 全镜像无独立 TD（仅模板容器名 `DynamicVectorClass<VoxClass*>`、VectorClass/VocClass 等）；按纪律 5 fail-closed，不猜名 | 需真机 RTTI 或另卡从 COL 链反查 CHD |
| U4 | `AudioController::sub_4060F0/130/170/1D0/270/310` 6 条语义 | 无串引用、无 IAT 导入、字段访问不特异；仅知被 `PlayGlobal 0x750920` 中 5 条直接调用 | 需追 `ecx`（thiscall）来源 + INI setter 族配对 |
| U5 | `BinkMovieLoop 0x432C70` 是否真的"阻塞主循环" | 机理（自持消息泵 + 4 回边）已证；但"期间主循环 0x52D9A0 不推进"未查等价形式（4 个 CreateThread 线程、WndProc、`0x54F7xx` 环队）| 按 §968 降 `[静态推断]`、删"不推进"绝对表述；真机断点下 `0x432E40` 前后看 `0xA8ED84 frame` 是否推进 |
| U6 | 音量字段的绝对值 `0xA8EB98/9C/A0` 与 YRpp 头冲突 | 绝对值已入账（存档路径 `fld [esi+0x38/0x3C/0x40]`→`push "SoundVolume"/"VoiceVolume"/"ScoreVolume"`@`0x8330BC/A8/9C`），字段名归属按 §968 D2 更正 | 保留绝对值，字段名已更；不改前序结论 |
| U7 | WaveClass `+0x240` 分配点与 slot12 的"巧合"风险 | 双点闭合 3/3 命中（`push 0x240`→operator new 与 vtable slot12 imm 相等），量级约 1/1.9e8 以下，但本卡未做 independent audit 复算 | 可交审计独立复算 `work/wave_vt.py` + `work/final_verify.py` |
