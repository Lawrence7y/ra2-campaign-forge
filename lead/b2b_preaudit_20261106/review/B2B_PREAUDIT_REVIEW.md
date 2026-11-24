# B2b 独立设计预审判定书复核回件

**复核员**：判定书复核员（独立复核员，新上下文，未参与 `B2B_PREAUDIT.md` 编写）  
**复核日期**：2026-11-06  
**被复核对象**：`lead/b2b_preaudit_20261106/B2B_PREAUDIT.md`  
**验证探针**：`lead/b2b_preaudit_20261106/_b2b_pa_probe.py` 与 `lead/b2b_preaudit_20261106/_b2b_pa_probe_out.txt`  
**铁律遵守**：
1. 零真机：不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存。
2. 零采样代码：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
3. 只读母本与被审对象：母本 `qc151_trip.py` 一个字节未动（SHA256 恒为 `517889c6...`）；`B2B_DESIGN.md` 与被审判定书只读。
4. 唯一写域：`lead/b2b_preaudit_20261106/`（本回件落盘于 `lead/b2b_preaudit_20261106/review/B2B_PREAUDIT_REVIEW.md`）。
5. 不 commit、不 push；Python 全走隔离模式 `-I` 与 `-X utf8`，全绝对路径。

---

## 0 机器可读复核结论

```yaml
subjectSha256: 3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f
subjectBytes: 20615
checkedEveryRow: true
noOverreach: true
hunkVerdictCount: 9/9
```

实算命令（本机无 `sha256sum`/`wc`，使用 Python hashlib 与 len）：
```bash
python -I -c "import hashlib, pathlib; p = pathlib.Path('D:/Project/ra2-campaign-forge/lead/b2b_preaudit_20261106/B2B_PREAUDIT.md'); data = p.read_bytes(); print('bytes:', len(data)); print('sha256:', hashlib.sha256(data).hexdigest())"
```
实算输出：
- `bytes: 20615`
- `sha256: 3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f`

---

## 1 基准文件指纹复核

依据项目铁律，在复核开始前与结束后对母本及相关基准件进行二进制 SHA256 与字节数核验，证明全过程零漂移、母本一个字节未动：

| 对象 | 相对路径 | SHA256 (64 hex) | 字节数 (Bytes) | 状态 |
|:--|:--|:--|--:|:--:|
| **正式母本** | `out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py` | `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636` | 399508 | **PASS**（零漂移，一个字节未动） |
| **被审设计 B2b** | `lead/b2b_design_20261106/B2B_DESIGN.md` | `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf` | 66735 | **PASS**（与判定书记录完全一致） |
| **被否旧设计 B2** | `lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md` | `deacab49b2bc02f44ecf629036427153affee422c2059c31ecc1471b1f311a5f` | 11638 | **PASS**（历史基准件一致） |
| **被复核判定书** | `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` | `3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f` | 20615 | **PASS**（复核目标版本） |

---

## 2 检查 1：逐条「文件:行」断言全量核验（不抽样）

本人对 `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` 全文中引用的**每一处**「文件:行」进行了逐行实读与机械比对，无任何抽样，核验详情如下：

### 2.1 九个 Hunk 的文件与行号引用核对
1. **H1**：
   - 判定书引用：母本 `qc151_trip.py:212-217` 对齐设计稿 `B2B_DESIGN.md:205-227`（`@@ -212,6 +212,21 @@`）。
   - 亲读核验：母本 `:212-214` 为 `CARRIER_FILES = ("gamemd.exe", ...)`，`:216-217` 为常量节标题；设计稿在 `:214` 后注入 5 个 `FRESHNESS_` 常量，两端上下文逐字符完全匹配。
   - 结论：**MATCH** ✅。
2. **H2**：
   - 判定书引用：设计稿 `B2B_DESIGN.md:230-241`（`@@ -4458,6 +4473,10 @@`）对齐母本 `qc151_trip.py:4458-4463`。
   - 亲读核验：母本 `:4458-4463` 为 `backup_carrier` 循环内 `dst.write_bytes...` 至 `return bak`；设计稿在 `:4460` 后追加 `rec.add("RESTORE", f"backup_mtime_pre:{name}", ...)`，上下文 6 行逐字符完全一致，且未修改 `bak[name]` 三键契约。
   - 结论：**MATCH** ✅。
