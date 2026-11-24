# ERRATA_W7 · W7 组引用勘误 —— 八行表限定句登记（只写限定句，不做 phase 2）

被核对象 = W9_SINGLESTEP.md / W8_STATIC_LOCATE.md / W7_W4_REVIEW.md / V6_V3_REVIEW.md
W9_SINGLESTEP.md  SHA256 = 13fa9fe35339ea40d123cf340b09c9ac692e848305ebc48d9d35f5421d895e36，字节数 = 40,592
W8_STATIC_LOCATE.md SHA256 = 20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262，字节数 = 26,485
W7_W4_REVIEW.md  SHA256 = 22753a0ef603c6999c95b25e28a2b5a2d5820ded39c9b59559d088bf20da6ca6，字节数 = 19,225
V6_V3_REVIEW.md  SHA256 = 75cad20763952e7a6d92274f8d29e7db30c307194e45437d8d459242baceffdb，字节数 = 17,892
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（目标镜像，本任务不反汇编它）
回件时刻 = 2026-11-06 08:23:11 +0800

> 以上五个 SHA256 / 字节数均为本组在本回件内用 `sha256sum` + `wc -c` **自算实得**（命令与输出见 §4），
> 非照抄 Leader 参照值；自算结果与参照值逐位一致。

## 0 总判与职责边界

- **本组总判：CONFIRMED** —— 八条限定句的每一个要素都落到 `W7_W4_REVIEW.md` 的 文件:行，或本组实跑命令的输出。
- **职责边界**：本组**只读** `W7_W4_REVIEW.md` 的表述、只写限定句；**未重跑、未复核、未"顺便验证"任何 W7 项的实质内容**
  （D-24 `RULING_D24.md:75`：另起 run 原样补完被用户停止的 phase 2 = 换名重建同一任务，禁止）。
  本组对 phase 2 仅做了一次**存在性/字节大小检查**（`ls -la` / `find`，见 §4-5、§4-6），用途是兑现限定句里
  「phase 2 未完成」这半句的证据，**不构成复核**；5 个落盘件的内容一字未读。
- 被核对象 = `W7_W4_REVIEW/W7_W4_REVIEW.md` §0 的八行表。**数据行实际是 :20-27**
  （:18 表头、:19 分隔线、:28 空行、:29-30 为表后备注行）；任务书写的「:20-30」把备注行也计入了（见 §6-1）。
- 汇总件语境：`W7_W4_REVIEW.md:14` 总判 **PARTIAL**；`:4-7` 记 phase 2 未完成 ⇒ 封顶 PARTIAL；
  `:30`「未经 phase 2 的 CONFIRMED 只按 PARTIAL 级信任采信」；`:212`「七项 CONFIRMED 一律按『phase 1 初判』引用」。

## 1 八行表逐项限定句（七项 + A1）

统一形状：「**phase 1 初判，phase 2 未完成，仅按 PARTIAL 采信**」，句内同时注明 phase-1 原档。
七项（A2–C）的 phase-1 原档均为 **CONFIRMED（被降级）**；A1 的 phase-1 原档为**本身就是 PARTIAL（非降级）**。

一览（逐字引用与限定句见各分条）：

| 项 | 被核对象 | 原位置 | phase-1 原档 | 汇总件已落实 | 判定档 |
|---|---|---|---|---|---|
| A1 | `card_0087E8E0.md` | `W7_W4_REVIEW.md:20` | 本来就是 PARTIAL（非降级） | 部分落实 | CONFIRMED |
| A2 | `card_00A8EC34.md` | `W7_W4_REVIEW.md:21` | CONFIRMED（被降级） | 部分落实 | CONFIRMED |
| A3 | `card_00B0CE88.md` | `W7_W4_REVIEW.md:22` | CONFIRMED（被降级） | 部分落实 | CONFIRMED |
| A4 | `card_00A8ED50.md` | `W7_W4_REVIEW.md:23` | CONFIRMED（被降级） | 部分落实 | CONFIRMED |
| B1 | `Q2_ALPHA.md` | `W7_W4_REVIEW.md:24` | CONFIRMED（被降级） | 部分落实 | CONFIRMED |
| B2 | `Q3_FRAME_EDGE_SPEC.md` | `W7_W4_REVIEW.md:25` | CONFIRMED（被降级） | 部分落实 | CONFIRMED |
| B3 | `Q4_REDLINE.md` | `W7_W4_REVIEW.md:26` | CONFIRMED（被降级） | 部分落实 | CONFIRMED |
| C | 七份跨文件一致性 | `W7_W4_REVIEW.md:27` | CONFIRMED（被降级） | 部分落实 | CONFIRMED |

