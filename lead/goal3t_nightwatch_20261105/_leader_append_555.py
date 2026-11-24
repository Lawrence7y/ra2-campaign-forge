# -*- coding: utf-8 -*-
"""Append §555: exit census intake (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7555"

head = subprocess.run(
    ["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
    cwd=REPO, capture_output=True).stdout.replace(b"\r\n", b"\n")
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.startswith(head):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = """
## §555 · 退场普查（37 个 archive 目录）：零趟游戏崩溃，四趟是 harness 脚本缺陷（2026-11-05）

> **本节的地位**：`RULING_D16` 第 7 节所列缺口「23 个缺 `w0` 目录」的邻域普查。
> run `dwfrun-49101bdc`，模型 `magpie/work/cn:hy4free$high`（备选 1），
> 独立复核判 **NEEDS_REVISION**，**8 条异议全部接受并改判**。
> 明细：`lead/goal3t_nightwatch_20261105/EXIT_CENSUS_77a0d667/01_exit_census.md`（245 行）。

### 一、★ 最重要的结论：**37 个 archive 目录，零趟「游戏崩溃」**

107 份 `except_post_*.txt` **全部同哈希 `6694b75e…`**（我亲验，`distinct hashes = 1`），
内容统一为 `EXCEPTION_SINGLE_STEP at 007CFC9F`，**属历史基线残件，不是任何一趟的崩溃证据**。

⇒ **本节范围内没有一条证据支持「游戏崩溃」**。
7 份 `error.txt` 里 3 份非空，**全部是 harness 自身的 Python 异常**，与游戏无关。

**这直接关系到目标②**：archive 这一批趟的失败**没有一次能归因到游戏引擎**。

### 二、`final_exit` 分布（我亲验，与回件逐项一致）

| `final_exit` | 趟数 | 目录 |
|---|---:|---|
| **0** | **14** | T5、T8、T9、T12、T13、T14、T15B、T16、T18、T20、T21、T31、T32、T33 |
| **1** | 1 | T10（`NameError: name 'user32' is not defined` @ `qc151_trip.py:3356`） |
| **19** | 3 | T11、T22、T23 |
| **22** | 2 | T6、T7 |
| **63** | 1 | T19 |
| **缺**（无 `qc151_run_log.json`） | **16** | T15_ABORTED、T17、T34–T45、T47、T49_u0800 |

**合计 14+1+3+2+1+16 = 37。**

### 三、★ 同一退出码**不**同一根因（复核员改判了调查员的初判）

**`19` 的三趟，调查员初判「三个不同根因」，复核员判「证据不足」，最终改判**：

| 趟 | 失败阶段 | 实测 | 改判后 |
|---|---|---|---|
| `T11` | **window** | `stage_timeout:window`，30.297s | **harness 脚本缺陷**（`C_DEFECT.md:128-133`：deadline 与阶段硬停上限耦合） |
| `T22` | **nav_menu** | 45.625s 超时，`NAV.verify_ok=false` | **harness 脚本缺陷** |
| `T23` | **nav_menu** | 44.672s 超时，**`NAV.verify_ok=true`** | **harness 脚本缺陷** |

**改判依据**：`T22`/`T23` 的 `red_centers` 与 `signature_got_nav_menu` **完全相同**（`[61,220,262,304,556]`），
变的是 harness 的 `NAV.wait_screen_nav_menu_post.want`（`T22=[72,…]`→fail，`T23=[220,…]`→ok）；
两趟 console 行号 `main 3967→3972`、`_main_wrapper 4185→4190` **表明两趟之间脚本已改**。
⇒ **差异在 harness 配置，不在游戏**。调查员初判的「游戏菜单画面不符⇒环境问题」**撤回**。

**`22` 的两趟**（`T6`/`T7`）：`wait_returncode=3221225781`（`0xC0000135 STATUS_DLL_NOT_FOUND`）、
`main_window_found=false` ⇒ 载体缺 `ddraw.dll`，**环境问题，同因**，但是两次独立发射。

**`63` 一趟**（`T19`）：`EnumProcessModulesEx: cbNeeded=80 > allocated=72`（模块表被截断）⇒ **无法判定**。
（调查员初判「环境瞬态 err=299」是**误引**，`err=299` 属 `l3_1101v4a`，已由调查员自查撤回。）

### 四、改判后的性质分布（复核员重算）

