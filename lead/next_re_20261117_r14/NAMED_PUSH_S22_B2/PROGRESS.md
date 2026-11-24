# PROGRESS — NAMED_PUSH_S22_B2

逐行四环核完即落 `EVIDENCE/ROW_<entry>.txt`；每 5 行追加进度。

- [1–5 行] `006C1010`(Parasite)/`006C1190`(Bomb)/`006C1310`(RadSite)/`006C1490`(TEvent)/`006C1610`(VoxelAnimType)：均为 TClassFactory<T>::slot3，② RTTI 钉住(slot#3)、③ QI HRESULT ③b② 成立(0x410260,{0,80004002,80004003},3ret)、④ 活 COM 类对象(各自独立 alloc/ctor/CLSID/reg，宿主 006BB9A0 非 atexit 非析构)——四环齐全。EVIDENCE 落盘 5 份。
- [6–10 行] `006C1790`(VoxelAnim)/`006C1910`(TAction)/`006C1A90`(Trigger)/`006C1C10`(TriggerType)/`006C1D90`(Script)：同上四环齐全。`006C1790` 对象 ctor 有两处 offset0 写表，主表取写 this 的那处(vt 007F6318, slot0=0x410260)。EVIDENCE 落盘 10 份。
- [11–15 行] `006C1F10`(ScriptType)/`006C2090`(Tag)/`006C2210`(TagType)/`006C2390`(Team)/`006C2510`(TeamType)：同上四环齐全，每行 CLSID 与注册 call 地址各自独立。EVIDENCE 落盘 15 份。
- [16–18 行] `006C2690`(TaskForce)/`006C2810`(UnitType)/`006C2990`(BuildingType)：同上四环齐全。`006C2810` 对象 ctor 两处 offset0 写表，主表 slot0=0x410260。累计 EVIDENCE 18 份。

## 汇总

- rows_checked=18；② 18/18；③b 18/18（全为 TClassFactory QI HRESULT ③b②）；④ 18/18（活 COM 类对象，非 atexit 非析构、非 direct-only）；四环齐全 18/18 = 1.0000。
- delta 产出 18 行（全部工厂 slot3）；无 fail 行。
