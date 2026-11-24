# _sh_findings.md — S604 生成脚本穷搜回件（2026-11-09，脚本体穷搜员）

被核对象 SHA256 = 593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740，字节数 = 20271
字节数 = 20271
（被核对象 = lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md；上值为本轮 `python -I -X utf8` + hashlib 自算，与编排方指纹比对 MATCH=True，见 `_sh_fp_out.txt` [1] 段。编排方六件 6/6 MATCH。）

---

## 0 一句话结论

**S604 的生成脚本体已经找到**——不在文件系统上（「不在盘、从未落盘为 .py」依然成立），而在 **zcode CLI 会话数据库** `C:\Users\Administrator\.zcode\cli\db\db.sqlite` 的 `part` 表 rowid=512655（会话 sess_4fc16d67-74ac-4000-b9e9-9fd1257930aa，2026-11-06 06:52:40，台账落盘前 23 秒）的 Bash 工具调用 `input.command` 里，全文逐字保存。本轮已原样重跑：**15/15 行 + −114.820 汇总行 + 2.19 倍行与台账 §604 表逐位一致**；落盘命令 512667 的 `sec` 文本与台账 §604 实文 3022 字符逐字节 MATCH。**码形定谳达成**（见 §4）。

## 1 第一步：上轮四路搜索结论复核（实读 S604_SCRIPT_GAP.md 全件 173 行）

| 证据链 | 性质 | 覆盖面 | 本轮核验 |
|---|---|---|---|
| 路线一 文件名搜索（§3.1） | 【本轮实跑】 | lead/ + out/re_work 的 .py（11790 件）——**仅文件系统、仅这两棵树** | 命中清单 9 件指纹与 mtime 本轮自算复核（`_sh_fp_out.txt` [2]） |
| 路线二 内容搜索（§3.2） | 【本轮实跑】 | lead/ + .tmp 的 .py，5 针——**仅文件系统** | 同上 |
| 路线三 产物反查（§3.3） | **产物自述** | S604_GAP_RECHECK.md:101/:153、SLOW_WINDOW_LIMITS.md:91 三处引文 | 属「上游产物自述未落盘」，非独立搜索 |
| 路线四 台账实读（§3.4） | 实读+围栏扫描 | 台账 §604 区无代码块、:9751 自述内联、ROUND_SUBAGENT_LOG 零 S604 | 属「台账自身自述+缺席证明」，非对会话存档的搜索 |

判定：四条链在**文件系统**范围内互相独立、方向一致，结论「未以文件形式落盘」成立；但其覆盖面**均未触及 CLI 会话存档**——而 §4.6-1 自己已把「会话记录/终端历史」列为首要可疑来源。本轮正是补上了这一路。

## 2 第二步：本轮实跑搜索全表（每路带 dirsVisited 与耗时；脚本 `_sh_r678_search.py`，输出 `_sh_r678_out.txt`）

