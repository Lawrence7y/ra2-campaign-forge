# LEAD_VERIFY_W54_INDEPENDENT · agy(Gemini 4 Hydrogen High) 异模型独立复核

> 记录人：Lead｜时间：2026-11-13 22:35｜手段：**异模型自写解析器 + Lead 亲跑**
> 被复核对象：`W54_save_determinism\SAVE_DETERMINISM.md`（24,924 B）+ `SAVE_NONDET_WHITELIST.json`
> 复核者：`call-agy` / Antigravity `gemini-4-hydrogen-high`（conversation `1b919028-01e9-4989-8407-25e35b522185`，143.5 s，out 26,372 tok）

## 1 · 方法（为什么这算独立）

1. **异模型、异实现**：我要求 Gemini **只用 Python 标准库自己写 CFB 解析器**（禁 `olefile`），**禁止先读 W54 的报告正文**（只许读白名单 JSON 的结构）。它自写了 `parse_cfb()`：header / DIFAT / FAT / directory / mini-FAT / mini-stream 全套；W54 用的是它自己的 `step2_cfb.py`。两条实现互不参考。
2. **Lead 亲跑**：脚本由我落地并执行，不是采信 agy 的自述输出。
   - 脚本：`V54_agy_verify\verify_w54_agy.py`（12,775 B，agy 原文逐字提取，仅补 1 行 `main()` 调用——**agy 的 `__main__` 块忘了调用 `main()`，这是一处真实缺陷，我如实记录**）
   - 命令行：`python verify_w54_agy.py "W45_b_line_equivalence\out" "W54_save_determinism\SAVE_NONDET_WHITELIST.json"`
   - 退出码 **0**

## 2 · 结果（agy 脚本实测输出）

| 判据 | 结果 | 与 W54 是否一致 |
|---|---|---|
| C1 OLE2/CFB v3 头 | **PASS** 8/8（`d0cf11e0a1b11ae1`，ver 3，sec_shift 9/512B，mini_shift 6/64B，hdr 512） | ✅ 一致（且与我 22:32 自己那份名字扫描一致） |
| C2 stream 数 | **PASS** 8/8 各 **15** 个（14 具名 + 1 个 `0x05` 前缀 SummaryInformation） | ✅ 一致 |
| C3 三个 FILETIME 同值 | **PASS** 8/8：每份文件内 `Start Time == Last Save Time == Play Time`（8 B 全等） | ✅ 一致，且**给出了 8 份的具体 FILETIME**（如 A1 `134390495385510000`） |
| C4 A1 vs A2 差异 | `total_diff=1,368,215`（`overlap=1,345,043` + `size_tail=23,172`），白名单覆盖 **54**，未覆盖 **1,368,161** | ✅ `1,345,043` 与 W54 的「掩码前 1,345,043 个差异字节」**逐位吻合** |
| 白名单规模 | **68 字节 / 30 个区间** | ✅ 与 W54「68 个绝对字节」吻合 —— **这条 W54 的计数现在有独立复算支撑了**（`LEAD_VERIFY_W54.md:7` 当时记的「未独立复算」据此闭合） |
| C5 元数据平面 | **0 差异 / 3,131 个未掩码字节** | ✅ 与 W54「元数据平面 A1==A2==B1==B2、0 差异字节」一致 |
| C6 白名单充分性 | 元数据平面 **YES**；全文件 **NO**（未覆盖 1,368,161） | ✅ 与 W54「对元数据平面充分、对全文件不足」一致 |

## 3 · 唯一的数值不一致（记账，不算翻案）

- `C5` 里 `raw_excluding_contents_diff_bytes = **10**`；W54 `§5.3` 提要时说「消掉 **@1012 那 6 字节**」。
- **不构成矛盾**：两者口径不同 —— agy 排除了「白名单 ∪ A1 的 CONTENTS 扇区 ∪ A2 的 CONTENTS 扇区」，W54 说的是「把 FAT/DIFAT 整体排除后残留 6 字节」。候选数组长度与文件长度都不同（A1 1,405,384 vs A2 1,382,212），尾部差异计入方式也不同。
- **处置**：登记为 `UNKNOWNS` 级小分歧，**不影响任何承重结论**（元数据平面 0 差异、全文件不足，两条一致）。若将来要用"残留字节数"做判据，须先统一口径。

## 4 · 签发

- `[签发]` **W54 的四条结构性结论成立**：`.SAV` 是 CFB 复合文档 / 15 个具名 stream / 非确定性只有墙钟时间戳一族（68 B / 30 区间）/ 白名单对元数据平面充分、对全文件不足。
- `[仍不签发]` 「存档字节等价成立」——**没有人**这么说过，W54 也没说；判定要等 W55b 按 frame 对齐重跑。
- `[方法学收获]` 异模型 + 我亲跑 + 禁读原报告，这套组合能在 20 分钟内独立复核一份 25 KB 的结论。**`call-agy` 本轮实测可用**（`gemini-4-hydrogen-high`），与 11-12 记的 `RESOURCE_EXHAUSTED` 状态已不同 —— 台账要更新这条。
- `[给后续卡的硬约束]` agy 会写出**忘调 `main()`** 这类结构缺陷 ⇒ **永远由 Lead 亲跑并检查退出码与输出为空的情况**，不接受"脚本已生成"作为证据。
