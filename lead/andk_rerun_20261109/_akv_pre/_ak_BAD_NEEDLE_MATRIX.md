# _ak_BAD_NEEDLE_MATRIX.md — 坏针哨兵全矩阵（件 × 项）

注射只在写域副本的输入文档上做；被核脚本一律用**原件逐字节副本**（BASE，SHA256 见 §4）。
「注入前判定」= 该件 BASE 基线实跑；「是否被抓」= 注入后 `EXIT≠0 ∧ verdict=FAIL`。

| gate | 项 | 检查内容 | 注射动作 | 注入前 | 注入后 | 注入后 STDOUT | 是否被抓 |
|---|---|---|---|---|---|---|---|
| d27 | 1 | [1] 两文件存在/非空/UTF-8 | 删除 FACTCHECK.md（缺文件负控） | PASS (EXIT=0) | FAIL (EXIT=2) | `'FAIL [1] 文件缺失或不是普通文件: lead/d27_ruling_20261106/FACTCHECK.md\r\n'` | **True** |
| d27 | 2 | [2] ^main:(A|B|C)$ 声明行 | 把 1 行合法声明改成不合法字面量 | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [2] 裁决书须含匹配 ^main:\\s*(A|B|C)\\s*$ 的一行\r\n'` | **True** |
| d27 | 3 | [3] 7 个必需二级标题 | 把二级标题『## 7 诚实账』改名，使 7 个必需小节缺 1 个 | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [3] 缺少二级标题: 诚实账\r\n'` | **True** |
| d27 | 4 | [4] 新证据是否成立 ⊇ 循环论证（单字面量） | 删除 d27 第 4 项单一字面量 '循环论证'（1 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [4] 新证据是否成立小节正文须包含: 循环论证\r\n'` | **True** |
| d27 | 5 | [5] 授权边界 ⊇ 本次不授权（单字面量） | 删除第 5 项单一字面量『本次不授权』（1 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [5] 授权边界小节正文须包含: 本次不授权\r\n'` | **True** |
| d27 | 6 | [6] 未背书 ⊇ 外推 OR 卡顿不存在  ← OR 项（两词全删） | 从 RULING_D27.md 全文删除两根针 '外推'(3 处) 与 '卡顿不存在'(1 处) | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [6] 未背书小节正文须包含: 外推 或 卡顿不存在\r\n'` | **True** |
| d27 | 6.5 | [6b] OR 项只杀一根针（删『卡顿不存在』） | 从 RULING_D27.md 全文删除第二根针 '卡顿不存在'（1 处）；第一根针 '外推' 保留 | PASS (EXIT=0) | PASS (EXIT=0) | `'PASS: D-27 八项机械检查通过；裁决书引用 71 处\r\n'` | **False** |
| d27 | 7 | [7] 裁决书引用 ≥8 处 | 把 71 处 file:line 引用的行号换成非数字，令引用计数 <8 | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [7] 裁决书引用须至少 8 处，实际 0 处\r\n'` | **True** |
| d27 | 8 | [8] FACTCHECK ⊇ selfBias | 从 FACTCHECK.md 删除第 8 项字面量 selfBias（7 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [8] FACTCHECK.md 须包含 selfBias\r\n'` | **True** |
| d28 | 1 | [1] 两文件存在/非空/UTF-8 | 删除 FACTCHECK.md（缺文件负控） | PASS (EXIT=0) | FAIL (EXIT=2) | `'FAIL [1] 文件缺失：lead/d28_ruling_20261106/FACTCHECK.md\r\nRESULT: FILE MISSING (exit 2)\r\n'` | **True** |
| d28 | 2 | [2] q1/q2 恰一行合法声明 | 把 2 行合法声明改成不合法字面量 | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [2] q1 须恰有一行合法声明（A|B|C）；合法 0 行，声明 1 行\r\nFAIL [2] q2 须恰有一行合法声明（甲|乙|丙|丁）；合法 0 行，声明 1 行\r\nRESULT: FAIL (exit 1)\r\n'` | **True** |
| d28 | 3 | [3] 7 个必需小节 | 把二级标题『## 7 诚实账』改名，使 7 个必需小节缺 1 个 | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [3] 缺少小节：诚实账\r\nRESULT: FAIL (exit 1)\r\n'` | **True** |
| d28 | 4 | [4] 历史数字 / 1681  ← OR 项（两词全删） | 从 RULING_D28.md 全文删除两根针 '历史数字'(3 处) 与 '1681'(5 处) | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [4] D 链处置 小节正文须至少包含其一：历史数字、1681\r\nRESULT: FAIL (exit 1)\r\n'` | **True** |
| d28 | 4.5 | [4b] OR 项只杀一根针（删『1681』） | 从 RULING_D28.md 全文删除第二根针 '1681'（5 处）；第一根针 '历史数字' 保留 | PASS (EXIT=0) | PASS (EXIT=0) | `'PASS: D-28 全部 8 项机械检查通过 (exit 0)\r\n'` | **False** |
| d28 | 5 | [5] 授权边界 ⊇ 本次不授权（单字面量） | 删除第 5 项单一字面量『本次不授权』（2 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [5] 授权边界 小节正文须同时包含：本次不授权\r\nRESULT: FAIL (exit 1)\r\n'` | **True** |
| d28 | 6 | [6] 未背书 AND 词表（删『外推』） | 删除第 6 项 AND 词表里的 '外推'（1 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [6] 未背书 小节正文须同时包含：外推、口径 B\r\nRESULT: FAIL (exit 1)\r\n'` | **True** |
| d28 | 7 | [7] 裁决书引用 ≥8 处 | 把 69 处 file:line 引用的行号换成非数字，令引用计数 <8 | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [7] RULING_D28.md 全文引用须至少 8 处，实际 0 处\r\nRESULT: FAIL (exit 1)\r\n'` | **True** |
| d28 | 8 | [8] FACTCHECK ⊇ selfBias | 从 FACTCHECK.md 删除第 8 项字面量 selfBias（7 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'FAIL [8] FACTCHECK.md 缺少 selfBias 字样\r\nRESULT: FAIL (exit 1)\r\n'` | **True** |
| d29 | 1 | [1] 两文件存在/非空/UTF-8 | 删除 FACTCHECK.md（缺文件负控） | PASS (EXIT=0) | FAIL (EXIT=2) | `'[1] Missing file: D:\\Project\\ra2-campaign-forge\\lead\\andk_rerun_20261109\\sandbox\\d29\\inj_1\\FACTCHECK.md\r\nFAIL (missing files)\r\n'` | **True** |
| d29 | 2 | [2] q1 恰一行合法声明 | 把 1 行合法声明改成不合法字面量 | PASS (EXIT=0) | FAIL (EXIT=1) | `'[2] RULING_D29.md: missing valid q1 line (甲/乙/丙/丁)\r\nFAIL (content)\r\n'` | **True** |
| d29 | 3 | [3] 7 个必需小节 | 把二级标题『## 7 诚实账』改名，使 7 个必需小节缺 1 个 | PASS (EXIT=0) | FAIL (EXIT=1) | `'[3] RULING_D29.md: missing section: 诚实账\r\nFAIL (content)\r\n'` | **True** |
| d29 | 4 | [4] 互斥 / 前提  ← OR 项（两词全删） | 从 RULING_D29.md 全文删除两根针 '互斥'(5 处) 与 '前提'(2 处) | PASS (EXIT=0) | FAIL (EXIT=1) | `'[4] Section 冲突是否成立: body must contain 互斥 OR 前提\r\nFAIL (content)\r\n'` | **True** |
| d29 | 4.5 | [4b] OR 项只杀一根针（删『前提』） | 从 RULING_D29.md 全文删除第二根针 '前提'（2 处）；第一根针 '互斥' 保留 | PASS (EXIT=0) | PASS (EXIT=0) | `'PASS\r\n'` | **False** |
| d29 | 5 | [5] 授权边界 ⊇ 本次不授权（单字面量） | 删除第 5 项单一字面量『本次不授权』（2 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'[5] Section 授权边界: body must contain 本次不授权\r\nFAIL (content)\r\n'` | **True** |
| d29 | 6 | [6] 未背书 AND 词表（删『外推』） | 删除第 6 项 AND 词表里的 '外推'（1 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'[6] Section 未背书: body must contain 口径 B AND 外推 AND 191\r\nFAIL (content)\r\n'` | **True** |
| d29 | 7 | [7] 裁决书引用 ≥8 处 | 把 52 处 file:line 引用的行号换成非数字，令引用计数 <8 | PASS (EXIT=0) | FAIL (EXIT=1) | `'[7] RULING_D29.md: found 0 citations; need at least 8\r\nFAIL (content)\r\n'` | **True** |
| d29 | 8 | [8] FACTCHECK ⊇ selfBias | 从 FACTCHECK.md 删除第 8 项字面量 selfBias（6 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'[8] FACTCHECK.md: missing selfBias\r\nFAIL (content)\r\n'` | **True** |
| d30 | 1 | [1] 两文件存在/非空/UTF-8 | 删除 FACTCHECK.md（缺文件负控） | PASS (EXIT=0) | FAIL (EXIT=2) | `'[1] Missing file: D:\\Project\\ra2-campaign-forge\\lead\\andk_rerun_20261109\\sandbox\\d30\\inj_1\\FACTCHECK.md\r\nFAIL (missing files)\r\n'` | **True** |
| d30 | 2 | [2] q1 恰一行合法声明 | 把 1 行合法声明改成不合法字面量 | PASS (EXIT=0) | FAIL (EXIT=1) | `'[2] RULING_D30.md: missing valid q1 line (甲/乙/丙/丁/戊)\r\nFAIL (content)\r\n'` | **True** |
| d30 | 3 | [3] 7 个必需小节 | 把二级标题『## 7 诚实账』改名，使 7 个必需小节缺 1 个 | PASS (EXIT=0) | FAIL (EXIT=1) | `'[3] RULING_D30.md: missing section: 诚实账\r\nFAIL (content)\r\n'` | **True** |
| d30 | 4 | [4] 93.98 / 误报率  ← OR 项（两词全删） | 从 RULING_D30.md 全文删除两根针 '93.98'(3 处) 与 '误报率'(3 处) | PASS (EXIT=0) | FAIL (EXIT=1) | `'[4] Section 三档权衡的实质: body must contain 93.98 OR 误报率\r\nFAIL (content)\r\n'` | **True** |
| d30 | 4.5 | [4b] OR 项只杀一根针（删『误报率』） | 从 RULING_D30.md 全文删除第二根针 '误报率'（3 处）；第一根针 '93.98' 保留 | PASS (EXIT=0) | PASS (EXIT=0) | `'PASS\r\n'` | **False** |
| d30 | 5 | [5] 授权边界 ⊇ 本次不授权（单字面量） | 删除第 5 项单一字面量『本次不授权』（2 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'[5] Section 授权边界: body must contain 本次不授权\r\nFAIL (content)\r\n'` | **True** |
| d30 | 6 | [6] 未背书 AND 词表（删『外推』） | 删除第 6 项 AND 词表里的 '外推'（4 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'[6] Section 未背书: body must contain 外推 AND 栈采样\r\nFAIL (content)\r\n'` | **True** |
| d30 | 7 | [7] 裁决书引用 ≥8 处 | 把 51 处 file:line 引用的行号换成非数字，令引用计数 <8 | PASS (EXIT=0) | FAIL (EXIT=1) | `'[7] RULING_D30.md: found 0 citations; need at least 8\r\nFAIL (content)\r\n'` | **True** |
| d30 | 8 | [8] FACTCHECK ⊇ selfBias | 从 FACTCHECK.md 删除第 8 项字面量 selfBias（8 处） | PASS (EXIT=0) | FAIL (EXIT=1) | `'[8] FACTCHECK.md: missing selfBias\r\nFAIL (content)\r\n'` | **True** |

