# W155 PROGRESS.md

| 时间 (Asia/Shanghai) | 做了什么 | 结论 / 下一步 |
|---|---|---|
| 2026-11-16T17:24:39 | 整份读 `R11_COMMON.md`(193 行) + `R12_FACTS.md`(55 行) | 底座已读；确认只写本卡目录、`-noanalysis`、双通道纪律 |
| 17:25:32 | 建卡目录；误在项目根建空 `work/`/`EVIDENCE/`（pwsh 相对路径），随即删除并正确建到卡目录 | 无污染；本卡写域已收敛 |
| 17:26 | 读 W122 三个可复用 Ghidra 脚本；grep 主台账 55B960/55B8F0/4666E0，读 §889 全文 | 已知 §889 记 W151 结论为 `[待复验]`；不重复引用未验数字 |
| 17:27 | `python work\scan_dispatch.py`：12,916 函数入口线性反汇编建 1,030,298 指令边界图；扫 `FF5x5C` 等模式 | 166 原始命中 / 129 边界命中（仅 atlas 覆盖区）；37 命中在 atlas 空洞，需定点证明 |
| 17:29 | `python work\analyze_candidates.py`：定点原始字节 + 从 0x55B880 扩展线性反汇编；候选排序 | `0x55B8F0` 是 nop 填充后的真实起点；`0x55B8C3` 在 `89 0c 86` 内；11 路阶梯浮现 |
| 17:30 | Lead 消息更正前提：把"0x55B8F0 已被否决"当未定、要求自证 | 已用自有字节证据独立判定（见上条），未引用 Lead 消息作依据 |
| 17:31 | `python work\dump_dispatch.py`：0x55B8F0 全函数反汇编 + 11 块自动解析 + 调用者扫描 | 11 块逐项映射到 instance_arrays.tsv；字节通道调用者=0 |
| 17:32 | `python work\caller_bytes_raw.py`：全 `.text` `E8 rel32` 扫描 + 全文件 dword 指针扫描 | `0x55B8F0`/`0x55B960` 均 0 命中；对照 0x4666E0=1 证明扫描有效 |
| 17:33 | Ghidra `W155All.java`（3 次编译修正后 run，exit=0） | `0x55B8F0/0x55B960` 无函数、无引用；`0x55AFB0` 由 `0x55D360` 每帧直接调用；33 callee 确认 |
| 17:34 | `python work\bullet_loops.py` + `bullet_closure.py`；Ghidra `W155Branches.java`（修正大小写后 run，exit=0） | 双通道一致：Bullet 2 回边、6/33 callee 有回边、W151 "全 nback=0" 错；闭包 303/15 Count 引用 |
| 17:35 | 写 `DISPATCH_SITE.md` / `PROGRESS.md` / `UNKNOWNS.md` / `DISAGREE.md` | 交付完成；下一步由 Lead 决定是否复核 LEAD_AUDIT 条目 |

> 注：Ghidra 两次成功运行均 `-noanalysis`，未复制/覆盖预置项目；无 `git commit/push`。
