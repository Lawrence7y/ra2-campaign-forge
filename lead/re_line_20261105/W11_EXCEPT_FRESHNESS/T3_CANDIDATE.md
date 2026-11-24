# T3 · 离线修复候选 + 测试（W11 · D-22 裁决(A)执行步）

```
被核对象 = qc151_trip.py + 相关 harness 文件
qc151_trip.py SHA256 = 517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636，字节数 = 399508，行数 = 7291
  （本人实算：sha256sum + wc -c + wc -l，2026-11-06T03:36+08:00，路径
   out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py）
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（目标镜像，本任务不反汇编它）
回件时刻 = 2026-11-06T03:50+08:00
```

**范围**：本件只做 T3（离线候选 + 测试）。零真机（未启动 gamemd/ra2loader/YURI）、
零采样注入（E3 维持暂停 D-13）、未读活进程内存；**未修改 `qc151_trip.py` 与
`out/re_work/` 下任何文件**（写域仅 `W11_EXCEPT_FRESHNESS/`，实测见 §6 自查）。
T1 语义三分类归 `T1_SEMANTICS.md`，判据设计归 `T2_CRITERIA.md`，本件只引用。

---

## 0 · 结论速览

- 候选模块 + 测试 + 建议性补丁文本三件已落 `candidate/`，测试 **14/14 全绿**：
  `PASS=14 FAIL=0 EXIT=0`（实跑命令与输出见 §4，输出件 `_w11_t3_test_out.txt`）。
- TASK T3 四个必备分支全覆盖（§3 表）：源件缺失 / 原样遗留 / 内容变化 / 复制失败，
  另加 T2 盲区与防回归用例 6 个（同内容重写、 vanished、C 模式、回拨旗标、
  旁证不参与定判、纯函数性、跑前快照失败显式留痕）。
- 判据 = T2 推荐组合 **B 主（跑前基线 sha256）+ A 加固版（mtime_pre 差分旁证）**；
  方案 C 只以 `policy.hard_evidence_mode` 标注置信（启用需新裁定）；方案 D 不进判定链。
- `PATCH_SUGGESTION.md` 仅是**建议性 diff 文本**，未应用于任何文件。

## 1 · 交付物清单（全部新建于唯一写域内）

| 文件 | 内容 |
|---|---|
| `candidate/except_freshness.py` | 纯函数候选模块：`make_pre_snapshot` / `classify_except_post` / `copy_post_evidence_guarded` + `VERDICT_DOC` |
| `candidate/test_except_freshness.py` | unittest 14 用例，沙箱建在 `W11_EXCEPT_FRESHNESS/_t3_sandbox_*`（用完即删） |
| `candidate/PATCH_SUGGESTION.md` | 3 段建议性 diff（补采 mtime_pre / 生成点加 F 判定+防静默 / 调用点接线）+ 不做什么清单 |
| `_w11_t3_test_out.txt` | 实跑输出（`Ran 14 tests … OK / PASS=14 FAIL=0 / EXIT=0`） |

## 2 · 候选设计（与 TASK T3 要求逐条对表）

1. **纯函数**：`classify_except_post(pre_snapshot, post_path, run_start_ts=None,
   policy=None) -> dict`——只读 `pre_snapshot`（dict）与 `post_path` 指向的文件，
   全程不写盘、不启动进程、不读活进程内存（test_11 专测：调用前后沙箱目录清单不变）。
2. **返回键**：至少含 `is_new` / `reason` / `evidence`（TASK 要求），另含
   `confidence` / `suspect_clock_rollback` / `f_vs_e_note` / `verdict_doc`。
   `is_new` 的语义 = **F（本趟窗口内被写/新出现）**；`is_new=None` 表示 F 不可判
   （vanished / error 类）。`f_vs_e_note` 固化口径边界：内容变化只回答 F，
   E（新异常）归 `except_set_diff` 集合差——`qc151_trip.py:677` 明令
   「不得用 sha 变化判 crash」，候选**不越界**做 crash 归因。
