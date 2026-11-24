# B1 · 把 W11 新鲜性候选应用到正式 harness（D-24 定谳 A>B>D>C 的 B 步）

> **来源**：D-24 定谳 `★ 定谳：D-24 = A>B>D>C`（`D24_RULING/RULING_D24.md:7`），
> B 步动作见 `:52`，授权归属见 `:61`（`B／G4` 行）+ `:77`（q3 回答）。
> **授权依据（裁决已定，不是我自裁）**：`RULING_D24.md:77` 明写
> 「**是，既有全开授权已覆盖正式 harness 应用的一般权限面，有权来源会话现在可安排并执行限定离线补丁、无须再次询问同一授权**」；
> `:61` 明写「有权来源会话可直接安排执行，**无须重复索取同一一般授权，也无需新增 D**；执行代理须有任务书明确的正式 harness 写域」。
> **本任务就是那个「执行代理」，本文件就是那个「任务书明确的写域授权」。**

## 0. 本任务要做的唯一一件事

**把 W11 的 `except_freshness.py` 候选语义，以最小侵入方式内联进 `qc151_trip.py` 的
`copy_post_except_evidence`，并留下应用前后指纹与回退材料。**

**只改新鲜性文件处理路径，不碰任何其他逻辑。**

## 1. 被改对象（★ 应用前必须自己重算，不符即停）

| 项 | 值（我在 2026-11-06 08:57 实算） |
|---|---|
| 路径 | `D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py` |
| SHA256 | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` |
| 字节数 | `399,508` |
| 行数 | `7,291` |
| mtime | `2026-10-20 00:08:02.206731100 +0800` |

★★ **你应用前必须自己跑 `sha256sum` + `wc -c` + `wc -l`。若与上表不符 ⇒ 立即停止，写 `OBJECT_CHANGED`，
不得套用旧版本候选，并在回件里说明差异。**

## 2. 候选语义来源（只读，不许改）

`lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py`（10,415 B，结构化接口如下）：

| 行 | 定义 | 用途 |
|---|---|---|
| `:64` | `make_pre_snapshot(except_path, *, sha=True) -> dict` | 跑前基线快照 |
| `:99` | `classify_except_post(pre_snapshot, post_path, run_start_ts=None, policy=None) -> dict` | 新鲜性判定，返回 `is_new / reason / evidence` |
| `:243` | `copy_post_evidence_guarded(src, out_dir, *, name_prefix=...) -> dict` | 带新鲜性判定的复制 |

配套：`candidate/test_except_freshness.py`（10,524 B，14 测全绿）、`candidate/PATCH_SUGGESTION.md`（7,585 B，**建议性 diff，本任务的直接起点**）。

## 3. 要改的三个点（严格按 `PATCH_SUGGESTION.md`，不许扩大）

### 3.1 `backup_carrier`（约 `:4458-4461`）—— 补采 `mtime_pre` + 捕获时刻

现在只记 `size + sha256`，**不记 mtime** ⇒ 跑后无法做 A 加固版差分。
要加：`mtime_pre` / `captured_at_epoch` / `captured_at_iso` 三个键（**只增不改**，历史可比性不断）。

### 3.2 `copy_post_except_evidence`（`:4561`，核心 `:4574-4582`）—— 加新鲜性判定 + 复制防静默

现在只判 `src.exists()`、原样复制、零新鲜性判断。要加：
- 新增形参 `pre_snapshot: dict | None = None`
- 判定逻辑按候选语义（sha256 主 + mtime 差分旁证），四个分支：
  `new_first_appearance` / `new_write` / `rewritten_same_content` / `leftover_unchanged`
- `write_bytes` 失败时 `rec.add("ERROR", ...)` 显式留痕再上抛（**不许静默**）
- info 里新增 `mtime_post / freshness_verdict / freshness_confidence / freshness_note`

### 3.3 两处调用点接线（`:5938-5939` 与 `:6390` 附近）

- `_except_evidence_copy()` 调用处传入 `pre_snapshot=_pre_freshness_snapshot`
- `backup_carrier` 之后、launch 之前构造该快照

★ **证据先于还原的现行顺序（`:5939` 早于 `:5953`）保持不变，不许动。**

## 4. ★★ 绝对不许做的事（越界即作废）

1. **不许改 `restore_carrier`**（`:4465-4499`）—— 只比 sha+size 的核验语义保持原样
2. **不许移走/改名/写载体 `except.txt`** —— 那是方案 C，触碰 U-5 裁定（`:6390-6408`），需新裁定
3. **不许加任何「sha 变化 ⇒ crash」判定** —— `:677` 明令禁止；`freshness_verdict` 只回答 F（新鲜性），
   `except_set_diff`（`:672-708`）仍是 E（新异常）唯一口径
4. **不许改 `carrier_post_state.json` 的既有字段**（只增不改）
5. **不许动 `.gitignore` 或任何其他文件** —— 唯一可写文件就是 `qc151_trip.py`
6. **不许运行完整 harness**（会启游戏）—— 零真机铁律
7. **不许写任何 hook / MiniDump / SuspendThread / StackWalk / 探针注入**（D-13 维持暂停）

## 5. 必须留的四个交付物

写到 `lead/re_line_20261105/B1_HARNESS_PATCH/`：

| 文件 | 内容 |
|---|---|
| `PRE_PATCH_FINGERPRINT.md` | 应用前实算的 SHA256 / 字节数 / 行数 / mtime，四条命令原文 + 输出 |
| `DIFF.md` | **完整 unified diff**（`diff -u` 或 `git diff` 输出），逐块说明改了什么、为什么 |
| `POST_PATCH_FINGERPRINT.md` | 应用后同样的四项 + **回退命令**（如何用备份还原回 `517889c68f037ab6…`） |
| `B1_HARNESS_PATCH.md` | 汇总：七节（`## 0 总判` / `## 1 应用前指纹` / `## 2 改动清单` / `## 3 差异` / `## 4 隔离验证` / `## 5 回退材料` / `## 6 诚实账`） |

