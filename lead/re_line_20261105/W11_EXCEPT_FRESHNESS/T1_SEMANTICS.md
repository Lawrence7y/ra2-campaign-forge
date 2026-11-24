# T1 · 全链路语义核查：`except.txt` 与 `except_post_*` 的完整生命周期

```
被核对象 = qc151_trip.py + 相关 harness 文件
qc151_trip.py SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508，行数 = 7291
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（目标镜像，本任务不反汇编它）
回件时刻 = 2026-11-06T03:31:04+08:00
```

核查方式：全部结论来自（a）本会话实读 `qc151_trip.py` 行号，或（b）实跑只读探针
`_w11_t1.py`（输出 `_w11_t1_out.txt`，同目录）与 `find`/`sha256sum`/`grep`/`wc` 命令。
零真机、零注入、未修改 `out/re_work/` 下任何文件。

---

## 0 · 总判

**T1 判定 = CONFIRMED（六问全部落到 文件:行号 或 实跑命令+输出）。**
对 Leader §595 四条前置事实：**三条完全成立，两条有行号/计数的精度偏差（非实质推翻）**，
第 4 条的「59 份」与今日盘面不符（实测 66 份，见 §7）。

三分类结论一览（★ = TASK.md 特别问）：

| # | 对象 | 三分类 | 一句话依据 |
|---|---|---|---|
| 1 | 载体 `except.txt` 来源链 | **源码明确设计** | 母本只读(:228)+`except_reset` 死代码(:623 无调用点)+交接复制(:4946-4958)+游戏写(:677) |
| 2 | 跑前基线 `pre_except_txt` 时点 | **源码明确设计** | 启动前唯一被动读取(:6394-6408)；注释明说 U-5 被动语义 |
| 3 | `copy_post_except_evidence` 调用时机 | **源码明确设计** | 唯一调用点 :5939；:6042-6052 序列第 1 位，先于 :6048 restore |
| 4 | 全链新鲜性检查 | **实现缺陷（全链缺失）** | `新鲜/fresh` 0 处、`getmtime` 0 处、`st_mtime` 仅 :4420 记录用 |
| 5 | `carrier_post_state.json` 比对 | **源码明确设计（留痕）；写了但没人比** | 写入 :4591-4598；仓内读者只做路径长度/件数审计，零比对 |
| 6 | `except_post_*` 归档/读取 | **源码明确设计（writer-only 留痕）** | harness 零读者、零清理；离线取证件有读者 |
| ★ | `copy_post_except_evidence` 新鲜性语义 | **实现缺陷** | 60/60 实跑趟中副本 ≡ 继承内容；无任何新鲜性条件（§5 详述） |

---

## 1 · Q1 载体 `except.txt` 从哪来 —— 【源码明确设计】

三条来源链，各自有行号：

**(a) 母本链（已死）**。`EXCEPT_MASTER = BENCH / "except.txt"`（`qc151_trip.py:228`，
`BENCH = ROOT/"ra2bench"` :195）。唯一向载体写 `except.txt` 的函数是 `except_reset`
（:623-669，从母本读字节写载体 :649-653）。但 **`except_reset` 没有任何调用点**：
探针 [C] 全文件扫描 `except_reset` 的非定义出现仅 4 处（:643/:646/:663 均为
`rec.add` 的 `"script:except_reset"` 字符串、:6408 为 U-5 禁用注释）——**U-5 后是死代码**。
实测母本：`sha256sum ra2bench/except.txt` →
`ca175a71c8a25228685d28bf5b3a9d883665aec429dc03c46478cf486672f39d`、26515 字节，
与常量 :229-230 逐字一致（母本完好、未被写）。

