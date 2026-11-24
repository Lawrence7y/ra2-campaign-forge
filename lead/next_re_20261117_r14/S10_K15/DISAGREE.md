# S10-K15 DISAGREE
1. 与派卡基线无数字分歧：现场 07:18:51 复算 S10 proved=114/526、named_L/S=513/526，与卡面一致。
2. 与合并表旧名有前缀分歧：006FB170/006FB470 当前 coverage 名为 AircraftClass::slot261/262；本卡按 RTTI COL+0xC→TD+8 实测六类共享同槽、无派生覆盖版直调，改归 TechnoClass 级。若合并策略要求保留旧名冲突，请登记 CONFLICTS，不改写本卡证据。
3. 与 K13/K14 结论无冲突：未碰 004D7330/004D85D0；006FB010 仍按 K13 的环①不足处理，没有借本批新行补环。
4. 与 K3/K5/K6/K8F/K9/K10/K12/K13 的禁区无交集：未扫 B8 imm32 C3 桩、QueueMission v[122]、九指令尾析构、Mission_* 桩、006FCDB0、004D8FB0 或 K12 四行。
5. R14-R17 自查：每行环③只用外部 vcall caller，环④只用盘面 [已证] 且本批外的 callee；两行没有互引，也没有把同一份 caller/callee 证据同时算成两环。
6. 环①/环④硬约束自查：引用的 0x414/0x418、+0x269、各 E8 目标都在目标函数体内或明示的外部 caller 位置出现；环④地址均在盘上 grade 第 5 列为 [已证]。