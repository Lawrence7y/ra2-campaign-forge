# SEMFIX-ENGFAM-B2 — S17 英文族 17 行依据从 ③b④ 改写为 ③b②（后 17 行）

> 状态：**完成**。17/17 行逐行取证并落盘 `EVIDENCE/ROW_<entry>.txt`；每 5 行追加 `coverage_delta.tsv` 与 `PROGRESS.md`。类名取得 17/17，③b② 成立 17/17，改写 17/17。

## 0. 自校验与通道

| 项 | 值 |
|---|---|
| 目标二进制 | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` |
| SHA-256（期望） | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| ImageBase | `0x400000` |
| `.text` | `[0x401000, 0x7E038D)` |
| 工具 | Python 3.12.10 / capstone 5.0.7（`skipdata=True`）/ pefile 2024.8.26，无 venv、无 pip install |
| 代码来源 | `work/semfix_lib.py` 复用自 `SEMFIX_ENGFAM/work/semfix_lib.py`（复用代码，不复用结论） |

只读线索（不作证据）：`TIEBREAK_ENGFAM\`、`S17_ENGFAM\`、`SEMFIX_ENGFAM\`。
每行地址均从二进制字节独立取证，不整批共用 reason。

## 1. 34 行过滤与 B2 切片

过滤语义：`coverage.tsv` 第 4 列匹配 `(?i)unproven|unverified|not proven`，全部 `subsystem=S17`、`grade=[已证]`、全在 atlas。实测命中 **34 行**（subsystem 计数 `S17:34`，grade 计数 `[已证]:34`），与卡面一致。

切片命令（与实测一致）：

```python
rows = [p for p in (line.split("\t") for line in COVERAGE.read_text(encoding="utf-8").splitlines())
        if len(p) >= 6 and re.search(r"unproven|unverified|not proven", p[3], re.I)]
