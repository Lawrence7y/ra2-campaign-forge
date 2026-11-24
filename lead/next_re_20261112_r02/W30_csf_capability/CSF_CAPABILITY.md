# CSF_CAPABILITY · W30 CSF 字符串读写能力与构建接线说明

> 状态：**已完成纯离线实现与全量验证**
> 日期：2026-11-13 ｜ run_id = `NEXT_RE_20261112_R02` ｜ 工具版本 `1.0`

---

## 1. CSF 二进制格式解析实证（官方 `ra2md.csf` / `ra2.csf`）

通过为 [mixlib.py](ra2forge_patched_v10/ra2forge/mixlib.py) 补齐 Westwood TS/RA2 的 4 字节尾部填充文件名哈希 `ts_crc_hash()`（见 [DISAGREE.md](DISAGREE.md) §1），直接从只读官方 MIX 中提取出两份真实 CSF 文件并在沙箱完成逐字节结构解析：

| 官方文件 | 来源 MIX | Entry ID (`ts_crc_hash`) | 字节大小 | 版本 | 标签数 | 字符串数 | 语言码 | 值类型分布 | 尾随字节 |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| `ra2md.csf` | `ra2youli/langmd.mix` | `0xbd835079` | 332,973 B | 3 | 5,211 | 5,211 | 9（中文） | `b' RTS'`: 4,007，`b'WRTS'`: 1,204 | 0 B |
| `ra2.csf` | `ra2youli/language.mix` | `0x7f6fbcdf` | 283,368 B | 3 | 4,479 | 4,479 | 9（中文） | `b' RTS'`: 3,275，`b'WRTS'`: 1,204 | 0 B |

### 1.1 头部结构（24 字节，小端序 `<4sIIIII`）

- `0x00`（`4s`）：魔数 `b' FSC'`（`0x43534620`，即小端序 `"CSF "`）。
- `0x04`（`I`）：版本号（官方为 `3`；解析器兼容 `2`/`3`）。
- `0x08`（`I`）：`num_labels`（` LBL` 记录总数）。
- `0x0C`（`I`）：`num_strings`（所有标签下的值记录总数）。
- `0x10`（`I`）：`unused`（保留/未使用字段）。**实测两份官方 CSF 的该字段均为 `0x00000000`**，且文件末尾 `trailing == 0`——**CSF v3 不含 CRC/校验和字段，也不含偏移索引表**。
- `0x14`（`I`）：`language`（语言码；`0` = English US，官方中文版 `ra2md.csf`/`ra2.csf` 为 `9`）。

### 1.2 标签与值记录

- **标签头（`12 + name_len` 字节）**：`b' LBL'`（`<4sII`）+ `num_values` + `name_len` + ASCII 标签名。
- **值类型 `b' RTS'`（小端 `"STR "`）**：`char_count`（`I`，UTF-16LE 码元数）+ `char_count * 2` 字节（每字节按 `b ^ 0xFF` 按位取反编码）。
- **值类型 `b'WRTS'`（小端 `"STRW"`）**：在 `b' RTS'` 之后追加 `extra_len`（`I`）+ `extra_len` 字节 ASCII 扩展名（例如 `VOX:ceva001` 的 `b'ceva001c'`）。
- **其它未知值类型**：在 `strict=False`（`read_csf` / `parse_csf` 默认）时，**如实记录告警并保留原始字节**（`CsfFile.warnings` / `unknown_records` / `CsfValue.raw_bytes`），不静默丢弃；在 `strict=True` 时显式抛出 `CsfError` 并标注偏移量与标签名。

---

## 2. 读写与往返验证实现（`ra2forge/csf.py`）

核心模块：[csf.py](ra2forge_patched_v10/ra2forge/csf.py)（纯 Python 标准库，零第三方依赖）。

