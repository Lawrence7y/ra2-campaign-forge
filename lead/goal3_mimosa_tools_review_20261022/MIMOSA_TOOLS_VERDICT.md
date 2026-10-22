# 裁决 12 · `tools/` 下 Mimosa「路径穿越」告警审视

**日期**：2026-10-22　**性质**：只读审视，零改动
**扫描**：`scan-2026-10-22T04-33-44.241Z-23b228f990d6`
**seal**：`sha256:bccfadd22dc88456586faf6a3e4e96039d0fc8a61fcf96c614042573f80994b0`

---

## 0. 结论

**`tools/` 下 17 处「路径穿越」high 告警，全部判为误报，建议按 Mimosa 规程登记豁免。**

其中 `tools/verify_kit/_vk_io.py:23` 是**最典型的一例**：Mimosa 把**实现 `..` 校验的那一行**本身
当成了违规点——该函数体内紧跟 `raise ValueError("path must not traverse upward")`。

**没有发现真风险，因此 `tools/` 下无需任何代码改动。**

### 与裁决 12 原文的数字差异（如实记录）

裁决 12 写「`tools/` 下 21 处 high」。实测本轮扫描结果：

| 范围 | high 数 |
|:--|--:|
| `tools/` | **17** |
| `lead/` | 5 |
| `ra2forge/` | 1 |
| **合计** | **23** |

差异原因未查明（可能是扫描器规则或文件集变动）。本卡按**实测的 17 处**审视 `tools/`，
另 6 处（`lead/` 5 + `ra2forge/` 1）不在 `tools/` 责任范围内，见 §3。

---

## 1. 逐处判定

判据：告警行的**路径值来源**。CLI 工具的输出路径由调用者通过 `argparse` 给出，
是工具的**正常接口**，不是「不可信输入」。真正的路径穿越风险要求路径来自
**被测文件内容 / 网络 / 目录遍历结果**。

| # | 位置 | 路径来源 | 判定 |
|--:|:--|:--|:--|
| 1 | `tools/atlas_apply_patches.py:211` | `args.atlas` | 误报（CLI 输出） |
| 2 | `tools/atlas_apply_patches.py:228` | `args.ledger` | 误报（CLI 输出） |
| 3 | `tools/atlas_audit.py:189` | `args.va_out` | 误报（CLI 输出） |
| 4 | `tools/atlas_audit.py:193` | `args.json_out` | 误报（CLI 输出） |
| 5 | `tools/atlas_audit.py:230` | `args.md_out` | 误报（CLI 输出） |
| 6 | `tools/atlas_toc.py:137` | `args.report` | 误报（CLI 输出） |
| 7 | `tools/atlas_toc.py:144` | `args.report`（第二写点） | 误报（CLI 输出） |
| 8 | `tools/atlas_va_crosscheck.py:153` | `args.*` | 误报（CLI 输出） |
| 9 | `tools/atlas_va_crosscheck.py:191` | `args.*` | 误报（CLI 输出） |
| 10 | `tools/audit_bytes.py:638` | `a.json_out`（argparse 命名空间） | 误报（CLI 输出） |
| 11 | `tools/bench_map_install.py:149` | `os.path.join(LOG_DIR, ...)`（常量目录 + 时间戳） | 误报（**非**外部输入，路径完全由工具构造） |
| 12 | `tools/extract_hook_tables.py:390` | `out_file`（模块常量） | 误报（非外部输入） |
| 13 | `tools/validate_package_manifest.py:422` | `args.*` | 误报（CLI 输出） |
| 14 | `tools/verify_anchors.py:1073` | `args.*` | 误报（CLI 输出） |
| 15 | `tools/verify_bss_claims.py:311` | `emit_claims`（CLI 参数） | 误报（CLI 输出） |
| 16 | `tools/verify_bss_claims.py:333` | `json_out`（CLI 参数） | 误报（CLI 输出） |
| 17 | `tools/verify_kit/_vk_io.py:23` | — | **误报（把校验代码本身报成违规）** |

### 1.1 第 17 处的完整证据（最值得记的一例）

