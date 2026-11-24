# NAMED-PUSH S06 B2 — PROGRESS

> 每 5 行追加；已核完的行即使中断仍有效。

- 初始化：目录已建、REPORT 骨架已写、delta.tsv / base_rate.tsv 表头已写。
- 目标 18 行（S06 named=True 剔伪名后 entry 升序第 19–36 行）。
- 材料自校验：gamemd.exe SHA256=`73201CC0...F67476` 逐字一致；Python 3.12.10 / capstone 5.0.7 skipdata=True / pefile 2024.8.26；atlas 只读。
- 方法：沿用 S06 B1 同套 RTTI 回扫 + 活 vtable 构造安装点法；②④ 不同源；三陷阱逐行排查。
- 复用 S06 B1 的方向标定：`0x410380=[eax+0xc] Read=流读入`；`0x410320=[eax+0x10] Write=流写出`。
- ② 高槽号处理：0071B920(slot91)/0071C1B0(slot69) 的 COL 距槽 364/276B，回扫上限从 40 提到 140 才命中，已逐行核实名串/槽号/槽值。

## 进度日志

### 第 1–5 行（005FEAF0 / 005FEC10 / 005FEF30 / 006B4FA0 / 006B5550）
- ②：5/5 RTTI 钉住（OverlayTypeClass slot5/6/8、SmudgeClass slot8、SmudgeTypeClass slot32；槽值==entry）。
- ③：005FEAF0 PASS（E_POINTER 判负流读入，被调 0x5f9720→0x410380，站点 call/test/jl@0x5FEB04/09/0B）；005FEC10 FAIL（29B 薄转发 ③a，与 B1 005439F0 同型）；005FEF30 FAIL（call [edx+0x10] 间接 + cmp -1 不可伪证）；006B4FA0 FAIL（同间接 -1）；006B5550 FAIL（0x7c8e17 分配零判断）。
- ④：5/5 行外构造器安装点（OverlayTypeClass 005FE2F1/in_func 005FE250；SmudgeClass 006B4A5C/in_func 006B4A50；SmudgeTypeClass 006B529B/in_func 006B5260）。
- 落盘：ROW_005FEAF0..ROW_006B5550 五份 EVIDENCE 已写。累计四环齐全 1。

### 第 6–10 行（006B55C0 / 006B5850 / 006B58B0 / 006B6160 / 006BF210）
- ②：5/5 RTTI 钉住（SmudgeTypeClass slot35/5/6/8；TClassFactory<VTerrainTypeClass> slot3）。
- ③：006B55C0 FAIL（分配零判断）；006B5850 PASS（E_POINTER 流读入，站点 call/test/jl@0x6B585B/60/62，被调 0x5f9720）；006B58B0 FAIL（29B 薄转发 ③a）；006B6160 FAIL（间接 -1）；006BF210 FAIL（工厂 CreateInstance：机械站点分配零判断 + QI 间接不可伪证）。
- ④：5/5 行外构造器安装点（SmudgeTypeClass 006B529B；TClassFactory 006BF149/in_func 006BF140）。
- 落盘：ROW_006B55C0..ROW_006BF210 五份 EVIDENCE 已写。累计四环齐全 2。

### 第 11–15 行（006BF390 / 0071B920 / 0071C1B0 / 0071C730 / 0071CDA0）
- ②：5/5 RTTI 钉住（TClassFactory<VTerrainClass> slot3；TerrainClass slot69/91/23/5；slot91/slot69 高槽号扩展回扫命中）。
- ③：006BF390 FAIL（工厂，同 006BF210）；0071B920 FAIL（0x5f5390 cmp 5/4 状态分派非错误哨兵 + 分配零判断）；0071C1B0 FAIL（间接 call [edx+0x6c]+零判断）；0071C730 FAIL（0x426630 返回 0/非0 零判断 D-46(A)）；0071CDA0 PASS（E_POINTER 流读入，手工站点 call 0x5f5e80@0x71CE79 / mov edi,eax / test edi,edi / jl@0x71CE82，被调 0x5f5e80→0x410380）。
- ④：5/5 行外构造器安装点（TClassFactory 006BF2C9；TerrainClass 0071B7BC/in_func 0071B7B0，另有 0071BBFF/0071BE5A 带 base-ctor call 0x5f3900 佐证）。
- 落盘：ROW_006BF390..ROW_0071CDA0 五份 EVIDENCE 已写。累计四环齐全 3。

### 第 16–18 行（0071DDD0 / 0071DE10 / 0071DEA0）
- ②：3/3 RTTI 钉住（TerrainTypeClass slot32/35/25）。
- ③：0071DDD0 FAIL（分配零判断）；0071DE10 FAIL（分配零判断）；0071DEA0 FAIL（间接 call [edx+0x9c] 零判断 + 0x5f92d0 的 al 布尔 0/1 D-46(A)）。
- ④：3/3 行外构造器安装点（TerrainTypeClass 0071DAF7/in_func 0071DA80，call 0x5f7090 base ctor）。
- 落盘：ROW_0071DDD0..ROW_0071DEA0 三份 EVIDENCE 已写。累计四环齐全 3（最终）。

## 三陷阱逐行排查
- eax 覆写：3 个 PASS 站点 test/jl 相邻，无 `mov eax,[…]` 夹入；0071B920 的 `mov [esp+0x10],eax` 只写内存不覆写 eax。
- 多路同一 call：3 个 PASS 站点均为单 call 本站点。
- 模板假句：分配零判断族（006B5550/006B55C0/0071DDD0/0071DE10）判为「对象初始化」式，不计 ③b。

## 汇总
- 核 18 行：① 18 / ② 18 / ③b 3 / ④ 18 / 四环齐全 **3**（rate 3/18=0.1667）。
- 产出 delta 3 行：005FEAF0、006B5850、0071CDA0。
- 与 S04 对比：本批 ② 真钉住 18/18（S04 为 0/36），败因全在 ③ 门槛（间接虚调用不可伪证、薄转发 ③a、分配/零判断 D-46(A)）。
