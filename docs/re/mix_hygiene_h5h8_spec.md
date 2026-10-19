# MIX 卫生 · H5/H6/H8 安装器补丁规格（R-MIX-H568）

> 任务 **R-MIX-H568** · 产品加固规格 · 工作区 `D:\Project\ra2-campaign-forge`
> 依据：`docs/re/mix_hygiene_product.md` §1.4 / §2.3 / §4 缺口 **H5**（00–97 CRC 扫描）、**H6**（非补零幽灵）、**H8**（残留清扫）。
> 目标：为 `ra2forge/install.py` 提出**可实现补丁规格**（本文件只读 `ra2forge/**`，不改代码）。
> 可写域：`out/re_work/re_sprint/R_mix_h568/**`、本文件。未触碰 `ra2forge/**`、`tools/**`、台账/看板、`gamemd`。
> 证据等级：[实证] = 字节/文件:行/可复算哈希；[推演]；[待实测]。
> 交叉：`ra2forge/install.py`、`ra2forge/mixlib.py`、`ra2forge/cli.py`、`ra2youli/ra2forge_install.json` v0.3、`out/re_work/re_sprint/R_mix_prod/residual_cross.json`。

---

## [0] 一页结论

1. **H5**：安装前用 `mixlib.MixFile` 枚举游戏目录 `expandmd00–97.mix` 条目 ID，与包内 `ECH*.MAP` 的 `crc_hash`/`classic_hash` 求交；**≥1 命中 = WARN**（我们 98 会压过 00–97 同 CRC），不拒装。
2. **H6**：包内出现非 `expandmdNN.mix`（两位补零）的 MIX 名 → **拒绝安装**；游戏目录幽灵名（`expandmd9.mix` / 三后缀 / 大小写漂移）→ **WARN**，卸载 `--legacy` 时可扫。
3. **H8**：`*.old-pre-migrate`、`*.pre-migrate.bak`、清单外孤儿 `*.ra2forge.bak` 不在现有 `uninstall` 路径内；纳入 **`uninstall --legacy` 残留清扫**（默认只列表，`--sweep-residuals` 才删/隔离）。
4. **集成点**：`ra2forge_install.json` 新增 `hygiene` 段（H5/H6/H8 结果 + 扫描快照）；`preinstall_warnings` 扩展为 `preinstall_hygiene`；`uninstall` 读 `manifest.hygiene` 并在 `--legacy` 时执行 H8 清扫。
5. **验收**：20 条用例（含 **`expandmd98.mix.old-pre-migrate` 清扫**）见 §5 与 `out/re_work/re_sprint/R_mix_h568/acceptance_cases.json`。

---

## [1] 现网缺口定位（只读交叉）

| ID | 产品缺口 | 现网 `install.py` | 证据 |
|:--|:---|:---|:---|
| H5 | 扫描 `expandmd00–97` 是否含与 `ECH*.MAP` 同 CRC 条目 | **未做**（仅 99 存在性告警 `install.py:81-84`） | mix_hygiene_product.md §1.4-H5 |
| H6 | 拒绝/告警非补零 `expandmd*.mix` 幽灵 | **未做**（`MIX_NAME="expandmd98.mix"` 硬编码，`package_files` 不校验命名） | 同上 §1.4-H6、§4-A4 |
| H8 | 卸载后残留清扫 `*.old-pre-migrate` 等 | **未做**（`_uninstall_legacy` 只清 `ra2forge_uninstall.txt` 列表 / 已知 legacy 集） | 同上 §1.4-H8、§2.3 R1–R4、§4-D5 |

现网已覆盖（保持不动）：H1 99 告警、H2 额外 `BATTLEMD*.INI` 告警、backup 不覆盖、manifest sha256、`--force` 语义、legacy `BATTLEMD.INI` 保护。

---

## [2] H5：expandmd00–97 同 CRC 扫描

### 2.1 语义

