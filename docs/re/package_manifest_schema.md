# RA2 DLC / 内容包清单 Schema v1 规范与使用说明

> 配套离线集成验证工具：`tools/validate_package_manifest.py`  
> 归属任务：`CONT-DLC01`（CONT-I1 离线等价集成）  
> 规范版本：`schema_version: 1`  
> 上游审计依据：`out/re_work/work_chain/IMPL001/dlc/`（已完成 C-AUD/r1/W1/F1/W3/R1/C-VERIFY-R2 收口）

---

## 1. 规范范围与安全红线声明

本规范定义《红色警戒 2》扩展内容包 / DLC 清单（`manifest.json`）的形态结构与安全约束。配套工具 `tools/validate_package_manifest.py` 为纯 Python 3 标准库实现的离线静态验证器。

### 1.1 核心边界与免责声明
1. **v1 仅验证清单形态**：本验证器只对清单文本进行 JSON 解析、字段形态、命名约束、结构依赖与基础路径安全性进行离线检查。
2. **不验证磁盘内容与资产存在性**：验证器不会检查清单声明的文件是否存在于磁盘、包体或镜像中，也不会在此阶段校验磁盘文件的实际 SHA256 哈希值（磁盘哈希比对由示例验证脚本或安装器在后续阶段执行）。
3. **不验证游戏运行时、存档与联机兼容性**：验证通过仅代表清单符合分发规范，不保证内容加载后不破坏游戏引擎内存、不保证读档一致性、不保证联机同步确定性（Net-Sync Determinism）。

### 1.2 未来安装层（Installer）强制安全要求
> [!IMPORTANT]
> **清单验证器放行某路径，绝不代表该路径可以直接安全安装到磁盘或游戏目录。**

未来独立发布的安装层必须实施以下独立安全控制：
1. **拒绝 Windows 非法与歧义路径**：安装层必须拒绝包含 DOS/Windows 保留设备名（如 `CON`, `PRN`, `AUX`, `NUL`, `COM1`~`COM9`, `LPT1`~`LPT9`，无论是否有扩展名）、非法字符（`<>:"|?*`）、尾随空格或尾随点的路径。
2. **必须使用操作系统文件 API**：安装层必须通过高级文件系统 API（如 Python `os.replace`, `shutil.copy2`, Win32 API `CreateFileW`, `MoveFileExW`）执行文件写入、移动与覆盖。
3. **严禁拼接 Shell 命令行**：严禁通过 `cmd.exe /c`、PowerShell、`os.system()` 或任何拼接命令字符串方式解压、移动或安装文件，彻底杜绝任意命令注入风险。

---

## 2. 完整合法清单示例（规范格式）

```json
{
  "schema_version": 1,
  "package_id": "soviet-covert-ops",
  "version": "2.10.5",
  "target_exe": "gamemd.exe",
  "target_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "files": [
    {
      "path": "ini/rulesmd.ini",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    },
    {
      "path": "maps/battlemd98.ini",
      "sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    },
    {
      "path": "maps/mission02.map",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    }
  ],
  "dependencies": [
    "base-core-assets",
    "yuri-exp-v1"
  ],
  "conflicts": [
    "incompatible-overhaul"
  ]
}
```

---

## 3. 字段规则与语义约束

### 3.1 顶层字段规范

| 字段 | 类型 | 是否必填 | 规范与约束 | 失败报障路径 |
|---|---|---|---|---|
| `schema_version` | 整数 | 是 | 必须严格为整数 `1`。布尔值（`true`/`false`）严格拒绝（`is_strict_int` 门禁）。 | `/schema_version` |
| `package_id` | 字符串 | 是 | 长度 1..64 字符。正则 `^[a-z0-9][a-z0-9-]*$`。仅允许小写字母、数字、连字符，必须以字母或数字起始。拒绝大写、下划线、空格、点。 | `/package_id` |
| `version` | 字符串 | 是 | 语义版本号，格式为 `X.Y.Z`。正则 `^(0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*)\.(0\|[1-9][0-9]*)$`。必须为 3 段非负整数，拒绝前导零（如 `01.0.0` 拒绝，`0.0.0` 合法）。 | `/version` |
| `target_exe` | 字符串 | 是 | 目标游戏执行文件，不区分大小写，规范化后仅限 `game.exe` 或 `gamemd.exe`。拒绝 `ra2.exe`、`ra2md.exe` 等其它名称。 | `/target_exe` |
| `target_sha256` | 字符串 | 是 | 目标主执行程序的 SHA256 指纹。必须为 64 位十六进制字符串（`^[0-9a-fA-F]{64}$`），规范化输出小写。 | `/target_sha256` |
| `files` | 数组 | 是 | 文件项清单，必须为非空数组（至少包含 1 个文件项）。详细约束见 §3.2。 | `/files` |
| `dependencies` | 数组 | 否 | 依赖的内容包 ID 列表。缺省时规范化为 `[]`。元素必须符合 `package_id` 规范；拒绝重复；拒绝自引用；拒绝与 `conflicts` 重叠。 | `/dependencies`, `/dependencies/<idx>` |
| `conflicts` | 数组 | 否 | 互斥的内容包 ID 列表。缺省时规范化为 `[]`。元素必须符合 `package_id` 规范；拒绝重复；拒绝自引用；拒绝与 `dependencies` 重叠。 | `/conflicts`, `/conflicts/<idx>` |