3. **判据映射 T2 §6 六分支决策表**（`classify_except_post` 内实现）：

   | pre | post | 判定 reason | is_new | 置信 |
   |---|---|---|---|---|
   | 缺 | 缺 | `absent_both`（附「不能证无崩溃」注记） | False | low |
   | 缺 | 在 | `new_first_appearance`（C 模式标 hard） | True | high / hard |
   | 有 | 失 | `vanished`（异常态旗标） | None | – |
   | 有 | sha 异 | `new_write`（F 高置信；E 归集合差） | True | high |
   | 有 | sha 同、mtime 异 | `rewritten_same_content`（B 盲区被 A 补住；mtime 倒挂加 `suspect_clock_rollback`、置信降 low） | True | medium / low |
   | 有 | sha 同、mtime 同 | `leftover_unchanged`（l1b_20261021 实测态） | False | high |
   | 任意 | 读失败/快照失败 | `post_read_error` / `error_pre_snapshot`（显式留痕，禁止静默） | None | – |

4. **A 加固版而非 naive A**：mtime 判据用「跑前实测 mtime_pre」差分，
   不用「mtime >= 跑开始」；`run_start_ts` 只回显进
   `evidence.corroboration.post_mtime_ge_run_start` 作旁证——test_10 用
   「未来时刻的荒谬锚点」证明锚点不参与定判（T2 §3-A 否决 naive 版的防回归）。
5. **复制失败显式留痕**：`copy_post_evidence_guarded` 复刻 harness
   `:4579-4582` 的 read_bytes→write_bytes→sha256 语义，任何一步 OSError 落为
   `{"ok": False, "stage": "read_bytes"/"write_bytes", "error", "traceback"}`，
   绝不静默（TASK T3 分支 4 的「不是静默」要求）。
6. **tolerance / policy**：`policy.mtime_abs_tol`（默认 0.0，NTFS 直接比；
   FAT 系介质可调）、`policy.hard_evidence_mode`（C 需新裁定，默认 False）。

## 3 · TASK T3 四分支覆盖表（合成文件、非真跑 harness）

| TASK 分支 | 测试用例 | 构造 | 预期 ⇒ 实测 |
|---|---|---|---|
| 源件缺失 | `test_01_branch1_source_missing` | 跑前不建 `except.txt`，跑后也不建 | `absent_both`、`is_new=False`、confidence=low、notes 含「不能证」⇒ **实测一致** |
| 原样遗留 | `test_02_branch2_leftover_unchanged` | 跑前写内容并快照，跑后不写不动 | `leftover_unchanged`、`is_new=False`、confidence=high、post sha/mtime == pre ⇒ **实测一致** |
| 内容变化 | `test_03_branch3_content_changed` | 跑前快照后追加新行 | `new_write`、`is_new=True`、confidence=high、sha 不同、`f_vs_e_note` 含「集合差」⇒ **实测一致** |
| 复制失败 | `test_04_branch4_copy_failure_write`（+ 4b/4c） | out_dir 不存在使 `write_bytes` 抛 FileNotFoundError；src 为目录使 read_bytes 抛；src 缺失 | `ok=False`、stage=`write_bytes`/`read_bytes`/`src_missing`、traceback 非空、无静默半成品 ⇒ **实测一致** |

扩展用例：`test_05` post 读失败留痕、`test_06` 同内容重写（纯 B 会漏、A 补住，
对应 T2 探针[4]）、`test_07` vanished、`test_08` C 模式置信标注、
`test_09` utime 拉回 mtime ⇒ `suspect_clock_rollback`（探针[3]手法）、
`test_10` 旁证不参与定判、`test_11` 纯函数性、`test_12` 跑前快照失败显式留痕。

## 4 · 实跑记录（本 ask 期间执行）

```
命令：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/test_except_freshness.py
      >   D:/Project/ra2-campaign-forge/lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt 2>&1
退出码：0
输出末行：Ran 14 tests in 0.273s / OK / PASS=14 FAIL=0 / EXIT=0
沙箱残留检查：ls -d …/W11_EXCEPT_FRESHNESS/_t3_sandbox_* ⇒ (无残留)
```

