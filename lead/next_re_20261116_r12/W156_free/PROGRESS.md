# W156 PROGRESS（时间 + 做了什么 + 结论/下一步）

- 17:24 读 `R11_COMMON.md`(193行) / `R12_FACTS.md`(55行) / `CAUSE_B.md`(389行) 全文；grep 台账 §654/§667/§890 相关节。确认任务与既往口径。
- 17:26 建 `W156_free/{work,EVIDENCE}`；核对 Ghidra 副本 `_ghidra/W156`（gamemd_auto.gpr + 两个 .rep，未复制/未覆盖）；拷 `w152_core.py`→`w156_core.py` 作字节通道底座；确认 0 个 java 进程。
- 17:28 写 `w156_scan.py`（capstone+pefile 双通道字节扫描：A8EB50 写、HeapFree IAT call、87F924 读写、5687F0 call、cell+E4/E8 写、raw byte 交叉验证）。运行 exit=0，4569 行 → `EVIDENCE/scan_byte_channel.log`。
  - 结论：写 `[A8EB50]` 字节通道仅 1 处 `0x43BB18`（构造器）；HeapFree call 3 处；87F924 367R/0W；5687F0 4 call。
- 17:30 写 `w156_dump5.py` dump 5 个重点函数反汇编 → `dump5_capstone.log`(1958行)。观察到 0x44FE60/0x452D40 只读 Count 遍历，非注销。
- 17:31 Ghidra 综合脚本 `W156Core.java`（引用查询 + 21 函数反编译）运行 exit=0，2056 行 → `ghidra_core.log`。
  - 结论：Ghidra 对 A8EB50 W=2（第二处 NOFUNC 0x4E6B91）；HeapFree IAT total=3；5 个重点函数确认是格式化/放置/查询，不是注销。
- 17:32 追 NOFUNC 写站点：`w156_dump_4e6b.py` dump 0x4E6B00 → 判定为 `DynamicVectorClass` 全局 init/clear（0x4E6B60/0x4E6BA0，atexit 清理），非逐对象注销。
- 17:33 Ghidra `W156Vtable.java` / `W156Vt2.java`（修正 4 字节间距）dump 数组 vtable 0x7E9E24/0x7E9E44 → 发现 `0x4E95E0`=Resize(operator_new)、`0x4E9690`=FindIndex、`0x4E82F0`/`0x4E9550`=Clear(free(Items))。
- 17:34 `w156_array_writes.py` 扫两个实例数组 Count/Items 写：Bld.Count atlas 内仅 1 写；Abs.Count 2 写（0x43BB72/0x4F5EFC，均为 inc 登记）。确认"Count 无 dec 绝对写"。
- 17:35 Ghidra `W156Final.java`：数组对象引用 + 符号搜索 → BldArray.obj(0xA8EB40) 引用 7 处，出现 `0x43BCF0`（紧跟构造器，疑似析构）。
- 17:36 **突破**：Ghidra `W156Dtor.java` 反编译 `0x43BCF0`(986B) → 确认为 BuildingClass 析构：FindIndex→`0x45AE10`(Delete index) 从 BldArray/FootArray/AbsArray 移除 + free 成员。
- 17:37 `w156_dtor_scan.py` 全指令扫 `0x43BCF0`：call 清单无 `0x5687F0`、无 `[vptr+0x124]`；dump `0x45AE10` 确认为 `Count--`+元素前移的注销原语。
- 17:38 Ghidra `W156Dtor2.java` 反编译 `0x445880`(dtor 内两次调用) → 是"撤销建造数量统计"，非摘链；grep 无 0x124/0x5687F0。
- 17:39 Ghidra `W156Verify.java`：BuildingClass 4 个 vptr 前 4 槽（确认槽0=0x410260 非析构，与 W152 一致）；`0x5F5850` 谓词反编译复核（+0x81/+0x74 逻辑与 W152 完全一致）；`0x43BCF0` 直接引用仅 1 处 `0x459F20`。
- 17:41 Ghidra `W156Callers.java`（首次因文件/命令并行竞态失败 exit=1，重跑 exit=0）：枚举 `0x45AE10`(8 caller)/`0x45ADD0`(21 caller)；反编译 `0x459F20` = **deleting destructor**（call 0x43BCF0 + free(this)）。判决链闭合。
- 17:42 判定 ②-b = **静态不可判**（已找到释放原语但 delete 经虚调用不可枚举）；三条硬排除全部复核成立。
- 17:45 写交付件 `FREE_PRIMITIVE.md` / `PROGRESS.md` / `UNKNOWNS.md` / `DISAGREE.md`。

**资源纪律**：全程最多 1 个 Ghidra 实例（实测 0→1）；所有 Ghidra 调用 `-noanalysis` + 输出重定向；未用 `Select-Object -First` 截断 java 管道（只在进程结束后读日志）；未改 Ghidra 项目外的任何游戏文件、未改主台账、未 git commit。
