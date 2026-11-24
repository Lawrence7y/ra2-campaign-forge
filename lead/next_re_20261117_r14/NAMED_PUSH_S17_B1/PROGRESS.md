# NAMED-PUSH S17 B1 — PROGRESS

- 批次 B1 = S17 中 `p3b2_named==True` 且名字非 `fn_`/`sub_` 伪名的全部候选（共 6 行，无伪名 ⇒ 全取），输出目录 `NAMED_PUSH_S17_B1\`。
- 判据：D-40 四环，②与④须独立证据链；③只认③b；宁严不宽（S17 已过门槛，本批只为补覆盖，不为凑数放宽）。
- 目标只读，SHA-256 现场一致；capstone 5.0.7 skipdata=True；pefile 2024.8.26；核验脚本落 work/ 可复算。
- 计数口径：rows_checked / ②钉住行 / ③b成立行 / ④成立行 / 四环齐全行。

## 进度（每 5 行追加）

### checkpoint @ 5 行（004A2B60 … 006BEF10）
- [x] 5 / 6 已核；5 份 EVIDENCE 落盘。
- 004A2B60(CStreamClass::slot3)：② 钉住(.?AVCStreamClass@@ slot#3)，④ PASS(构造器 004A285E)，但 ③ FAIL——两处被检 call 均为 `call [ecx+0xc]` 未钉虚调用，被调返回约定无法从字节伪证。非四环。
- 004A2CD0(CStreamClass::slot4)：② 钉住(slot#4)，③ PASS(③b②：两处直接 `call 0x4A3020`，被调 004A3089/004A30CD 返 0x80004005，jl 分支两路动作不同)，④ PASS(004A285E)。**本批第 1 条四环齐全**。
- 00539AE0(Load_StreamFields)：自由函数，dword_refs=0 ⇒ ② 物理不可得；③ 全 20 站点未钉虚调用 FAIL；④ direct-only FAIL。非四环。
- 0055AAC0(Load_SwizzledObject)：自由函数，dword_refs=0 ⇒ ② FAIL；③ 单站点未钉虚调用 FAIL；④ direct-only FAIL。非四环。
- 006BEF10(TClassFactory<VCStreamClass>::slot3)：② 钉住，③ PASS(③b②：006BEF6A `call [eax]` 经构造器装主表 007E5DAC slot0 钉死为 004A2990 QueryInterface，004A2999/004A2A02 E_POINTER/E_NOINTERFACE 可伪证，jge 分支 Release/保留两路不同)，④ PASS(006BEE49)。**本批第 2 条四环齐全**。
- 四环齐全累计：2。

### 收尾（第 6 行 + 咽喉复核）
- [x] 6 / 6 已核；6 份 EVIDENCE 落盘。
- 006BF690(TClassFactory<SuperClass>::slot3)：② 钉住，③ PASS(③b②：006BF6ED `call [eax]` 经构造器 0x6CAEC0 装主表 007F3FE8 slot0 钉死为 00410260 QueryInterface——符合主表 slot0 常见 00410260，00410269/004102E6 E_POINTER/E_NOINTERFACE 可伪证，jge 分支 Release/保留两路不同)，④ PASS(006BF5C9)。**本批第 3 条四环齐全**。
- [x] 咽喉复核：
  - **㉓ 析构器陷阱**：枚举三条主虚表全部写点——007E5DAC: 004A285E(004A2820 构造器)/004A2889(004A2880 删除析构器)/004A3119(004A3110 删除析构器)；007F3768: 仅 006BEE49(构造器)；007F37E0: 仅 006BF5C9(构造器)。排除删除析构器与 atexit 注册(三处 atexit_sites=[])，④ 锚点全部落构造器，无落析构器者。
  - **小成员表陷阱**：004A2820 同时装主表 [esi]=007E5DAC 与副表 [esi+4]=007E5D94；006BEF10 QI 站点取 [esi]=007E5DAC 主表 slot0=004A2990（非副表 004A3220）；006BF690 QI 站点取 [esi]=007F3FE8 主表 slot0=00410260，均与「主表 slot0 常见 00410260」一致。
  - **读写方向**：② 读 .rdata 槽/COL/TD 数据；④ 读 .text 构造安装指令；③ 读被调返回常量，方向未反。
  - **RTTI 技术条**：pTD/pCHD 按绝对 VA 解析(如 0081FC30/00840F68/00841068)，TD+8 作内联串直读，均非 RVA/指针。
  - **③ 可伪证性**：三成立行失败返回均为多值 HRESULT(0x80004005 / E_POINTER+E_NOINTERFACE)，非 {0,1} 布尔。
  - **eax 覆写/多路同一 call/模板假句**：逐行排查，四环成立行均无覆写、无同 call 仅差参数、无初始化模板假句。
- [x] delta 3 行，base_rate、REPORT 定稿；残留骨架 REPORT 已整体重写，交付中无任何未完成状态残留。

## 最终计数
- rows_checked = **6**
- ring2_ok（②钉住） = **4**（004A2B60/004A2CD0/006BEF10/006BF690）
- ring3b_ok（③b成立） = **3**（004A2CD0/006BEF10/006BF690）
- ring4_ok（④成立） = **4**（004A2B60/004A2CD0/006BEF10/006BF690）
- all_four_rings（严格 D-40） = **3**
- rate = 3/6 = **0.5000**
- delta 行数 = **3**
