# -*- coding: utf-8 -*-
"""M52: apply strict-minimal edits to PANEL.md. Line-based, exact, with verification."""
import io, hashlib

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"

with open(P, "r", encoding="utf-8", newline="") as f:
    raw = f.read()
print("before bytes:", len(raw.encode("utf-8")))
print("before sha:", hashlib.sha256(raw.encode("utf-8")).hexdigest())

# Preserve original line endings: detect
nl = "\n"
lines = raw.split(nl)
print("line count (split):", len(lines))

# --- sanity: confirm expected lines at 1-based positions ---
assert lines[0].startswith("# PANEL — R14 coverage 覆盖面板（M50 并表")
assert lines[12].startswith("| **A · atlas 分母（下界）** | **12,916** |")
assert lines[13].startswith("| **B · 审计口径（下界）** | **14,535** |")
assert lines[14].startswith("| **C · 审计口径（下界）** | **18,479** |")
assert lines[15].startswith("| 当前 `coverage.tsv` 行数 | **18,479** |")
assert lines[16].startswith("| 全表 `[已证]` / atlas 内 `[已证]` | **1,460 / 1,455** |")
assert lines[54] == "## M50 并表说明（P0-ADJ4 去重并入：净新入口 48 行，subsystem 暂填 S22，不计入任何子系统百分比）"

# --- 1) title line: prepend M52 segment ---
m52_title = ("M52 PANEL 全表同步（对齐 M51 后现态；不改 coverage.tsv、不做新裁决；"
             "按盘上重算 coverage 18,498 / 全表 [已证] 1,460 / atlas 内 [已证] 1,455 / "
             "conflict==1 254；C 18,431→18,498（+67=M50 48+M51 19，67 行全 atlas 外/S22/"
             "P0 入口闭合用）；三分母 A/B/C=12,916/14,554/18,498（B 按 §9.1 coverage∖initterm 3,944 "
             "=18,498−3,944=14,554，随 C 同增 67；PANEL M50 旧记 14,535 为仅含 M50 的截面）；"
             "面板 21 行+TOTAL 逐行核对改动 0，达标仍 S15/S16/S17）；")
lines[0] = "# PANEL — R14 coverage 覆盖面板（" + m52_title + lines[0][len("# PANEL — R14 coverage 覆盖面板（"):]

# --- 2) three-denominator table B row ---
lines[13] = ("| **B · 审计口径（下界）** | **14,554** | "
             "= coverage 18,498 − initterm 3,944（§9.1 集合差定义；3,944 = `P0_INITTERM/INITTERM_TABLE.tsv` 全部 target，"
             "实测 3,944 项全在 coverage：3,922 条 name=`initterm_thunk_NNNN` + 22 条早收编 `sub_`）= 14,554；"
             "= 14,487 + 67（M50 48 + M51 19，均非 initterm、S22/atlas 外）；B 与 C 同增同减（§9.1）；"
             "PANEL M50 段旧记 14,535（仅 +48）为当时截面，本卡按含 M51 的现态统一 |")

# --- 3) three-denominator table C row ---
lines[14] = ("| **C · 审计口径（下界）** | **18,498** | "
             "= B + 3,944 = 14,554 + 3,944 = 18,498（≡ `coverage.tsv` 数据行 18,498，实测成立）；"
             "C 口径 18,431 → 18,498：M50 并入 48 行 P0 新入口、M51 并入 19 行（累计 +67）|")

# --- 4) current coverage row count ---
lines[15] = ("| 当前 `coverage.tsv` 行数 | **18,498** | "
             "M50 +48（P0-ADJ4 去重后净新入口，grade 全 [静态推断]、subsystem S22、atlas 外）+ "
             "M51 +19（a-P0-ADJ5 审计确认外部取址证据入口，grade 全 [静态推断]、subsystem S22、atlas 外）；"
             "M46/M45/M44/M43/M42/M41/M34/M31/M28/M26/M25/M24/M23/M21/M20 行数未变（无新增/删除 entry）；"
             "M19 行数未变；M18 K16 +1 提级、M17 K15 +2 提级、M15 K13 +1 提级、M12 K12 +4 提级 |")

