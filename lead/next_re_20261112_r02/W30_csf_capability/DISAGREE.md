# DISAGREE · W30 与任务书前提及既有代码假设的分歧记录

> 状态：**已完成并经实测印证**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02`

## 1. 勘误：`mixlib.py` 既有 `crc_hash()` 无法匹配 `langmd.mix` / `language.mix` 中的 `ra2md.csf` / `ra2.csf`

- **任务书前提**：提示“用项目自带 `mixlib.py` 提取到你的写域”。
- **实测事实**：直接调用 v9 `MixFile("ra2youli/langmd.mix").get("ra2md.csf")` 返回 `None`，`MixFile("ra2youli/language.mix").get("ra2.csf")` 亦返回 `None`。
  - 根因：v9 [mixlib.py](../W26_dlc_unseal_fix/ra2forge_patched_v9/ra2forge/mixlib.py#L205-L207) 的 `crc_hash()` 直接计算 `zlib.crc32(filename.upper().encode("ascii"))`，而 Westwood TS/RA2 引擎对文件名长度非 4 的倍数的条目在算 CRC-32 前会做 4 字节尾部填充（例如 `"RA2MD.CSF"` 9 字节填充后 CRC-32 为 `0xbd835079`，而直接 CRC-32 为 `0x42cbedcb`；`"RA2.CSF"` 7 字节填充后为 `0x7f6fbcdf`，直接 CRC-32 为 `0x0adb1469`）。
- **本卡处置**：在 v10 [mixlib.py](ra2forge_patched_v10/ra2forge/mixlib.py#L211-L218) 新增 `ts_crc_hash()` 并在 `MixFile.get()` 中作为候选 ID 一并匹配，使 `MixFile.get("ra2md.csf")` 与 `MixFile.get("ra2.csf")` 直接可用；同时**保留原 `crc_hash()` 与 `write_mix()` 不变**，确保不传 `--csf-out` 时产物 `expandmd98.mix` 与 v9 100% 逐字节相同（C6 硬证据）。

## 2. 事实澄清：官方 `ra2.csf` 存在 3 对仅大小写不同的重复标签

- **实测事实**：`ra2md.csf` 5,211 条标签大小写不敏感亦无碰撞；但 `ra2.csf` 4,479 条标签中存在 3 对仅大小写不同的条目（`txt_defense_tab` / `TXT_DEFENSE_TAB`、`txt_structure_tab` / `TXT_STRUCTURE_TAB`、`txt_structure_tab_desc` / `TXT_STRUCTURE_TAB_DESC`）。
- **本卡处置**：`CsfFile.set()` 与 `append_or_set_label()` 默认采用**精确匹配**（`case_insensitive=False`），因此对官方文件追加新标签时不会误吞或折叠原文件中的任何一对条目，保证“原有标签一条不丢”；同时保留 `case_insensitive=True` 可选参数。

## 3. 回归用例命名避让：W26 已有 `C1` / `C2`，新增 CSF 用例记为 `CSF1`–`CSF6`

- **事实**：`regress_dlc_v9.py` 的 39 个用例中已包含向后兼容用例 `C1` 与 `C2`。
- **本卡处置**：完整保留全部 39 个 W26 用例名称与语义（仅在 `P4` 将 `TOOL_VERSION` 断言由 `"0.9"` 随版本演进同步为 `"1.0"`），将 T4 新增的 C1–C6 记为 `CSF1`–`CSF6`（共 45 用例）。
