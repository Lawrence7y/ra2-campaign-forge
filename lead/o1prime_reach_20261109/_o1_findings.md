# O1′ 子格实证回件（lead/o1prime_reach_20261109/）

被核对象 SHA256 = ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2，字节数 = 412759
（被核件 = lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py；另 STATE_MATRIX.json 实测 sha256=1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016、3558 字节，与编排方指纹一致；10 件指纹全 MATCH，见 _o1_fp_out.txt）

## 一、两条路径实读答案（被核件行号）

- (a) 控制流：`:4769` 先 `post_observed.update({"exists": True, ...})` → `:4771` 组 dst 名 → `:4772 dst.write_bytes(blob)` 抛异常 → `:4773 except Exception` → `:4777-4785` 三条 `rec.add("ERROR",…)`（freshness_copy_failed / stage="read_bytes/stat/write_bytes" / traceback）→ `:4786 post_observed["read_error"] = f"{type(exc).__name__}: {exc}"` → `:4788-4789` classify+_emit_f("copy_failed") → `:4790 raise`。**正是走 ：4786，无旁路**。实证 traceback 绑定：`File "…\qc151_trip.candidate_lf.py", line 4772, in copy_post_except_evidence / dst.write_bytes(blob)`（_o1_dump_rows_out.txt，B1 与 B4 两例同）。
- (b) 此时 post_observed = `{exists: True, size: len(blob), sha256: <源件sha>, mtime_post: <源件mtime>, captured_at_iso: <:4765已置>, read_error: "FileNotFoundError/PermissionError: …"}`。实测 B1：exists=True, size=56, sha256=14f8168b…, read_error=FileNotFoundError [Errno 2]；B4：read_error=PermissionError [Errno 13]。
- (c) classify_except_freshness 的 read_error 检查在**第一个分支**（`:4643-4646`，先于 st 检查、先于 exists 分支）⇒ 返回 `("post_read_error", "none", None, usable_as_crash_evidence=False)`，pre_snapshot_state 如实保留。三种真实失败形态实测一致；**运行期从不输出 new_first_appearance/high**。
- (d) STATE_MATRIX.json 第 6 行原文 condition「跑前确认无件 + 跑后在场（存在性硬证）⇒ 本趟新出现」，verdict=new_first_appearance、confidence=high，**无 read_error 例外句**；而矩阵的 post_read_error 行（第 5 行）preState 只写 "present"。故按「preState+condition」字面键匹配，(absent_confirmed × exists=True × read_error) 格的唯一 claimant 是第 6 行 ⇒ 矩阵文本称 high，实码给 none。**冲突为真，但它是矩阵文本 vs 实码的文档层错配，不是运行期谎报**（与裁决 RULING_MATRIX_AB.md:55「运行期零缺陷声明」一致）。

## 二、可达性实证（方法 A+B 混合 + C 对照）

- 方法：静态 import 被核模块（importlib 标准导入；import 安全性先由 _o1_astcheck.py 静态证明——顶层仅常量/定义/__main__ 守卫 + 两处良性调用 `:182 SetProcessDPIAware`、`:3337` 纯计算）；在被核模块上直接调用真 `make_pre_freshness_snapshot`/`copy_post_except_evidence`/真 `Recorder`，spy 抓 classify 实收实参与真实返回；写失败全部落在唯一写域 `_o1_tmp`。Mimosa 拦截了首版 exec 方案后改为 import 方案（更贴任务允许清单）。
- 实测（python 3.12.10 / Windows 11 10.0.26200）：
  - success_control（out_dir 正常）：copy 成功 ⇒ new_first_appearance/high/is_new=True/usable=False（:6 行**合法**形态，作对照）。
  - B1 out_dir 父目录缺失：真 FileNotFoundError ⇒ post_observed{exists=True, read_error=FileNotFoundError} ⇒ **post_read_error/none/None/False**。
  - B2 out_dir 为普通文件：真 FileNotFoundError ⇒ 同上 post_read_error/none。
  - B3 超长路径（~370 字符）：本机长路径已放行，写入**成功** ⇒ new_first_appearance/high（合法）。该失败形态本机未复现，如实记。
  - B4 icacls 拒写（*S-1-1-0:(WD)，事毕 /remove:d 还原）：真 PermissionError WinError 13 ⇒ **post_read_error/none/None/False**。
  - 方法 C（构造字典喂真 classify）：exists=True×read_error×{absent_confirmed, present} 均 ⇒ post_read_error/none；exists=None×read_error ⇒ post_read_error/none；exists=True 无 read_error×absent_confirmed ⇒ new_first_appearance/high（:6 合法形态）。