**(b) 交接/源目录链（现行唯一初始化来源）**。`main()` 在 `--carrier-create-from`
给出时调 `create_isolated_carrier(rec, src_dir, WORKDIR/"ct", names)`（:6318-6325，
names 默认 = `CARRIER_FILES` :6319，五件含 `except.txt` :213-214）。该函数
`os.mkdir` 排他新建本趟唯一载体目录（:4926-4927），对五件逐一
`s.exists()`（:4946-4948，**源目录没有该件则跳过登记 None**）→
`read_bytes→write_bytes` 真实字节复制（:4958）→ 复读验 SHA（:4959-4961）。
**实证**：趟 `l3_20261031hb/carrier_creation_receipt.json` 的 `files["except.txt"]`
= `src=_src_L3_sf10c_20261021/except.txt`、`sha256_src=sha256_dst=6694b75e…`、
size 26405——即载体 `except.txt` 就是源目录内容逐字节继承。
该 `6694b75e` 正是 `ERRATA_CARRIER_REBUILD.md:22` 记录的**漂移留痕版本**
（交接建于 2026-10-17 21:05、早于 22:43 基线恢复 ⇒ 交接版即漂移版）。
即：**现行趟的载体 `except.txt` 初始内容 = 2026-10-17 时代的历史漂移内容（1046 行），
不是母本、不是干净态。**

**(c) 游戏写（运行期唯一写者）**。U-5 后 harness 自身运行期对载体 `except.txt`
零写（:6390-6392 注释、:6406-6408 `SKIPPED_U5`）；`except_set_diff` docstring
:676-677 明令「不得用 sha 变化判 crash（★ 游戏自身会重写该文件）」——游戏是
运行期写者，这是口径前提。

---

## 2 · Q2 跑前基线 `pre_except_txt` 是哪一刻 —— 【源码明确设计】

- **时点**：`main()` 的 `except_baseline` 阶段（budget :6393/:6409），位于
  `backup_carrier`（:6385-6388）**之后**、`mother_freeze`（:6415 起）与游戏启动
  **之前**。`_except_pre_path.exists()`（:6395）→ 全文 `read_text(errors="replace")`
  进内存 str（:6396-6397），只此一次；缺失则 `pre_except_txt = None`（:6402）。
  全程唯一消费点：`finalize_trip` 收尾第 3 项 `_except_diff`（:5974-5980），
  在 `finally` 里（`finalize_trip` 调用点 :7117-7125）。
- **「与本趟之前那次混淆？」**——**不可能**。理由：(1) 它严格在启动前读取，
  读取的就是「本趟启动前一瞬」载体文件内容；(2) 载体目录每趟排他新建
  （:4926-4927 `os.mkdir` 已存在即抛），不存在「上一趟的载体」；(3) 实证：
  探针 [E] 60/60 趟中 `except_post_*.txt` 的 sha256 == 本趟 receipt 的
  `sha256_dst`（启动前继承字节），即跑后文件 ≡ 启动前文件 ≡ 基线。
- **真正的混淆形态（要防的是这个）**：基线**内容**是历史漂移（6694b75e，
  2026-10-17 时代），不是「干净状态」。U-5 设计把全部历史内容当作「已存在」
  处理（:6390-6392 注释明说「被动读取现有内容作基线」），集合差
  （Counter 多重集差 :683-685）按行多重集扣除，历史行不会误报为新增——
  语义自洽。**风险不在 harness 内，而在「except_post_」这个名字对离线读者的暗示**
  （见 §5、§6）。
- **附发现（轻缺陷）**：`pre_except_txt` 是内存 str（:5901 参数传递），**其
  sha256 从未落盘**（探针 [C]：基线记录只有 `baseline_source=passive_read`
  :6398 与缺失态 :6403）。离线无法直接复算「基线指纹」；间接弥补是
  `backup_carrier` 对五件含 `except.txt` 记录了跑前 `sha256`（:4457-4461，
  bak dict → `restore_carrier` 记录 `backup_sha256:except.txt` :4494-4495）。

---

## 3 · Q3 `copy_post_except_evidence` 调用时机 —— 【源码明确设计】

- **唯一调用点**：`_except_evidence_copy()` 内 :5939（探针 [C]：`copy_post_except_evidence(`
  全文件 2 处 = :4561 def + :5939 call）。
- **顺序**：`run_guarded_steps` 列表 :6042-6052 共 9 项——第 1 项
  `("except_evidence_copy_and_verify", _except_evidence_copy)` :6043，
  第 6 项 `("restore_carrier", _restore)` :6048。**先取证、后还原，顺序正确**，
  与 docstring 声明的 QC162:W7 一致（:4566-4571）。
