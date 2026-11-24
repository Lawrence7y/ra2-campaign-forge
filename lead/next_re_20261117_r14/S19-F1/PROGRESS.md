# S19-F1 · PROGRESS（结论表 · 分级 · 复算）

## 结论表

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | dsound.dll 仅导入 ordinal#1（DirectSoundCreate），IAT `0x7E1050` → 唯一 thunk `0x7C89DA`；唯一调用点 `0x40948E` 在 AudioInit `0x409470`（atlas gap） | `[已证]` | `EVIDENCE/task1_summary.txt`、`task1_init_409470.txt` |
| 2 | AudioInit 建 IDirectSound→SetCooperativeLevel→CreateThread(proc=`0x4095B0`)；`0x4095B0` 调 IDirectSoundBuffer 的 GetStatus/GetCurrentPosition/Stop/Lock/Unlock/Restore，是**喂缓冲线程** | `[已证]` | `EVIDENCE/task1_thread_4095B0.txt` |
| 3 | 每帧更新入口 `0x406F70`（AudioFrameUpdate）：重入锁 `[0x87E75C]`，33ms 门 `cmp eax,0x21`，门内 5 子步 `0x4041D0/0x750EC0/0x752760/0x7209D0/0x7B84D0`；2 调用点 `0x48D08C`/`0x607F0A` | `[已证]` | `EVIDENCE/task1_frame_406F70.txt` |
| 4 | `VocClass` **24 字段**（0x148 B）；13 个 INI setter 全由 parse fn `0x750440` 调用，键名/偏移逐字符核对；读者在 `0x4041D0`/`0x405190` | `[已证]` | `EVIDENCE/task2_ini_writers_406500.txt`、`task2_reader_summary.txt`、`task2_ini_parse_00750440.txt` |
| 5 | 播放函数 `0x750920` PlayGlobal = **116 调用点 / 66 调用者函数**；另有 `0x7509E0`(97/65)、`0x750E20`(18/10)；VoiceAlloc `0x405190` 4/4 | `[已证]` | `EVIDENCE/task2_callers_00750920.txt`、`task2_explore_summary.txt` |
| 6 | 一次性（VocClass，300 槽池）vs 流式（AudioStream `[0xB1D4CC]`，`0x407B60`）区分明确；Theme 停止 `0x720EA0`，播放 `0x720BB0`，AI `0x7209D0`（唯一 caller `0x406F70`） | `[已证]` | `EVIDENCE/task3to5_dump_summary.txt`、`task3to5_Theme_Stop_00720EA0.txt` |
| 7 | EVA：事件名串 `ECX=0x819030`("EVA_StructureSold") → `call 0x752700` @`0x449CE5` → stricmp 名→索引表 `[0xB1D4A4]/[0xB1D4B0]` → `0x752480` 入队 → `0x752760` → `0x407B60` 专用流 | `[已证]` | `EVIDENCE/task4_EVA_StructureSold_trigger_00449C30.txt`、`task4_EVA_QueueVoice_00752700.txt` |
| 8 | VQA/Bink 过场**阻塞主循环**：`0x432C70` 自持消息泵 + 4 条回边到 `0x432CB8`，`BinkDoFrame 0x432E40`；期间主循环 `0x52D9A0` 不推进 | `[已证]` | `EVIDENCE/task5_bink.txt`、临时 dump 见 `work/task4to6_deep.py` |
| 9 | 音量存 `GameOptionsClass::Instance 0xA8EB60` 的 float 字段；`fld dword` 实证 `0xA8EB98/9C/A0`；INI 键 "SoundVolume/VoiceVolume/ScoreVolume" 在 `.data 0x832Fxx/0x8330xx`（表驱动） | `[静态推断]`（偏移与 YRpp 冲突） | `EVIDENCE/task6_volume.txt` |

## 分级说明
- `high`（子系统归属置信度）与 `[已证]`（证据等级）是两个量纲，本卡不混用。
- `VocClass` 类名取已入账交叉事实，非本次 RTTI 新发现（该类无自身 TD，仅 `VectorClass<VocClass*>` 模板名），未触发 §965 fail-closed。

## 1–3 核心数字及复算方法

**数字 1：`VocClass` 字段数 = 24**（0x148 B）
复算：`python work/task2_writers.py` → parse fn `0x750440` 的 13 个 setter 覆盖 15 个 INI 字段槽；`task2_reader_summary.txt` 读者证据补全结构字段（链表头/活跃计数/实例表/采样表）；`FLOW.md §3` 逐行计数 = 24。对照：`audio_engine_deep_dive.md` 列 24 行（线索一致）。

**数字 2：播放函数 `0x750920`，116 调用点 / 66 调用者函数（Ghidra 110）**
复算（通道 A，不依赖 atlas entry+size）：`python work/task2_explore.py` → capstone 全 `.text` 线性 sweep（`skipdata=True`，1,394,120 指令 / 跳过 66 字节）得 `sites=116`；`Atlass.containing()` 函数区间包含得 `caller_fns=66`（atlas `n_callers=110` 是不同量纲）。
复算（通道 B，Ghidra 12 函数感知 xref）：`EVIDENCE/ghidra_xref_full.txt` → `getReferencesTo(0x750920)=110`。**Ghidra 的 110 个站点是 capstone 116 个的真子集；差 6 处（`0x63A2FF/0x63A352/0x63A3E4/0x63A437/0x6E1772/0x6EDEA6`）全部是 atlas gap，但每一处都是合法 `E8 rel32 call 0x750920`（`EVIDENCE/task2_dual_channel_gap_analysis.txt` 逐条反汇编证实）。** 这正是纪律 1「两条通道都依赖 atlas 边界会一起漏」的实证：通道 A 不依赖 atlas 故多覆盖 6 处。
区分：`调用点数`=直接 `call` 指令条数（capstone 116 / Ghidra 110）；`调用者函数数`=站点按函数区间去重后的函数个数（66）；`atlas n_callers`=110（atlas 自身计数，恰与 Ghidra 相等但不同来源）。三者不可互换。
同类差异：PlayAt 97/96、PlayIndexAtPos 18/15、EVA QueueVoice 77/75、ThemeStop 27/20，cap-only 站点全在 atlas gap（`EVIDENCE/task2_dual_channel_diff.txt`）。

**数字 3：EVA 链 4 调用跳 + VQA 阻塞 = 是**
复算：`grep -E "752700|752480|752760|407B60" EVIDENCE/task2_callers_*.txt` + `EVIDENCE/task4_*.txt`；VQA 回边见 `task5_bink.txt` 配套 dump（4 条 `jxx → 0x432CB8`）。

## 停机核验
- 目标 SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` = 给定 `73201CC0…F67476` ✓
- 116/97/18 与 `audio_throttle_landing.md` 线索值（116/97/18）一致 ✓（线索仅作交叉，不作为证据）
- 未改任何台账/覆盖表/游戏文件；未 git commit。
