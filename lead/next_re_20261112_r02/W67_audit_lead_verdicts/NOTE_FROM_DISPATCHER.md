# 外派方提示（zcode-runner 写，非任务书）

> 这不是任务的一部分，是我（派你跑这张卡的人）在旁路独立核证时发现的东西，请**纳入考虑**。

## 1 · `_w67_verify1_out.txt` 里有一处**脚本 bug**，W44 的 mtime 列不可信

我重跑了 `w67_verify1.py`，并独立用两套 API 复算，确认：

- 磁盘真值（`os.stat` 与 PowerShell `LastWriteTime` 一致）：
  - `crop_w44_campaign_menu_content3x.png` → `2026-11-13 19:49:21`
  - `crop_w44_ctrl_campaign_menu_content3x.png` → `2026-11-13 19:51:29`
- 但 `_w67_verify1_out.txt` 这两行都写 `mtime=2026-11-13 19:54:36`

**根因**（`w67_verify1.py` 第 130–135 行）：
第一个 for 循环结束后 `fp` 仍指向上一次迭代的值（Python 循环变量外泄），第二个循环 `for fn, h, mt in s256:` **只重绑了 `fn/h/mt`，没重绑 `fp`**，于是 `mtime(fp)` 恒等于目录下排序后**最后一个文件**的 mtime —— 那个文件是 `uninstall.ndjson`，它的 mtime 正好是 `19:54:36`。

**结论**：
- 该脚本 **sha256 列、size 列可信**（都在循环内正确计算）
- 该脚本 **W44 段的 mtime 列全部无效**
- 同理，任何「`mtime(fp)` 出现在第二个循环里、且 `fp` 未重绑」的地方都要怀疑。**你引用它之前请自己复算 mtime。**

## 2 · 我自己已独立核过的值（你可以直接引用，标注来源为「外派方复算」）

用 python 直读 `ra2bench\gamemd.exe`（4,825,360 B，sha256 前缀 `73201cc021497c95`）：

| 项 | 实测 | 与签发件/脚本对比 |
|---|---|---|
| LE32 `0xA8F7AD` | count=1 @ `0x12f00c` | MATCH |
| `A0 AD F7 A8 00` | count=1 @ `0x12f00b` | MATCH（VA 0x52F00B 的 A0 read gate） |
| LE32 `0xA8F7AC` | count=1 @ `0x2be030` | MATCH |
| `BATTLE.INI`（精确） | count=**0** | MATCH（W64b 声称 0） |
| `BATTLEMD.INI`（精确） | count=1 @ `0x426198` | MATCH（VA 0x426198） |
| `BATTLEMD`（前缀） | count=2 @ `0x426198`, `0x4261a8` | MATCH（VA 0x4261A8） |
| VA `0x5CF04F`→FOFF `0x1cf04f` | `83 ff 64 7f 1d` = `cmp edi,0x64; jg` | MATCH |
| VA `0x5CF367`→FOFF `0x1cf367` | `83 fd 64 7f` = `cmp ebp,0x64; jg` | MATCH |
| VA `0x5AE0B8`→FOFF `0x1ae0b8` | `66 89 83 a0 35 00 00` = `mov word [ebx+0x35A0],ax` | MATCH |
| VA `0x6859BF`→FOFF `0x2859bf` | `8a 81 ac 34 00 00` = `mov al,[ecx+0x34AC]` | MATCH |
| `BATTLEMD.INI` pristine | 2733 B, sha `7e40691a…` | MATCH |
| `.bak` | 241 B, sha `9f804531…` | MATCH |
| W45 八份 SAV 尺寸 | 全部与声称值一致 | MATCH |
| W44 两图 sha | 均 `0c7fb5fb…`（逐字节相同） | MATCH（但 mtime 见 §1） |

**没核的**：`0x6859C7 je +0x47`、`0x685C4E/0x685C54`、`0x68A11F`、邻域扫描 36、`all1/sov1/tut1` 计数。这些**仍是 [未核]**，别当我核过了。

## 3 · 环境事实（与审计无关，但你写 UNKNOWNS 时可能用到）

- `next_re_20261112_r02\.game_instance.lock` 确实存在，内容显示 **W70 trip 已于 00:38:39 正常结束**（`ok=True, outcome=FULL_CHAIN_M1_M2_M3`，residual=0，owner 已归还 lead）。**你没有碰它，正确。**
- 当前**没有** `gamemd` 进程在跑。
- 我在 00:35:07 做过 14 个输入文件的 sha256 基线，存放在 `_baseline_inputs.txt`。**你的 STEP1 结论（14/14 MATCH）我已复核，成立。**

## 4 · 一句提醒

Lead 已明确：**不要再花时间重跑数值核验**。数值这块我和上一实例已经做得够了。把时间留给**通读原文 + 找 A/B/C 叙述层问题**。
