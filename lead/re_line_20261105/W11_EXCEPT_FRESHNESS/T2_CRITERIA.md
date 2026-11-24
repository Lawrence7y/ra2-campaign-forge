# T2 · 新鲜性判定的可实施判据（W11 · D-22 裁决（A）执行步）

```
被核对象 = qc151_trip.py + 相关 harness 文件
qc151_trip.py SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508，行数 = 7291
  （本人实算：sha256sum + wc -c -l，2026-11-06T03:11:35+08:00，路径
   out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py）
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（目标镜像，本任务不反汇编它；
  ★ 本人另行实算复验一致：sha256sum ra2youli/gamemd.exe → 73201cc0…f67476，2026-11-06）
回件时刻 = 2026-11-06T03:20+08:00
```

**范围**：本件只做 T2（判据设计）。零真机、零注入、未读活进程内存；
未修改 `qc151_trip.py` 与 `out/re_work/` 下任何文件（写域仅
`lead/re_line_20261105/W11_EXCEPT_FRESHNESS/`）。T1 的三分类（源码明确设计/实现缺陷/证据不足）
归 T1 件，本件不越界下判，只在第 1 节引用其代码事实底座。

---

## 0 · 结论速览

| 方案 | 判据 | 可行性 | 代价 | 误判风险 | 结论 |
|---|---|---|---|---|---|
| A · mtime 比较 | `src.stat().st_mtime >= t_run_start` | 可行但**naive 版不可用**；须加固为「跑后 mtime ≠ 跑前实测 mtime」 | 极低（stat 两次） | 复制保留 mtime（探针[2]实测成立）、时钟回拨（原理项）、同 tick 多次写（探针[6]实测有碰撞）、utime 主动伪造（探针[3]）、mtime=最后写时刻≠异常发生时刻 | **只作旁证** |
| B · 跑前基线哈希 | 跑前 `sha256(except.txt)`，跑后不同才算本趟被写 | **高**——跑前/跑后哈希工件已在盘上，纯离线比对，零 harness 改动 | 近乎零（比对两份已有 JSON） | ①「同内容重写」假阴性（探针[4]实测：sha 相同、mtime 已变）；②内容变化 ≠ 新异常——`:677` 明写游戏自身会重写该文件，假阳性当 crash | **主判据（回答 F）**，但必须与 E（新异常判定）分开 |
| C · 跑前改名移走 | 跑前移走，跑后出现即为新 | 技术可行；**政策冲突 U-5**（`:6390-6408` 被动基线是外部裁定产物） | 中（先读后移 + 裁定 + 行为扰动验证） | 游戏/loader 对 except.txt 缺席的行为反应**未验**（零真机不能验） | **opt-in 硬证模式**，需新裁定，不作默认 |
| D · 游戏侧保证 | 依赖游戏只在崩溃时写 | **不可行** | – | 仓内证据反向：`:677`「游戏自身会重写该文件」；「只在崩溃时写」离线不可验 | **否决**，只作文案注释 |

**推荐判据组合**：**B（基线哈希，主）+ A 加固版（mtime 差分，旁证）**，C 备选、D 否决。
判定输出 **F（freshness，本趟是否被写过）与 E（new exception，集合差）两个独立结论**，
理由与六分支决策表见 §6。

---

## 1 · 判据设计的代码事实底座（全部 file:line 本人本轮亲读）

1. **生成点** `copy_post_except_evidence` `qc151_trip.py:4561-4599`：`:4574-4578` 只判
   `src.exists()`；`:4579` `read_bytes` 原样复制；副本名 `except_post_{datetime.now()…}.txt`
   `:4581`；副本信息含 `size/sha256` `:4583-4585`。**无任何新鲜性判断。**
2. **载体每趟新建、复制方式不保留 mtime**：`:4925-4927` `carrier_dir = trip_root /
   f"c_{stamp}_{os.getpid()}"`，`os.mkdir` 排他；`:4958` `d.write_bytes(s.read_bytes())`；
   `:4973` receipt 自记 `copy_method="read_bytes→write_bytes（真实字节，非链接/硬链接）"`。
   ⇒ trip 自建载体里 `except.txt` 的 mtime = **harness 复制时刻**（探针[1]实测该方式不保留源 mtime）。
3. **跑前被动基线（U-5）**：`:6390-6409`，`:6394-6397` 读现有内容作 `pre_except_txt`；
   `:6398-6400` `baseline_source=passive_read`；`:6406-6408` `reset_verdict=SKIPPED_U5`。
   ⇒ **harness 对载体 except.txt 的任何主动写/移，都是对 U-5 立场的政策回退**（C 方案的约束）。
