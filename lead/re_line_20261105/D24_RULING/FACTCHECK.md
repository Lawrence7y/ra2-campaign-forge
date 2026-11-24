# D-24 · V1/V2/V3 事实核证

核证时间：2026-11-06 07:14 +0800。范围仅 TASK.md §2 三项。已按指定顺序读取 D-24 全文、TASK.md 全文及 §1 七件相关节；锚点 §二之二、§二之三、§三及 §四 A5/A12/A24 已读。

## V1 · 现在是否零工作流在飞

**未验／未独立核。** 本次提供的工具中没有 `ListWorkflowRuns`，未执行读取 20 条 run 状态的检查。按 TASK.md:30 指定降级方式转录 `lead/PENDING_DECISIONS.md:68-72`：截至条目记载的 2026-11-06 07:0x，W8 `dwfrun-6c06fd50`、W10 `dwfrun-67b0c1d8`、W9 `dwfrun-6cdbba53`、W11 `dwfrun-7d468cc0`、D-22 `dwfrun-daa0cd3f`、D-23 `dwfrun-580997b9` 全部 completed；W7 `dwfrun-808778a9` stopped（stop_reason=user）；W4 `dwfrun-c976a0e3` interrupted。这仅是历史记录，不证明核证时刻零在飞，也不把工具缺失当作无工作流存在。

## V2 · 正式 harness 是否保持记载版本

**核证通过：当前内容与所给基线一致，支持 W11 未应用至正式 harness。** 不据此推断文件从未被临时改动再还原。

被核对象 SHA256 = `517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636`，字节数 = `399508`。

本次在 Git Bash 实跑的完整命令：

```bash
sha256sum D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
wc -c D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
wc -l D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
stat D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
```

依次输出：SHA256 如上；`399508`；`7291`；stat 的 `Size: 399508`、`Modify: 2026-10-20 00:08:02.206731100 +0800`。命令批次退出码 0。其余 stat 字段：Blocks 392、IO Block 65536、regular file、Device 447770beh/1148678334d、Inode 11258999068517337、Links 1、Access mode 0755、Uid/Gid 197108；Access 时间 2026-11-06 07:13:08.317927700 +0800，Change 时间 2026-10-20 00:08:02.212207000 +0800，Birth 时间同 Modify。

与 `lead/PENDING_DECISIONS.md:81-83`、`W11_EXCEPT_FRESHNESS/W11_EXCEPT_FRESHNESS.md:16-19` 及 TASK.md:31 一致。7291 行由本次 `wc -l` 得出。

## V3 · W11 离线候选测试日志是否全绿

**日志核证通过：既有日志记录 14/14 全绿。未重跑测试，不声称本次重新运行测试通过。**

本次实跑：

```bash
wc -l D:/Project/ra2-campaign-forge/lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t3_test_out.txt
```

输出 `35`。随后用 Read 工具读取该绝对路径的第 33 行起、3 行，实际输出：

```text
33 OK
34 PASS=14 FAIL=0
35 EXIT=0
```

与 `lead/PENDING_DECISIONS.md:81` 及 TASK.md:32 一致。

## 差异与实跑产物

三项范围内未发现与 D-24 记载不一致的已核事实；V1 当前状态保持未验，不能将其算作已确认一致。

补充探针实跑命令：

```bash
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/D24_RULING/_d24_facts.py
```

退出码 0。探针只定点读取 harness 字节、mtime 与日志末三行；再次得到相同完整 SHA256、399508 字节、7291 个 LF、mtime `2026-10-20T00:08:02.206731+08:00`，以及 `V3_EXPECTED_TAIL_MATCH=True`。输出已保存至 `D:/Project/ra2-campaign-forge/lead/re_line_20261105/D24_RULING/_d24_facts_out.txt:1`；V2 字段在第 5–9 行，V3 在第 10–14 行。该补充探针不替代前述已执行的四条文件系统命令。

探针初稿两次被 Mimosa 写入钩拦截（命令注入告警）；最终稿去掉了 subprocess，仅使用标准库定点读文件后写入自身输出，成功运行。没有修改只读对象，没有启动游戏、采样或读取活进程内存，没有使用 Engine，没有 commit/push。