3. **H3**：
   - 判定书引用：设计稿 `B2B_DESIGN.md:244-377`（`@@ -4558,8 +4577,131 @@`）对齐母本 `qc151_trip.py:4558-4565`；作用域依赖符号 `hashlib/time/Path` 见母本 `:167-175`，`sha256_file` 见母本 `:416`，`now_iso` 见母本 `:432`。
   - 亲读核验：母本 `:4558-4565` 8 行上下文与 diff `-` 侧逐行完全一致；依赖符号亲读确认：母本 `:167` `import hashlib`、`:173` `import time`、`:175` `from pathlib import Path`、`:416` `def sha256_file(p: Path) -> str:`、`:432` `def now_iso() -> str:`，全部在模块作用域存在且就绪。
   - 结论：**MATCH** ✅。
4. **H4**：
   - 判定书引用：母本 `qc151_trip.py:4572-4591` 对齐设计稿 `B2B_DESIGN.md:380-495`（`@@ -4572,20 +4714,105 @@`）。
   - 亲读核验：母本 `:4572-4591` 为原 `copy_post_except_evidence` 函数体（20 行）；设计稿完全重写该体并实现 3 个出口落盘 F 字段及 12 键 info，上下文行与删除行逐行完全吻合。
   - 结论：**MATCH** ✅。
5. **H5**：
   - 判定书引用：设计稿 `B2B_DESIGN.md:498-508`（`@@ -5906,7 +6133,8 @@`）对齐母本 `qc151_trip.py:5906-5912`。
   - 亲读核验：母本 `:5906-5912` 7 行上下文逐字一致；设计稿在 `finalize_trip` 签名末尾安全追加 `pre_freshness_snapshot: dict | None = None`，无参数错位。
   - 结论：**MATCH** ✅。
6. **H6**：
   - 判定书引用：设计稿 `B2B_DESIGN.md:511-521`（`@@ -5936,7 +6164,8 @@`）覆盖母本 `qc151_trip.py:5936-5942`（母本 `:5939` 唯一调用点）。
   - 亲读核验：母本 `:5936-5942` 7 行上下文逐字一致；母本 `:5939` 原为 `copy_post_except_evidence(rec, carrier_dir, out_dir)`，设计稿替换为传参 `pre_freshness_snapshot=pre_freshness_snapshot`，闭合传参链。
   - 结论：**MATCH** ✅。
7. **H7**：
   - 判定书引用：设计稿 `B2B_DESIGN.md:524-534`（`@@ -6294,6 +6523,9 @@`）与母本 `qc151_trip.py:6294-6299`；外层 `try:` 位于母本 `:6313`；预初始化位于 `:6296` 之后；5 个早退点 `:6340`、`:6349`、`:6361`、`:6374`、`:6377`；收尾位于 `finally:7122`。
   - 亲读核验：母本 `:6294-6299` 6 行上下文逐行吻合；母本 `:6313` 确为 `try:`；`:6296` 为 `pre_except_txt = None`；5 个早退点在母本中确为 `return EXIT_CARRIER_NOT_OWNED` (:6340)、`return EXIT_TARGET_MISSING` (:6349)、`return EXIT_TARGET_MISMATCH` (:6361)、`return EXIT_PRECHECK_SHA_MISMATCH` (:6374)、`return EXIT_PRECHECK_SIG_MISMATCH` (:6377)；收尾调用点在母本 `:7122`（`:7117-7125`）。预初始化确在 `try:` 之前。
   - 结论：**MATCH** ✅。
8. **H8**：
   - 判定书引用：母本 `qc151_trip.py:6386-6391` 对齐设计稿 `B2B_DESIGN.md:537-553`（`@@ -6386,6 +6618,15 @@`）；快照构造位于 `:6388` 后（`:6387` 备份后、`:6456` launch 前）。
   - 亲读核验：母本 `:6386-6391` 6 行上下文逐字吻合；母本 `:6387` 为 `bak = backup_carrier(rec, carrier_dir)`，`:6388` 为 `budget.end_stage("backup")`；母本 `:6456` 为 `budget.begin_stage("launch")`。快照构造位置准确无误。
   - 结论：**MATCH** ✅。
9. **H9**：
   - 判定书引用：母本 `qc151_trip.py:7122-7128` 对齐设计稿 `B2B_DESIGN.md:556-566`（`@@ -7122,7 +7363,8 @@`）。
   - 亲读核验：母本 `:7122-7128` 7 行上下文逐行吻合；设计稿在 `:7125` 的 `created_receipt=...` 后追加实参 `pre_freshness_snapshot=_pre_freshness_snapshot`，形参名与实参名一致。
   - 结论：**MATCH** ✅。