4. **跑前备份（pre 哈希已有！）**：`backup_carrier` `:4447-4462`，`:4458`
   `dst.write_bytes(src.read_bytes())`，`:4461` `rec.add("RESTORE","backup_sha256:{name}",…)`。
   调用点 `:6387`（launch 之前）。⇒ **跑前 sha256 已落在 `qc151_fields.json`**。
5. **launch 锚点**：`launch_direct` `:1072ff`，Popen 后 `:1107` 取
   `ct = get_process_creation_time(proc.pid)`、`:1109` 记
   `LAUNCH.launch_pid_creation_time`；该函数 `:766-786` 返回
   **Windows FILETIME 100-ns 计数**（内核记录的进程创建时刻，UTC）。
   ⇒ 精确 launch 时刻锚点**已存在**（精度 100ns，远高于 `now_iso()` 的秒级，`:432-434`）。
6. **finalize 步序**：`:6042-6052` `run_guarded_steps`：`except_evidence_copy_and_verify`(第1) →
   `except_set_diff`(第3) → `restore_carrier`(第6)。`_except_diff` `:5974-5985` 的
   `post_txt` **直接重读载体文件**（`:5978`），先于 restore ⇒ 读到的是跑后原件。
7. **集合差口径**：`except_set_diff` `:672-708`，Counter 多重集差 `:685`；
   ★★ `:675-677` docstring 明令：「**不得**用 `sha` 变化判 crash（★ 游戏自身会重写该文件）」。
8. **:4420 的 mtime**：属 `_render_log_probe` `:4413-4425`，只列 `ra2render*.log` 的
   size/mtime 作探针元数据，**不是新鲜性检查**。全文件 `grep -n mtime` 仅 `:4420/:4422` 两处。
9. **跑后快照**：`carrier_post_state.json` `:4591-4596`（五件 post size+sha256）；
   `restore_carrier` `:4488-4498` 另记 `current_sha256:{name}`（post）与逐件 PASS/FAIL。
   ★ restore 只比 sha+size（`:4489`），**不比 mtime**。
10. **真实趟实测（l1b_20261021，只读）**：
    `carrier_creation_receipt.json`：`files["except.txt"] = {src: …\_src_L1_sf8_20261020\except.txt,
    sha256_src = sha256_dst = 6694b75e…aac251, size: 26405}`，`created_at = 2026-10-21T18:42:42+08:00`；
    `carrier_post_state.json`：`except.txt sha256 = 6694b75e…`（与 pre 相同）；
    `except_set_diff.json`：`pre=1046 post=1046 new_exception_count=0`；
    `qc151_fields.json` 同时含 `RESTORE.backup_sha256:except.txt` 与 `RESTORE.current_sha256:except.txt`。
    ⇒ **「原样遗留」链路在真实趟坐实**：carriers 的 except.txt 是母本目录遗留件逐字节复制进来的，
    全程内容未变。载体目录 `ct/` 已被删除链清理（ls 实证不存在）。

---

## 2 · 概念澄清：三个不能混的问题

- **F（freshness）**：`except.txt` 在本趟运行窗口内**是否被写过**（本任务 T2 的目标）。
- **E（new exception）**：集合差里是否出现新 `Exception occurred at` 行（`:679` 已有口径）。
- **C（cause）**：本趟的写是否由崩溃引起。

★ `:677` 禁止的是「用 sha 变化判 **crash**」，因为游戏自身会重写该文件；
它**不禁止**用 sha/mtime 回答 F。把 F 的结论直接当 C/E 用，正是当前数据的误读风险：
59 份 `new_exception_count=0` 只证明「内容与跑前基线集合相同」（E），不证明「文件本趟没被动过」（F）。

## 3 · 四方案逐条评估

### 方案 A · mtime 比较

- **naive 判据** `st_mtime >= t_run_start`：**不可用**。三个原因：
  ① `t_run_start` 无精确锚（`now_iso()` 秒级精度，`:432-434`）；
  ② trip 自建载体里 except.txt 的 mtime 起点 = harness 复制时刻（§1.2），
  「复制后未被动过」与「本趟被写」都要以复制时刻为界而不是以 launch 时刻为界；
  ③ mtime 单值携带不了「跑前状态」信息，无法区分「遗留件」与「本趟写的时间戳恰好一致」。