「部分落实」的统一理由：汇总件已在八行表逐项标注「降级为『phase 1 初判』」（`:21-27`）与 A1 的 PARTIAL（`:20`），
并有总规则（`:30`、`:212`）；但「仅按 PARTIAL 采信」的**逐字统一限定句在汇总件中不存在**
（`grep -n "仅按 PARTIAL\|PARTIAL 采信"` 零命中，见 §4-4），A1 的「自身即 PARTIAL、非被降级」也未以一句话明写
（仅由 `:20` 的 phase-1 列与 `:29` 隐含）。本勘误补的正是这句。

### W7-A1 · `card_0087E8E0.md`（代际尝试代理）

- 原位置：`lead/re_line_20261105/W7_W4_REVIEW/W7_W4_REVIEW.md:20`
- 原断言（逐字引用）：
  ```
  | A1 | `card_0087E8E0.md` | **PARTIAL** | 未完成（`_rerun_a1_out.txt` 589 B，仅跑到 §1.1） | PARTIAL |
  ```
- **phase-1 原档：本来就是 PARTIAL（不是被降级的）。**
- **限定句（逐字可粘贴）**：
  > 【W7-A1 · card_0087E8E0.md（代际尝试代理）】phase 1 初判即为 PARTIAL：A1 自身就是 PARTIAL（三处文字级必改所致，substantiveDefect=false），不是由 CONFIRMED 降级而来；phase 2 复核未完成，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:20 两列均记 PARTIAL、:29 明写「七份里只有 A1 判 PARTIAL」、:36-41 给出三条理由，
  但「自身即 PARTIAL（非降级）」未以一句话明写，统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:20`（表行）、`:29`、`:36-41`（三条理由与 `substantiveDefect = false`、A1 记 PARTIAL）、
  `:75`（§2 标题）、`:192-194`（必改项 1–3：`:54` linker-map 假陈述、`:47` `0x67C8E0`→`0x6C8E0`、`:306` `0x56721B`→`0x56721A`）；
  本组实查 `ls -la reviews/`：`_rerun_a1_out.txt` 589 B 在盘（存在性/大小，内容未读）。

### W7-A2 · `card_00A8EC34.md`（索敌入口累计）

- 原位置：`W7_W4_REVIEW.md:21`
- 原断言（逐字引用）：
  ```
  | A2 | `card_00A8EC34.md` | CONFIRMED | 未完成（无落盘） | 降级为「phase 1 初判」 |
  ```
- **phase-1 原档：CONFIRMED（被降级）。**
- **限定句（逐字可粘贴）**：
  > 【W7-A2 · card_00A8EC34.md（索敌入口累计）】phase 1 初判 CONFIRMED，phase 2 复核未完成（无落盘），按铁律 9 降级，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:21 已标降级；统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:21`、`:30`、`:212`；本组实查 `reviews/` 目录无 A2 对应复核落盘件（与表行「无落盘」一致）。

### W7-A3 · `card_00B0CE88.md`（脏矩形 Count）

- 原位置：`W7_W4_REVIEW.md:22`
- 原断言（逐字引用）：
  ```
  | A3 | `card_00B0CE88.md` | CONFIRMED | 未完成（无落盘） | 降级为「phase 1 初判」 |
  ```
- **phase-1 原档：CONFIRMED（被降级）。**
- **限定句（逐字可粘贴）**：
  > 【W7-A3 · card_00B0CE88.md（脏矩形 Count）】phase 1 初判 CONFIRMED，phase 2 复核未完成（无落盘），按铁律 9 降级，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:22 已标降级；统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:22`、`:30`、`:212`；`reviews/` 无 A3 对应复核落盘件。

### W7-A4 · `card_00A8ED50.md`（Bullet Count）

- 原位置：`W7_W4_REVIEW.md:23`
- 原断言（逐字引用）：
  ```
  | A4 | `card_00A8ED50.md` | CONFIRMED | 未完成（无落盘） | 降级为「phase 1 初判」 |
  ```
- **phase-1 原档：CONFIRMED（被降级）。**
- **限定句（逐字可粘贴）**：
  > 【W7-A4 · card_00A8ED50.md（Bullet Count）】phase 1 初判 CONFIRMED，phase 2 复核未完成（无落盘），按铁律 9 降级，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:23 已标降级；统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:23`、`:30`、`:212`；`reviews/` 无 A4 对应复核落盘件。

