# NAMED-PUSH S06 B3 进度

初始：目录已建、REPORT 骨架已写、筛选得 10 行（#37–#46，S06 named 共 46，取 37–54 落到 37–46）。

## 已核 #37–#41

- #37 0071E1D0 TerrainTypeClass::slot5：①PASS ②PASS ③PASS(流读入) ④PASS ⇒ 产出[已证]
- #38 0071E240 TerrainTypeClass::slot6：①PASS ②PASS ③FAIL(薄转发) ④PASS ⇒ 不产出
- #39 0071E360 TerrainTypeClass::slot8：①PASS ②PASS ③FAIL(间接调用) ④PASS ⇒ 不产出
- #40 007220A0 TiberiumClass::slot7：①PASS ②PASS ③PASS(取指针非流IO) ④PASS ⇒ 产出[已证]
- #41 007220D0 TiberiumClass::slot6：①PASS ②PASS ③PASS(流写出) ④PASS ⇒ 产出[已证]

## 已核 #42–#46

- #42 007281A0 TubeClass::slot5：①PASS ②PASS ③PASS(流读入) ④PASS ⇒ 产出[已证]
- #43 007281E0 TubeClass::slot6：①PASS ②PASS ③FAIL(薄转发) ④PASS ⇒ 不产出
- #44 00728710 TubeClass::slot8：①PASS ②PASS ③FAIL(间接调用) ④PASS ⇒ 不产出
- #45 00763D90 WaypointPathClass::slot6：①PASS ②PASS ③PASS(流写出) ④PASS ⇒ 产出[已证]
- #46 00763E20 WaypointPathClass::slot8：①PASS ②PASS ③FAIL(间接调用) ④PASS ⇒ 不产出

