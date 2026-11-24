# LEAD_VERIFY_W84 · 失败重试框真机样本已取到（含正对照 + 双份复现）

> 记录人：Lead｜时间：2026-11-14 11:28｜卡：W84（**GLM-5.3-Flash**，真机 4 趟）
> 说明：W84 在写报告前仍在收尾（删沙箱），`REAL_DIR_PROOF.txt` 未落。**我据盘上 `TRIP_RESULT.json` 与截图签发**，真目录我另核（见 §5）。
> 本卡补的正是 `W79 UNKNOWNS U4` 记的 `[待运行验证]`：三态探针里唯一没有真机样本的那一态。

## 1 · 四趟实测（我逐趟读 `TRIP_RESULT.json`）

| 趟 | `outcome` | `kind` | frame | 控件集（`visible`） |
|---|---|---|---|---|
| `trip_df1` | `TASK_FAILED_DEFEAT_RESTART_DIALOG` | `defeat_restart_dialog` | **274** | `GUI:Blank`, **`GUI:Cancel`**, **`GUI:OK`** |
| `trip_df2` | `TASK_FAILED_DEFEAT_RESTART_DIALOG` | `defeat_restart_dialog` | **274** | 同上（重复趟） |
| `trip_wv1` | `VICTORY_RESULT_AND_TERMINATION_OK` | `victory_score_screen` | **165** | `GUI:Blank`, **`GUI:Continue`**, **`GUI:HeadsTaken`**, `GUI:ParTime`, `GUI:StandaloneScore`, `GUI:YourTime` |
| `trip_wv2` | `VICTORY_RESULT_AND_TERMINATION_OK` | `victory_score_screen` | **165** | 同上（重复趟） |

## 2 · 判据是可判别的（这是本卡的核心，不是"认出来了"）

**两个态的控件集完全不相交**：
- 失败框：**`GUI:OK` + `GUI:Cancel`**
- 胜利屏：**`GUI:Continue` + `GUI:HeadsTaken`**（+ `ParTime`/`StandaloneScore`/`YourTime`）

⇒ 探针不是靠"猜"或"看图像"，而是靠**控件 id 集合的差集**判定。**正对照（`wv1`/`wv2`）证明它不会把胜利屏误判成失败框** —— 这正是我在任务书里要求的必证项。

## 3 · 弹窗原文（我亲自读了裁剪图）

`out\screen_trip_df1_defeat_dialog_crop.png`（563×337，弹窗区域完整、未裁切掉正文）：
> **「確定重新執行此場任務嗎？」**
> 按钮：**「是」** / **「否」**

`[与我先前的目击一致]` 与 `W78 trip2` 目击到的是**同一个弹窗**（当时 W78 把它记成 `error dialog`，是误判；W83c 的探针已能正确分三态）。
`[它没有点 OK]` `ok=True` 且没有续跑第二局 ⇒ 遵守了"检测到失败框绝不点 OK/是"的红线。

## 4 · 双份复现（超出我的要求）

我只要求"各 1 趟"，它跑了 **各 2 趟**：
- 失败框 **274 / 274**（完全一致）
- 胜利屏 **165 / 165**（完全一致）

⇒ 两个终局都是**确定性的**，不是偶发捕获。

## 5 · 真目录与锁（我自己核的，不等它的 proof 文件）

`[本次实测]` `ra2youli` 4 个锚点全部与期望一致：
- `gamemd.exe` = **`73201cc021497c95…`**（**未打补丁**）
- `ddraw.dll` = `85e0f7d530dfda13…`
- `RA2MD.INI` = `c91c6a475b816fab…`
- `BATTLEMD.INI` = `7e40691a3480b1e5…`
`gamemd` 残留 **0**、锁 `owner=lead`。
`[仍缺]` 它的 `REAL_DIR_PROOF.txt`（`IDENTICAL_TREE` 全树自证）**尚未落盘** —— 我只核了 4 个锚点与无残留进程，**没有做 647 文件全树比对**。这一条我记为**未完成核对**，不当作已证。

## 6 · 一处 `ok` 字段的严格性（记录，非缺陷）

`trip_wv1`/`trip_wv2` 的 `ok=False`，但 `outcome=VICTORY_RESULT_AND_TERMINATION_OK`。根因：`terminal.end_of_game_byte = None`（收尾时读不到该字段）。
⇒ `ok` 的判定包含"`end_of_game_byte` 必须可读"，本趟读不到 ⇒ `ok=False`。**`outcome` 与 `kind` 是对的。**
`[与 W78 trip4 的 ok=False 是两个不同的点]` 那次是 `no_extra_start=false`（判定器单关形状 bug）；这次是"字段不可读的严格性"。
⇒ **共同教训：`ok` 字段不能单独当成功判据，必须看 `outcome` + 底层轨迹 + 控件集。**

## 7 · 签发

`[签发]` **三态探针的第三态（失败重试框）已有真机样本，且判据经正对照证明可判别**。
- 失败框：`kind=defeat_restart_dialog`、控件 `GUI:OK`+`GUI:Cancel`、frame **274**（2/2 一致）
- 胜利屏：`kind=victory_score_screen`、控件 `GUI:Continue`+`GUI:HeadsTaken`、frame **165**（2/2 一致）
- 超时态：此前 `W83c` 已有 2 样本（`NO_RESULT_WITHIN_150s`）

⇒ **三态全部有真机样本**，`W79 UNKNOWNS U4` 的 `[待运行验证]` **闭合**。
`[边界]` 1 个布局 / 1 镜像 / 4 趟；失败框文本为繁体中文；未测其它语言/分辨率下是否仍靠同组控件 id 判别（`[待运行验证]`）。

