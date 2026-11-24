# S19-F1 · UNKNOWNS

| # | 未决项 | 现状 | 需要什么 |
|---|---|---|---|
| U1 | 播放入口调用数双通道差异（**已裁决，非未决**） | capstone 线性 sweep = 116 sites；Ghidra xref = 110。差 6 处全是 atlas gap 内的合法 `E8 call`（逐条反汇编证实）；Ghidra 集合是 capstone 的真子集。 | 保留双列，不需进一步取证；见 `EVIDENCE/task2_dual_channel_gap_analysis.txt`、`DISAGREE.md` D1。 |
| U2 | `VocClass` 24 字段中 `+0x0C SamplesOK` 的读者 | 写者（ctor/load）与 INI 键已证，但运行时读点未单独定位。 | 定点扫 `0x4041D0`/`0x405190` 中 `[reg+0xC]` 的 this 来源；或运行时验证。 |
| U3 | `+0x9C SampleIndices` / `+0x11C NumSamples` 的精确读写者 | 结构偏移与 load 路径已证（INI parse fn 写 sample 索引），但写者/读者地址未逐条列出。 | 对 `0x405170`/`0x405190` 上下文做 this 溯源后补。 |
| U4 | 音量字段偏移与 YRpp 头冲突 | 本次 `fld dword` 实证 `0xA8EB98/9C/A0`；YRpp `GameOptionsClass.h` 标 `SoundVolume@+0x30(0xA8EB90)/VoiceVolume@+0x34/ MovieVolume@+0x38`。 | 见 `DISAGREE.md` D2。需以 `RulesClass::Load_INI` 中键→字段写入点定谳（本卡未穷举）。 |
| U5 | VQA 与 Bink 的关系 | 本镜像既导入 `binkw32.dll` 又保留 `VQAClass::Advance_Frame`/`.VQA` 字符串；`0x759C30`(VQAClass) 与 `0x432C70`(Bink) 是两条独立实现，谁在何种电影/平台被选、切换判据未查。 | 追 `0x5BED40`/`0x5C0550` 的分支条件与 `IsScoreRepeat`/画质开关。 |
| U6 | `Theme=` 键到 `Theme::*` 的直接调用点 | "Theme"@`0x824194` 有 4 imm xrefs（`0x4F1CA0/0x689E90/0x68AD70/0x76CA60`），但未逐条确认哪一个是 INI 读取并触发 `QueueSong`/`Stop`。 | 细读这 4 处函数并做键→函数映射。 |
| U7 | 300 槽池分配 `0x405190` 的 4 个调用者中"非 Play 入口"的那个 | 4 sites/4 fns 已列（`EVIDENCE/task2_callers_00405190.txt`），其中 `0x4066C0` 等需确认语义。 | 读 `0x4066C0` 等函数上下文。 |
| U8 | EVA 名→索引表 `[0xB1D4A4]` 的构建函数 | 已证 QueueVoice 用 stricmp 扫该表；表由谁从 INI/[EVA] 段填充未查（本卡只追播放链）。 | 追对 `[0xB1D4B0]` count 的写点。 |
| U9 | `AudioInit 0x409470` 在 function_atlas 中为 gap | 本卡实测它是真函数入口（前接 `0x40946A ret` + 5×nop，序言 `sub esp,0x400`/`push ebx..`），Ghidra 亦报 1 处引用（来自 data `0x81636C` 函数指针）。atlas 缺它是覆盖表缺口。 | 合并员可据本卡 `coverage_delta.tsv` 的 GAP 标注补入 atlas；非本卡写域。 |