- MIX 查找按 **CRC32(大写文件名)** 命中（`mixlib.crc_hash`，`mixlib.py:205-207`）；引擎不读「local mix database」。
- 装载序：`expandmd99 → … → expandmd00`，**大号先装 = 同 CRC 赢**。故 00–97 中与我们地图同 CRC 的条目会被 **98 覆盖**（我们压过补丁）；99 压过我们（已有 H1）。
- H5 的产品动作是 **告知覆盖关系**，不是拒装：用户可能有意用 98 替换旧包地图。

### 2.2 算法（可直接贴进 `install.py`）

```python
# 伪代码；实现落在 preinstall_hygiene(game, package_files)
MAP_NAME_RE = re.compile(r"^ECH\d+\.MAP$", re.I)

def _map_hash_ids(name: str) -> set[int]:
    from .mixlib import crc_hash, classic_hash
    return {crc_hash(name), classic_hash(name)}

def scan_h5_crc(game: Path, map_names: list[str]) -> list[dict]:
    """H5: expandmd00-97 entries colliding with package map hashes."""
    findings = []
    want: dict[int, str] = {}
    for n in map_names:
        for hid in _map_hash_ids(n):
            want[hid] = n
    if not want:
        return findings
    for slot in range(0, 98):                      # 00..97 inclusive
        mix_path = game / f"expandmd{slot:02d}.mix"
        if not mix_path.is_file():
            continue
        try:
            with MixFile(mix_path) as mf:
                for e in mf.entries:
                    if e.id in want:
                        findings.append({
                            "check": "H5",
                            "slot": slot,
                            "mix": mix_path.name,
                            "entry_id": f"{e.id:08X}",
                            "map": want[e.id],
                            "entry_size": e.size,
                            "who_wins": "ra2forge (98 loads before 00-97)",
                        })
        except (OSError, ValueError) as exc:
            findings.append({
                "check": "H5",
                "slot": slot,
                "mix": mix_path.name,
                "error": f"unreadable MIX: {exc}",
                "severity": "WARN",
            })
    return findings
```

### 2.3 阈值与失败处置

| 条件 | 阈值 | 级别 | 安装动作 | 失败处置 |
|:---|:---|:---|:---|:---|
| 00–97 无同 CRC | 命中数 = 0 | PASS | 静默 | — |
| 00–97 有同 CRC | 命中数 ≥ 1 | **WARN** | 继续安装；写入 `manifest.hygiene.h5` | 文案写明「98 将覆盖 <mix> 内 <map>（CRC <id>）」 |
| MIX 不可读 | 任一 | WARN | 继续；记录 error | 不阻塞（损坏补丁包不是我们的责任） |
| 99 有同 CRC | 命中数 ≥ 1 | **WARN-HIGH** | 继续；并入 H1 文案 | 明确「99 会覆盖我们的地图」 |
| 包内 MAP 名非 `ECH*.MAP` | — | 不扫 | 仅扫 `ECH*.MAP`（`package_files` 已收集 `*.MAP`） | 其它 MAP 同样纳入（见 2.4） |

**2.4 扫描集合扩展**：H5 不应只限 `ECH*.MAP`——凡 `package_files()` 返回的 `*.MAP` 全部纳入 `map_names`（向前兼容后续战役改名）。默认产品包为 `ECH01–03.MAP`。

**2.5 已知 CRC 常量**（`mixlib.crc_hash`，[实证] 可复算）：

| 名 | crc_hash | classic_hash |
|:---|:---|:---|
| `ECH01.MAP` | `0x8067D343` | `0x704D79CC` |
| `ECH02.MAP` | `0xC7C7A993` | `0x704D89CC` |
| `ECH03.MAP` | `0xFAA78023` | `0x704D99CC` |

匹配时 **crc ∪ classic 双集合**（`MixFile.get` 同口径，`mixlib.py:286-290`），防旧工具写 classic 的边角。

---

## [3] H6：非补零 / 幽灵 `expandmd*.mix`

### 3.1 语义

引擎槽位名固定 `EXPANDMD%02d.MIX`（`0x5301BA mov edi,0x63` → `dec edi/jns`）。下列文件**永远不会被装载**，但用户可能误以为生效：