测试沙箱由 `tempfile.mkdtemp(dir=W11_EXCEPT_FRESHNESS)` 创建、tearDown
`shutil.rmtree` 清理；**未在 `out/re_work/` 下产生或触碰任何文件**。

## 5 · PATCH_SUGGESTION 摘要（详见 `candidate/PATCH_SUGGESTION.md`）

- **补丁 1**（`backup_carrier :4458-4461`）：备份记录增补 `mtime_pre` +
  `captured_at_epoch/iso`，新记账键 `RESTORE.backup_mtime_pre:{name}`——
  A 旁证的最小采集面；历史趟无此字段，A 对历史趟退化（T2 §5 口径）。
- **补丁 2**（`copy_post_except_evidence :4561-4599`）：签名加可选
  `pre_snapshot`；就地内联最小移植候选判据（`freshness_verdict/confidence`
  进 `info`）；`write_bytes` 包 try/except-OSError——先显式记账
  `evidence_copy_write_failed` 再按原语义上抛（error 并留痕，非静默）。
- **补丁 3**（调用点 `:5938-5939` + 基线采集点 `:6387` 后）：接线
  `pre_snapshot=_pre_freshness_snapshot`；**不改证据先于还原的现行序**
  （`run_guarded_steps` 序 `:6042-6052` 经核正确，T1 已核，本补丁不动）。
- **不做什么**：不改 `restore_carrier`；不移走/不写载体 `except.txt`
  （C 触碰 U-5，`:6390-6408`，需新裁定）；不加任何 sha→crash 判定
  （`:677` 口径不变）；不改 `carrier_post_state.json` 既有字段。
- ★ 补丁 2 的内联移植未重跑四分支测试（测试对象是 `candidate/except_freshness.py`
  本体，内联版语义一致性属「若获授权应用后」的验收项，已写入 PATCH_SUGGESTION）。

## 6 · 铁律遵守自查（本件实测）

- `qc151_trip.py` 未修改：本轮两次实算 SHA256（03:36 与 03:38）均为
  `517889c6…c5ba636`、399508 字节、7291 行，与 TASK §0 绑定一致。
- 写域检查：本轮新建/写入仅 `candidate/` 三件 + `_w11_t3_test_out.txt` +
  本件，全部位于 `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/`；
  测试沙箱 `_t3_sandbox_*` 建于该目录内并已清理（§4）。
- 零真机/零注入/未读活进程内存：本件全部操作为文件系统读写与 python 离线执行。
- 未 commit、未 push。

## 7 · 诚实账（未验 / 边界）

1. **候选是离线语义验证，不是 harness 集成验证**：`classify_except_post` 接的
   `pre_snapshot` 口径（sha256+size+mtime）与 harness 现行 `backup_carrier`
   记录（只有 sha+size，无 mtime，`:4460-4461`）**不等价**——对历史趟只能跑
   B 主判据（A 旁证缺 mtime_pre 退化），这已在候选里显式降级标注而非掩盖。
2. **同 tick 盲区残余**：若游戏在跑前快照的同一 NTFS tick 内重写同内容
   （sha 同 + mtime 同），B、A 双盲——探针[6]实测同 tick 多次写部分不可分辨；
   实际上跑前快照在 launch 前、游戏写在 launch 后，实践中不同 tick，但**理论上未排除**。
3. **时钟回拨**：T2 已标原理项未实测；候选只在「mtime 倒挂 + sha 同」时降级
   置信并留两侧 epoch，不能识别「回拨后写入且 mtime 恰好等于 mtime_pre」。
4. **游戏写 `except.txt` 的真实时机**未验（零真机不可验）：候选回答 F，
   不回答 C（crash 归因）；D 方案被 `:677` 口径否决、未进入候选判定链。
5. **补丁 2 内联版与候选模块的一致性未测**（PATCH_SUGGESTION 是文本，未应用；
   应用于 harness 需用户新授权，属 D-22 nextSteps 第 5 条）。
6. F/mt 协议外的 `policy.mtime_abs_tol` 非 0 值未在 FAT 介质实测
   （本盘 D:\ 为 NTFS，T2 探针[0]）；默认 0.0 路径已被测试覆盖。
