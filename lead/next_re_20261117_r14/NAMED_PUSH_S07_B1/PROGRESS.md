# PROGRESS — NAMED_PUSH_S07_B1

- [1–5 行] 00421730(AlphaShapeClass::vslot8): ②P ③P ④P 四环齐全; 00435BE0(BuildingLightClass::vslot69): ②P ③F ④P 不产出; 004361D0(BuildingLightClass::vslot23): ②P ③F ④P 不产出; 004370C0(BuildingLightClass::vslot8): ②P ③P ④P 四环齐全; 00491210(ConvertClass::slot0): ②P ③P ④P 四环齐全
- [6–10 行] 004BAD80(DSurface::slot23): ②P ③F ④P 不产出; 004BB0D0(DSurface::slot3): ②P ③F ④P 不产出; 004BB620(DSurface::slot4): ②P ③F ④P 不产出; 004BB830(DSurface::slot7): ②P ③F ④P 不产出; 004BF750(DSurface::slot36): ②P ③F ④P 不产出
- [11–15 行] 004C0750(DSurface::slot19): ②P ③F ④P 不产出; 004C0E30(DSurface::slot20): ②P ③F ④P 不产出; 005550C0(LightSourceClass::slot5): ②P ③P ④P 四环齐全; 00555110(LightSourceClass::slot6): ②P ③P ④P 四环齐全; 00555150(LightSourceClass::slot8): ②P ③P ④P 四环齐全
- [16–18 行] 00565C10(DisplayClass::slot28): ②P ③F ④P 不产出; 00567230(DisplayClass::slot29): ②P ③F ④P 不产出; 006DBD20(Tactical::slot5): ②P ③P ④P 四环齐全

- 汇总: rows_checked=18；②=18；③b=7；④=18；四环齐全=7 (0.3889)
- 三陷阱逐行核过：①读写方向(2 条流读入 005550C0/006DBD20、1 条流写出 00555110 逐字节核定未写反)；②④锚落析构器(④ 全取行外 ctor 装表，体内析构自装表按㉓排除)；③小成员表(ConvertClass 007E5318/007E5338 容器表排除，全取对象主表)。
