# CONFIG_RESTORE · W15 RE-N04e

run_id `NEXT_RE_20261112_R02` ｜ 基线：`baseline_pre_launch\PRE_LAUNCH_BASELINE.tsv`

## 开工前核对（attempt1 与 attempt2 相同，均全过）

| 文件 | bytes | sha256 | 与 TSV 一致 |
|---|---|---|---|
| RA2MD.INI | 1754 | c91c6a47…d3c27d | ✔ |
| ddraw.ini | 14782 | c983abad…df9d52 | ✔ |
| RA2MD.INI.benchbak | 1754 | c91c6a47…d3c27d | ✔ |
| gamemd.exe | 4825360 | 73201cc0…f67476 | ✔ |
| ddraw.dll | 411648 | 85e0f7d5…283a03a9 前缀（完整值见 TSV） | ✔ |
| 载体 [8]试验地_Pro_ProvingGrounds.yrm | 175361 | 3e3c8745…bfd5b19 | ✔（卡面钉定值） |

统一条件（开局前逐字记录）：RA2MD `[Video]` ScreenWidth/Height=1366/768、VideoBackBuffer=no；
`[Skirmish]` GameSpeed=2；ddraw windowed=false / fullscreen=false / renderer=direct3d9 /
maxfps(gamemd)=60 / singlecpu=true / vsync=false。

## 收尾还原（attempt2，探针 finally 实算自证）

| 文件 | pre_restore_sha | post_restore_sha | 与基线逐字节一致 | sha_match |
|---|---|---|---|---|
| RA2MD.INI | （运行期被游戏改写） | c91c6a47… | ✔（read_bytes == baseline bytes） | True |
| ddraw.ini | （同上） | c983abad… | ✔ | True |
| RA2MD.INI.benchbak | （同上） | c91c6a47… | ✔ | True |
| gamemd.exe | — | 73201cc0… | verify_only | True（unchanged） |
| ddraw.dll | — | 85e0f7d5… | verify_only | True（unchanged） |

- 还原方式：从 `baseline_pre_launch\` 逐字节 `shutil.copyfile`，再 `sha256` + `read_bytes()` 双重实算自证。
- 文件清单差分（开工 647 项 vs 收尾 647 项）：added=0, removed=0, changed=0 —— **无任何遗留写回**。
  （运行期游戏对 INI 的正常改写已被还原覆盖；这是卡面授权的例外动作。）
- attempt1 同链路收尾亦完成（见 SAFETY.md）。

## 结论
配置最终态 = 基线态，字节级一致；载体与 exe/dll 未被触碰。