- **顺序的现存意义**：现 `restore_carrier` 已改为「只核验不写回」（:4470-4471
  docstring、:4488-4489 只比对 sha/size 并记账），即使顺序颠倒也不会覆盖内容；
  先取证序保留为防御性设计（docstring :5912-5918 说明）。整个 `finalize_trip`
  由 `main()` 的 `finally` 调用（:7117-7125），异常路径也会走到（`run_guarded_steps`
  逐项独立、跑完重抛 :4521-4534）。
- **同层第 1 项还有第二份副本**：`move_out_evidence_and_verify`（:5941，:5336-5451）
  递归搬出**载体全树**到 `out_dir/evidence/<stamp>/`，并把 `except.txt` 列为
  **必需件**（:5384-5386 插队、:5396 `is_required`、:5402-5406 缺失即失败）。
  即实跑趟里存在**两份**跑后副本：顶层 `except_post_*.txt` 与
  `evidence/<stamp>/except.txt`（实测 l3_20261031hb 两份 sha256 均为 6694b75e）。
- **附发现（一致性缺口，轻缺陷）**：对「跑后 `except.txt` 不存在」三种行为并存：
  `copy_post_except_evidence` 如实记账返回 None（:4575-4578）；
  `move_out_evidence_and_verify` 判必需件缺失 = 失败（:5402-5406）；
  `_except_diff` 直接 `read_text` **无 exists 检查**（:5978），缺失会抛
  `FileNotFoundError`（由 `run_guarded_steps` :4521-4534 记账重抛，不静默）。
  三者都不会静默吞掉，但语义不一致。

---

## 4 · Q4 有没有任何地方检查过新鲜性 —— 【实现缺陷（全链缺失）】

- 探针 [C] 全文件扫描（`qc151_trip.py` 7291 行）：
  - `st_mtime` 仅 **1 处** :4420（+ :4422 异常分支 null）——属于
    `_render_log_probe`（:4413-4425），对象是 `ra2render*.log`（:4416 glob），
    调用点 :6618/:6694（F 字段窗口边界诊断），**只记录 size/mtime，不与任何
    时间比较，与 `except.txt` 无关**——**不是新鲜性检查**。
  - `getmtime` **0 处**；中文「新鲜」**0 处**；`fresh` **0 处**。
- `except.txt` 相关的全部后置检查只有两类 **完整性**（integrity）语义，
  没有**新鲜性**（freshness，「内容确属本趟产生」）语义：
  1. `move_out_evidence_and_verify`：搬出前算源 sha → 写副本 → 复读副本算
     sha，两者相等才算 ok（:5410、:5451-5453）——证明「副本 == 搬出瞬间的源」，
     不证明「源是本趟写的」。
  2. `restore_carrier`：跑后载体件 sha/size vs 跑前备份 bak（:4488-4489，
     PASS/FAIL 只记账不写回）——证明「本趟改没改」，反过来讲：**一旦它报
     PASS（历史 60 趟均如此），恰等于承认 `except.txt` 内容与跑前逐字节相同，
     即 `except_post_*` 是纯继承内容的再拷贝**。
- 仓内其它用 mtime 的件（`crash_census/T00_pin_except_sha.py:17-18`、
  `U04_fingerprint.py:134-135`、`U02_single_pass_census.py:238/252`）均为
  **记录字段**（isoformat 落盘），无一处做时间比较闸门。
- 结论：**除 `except_set_diff` 的集合差（:672-708）外，全链没有任何机制区分
  「本趟新写」与「继承遗留」。** 判 **实现缺陷**（对 D-22 所指认的「崩溃证据
  新鲜性」必要条件缺失；D-22 裁 A「先修观测」即此）。

---

## 5 · Q5 `carrier_post_state.json` 有没有人比 —— 【写了但没人比】

- **写入**：:4591-4596——对 `CARRIER_FILES` 五件逐一 `exists()` →
  `{path, size, sha256}`（:4593-4594）→ 写 `carrier_post_state.json`（:4595-4596）；
  路径记入 rec（:4597-4598）。docstring 自述用途：「跑后载体件快照（★ 供
  『证据先于还原』复核：证明取的是跑后状态）」（:4589）。