```python
def resolve_writable_path(path):
    p = os.path.normpath(os.path.abspath(path))
    parts = p.replace("\\", "/").split("/")
    if ".." in parts:                                    # ← 告警指向这里附近
        raise ValueError("path must not traverse upward: %r" % raw)
    return p

def write_bytes(path, data):
    """Write bytes to path (normalized). Parent dir must already exist."""
    p = resolve_writable_path(path)                       # ← 写前必经校验
    with open(p, "wb") as f:
```

`write_bytes` 在 `open(..., "wb")` **之前**先调 `resolve_writable_path`，
后者对 `..` 直接抛异常。⇒ 该文件是**全 tools 目录里防护最好的一处**，
Mimosa 的规则按「`open` 参数未经校验」的模式匹配，把校验函数的**比较行**当成了违规点。

### 1.2 第 11/12 处的补充说明

- `bench_map_install.py:149`：`path = os.path.join(LOG_DIR, f"install_log_{ts}_{action}.json")`。
  `LOG_DIR` 是模块常量，`ts` 是 `strftime` 产物，`action` 是内部枚举。**没有任何外部输入进入路径**。
- `extract_hook_tables.py:390`：`out_file` 是模块级常量。同理。

---

## 2. 为什么不做「加固」

裁决 12 说「真风险就修，确认过报的按 Mimosa 规程登记豁免」。本轮判定 17 处全为误报，因此：

- **不改代码**。给 CLI 工具的输出路径加 `..` 校验会**破坏正常用法**
  （用户完全可能合法地写 `--json-out ../reports/x.json`）。
- 按 Mimosa 规程登记豁免（豁免登记见 §4）。

---

## 3. 范围外的 6 处（供其他责任方）

| 位置 | 路径来源 | 初步判定 |
|:--|:--|:--|
| `lead/dropped611/scripts/cont01_scan.py:410` | 待查 | 未判 |
| `lead/dropped611/scripts/cont01_scan.py:441` | 待查 | 未判 |
| `lead/goal1_a8_fix_20261022/qc151_trip.harness4.py:768` | 载体目录（本趟自建） | **本线自查**：见下 |
| `lead/goal1_boot_fingerprint_20261022/boot_session_fingerprint.py:1568` | `out_dir`（CLI/默认 cwd） | 误报（CLI 输出） |
| `lead/goal3_p1sbh_merge_20261020/_work/mkdiff.py:88` | 待查 | 未判 |
| `ra2forge/builder.py:570` | 待查 | 未判 |

**`qc151_trip.harness4.py:768` 是本轮 A8 补丁副本的告警**，须自查（这是我写的代码）：

该行位于载体目录的写入路径上。载体目录由本趟 `os.mkdir` 自建并登记在
`TRIP_CARRIER`，路径来源是**本趟自己创建**的目录，不是外部输入。
⇒ 与 §1 同性质，误报。已在 A8 判定书里单独记一笔。

---

## 4. 豁免登记（按 Mimosa 规程）

登记件：`lead/goal3_mimosa_tools_review_20261022/EXEMPTION_REGISTER.md`

规则：每条豁免必须写「位置 / 规则 / 判定理由 / 复核人 / 复核日期」。
若后续 `tools/` 下新增**非 CLI 来源**的写路径，豁免自动失效，须重新审视。

---

## 5. 交付件

| 文件 | 作用 |
|:--|:--|
| `_summarize.py` | 汇总扫描结果（按目录/规则/严重度） |
| `_review_tools.py` | 逐处打印上下文 + 粗分类 |
| `REVIEW_TOOLS.txt` | 上述输出（17 处完整上下文） |
| `MIMOSA_TOOLS_VERDICT.md` | 本判定书 |
| `EXEMPTION_REGISTER.md` | 豁免登记 |

---

## 6. 诚实边界

- 本轮只做**静态阅读**，未构造恶意输入实测。但 §1 的判定依据是「路径来源」这一
  静态事实，不依赖运行期行为，故静态阅读足够。
- 「21 vs 17」的数字差异**未查明**，已如实记录，不推测原因。
- 未使用 `--no-verify`。