### W7-B1 · `Q2_ALPHA.md`（alpha 可解性）

- 原位置：`W7_W4_REVIEW.md:24`
- 原断言（逐字引用）：
  ```
  | B1 | `Q2_ALPHA.md` | CONFIRMED | 未完成（`_b1_rerun_out.txt` **0 字节**） | 降级为「phase 1 初判」 |
  ```
- **phase-1 原档：CONFIRMED（被降级）。**
- **限定句（逐字可粘贴）**：
  > 【W7-B1 · Q2_ALPHA.md（alpha 可解性）】phase 1 初判 CONFIRMED，phase 2 复核未完成（复核探针输出 0 字节，复核意见未落盘），按铁律 9 降级，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:24 已标降级；统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:24`、`:30`、`:212`；本组实查 `ls -la reviews/`：`_b1_rerun_out.txt` 0 B 在盘。

### W7-B2 · `Q3_FRAME_EDGE_SPEC.md`（帧沿规格）

- 原位置：`W7_W4_REVIEW.md:25`
- 原断言（逐字引用）：
  ```
  | B2 | `Q3_FRAME_EDGE_SPEC.md` | CONFIRMED | 未完成（`B2_probe_rerun_out.txt` 19,631 B，探针跑完但复核意见未落盘） | 降级为「phase 1 初判」 |
  ```
- **phase-1 原档：CONFIRMED（被降级）。**
- **限定句（逐字可粘贴）**：
  > 【W7-B2 · Q3_FRAME_EDGE_SPEC.md（帧沿规格）】phase 1 初判 CONFIRMED，phase 2 复核未完成（探针跑完但复核意见未落盘），按铁律 9 降级，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:25 已标降级；统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:25`、`:30`、`:212`；本组实查 `ls -la reviews/`：`B2_probe_rerun_out.txt` 19,631 B 在盘。

### W7-B3 · `Q4_REDLINE.md`（三红线重评）

- 原位置：`W7_W4_REVIEW.md:26`
- 原断言（逐字引用）：
  ```
  | B3 | `Q4_REDLINE.md` | CONFIRMED | 未完成（`_b3_reprobe.txt` **0 字节**） | 降级为「phase 1 初判」 |
  ```