- **harness 内零比对**：探针 [C] `carrier_post_state` 全文件 3 处
  （:4595/:4597/:4598，**全部写入侧**）。`bak`（跑前备份）在 harness 内只被
  `restore_carrier` 直接对载体文件比对（:4488-4489），**不经这份 JSON**。
- **仓内其它读者（实查）**：仅离线审计件
  `goal1_gate_offline_20261021/_audit_trips.py:17-18`（读它只为取
  `gamemd.exe.path` 的**目录路径长度**做 QC193 审计）、`_audit_final.py:16`、
  `_audit_dedup.py:19`、`_audit_pathlen.py:24-26`（件数/路径长度统计）。
  **没有任何一处把它的 sha256 与跑前备份比对。**
- **明写**：**写了但没人比。** 「跑后 vs 跑前」的比对语义由 `restore_carrier`
  独立承担（且其结果与该 JSON 内容互不引用）；这份 JSON 是**冗余留痕**，
  其唯一被消费方式是路径长度审计。判 **源码明确设计（留痕）**；若有人期望
  「据它离线复核新鲜性」，则该期望无实现支撑——同样落入 §4 的实现缺陷。

---

## 6 · Q6 `except_post_*` 的归档/清理与读者 —— 【源码明确设计（writer-only 留痕）】

- **harness 内零读者、零清理**：`except_post` 全文件 1 处 = writer :4581；
  `unlink(` 4 处均为 `hit_png`（:1919/:1954/:2676/:2763，截图防 WinError 183），
  `rmtree(` 1 处 :5759 = 删除载体目录（delete chain，只删 `ct/c_*`）。
  实测：`l3_20261031hb/ct/` 为空、`carrier_delete_result.json` 记录边界与删除。
- **生命周期**：载体内的 `except.txt` 随载体 rmtree 消亡；`except_post_*.txt`
  与 `evidence/<stamp>/except.txt` **永久留在趟目录**，趟目录由人工/离线流程
  归档为 `archive_T*`（无代码归档逻辑）。数据面：两棵趟树（chain + repo-root
  `lead/qc161_u0400_trip`）合计 `except_post_*.txt` **112 个**、
  `except_set_diff.json` 66 个、`carrier_post_state.json` 63 个（探针 [D]，
  深度≤3、剪枝 ct/evidence 等；`find` 不设上限口径：diff 66、post 113）。
- **读者（实查）**：harness 零读者；**离线取证件是唯一读者**——
  `goal3t_nightwatch_20261102/swarm_20261104/T42E4_FORENSIC_085458ab/_except_post.py:2-9`
  （读单件 size/mtime/头 1200 字节）；离线审计读的是 `except_set_diff.json`
  （`_audit_trips.py:52-57`）而非 `except_post` 本体。
- 风险注记：正因 harness 内无消费者，「except_post_」文件名对离线读者的
  「本趟崩溃证据」暗示无人纠正——60/60 趟其内容 ≡ 继承内容（探针 [E]），
  **作为「本趟证据」的信息量为零**。

---

## 7 · Leader §595 前置事实核对 + ★ 特别回答

**前置事实逐条**：

1. 「生成点唯一 `copy_post_except_evidence()` :4561，核心 :4576-4581」——
   **成立**。def 在 :4561；引用代码（src/exists/read_bytes/dst/write_bytes）逐字
   在 :4574-4582。行号偏差 2 行（:4576-4581 → 实为 :4574-4582），**非实质错误**。
2. 「:6394-6406 明写 baseline_source=passive_read、reset_verdict=SKIPPED_U5」——
   **成立**。:6398（passive_read）、:6406（SKIPPED_U5）。
3. 「except_set_diff :672-707 用 Counter 多重集差」——**成立**。
   def :672、`c_post - c_pre` :685、return :708（区间实为 :672-708，非实质错误）。
4. 「59 份 except_set_diff.json 的 pre_line_count 恒为 1046（59/59）、
   new_exception_count 全 0（59/59）」——**实质成立，计数过期**。实测今日
   全仓（chain 61 + repo-root 5）= **66 份，66/66 全部 (pre=1046, new=0)**
   （`find` + stdin 管道实跑）；探针深度≤3 口径 64 份同分布。
   「59」应为 §595 记账时点的快照数，非今日盘面。

