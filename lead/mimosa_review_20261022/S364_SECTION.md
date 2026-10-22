
## §364　Mimosa 完整审计首次跑通 + 28 项发现逐条复核

**日期**：2026-10-22
**触发**：commit/push 钩子连续报 `scanner_enobufs`（扫描不完整）。
本轮改用 `security_scan_start` + `security_scan_status` 后台作业，**首次拿到完整结论**。

### 一、扫描本体（如实记录覆盖边界）

| 项 | 值 |
|:--|:--|
| scanId | `scan-2026-10-22T07-22-01.043Z-9556db1dedec` |
| seal | `sha256:4a52ea1767607933461fbc90a34a470dd46412db8a204ca65e4bd603b6818254` |
| depth | `normal` |
| **completeness** | **`partial`** |
| **runStatus** | **`inconclusive`** |
| selectedFiles / parsedFiles | 591 / **591** |
| readFailures / parseFailures / truncated | **0 / 0 / false** |
| findingCount | **28**（high 27 / low 1） |
| gaps | `部分分析阶段未能完整覆盖` |

★ **`threatModel` / `findingDiscovery` / `validation` / `pathAnalysis` 四阶段的
status 全是 `not_applicable`**（entryPoints=0, functions=0, callEdges=0）。
⇒ **不得声称「项目安全」。** 本结论只是「591 个文件全部读入并静态扫描，
产出 28 项，逐条复核如下」，不是完整安全证明。

### 二、28 项逐条复核

每条发现连同前后 3 行上下文已导出到
`lead/mimosa_review_20261022/FLAGGED_LINES.txt`（301 行）。

#### A. 16 项 `tools/` high 路径穿越 —— 全部**假阳性**（延续裁决 12）

| 文件 | 处数 |
|:--|:--:|
| `tools/atlas_audit.py` | 3 |
| `tools/atlas_apply_patches.py` | 2 |
| `tools/atlas_toc.py` | 2 |
| `tools/atlas_va_crosscheck.py` | 2 |
| `tools/verify_bss_claims.py` | 2 |
| `tools/audit_bytes.py` | 1 |
| `tools/bench_map_install.py` | 1 |
| `tools/extract_hook_tables.py` | 1 |
| `tools/validate_package_manifest.py` | 1 |
| `tools/verify_anchors.py` | 1 |

**判据**：全部是「以命令行参数或本脚本固定相对路径作为写入目标」——
开发者在自己的终端跑、写自己的输出文件，**不存在权限边界**（无服务端、无他人输入）。

#### B. `_vk_io.py:23` —— 有防护，但扫描器未跨函数跟踪（假阳性）

```python
def resolve_writable_path(raw):
    p = os.path.realpath(os.path.abspath(raw))
    parts = p.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError("path must not traverse upward: %r" % raw)
    return p
```

`write_bytes()` 第 22 行先调 `resolve_writable_path(path)`，第 23 行才写。
⇒ 该函数**显式拒绝上跳**。扫描器只看到第 23 行的写入点，没跟踪到校验。
**这是 17 项 `tools/` 里唯一「有防护却被误报」的一处**；
其余 16 项是「确实没有防护、但也不需要防护」。

#### C. 4 项固定字面量路径 —— 假阳性

| 位置 | 路径来源 |
|:--|:--|
| `lead/dropped611/scripts/cont01_scan.py:410` / `:441` | 硬编码绝对路径（本机工作目录下的固定输出） |
| `lead/goal3_p1sbh_merge_20261020/_work/mkdiff.py:88` | 硬编码 `'sbh_on_p1_input.diff'` |
| `ra2forge/builder.py:570` | `path` 由调用方（本项目自己的 builder）传入 |

#### D. 3 项派生路径 —— 假阳性

| 位置 | 说明 |
|:--|:--|
| `lead/goal1_a8_fix_20261022/qc151_trip.harness4.py:768` | `dst = carrier_dir / "except.txt"`，文件名是**常量**；`carrier_dir` 是载体目录本身 |
| `lead/goal1_a8_fix_20261022/qc151_trip.harness5.py:768` | 同上（同一段代码） |
| `lead/goal1_boot_fingerprint_20261022/boot_session_fingerprint.py:1568` | 文件名由时间戳 + 指纹ID 拼成，不含路径分隔符 |

