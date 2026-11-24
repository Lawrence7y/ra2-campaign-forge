# a-NAMED-PUSH-2 — 异族审计第二批 11 行

## 身份

你是**异族独立审计员**。执行器为 Hy4（S05）与 DeepSeek（S14），**你不是这两家**。只采信你自己反汇编的字节。

## 待审：11 行，三个来源

| 来源目录 | subsystem | 行数 | 说明 |
|---|---|---:|---|
| `NAMED_PUSH_S14_B2` | S14 | 6 | rate 0.3333；其中 4 行是**标量析构**（靠容器 Find 返 -1 分支成立） |
| `NAMED_PUSH_S05_B1` | S05 | 3 | |
| `NAMED_PUSH_S05_B2` | S05 | 2 | |

各目录下有 `delta.tsv`（6 列）、`EVIDENCE\ROW_<entry>.txt`、`REPORT.md`、`base_rate.tsv`，**只当线索**。

先把这 11 个 entry 从三个 `delta.tsv` 里自己取出来，把取法写进报告。

## 目标与工具

- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install

## 每行必须验的五件事（与上一批同标准）

1. **② 类身份独立成立**：RTTI 描述符 → 类名，或虚表地址 + 槽号 + 该槽确指向本 entry。给地址。`slotN` 名字里的类名只是线索。
2. **③b 具体形态**：③b①/②/③/④ 之一，给成链地址与字节。
   - ③b②：失败返回什么、成功返回什么、**调用方哪条指令拿它分支**
   - **禁止**「被调用者内部的写」当循环内非栈写；**禁止** ③a 形态
3. **④ 使用见证独立成立**：活虚表派发点或真实调用者。**direct-only 不足**。
4. **④ 与 ② 不同源**：同一虚表槽不能既证类身份又证被使用。同源 ⇒ `FAIL`。
   - ⚠️ 特别警惕 **㉓ 成对陷阱**：④ 的锚点若落在**析构器**里（而不是正常调用点），判 `FAIL`。上一批 `005C46E0` 正是这样被否的。
5. **语义与实测是否相符**：第 4 列写的方向/形态与你实测是否一致。**读写方向反了、子型标错，都判 `FAIL`**（上一批 `0065AC40` 正是方向写反被否）。

## 本批要特别回答的一件事

S14 的 6 行里有 **4 行是标量析构**，执行器的理由是「全局 `DynamicVectorClass<T*>` 容器 `Find` 返 `-1`（字节 `83 c8 ff`）→ 命中才压缩移除」构成 ③b②。

请对这 4 行单独给结论：

- 这个 `Find` 返 `-1` 的哨兵**是否真被检查并分支**（给 `cmp`/`test` 与跳转地址）？
- 「析构函数体内的容器移除」**是否**构成 ③b② 的「可伪证错误码/返回约定」？你的判断依据是什么？
- 若你认为**析构语义不足以构成 ③b**，明确写出来并判 `FAIL`——**不要**因为执行器已经产出就放行。

## 输出

- `NAMED_PUSH_AUDIT2\VERDICT.md`：逐行一节，五项结论 + 地址字节
- `NAMED_PUSH_AUDIT2\verdict.tsv`：表头 `entry	subsystem	verdict	ring2_at	ring3b_form	ring4_at	same_source	reason`，**11 行**
  - `verdict` 只能 `PASS`/`FAIL`；`entry` 大写无 `0x`；`ring3b_form` 填 `3b1`~`3b4`；`same_source` 填 `yes`/`no`
  - `reason` 每行不同、含本行地址
- `NAMED_PUSH_AUDIT2\SUMMARY.md`：PASS n / FAIL m + FAIL 逐条原因 + 对"S14 4 行析构"的专门结论

## 执行纪律

1. 先建目录、先写 SUMMARY 骨架，再逐行干
2. 每验完一行立刻落盘
3. 时间不够写 `PARTIAL.md`

## 纪律

- 证据不足判 `FAIL`
- 不许引用执行器的 `ROW_*.txt` 当证据
- **不许修改** `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`NAMED_PUSH_*` 下任何文件；只写 `NAMED_PUSH_AUDIT2\`
