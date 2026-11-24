# SEMFIX-ENGFAM-BATCH — 分批把 34 行依据从 ③b④ 改写为 ③b②

## 为什么分批

上一次单卡跑 34 行，代理在写完 3 个脚本后就中断了（约 02:03:50 无后续产出），没有任何 delta / REPORT / EVIDENCE。**原因判定：单代理逐行反汇编 34 行超出其回合预算。**

本卡按批次执行，每批 **17 行**，两个批次并行、各自独立输出目录，互不写同一文件。

## 你的批次（见任务下发时的说明）

- **B1**：34 行中**地址最小的 17 行**，输出目录 `SEMFIX_ENGFAM_B1\`
- **B2**：其余 17 行，输出目录 `SEMFIX_ENGFAM_B2\`

34 行清单自己从 `coverage.tsv` 过滤得到（语义匹配 `(?i)unproven|unverified|not proven`，全 S17、全 `[已证]`、全在 atlas），按 entry 数值升序排序后按你的批次切片。**把切片命令与 17 个 entry 写进报告。**

## 硬性执行纪律（上次失败的教训）

1. **先建目录、先写 REPORT 骨架**，然后再逐行干活。
2. **每核完一行立刻落盘** `EVIDENCE\ROW_<entry>.txt`，不要攒到最后一起写。
3. **每 5 行追加一次** `coverage_delta.tsv` 与进度行到 `PROGRESS.md`，确保中断也不丢已完成的行。
4. 单行取证时间要克制：只取本卡要求的锚点，不做全函数语义重建。
5. 若中途意识到做不完，**立刻写 `PARTIAL.md`** 说明已完成哪几行、剩余哪几行 ⇒ 已完成的行仍然有效。

## 已裁定的事实（不要重开）

- 34 行结论仍成立，但**依据错了**。
- **③b④ 全族不成立**：循环体内写内存只有 `mov [esp+0xC],0`（栈写）+ 6 条 `push`，**非栈写 0 条**。流写发生在 `IStream::Write` / `ole32!OleSaveToStream` 被调用者内部，按 `0045A640` 界线不算本函数循环内写。
- **成立通道是 ③b②**：4 处 call 派生 HRESULT 检查（`test eax,eax` + `jl`），失败落点约 `+0x78` 不清零 eax、原样返回；成功 `xor eax,eax` 返回 0；被调用方以 `test/jge` 消费。
- 该模板第 17 个成员是 `0x6805F0`（归 S05），故"35 个槽"是模板副本数，S17 仍 34 行。

## 目标与工具

- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install
- 只读线索（不作证据）：`TIEBREAK_ENGFAM\`、`S17_ENGFAM\`、`SEMFIX_ENGFAM\`（含上次留下的 `semfix_lib.py` / `s1_scan.py`，**可以复用代码，不可以复用结论**）

## 每行要取的锚点（取到即止）

1. **元素类**：该行用的 `.bss` 向量地址、构造写入点地址、元素类 RTTI 描述符地址、类名字符串地址。取不到写 `未取得`。
2. **③b② 锚点**：HRESULT 检查点（`test eax,eax` 或 `cmp`）地址 + 紧随 `jl/jne` 地址；失败落点地址；成功路径 `xor eax,eax` 地址；**至少一处调用方消费该返回值的地址**。
3. **④ 使用见证**：真实调用者或活虚表派发点（**direct-only 不足**）。

## 第 4 列语义改写要求

- **删掉**尾缀 `class name unproven (arg .bss obj)`
- **写入** ③b② 表述：失败返回什么、成功返回什么、谁消费
- **不得**出现"循环内非栈写"或 ③b④ 字样
- 带第 1–2 步的地址锚
- **类名 `未取得` 的行不得改写**，原样留在池里并在报告单列

## 输出（只写你那个批次目录）

- `coverage_delta.tsv`：表头 6 列 `entry	subsystem	name	one_line_semantics	grade	evidence_path`
  - **`entry` 大写十六进制、不带 `0x` 前缀**
  - `grade` 保持 `[已证]`；`evidence_path` 写 `SEMFIX_ENGFAM_B1/EVIDENCE/ROW_<entry>.txt`（B2 同理换目录名）
  - `name`、`subsystem` 原样不动（**不许顺手改名**）
- `EVIDENCE\ROW_<entry>.txt`：逐行
- `REPORT.md`：本批 17 行总表（entry / 类名取得否 / ③b② 成立否 / 是否改写）+ 切片命令
- `PROGRESS.md`：每 5 行追加的进度
- `base_rate.tsv`：`population	rows	class_named	ring3b2_ok	rewritten	rate`

## 纪律

- **不许**修改 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账；只写你自己那个批次目录。
- 每行必须有该行自己的地址；**不许整批共用一段 reason 文字**（上一张卡的 34 行 reason 全同是本轮被反审的关键触发点）。
- 类名取不到就写 `未取得`，**不许编**。
