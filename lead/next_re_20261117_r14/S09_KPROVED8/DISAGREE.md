# S09-KPROVED8 · DISAGREE（分歧与只登记不裁事项）

本卡只做逆向取证与写域内交付，不改 coverage/台账/COMMON/CONFLICTS，故下列分歧**只登记不改盘**。

## D1 · 多表同 slot 的类归属（错源⑯）

- `006D0A20`（slot16）在 3 张 RTTI 持有表出现：`MouseClass`(vt7E1964) / `TabClass`(vt7EDFB4) / `ScrollClass`(vt7F1094)，全部 `vt[16]==entry`，TD+8 内联名逐表可读。
- `00565AA0`（slot22）在 8 张表出现：`MouseClass`(7E1964) / `DisplayClass`(7E6114) / `MapClass`(7ED404) / `TabClass`(7EDFB4) / `PowerClass`(7EFF54) / `RadarClass`(7F0344) / `ScrollClass`(7F1094) / `SidebarClass`(7F3058)，全部 slot22==entry、名逐表可读。
- 按错源⑯「同址多表同 slot ⇒ 归基类级」，二者应归其共同基类级；**但 name 栏保留 coverage 现值**（`MouseClass::slot16` / `MouseClass::slot22`），不在本卡改名（避免 §8.7 判据2「②类名与 name 栏不一致」自相矛盾，且改名属数据卫生不属本卡授权）。此类归属争议历史上由 CONFLICTS 只登记不裁（S09_KPROVED 的 004AAE90 等先例）。本卡不写 CONFLICTS.tsv（写域限制），仅在此登记。

## D2 · grade 升 `[已证]` 但 ④ 全走活 vt 而非 direct

- 本 8 行全 .text 重扫 direct E8 = 0（`work/final_verify.json` 的 ok4 全 0），④ 见证**全部**由 D-43(A) 宽读法活 vt 承担（构造器装活表 + vt[slot]==entry + 写点行外 + site 不共用，不要求真实派发点）。
- 这与 §8.6 条1「direct call 或活 vt 槽位」两形态并列一致，且 D-43(A) 已关闭「④是否瓶颈」立项（宽/严读法仅差 18 行）。但 audit 若按严读法（要求真实派发点）复核，本 8 行④ 会全部落空——此分歧按 RULING-R15 D-43(A) 已裁宽读法为准，不属未决。登记仅供复核透明。

## D3 · ③b 哨兵口径（005BDDC0 未选）

- `005BDDC0`（MouseClass::slot10）与已并入 proved 的 `005BDC80`（KPROVED6，slot19）结构同族（0x3039/0xd431 魔数、-1 状态哨兵）。KPROVED6 以「哨兵可证伪」按 ③b② 入表；本卡按 D-46(A) 窄读（只认 call 返回错误码、bool/状态哨兵不算）**未选**此行，改用 strict 行 `00771900`。
- 这是口径一致性分歧：历史上同类行已入表、本卡更严。只登记，不回退既有行。

## D4 · ③b 基率操作化的主观性

- 基率 strict/loose 的操作化由本卡 `work/base_rate.py` 自定（严格档只认 T1 跳表/T2 返回错误码/T4 带非栈写的循环；宽松档再加弱信号）。§8.6 条4 已指出「同一判据两种操作化判别力 0%~95.7%」，故两档并报、不单选一档当定论。本 8 行经手核均为硬 ③b，且在 strict K 集内；基率只作统计控制，不作「K=8×均值」式伪校验（判据3）。

无其它分歧。所有写入均在 `S09_KPROVED8\` 与 `_ghidra\S09_KPROVED8\` 内；未改共享文件。