- **加固判据（推荐）**：跑前（backup_carrier 时刻 `:6387`）实测并记录
  `mtime_pre = src.stat().st_mtime`；跑后（evidence copy 时刻 `:4574`）实测 `mtime_post`。
  `mtime_post != mtime_pre` ⇒ 本趟被写过（存在写入事件）；相等 ⇒ 本趟未被写（弱证据，见下）。
  若要锚到墙钟，用 `launch_pid_creation_time`（FILETIME 100ns，§1.5）换算 epoch
  （`ft/1e7 - 11644473600`），**不要**用 `datetime.now()` 字符串比 mtime。
- **mtime 不可靠场景清单**（★ TASK 点名三项全含；[n]=探针实测，见
  `_w11_t2_mtime_probe_out.txt`；「原理」= 未实测、按文件系统语义处理）：
  1. **复制保留 mtime** [2 实测成立]：`shutil.copy2`/`copytree`/robocopy/资源管理器复制/zip 解包
     都保留源 mtime。harness 现行 `write_bytes` 复制不保留 [1 实测]，但**交接（handover）路径
     的复制方式不由本脚本控制**——若交接用 copy2 类工具，except.txt 会带着旧 mtime 进场，
     naive 版直接误判「旧文件」。⇒ 判据必须用「跑前实测 mtime」自建基线，不信任进场 mtime。
  2. **时钟回拨**（原理项，需改系统时间权限，探针不实测 [7]）：跑前锚点测量后、游戏写入前，
     系统时钟被回拨（手动改钟/NTP 大步校正/VM 恢复/RTC 漂移）⇒ 写入时刻的 mtime <
     锚点 ⇒ 「mtime 未变/变旧」假阴性。NTFS 存 UTC 不受时区/DST 影响，但**改钟本身**无解。
     缓解：锚点同时记 `time.time()` 浮点与 `now_iso()`，事后审计
     `mtime_post < mtime_pre` 且 sha 同的组合即标记「疑似回拨，置信降级」。
  3. **同一 tick 多次写** [6 实测]：NTFS 名义 100ns 粒度，但探针连写 200 次只得到
     **122 个不同 mtime**（约 39% 碰撞）——同 tick 多次写**部分不可分辨**，只能证明
     「至少写过一次」，数不出写了几次。FAT/exFAT 粒度 2s（本盘 D:\ 为 NTFS [0 实测]，
     但外接/交接介质可能是 FAT 系——未验）。
  4. **mtime 可被主动伪造** [3 实测]：`os.utime` 可把刚写的文件标成任何时刻。
     游戏无此动机，但任何中间工具（清理脚本、同步盘）都可能 touch。
  5. **mtime = 最后写时刻 ≠ 异常发生时刻**（D-22 事实核证员指出的点）：长跑崩溃在 T、
     游戏在 T+k 退出时才 flush，mtime=T+k；多次异常只留最后一次的 mtime；
     追加式写入时 mtime 只反映末次追加。⇒ mtime 不能用来回答「异常发生在何时」，
     只能回答「跑前测量之后有没有写入事件」。
  6. **Windows 文件时间缓存**（原理项，未逐字核 MSDN）：NTFS 对已打开句柄的
     last-write 更新有短延迟，句柄关闭/进程终止时才落定。本判据只在游戏进程退出后读，
     实际风险低；若未来有人在运行中读，须重估。
- **结论**：可行、代价极低（两次 stat），但**单独使用不成立**——它是 B 的旁证
  （专补 B 的同内容重写盲区），不是独立判据。

### 方案 B · 跑前基线哈希

- **判据**：跑前（`backup_carrier` `:6387` 或 receipt/handover 校验时）算
  `sha256(except.txt)` + `size` + `mtime`；跑后（`copy_post_except_evidence` `:4580` 已算
  post sha）比对。不同 ⇒ 本趟被写过（F=new_write）。
- **可行性：高；代价：近乎零。** 跑前/跑后工件**都已在盘上**（§1.4/§1.9/§1.10 实测）：
  - 跑前：`receipt.files["except.txt"].sha256_dst`（trip 自建模式）或交接证明
    `files{name:{sha256}}`（`assess_carrier_ownership` `:5001-5003`）；以及
    `qc151_fields.json` 的 `RESTORE.backup_sha256:except.txt`。
  - 跑后：`carrier_post_state.json`、`RESTORE.current_sha256:except.txt`、
    `except_post_*.txt` 伴随的 `evidence_copy.sha256`。
  ⇒ 对**历史 59 趟**也能离线补算 F，无需任何 harness 改动。