| 形态 | 例 | 引擎 | 分类 |
|:---|:---|:---|:---|
| 一位数 / 未补零 | `expandmd9.mix` | 找不到 | **H6 幽灵** |
| 三位数 | `expandmd100.mix` | 找不到 | **H6 幽灵** |
| 后缀残留 | `expandmd98.mix.old-pre-migrate` | 找不到 | **H8 残留**（兼 H6 可见性） |
| 备份 | `expandmd98.mix.ra2forge.bak` | 找不到 | **H8 残留**（清单 backup 除外） |
| 大小写漂移 | `EXPANDMD98.MIX` | Windows 找到；跨平台风险 | **H6 soft** |
| 合法 | `expandmd98.mix` | 找到 | OK |

### 3.2 算法

```python
CANONICAL_EXPANDMD = re.compile(r"^expandmd(\d{2})\.mix$", re.I)   # 两位补零
GHOST_NAME         = re.compile(r"^expandmd(\d+)\.mix$", re.I)     # 数字位数≠2
ANY_EXPAND_GLOB    = "expandmd*"                                   # 宽松枚举

def scan_h6_ghosts(root: Path, *, source: str) -> list[dict]:
    """H6: non-canonical expandmd* names under `root`.
    source = 'package' | 'game'
    """
    findings = []
    for p in sorted(root.glob("expandmd*")):
        if not p.is_file():
            continue
        name = p.name
        if CANONICAL_EXPANDMD.match(name):
            if name != name.lower() or name != f"expandmd{int(CANONICAL_EXPANDMD.match(name).group(1)):02d}.mix":
                # EXPANDMD98.MIX / ExpandMd98.mix: Windows 可用，跨平台 WARN
                if name != name.lower():
                    findings.append({
                        "check": "H6", "kind": "case-drift", "name": name,
                        "source": source,
                        "engine_loads": "yes-on-windows",
                        "severity": "WARN",
                    })
            continue
        if GHOST_NAME.match(name):
            kind = "unpadded"          # expandmd9.mix / expandmd100.mix
        elif name.lower().endswith(".mix.old-pre-migrate") or ".old-pre-migrate" in name.lower():
            kind = "residual-suffix"   # 交给 H8，这里只标记
        elif name.lower().endswith(".ra2forge.bak") or name.lower().endswith(".pre-migrate.bak"):
            kind = "backup-suffix"     # 交给 H8
        else:
            kind = "other-expandmd"
        findings.append({
            "check": "H6", "kind": kind, "name": name, "source": source,
            "engine_loads": False,
            "severity": "REFUSE" if source == "package" and kind in ("unpadded", "other-expandmd")
                        else "WARN",
            "hint": "engine only loads EXPANDMD%02d.MIX (two-digit zero-padded)",
        })
    return findings
```

### 3.3 阈值与失败处置

| 场景 | 条件 | 级别 | 处置 |
|:---|:---|:---|:---|
| **包内** | 存在非 `expandmd\d{2}\.mix` 的 expandmd* 文件 | **REFUSE** | `install_package` 抛 `ValueError("package contains non-canonical MIX name …")`；不写任何文件 |
| **包内** | 包内 MIX 名正确但非小写（`EXPANDMD98.MIX`） | WARN | 继续；建议 rebuild 为 `expandmd98.mix` |
| **游戏目录** | `expandmd9.mix` / `expandmd100.mix` 等幽灵 | **WARN** | 继续；写 `manifest.hygiene.h6`；卸载 `--legacy` 时列入清扫候选 |
| **游戏目录** | 大小写漂移 | WARN | 继续 |
| **游戏目录** | 后缀残留（`.old-pre-migrate` / `.bak`） | WARN（转 H8） | 不在此拒装 |

**硬边界**：包内命名由构建方控制，必须硬拒；游戏目录是用户领地，只告警、不擅自改名/删除（删除权在 H8 的 `--sweep-residuals`）。

---

## [4] H8：残留清扫（含 `expandmd98.mix.old-pre-migrate`）

### 4.1 残留分类（对照 residual_cross.json R1–R6）

