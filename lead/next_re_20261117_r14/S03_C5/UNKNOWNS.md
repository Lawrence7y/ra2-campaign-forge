# S03-C5 UNKNOWNS

## U1 · 00431F10 `CDFileClass::vslot5` — ③ 环不成立（③a）
- ① 入口成立（16B 对齐、被 29 个 E8 站点直调）；② 成立（vt 0x7E1668 slot5 `.?AVCDFileClass@@`，共享 BufferIOFileClass 链，RTTI 链读通）；④ 成立（29 direct 站点，双通道一致）。
- ③ 失败：函数体仅 8 条指令、CFG extent 0x16 B。`+0x00 mov al,[ecx+0x29]` / `+0x03 test` / `+0x05 je +0xC` / `+0x07 mov al,1` / `+0x09 ret 4` / `+0xC push 0` / `+0xE call 0x65CBF0` / `+0x13 ret 4`。只是「标志 getter + 单调用回退」，线性、无多路闸、无循环、无错误码返回约定、无形状断言 => D-42 ③a。
- 处置：不进 delta、不升 `[已证]`，保留盘上 grade。若要升须另有结论本身的字节证据（§8.1 ⑬）。

## U2 · 00473AE0 `CCFileClass::slot12` — ③ 环不成立（③a 薄壳）
- ①/②/④ 均成立（vt 0x7E16B0 slot12 `.?AVCCFileClass@@`；11 direct 站点）。
- ③ 失败：22 指令、0x30 B。仅 `+0x08` 一道 NULL 闸 + `+0x17 call [vptr+0x40]` 报错误码 0xd + `+0x27 call 0x432050` 一次委托；薄壳包装，无合同闭合判据（D-42 ③a「纯转发桩/单次调用」）。不进 delta。

## U3 · 0047AF10 `CDFileClass::slot8` — ③ 环不成立（③a）
- ①/②/④ 均成立（vt 0x7E1668 slot8 `.?AVCDFileClass@@`；21 direct 站点）。
- ③ 失败：42 指令、0x59 B。`+0x0E test ebx`/`+0x10 jne` 单错误闸；`+0x24 test al`/`+0x26 jne` 与 `+0x28 cmp edi,2`/`+0x2B je` **两条件汇合到同一目标 0x47AF53**（逻辑 OR，非互斥多路），只形成 2 路委托。未达 D-42 细则#1「≥3 道互斥闸且各闸动作不同」，无循环/跳表/返回约定 => ③a。不进 delta。

## U4 · 基线池 N=102 而非 104（盘面自证）
- coverage.tsv 现态 S03 `[静态推断]` = 104 行（17→24 `[已证]` 系上卡 C4 并入 7 行）；但其中 2 行在 SURVEY_RING24 classification.tsv 无 CFG extent（ext_lo/ext_hi 空），无法反汇编测 ③b。基线池按「有 extent 的 S03 `[静态推断]`」= 102 行。两档基线均用 N=102。未改盘面。

## U5 · ④ livevt 全条款不适用（口径声明，非缺口）
- 本卡 8 行 ④ **全部**为 direct-call（E8 边界 + site+5+rel32==entry + 体外 + 非自环），无一行走 livevt 派发。故 §8.6 条1「构造器活 vptr vs atexit 析构器表」判别对本卡 ④ 不适用；② 的 RTTI 读静态 `.rdata` COL/TD 表，不经运行时 vptr。已按纪律10 核 `call 0x7C978A`（atexit）站点 336 处，均未参与本卡取证。

## U6 · P3 伪 (vt,slot) 数量为自测值（与上卡口径差异说明）
- 本卡单类文件类 entry 的伪 (vt,slot) 数为 18~29（加表长约束后 1），上卡 006C9890/00631CC0 为 9 链/8 链 straw/pipe 类故达 616/566。两卡机制相同（下一张表 COL 被当自表槽位），仅被测 entry 的共享链数不同；本卡数字为现场复算，非照搬。见 `EVIDENCE/p3_table_constraint.json`。