### 2.2 五个早退路径与正常退场引用核对
- 判定书引用母本 `:6340`、`:6349`、`:6361`、`:6374`、`:6377` 为 5 个早退点，`:7029` 为 `return EXIT_OK` 正常退场点。
- 亲读核验：母本 `:7029` 确为 `return EXIT_OK`，母本 `:7030` 紧随 `except BaseException as exc:`；前述 5 个早退点确为 `:6387` 备份前所有提前返回点。
- 结论：**MATCH** ✅。

### 2.3 状态矩阵与代码实现引用核对
- 判定书引用 `STATE_MATRIX.json` 14 条记录及 `B2B_DESIGN.md:148-161` §2 表格。
- 亲读核验：`STATE_MATRIX.json` 确为 14 条记录，`B2B_DESIGN.md:148-161` 确为 14 行表格，二者条件、verdict、confidence 与 usableAsCrashEvidence（全为 false）完全一致。
- 判定书引用 `B2B_DESIGN.md:299` 硬编码 `"usable_as_crash_evidence": False`、`:304-307` 脏值归一为 `"unknown"`、`:316-320` `unknown` 直出且置信度为 `"none"`。
- 亲读核验：设计稿相应行号代码确真如此实现。
- 结论：**MATCH** ✅。

### 2.4 F/E 分离与退出码隔离引用核对
- 判定书引用母本 `:672-708` 为 `except_set_diff`、`:677` 为「不得用 sha 变化判 crash」、`:5984-5990` 为唯一影响退出码处。
- 亲读核验：母本 `:672-708` 确为 `except_set_diff`，`:677` 确包含该禁止说明，`:5984-5990` 确为 `if not setdiff.get("no_new_exception", True): ... note_cleanup_failure(EXIT_INTERNAL_ERROR, ...)` 判据块。
- 判定书引用设计稿 `B2B_DESIGN.md:626-654` §6 F/E 分离约束；实测 9 个 hunk 的 `-` 侧区间完全避开 `:5984-5990`，F 区代码禁词出现次数为 0。
- 结论：**MATCH** ✅。

**逐条核验结论**：判定书中的所有引用均真说了那句话，无一虚构，无一张冠李戴。`checkedEveryRow: true` 成立。

---

## 3 检查 2：重跑验证探针并比对输出

本人在项目根目录下以隔离模式及 UTF-8 执行探针脚本：
```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/b2b_preaudit_20261106/_b2b_pa_probe.py"
```

### 3.1 实跑输出指纹比对
- 探针运行前 `lead/b2b_preaudit_20261106/_b2b_pa_probe_out.txt` 指纹：
  - SHA256: `bc388bac72b221108d1e38c5ac19c81e32b599ba363bbed57b7a067e2bc7a993`
  - 字节数: `11999`
- 重跑探针后 `_b2b_pa_probe_out.txt` 指纹：
  - SHA256: `bc388bac72b221108d1e38c5ac19c81e32b599ba363bbed57b7a067e2bc7a993`
  - 字节数: `11999`
- 结论：探针输出与现存 `_b2b_pa_probe_out.txt` **逐字节完全一致（0 差异）**。

### 3.2 探针输出核心要点核验
1. **母本与设计稿指纹**：
   - 母本 SHA256: `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`（399,508 B, 7,291 行），PASS。
   - 设计稿 SHA256: `565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf`（66,735 B, 693 行）。
2. **Hunk 提取与匹配**：
   - 提取到 9 个 diff 块、9 个 hunk；全部 9 个 hunk 的 `-` 侧原文在母本中 100% 逐行匹配，且在母本中唯一出现 1 次。
3. **内存拼接与 AST 语法树解析**：
   - 内存拼接后总行数 7,533 行（净增 242 行，与各 hunk delta 累加和 `15+4+123+85+1+1+3+9+1=242` 完全一致）。
   - `ast.parse` 结果：`SUCCESS (0 syntax errors)`；关键函数（`make_pre_freshness_snapshot`、`classify_except_freshness`、`copy_post_except_evidence`、`finalize_trip`、`main`）全部完备且签名形参闭合。