| 类 | glob / 判据 | 示例 | 风险 | 清扫权 |
|:---|:---|:---|:---|:---|
| **A. pre-migrate** | `*.old-pre-migrate` | `expandmd98.mix.old-pre-migrate` (43702B，内含旧 `BATTLEMD.INI`+XCC db+3 MAP) | **中**：误改名会复活旧覆盖包 | `--sweep-residuals` 删或隔离 |
| **B. pre-migrate bak** | `*.pre-migrate.bak` | `ra2forge_uninstall.txt.pre-migrate.bak` | 低 | 同上 |
| **C. 孤儿 backup** | `*.ra2forge.bak` 且 **不在** `manifest.files[].backup` | `BATTLEMD.INI.ra2forge.bak`、`expandmd98.mix.ra2forge.bak` | 低–中（旧覆盖件备份） | 同上；有 forge marker 的先隔离 |
| **D. removed bak** | `*.ra2forge.removed.bak` | `BATTLEMD.INI.ra2forge.removed.bak` | 低 | 同上 |
| **E. 在用 backup** | 命中 `manifest.files[].backup` | `ECH01–03.MAP.ra2forge.bak` | — | **禁止清扫**（卸载还原源） |
| **F. 清单自身** | `ra2forge_install.json` / `ra2forge_uninstall.txt` | — | — | 已有路径处理，H8 不碰 |

### 4.2 算法

```python
RESIDUAL_PATTERNS = (
    "*.old-pre-migrate",      # A
    "*.pre-migrate.bak",      # B
    "*.ra2forge.removed.bak", # D
)
BACKUP_SUFFIX = ".ra2forge.bak"   # 已有常量 install.py:29

def scan_h8_residuals(game: Path, manifest: dict | None) -> list[dict]:
    """H8: migration leftovers outside the uninstall restore path."""
    protected = {
        e.get("backup") for e in (manifest or {}).get("files", [])
        if e.get("backup")
    }
    findings = []
    seen: set[str] = set()

    for pat in RESIDUAL_PATTERNS:
        for p in sorted(game.glob(pat)):
            if p.name in seen:
                continue
            seen.add(p.name)
            findings.append({
                "check": "H8",
                "kind": ("pre-migrate-mix" if p.name.lower().endswith(".old-pre-migrate")
                         else "pre-migrate-bak" if p.name.lower().endswith(".pre-migrate.bak")
                         else "removed-bak"),
                "name": p.name,
                "bytes": p.stat().st_size,
                "severity": "WARN-MEDIUM" if "old-pre-migrate" in p.name.lower() else "WARN-LOW",
                "action_default": "list-only",
                "action_sweep": "quarantine-or-delete",
            })

    for p in sorted(game.glob("*" + BACKUP_SUFFIX)):
        if p.name in seen or p.name in protected:
            continue
        seen.add(p.name)
        findings.append({
            "check": "H8",
            "kind": "orphan-backup",
            "name": p.name,
            "bytes": p.stat().st_size,
            "severity": "WARN-LOW",
            "in_manifest_backup": False,
            "action_default": "list-only",
            "action_sweep": "quarantine-or-delete",
        })
    return findings
```

### 4.3 阈值与失败处置

| 条件 | 阈值 | 级别 | 安装（装后 C4） | 卸载 |
|:---|:---|:---|:---|:---|
| A/B/D/C 命中 | 计数 ≥ 1 | WARN | 继续；写 `manifest.hygiene.h8` | `--legacy` **列表**；`--legacy --sweep-residuals` **清扫** |
| 含 `.old-pre-migrate` | ≥ 1 | **WARN-MEDIUM** | 文案强调「含旧 INI，勿当现包」 | 优先隔离到 `ra2forge_quarantine/`（见 4.4） |
| 仅孤儿 `.ra2forge.bak` | ≥ 1 | WARN-LOW | 可删提示 | 默认保留；sweep 才动 |
| E 在用 backup | — | PASS | 不报告为残留 | **永不删** |
| 清扫 IO 失败 | — | WARN | — | `warnings.append`，继续其余项（`install.py:258-261` 同风格） |