## 汇总

| gate | 8 项 AND_8 | 9 行 AND_9（含「只杀一根针」） | 抓到数 | 漏抓项 |
|---|---|---|---|---|
| d27 | True | **False** | 8/9 | [6b] OR 项只杀一根针（删『卡顿不存在』） |
| d28 | True | **False** | 8/9 | [4b] OR 项只杀一根针（删『1681』） |
| d29 | True | **False** | 8/9 | [4b] OR 项只杀一根针（删『前提』） |
| d30 | True | **False** | 8/9 | [4b] OR 项只杀一根针（删『误报率』） |

**7 项单一字面量的结论**：本实跑把 8 个编号项各自注射一根坏针，四件全部 8/8 被抓（`AND_8=True`）：`[1]` 缺文件、`[2]` 声明行、`[3]` 小节标题、`[4]`/`[5]`/`[6]` 字面量、`[7]` 引用计数、`[8]` selfBias。即单元素 `all([word in body])` 在本口径下**都在工作**，删掉字面量即非零退出。
**唯一漏抓**是每件额外加的第 9 行「OR 项只杀一根针」：四件全部 `注入后仍 PASS / EXIT=0`。这不是「单项检查没工作」，而是 OR 语义本身允许另一根针单独满足 ⇒ `AND_9=False`。