4. **行号冲突与累积偏移**：
   - 母本 `-` 侧与声明 `+` 侧各区间均互不重叠（间距 6..4240 行）；累积偏移检验（Cumulative Offset Drift Check）全部 9 个 hunk 均为 MATCH，零行号冲突、零漂移。

---

## 4 检查 3（专项 A）：九个 Hunk 判定专项排查（有无 BLOCKED / UNVERIFIABLE 悄写成 OK）

对判定书第二节「九个 Hunk 逐项核验」的判定逐一复核：
- H1: **OK**。顶层常量注入，语法合规，无全局污染。
- H2: **OK**。`backup_carrier` 记录 `RESTORE.backup_mtime_pre`，保持原有三键字典结构。
- H3: **OK**。纯函数实现，不侵入退出码，向后兼容 `pre_freshness_snapshot=None`。
- H4: **OK**。全出口落盘，三态严格可分，`unknown` 恒置信度 `none`。
- H5: **OK**。签名末尾追加可选参数，不破坏既有调用点。
- H6: **OK**。母本 `:5939` 唯一调用点显式闭合传参链，彻底消除旧 B2 的 N5 死因。
- H7: **OK**。`main` 的 `try:` 之前完成 `_pre_freshness_snapshot = None` 预初始化，彻底消除旧 B2 的 E1 死因（杜绝 5 个早退点与前置异常抛出 `NameError`/`UnboundLocalError`）。
- H8: **OK**。在载体备份完成与进程启动之间采集合规快照，时序合理。
- H9: **OK**。主流程 `finally` 块安全传递快照对象至 `finalize_trip`。

**专项核查结论**：
1. 没有把任何静态存在阻断项（如语法错误、作用域泄漏、早退漏绑、行号重叠、调用点漏改）的 hunk 判定为 OK。
2. 判定书没有把不可验证的运行期表现（如游戏进程并发锁、真实退出码等）伪造成静态 OK，而是在第六节「未验」中列明 5 项未验事项。
3. **未发现把 BLOCKED 悄悄写成 OK，未发现把 UNVERIFIABLE 悄悄写成 OK**。

---

## 5 检查 4（专项 B）：越权表述专项排查（有无将「设计 YES」写成「可应用」）

本人对 `lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` 全文检索「可应用」、「应用到母本」、「可直接施用」等关键词，并对其效力边界条款进行专项审查：
1. **明确界定 YES 的效力**（L15-L18）：
   > `verdict: YES 的准确含义 = 可以拿去编写候选；不等于可以应用到母本。`  
   > `绝对禁止将本设计直接应用到母本，后续仍须严格执行候选编写、独立代码复审、隔离副本集成验证与真机验收流程。`
2. **明确将母本施用列为未验**（L194）：
   > `4. 母本施用及回归未验：依据铁律 4，母本 qc151_trip.py 一个字节未动。候选补丁在隔离副本环境的打补丁实测、回退演练以及各历史趟件回放未验。`
3. **全文检索结论**：
   判定书全文无任何「可以应用到母本」、「可直接施用」或越权放行的表述。
4. **专项核查结论**：`noOverreach: true`。

---

## 6 检查 5：Hunk 标题计数与判定数核对

- 判定书第二节包含 9 个 hunk 标题：
  - `#### H1` (L23)
  - `#### H2` (L28)
  - `#### H3` (L33)
  - `#### H4` (L38)
  - `#### H5` (L43)
  - `#### H6` (L48)
  - `#### H7` (L53)
  - `#### H8` (L58)
  - `#### H9` (L63)
- 每个 hunk 标题下均包含明确判定 `- **判定**：OK`。
- 逐个 hunk 判定数：`9/9`。
- **结论**：`hunkVerdictCount: "9/9"`。

---

## 7 问题项列表 (issues)

复核过程中未发现事实错误、行号错引、表述越权或掩盖阻断问题：
```json
[]
```
- `issues: []`（0 个问题项）。

---

## 8 复核总结论

`lead/b2b_preaudit_20261106/B2B_PREAUDIT.md` 判定书是一份严谨、诚实、数据完全复现、效力边界严密清晰的合格设计预审判定书。判定书给出的 `verdict: YES`（含义为可拿去起草候选补丁，绝不可直接应用到母本）完全成立。

- `checkedEveryRow`: **true**
- `hunkVerdictCount`: **"9/9"**
- `noOverreach`: **true**
- `subjectBytes`: **20615**
- `subjectSha256`: **"3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f"**
- `issues`: **[]**
