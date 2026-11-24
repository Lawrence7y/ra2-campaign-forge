# NAMED-PUSH S06 B1 — PROGRESS

> 每 5 行追加；已核完的行即使中断仍有效。

- 初始化：目录已建、REPORT 骨架已写、delta.tsv / base_rate.tsv 表头已写。
- 目标 18 行（S06 named=True 剔伪名后 entry 升序前 18）。
- 材料自校验：gamemd.exe SHA256 逐字一致；capstone 5.0.7 skipdata=True / pefile 2024.8.26；atlas 只读。
- 工具准备：`_work/` 下 recore/core2（复用 S14 B1 同法），自建 filter/analyze/deepinspect/ring4 等脚本。
- 关键方向核定：`0x410380 = [eax+0xc] Read = 流读入`；`0x410320 = [eax+0x10] Write = 流写出`（避免 S14 0065AC40/006A48A0 读写写反被否）。
- ㉓ 处理：逐点区分构造器安装（base ctor call + field init）与析构器安装（全局表注销 / push 1;call [vtable slot0]）；④ 锚只取构造器安装点。

## 进度日志

### 第 1–5 行（004839F0 / 00483C10 / 00543330 / 005439F0 / 00543B10）
- ②：5/5 全数 RTTI 钉住（IsometricTileClass 高槽号 slot73 需把回扫上限从 40 提到 130 才命中 COL；已核实槽值==entry）。
- ③：004839F0 PASS（E_POINTER 判负流读入，手工捕获 `cmp eax,ebx(=0);jl`，机械 chA 漏检）；00483C10 PASS（E_POINTER 判负流写出）；00543330 FAIL（间接虚调用+零判断）；005439F0 FAIL（③a 纯转发 29B）；00543B10 FAIL（call [edx+0x10] 间接，-1 不可伪证）。
- ④：5/5 均有行外构造器安装点（CellClass vt 0x7e4eec 用 0047BD5C；IsometricTileClass vt 0x7ec258 用 005439B7；析构器 0047BB69/00543B16 按 ㉓ 排除）。
- 落盘：ROW_004839F0..ROW_00543B10 五份 EVIDENCE 已写。累计四环齐全 2。

### 第 6–10 行（00549AA0 / 00549AE0 / 00549C80 / 00549D70 / 00589A60）
- ②：5/5 全数 RTTI 钉住（IsometricTileTypeClass slot#32/#35/#5/#6、DynamicVector slot#2 均槽值==entry）。
- ③：00549AA0 FAIL（0x7C8E17 分配包装+零判断）；00549AE0 FAIL（零判断）；00549C80 FAIL（chA p3=0）；00549D70 FAIL（chA p3=0 薄封装）；00589A60 FAIL（分配零判断+对象初始化模板假句）。
- ④：5/5 均有行外构造器安装点（IsometricTileTypeClass vt 0x7ecc48 用 00544A42；DynamicVector vt 0x7ed4a0 用 005650CD）。
- 落盘：ROW_00549AA0..ROW_00589A60 五份 EVIDENCE 已写。累计四环齐全仍 2。

### 第 11–15 行（005F3E70 / 005F92D0 / 005FC570 / 005FD270 / 005FDF70）
- ②：5/5 全数 RTTI 钉住（005F92D0 slot#25、005FC570 高槽号 slot#73 已核实）。
- ③：005F3E70 FAIL（间接虚调用+零判断）；005F92D0 PASS（Find 返 -1 哨兵，被调 0x7514D0 `or eax,-1`@0x751516 字节伪证，站点 cmp/je@0x5F93BA/BD）；005FC570 PASS（Find 返 -1，被调 0x5FDD20 `or eax,-1`@0x5FDDD8，站点 cmp/je@0x5FD1C0/C3）；005FD270 FAIL（零判断 0x47C550）；005FDF70 FAIL（call [edx+0x10] 间接，-1 不可伪证）。
- ④：5/5 均有行外构造器安装点（IsometricTileClass 005439B7；IsometricTileTypeClass 00544A42；OverlayClass vt 0x7ef3d4 用 005FC38F）。
- 落盘：ROW_005F3E70..ROW_005FDF70 五份 EVIDENCE 已写。累计四环齐全 4。

### 第 16–18 行（005FE530 / 005FE570 / 005FE770）
- ②：3/3 全数 RTTI 钉住（OverlayTypeClass slot#32/#35/#25）。
- ③：005FE530 FAIL（0x7C8E17 分配零判断）；005FE570 FAIL（0x7C8E17 分配零判断）；005FE770 FAIL（0x528A10 失败返 0 零判断，S14 00511850 同型）。
- ④：3/3 均有行外构造器安装点（OverlayTypeClass vt 0x7ef600 用 005FE2F1）。
- 落盘：ROW_005FE530..ROW_005FE770 三份 EVIDENCE 已写。累计四环齐全 4（最终）。

## 汇总
- 核 18 行：② 18 / ③b 4 / ④ 18 / 四环齐全 **4**（rate 4/18=0.2222）。
- 产出 delta 4 行：004839F0、00483C10、005F92D0、005FC570。