1. **解析与严格校验**：`parse_csf()` / `read_csf()` 对截断头部、错误魔数、不支持版本、截断标签/值载荷、非法 UTF-16LE 与非 ASCII 标签名均抛出 `CsfError`。
2. **安全写入与原子替换**：`write_csf()` 先完成全量字节序列化并在内存中调用 `parse_csf(..., strict=True)` 自检，再通过同目录临时文件 + `os.replace()` 原子替换，确保异常情况下不写坏目标文件。
3. **`append_or_set_label(csf_path, label, text, ...)`**：
   - 若文件已存在，先用 `read_csf(..., strict=True)` 严格解析并快照全部既有标签与值；若畸形则直接报错退出，原文件字节零改动（`CSF5` 实测验证）。
   - 按精确标签名查找：存在则更新（不翻倍计数，`CSF3` 实测验证），不存在则追加。
   - 重写时保持 `num_labels`、`num_strings`、`unused`、`language` 与其余全部标签（含所有 `WRTS` 扩展名）完整不变。
   - **写后必做磁盘往返自检**：重新调用 `read_csf(p, strict=True)` 读回，断言目标标签文本逐字节一致、计数与既有全部标签逐条未变。
4. **官方 CSF 抽样与往返实证**：
   - 官方 `ra2md.csf` 原始解析再编码 `orig.to_bytes() == raw`：**100% 逐字节一致**（`ra2.csf` 同为 `True`）。
   - 抽样官方标签：`DESC:ALL1` = `'盟軍戰役 - 愛國者之熱血'`，`DESC:SOV1` = `'蘇聯戰役 - 毀天滅地大行軍'`，`VOX:ceva001` = `('警告：偵測到核彈發射井。', extra='ceva001c')`。
   - 对官方 `ra2md.csf` 追加新标签 `RA2F:TEST0001` 后读回（见 [out/CSF2.log](out/CSF2.log)）：标签数 `5211 -> 5212`，字符串数 `5211 -> 5212`，新标签逐字节一致，原有 **5,211 条标签与所有 `WRTS` 扩展名 100% 不变**。

---

## 3. 与 `builder.py` / `cli.py` 的最小接线

- **新增可选 CLI 开关**：`ra2forge build` 新增 `--csf-out PATH`（及可选 `--csf-base CSF_PATH`）。
  - **不传 `--csf-out` 时**：行为与 v9 **100% 逐字节一致**（`CSF6a` 实测对比 `out_v9` 与 `out_v10` 全部 7 个输出文件 SHA-256 与字节长度完全相同）。
- **传入 `--csf-out PATH` 且 design 存在非空 `campaign.description` 时**：
  1. `csf_label_for()` 生成稳定标签名 `RA2F:<8位SHA256大写十六进制>`（优先取 `design.package.id`，未声明时确定性回退 `battle:<battle_id>:<campaign.name>`），避免与 `DESC:ALL1` 等官方标签冲突。
  2. `BATTLEMD98.INI` 的 `Description=` 写入该标签（不再直接写原始文本）。
  3. 写入/更新 `--csf-out`（若指定 `--csf-base` 则先严格校验并克隆基础 CSF），并在产物目录生成可直接使用的 `ra2md.csf` 与结构化补丁清单 `csf_patch.json`。
  4. `BUILD_REPORT.txt` 新增 `csf_mode=enabled`、`csf_target=ra2md.csf`、`csf_label=...`、`csf_text=...`、`csf_instruction=...`，并在 `artifacts:` 中列出 `ra2md.csf` 与 `csf_patch.json`。
- `verify.py` 的既有语义完全未改；W26 全部 39 个用例无一削弱。

---

## 4. 能力边界与未真机验证声明

- **重要声明（严禁误读）**：本模块具备 CSF v2/v3 的离线读写与增量更新能力，但**散装 `ra2md.csf` 放置在游戏根目录时是否覆盖 `langmd.mix` 内的同名文件，属于游戏引擎自身的文件系统加载优先级行为，本卡为纯离线任务，未做验证，需真机实测定谳**。
- 本卡未修改 `install.py` 的安装清单逻辑，不会把 `ra2md.csf` 自动复制进游戏目录；若真机确认散装 `ra2md.csf` 可覆盖 MIX 内同名文件，仍需在后续安装策略卡片中显式纳入备份/卸载范围。
