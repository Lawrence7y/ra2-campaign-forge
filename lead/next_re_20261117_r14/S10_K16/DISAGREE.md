# S10-K16 DISAGREE
1. 与派卡数字无分歧：现场 07:43:09 复算 S10 proved=114/526、named_L/S=513/526，与卡面一致。
2. 与 coverage 旧名有归属分歧：00701410/0070B570/006F4EB0 当前盘面名为 AircraftClass::slot259/263/264；本卡按 RTTI COL+0xC→TD+8 实测六类同槽共享、无派生覆盖版，改归 TechnoClass 级。若合并需要保留 conflict，请登记 CONFLICTS，本卡不改写共享表。
3. 与 K15 无冲突：006FB170/006FB470 未碰；006FB740 仍按 K15 的“内部 stage 无外部枚举”处理，未借本批新行补证。
4. 与 K13/K14/K3/K5/K6/K8F/K9/K12 禁区无交集：未碰 004D7330/004D85D0/006FCDB0、B8 imm32 C3 桩、QueueMission v[122]、析构族、Mission_* 桩或 K12 四行。
5. R14-R17 自查：00701410 的外部比较与 vcall 只计一环；0070B570 与 006F4EB0 的 006F9E50 门控/调用各只在本行计一环；环④ callee 均在 batch 外且 grade 第 5 列 [已证]。
6. 环①/④硬约束自查：引用地址在 body 或明示外部 caller 位置真出现；三行环④ call 目标计数分别为 1/1/2，盘面 grade 均 [已证]。