- **误判风险（★ 必须说清的部分）**：
  1. **同内容重写 → 假阴性**（TASK 点名）：游戏确实重写了文件但内容与基线逐字节相同
     （同一次崩溃特征重复写、或 game 周期性重写同内容）⇒ sha 相同 ⇒ 误判「本趟没写过」。
     探针[4]实测该盲区成立。**缓解 = 叠加 A 加固版**：sha 同但 mtime 变 ⇒
     判「本趟被写、内容恰好相同」（rewritten_same_content），置信中，不再漏。
  2. **内容变化 ≠ 新异常 → 假阳性当 crash**：`:677` 明写游戏自身会重写该文件。
     sha 变化只回答 F（被写过）；把它当 E/C（新异常/崩溃）用违反 harness 自己的口径。
  3. **基线时机错误**：基线必须取在「载体定稿之后、launch 之前」
     （`:6387` backup 或 receipt `:4966-4983`）；若取在交接验收前，交接搬运本身的
     写入会被算进「本趟」。
  4. **编码口径**：`:6396` `read_text(errors="replace")` 会把坏字节替换掉，
     文本比对与字节比对可能不一致；B 方案一律用 `read_bytes` 的 sha（`:4580` 现行即字节级）。
- **结论**：**主判据**。回答 F 信号强、可离线追溯历史趟；短板（同内容重写）由 A 旁证补。

### 方案 C · 跑前改名/移走

- **判据**：跑前把 `except.txt` 移出载体（先 `read_bytes` 留 pre 内容进证据域），
  跑后该文件**在场**即为「本趟新产生」——缺席→在场是不可伪造的存在性证据，
  天然免疫「同内容重写」盲区与 mtime 伪造。
- **可行性**：技术上一次 `os.replace` 即可；**政策上冲突**：`:6390-6408` 的被动基线是
  外部裁定 V5 §6.1.1 U-5 的产物（移除 harness 对载体 except.txt 的覆盖写）；
  跑前移走 = 对同一文件的又一次主动干预，**需要新裁定**，不是技术问题。
- **代价**：中。①先读后移（保住 pre 内容与 except_set_diff 的可比性）；
  ②记账面核对过：`restore_carrier` 对无备份件记 `restore_skipped` 不判失败
  （`:4477-4479`），trip 自建载体最后整体删除（`carrier_delete_chain`），爆炸半径有限；
  ③历史可比性断裂：59 趟口径是「pre 在场 + 集合差」，C 之后 pre 恒缺失，
  新旧趟数据不可同表比较。
- **误判风险**：①**行为扰动未验**——游戏/loader 对 except.txt 在启动时缺席的反应未知
  （会不会照常写？会不会因缺文件改变行为？），零真机约束下不可验，只能标「未验」；
  ②若游戏对已存在文件采取「追加」而对不存在文件「新建」，C 反而改变数据形态；
  ③移走动作本身若失败（占用/权限），必须显式 error 而非静默继续。
- **结论**：**opt-in 硬证模式**。仅当 B+A 组合给出 `rewritten_same_content` 且需要定谳
  C（crash 归因）时，经新裁定启用。

### 方案 D · 游戏侧保证

- **判据**：假设「游戏只在崩溃时写 except.txt」，文件在场变化即崩溃。
- **可行性：不可行**。①「只在崩溃时写」无法离线验证（零真机）；②仓内证据**反向**：
  `:677` 明写「游戏自身会重写该文件」——说明游戏存在非崩溃场景的写，前提本身与
  harness 口径矛盾；③不可控：harness 无法强制游戏按假设行事。
- **结论**：**否决作为判据**。它只能作为文案注释（「文件被写可能与崩溃相关」），
  不能进入判定链。

## 4 · 探针证据（`_w11_t2_mtime_probe.py` → `_w11_t2_mtime_probe_out.txt`，EXIT=0）

- [0] D:\ 卷 `NTFS`（GetVolumeInformationW 离线查询）。
- [1] `write_bytes` 复制不保留 mtime（=harness `:4958` 方式，mtime=复制时刻）。
- [2] `shutil.copy2` 保留 mtime（陷阱成立）。
- [3] `os.utime` 伪造 mtime 成功（2000-01-01）。
- [4] 同内容重写：sha 相同、mtime 变化 ⇒ **B 失明、A 可见**。
- [5] 内容变更 + utime 拉回：sha 变化、mtime 相同 ⇒ **A 失明、B 可见**。
- [6] 连写 200 次：122 个不同 mtime ⇒ 同 tick 多次写**部分不可分辨**。
- [7] 时钟回拨：需改钟权限，未实测，按原理处理（⇒ A 假阴性方向）。

