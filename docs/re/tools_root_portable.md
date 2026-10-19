# M 轨工具 ROOT 便携解析（RA2FORGE_ROOT）

> 执行方 MiMo（M 轨 T22）· 工作区 `D:\Project\ra2-campaign-forge`
> 实现：`tools/_ra2_paths.py` · 证据：`out/re_work/tools_root/resolve_cases.json`
> 证据等级：`[实证]` = 脚本实跑输出。

---

## 1. 问题

M 轨工具原先散落三种 ROOT 写法：硬编码 `D:\Project\ra2-campaign-forge`、`Path(__file__).resolve().parents[1]`、字符串常量。仓库一旦挪窝/克隆到别的盘，硬编码即失效。

## 2. 解析顺序（`_ra2_paths.resolve_root(anchor_file)`）

| 序 | 来源 | 行为 |
|---|---|---|
| 1 | 环境变量 `RA2FORGE_ROOT`（非空） | 直接采用 |
| 2 | 脚本相对：`Path(anchor_file).resolve().parents[1]` | `tools/` 的父目录 = 仓库根 |
| 3 | 旧硬编码 `D:\Project\ra2-campaign-forge` | **仅兼容**；stderr 打 `[warn]` 后回退 |

`anchor_file` 一般传调用方的 `__file__`；省略则用本模块路径（同在 `tools/` 下结果一致）。

## 3. 用法（CLI 不变）

```python
# tools/<any>.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ra2_paths import resolve_root

ROOT = resolve_root(__file__)
```

```powershell
# 临时改根（测试/跨机）
$env:RA2FORGE_ROOT = "E:\other\ra2-campaign-forge"
python tools\bench_map_install.py --verify
```

**CLI 接口零改动**：子命令、参数、退出码、输出格式均保持原样；仅路径推导换源。

## 4. 已接入工具（本波次写域内）

| 工具 | 状态 |
|---|---|
| `tools/_ra2_paths.py` | 定义 `resolve_root` / `ENV_KEY` / `LEGACY_ROOT` |
| `tools/h1_map_fingerprint.py` | `ROOT = resolve_root(__file__)` |
| `tools/bench_map_install.py` | `ROOT = str(resolve_root(__file__))` |
| `tools/empty_map_gen.py` | 本轮由硬编码改为 `resolve_root(__file__)` |

域外仍有硬编码（`tools/verify_bss_claims.py`、`tools/lead_watch.py`、`tools/bench_maps/*.py` 等）——不在本波次写域，**不代改**；需要时另开工单。

## 5. 解析顺序自证（`out/re_work/tools_root/resolve_cases.json`）

| 用例 | `RA2FORGE_ROOT` | 解析结果 |
|---|---|---|
| script_relative | （未设） | `D:\Project\ra2-campaign-forge` |
| env_override | `D:/Project/ra2-campaign-forge` | `D:\Project\ra2-campaign-forge` |
| env_override_other | `C:/tmp/other_root` | `C:\tmp\other_root` |

顺序 1→2→3 成立；空串环境变量等价未设（回落脚本相对）。

## 6. 回归（2026-09-30 实跑）

| 门禁 | 结果 |
|---|---|
| `python -m py_compile tools/_ra2_paths.py tools/empty_map_gen.py tools/h1_map_fingerprint.py tools/bench_map_install.py` | exit 0 |
| `python tools/h1_map_fingerprint.py verify` | 三档 H1 全 PASS |
| `python tools/empty_map_gen.py verify` | PASS |
| `python tools/bench_map_install.py --verify` | `PASS=14 FAIL=0` |
| `python tools/check_except_gate.py --selftest` | 自检 PASS |