```
harness 脚本缺陷   5      ← T10、T11、T22、T23、T5
环境问题           2      ← T6、T7
人为中止           1      ← T15_ABORTED（ABORTED_NOTE.md 明写「被宿主取消信号打断」）
无法判定          29
游戏崩溃           0      ← ★ 一条也没有
```

### 五、`final_exit=0` 但带 `error.txt` 的仅 `T5`，且**不算异常退出**

`archive_T5/error.txt`（`ctypes.ArgumentError`，mtime `08:14:58`）
比同目录 `qc151_run_log.json`（`11:13:34`，`final_exit=0`）**早约 3 小时**，
且该趟 `except_set_diff.json` 记 `new_exception_count=0`
⇒ **是更早一次失败尝试的残留件，不是本次运行的异常**。
**按「同目录=同一次事件」读会得出反结论**——这是本线一个典型陷阱。

### 六、复核员推翻调查员的 8 条（全部成立）

| # | 调查员原写 | 复核员实测 |
|---|---|---|
| 1 | 13 个目录无 `except_post` | **18 个**（19 有 / 18 无） |
| 2 | 「无法判定」26 个 | **29 个**（改判后） |
| 3 | 24 个目录名台账零命中 | **21 个**（16 个有命中） |
| 4 | `T32` console 0 字节 | **该目录根本没有 console 文件**，应写「缺」 |
| 5 | 43 个目录 / 104 份 JSON（自相矛盾） | **44 个目录**（43 子目录 101 份 + 根 3 份） |
| 6 | 14 趟 run log 缺但 measure 在场 | **12 趟**有 measure，`T35`/`T37` **全缺** |
| 7 | `T22`/`T23` 是「环境问题」、三个不同根因 | **均为 harness 脚本缺陷**，撤回「三个不同根因」 |
| 8 | 旁证行号多处错 | 逐条改正 |

⇒ **调查员一次过写下 8 处数字/归因错误，全部由复核阶段抓出。**
这正是「至少一道独立核验」这条纪律的价值所在。

### 七、对台账的连带订正

1. **台账 §0 附近（日志 §43）称「`archive_T*` 命名止于 T23」——错**。
   盘面 **37 个**，`T31`–`T49_u0800` 共 17 个在 T23 之后。以 37 为准。
2. **16 个 archive 缺 `qc151_run_log.json`，台账从未登记这个缺口**——
   而台账大量引用它们的 `measure_w*.json` 数值。**现已登记。**
3. **§547 的「全 archive_T* 14 趟」范围表述不成立**：盘面 37 个、14 份有 `w0`、23 个缺。
   `RULING_D16:35` 已裁须改为「**14 份可核 `w0` 中唯一首拍为零**」。**本节据此订正。**
4. **「107/107 同签名」在 archive 范围内需补边界**：37 个 archive 内只有 **24 份**，
   其余 83 份散在根层与非 archive 子目录。**13 个 archive 是「缺件」不是「有例外签名」。**

### 八、诚实账

1. **我亲验了 3 项**：37 个目录数、`final_exit` 直方图（逐值逐目录全对）、
   107 份 `except_post` 单一哈希 `6694b75e…`。
   其余（归因判定、8 条改判、`19` 三趟的脚本差异）**采信回件与复核员**，我未逐份重读 console。
2. **调查员初版 8 处错误全部由复核员抓出，我没抓到任何一条**——
   我在派发时给的是「问题 B 最容易犯同码=同因」，恰恰是它错了的地方，
   但**我没有在回件后独立核验归因**，只核了计数。
3. **「游戏崩溃 0 趟」这条结论我未独立验证**（需要逐趟读 console 与字段）。
   我验证的是**它的必要条件**（107 份 except 单一哈希）。
4. 本轮**零真机**、**零母本改动**、**未 commit**。
5. **未查**：23 个缺 `w0` 目录的**建筑数**（原定缺口，本轮查的是退场不是负载）。

### 九、证据入口

- 明细：`lead/goal3t_nightwatch_20261105/EXIT_CENSUS_77a0d667/01_exit_census.md`（245 行）+ `02_verify.md`
- 我亲验：37 目录 `final_exit` 直方图；`except_post` 107 份 `distinct hashes = 1`
- 旁证：`book_T12_20261017/C_DEFECT.md:24-33,111,128-137,173-179`、
  `L1_BASELINE_TRIPS_20261021.md:39`、`TRIP_ID_RECONCILIATION_20261018.md:4`
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION.encode("utf-8")))
