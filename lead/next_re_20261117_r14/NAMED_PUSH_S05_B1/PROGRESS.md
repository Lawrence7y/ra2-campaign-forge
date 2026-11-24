# NAMED-PUSH S05 B1 — PROGRESS

- 批次 B1 = S05 中 `p3b2_named==True` 的行按 entry 升序取前 18，输出目录 `NAMED_PUSH_S05_B1\`。
- 判据：D-40 四环，②与④须独立证据链；③只认③b；宁严不宽，虚报不可接受。
- 目标只读，SHA-256 现场一致；capstone 5.0.7 skipdata=True；pefile 2024.8.26。
- 骨架/delta 表头/base_rate 骨架开工先落；随后逐行核、逐行落盘 EVIDENCE。
- 计数口径：核完行 / ②钉住行 / ③b成立行 / ④成立行 / 四环齐全行。

## 进度（每 5 行追加）

### checkpoint @ 5 行（00410380 … 004176F0）
- [x] 5 / 18 已核；5 份 EVIDENCE 落盘。
- 观察：00410380（AbstractClass）无虚表槽/RTTI，② FAIL（全镜像 4B VA 0 命中），direct 42 但 direct-only 不足 -> 不成立。00410C30 ② 钉住（.?AVAbstractTypeClass@@ slot8），③b② 成立（call [edx+0x10]→cmp eax,-1→je，两路动作真不同+数组前移非栈写），④ 活 vt 派发 -> 第一条可升 [已证]。00414290 ② 钉住（.?AVAircraftClass@@ slot0），③b② 成立（call 0x410260 QueryInterface HRESULT {0,80004002,80004003}→test/jge，两路真不同），④ 活 vt -> 第二条 [已证]。00414BB0/004176F0 ② 钉住但 ③ FAIL（间接/malloc/unknown 返回，跳表仅 2/3 目标）。
- 累计：② 钉住 4；③b 成立 2；④ 成立 4；四环齐全 2。

### checkpoint @ 10 行（… 0041AA80）
- [x] 10 / 18 已核；10 份 EVIDENCE 落盘。
- 观察：00417CC0（p3=0，10 处 call->test 无可伪证常量）、004190B0（被调 0x4D8FB0 返回枚举 {0xA,0x14} 非错误码；双跳表大型状态机）、004196B0（p3=0）、0041A9E0（被调 0x6FC0B0 串比较族返回 {0}，TEST_EAX jne 布尔探测）、0041AA80（CMP_IMM imm=1 布尔态 + 间接/unknown 返回）——5 行 ② 全钉住（其中 004190B0/004196B0/0041A9E0/0041AA80 槽号 101/107/240/288 由扩展回扫 kmax=400 钉死），③ 全 FAIL，④ 全有活 vt 派发。
- 累计：② 钉住 9；③b 成立 2；④ 成立 9；四环齐全 2。

### checkpoint @ 15 行（… 0041CE90）
- [x] 15 / 18 已核；15 份 EVIDENCE 落盘。
- 观察：0041B890（p3=0 小函数）、0041BBD0（被调 vt[0x278]=0x65AAA0 返回 unknown，cmp eax,1 布尔 getter/缓存刷新）、0041CB20（malloc+构造模板假句）、0041CC20（被调 0x528A10 返回 {0} 空判+对象初始化模板假句）、0041CE20/0041CE90（p3=0 极小函数）——② 全钉住，③ 全 FAIL，④ 全有活 vt 派发。
- 累计：② 钉住 14；③b 成立 2；④ 成立 14；四环齐全 2。

### 收尾（16–18 行 + 咽喉复核）
- [x] 18 / 18 已核；18 份 EVIDENCE 落盘。
- [x] 0041CFE0（AircraftTypeClass::vslot8）③b② 成立：call [edx+0x10]@0x0041D01A→cmp eax,-1@0x0041D01D→je@0x0041D020，与 00410C30 同构但地址/全局对象/槽均独立（0xA8B218 / vt 007E2868 slot8 槽 007E2888）；④ 构造安装点 0041C900/0041CE44/0041CFE6。第三条 [已证]。
- [x] 00450630（fn_）② FAIL：无虚表槽/RTTI，direct 1（004401B6）direct-only 不足 -> 不成立。
- [x] 咽喉复核：
  - 3 条 [已证] 的 cmp/test 与 jcc 之间均 0 处 eax 覆写（analysis.json chA_eax_trap=0）；
  - 00414290 被调 0x00410260 完整反汇编确认 E_POINTER(0x80004003)/E_NOINTERFACE(0x80004002)/S_OK(0) 三态 HRESULT 返回；
  - 00410C30/0041CFE0 全局对象指针 0xA8E968/0xA8B218 落在 .data 未初始化区(VirtualSize>RawSize)静态不可读，可伪证性由调用点 cmp eax,-1 哨兵提供（D-40 call_site_cmp 形态，与 S18 已过审 005414C0 同法）；
  - 16 行 slot offset/4 == 名字线索槽号，② 非仅凭 slotN 类名。
- [x] delta 3 行（00410C30/00414290/0041CFE0），base_rate、REPORT 定稿。

## 最终计数
- rows_checked = **18**
- ring2_ok（②钉住） = **16**
- ring3b_ok（③b成立） = **3**
- ring4_ok（活虚表派发/真实调用者） = **16**
- all_four_rings（严格 D-40） = **3**
- delta 行数 = **3**
