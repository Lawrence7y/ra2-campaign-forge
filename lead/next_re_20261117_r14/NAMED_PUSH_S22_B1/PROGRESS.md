# PROGRESS — NAMED_PUSH_S22_B1

逐行四环核完即落 `EVIDENCE/ROW_<entry>.txt`；每 5 行追加进度。

- [1–5 行] `0069C9C0`/`0069CBC0`（Vector/DynamicVector<Wstring>::slot2）：② 钉住，③ FAIL（operator-new 空判断模板假句 + bool 返回，D-46(A)），④ 未计入；`006BF810`/`006BF990`/`006BFB10`/`006BFC90`/`006BFE10`（工厂 slot3）：①②③④ 全成立。EVIDENCE 落盘 5 份。
- [6–10 行] `006BFF90`/`006C0110`/`006C0290`/`006C0410`/`006C0590`（工厂 slot3）：② RTTI 钉住、③ QI HRESULT ③b② 成立、④ 活 COM 类对象成立（分配+ctor 装表+CLSID 注册，非 atexit 非析构），全部四环齐全。EVIDENCE 落盘 10 份。
- [11–15 行] `006C0710`/`006C0890`/`006C0A10`/`006C0B90`/`006C0D10`（工厂 slot3）：同上四环齐全。注意 `006C0A10`(SpawnManager) 对象 ctor `006B6EA0` 有两处 offset0 写表——首写 `mov [edi],0x7F36B4` 是成员子对象(edi=esi+0x38)，主表是末写 `mov [esi],0x7F3650`(esi=this)，其 slot0=0x410260 ⇒ ③b② 仍成立。EVIDENCE 落盘 15 份。
- [16–18 行] `006C0E90`（工厂 slot3）四环齐全；`0069C9C0`/`0069CBC0` 已在首批落盘。累计 EVIDENCE 18 份。

## 汇总

- rows_checked=18；② 18/18；③b 16/18（2 个 Vector slot2 不成立）；④ 16/18；四环齐全 16/18 = 0.8889。
- delta 产出 16 行（全部工厂 slot3）；`0069C9C0`/`0069CBC0` 不产出。
