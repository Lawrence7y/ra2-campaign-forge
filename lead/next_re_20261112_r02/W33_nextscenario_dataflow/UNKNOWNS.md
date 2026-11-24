# 未覆盖项与待运行验证（UNKNOWNS）

1. **`MSG:UnableMapSelect` 弹窗之后 `0x00685A79..0x00685C54` 的活进程后续流转** `[待运行验证]`：
   - 静态上 `0x00685A74`（`call 0x5add10`）未检测 `eax` 返回值，继续执行 `0x00685BA1 call 0x5db680` 与 `0x00685C1C call 0x49f7a0`（本镜像中 `0x0049F7A0` 为 `b0 01 c3` 即固定返回 `1` `[本次读码]`）。
   - `[Scen+0x125C]` 在 `0x005AE100` 失败时未被 `0x00686700` 更新（仍保留原值或由其他外围清理逻辑重置），因此 A2（`ECH02.MAP`）绝不会被传入 `Start_Scenario`（`0x00683AB0`）。至于弹窗点击 `TXT_OK` 后在 `W27` 真机上究竟回到主菜单还是重载上一关，未设断点抓内存态确认，留作 `[待运行验证]`（不影响「`ECH02.MAP` 根本未进入选图/开图阶段」的静态判决）。
2. **是否可通过散装 `MAPSELMD.INI` 覆盖修复 `W27` 链路推进** `[待运行验证]` `[静态推断]`：
   - `0x005CEF62..0x005CEF78` 以 `[edx+0x1c]`（即 `CCFileClass::Open`，`0x00473D10`，磁盘优先）打开 `"MAPSELMD.INI"` `[本次读码]`。
   - 静态逻辑推论：在游戏目录放置含对应 `[Nod]`/`[GDI]` 阶段与 `Scenario=ECH01.MAP` / `ECH02.MAP` 的散装 `MAPSELMD.INI`，可被 `0x005CEEF0` 优先加载并解决 `MapSelect: Invalid stage!` 与 `NextScenario` 匹配失败问题；此修复方案的实际真机效果尚未实测 `[待运行验证]`。
3. **`CCINIClass::Load`（`0x004741F0`）调用 `INIClass::Load`（`0x00525A60`）后经由 `FileStraw` 读取 `CCFileClass` 的内层循环细节** `[部分读码]`：
   - 已证实 `0x00525ABA..0x00525AD6` 将 `CCFileClass*` 通过 `0x007EB758`（`0x006C9890`）链接到 `FileStraw`，并已验证 `CCFileClass` 虚表 `0x007E16B0` 的 `+0x14 = 0x00473C50`（`Is_Available`）、`+0x1C = 0x00473D10`（`Open`）、`+0x24 = 0x00473B10`（`Read`） `[本次读码]`。
   - `0x00525BE2` 之后 `FileStraw::Get` 调用 `[FileClass + 0x14]`/`[FileClass + 0x1C]`/`[FileClass + 0x24]` 的具体行号未逐条展开反汇编，但任何经该虚表打开的 `.MAP` 均必然走 `0x007E16B0` 的磁盘+MIX 双寻址逻辑 `[本次读码]`。
4. **`ScenarioClass::Read_INI` 中读取 `SkipMapSelect` 字符串指令的精确 VA 展示** `[未在本轮打印]`：
   - 已在 `step8`/`step9` 验证 `SkipMapSelect` 对应 `byte ptr [esi + 0x34B0]`，并在 `step14` 验证 `0x00685A38`（`mov al, byte ptr [ecx + 0x34b0]`）与 `0x005C390F`（`mov byte ptr [ecx + 0x34b0], 1`）的精确字节 `[本次读码]`；`ScenarioClass::Read_INI` 内 `SkipMapSelect` 读取点本身未在 `step14` 再次打印（仅在 `0x00689FB5..0x0068A045` 之外）。