- **phase-1 原档：CONFIRMED（被降级）。**
- **限定句（逐字可粘贴）**：
  > 【W7-B3 · Q4_REDLINE.md（三红线重评）】phase 1 初判 CONFIRMED，phase 2 复核未完成（复核探针输出 0 字节，复核意见未落盘），按铁律 9 降级，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:26 已标降级；统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:26`、`:30`、`:212`；本组实查 `ls -la reviews/`：`_b3_reprobe.txt` 0 B 在盘。

### W7-C · 七份跨文件一致性

- 原位置：`W7_W4_REVIEW.md:27`
- 原断言（逐字引用）：
  ```
  | C | 七份跨文件一致性 | CONFIRMED | 未完成（`_cprobe_rerun.txt` 12,697 B，探针跑完但复核意见未落盘） | 降级为「phase 1 初判」 |
  ```
- **phase-1 原档：CONFIRMED（被降级）。**
- **限定句（逐字可粘贴）**：
  > 【W7-C · 七份跨文件一致性】phase 1 初判 CONFIRMED，phase 2 复核未完成（探针跑完但复核意见未落盘），按铁律 9 降级，仅按 PARTIAL 采信。
- 汇总件已落实：**部分落实**（:27 已标降级；统一限定句不存在）。
- 判定档：**CONFIRMED**。
- 证据：`W7_W4_REVIEW.md:27`、`:30`、`:212`；本组实查 `ls -la reviews/`：`_cprobe_rerun.txt` 12,697 B 在盘。

## 2 A1 单独说明（自身即 PARTIAL，非降级）

1. A1 的 PARTIAL 是它 **phase 1 判定的原档**：八行表 `:20` 的「phase 1 判定」列即为 `**PARTIAL**`，
   「计入本判定书」列也是 `PARTIAL` —— 与 A2–C 七项的「CONFIRMED → 降级为『phase 1 初判』」是**两种不同路径**。
   判定书 `:29` 明写：「七份里只有 A1 判 PARTIAL，其余七项（含 C 组）phase 1 判 CONFIRMED」。
2. PARTIAL 的成因（`:36-41`、`:89-90`、`:192-194`）：三处**文字级**必改 ——
   `card_0087E8E0.md:54`「仓内 `*.MAP` 均为 FinalAlert2 地图，无 linker map」为**假**（实有
   `out/re_work/fog_probe/mapbuild/ra2render.map` 247,159 B 的 MSVC linker map）；
   `:47` `0x87E8E0 − 0x812000` 误写 `0x67C8E0`（应为 `0x6C8E0`，结论不受影响）；
   `:306` `0x56721B` 应为 `0x56721A`（差 1 字节）。三者 `substantiveDefect = false`，A1 的三个重点结论不翻转。
3. ⇒ 引用 A1 时**不得**表述为「A1 被 phase 2 / D-24 降级」；只能表述为
   「A1 phase 1 即判 PARTIAL（三处文字级必改），phase 2 未完成，按 PARTIAL 采信」（即 §1 的 W7-A1 限定句）。
4. 以上内容级事实本组**未重新复核**，全部采信 `W7_W4_REVIEW.md` 原文（Leader 亲验记录见该文件 §6-1）。

## 3 引用规则（可直接贴给别人照做）

1. **引用 W7 任一项（A1–A4、B1–B3、C）的结论时，必须整句带上该条的限定句**（§1 各分条「限定句」栏，逐字），
   并给出来源 `W7_W4_REVIEW.md:20-27`。**不得**把八行表「phase 1 判定」列里的 CONFIRMED 单独抽出当作 CONFIRMED 引用。
2. 七项通用最小限定句（上下文已点名具体项时可用）：
   > phase 1 初判，phase 2 未完成，仅按 PARTIAL 采信。
3. **A1 专用**：引用 `card_0087E8E0.md` 相关结论时，限定句必须写明「**自身即 PARTIAL（三处文字级必改），不是由 CONFIRMED 降级而来**；
   phase 2 复核未完成，仅按 PARTIAL 采信」—— 禁止写成「A1 被降级」。
4. 引用 `W7_W4_REVIEW.md` 判定书本身时，必须同时注明：总判 PARTIAL（`:14`）、phase 2 未完成（`:4-7`、`:210`）、
   phase 4 未跑（`:212`）；其中「探针输出落盘个数」以 **5** 为准（`:210` 与 `reviews/` 落盘实况一致；`:4` 的「4 个」为笔误，见 §6-2）。
5. 本勘误**不授权**任何形式的 W7 phase 2 重开（D-24 `RULING_D24.md:75`；换名重开同违）。

## 4 本组实跑命令与输出（全部在本回件内执行）

1. `sha256sum`（Git Bash，工作目录 `D:/Project/ra2-campaign-forge`）：
   ```
   13fa9fe35339ea40d123cf340b09c9ac692e848305ebc48d9d35f5421d895e36 *lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md
   20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262 *lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md
   22753a0ef603c6999c95b25e28a2b5a2d5820ded39c9b59559d088bf20da6ca6 *lead/re_line_20261105/W7_W4_REVIEW/W7_W4_REVIEW.md
   75cad20763952e7a6d92274f8d29e7db30c307194e45437d8d459242baceffdb *lead/re_line_20261105/V6_V3_REVIEW/V6_V3_REVIEW.md
   73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476 *ra2youli/gamemd.exe
   ```
2. `wc -c`（同上四份 .md）：40,592 / 26,485 / 19,225 / 17,892 B（合计 104,194）。
3. `grep -n "^| A[1-4] \|^| B[1-3] \|^| C |" W7_W4_REVIEW.md` → 八行表数据行定位为 **:20-27**（八行逐字内容见 §1 各分条）。
4. `grep -n "phase 1 初判\|仅按 PARTIAL\|PARTIAL 采信\|探针输出" W7_W4_REVIEW.md` →
   命中 `:4`（探针输出）、`:21-27`（phase 1 初判）、`:210`（探针输出）、`:212`（phase 1 初判）；
   **「仅按 PARTIAL」「PARTIAL 采信」零命中** ⇒ 统一限定句在汇总件中不存在（判定「部分落实」的依据）。
   另：`:4` 称「只有 4 个探针输出落盘」，`:210` 称「只落了 5 个探针输出」（见 §6-2）。
5. `ls -la parts/ reviews/` →
   `parts/`：A1–A4、B1–B3、C 八份 .md（20,077 / 26,333 / 19,981 / 16,000 / 21,526 / 17,121 / 22,997 / 24,728 B）；
   `reviews/`：**恰好 5 个文件、零份 `*_review.md`** ——
   `B2_probe_rerun_out.txt` 19,631 B、`_b1_rerun_out.txt` 0 B、`_b3_reprobe.txt` 0 B、`_cprobe_rerun.txt` 12,697 B、
   `_rerun_a1_out.txt` 589 B（五个大小与 `:20-27` 表行及 `:210` 的记载逐项一致）。
6. `find "…/lead/re_line_20261105" \( -name "_rerun_a1_out.txt" -o -name "_b1_rerun_out.txt" -o -name "B2_probe_rerun_out.txt" -o -name "_b3_reprobe.txt" -o -name "_cprobe_rerun.txt" \)` →
   仅命中 `W7_W4_REVIEW/reviews/` 下上述 5 个文件，无其他副本。

## 5 诚实账

1. **本组做了**：四份被核 .md + `gamemd.exe` 的 SHA256/字节数自算；八行表行号定位与逐字摘录；限定句撰写；
   phase 2 落盘状态的存在性/大小检查（`ls`/`find`，未读任何落盘件内容）。
2. **本组没做（且被禁止做）**：未重跑、未复核、未"顺便验证" A1–C 八项的任何实质判断；
   未读 `_rerun_a1_out.txt` 等落盘件内容（「仅跑到 §1.1」等内容级描述系采信 `W7_W4_REVIEW.md:20` 原文）；
   未动 W4 七份正文、未动 `W7_W4_REVIEW.md`、未动任何既有件。
3. 零真机、零采样注入、未用 `ra2tool.Engine`（一次都没用）、未用任何 Python 探针（纯 shell：`sha256sum`/`wc`/`grep`/`ls`/`find`/`date`）、未 commit、未 push。
4. 唯一写域内的写入 = 本文件 `ERRATA_W7.md`。
5. 未验项：无 —— 本组全部断言均已落到 文件:行 或本回件内实跑命令的输出；超出此范围的（如八项实质复核）属禁止事项而非未验。

## 6 本组发现 Leader 写错/不一致的地方

1. **行号小误**：任务书称八行表在「`:20-30`」；实际数据行为 **`:20-27`**（`:18` 表头、`:19` 分隔线、`:28` 空行、`:29-30` 为表后备注行）。
   非实质，但后续引用行号应以 `:20-27` 为准。
2. **`W7_W4_REVIEW.md:4` 与 `:210` 自相矛盾**：`:4` 写「只有 **4 个**探针输出落盘、其中 2 个是 0 字节空文件」，
   `:210` 写「只落了 **5 个**探针输出、2 个是 0 字节」；§0 表（`:20-27`）列出的 phase-2 落盘件也是 **5 个**
   （`_rerun_a1_out.txt` 589 B、`_b1_rerun_out.txt` 0 B、`B2_probe_rerun_out.txt` 19,631 B、`_b3_reprobe.txt` 0 B、`_cprobe_rerun.txt` 12,697 B），
   本组 `ls -la reviews/` 实查磁盘恰好这 5 个 ⇒ **`:4` 的「4 个」为错，以 5 为准**。
   不影响本组限定句（限定句不引用该计数），但引用该判定书时此数字不得再以 `:4` 为据。
3. **参照值核对结果（非错误，登记备查）**：Leader 给的四份参照 SHA256/字节数与本组自算逐位一致；
   `gamemd.exe` 的 `73201cc0…` 亦自算一致（并见 `W7_W4_REVIEW.md:62` 同值）。
