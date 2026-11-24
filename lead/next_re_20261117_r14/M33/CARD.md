# M33 · 并入 `a-S21-C3` 白名单 **2 行**（`0053AF40` `00595740`）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M33\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M33.bak`。

## 审计裁定（`a-S21-C3` PARTIAL）
卡交 5 行，审计逐行复算后：**只有 2 行四环齐全**。

### ✅ 白名单 2 行（`[未证]` → `[已证]`；**name 保持盘上现值不动**）

| entry | 盘上 name | 盘上 grade | 新 grade |
|---|---|---|---|
| `0053AF40` | `PsyDom::Update` | `[未证]` | `[已证]` |
| `00595740` | `sub_00595740` | `[未证]` | `[已证]` |

**语义栏用 delta 里那两行**（审计已验 ③ 成立）：
- `0053AF40`：审计实测「跳表 stage0→+0x11E、1→+0x17、2→+0x24、3→+0x82、4→+0xB3、5→+0xFF，**11/11 断言全中**」。**用 delta 的语义原文**（已含这些偏移）。
- `00595740`：审计说「成立（13 处成员 ctor，只漏列 +0x13D/+0x152）」⇒ **用 delta 的语义原文**，但**若 delta 里没有 +0x13D/+0x152，请在该行语义末尾补一句**：`另有 +0x13D/+0x152 两处成员 ctor（vt 0x7ED90C）`。

⚠️ **`00595740` 的 evidence_path 必须改**：审计明确要求「把『审计白名单』换成 `YRpp/MapSeedClass.h:8-109` + `0x7E4DD8`/`0x7ED90C` 的 COL→TD 链」。
   请把该行的 `evidence_path` 改为指向 `S21_C3\_audit\VERDICT.md` §3（那里有 YRpp 原文行 + COL→TD 实测），并在语义或备注里保留「YRpp `MapSeedClass.h` + 字节双吻合」字样。

### ❌ 不得并入的 3 行（**整行不动**，保持盘上现值）
| entry | 盘上 grade | 审计理由 |
|---|---|---|
| `00539760` | `[未证]` | ③ 属 P 级（清零/置默认值，「多个全局」未具名），`+0xE7` 偏移错 |
| `0053AB50` | `[未证]` | 整个函数只有 4 条指令（一调一写），D-40 明文排除 |
| `00599650` | `[静态推断]` | ③ 内容真但**两处偏移区间坏**（应为 `+0x15~+0xF8` 与 `+0xEF8~+0xF9C`）；② 仍缺 |

## 硬要求
1. **只改 2 行的第 4/5/6 列**（semantics / grade / evidence_path）；**name 与 subsystem 不动**。
2. 合并后数据行仍 **18,431**；`conflict=1` 保持 **254**。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M33\MERGE_LOG.tsv`：2 行改动 + 3 行 rejected（附理由）+ 一句「按 D-41 默认(A)：② 无通道即不升」。
4. 更新 `COVERAGE\PANEL.md`（S21 段）。

## 预期（自行核对，不符先停）
- `[已证]` **1,386 → 1,388**（+2）｜`[未证]` **11,026 → 11,024**（−2）｜`[静态推断]` 6,019 不变；和 = 18,431
- **S21：proved 26 → 28**（门槛 65，差 37）｜named 91 不变

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M33\PROGRESS.md`：前后直方图 / 2 行改动 / 3 行 rejected / S21 proved 前后 / coverage 前后 SHA。
完成后只回复：并入行数 / rejected 数 / `[已证]` 前后 / S21 proved 前后 / coverage 前后 SHA。