# SINGLE_WRITER_TAKEOVER — M53 接管 COVERAGE 独占写权

## 1. 接管声明（Lead 指定）

- 卡号 **M53**，Lead 已确认本仓曾有第二个会话并发写 `COVERAGE/PANEL.md`（2026-11-19 22:11–22:17 实测，见 RULING_R15 §2 事实更正 3）。
- 从本卡起，**M53 是 `COVERAGE/` 下 `PANEL.md` 与 `coverage.tsv` 的唯一写者**；任何其它卡不得再改这两个文件。
- 本卡写域：`COVERAGE/coverage.tsv`、`COVERAGE/PANEL.md`、`M53/`、`_hygiene/` 下 M53 备份。其余只读；未改 `CONFLICTS.tsv`、`PENDING_CORRECTIONS.tsv`、台账、`R14_COMMON.md`、`STATUS_BOARD.md`、`ra2youli/`；未 git commit；未建 venv、未 pip install。

## 2. 接管时基线（改前，untracked 文件，无 git 历史可追）

| 文件 | bytes | 行数(LF) | sha256 | mtime(本地) |
|---|---:|---:|---|---|
| `coverage.tsv` | 3,730,020 | 18,498 | `b4c998c06f91e9b23c0a34ea459a308eee8212671d761b0189b7135dfbcbe94c` | 2026-11-19 22:04:36.637 |
| `PANEL.md` | 102,125 | 482 | `869e7daf4ea33936f3a8fc73566f069ee28c9370718408bbf831e796169f17a2` | 2026-11-19 22:19:02.075 |

备份：`_hygiene/coverage.M53.bak`、`_hygiene/PANEL.M53.bak`（sha 与上面改前逐一相等）。

## 3. 本卡改后现态（交接基线）

| 文件 | bytes | 行数(LF) | sha256 | mtime(本地) |
|---|---:|---:|---|---|
| `coverage.tsv` | 3,730,077 | 18,498 | `6734029ed9e68355d3f2a896fe6533547d2abf84eafc0cfcb04953b9c0df0920` | 2026-11-19 22:23:09.329 |
| `PANEL.md` | 105,815 | 499 | `93107ea25dbc8381402fb7f4d7fc8e07714f4aaa537be7338fdc667053538267` | 2026-11-19 22:23:50.677 |

说明：行数口径为 LF 计数；两文件均无 BOM、`coverage.tsv` 末行无换行（Get-Content 会报 18,499）、`PANEL.md` 末行有换行。接管期间每次写入前 guard 均比对 baseline sha+mtime 全等，**无第三方写入**。

## 4. 后续卡必须遵守的规则（强制）

1. **读写前各记一次 mtime + sha256**：任何卡在读这两个文件前、写这两个文件前，都必须各记一次 `mtime` 与 `sha256`（可用 `Get-Item.LastWriteTime` + `Get-FileHash -Algorithm SHA256`）。这是本仓 untracked 文件识别并发写入的唯一手段。
2. **写前 guard 必须与读前基线相等**：写前比对 sha256 与 mtime，若与上一步记录不一致 ⇒ **立即停手报告**，不得覆盖，等 Lead 裁决。
3. **改后再记一次**：写入完成后再记 bytes / 行数(LF) / sha256 / mtime，写进该卡 PROGRESS，与本文件交接基线比对。
4. **先备份到 `_hygiene/`**：改动前把原文件复制到 `_hygiene/<file>.M<卡号>.bak`，并核对备份 sha256 = 改前 sha256。
5. **写完同步更新本交接基线**：若你不是 M53 且获 Lead 明确授权接棒写权，须在本文件追加新一节「交接记录」（卡号、时间、改前/改后 sha256），并知会 Lead；未获授权不得改这两个文件。
6. **不得绕过**：禁止以 git revert / 整文件重写等方式掩盖第三方写入；一切差异以 mtime + sha256 记录为证。
