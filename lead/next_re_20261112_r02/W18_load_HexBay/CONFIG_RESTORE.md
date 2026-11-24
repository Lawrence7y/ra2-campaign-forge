# CONFIG_RESTORE · W18 RE-N04g（HexBay B′ 臂）

基线：`baseline_pre_launch\`（PRE_LAUNCH_BASELINE.tsv + 三份副本），开工五文件哈希守卫全 match（探针 S0）。

## 还原结果（探针 finally，逐字节拷贝 + 实算自证）

| 文件 | pre_restore sha256 | post_restore sha256 | byte_identical_to_baseline | sha_match | tsv_matches_copy |
|---|---|---|---|---|---|
| RA2MD.INI | c91c6a47…3c27d | c91c6a47…3c27d | **True** | **True** | True |
| ddraw.ini | c983abad…f9d52 | c983abad…f9d52 | **True** | **True** | True |
| RA2MD.INI.benchbak | c91c6a47…3c27d | c91c6a47…3c27d | **True** | **True** | True |
| gamemd.exe | —（verify-only） | 73201cc0…f67476 | 未动 | **True**（=基线） | — |
| ddraw.dll | —（verify-only） | 85e0f7d5…3a03a9 | 未动 | **True**（=基线） | — |

## 运行期写回（如实记录）

- `written_back.changed = ["RA2MD.INI"]`：游戏进程退出时写回自身设置（预期行为，非探针写入）。
- 还原后 RA2MD.INI 与基线逐字节一致（上表）——写回已被基线副本覆盖。
- `added/removed = []`；inventory 647 项（启动前）→ 647 项（收尾后），无新增/丢失文件。

## 载体文件完整性

- `[8]黑心湾_HexBay.yrm`：开工 355,713 B / sha256 `cb6c5224efcdfc9a79455f5b95cd4aeb8b6efbb655fc99ede104aadfd536529d`；探针运行全程只读（RPM 走游戏进程内存，不落盘），未改动；收尾 inventory 无该文件变更记录。