[4]/[5] 合起来正是「B 主 + A 旁证」互补性的直接证据：两者盲区互不重叠。

## 5 · 历史趟可离线补算 F 的最小路径（零 harness 改动）

对每趟 out-dir：
`pre_sha = fields.RESTORE.backup_sha256:except.txt`（或 `receipt.files["except.txt"].sha256_dst`）
↔ `post_sha = carrier_post_state.json["except.txt"].sha256`（或 `fields.RESTORE.current_sha256:except.txt`）。
三态：相同 ⇒ leftover_unchanged（l1b 实测即此态）；不同 ⇒ new_write；缺失 ⇒ absent/未测。
★ 限制：历史趟**无 mtime_pre**（`:4460` 只记 size+sha），A 旁证对历史趟退化不可用——
只能对**未来趟**加采（在 `:4460` 的 dict 里加 mtime + `time.time()` 捕获时刻，属 T3/PATCH 建议）。

## 6 · 推荐判据组合与决策表

**推荐：B（主）+ A 加固版（旁证），C 备选、D 否决。** 理由：
1. B 成本近零且可回溯历史趟（§5）；
2. B 与 A 的盲区**互不重叠**（探针[4][5]）：B 漏「同内容重写」时 A 可见，A 被
   utime 欺骗时 B 可见；叠加后单工具欺骗不成立，双工具同时欺骗（改内容+改 mtime 对齐）
   属蓄意伪造，超出本任务威胁模型；
3. A 加固版用「跑前实测 mtime」而非墙钟，规避复制保留 mtime 与 launch 锚精度问题，
   残余风险（回拨、同 tick）走降级标记而非误判；
4. C 的存在性证据最强但触碰 U-5 政策与未验行为扰动，只作定谳手段；
5. D 与 `:677` 口径直接矛盾，进入判定链会系统性污染 C（crash 归因）。

**六分支决策表**（`policy` 指示 C 是否经裁定启用）：

| pre 存在 | post sha vs pre | post mtime vs pre | 判定（is_new 语义=F） | 置信 |
|---|---|---|---|---|
| 缺 | 缺 | – | `absent_both`（无崩溃证据，也无法证无崩溃） | – |
| 缺 | 在场 | – | `new_first_appearance`（本趟新产生，强） | 高 |
| 有 | 文件消失 | – | `vanished`（error/flag，异常态） | – |
| 有 | 不同 | – | `new_write`（本趟被写；是否新异常交 E 另判） | 高 |
| 有 | 相同 | 不同 | `rewritten_same_content`（★ B 的盲区被 A 补住；TASK 点名场景） | 中（C 启用可升高） |
| 有 | 相同 | 相同 | `leftover_unchanged`（原样遗留；l1b 实测态） | 高 |
| 任意 | 复制/读失败 | – | `error` + 留痕（禁止静默） | – |

**回拨审计规则**：`mtime_post < mtime_pre` 且 sha 相同 ⇒ 标 `suspect_clock_rollback`，
置信降级并在 evidence 里带出两侧 epoch 捕获时刻。

## 7 · 诚实账（未验清单）

1. **ERRATA_CARRIER_REBUILD.md 未找到**：`find` 全仓（out/re_work 全深 + lead，排除
   .git/.mimosa）无此名文件 ⇒ 其所述载体重建语义**未验**；TASK §1.T1 第 1 条引用它作相关件，
   只能留待 T1 用其他证据链。
2. **时钟回拨**未实测（需改系统时间权限，违反零风险约束）——按文件系统原理处理，标注为原理项。
3. **游戏写 except.txt 的确切时机**（崩溃时？退出时？周期性？）**未验**——零真机不可验；
   仅 `:677` 一句「游戏自身会重写」可作反向证据。
4. **交接（handover）路径的复制方式**未验（本仓实测趟是 trip 自建模式 l1b）；
   若交接用 copy2 类工具，进场 mtime 不可信——判据设计已按「不信任进场 mtime」处理。
5. **FAT 系粒度 2s** 未在本盘实测（D:\ 为 NTFS [0]）；仅当载体落在 FAT 介质才生效。
6. **MSDN 文件时间缓存语义**未逐字核（原理项，探针[7]同批未实测项）。
7. TASK §0 四条前置事实中，本轮**直接亲验**了第 1（`:4561-4599`）、第 2（`:6390-6408`）、
   第 3（`:672-708`）条；第 4 条「59 份 setdiff 全 0」仅抽查 l1b 一份（1046/1046/0）——
   全量复核归 T4，未在本件展开。
