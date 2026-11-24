# SUMMARY — C3-44 真名撞车裁决

口径：只按 E1>E2>E3>E4 与来源卡裁决（PASS>PARTIAL>无>FAIL）判名字；P2 按特别处理，真名侧胜；不改共享表。

总计 44；winner：cov=24，other=14，deadlock=6。
形态：P1=0，P2=15，P3=22，P4=7。
misclassified=P2：15 条。
胜者一侧已有 PASS/PARTIAL 审计（可机械落地）：38 条。

## deadlock 清单（同档同裁决，需人看）
- 004664C0 BulletClass::BulletClass <> BulletClass::Construct（P4，E=E2/E2，裁决=PARTIAL/PARTIAL）：cov(C02 self_known)与other(YRpp JMP_THIS Construct)同为E2，两侧卡均PARTIAL；同档同裁决，不裁。
- 00489280 MapClass::MapClass <> DamageArea（P3，E=E2/E2，裁决=PARTIAL/PARTIAL）：cov(self_known)与other(YRpp JMP_STD DamageArea)同为E2，两侧卡均PARTIAL；同档同裁决，不裁。
- 004C6970 NetworkEvents::FillEvent_ProduceAbandonSuspend <> FillEvent_Produce;FillEvent_ProduceAbandonSuspend（P3，E=E2/E2，裁决=PARTIAL/PARTIAL）：cov与S18侧均为YRpp/kb外部地址名E2，两侧卡均PARTIAL；同档同裁决，不裁。
- 0055D360 MainLoop::PerFrameUpdate <> MainLogicFrame;SortLayer2（P3，E=E3/E3，裁决=PARTIAL/PARTIAL）：PerFrameUpdate与MainLogicFrame/SortLayer2均由函数体/主循环行为推断(E3)，两侧卡均PARTIAL；同档同裁决，不裁。
- 005678E0 MapClass::MapClass <> MapClass::RevealArea2（P3，E=E2/E2，裁决=PARTIAL/PARTIAL）：cov(self_known)与other(YRpp JMP_THIS RevealArea2)同为E2，两侧卡均PARTIAL；同档同裁决，不裁。
- 006CBCA0 SuperClass::changed <> SuperClass::HasChargeProgressed（P4，E=E2/E2，裁决=PARTIAL/PARTIAL）：cov(kb名changed)与other(YRpp JMP_THIS HasChargeProgressed)同为E2，两侧卡均PARTIAL；同档同裁决，不裁。

证据只引用 `C3_ADJ/DECISIONS.tsv` 已列路径、COVERAGE 行、以及盘上来源卡 `_audit/VERDICT.md`；无证据一律 E5。
