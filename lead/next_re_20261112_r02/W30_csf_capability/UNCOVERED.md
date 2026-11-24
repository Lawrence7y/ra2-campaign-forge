# UNCOVERED · W30（CSF 读写能力）未覆盖与不确定项

> 状态：**已完成并按实测口径锁定**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02`

1. **散装 `ra2md.csf` 能否覆盖 `langmd.mix` 内同名文件（核心引擎行为边界）**：
   - 本卡严格遵守纯离线红线，未启动 `gamemd.exe`、未挂接进程。**散装 `ra2md.csf` 放在游戏目录后引擎是否优先读取（覆盖 `langmd.mix` 内置的 `ra2md.csf`），以及在中文系统下是否真正替换 `BATTLEMD98.INI` `Description=RA2F:...` 为文本而非 `MISSING:'RA2F:...'`，本卡未验证，必须真机实测确认**。
2. **`install.py` 安装/备份/卸载链路尚未接入 `ra2md.csf`**：
   - 依任务书“只做最小接线、不改 `verify.py` 语义、不削弱 W26 用例”约束，本卡仅在 `builder.py` 可选生成 `ra2md.csf` 与 `csf_patch.json`，未让 `install.py` 将 `ra2md.csf` 写入游戏目录（亦避免在未真机确认覆盖规则前引入游戏目录 `ra2md.csf` 冲突）。
3. **非 `b' RTS'` / `b'WRTS'` 未知 CSF 值类型的跨记录边界**：
   - 两份官方 CSF（`ra2md.csf`、`ra2.csf`）全部 9,690 条记录仅含 `b' RTS'` 与 `b'WRTS'`。对于非标准第三方未知值类型，CSF 格式本身无通用字节长度前缀：若其出现在文件末尾，`csf.py` 完整保留原始字节并告警；若其出现在多条记录中间，因无法无歧义推断其长度，`parse_csf(..., strict=False)` 保留从该记录起至 EOF 的全部原始字节并停止后续增量改写（防止写坏文件），未尝试启发式猜长度。
4. **`mixlib.py` 的 `write_mix()` 仍沿用原 `crc_hash()`**：
   - 为满足 C6“不传 `--csf-out` 时产物（含 `expandmd98.mix`）与 v9 逐字节一致”，本卡仅新增 `ts_crc_hash()` 供 `MixFile.get()` 读取官方 MIX，未改动 `write_mix()` 使用的 `crc_hash()`（文件名长度非 4 的倍数时二者结果不同；对长度非 4 倍数的新地图名在真机 MIX 查找中的表现沿用既有构建基线，未在本卡改变）。
5. **非 Windows 平台与 W26 既有未覆盖项**：
   - 沿用 [W26 UNCOVERED.md](../W26_dlc_unseal_fix/UNCOVERED.md)（非 Windows POSIX 只读行为、`WinError 32` 锁句柄、`SIGINT` 异步中断等未独立实测）。
