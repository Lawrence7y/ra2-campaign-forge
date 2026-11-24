# a-NAMED-PUSH — 异族审计 8 行 proved 增量

## 身份

你是**异族独立审计员**。执行器分别是 Hy4（S18/S10）与 DeepSeek（S14），**你不是这两家**。只采信你自己反汇编出的字节。

## 待审：8 行，来自四个批次

| 批次 | 目录 | 行数 | entry |
|---|---|---:|---|
| S18 B1 | `NAMED_PUSH_S18_B1` | 1 | `005414C0` |
| S18 B2 | `NAMED_PUSH_S18_B2` | 2 | `005C46E0`、`0071F8C0` |
| S14 B1 | `NAMED_PUSH_S14_B1` | 5 | `0041F580`、`00503040`、`00512290`、`00512480`、`0065AC40` |
| S10 B2 | `NAMED_PUSH_S10_B2` | 0 | （无产出，仅记录 ④ 18/18 全灭） |

每批的 `delta.tsv` 6 列、`EVIDENCE\ROW_<entry>.txt`、`REPORT.md`、`base_rate.tsv` 都在各自目录下（**只当线索**）。

Lead 已核过格式：8 行全部 6 列、`entry` 为 8 位大写十六进制无 `0x`、`grade = [已证]`、8 个 entry 互不相同。**格式已过关，你审内容真假。**

## 目标与工具

- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install

## 每行必须验的五件事

1. **② 类身份独立成立**：RTTI 描述符 → 类名字串，或虚表地址 + 槽号 + 该槽确实指向本 entry。给地址。
   - `slotN` 名字里的类名**只是线索**；钉不住判 `FAIL`。
2. **③b 的具体形态**：必须属于 ③b①/②/③/④ 之一，给成链的地址与字节。
   - ③b②：失败返回值是什么、成功返回值是什么、**调用方在哪条指令拿它分支**（给 `test/cmp` 与跳转地址）
   - ③b①：跳转表地址、条目数、**每条路径各自的验证地址**
   - **禁止**把「被调用者内部的写」当 ③b④ 的循环内非栈写
   - **禁止** ③a 形态（单调用+单写、纯转发、零+默认、无分支直线）
3. **④ 使用见证独立成立**：活虚表派发点或真实调用者，给地址。
   - **direct-only 不足**
   - **④ 与 ② 必须不同源**：同一个虚表槽不能既证类身份又证被使用。若两者同源 ⇒ `FAIL`
4. **`eax` 覆写陷阱**：`test eax,eax` 后、分支前 `eax` 是否被 `mov eax,[…]` 覆写？覆写则返回值未被消费 ⇒ `FAIL`
5. **语义串与实际是否相符**：执行器写进第 4 列的形态，与你实测的是否一致。**写错了（哪怕只是标错 ③b 子型）也要判 `FAIL`**——依据错误的行不能入账（先例：`004AB9B0`、`Save_VectorBlock` 族）。

## 输出

- `NAMED_PUSH_AUDIT\VERDICT.md`：逐行一节，五项结论 + 地址与字节
- `NAMED_PUSH_AUDIT\verdict.tsv`：表头 `entry	subsystem	verdict	ring2_at	ring3b_form	ring4_at	same_source	reason`，**8 行数据**
  - `verdict` 只能 `PASS` / `FAIL`
  - `entry` 大写十六进制无 `0x`
  - `ring3b_form` 填 `3b1` / `3b2` / `3b3` / `3b4`
  - `same_source` 填 `yes` / `no`（② 与 ④ 是否同源）
  - `reason` 每行不同、含该行自己的地址
- `NAMED_PUSH_AUDIT\SUMMARY.md`：PASS n / FAIL m，逐条列出 FAIL 原因，并回答：
  - 「8 行里靠 ③b② 成立几行、③b① 几行、其它子型几行」
  - 「并入 PASS 的行后，S18 / S14 的 proved 各变为多少」（口径：atlas 内 `[已证]`）

## 执行纪律

1. 先建目录、先写 SUMMARY 骨架，再逐行干
2. 每验完一行立刻落盘
3. 时间不够写 `PARTIAL.md`，已验的行仍有效

## 纪律

- 证据不足判 `FAIL`，不许"基本成立"
- 不许引用执行器的 `ROW_*.txt` 当证据
- **不许修改** `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`NAMED_PUSH_*` 下任何文件；只写 `NAMED_PUSH_AUDIT\`
