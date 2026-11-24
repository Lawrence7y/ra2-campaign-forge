# W157 PROGRESS

- 17:42 读完 R11_COMMON.md + R12_FACTS.md 全文（第一步完成）；grep 主台账 §881-4/§882-5/§883/§889-6 定位争议双方，未改台账。
- 17:44 确认 Ghidra 副本 `\_ghidra\W157` 存在（未复制/未覆盖）、无 java 进程独占、建 work/ 与 EVIDENCE/。注意：并行 write+pwsh 起 Ghidra 有竞争（脚本文件未落盘），改为先写后跑。
- 17:46 写 `W157Dump.java`（自写，非拷 W151），首跑 2 处 API 编译错（`getFlows()` 返回数组、`FlowType.isConditionalJump` 不存在），改用 mnemonic 判跳转，第 3 跑 exit=0、2855 行、有 ### DONE。
- 17:48 [关键] 读 w157dump.log：`0x67D300` size=4411、**BACKEDGE=111**、STRINGS(0)、CALLEES(52)；**0x67D1AF 所在函数 = 0x67CEF0**（CALLER ACTUAL_ENTRY=0x67CEF0）；XREFS: 67D300=1处 / 67CEF0=4处 / 5F6250=14处（含8 DATA）；0x67CEF0 有字符串 "SUN.EXE"。初步倾向序列化。
- 17:50 读 0x67CEF0 全反汇编：大量 IAT 导入调用 + E_POINTER(0x80004003) + QueryInterface 式虚调用 + COM 对象创建，确认存档/COM 形态。
- 17:51 capstone 独立通道（`w157_capstone.py`）：从 0x67D300 入口线性反汇编 1706 条、**ALL_JUMP_BACKEDGES=111**，与 Ghidra 对账一致；7 个关键字节全部 on_boundary=True；dump 数据区拿到 "SAVING GAME [%s] - Complete."、"CONTENTS"(宽)、"SUN.EXE"、GUID、IID_IPersistStream(0x7f7c80)。
- 17:52 读 0x5F6250：`0x4A1D50`(写dword)+`0x4A1CA0`(CRC32 查表 0x81f7b4) ⇒ 逐字段序列化器 + CRC，W151 正确。
- 17:53 写 `W157Callers.java`（调用者上下文+反编译），修正 `getAddressSet` API 后用顺序遍历+break；exit=0、1054 行。
- 17:54 [门控定案] `0x55DC92`（在 0x55D360 内）前 `cmp [0xA8B238],0/jne`、`test [0xABCE08]/jne`、`mov [0xABCE08],1`；4 个调用者全是存档（.sav / TXT_SAVING_GAME / SAVEGAME.NET / LoadDlg.CPP）。⇒ 非每帧。
- 17:55 [铁证] Ghidra 反编译 `0x67D300` = `IStream::Write` + `QueryInterface(IID_IPersistStream)` + `OleSaveToStream` + `Release`；`0x67CEF0` = `StgCreateDocfile`+`CreateStream("CONTENTS")`+`CoCreateInstance`+`OleRun`。判决：序列化成立，每帧协调器证伪。
- 17:56 `W157Verify.java`：确认 IAT 符号（OleSaveToStream/StgCreateDocfile/CoCreateInstance/OleRun/MultiByteToWideChar）；发现 W151 的 `fn_67cef0_bulletloop.log` 把 0x67CC30 误标为 0x67CEF0（前者 containing fn=NULL，后者 0x67CEF0..0x67D2FF 无回边）；0x5F6250 在 8 个 vtable 中。
- 17:57 `w157_perframe.py`：`0x55D360` 90 direct calls / 44 unique；每帧候选排序（事件泵链 0x647260→0x6474C7→0x64C380 为首）；确认 0x6475AE call 0x64C380。
- 17:58 写 RULING_67D300.md（判决+两假设+111回边+门控+台账建议+LEAD_AUDIT 3 条）、PROGRESS.md、UNKNOWNS.md、DISAGREE.md。完成。
