# SEMFIX-ENGFAM — 把 34 行依据从 ③b④ 改写为 ③b②（含元素类定名）

## 背景（已裁定，直接执行，不要重开）

异族反审 `TIEBREAK_ENGFAM` 的裁定：

- 34 行（`coverage.tsv` 中语义匹配 `(?i)unproven|unverified|not proven`，全 S17、全 `[已证]`、全在 atlas）**结论仍成立**，但**依据错了**：
- **③b④（循环体内有界非栈写）全族不成立**：循环体内写内存只有 `mov [esp+0xC],0`（栈写）+ 6 条 `push`，**非栈写 0 条**。真正的流写发生在 `IStream::Write` / `ole32!OleSaveToStream` 被调用者内部，按 `0045A640` 界线不算本函数循环内写。
- **成立通道是 ③b②**：4 处 call 派生 HRESULT 检查（`test eax,eax` + `jl`），失败落点 `+0x78` 不清零 eax、原样返回，成功 `xor eax,eax` 返回 0；且被调用方以 `test/jge` 消费。
- 该族模板的第 17 个成员是 `0x6805F0`（归 S05），故"35 个槽"指模板副本数，S17 仍是 34 行。

## 目标与材料

- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install
- 只读参考（**都只当线索，不作证据**）：`TIEBREAK_ENGFAM\`（`VERDICT.md`/`FAMILY.md`/`sample.tsv`）、`S17_ENGFAM\`
- 34 行清单：自己从 `coverage.tsv` 过滤，把过滤命令写进报告

## 每一行要做的事

1. **定元素类**：找出该行使用的 `.bss` 向量地址与其类型，沿构造写入点取到元素类的 RTTI 名。给出：向量地址、构造写入点地址、RTTI 描述符地址、类名字符串地址。**取不到就写"未取得"**，不许猜、不许从 `S17-F1` 的旧笔记转抄。
2. **取证 ③b② 锚点**：逐行给出
   - HRESULT 检查点：`test eax,eax` 或 `cmp` 的地址 + 紧随的 `jl/jne` 地址
   - 失败落点地址（应为 `+0x78` 一带，若不同请给出实测值）
   - 成功路径 `xor eax,eax` 地址
   - 至少一处"被调用方消费该返回值"的证据地址
3. **取证 ②③④ 其余三环**：② 类身份（第 1 步结果）、③ 整体合同（③b② 的可伪证返回约定）、④ 使用见证（真实调用者或活虚表派发，**direct-only 不足**）。
4. **改写第 4 列语义**，必须满足：
   - **删除**尾缀 `class name unproven (arg .bss obj)`（该类已定名，措辞不得再自陈未证）
   - **写入** ③b② 表述：可伪证 HRESULT 返回约定的具体形态（失败返回什么、成功返回什么、谁消费）
   - **不得**再出现"循环内非栈写"或 ③b④ 字样
   - 带上第 1–3 步的地址锚
   - 若第 1 步"未取得"类名，则该行**不得**改写（原样留在池里，并在报告里单列）

## 输出（只写自己目录）

- `SEMFIX_ENGFAM\coverage_delta.tsv`
  - 表头 6 列：`entry	subsystem	name	one_line_semantics	grade	evidence_path`
  - **`entry` 一律大写十六进制、不带 `0x` 前缀**（与 `coverage.tsv` 一致，否则无法连表）
  - 只放**成功改写**的行；`grade` 保持 `[已证]`；`evidence_path` 写 `SEMFIX_ENGFAM/EVIDENCE/ROW_<entry>.txt`
  - `name`、`subsystem` 原样不动（**不许顺手改名**，`slotN` 形式不是问题）
- `SEMFIX_ENGFAM\EVIDENCE\ROW_<entry>.txt`：每行一个，含第 1–3 步的地址与字节
- `SEMFIX_ENGFAM\REPORT.md`：34 行总表（entry / 类名取得否 / ③b② 成立否 / 是否改写），以及
  - "类名未取得"的行清单
  - "③b② 复核不成立"的行清单（若出现，这些行要单独标出来，交下一张卡处理）
- `SEMFIX_ENGFAM\base_rate.tsv`：表头 `population	screened	rewritten	rate`，诚实报告改写成功率

## 纪律

- **不许**修改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账；只写 `SEMFIX_ENGFAM\`。
- 不许写 ③b④；不许保留 `unproven` 字样；不许整族共用一段 reason 文字（每行必须有该行自己的地址）。
- 类名取不到就如实写"未取得"，**不许**为了凑满 34 行而编类名。