★ **备份必须做**：应用前把原文件复制一份到 `B1_HARNESS_PATCH/qc151_trip.py.bak`，
并记录该备份的 SHA256（应等于 `517889c68f037ab6…`）。

## 6. 隔离验证（不许跑真 harness）

改完后必须证明：
1. **语法可编译**：`python -I -X utf8 -c "import ast,io; ast.parse(io.open(r'<path>',encoding='utf-8').read())"` → 退出码 0
2. **改动面纯净**：用 `difflib` 或 `git diff --stat` 证明**只改了三处**（`backup_carrier` / `copy_post_except_evidence` / 两处调用点）
3. **新增函数可单测**：把新增的判定逻辑抽成可导入的纯函数，在 `B1_HARNESS_PATCH/` 内用**合成文件**跑四个分支
   （源件缺失 / 原样遗留 / 内容变化 / 复制失败），输出必须 `PASS=n FAIL=0 EXIT=0`
4. **六个禁止面 API 计数不变**：`WriteProcessMemory` / `CreateRemoteThread` / `SuspendThread` /
   `MiniDumpWriteDump` / `StackWalk` / `SetWindowsHookEx` 出现次数与改前逐项相同
5. ★ **不许运行 `qc151_trip.py` 本体**（`--help` 也不行，它会初始化 harness）

## 7. 回件强制头部

```
被核对象 = qc151_trip.py
应用前 SHA256 = <自己实算>，字节数 = <自己实算>，行数 = <自己实算>
应用后 SHA256 = <自己实算>，字节数 = <自己实算>，行数 = <自己实算>
备份 SHA256   = <自己实算>，应等于应用前 SHA256
候选参考件 = lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py（10,415 B）
gamemd.exe SHA256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（本任务不反汇编它）
回件时刻 = <实际时刻>
```

## 8. 判定档

- **CONFIRMED**：三处改动全部落地 + 五项隔离验证全过 + 回退材料齐 + 指纹绑定。
- **PARTIAL**：改动落地但某项验证只能给「未验」。
- **REFUTED**：发现候选语义与 harness 现有逻辑**结构性冲突**（例如 `:677` 的禁令被触发）。
  ★ 若你判断这个补丁**不该应用**，直接说并给依据——**那比硬着头皮改更有价值**。

## 9. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**。
- **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。**D-13 维持暂停**。
- ★★ **写域 = `lead/re_line_20261105/B1_HARNESS_PATCH/` + 唯一被改文件 `qc151_trip.py`**。
  其余一律只读：`ra2youli\`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `W1_*`…`W11_*` 既有件、`D*_RULING\`、`V6_V3_REVIEW\`、`A1_*`、`A1_ERRATA_MAP\`、`_leader\`。
- ★★ **不许恢复/重建 W7 的 phase 2**（D-24 明令）。
- **不 commit、不 push。**
- Python 一律 `python -I -X utf8`，绝对路径。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- ★ **否定性/存在性事实先用 `find`/`ls`/`wc`/`sha256sum`/`grep`**，不要上全仓 Python 遍历。
- ★ **本任务不需要 `ra2tool.Engine`** —— 一次都不要用。
- ★ **并行度**：本任务最多同时 2 个子代理。
- ★ **`out/` 被 `.gitignore:33` 忽略**，所以 `git diff` 看不到改动——必须用**文件级 SHA256 + `diff -u` 备份对比**证明改动。