### 4.4 清扫策略（`--sweep-residuals`）

1. **默认模式（无 `--sweep-residuals`）**：只把 H8 发现写入 `actions`/`warnings`/`manifest.hygiene.h8`，不删文件。
2. **隔离优先**：`expandmd98.mix.old-pre-migrate` 等「疑似可复活旧包」的 A 类 → `shutil.move` 到 `game/"ra2forge_quarantine"/`（同名冲突则加 `.1` 后缀），`actions.append("quarantined …")`。
3. **删除次选**：B/D 类（文本 bak、removed bak）直接 `unlink`。
4. **孤儿 C 类**：文件头前 400 字节含 `FORGE_MARKER` → 隔离；否则删除。
5. **幂等**：重复 sweep 遇不到同名（已移走/删掉）则跳过。
6. **绝不**：删 E 类在用 backup、删官方 `BATTLEMD.INI`、删用户非 ra2forge 命名文件。

### 4.5 `expandmd98.mix.old-pre-migrate` 专项（验收锚点）

| 项 | 值 |
|:---|:---|
| 路径 | `<game>/expandmd98.mix.old-pre-migrate` |
| 字节 | 43,702（ra2youli 快照） |
| 内容 | 旧 MIX：`BATTLEMD.INI`（forge 覆盖件）+ `ECH01–03.MAP` + XCC `local mix database.dat` |
| 为何危险 | 若被改名为 `expandmd98.mix` 会以 98 槽复活旧覆盖包（含会覆写官方战役列表的 INI） |
| 引擎现状 | 后缀存在 ⇒ **不被装载**（幽灵） |
| H8 动作 | 扫描识别 → `--legacy` 列出 → `--sweep-residuals` 隔离到 `ra2forge_quarantine/`（或 `--sweep-delete` 直接删） |
| 禁止 | 当作现包；当备份还原源；静默删而无 actions 记录 |

---

## [5] 与 `ra2forge_install.json` / 卸载路径集成

### 5.1 Manifest v0.4 增量 schema

```json
{
  "tool": "ra2forge",
  "version": "0.4",
  "installed_at": "…",
  "package": "…",
  "game_dir": "…",
  "files": [ { "name": "…", "action": "…", "bytes": 0, "sha256": "…", "backup": "…|null" } ],
  "warnings": ["…"],
  "hygiene": {
    "checks": ["H5", "H6", "H8"],
    "h5": {
      "maps_scanned": ["ECH01.MAP", "ECH02.MAP", "ECH03.MAP"],
      "slots_scanned": [0, 1, 97],
      "collisions": [
        {"slot": 1, "mix": "expandmd01.mix", "entry_id": "8067D343", "map": "ECH01.MAP",
         "who_wins": "ra2forge (98 loads before 00-97)"}
      ]
    },
    "h6": {
      "package_ghosts": [],
      "game_ghosts": [
        {"name": "expandmd9.mix", "kind": "unpadded", "engine_loads": false}
      ]
    },
    "h8": {
      "residuals": [
        {"name": "expandmd98.mix.old-pre-migrate", "kind": "pre-migrate-mix",
         "bytes": 43702, "severity": "WARN-MEDIUM", "action_default": "list-only"}
      ],
      "swept": []
    }
  }
}
```

兼容性：旧 v0.3 清单无 `hygiene` 段时，`_load_manifest` 后 `manifest.get("hygiene") or {}`，H8 按「无保护集 = 仅跳过显式 backup 字段」降级。

### 5.2 调用点改造（`install.py`）