#### E. 1 项陈旧发现 —— 文件已不存在（UNVERIFIABLE）

`re_atlas/evidence/_xv_engine.py:234`：
`find . -name "_xv_engine.py"` **零命中**，该文件已不在仓库中。
⇒ 扫描器读了索引里的陈旧条目。**无法复核，按 UNVERIFIABLE 归档。**

#### F. 1 项 low —— 假阳性

`ra2forge/maplib.py:161`：`rng = random.Random(seed or (row0*7919 + col0*31 + self.w))`
——地图装饰物（树木）散布的**确定性种子**，目的是「同一格点每次生成同一片树林」。
`CWE-330` 针对密码学/令牌场景，此处**恰恰需要可复现**。
⇒ 用随机数在这里是**功能需求**，不是缺陷。

#### G. ★ 2 项 high —— **真实缺口（唯一的真发现）**

`lead/goal1_a8_fix_20261022/VERIFY_A8.py:510` 与 `:687`。
两处都是「把从 `harness4` 副本里读出的函数源码文本，放进干净命名空间当代码执行」
（即 `exec` 一个由 `compile` 生成的代码对象）。`ns` 只注入 `Path`。

**为什么这是真缺口（不是假阳性）**：
- 本验证器的 K2 只**记录**副本的 `LF16 = cd9bbc87e46054af`，**没有把它与常量比对**
  （K2 的 `ok` 判据是「无 CRLF + 无 BOM + 以换行结尾」，与哈希无关）。
- 生成器 `_gen_harness4.py` 确实 assert 了**母本**哈希，但**副本**哈希在
  这个执行点上**没有任何门禁**。
- ⇒ 若 harness4 被改动（或被替换），K7/K9 会**静默地执行改后的代码**，
  并把执行结果当作「A8 补丁合格」的证据。

**危害等级**：低。三点理由：
1. 执行对象是本仓库内、本会话自己生成的文件；
2. 命名空间干净，只注入 `Path`；
3. 该脚本是**离线证据工具**，不在产品运行路径上。

**但「验证器自身可被被验证对象反向影响」是结构性缺陷**，必须记账。

**建议处置（未执行，等裁决）**：
在执行前加一条断言，把副本哈希与常量 `cd9bbc87e46054af` 比对。
代价：会改变 `VERIFY_A8.py` 本身，进而使已交付的 `VERIFY_A8.txt` 与实际脚本
不再一一对应 ⇒ **需要重跑并重新签发 K1–K10 判定书**。
⇒ 因此本轮**只记账，不擅自改已交付的验证件**（铁律 4：母本与在用脚本零改动）。

### 三、结论

| 分类 | 项数 | 判定 |
|:--|:--:|:--|
| `tools/` 开发者工具写输出文件 | 16 | 假阳性（无权限边界） |
| `_vk_io.py` 有防护被误报 | 1 | 假阳性（跨函数校验未被跟踪） |
| 固定字面量 / 派生路径 | 7 | 假阳性 |
| 陈旧索引（文件已删） | 1 | UNVERIFIABLE |
| 非安全随机（地图装饰） | 1 | 假阳性（功能需求） |
| **验证器执行点未 pin 副本哈希** | **2** | **真实缺口（低危，待裁决）** |

⇒ **26 项假阳性 / 1 项陈旧 / 1 项真缺口（计 2 处）。**
⇒ 裁决 12 的「`tools/` high 全为假阳性」在完整扫描下**依然成立**（17/17）。

### 四、交付件

| 文件 | 说明 |
|:--|:--|
| `lead/mimosa_review_20261022/FLAGGED_LINES.txt` | 28 项 × 前后 3 行上下文（301 行） |
| `lead/goal3_mimosa_tools_review_20261022/EXEMPTION_REGISTER.md` | 前次 17 项豁免登记（本轮复核仍成立） |

### 五、诚实边界

- 扫描 `completeness = partial`、`runStatus = inconclusive`，四阶段 `not_applicable`
  ⇒ **本轮不能作为「项目安全」的证据**，只能作为「591 文件静态扫描的 28 项已逐条复核」。
- 未做 deep 档扫描。
- `_xv_engine.py` 无法复核（文件已不存在），需重建索引后再扫。

---