- 产出：_o1_harness2.py/_o1_harness2_out.txt、_o1_dump_rows.py/_o1_dump_rows_out.txt、_o1_rows_dump.json（含全量 rows+traceback）、_o1_astcheck.py/_o1_astcheck_out.txt、_o1_fp.py/_o1_fp_out.txt。

## 三、write_bytes 失败的现实性

dst = `out_dir/except_post_<微秒时间戳>.txt`（:4771），out_dir=WORKDIR（finalize 缺省 ：6160-6161；来源 --out-dir/env :6424-6430；main 早期 `mkdir(parents=True, exist_ok=True)` :6450）。写入量 = 载体 except.txt 大小（母本 26515 字节量级，:244-245）。名字全新唯一 ⇒ 不存在「目标已存在只读/被占用」常态。
- 磁盘满：~26KB 自身量级几乎不可能；且磁盘满时更早的写帧/manifest 已先失败。**罕见**。
- 权限/AV 拦截：out_dir 是同进程刚建的运行期写域；企业端点 AV 拦项目目录写入可能存在。**罕见（环境级）**。
- 目标被占用：名字全新。**近乎不可能**。
- 路径过长：仅当操作者传极端 --out-dir；本机实测长路径放行（B3 写成功）；且 WORKDIR 启动即建，过长在趟前已失败。**罕见**。
- 只读介质 / out_dir 中途被删被换：**近乎不可能**（需外部并发干扰）。
结论：无任何由 trip 自身逻辑产生的触发路径，全部环境级、日常概率低。且一旦发生是**响亮失败**：ERROR×3（:4777-4785）→ raise（:4790）→ run_guarded_steps 落 finalize_errors.txt 并原样重抛（:4540-4553）→ write_finalize_error 落 error.txt（:4556-4577）。

## 四、虚报 high 的实际后果

- (a) 矩阵文本若被当真：会把一次证据副本环境失败读成「本趟新出现 except.txt（存在性硬证）· 高置信」——环境故障误读成崩溃征兆。
- (b) 实读代码确认：运行期**无任何**分支消费 confidence/new_first_appearance——F 字段只组装进 info/rec（:4798-4806、:4730-4753）；E/退出码口径独立（门禁注释 ：217-220、docstring :4619-4620）。freshness_confidence/verdict 的全部下游是测试断言（test_candidate.py:262-263 恰断言 copy 失败 ⇒ post_read_error/none，与实证一致）与设计/裁决探针；候选件本身 0 处引用 STATE_MATRIX（grep -c=0），读矩阵的 33 个 .py 全是审计/探针/测试脚本。
- (c) 该格 usable_as_crash_evidence=**False** 且恒 False（classify :4625/:4631 强制；落盘 ：4747-4750 note「恒 False：F 结论不得作为本趟崩溃证据」）。运行期账本四元组 = (post_read_error, none, None, False)，high 被 confidence=none + usable=False 双重兜死；暴露面只剩「人类审计者/严格键匹配器按矩阵 ：6 文本解读」，而同一账本并存 freshness_copy_failed ERROR + finalize_errors.txt，冲突自明。

## 五、结论

O1′ 的**输入格实流可达——已实证**（三种真实 write_bytes 失败产出 exists=True×read_error，traceback 绑定被核件 ：4772；裁决的码序链 ：4769→:4772→:4786 正确）。但**「虚报 high」不出现在运行期**：真 classify 恒回 post_read_error/none/None/usable=False；触发条件全部环境级罕见；发生时趟响亮失败、留痕自明。按本任务定义（真实流出现**且造成后果**），O1′ 应归**理论错配（文档/矩阵文本层）**：输入可达性真实（强于 W3 的 fixture-only），后果不成立（运行期零错误输出，与裁决 ：55 自述一致；裁决 ：243 自认「真机实流未复现、实际文件系统故障形态未验」——本实证在零真机约束内补上了文件系统故障形态这一环）。把它列为「活性错配三处之一」就「输入可达」而言成立、就「造成后果」而言名过其实。不判矩阵该不该改（归 A/B 裁决）。严重度：low。
