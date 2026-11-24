# PROGRESS — NAMED_PUSH_S22_B3

逐行四环核完即落 `EVIDENCE/ROW_<entry>.txt`；每 5 行追加进度。

- [1–5 行] `006C2B10`(AircraftType)/`006C2C90`(InfantryType)/`006C2E10`(BulletType)/`006C2F90`(IsometricTileType)/`006C3110`(OverlayType)：均 TClassFactory<T>::slot3。② RTTI 钉住(slot#3)、C1 主虚表 slot0=00410260 成立(006C2C90 的 ctor 先写 edi 成员表 007EB6D4，主表是写 esi 的 007EB610，slot0=00410260，未踩小成员表陷阱)；③ QI HRESULT ③b② 成立；④ 活 COM 类对象(各自独立 alloc/ctor/CLSID/reg，host 006BB9A0 非 atexit 非析构)。四环齐全。EVIDENCE 落盘 5 份。
- [6–10 行] `006C3290`(SmudgeType)/`006C3410`(Unit)/`006C3590`(Building)/`006C3710`(Aircraft)/`006C3890`(Infantry)：前 3、末 1 四环齐全；**006C3710 FAIL**：对象主虚表 007E22A4 的 slot0=00414290（QI 包装器内含 ~AircraftClass 脏锚、返回 esi 无 HRESULT 三态），C1(主虚表 slot0≠00410260) 与 ③b(被调无可伪证 HRESULT 常量) 双 FAIL，不产出。EVIDENCE 落盘 10 份。
- [11–13 行] `006C3A10`(Anim)/`006C3B90`(AnimType) 四环齐全；**006C3D10 FAIL**：对象主虚表 007EAB58 的 slot0=005125A0（是结构同 00410260 的 HRESULT 三态 QI，但地址≠00410260），按本批 C1 硬约束判 ② FAIL、不产出（三维同构但非规范地址，登记待裁）。累计 EVIDENCE 13 份。

## 汇总

- rows_checked=13；② RTTI 13/13，② 含 C1(主虚表 slot0=00410260) **11/13**；③b 12/13；④ 13/13（④ 锚点全在 host 006BB9A0，host/fc atexit 均空，㉓ 排除、无锚落析构器）；四环齐全 **11/13 = 0.8462**。
- delta 产出 11 行（006C2B10 / 006C2C90 / 006C2E10 / 006C2F90 / 006C3110 / 006C3290 / 006C3410 / 006C3590 / 006C3890 / 006C3A10 / 006C3B90）。
- FAIL 2 行：006C3710（主虚表 slot0=00414290 + ③b 不可伪证 + ㉓ 脏锚）、006C3D10（主虚表 slot0=005125A0≠00410260）。
