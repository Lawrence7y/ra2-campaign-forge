# S17-F1 · DISAGREE（与线索文档/台账的分歧登记）

> 分歧只登记、不改他处文件（不改台账 / 不改 `docs\re\` / 不改 COVERAGE）。

## D1 · `savegame_block_manifest.md` 把 `0x67CEF0` 标为 "Game::Load"（§0/§2.3）

- **线索原文**：`Game::Load 0x0067CEF0（校验魔数/开 CONTENTS 流）；核心 Game::Load_Core 0x0067E440`。
- **本卡判定（双通道 `[已证]`）**：`0x67CEF0` 是**写档文件构造器**，不是 Load。三条独立证据：
  1. `0x67CEF0` 内 `0x67CF42 call [0x7E15C8]`，pefile 解析 `0x7E15C8 = ole32!StgCreateDocfile`（**创建**容器，非打开）；线索自己 §12.4.3 也把它定名为 StgCreateDocfile，与本卡一致，但与 §0/§2.3 的 "Load" 标签自相矛盾。
  2. `0x67CEF0` 日志串 `SAVING GAME [%s - %s]`（`@0x83D564` 簇），非 "LOADING GAME"（LOADING 在 `0x67E44D push 0x83D620`）。
  3. `0x67CEF0` 内 `0x67D1AF call 0x67D300`（=写着名的 COM/OLE 写序列化器），且全镜像 `0x67D300` 唯一调用者就是它。
- **真正的读核心** = `0x67E440`（`0x67E489 StgOpenStorage` / `0x67E572 IStorage::OpenStream("CONTENTS")` / `0x67E840 OleLoadFromStream`）。
- **影响**：FLOW/PROGRESS 用本卡口径（写 `0x67CEF0→0x67D300`，读 `0x559DC5→0x67E440`）；线索 §2.3/§2.4 的 Save/Load 标签不得直接引用。

## D2 · `savegame_block_manifest.md` 把 `0x67D0C0` 标为 "Save 外层"（§2.1）

- **线索原文**：`Save 外层 0x67D0C0（__thiscall, 1 栈参=文件名）`，其内 `CoCreateInstance`/`IStream::Write`。
- **本卡判定（`[已证]`）**：`0x67D0C0` 不是独立函数入口，而是 `0x67CEF0` 函数体内部的一条指令序列。证据：
  1. `0x67CEF0` atlas/本卡 capstone 双通道 size = 1040 B = `0x67CEF0..0x67D300`，`0x67D0C0` 落在其中。
  2. rel32 全 `.text` 扫描：`0x67D0C0` 作为 `E8/E9` 目标 **0 处**，imm32 引用 **0 处**（`EVIDENCE\analysis_main.txt` §3）。
  3. 线索 §2.1 描述的 `CoCreateInstance [0x7E15FC]`/`call [ecx]`/`call [edx+0xC]` 确在 `0x67CFxx..0x67D1xx` 出现，但属于 `0x67CEF0` 体内（本卡 §4 已逐条列出）。
- **影响**："存档总入口"记 `0x67CEF0`，不记 `0x67D0C0`。

## D3 · 线索 "指针 Swizzle 不是自研表、由 OLE CLSID 承担"（`savegame_block_manifest.md §0/§2.5`）

- **线索原文**：对象寻址 = OLE CLSID + 存储路径，镜像内未见裸地址落盘，"指针 Swizzle 不存在自研表"。
- **本卡判定（部分一致、部分分歧）**：
  - **一致**：跨对象引用确实靠 OLE CLSID（`OleSaveToStream`/`OleLoadFromStream`），CONTENTS 内无裸地址落盘 —— 本卡模板反汇编证实（`EVIDENCE\ghidra_dump.log` template 段）。
  - **分歧**：镜像内**存在**自研指针重定位管理器 `SwizzleManagerClass`（`0xB0C110`，vtable `0x7F4108`，`Here_I_Am 0x6CF240` + `Reset 0x6CF350`），其 `0x6CF2A8` 清字段、`0x6CF3BA` 回填，两表 `{原值, &字段}` 8 B 表项 —— 这正是任务书所述 Swizzle 惯用法。线索 §2.5 "不存在自研表"若指"无独立 swizzle id 落盘表"成立；若指"无 swizzle 机制"则错。
  - 与 `re_atlas\kb\21`（本卡指定线索）一致：kb/21 已撤回"字段注册表"误读，定谳为 `SwizzleManagerClass::Instance` + 485 处登记（本卡 rel32 通道实测 476 处直接 E8，口径差：kb/21 含 5 处槽6+插队+2 处屏蔽假命中；两者非矛盾）。
- **影响**：FLOW §5 按"OLE 跨对象 + 自研 Swizzle 字段回填"双层描述，不采纳"无自研 swizzle"的笼统说法。

## D4 · 卡正文 "mode==0（存）/mode!=0（读）分支" 的措辞

- **卡候选假设（按纪律 11 视为猜测）**：把"存/读"描述成某个 `mode` 参数的两个分支。
- **本卡判定（`[已证]`）**：存/读是**两条独立调用链**（写 `0x67CEF0→0x67D300`，读 `0x559DC5→0x67E440`），并非同一函数按 mode 分流。镜像中的 `mode` = `[0xA8B238]`（SessionClass GameMode：0=菜单、5=遭遇战/局内），其作用有二：
  1. 在 `0x55DBCD` 作为**写档门控**的一部分（mode==0 且首次自动存档）；
  2. 在 Save_Core `0x67E3BD cmp [0xA8B238],5` 决定**是否写 Skirmish Session.Options**（写档内部的子分支）。
  - 它**不是**"存 vs 读"的选择器。
- **影响**：FLOW §3/§4 分别列 Save/Load 顺序，不用 "mode==0/!=0" 作为两分支标签；该措辞在 PROGRESS/交付中不复用。

## D5 · `0x67D300` "每帧协调器" 旧说法

- 已在台账 §882-5/§873 被 §894 推翻，R14_COMMON §1 列入作废索引。本卡只复核门控证据（`0x55DBCD..0x55DC92`，双通道一致），**不重做、不引用旧结论**。无新分歧。
