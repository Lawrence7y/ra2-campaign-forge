# S10-K6 DISAGREE
| # | 对象 | 本卡处置 | 依据 |
|---|---|---|---|
| D1 | K4 19 行 Mission_* 名称 | 不重交、不借 id→名表升级；仍按单源 [静态推断] 处理。 | S10_K4/_audit/VERDICT.md 必审2；本卡新名用数字 id+字段/条件。 |
| D2 | K5 7 行已交付但未入盘 | 不触碰、不重复计入；基线按现场 92。 | EVIDENCE/baseline_recompute.txt、delta_validate.txt；coverage mtime 04:05:20+08。 |
| D3 | K4 把 EVA/Tip/TXT 串称“共享尾引用” | 对本卡无冲突：那些串若单独使用仍不升；本卡改走 QueueMission 四环。 | EVIDENCE/string_candidates_disasm.txt、QUEUE_MISSION_S10_PROOFS.txt。 |
| D4 | vtable slot 归属 | 仅用于定位与类名，绝不作为语义或命名证据。 | 新名全部含数字 mission id + 字段/门控行为。 |
| D5 | 004DFA70/00521760 字段写环来源 | 如实注明为 QueueMission 被调写 [B4]/[B8]，不是函数自身写；保守审计可删除。 | UNKNOWNS U7。 |
| D6 | 门槛与百分比 | 用现场 526 分母与 ceil(526/2)=263，不沿用卡面 513/257。 | baseline_recompute.txt。 |