| 函数 | 现网 | 补丁 |
|:---|:---|:---|
| `package_files` | 收集 INI/MAP/MIX | **加**包内 H6 校验：MIX 名必须 `expandmd\d{2}\.mix`；违规 `ValueError` |
| `preinstall_warnings(game)` | H1/H2/legacy | **改名/扩展**为 `preinstall_hygiene(game, package_maps) -> (warnings, hygiene_dict)`；内含 H5/H6-game/H8-scan |
| `install_package` | 复制+写 manifest | 复制**前**跑 `preinstall_hygiene`；REFUSE 级直接 `ValueError`；WARN 级并入 `warnings`；写 manifest 时带 `hygiene` 段 |
| 装后（可选） | 无 | 重跑 H6/H8 一次作 post-check（产品 §4-C4/C5），结果覆盖 `hygiene.h6/h8` |
| `uninstall(..., legacy=)` | `_uninstall_legacy` | **加** `sweep_residuals: bool = False` 参数；`--legacy` 时先跑 `scan_h8_residuals`，若 `sweep_residuals` 执行 4.4 清扫 |
| `uninstall` 返回 | `{game_dir, actions, warnings}` | 增 `"hygiene"` 键（本轮 H5 不重跑；H6/H8 快照） |

### 5.3 CLI（`cli.py`）增量

```
uninstall --game DIR [--legacy] [--drop-legacy-battlemd] [--force]
          [--sweep-residuals]          # 新：清扫 A/B/C/D 残留
          [--sweep-delete]             # 新：A 类也直接删（默认隔离）
```

`--sweep-residuals` **依赖** `--legacy`（残留本就是迁移遗留）；单独给出时报错退出（exit 2）。

### 5.4 卸载顺序（补丁后）

1. manifest 文件逆序删除 + backup 还原（现网不变）。
2. `legacy`：`_uninstall_legacy`（现网不变）。
3. `legacy and sweep_residuals`：`scan_h8_residuals` → 4.4 清扫；被清扫项写入 `actions`/`hygiene.h8.swept`。
4. 返回。

---

## [6] 验收用例（20 条）

编号规则 `AC-H5xx / AC-H6xx / AC-H8xx / AC-INTx`。机器可读版：`out/re_work/re_sprint/R_mix_h568/acceptance_cases.json`。

### 6.1 H5（CRC 扫描）

| ID | 前置 | 操作 | 期望 |
|:---|:---|:---|:---|
| AC-H5-01 | 干净游戏目录（仅 `gamemd.exe`+`expandmd01.mix` 无同 CRC） | `install` | H5 PASS；`hygiene.h5.collisions=[]` |
| AC-H5-02 | `expandmd01.mix` 内含 `ECH01.MAP`（CRC `8067D343`） | `install` | WARN：「98 将覆盖 expandmd01.mix 内 ECH01.MAP」；**安装成功**；`collisions` 含 slot=1 |
| AC-H5-03 | `expandmd50.mix` 内含三张同 CRC 地图 | `install` | 3 条 collision；安装成功 |
| AC-H5-04 | `expandmd97.mix` 与 `expandmd00.mix` 各 1 条命中 | `install` | 2 条 collision，slot ∈ {0,97} |
| AC-H5-05 | `expandmd99.mix` 含 `ECH02.MAP` | `install` | WARN-HIGH（并入 H1）；`who_wins` 表明 99 压过 98 |
| AC-H5-06 | `expandmd01.mix` 仅 classic_hash 命中（伪造条目 ID=`704D79CC`） | `install` | 仍报 collision（双集合） |
| AC-H5-07 | `expandmd01.mix` 损坏（截断到 4 字节） | `install` | H5 WARN「unreadable MIX」；安装不中断 |

### 6.2 H6（幽灵名）

| ID | 前置 | 操作 | 期望 |
|:---|:---|:---|:---|
| AC-H6-01 | 包内含 `expandmd9.mix` | `install` | **ValueError 拒绝**；游戏目录零写入 |
| AC-H6-02 | 包内含 `expandmd98.mix` + `expandmd100.mix` | `install` | **拒绝**（100 非两位） |
| AC-H6-03 | 包内仅 `expandmd98.mix`（小写合法） | `install` | 成功；`package_ghosts=[]` |
| AC-H6-04 | 游戏目录有 `expandmd9.mix` | `install` | WARN；`game_ghosts` 含 unpadded；安装成功 |
| AC-H6-05 | 游戏目录有 `EXPANDMD98.MIX`（大写） | `install` | WARN case-drift；安装成功 |
| AC-H6-06 | 游戏目录有 `expandmd98.mix.old-pre-migrate` | `install` | H6 标 `residual-suffix` + H8 报 WARN-MEDIUM |

