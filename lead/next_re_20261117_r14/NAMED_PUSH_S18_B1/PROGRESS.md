# NAMED-PUSH S18 B1 — PROGRESS

- 批次 B1 = S18 中 `p3b2_named==True` 的行按 entry 升序取前 18，输出目录 `NAMED_PUSH_S18_B1\`。
- 判据：D-40 四环，②与④须独立证据链；③只认③b；宁严不宽。
- 目标只读，SHA-256 现场一致；capstone 5.0.7 skipdata=True；pefile 2024.8.26。
- 骨架/delta 表头/base_rate 骨架开工先落；随后逐行核、逐行落盘 EVIDENCE。
- 计数口径：核完行 / ②钉住行 / 四环齐全（严格 D-40）。

## 进度（每 5 行追加）

### checkpoint @ 5 行（0048BF40 … 004A0630）
- [x] 5 / 18 已核；5 份 EVIDENCE 落盘。
- 观察：5 行 ② 全部钉住（ConnectionClass/ConnectionPointClass 的 RTTI vtable 槽，slot offset/4=线索槽号）；与 S04「② 全灭」形成对照。③ 全部不成立：0048BF40/0048C3B0 bool 0/1 主输出(D-46(A))+纯转发壳，0048C040/0048C320 被调返回源 unknown，004A0630 p3=0。④ 均有活虚表派发链（构造安装点，非 atexit）。
- 四环齐全累计：0。

### checkpoint @ 10 行（… 005414C0）
- [x] 10 / 18 已核；10 份 EVIDENCE 落盘。
- 关键：005414C0 (IPXManagerClass::slot2) 四环齐全 —— ③b② 为 call [edx+0x18]@0x0054159B → cmp eax,-1@0x0054159E → je@0x005415A1，被调 0x00541040 确实 `mov eax,0xffffffff;ret`（失败 -1，非 bool），失败路 inc [esi+0xA0](非栈写)+ret 0，成功路查表+call [eax+8] 实发送+ret 1，动作真不同；② vt 007EC16C+08 RTTI .?AVIPXManagerClass@@；④ 活表安装点 005408F7(mov [esi],0x7EC16C 已字节复核)/005409FA。这是本批第一条可升 [已证] 的行。
- 0053FCB0(p3=0)、0053FF10/0053FFA0(被调 unknown)、00540050(bool) ③ 均 FAIL。
- 四环齐全累计：1。

### checkpoint @ 15 行（… 005C1A10）
- [x] 15 / 18 已核；15 份 EVIDENCE 落盘。
- 观察：00541820（大函数 6 站点全为 null/bool 探测、无可伪证错误码）、00542350/005423C0（getter 纯转发 ③a）③ FAIL；005C18A0/005C1DC0（malloc+对象初始化模板假句）、005C1A10（被调 0x775940 bool / 0x7CD680 未知）③ FAIL。② 全部钉住，④ 全部有活虚表派发链。
- 四环齐全累计：1。

### 收尾（16–18 行 + 咽喉复核）
- [x] 18 / 18 已核；18 份 EVIDENCE 落盘。
- [x] 咽喉复核：
  - 005414C0 的 ④ 构造安装点 005408F7 反汇编确认 `mov dword ptr [esi],0x7EC16C` (C7 06 6C C1 7E 00)，真实活表安装、非 atexit；④ 与 ②（.data RTTI 链）不同源成立。
  - 005C2100/005C2680 被调 0x5E26C0/0x49BC80 返回源=(call)/unknown，无可伪证 imm 错误码；005C2680 两路同含 call 0x0049C2C0（多路同一 call 细则#1）。③ FAIL。
  - 全 18 行 slot offset/4 == 线索槽号，② 与名字一致，非仅凭 slotN 类名。
- [x] delta 1 行（005414C0），base_rate、REPORT 定稿。

## 最终计数
- rows_checked = **18**
- ring2_ok（②钉住） = **18**
- ring3b_ok（③b②成立） = **1**
- ring4_ok（活虚表派发/真实调用者） = **18**
- all_four_rings（严格 D-40） = **1**
- delta 行数 = **1**