rows.sort(key=lambda r: int(r[0], 16))     # entry 数值升序
b2 = rows[17:]                              # 后 17 行
```

34 行按 entry 升序（idx 00..33），B1 = idx 00..16，B2 = idx 17..33。

**本批 B2 的 17 个 entry（升序）**：

| # | entry | coverage name |
|---|---|---|
| 17 | 006806F0 | Save_VectorBlock_19 |
| 18 | 00680770 | Save_VectorBlock_20 |
| 19 | 006807F0 | Save_VectorBlock_21 |
| 20 | 00680870 | Save_VectorBlock_22 |
| 21 | 006808F0 | Save_VectorBlock_23 |
| 22 | 00680970 | Save_VectorBlock_24 |
| 23 | 006809F0 | Save_VectorBlock_25 |
| 24 | 00680A70 | Save_VectorBlock_26 |
| 25 | 00680AF0 | Save_VectorBlock_27 |
| 26 | 00680B70 | Save_VectorBlock_28 |
| 27 | 00680BF0 | Save_VectorBlock_29 |
| 28 | 00680C70 | Save_VectorBlock_30 |
| 29 | 00680CF0 | Save_VectorBlock_31 |
| 30 | 00680D70 | Save_VectorBlock_32 |
| 31 | 00680DF0 | Save_VectorBlock_33 |
| 32 | 00680E70 | Save_VectorBlock_34 |
| 33 | 00680EF0 | Save_VectorBlock_35 |

## 2. 本批 17 行总表（entry / 类名取得否 / ③b② 成立否 / 是否改写）

> 逐行取证完成。每行地址由本批脚本 `work/extract_b2.py` 从二进制字节独立取得，见 `PROGRESS.md` 与 `EVIDENCE/`。

| entry | coverage name | 类名取得否 | ③b② 成立否 | 是否改写 | 容器实例类名（RTTI 名串） |
|---|---|---|---|---|---|
| 006806F0 | Save_VectorBlock_19 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVEMPulseClass@@@@` |
| 00680770 | Save_VectorBlock_20 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVSuperWeaponTypeClass@@@@` |
| 006807F0 | Save_VectorBlock_21 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVSuperClass@@@@` |
| 00680870 | Save_VectorBlock_22 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVTerrainTypeClass@@@@` |
| 006808F0 | Save_VectorBlock_23 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVTerrainClass@@@@` |
| 00680970 | Save_VectorBlock_24 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@` |
| 006809F0 | Save_VectorBlock_25 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVAlphaShapeClass@@@@` |
| 00680A70 | Save_VectorBlock_26 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVWaveClass@@@@` |
| 00680AF0 | Save_VectorBlock_27 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVCaptureManagerClass@@@@` |
| 00680B70 | Save_VectorBlock_28 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVDiskLaserClass@@@@` |
| 00680BF0 | Save_VectorBlock_29 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVParasiteClass@@@@` |
| 00680C70 | Save_VectorBlock_30 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVTemporalClass@@@@` |
| 00680CF0 | Save_VectorBlock_31 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVAirstrikeClass@@@@` |
| 00680D70 | Save_VectorBlock_32 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@` |
| 00680DF0 | Save_VectorBlock_33 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@` |
| 00680E70 | Save_VectorBlock_34 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVBombClass@@@@` |
| 00680EF0 | Save_VectorBlock_35 | 是 | 是 | 是 | `.?AV?$DynamicVectorClass@PAVRadSiteClass@@@@` |

合计：类名取得 **17/17**；③b② 成立 **17/17**；改写 **17/17**；无「类名未取得」行需单列。

说明：
- 每行类名来自该行 `.bss`/`.data` 静态向量的活表 RTTI：构造写入点 `mov dword ptr [vec],vt` → `COL=[vt-4]` → `TD=[COL+0xC]` → 名串 `TD+8`。每向量另有 `VectorClass<...>` 死表（装于 atexit 析构器），按活表口径排除。
- ③b② 成立：每行函数体 4 处 call 派生 HRESULT 检查 `test eax,eax`+`jl` → 公共失败落点（`+0x78`，eax 不清零、原样返回失败 HRESULT），成功 `xor eax,eax`（`+0x76`），调用方 `test eax,eax`/`jge` 消费。
- ④ 使用见证：每行唯一 `E8` 调用点在真实函数体 `0x67D300` 内，调用点前有 `mov edx,vec`/`mov ecx,esi`、调用后有返回值消费；`0x67D300` 自身被 `0x67D1AF` 直调（非裸 E8）。
- 类名是容器实例名 `DynamicVectorClass<PAVXxx>`，元素类以模板实参出现（无元素类自身独立 COL/TD），与只读线索同形，但本批地址均独立取证。

## 3. 已裁定事实（不重开）

- ③b④ 全族不成立：循环体内仅 `mov [esp+0xC],0`（栈写）+ 6 条 push，非栈写 0 条；流写在 `IStream::Write`/`OleSaveToStream` 被调用者内部，按 `0045A640` 界线不算本函数循环内写。
- 成立通道是 ③b②：4 处 call 派生 HRESULT 检查（`test eax,eax`+`jl`），失败落点约 `+0x78` 不清零 eax、原样返回；成功 `xor eax,eax` 返回 0；被调用方以 `test/jge` 消费。
- 模板第 17 个成员 `0x6805F0` 归 S05，不属 S17；"35 个槽"是模板副本数，S17 仍 34 行。

## 4. 每行锚点记录

逐行见 `EVIDENCE/ROW_<entry>.txt`。三类锚点：
1. 元素类：`.bss` 向量地址、构造写入点地址、元素类 RTTI 描述符地址、类名字符串地址；
2. ③b②：HRESULT 检查点（`test eax,eax` 或 `cmp`）+ 紧随 `jl/jne`、失败落点、成功 `xor eax,eax`、至少一处调用方消费地址；
3. ④ 使用见证：真实调用者地址。

## 5. 产物

- `coverage_delta.tsv`（6 列表头）
- `EVIDENCE/ROW_<entry>.txt` × 17
- `PROGRESS.md`（每 5 行追加）
- `base_rate.tsv`
- `REPORT.md`（本文件）