### 3.2 文件项（`files[i]`）规范

每个文件项必须是一个包含以下字段的 JSON 对象：

| 字段 | 类型 | 是否必填 | 规范与约束 | 失败报障路径 |
|---|---|---|---|---|
| `path` | 字符串 | 是 | 相对包内路径。必须为非空字符串。详细安全与 Windows 等价规则见 §3.3。 | `/files/<idx>/path` |
| `sha256` | 字符串 | 是 | 包内该文件的 SHA256 哈希值。必须为恰好 64 位十六进制字符串，规范化输出统一为小写。 | `/files/<idx>/sha256` |

### 3.3 路径安全与 Windows 等价归并规则（D7 / D9）

1. **绝对路径与跨卷禁止**：
   - 严禁以 `/` 或 `\` 起始的根路径（如 `/maps/a.map`）。
   - 严禁 Windows 驱动器绝对或相对路径（正则 `^[a-zA-Z]:`，如 `C:foo.map`, `D:\bar.ini`）。
   - 严禁 UNC 网络路径（正则 `^(\\\\|//)`，如 `\\server\share\file`）。
   - 严禁包含 NUL 截断字符（`\0`）。
2. **目录穿越与分隔符规范化**：
   - 路径中的反斜杠 `\` 统一视作路径分隔符并规范化为正斜杠 `/`。
   - 严禁目录穿越组件 `.` 与 `..`（如 `maps/../game.exe`）。
   - 严禁空组件或连续分隔符（如 `maps//mission.map`、`maps/`）。
3. **Windows 尾随空格与点等价归并（Trailing Space / Dot Stripping）**：
   - Windows Win32 子系统在创建文件与目录时，会自动剥离每个路径组件末尾的空格与点。
   - **组件归并后为空即拒绝**：若任一路径组件经 `c.rstrip(" .")` 处理后为空字符串（例如纯空格 `' '`、纯点 `'.'`、或点与空格混合 `' . '`），该路径存在歧义或逃逸风险，验证器立即判定非法并拒绝（例如 `maps/ . /test.map`）。
   - **Windows 判重等价键**：判重时不以原始字符串比对，而是使用每个组件剥离尾随空格与点并转为小写后的规范键：
     $$\text{canonical\_path} = \text{"/"}.\text{join}(c.\text{rstrip}(" .") \text{ for } c \text{ in components}).\text{lower}()$$
     若不同文件项的 `canonical_path` 发生碰撞（例如 `maps/mission.map` 与 `maps/mission.map ` 或 `MAPS/mission.map`），判定为路径重复碰撞并拒绝。
4. **保留系统文件名防覆盖（Reserved Filenames）**：
   - 为防止内容包意外破坏游戏关键主文件，路径最后一段（文件名）在剥离尾随空格和点后，不区分大小写匹配以下 5 个保留名称时一律拒绝：
     - `game.exe`
     - `gamemd.exe`
     - `ra2.exe`
     - `ra2md.exe`
     - `battlemd.ini`
   - 合法扩展命名（如 `battlemd98.ini`, `battlemd99.ini`）允许放行。

### 3.4 严格未知字段策略（Strict Schema Rejection）

- **顶层严格门禁**：清单顶层仅允许 `ALLOWED_TOP_LEVEL_KEYS`（共 8 个键）。若存在任何未声明的顶层键（例如 `"author"`, `"description"`, `"notes"` 等），验证器立即报错 `/key: Unrecognized top-level field` 并返回 exit 2。
- **文件项严格门禁**：文件项中仅允许 `path` 与 `sha256` 两个键。若存在任何额外键（例如 `"size"`, `"compressed_sha256"` 等），验证器报错 `/files/<idx>/key: Unrecognized file entry field` 并返回 exit 2。
- **设计初衷**：防止作者笔误漏检（如拼错字段名）、防止未版本化的私有元数据漂移、杜绝利用未知字段进行未审计的信息走私。

### 3.5 声明路径输出保真（Declared Path Output Fidelity）

- 在验证通过后的规范化清单输出中，`files` 列表中的 `path` 字段**严格保留作者原始声明的字面值**（仅统一将反斜杠 `\` 规范化为正斜杠 `/`）。
- **保留原始大小写与尾随字符**：Windows 等价判重剥离尾随空格/点仅用于安全判定与查重，不改变输出字符串的原始形态，确保包内路径声明的忠实还原。

### 3.6 ASCII 码点排序（ASCII Codepoint Sorting）

- 验证通过并输出规范化清单时，`files` 数组严格按照文件项的 `path` 字段升序排列（按标准 Python 字符串比较 / Unicode ASCII 代码点升序排序：`normalized_files.sort(key=lambda x: x["path"])`）。
- 保证输出清单的完全确定性与跨平台一致哈希。

---

## 4. 命令行接口与退出码规范

### 4.1 CLI 语法

```bash
python tools/validate_package_manifest.py [-h] [--json] [--quiet] [--out OUT] manifest
```

| 参数 | 说明 |
|---|---|
| `manifest` | 目标清单 JSON 文件路径（只读打开，必须为有效 UTF-8 编码） |
| `--json` | 校验失败时，以结构化 JSON 格式输出错误列表至 stdout（格式见 §4.3） |
| `--quiet` | 校验成功时静默，不向 stdout 输出规范化清单内容 |
| `--out OUT` | 校验成功时，将规范化后的 JSON 清单写入指定的输出文件路径 |
| `-h, --help` | 显示使用帮助并以退出码 0 退出 |

### 4.2 退出码定义

| 退出码 | 状态 | 触发条件与行为 |
|---|---|---|
| `0` | **成功（VALID）** | 清单完全符合 schema v1 及全部安全规则。stdout 输出规范化 JSON（除非 `--quiet`）。 |
| `2` | **验证失败（INVALID）** | 清单违反 schema 字段要求、格式规则、路径安全或唯一性约束。输出包含具体的 JSON Pointer 字段路径（如 `/files/0/path`）。 |
| `3` | **错误（ERROR）** | 外部与环境错误：命令行用法错误、参数缺失、文件不存在、不可读、非 UTF-8 编码、或 JSON 语法解析错误（Syntax Error）。 |

### 4.3 结构化 JSON 错误格式（`--json`）

当传入 `--json` 且清单存在形态或规则错误时，工具在 stdout 产生符合以下格式的 JSON：

```json
{
  "valid": false,
  "error_count": 1,
  "errors": [
    {
      "path": "/files/0/path",
      "message": "Reserved filename 'game.exe ' (Windows equivalent 'game.exe') is prohibited"
    }
  ]
}
```

---

## 5. 常见错误代码与排查指引

| 错误信息特征 | 常见原因 | 修复指引 |
|---|---|---|
| `Field 'schema_version' must be integer 1` | 提供了布尔值 `true` 或数字 `2` | 确保写为 `"schema_version": 1` |
| `Unrecognized top-level field '...'` | 存在非标准元数据字段（如 `author`） | 删除未知顶层字段，符合严格 schema 策略 |
| `Duplicate path '...' (case-insensitive Windows equivalence collision)` | 两个文件仅大小写或尾随点/空格不同 | 检查包内文件路径，确保规范化后互斥 |
| `Reserved filename '...' is prohibited` | 文件名为 `gamemd.exe` 或 `battlemd.ini` | 改用游戏补丁或战役编号命名（如 `battlemd98.ini`） |
| `Path '...' contains prohibited component consisting only of spaces or dots` | 路径组件包含纯空格或纯点（如 `/ . /`） | 清理路径组件，避免利用空格/点逃逸 |
| `Package ID '...' appears in both 'dependencies' and 'conflicts'` | 同一包 ID 同时出现在依赖与互斥中 | 依赖与互斥必须互斥，移除逻辑冲突项 |

---

## 6. 工具集成演进记录

- **IMPL001 原型研发**：由 Antigravity CLI 实现原型 `out/re_work/work_chain/IMPL001/dlc/worker/validate_package_manifest.py`，经多轮审计与 60 组官方 fixtures 校验通过（sha256: `e9584e340f49cb2fee12c356a3f83628f69c694a23911f47fe5d461e44194968`）。
- **CONT-DLC01 离线工具集成**：由 CONT-I1 将原型等价集成至项目公共工具目录 `tools/validate_package_manifest.py`，保持 100% 行为等价、字节一致与 60/60 fixture 全量 PASS。