**★ `copy_post_except_evidence` 属于哪一类：实现缺陷（就新鲜性语义而言）。**

推理链（全部有据）：
- 就其**字面意图**——「还原**之前**把跑后状态另存副本」（docstring :4563-4573，
  QC162:W7）——实现与意图一致：exists 判断（:4575）、原样 read_bytes/write_bytes
  （:4579/:4582）、先于 restore（:6043 vs :6048）。这一半是「设计如此」。
- 但 D-22 所核查的语义是**新鲜性**：这份副本是否承载「本趟」的信息。
  关键事实：**U-5 之前** `except_reset` 会把母本写回载体（:623-669），基线
  确定性等于母本 ⇒ 「except_post 与基线不同 ⇔ 本趟新写」隐式成立；**U-5 之后**
  覆盖写被移除（:6406-6408），载体 `except.txt` 变成继承漂移件（6694b75e），
  「except_post ≡ 基线」成为常态——实测 **60/60 趟中 `except_post_*.txt` 的
  sha256 与本趟 receipt 继承 `sha256_dst` 逐字节相同、0 趟不同**（探针 [E]：
  match=60, differ=0）。
- 即：该函数留档的文件在**全部实跑记录中不含任何本趟信息**，而它的记录
  note（:4585-4588）与文件名（`except_post_`）仍以「本趟跑后的原件副本/
  崩溃证据」名义呈现，且**没有任何字段、校验或比对把「与跑前基线相同」
  这一事实写进记录**（若比了 bak sha :4460，一秒就能标出）。
- 定性：**意图（崩溃证据留档、可复核）与实现（无新鲜性条件）不符、缺少
  必要条件 ⇒ 实现缺陷。** docstring 没有撒谎（「跑后」是时点描述，字面为真），
  缺的是：U-5 改变基线语义后，实现没有跟进补上新鲜性标注/校验——
  这正是「实现落后于语义环境变化」的实现缺陷，而非「设计如此」。

**修复方向（建议性，不属本卡修改范围）**：在 `copy_post_except_evidence`
内取 `bak.get("except.txt", {}).get("sha256")` 与当前 sha 比对，把
`same_as_pre_run`（布尔）+ 两 sha 写进 `info` 与 `carrier_post_state.json`；
为真时文件名或 note 明示「content unchanged since pre-run (inherited)」。
（此为 T3 候选件 `except_freshness.py` 的设计输入；对 `qc151_trip.py`
的实际修改需 D-22 nextSteps 第 5 条新授权，本卡不改。）

---

## 8 · 诚实账

- 本卡唯一写域：`lead/re_line_20261105/W11_EXCEPT_FRESHNESS/`
  （`T1_SEMANTICS.md` + `_w11_t1.py` + `_w11_t1_out.txt`）。未写其它任何文件；
  未修改 `qc151_trip.py` 与 `out/re_work/` 下任何文件（只读）。
- 零真机、零注入、未读活进程内存。所有 Python 以 `python -I -X utf8` + 绝对路径运行。
- 探针深度≤3 + 剪枝（ct/evidence/_carrier_bak/shots 等）⇒ [D] 的 112/64/63 是
  截断口径；不截断口径的 diff=66（实跑 `find | wc -l`）、post=113（chain 108 +
  root 5）。两者均已如实并列。
- 交接载体的完整 86 件清单（HANDOVER_SHA.txt）未逐件复核（T1 六问不需要）；
  `ERRATA_CARRIER_REBUILD.md` 全文已读（:22 漂移留痕与实测 6694b75e 相符）。
- §555「37 个 archive 零趟游戏崩溃」属 T4 影响面，本卡未核。
- Mimosa 安全钩对探针初稿的「路径穿越」拦截：为消除数据流歧义，E 段改为
  纯 `os.walk` 分组、路径全部由 walk 结果直接给出（无 listdir+字符串拼接），
  最终件通过钩子并实跑成功；行为语义不变（只读）。