### 6.3 H8（残留清扫）

| ID | 前置 | 操作 | 期望 |
|:---|:---|:---|:---|
| AC-H8-01 | 游戏目录有 **`expandmd98.mix.old-pre-migrate`**（43702B） | `uninstall --legacy --sweep-residuals` | 该文件 **消失**（隔离至 `ra2forge_quarantine/` 或删除）；`actions` 有 `quarantined/removed expandmd98.mix.old-pre-migrate`；`hygiene.h8.swept` 非空 |
| AC-H8-02 | 同上 | `uninstall --legacy`（无 sweep） | 文件**仍在**；`warnings` 列出；**不删** |
| AC-H8-03 | 有 `ra2forge_uninstall.txt.pre-migrate.bak` | `--legacy --sweep-residuals` | 删除；`actions` 记录 |
| AC-H8-04 | 有孤儿 `BATTLEMD.INI.ra2forge.bak`（含 FORGE_MARKER） | `--legacy --sweep-residuals` | 隔离（非直接删） |
| AC-H8-05 | 有 `ECH01.MAP.ra2forge.bak` 且在 `manifest.files[].backup` | `--legacy --sweep-residuals` | **保留**（E 类保护）；卸载正常还原 |
| AC-H8-06 | 干净目录 | `uninstall --legacy --sweep-residuals` | 无清扫动作；幂等 |
| AC-H8-07 | A 类文件只读/锁定 | `--legacy --sweep-residuals` | `warnings` 记 IOError；其余项继续 |

### 6.4 集成

| ID | 前置 | 操作 | 期望 |
|:---|:---|:---|:---|
| AC-INT-01 | v0.3 旧清单（无 `hygiene`） | `uninstall --legacy --sweep-residuals` | 不抛错；H8 降级扫描仍工作 |
| AC-INT-02 | 安装后 | 读 `ra2forge_install.json` | 存在 `hygiene.checks=["H5","H6","H8"]` 且三段齐全 |

---

## [7] 实现切片（建议 PR 顺序）

| 切片 | 内容 | 风险 |
|:---|:---|:---|
| P1 | `scan_h6_ghosts` + `package_files` 硬校验 + CLI 文案 | 低 |
| P2 | `scan_h5_crc` + `preinstall_hygiene` 合并 + manifest `hygiene` | 低 |
| P3 | `scan_h8_residuals` + `--sweep-residuals/--sweep-delete` + 隔离目录 | 中（删除权） |
| P4 | 装后 post-check + 验收脚本跑 AC 全表 | 低 |

每片独立可测；P1/P2 不触碰删除路径。

---

## [8] 未闭环

| ID | 缺口 | 影响 |
|:---|:---|:---|
| U-H5-1 | 同 CRC 但字节不同的条目（哈希碰撞/同名异内容）内容级 diff | 仅告警 CRC；不比对字节（MIX 内读条目成本高） |
| U-H8-1 | 隔离目录是否应随 `--force` 一并清空 | 规格默认否；留给产品决策 |
| U-H6-1 | 大小写在非 Windows 文件系统的真实装载行为 | [推演] Windows 不敏感；跨平台仅 WARN |

---

## [9] 交叉引用

- 产品缺口与优先级：`docs/re/mix_hygiene_product.md` §1.4 H5/H6/H8、§2.3、§4
- 安装器现网：`ra2forge/install.py`（`package_files:42` / `preinstall_warnings:61` / `install_package:92` / `uninstall:154` / `_uninstall_legacy:210`）
- MIX 读取与 CRC：`ra2forge/mixlib.py:205-207`（`crc_hash`）、`:286-290`（`get` 双集合）、`:231-296`（`MixFile`）
- 残留快照：`out/re_work/re_sprint/R_mix_prod/residual_cross.json`
- 本任务产物：`out/re_work/re_sprint/R_mix_h568/{README.md,h5h8_patch_spec.json,acceptance_cases.json,residual_sweep_plan.json}`
