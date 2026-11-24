# W161 进度日志（append-only）

- **2026-11-16 18:45** 开工。整份读完 `R11_COMMON.md`（193 行）与 `R12_FACTS.md`（182 行，§6–9 重点）。确认纪律：不用 Ghidra、capstone 必须 skipdata=True、双通道且≥1 通道不依赖 function_atlas entry+size、字节命中先验指令边界、禁 p 值/CI/显著、写"新发现"前 grep 主台账。
- **18:46** 环境核验：python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；目标 exe SHA-256 逐值吻合 `73201CC0…F67476`。建 `work\`、`EVIDENCE\`。
- **18:47** 读 `_lead_audit\audit_lib.py` 仅学写法（VA 寻址、skipdata、boundary_check、full-sweep），未 import / 未改。grep 主台账 `GOAL_THREE_TARGETS_20261018.md` 的 `0x114|Draw|0x7E46E4|0x4666E0`：命中 §889-2（槽表未复核）、§889-5（303 函数闭包 / 0.65 高 1–2 数量级猜想）、line 18103（BulletClass::Draw 0x468090）、line 5800（0x8A0394=ObjectsInLayers）、line 6813（0x6D8DB0 分层 DrawIfVisible）。
- **18:49** 写 `work\w161_lib.py`（自研 Bin/md32/linear_from/boundary_check/load_atlas/load_calledges/sweep_full_text/sweep_disps_to/insn_stats）。sanity：0x4666E0=1794 指令/816 访存/2 回边（0x466764→0x46674E, 0x4678F6→0x467879），与 R12_FACTS §6.1 逐值吻合。
- **18:51** Q1：`w161_q1_closure.py` 双通道 BFS 深度 1–4。全 .text 扫 1,394,120 指令/66 跳字节（与 §6.2 真值吻合）。通道 A（Ghidra）=303 函数/32,628 指令；通道 B（字节）=422 函数/45,610 指令；深度 1 两通道均 33 callee。→ `EVIDENCE/Q1_closure.json`。
- **18:52** Q1 换算：`w161_q1_time.py`。AI 本体 0.60–7.18 µs；最保守全闭包 B + 1 GHz + CPI4 = 182.44 µs，仍比 650 µs 小 3.6×。结论：更新代码非主因（判据满足）。
- **18:53** Q2.1：`w161_q2_vtable.py` dump 0x7E46E4 的 126 槽，125 非空槽与 `vtable_members.tsv` 0 差异；槽 69=`0x468090`(923 B/277 指令)、槽 65=`0x5F4B10`、槽 23=`0x4666E0`、槽 11=`mov eax,8`。
- **18:54** Q2.1b：`w161_q2_draw.py` 深挖候选槽 callee。槽 69 有多处 surface 虚表间接调用 + `0x4AED70`(1317 B) 绘制助手。
- **18:55** Q2.1c/2.2：`w161_q2_render.py` 全反汇编 DrawIfVisible(0x5F4B10)，确认 **0x5F4CFD `ff 90 14 01 00 00`=`call [eax+0x114]`**（boundary_check=True）⇒ 槽 69=Draw 由调用链证实。修正首版扫描 bug（0x114>255 需 disp32 而非 disp8）；子弹容器绝对引用：0xA8ED40=4 / 0xA8ED44=10 / 0xA8ED50=15 处，全在 ctor/dtor/init/移除器/SYNC/调试函数。
- **18:56** Q2.2：`w161_q2_render2.py` 正确扫描 call[reg+0x114]（6 处）/call[reg+0x104]（7 处）全边界有效；5 个 DrawIfVisible 槽调用在 0x6D8DB0 渲染簇。子弹容器函数无一调 Draw。
- **18:57** Q2.2b：`w161_q2_cluster.py` 确认 0x6D8DB0 按 MapClass::ObjectsInLayers 分层（层基 0x8A0364/计数 0x8A0370/stride 0x18）+ 视口裁剪后调 DrawIfVisible。台账 line 5800 佐证 0x8A0394=Layer2.Items。**没有"遍历子弹数组 + Draw"的循环**；"每发都画"静态不成立。
- **18:58** Q3：`w161_q3_resolvability.py`（输入已发布数字，不重算回归）。局部斜率 0.040–1.036（26×）；子区间拟合 0.53/0.71/0.94；噪声/量子/台阶带宽 0.113/0.164/0.264 ms/发；占空比 2.59%/发；压缩修正高端 1.19–1.90。结论：0.65 是不可分辨的聚合量，非上界（高端真值更大）。
- **19:00** 写交付：`BULLET_COST_ATTRIB.md`（5 行摘要 + Q1–Q4 + LEAD_AUDIT）、本 `PROGRESS.md`、`UNKNOWNS.md`、`DISAGREE.md`。核心数字复核（槽69原始字节、闭包累计、回边）已记入 LEAD_AUDIT。

**结论一句话**：0.65 ms/发 不是真实每发 CPU 成本（更新代码小 1.5–3 数量级）、不是干净上界（量化压缩使高端真值更大），应作不可分辨的帧台阶聚合量；最有区分力的下一步是"分帧时长直方图"与"战斗态 EIP 采样"。