| 路 | 范围 | dirsVisited | filesSeen | 耗时 | 截断 | 结果 |
|---|---|---:|---:|---:|---|---|
| R6a 用户 TEMP | C:\Users\Administrator\AppData\Local\Temp | 2076 | 18115 | 39.1s | 否 | 79 命中全为 11-08/09 会话回声与 dsh 对象哈希噪声；**pyInWindow(11-04..08)=0** |
| R6b 系统 TEMP | C:\Windows\Temp | 1 | 7 | 0.01s | 否 | 0 |
| R6c 回收站 | C:\$Recycle.Bin | 3 | 3 | 0.00s | 否 | 0（近空） |
| R6d 仓库 .tmp | .tmp 深层 | 12 | 129 | 0.39s | 否 | 内容 0 命中；窗内 .py 48 件全列、无一相关 |
| R6e/f/g C:\Temp、D:\Temp、D:\tmp | 三处 | 828 | 4898 | 4.5s | 否 | 6 命中=cargo 哈希噪声 |
| R6h .zcode 遍历 | 全 .zcode depth5 | 2387 | 5453 | 90.5s | **是（预算）** | 51 命中=UUID 哈希噪声+10 月 rc4_gap_diff 日志+今日日志；**因此转定向 DB 挖掘（§3）** |
| R6i .agents | 全 .agents | 119 | 696 | 5.3s | 否 | 0 |
| R6j VSCode Backups | Code\Backups | 1 | 0 | 0.00s | 否 | 空 |
| R6k Recent .lnk | Recent | 3 | 907 | 0.25s | 否 | 1 哈希噪声；窗内 .lnk=0 |
| R8 编辑器残迹 | 仓库 depth5 | 2315 | 434850 | 29.6s | 否 | 21 件全为 .sav/.bak/.orig 游戏与 RE 旧件；无 .swp/*~；.vscode/.idea 不存在；Notepad++ 备份不存在 |
| R9 日志内嵌 Python | 仓库 depth8，.log/.txt/.out/.md/.json/.jsonl ≤5MB | 5288 | 64378 | 120.1s | **是（预算）** | 209 命中全部为「604」数字噪声（十六进制地址/字节数/行号），逐条摘句核实无脚本块 |
| R10 仓库名复核 | 仓库 depth8，名含 604/slowframe/gapdiff | 8522 | 533992 | 7.4s | 否 | 7588 命中=哈希/日期碰撞 + rc4_gap_diff_fix 时代（2026-10-12）旧件；**复现 R1/R2 全部 8 件，无遗漏件** |
| R7 git | stash list / .git/lost-found / fsck --full --dangling --no-reflogs（只读列举，未用会写盘的 --lost-found） | — | 213 悬空 blob+25 commit+20 tree | fsck+逐 blob 扫描 52.3s | 否 | stash 空；lost-found 不存在；**213 blob 逐个 cat-file 内容扫描：64 个含 measure_w/frame_edges（goal1 时代 10-18 旧工具结果），0 个含 空档差/快1/3/慢1/3/s604/gapdiff**；历史删除路径 grep 空 |
| DB 扫描 | db.sqlite（3.1GB）immutable=1 只读，全 99 对象、全 TEXT 列 7 针 | — | — | 139.6s | 否 | 10224 命中行；其中 CN 针（空档差/快1/3/慢1/3/最大空档）**仅 2 行** → 顺藤摸到 §3 |

（R9/R10 的全量清单与逐条摘句在 `_sh_r678_out.txt`；R7 全输出在 `_sh_r7_out.txt`、`_sh_r7_blobs_out.txt`。）

## 3 第三步：真伪鉴别与决定性发现

### 3.1 已知候选逐件判定（R1/R2 命中 9 件，指纹+mtime 见 `_sh_fp_out.txt` [2]）

| 候选 | 字节 | mtime | (a)完整脚本? | (b)11-06 撰写轮产物? | (c)能定谳码形? |
|---|---:|---|---|---|---|
| slowframe_r3/_r3_recompute_gapdiff.py | 12659 | 11-08 12:43 | 是（第三方复算） | 否（11-08） | 否——自身实现 edge+floor 正确口径，非原脚本 |
| slowframe_r3/_s604_delta_check.py | 2076 | 11-08 13:25 | 是（核对件） | 否 | 否 |
| slowframe_r3/_s604_fp_check.py | 2636 | 11-08 13:23 | 是（指纹件） | 否 | 否 |
| slowframe_r3/_verify_r3_gapdiff.py | 9811 | 11-08 13:05 | 是（第三重实现） | 否 | 否 |
| out/re_work/.../echgap_diff.py | 14176 | **2026-10-01** | 是（RE 时代旧件） | 否 | 否 |
| ledger_appendix/_la_draft3_s604_gapdiff.md | 7703 | 11-08 23:14 | 文档 | 否 | 否 |
| s604_attribution/_sa_ATTRIBUTION_S604.md | 17272 | 11-09 00:04 | 文档 | 否 | 否 |
| o1prime/_o1v_out_is_file | 39 | 11-09 04:00 | 探针残渣 | 否 | 否 |
| w2_samecause/outfile_as_outdir | 0 | 11-09 04:11 | 空件 | 否 | 否 |

**结论：9 件全非生成器，最老的也只到 2026-10-01。文件系统上确无 11-06 脚本残迹。**

### 3.2 决定性发现（本轮实跑提取）

会话库 `part` 表 CN 针仅 2 行 → 顺藤：
- `part.data rowid=512550`（同会话，11-06 06:4x）：两窗「帧内最大空档」诊断脚本（l1c/w0+t55k/w0）——同族探针，非生成器；
- 顺会话 sess_4fc16d67-74ac-4000-b9e9-9fd1257930aa（标题「每25分钟驱动逆向线」，1714 消息/5933 parts/**1008 个 Bash 调用**）按 `measure_w1`/`1/3` 模式提取 70 行 → 锁定时间线：

| rowid | 时间 | 内容 |
|---|---|---|
| 512645 | 11-06 06:52:26 | 帧时长方差（edge 口径 `fe[i][1]-fe[i-1][1]`）两窗探针 |
| 512650 | 11-06 06:52:33 | 两窗三分对照；输出「最慢1/3 p50=64.3 < 最快1/3 p50=154.8」= **台账 ：9752「分组标签写反」的现场** |
| **512655** | **11-06 06:52:40** | **★ §604 生成器本体**（"Within-window slow vs fast frame intra-gap comparison across all 15"），`input.command` 全文 1245 B |
| 512667 | 11-06 06:53:03 | §604 落盘命令（append），输出 `IS_PREFIX_EXT True LINES 9757` |
| 512670 | 11-06 06:53:11 | 节拍轮 49 锚账（自述两错与台账 §五一致） |

### 3.3 三重真实性验证（本轮实跑）

1. **重跑复现**：把 512655 的 command 原文存为 `_sh_gen512655_payload.py`，`python -I -X utf8` 在现盘语料上重跑 → 15/15 行、`-114.820` 汇总行、`2.19 倍`行与 2026-11-06 输出及台账 §604 表**逐位一致**（`_sh_gen512655_out.txt`）。语料未漂移与 R3 转验（GAP 件 §4.2）一致。
2. **落盘文本同源**：512667 `sec` 文本 vs 台账 §604 实文 = 3022 字符逐字节 **MATCH=True**（sha256=6a893fb8b9942b5bc7e23cee0bd07ae1bbe0f252d7403832f90793c628059788）。
3. **指纹链**：台账本体 SHA256 = 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede（759518 B，编排方指纹+本轮自算双验）；台账 mtime 2026-11-06 06:53:04 与 512667 落盘时刻 06:53:03 吻合。

## 4 码形定谳（回答任务第五步，且优于其预设）

原脚本关键行（512655 command 原文）：

```python
fe=d['frame_edges']
dur={fe[i][0]:(fe[i][1]-fe[i-1][1])*1000.0 for i in range(1,len(fe))}   # ★ 错误行
...
rec.append((fi,dur[fi],max(gaps)*1000.0))
...
rec.sort(key=lambda r:r[1]); k=len(rec)//3; fast=rec[:k]; slow=rec[-k:]
```

- **确切错误行 = `dur=` 字典推导行**：键取第 i 条 edge 的帧号 `fe[i][0]`，值却是 `fe[i][1]-fe[i-1][1]`（即 fe[i−1]→fe[i] 区间长 = **前一帧**的时长）。于是每行 `(maxgap(fi), dur(前一帧))`——按「时长」排序分三分时，**每个时长值挂接的是其时间后继帧的 maxgap**。
- 这正是上游 C8a（「时长-空档错一帧对齐 · 时间后继挂接」，75/75 数值等价）的**代码级实现**；不是 zip 截断、不是回绕 wrap、也不是 C13c bisect——三种候选码形全部**证伪**，原脚本走的是第四种形：**字典错位（off-by-one mis-keying）**。maxgap 本身的计算（`ts=sorted(ts); gaps=[ts[i+1]-ts[i]…]`）正确。
- 台账 ：9752「标签写反」= 512650 两窗版；:9753「x[4]-x[3] 得 −114.8」= 512655 汇总行原样留在输出里（`diffs=[x[4]-x[3]…]`），台账正文按逐窗 `sg-fg` 改正——两处自认错误与 DB 记录逐条对上。

**第五步各问的修订答案**：
- (a) 不再影响任何判断——「该不该改台账」与「怎么错的」现在都有据：§604 空档两列（30 格）是错位挂接的产物，正确算法复算值见 R3 [D]（+0.0065..+0.1080）；处置建议由编排方定。
- (b) 不再需要「等价类」表述——可直接写「码形已定谳：`dur` 字典错位一行，数值等价于 C8a（75/75）」。
- (c) 已执行：重跑原脚本逐位复现 = 最强验证；如需再验，跑 `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_gen512655_payload.py`（cwd=仓库根），比对 15 行与 `-114.820`/`2.19` 两汇总行。

## 5 完备性与未验项（不补造）

- 已覆盖：仓库全树 8522 目录名复核 + 434850 文件名（R8）+ 64378 文本件内容（R9）+ 用户/系统 TEMP、回收站、C:\Temp、D:\Temp、D:\tmp、.agents、VSCode Backups、Recent、.tmp 深层 + git 全历史路径/悬空对象 213 blob + 3.1GB 会话库全 TEXT 列。
- 预算截断如实申报：R6h（90s）、R9（120s）两路带 truncated=True；但两者均已由定向挖掘（CLI 日志逐件清点 + DB 全列扫描）所涵盖，未留死角于本任务目标。
- 不可能覆盖（如实申报）：已删除文件在磁盘上的未分配残块（本轮未做磁盘级 carving）；db.sqlite 的 WAL 增量（immutable=1 读主库快照；11-06 行已在主库并经台账交叉验证）；`db.sqlite.bak-2026-11-05T14-37-34`（2.7GB，mtime 2026-11-05 22:36，**早于撰写轮，未扫**，如需可另开一轮）；OneDrive 存在但未审计其云端内容；JetBrains LocalHistory 存在但为专有二进制未解析。
- 纪律：零真机、零采样代码、未 commit、未 push；全部被搜件只读（DB 用 immutable=1 零写入零锁文件）；写域仅 lead/s604_script_hunt_20261109/，产出 16 件均 _sh_ 前缀。

## 附：本轮关键实跑命令

1. `python -I -X utf8 D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109/_sh_fp_verify.py` → 6/6 MATCH + 绑定行
2. `python -I -X utf8 …\_sh_r678_search.py`（297.2s，R6/R8/R9/R10 全表）
3. R7：`git stash list`；`git fsck --full --dangling --no-reflogs --no-progress`；逐 blob `git cat-file` 扫描（`_sh_r7_blobs.py`）
4. `grep -c` 针计数 ×3 份 CLI 日志；字节偏移 `grep -abo` + `tail -c +N | head -c`
5. `python -I -X utf8 …\_sh_dbscan.py`（immutable=1，全 TEXT 列，139.6s）→ CN 针 heredoc 提取（16.7s）→ 会话 512640-512960 时间线 → 512655/512667/512670 全文提取
6. `python -I -X utf8 …\_sh_gen512655_payload.py` → 15/15 逐位复现
7. 台账 §604 vs `sec` 文本逐字节比对 → MATCH=True（3022 字符）
