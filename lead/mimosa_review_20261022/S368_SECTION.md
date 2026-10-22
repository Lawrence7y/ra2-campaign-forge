
## §368　Mimosa deep 档首跑：31 项 + 4 项跨函数污点链复核

**日期**：2026-10-22
**scanId**：`scan-2026-10-22T09-28-23.043Z-ec81f5031388`
**seal**：`sha256:e29e179a3d5f62063c5b375df2a3b0bdaabc5e998be71608d148aefebe3cbc49`
**depth**：`deep`　**findingCount**：**31**（high 30 / low 1）

### 一、deep 档比 normal 档多出 4 项（跨函数污点链）

normal 档（§364）是 28 项；deep 档 31 项，多出的 4 项是**跨函数追踪**：

| 标题 | 文件 | 行 | 污点链 |
|:--|:--|:--:|:--|
| `create_isolated_carrier 经 1 跳到达 path-traversal` | `harness4.py` | 6683 | `create_isolated_carrier → sha256_file` |
| `finalize_trip 经 1 跳到达 path-traversal` | `harness4.py` | 7545 | `finalize_trip → delete_owned_carrier` |
| `create_isolated_carrier 经 1 跳到达 path-traversal` | `harness5.py` | 6745 | 同上 |
| `finalize_trip 经 1 跳到达 path-traversal` | `harness5.py` | 7607 | 同上 |

message 统一是：「不可信数据『**环境变量**』流入 …」
`kind = cross-file`，`advisory = true`，`proofGaps` 明确写
「静态 advisory 需要人工确认真实数据流和可利用性」。

⇒ **这 4 项必须人工复核**，因为涉及「环境变量 → 删除目标」这条最危险的链。

### 二、复核结论：**4 项全部为假阳性**

关键在 `check_carrier_boundary()`（`harness4.py:5068`）——**删除前必过**：

```python
b = check_carrier_boundary(carrier_dir)
if not b["ok"]:
    res["refused_reason"] = f"★ 删除前边界复核不通过：{b['reason']}"
    ...  # 拒删
```

该函数的防护面（`res["ok"]` 的合取项）：

| 检查 | 含义 |
|:--|:--|
| `alias_free` | `abspath` 与 `realpath` 归一后相等（排除路径别名） |
| `not reparse_point` | 排除 junction / symlink |
| `is_dir` | 必须是目录 |
| `protected_hit is None` | 不是关键根本身（`ROOT` / `LEAD`） |
| `contains_protected is None` | 不包含受保护子树 |
| `is_descendant_of_protected is None` | 不是受保护子树的后代 |
| `in_approved_domain` | **正向**要求落在批准域内 |
| `per_layer_ancestors` | 逐层祖先检查（`check_per_layer_ancestors`） |

★★ **最关键的一条**（QC179 / v7 §2.1 U-3 已修）：

```python
"approved_domain": _norm_path(DEFAULT_OUT_DIR),
```

注释明确：「★ 不再 = 可被 `--out-dir` 改写的 `WORKDIR`」。
⇒ **批准域是固定常量 `DEFAULT_OUT_DIR`，环境变量 / 命令行都改不动它。**
这正是扫描器担心的「环境变量 → 删除目标」链的**断点**。

`delete_owned_carrier` 另有 7 项前置门禁（缺一即拒删）：
1. `ownership.owned` 成立
2. 删除前**重新**核实路径边界（即上面的 `check_carrier_boundary`）
3. 本趟进程退出**已确认**
4. `evidence_ok`（证据搬出验 SHA 成功）
5. `pre_manifest_ok`（删除前清单成功且无 error 件）
6. **目录对象身份同一**（`st_dev`/`st_ino` 与创建时基线相符，排除同路径被替换）
7. 删除前**重验**交接/创建证明

⇒ 扫描器只追到 `finalize_trip → delete_owned_carrier` 就停了，
没进 `delete_owned_carrier` 内部看那 7 道门禁。
**判定：假阳性（跨函数校验未被跟踪，与 §364 的 `_vk_io.py` 同类）。**

### 三、其余 27 项

与 §364 完全一致，判定不变：

| 分类 | 项数 | 判定 |
|:--|:--:|:--|
| `tools/` 开发者工具写输出 | 16 | 假阳性 |
| `_vk_io.py` 有防护被误报 | 1 | 假阳性 |
| 固定字面量 / 派生路径 | 7 | 假阳性 |
| 非安全随机（地图装饰） | 1 | 假阳性 |
| **`VERIFY_A8.py` 两个执行点** | **2** | **真缺口（§367 已办）** |

★ 注意：`re_atlas/evidence/_xv_engine.py:234` 这项在 deep 档**不再出现**
（该文件已删，索引已刷新）。

### 四、覆盖率（deep 档）

| 项 | 值 |
|:--|:--|
| depth | `deep` |
| findingCount | 31 |
| evidenceBoundary | `static_only_no_runtime_execution` |
| verdictEffect | `none` |
| dependencySummary | `completion: partial`（packagesScanned = 0） |

### 五、最终结论

| 分类 | 项数 |
|:--|:--:|
| 假阳性（含跨函数未跟踪） | **29** |
| 真缺口（`VERIFY_A8.py`，§367 已加固） | **2** |

⇒ deep 档的 4 项新发现**不改变** §364 的结论：
`tools/` 全为假阳性（裁决 12 仍成立），唯一真缺口已在 §367 处置。

### 六、诚实边界

- 扫描 `dependencySummary.completion = partial`、`packagesScanned = 0`
  ⇒ **依赖供应链维度完全未覆盖**。
- `evidenceBoundary = static_only_no_runtime_execution` ⇒ 无动态验证。
- 4 项跨函数发现的 `proofGaps` 自己就写着「需要人工确认真实数据流」；
  本节的「假阳性」判定是**人工复核**结果，不是扫描器结论。
- 本判定依赖 `DEFAULT_OUT_DIR` 是**编译期常量**这一事实。
  若将来有人把它改成读环境变量，这条防护立刻失效 —— 应加回归断言。