# --- 5) proved row: prepend M52 recompute note, keep history ---
old_prefix = "| 全表 `[已证]` / atlas 内 `[已证]` | **1,460 / 1,455** | "
assert lines[16].startswith(old_prefix)
lines[16] = (old_prefix + "M52 盘上重算 **1,460 / 1,455**（M50/M51 +67 行 grade 全 [静态推断]、atlas 外，已证不变；与 M47 段一致）；"
             + lines[16][len(old_prefix):])

# --- 6) insert M52 section before M50 section ---
m52_section = """## M52 PANEL 全表同步（对齐 M51 后现态）

- 同步性质：只读重算，不改 `coverage.tsv`、不做任何新裁决；coverage.tsv SHA-256 改前/改后均 `b4c998c06f91e9b23c0a34ea459a308eee8212671d761b0189b7135dfbcbe94c`。
- **(a) C 口径 18,431 → 18,498**：增 **67** = M50 的 48（P0-ADJ4 去重后净新入口）+ M51 的 19（a-P0-ADJ5 审计确认的外部取址证据入口）；盘上 `coverage.tsv` 数据行 **18,498**（表头 1 行逗号、数据 TAB 8 列），与 C 口径相等。
- **(b) 这 67 行的归属标注**：全部在 atlas 外（exact 命中 0）、subsystem 暂填 S22、grade 全 `[静态推断]`；`one_line_semantics` 语义标注「P0 入口闭合用；归属待 P1，不计入任何子系统百分比」（M51 19 行在 delta 原文基础上据实补外部取址证据，末尾保留该标注）。不进 A 分母（12,916 不变），21 个子系统面板行与 S22 行 atlas 内数值一律不动。
- **(c) B 口径按 §9.1 集合差定义重算为 14,554（原 §9.1 定值是 14,487）**：**B = coverage ∖ initterm 3,944 = 18,498 − 3,944 = 14,554**，即 B 随 C 同增 **67**。理由：实测 `P0_INITTERM/INITTERM_TABLE.tsv` 3,944 个 target 全部在 coverage（3,922 条 name=`initterm_thunk_NNNN` + 22 条早收编 `sub_`），而 M50 的 48 与 M51 的 19 共 67 行**不在**该 3,944 项内（0/67），均为 `sub_` 名/S22/atlas 外，按 §9.1「∖ initterm」集合差定义落入 B；§9.1 明载「B 与 C 是同一入口集合在是否计 thunk 上的两个视图，必须同增同减」，故 C +67 ⇒ B +67（14,487 + 67 = 14,554）。PANEL M50 段旧记 B=14,535（仅 +48）为仅含 M50 的截面，本卡按含 M51 的现态统一为 14,554。
- 三分母 A/B/C = **12,916 / 14,554 / 18,498**；恒等式 B + 3,944 = C（14,554 + 3,944 = 18,498）盘上成立。
- 盘上重算：grade（第 5 列）`[已证]` **1,460** / `[静态推断]` **6,014** / `[未证]` **11,024**（和 18,498）；第 8 列 `conflict==1` **254**；atlas 内 entry **12,916**、atlas 外 **5,582**（其中 S22 **5,386**）；全表已证 **1,460**、atlas 内已证 **1,455**。
- 面板行级：21 个子系统行（S01–S21）+ TOTAL 行逐行核对，改动 **0** 行（atlas 内数值与 M47 完全一致，M50/M51 新入口不进 A 分母）；达标子系统 **S15 / S16 / S17**（判据 `named_n_S(R14) >= ceil(0.9n)` 且 `proved_n >= ceil(0.5n)`，S13 named 216 命中 90% 但 proved 89 < 120 不达标）。
- 未改 CONFLICTS.tsv、PENDING_CORRECTIONS.tsv、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli；未做新裁决、未 git commit、未建 venv、未 pip install。PANEL.md 改前备份 `_hygiene/PANEL.M52.bak`（SHA-256 与改前一致）。

"""
idx = next(i for i, l in enumerate(lines) if l.startswith("## M50 并表说明"))
lines.insert(idx, m52_section)

new_raw = nl.join(lines)
with open(P, "w", encoding="utf-8", newline="") as f:
    f.write(new_raw)

print("after bytes:", len(new_raw.encode("utf-8")))
print("after sha:", hashlib.sha256(new_raw.encode("utf-8")).hexdigest())
print("after line count:", len(lines))
