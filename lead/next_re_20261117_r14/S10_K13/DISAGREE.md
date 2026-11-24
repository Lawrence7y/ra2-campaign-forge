# S10-K13 DISAGREE
1. 与派卡现状无数字分歧：现场 06:32:17 复算 S10 proved=113/526、named_L=513/526，与卡面一致。
2. 与 R14-R17 无冲突：每行环③使用外部 caller、环④使用本批外且盘面 [已证] 的 callee；006FB010 因环①不足主动退出，不用同批互引补环。
3. 与 K10/K12 无 entry 重叠：未碰 006FCDB0、004D8FB0、0051D6F0、0051DAF0、0051B1F0、00522340，也未重扫 K3 的 B8 imm32 C3 桩与 K6/K8 的 QueueMission 家族。
4. 004D85D0/004D7330 在 coverage 中现名分别为 AircraftClass::slot99/FootClass::slot91；本卡以行为证据覆盖，合并员如判 name 冲突请登记 CONFLICTS 而非改写本卡证据。