---

## 8 · 补：真目录**全树 647 文件哈希比对**（Lead 自己做，10:28 后）

`[背景]` W84 的 `REAL_DIR_PROOF.txt` **一直没落盘**。真机红线要求"每趟真机必须证明真目录零改动"，所以我**不拿"4 个锚点一致"充作全树自证**，自己补做。

`[方法]` 用 **W83c 的 `out\real_pre.json`**（647 条 `{rel, sha256}` 全树快照，那是 W83c 动手前的基线）作参照，对当前 `ra2youli` **逐文件重算 sha256**。

`[结果·本次实测]`
```
pre entries: 647
checked=647  missing=0  diffs=0
```
另：`Get-ChildItem -Recurse -File` 统计 = **647 文件 / 1,989,215,270 B**（与 `W76`/`W78`/`W79`/`W83c` 各卡的 PRE/POST 完全一致）。

`[签发]` **W84 的四趟真机未改动真目录任何一个字节** —— 这是**全树 647 文件逐个哈希**的结论，不是抽样。
`[一处诚实说明]` 用 W83c 的 PRE 快照作基线，成立的前提是**从 W83c 动手到现在真目录没有被别的东西改过**。这个前提我用 4 个锚点交叉核过（`gamemd.exe`/`ddraw.dll`/`RA2MD.INI`/`BATTLEMD.INI` 全部与期望值一致），且这一时间段内只有 W84 在跑真机。**若期间有第三方改动，本证明会漏报**——记为方法边界。

---

## 9 · ⚠ 我签错四处，据 W84 终版报告 + 我重核原始产物**订正**（11:34）

### 订正 1（重要）：弹窗文本**没有「要」字**
- **我写的（错）**：「確定**要**重新執行此場任務嗎？」
- **实际**：**「確定重新執行此場任務嗎？」**
- `[我重核 W84 的 `memory_hits` 原始记录]` utf16le 命中：`確定要重新執行此場任務嗎` = **0**、`要重新執行` = **0**、`重新執行此場任務` = **2**；而 `確定要重新` = 1 是**另一条字符串**（热键框）。
- `[我是怎么错的]` 我从**低分辨率裁剪图**（563×337）目视转写，把「確定」和「重新」之间**脑补了一个「要」**。
- `[这是本轮第 6 次、且是同一个病根]` 前五次：菜单封死（W58）、点击写入 -1（W75）、`+0x35A0` 机制（W76）、裁切截图读数（W78 U4）、结算屏字段读错位置（W79）。这次是**从截图转写文本**。
- `[规矩再加强一条]` **截图只能用来"确认识别形态"（有没有弹窗、弹窗大致长什么样），不能用来**逐字转写文本**。逐字文本必须来自**内存 RPM 命中**或**控件 text 字段**。**

### 订正 2：`REAL_DIR_PROOF.txt` **已落盘**（我曾写"未落盘"）
- 我在 §5 写"尚未落盘" —— 那是我检查时它还没写完；它后来写了。
- `[我重核]` `identical_tree=True`、`file_count=647`、`total_bytes=1,989,215,270`、`maplike_count=277`、`gamemd.exe` = `73201cc0…`（未打补丁）、`finalize restore: all rows byte_identical=True`。
- `[我自己补做的全树比对仍然有效且独立]` 我用 W83c 的 PRE 快照核了 647 条 `{rel,sha256}`：`checked=647 missing=0 diffs=0`。**两条独立路径得出同一结论**，比我原来那条"只有 4 个锚点"强。

### 订正 3：`trip_wv1/wv3` 的 `ok=False` 真因不是"探针严格性"
- **我写的（错）**：「`ok` 的判定包含 `end_of_game_byte` 必须可读，本趟读不到 ⇒ `ok=False`」——把成因归给**探针的字段严格性**。
- **实际（W84）**：**结算屏未点击时的随机自退竞态**（实测 ~12 s 与 ~55 s 两例）＋ 一处 `min_window_met` **记账 bug**（已修）。`end_of_game_byte=null` 只是**竞态的表现**，不是成因。
- `[我重核 trip_wv1]` `min_window_met=False`、`elapsed_s=54.78`（observe_sec=60）、`terminal.elapsed_s=0.17`、`scen_filename_traj=[]` ⇒ **终局块是空的**，与"游戏自行退出、没采到终局后状态"一致，**与"字段读不出"是两回事**。
- `[教训]` 我看到 `end_of_game_byte=null` 就**直接推断**成"探针要求该字段、读不到即 false"，**没有再往下问"为什么读不到"**。这正是"把结果当机制"的老病。

### 订正 4：判据可以更精确（W84 给了控件 id）
| 控件 | cls | ctrl_id | rect |
|---|---|---|---|
| 弹窗宿主 | `#32770` | — | [117, 91, 417, 308] |
| **`GUI:OK`** | Button | **1454** | [323, 259, 406, 276] |
| **`GUI:Cancel`** | Button | **2**（`IDCANCEL`） | [323, 281, 406, 298] |
| `GUI:Blank` | Static | 1456 | [157, 135, 377, 190] |

⇒ 判据可以写得更硬：**失败框 = 存在 `#32770` 宿主 + `Button#1454(GUI:OK)` + `Button#2(GUI:Cancel)`**；胜利屏 = `GUI:Continue` + `GUI:HeadsTaken`。**5 趟两集合零交叉**。
