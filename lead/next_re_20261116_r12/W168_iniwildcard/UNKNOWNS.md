# W168 UNKNOWNS（分级未证清单）

## [未证]

1. **引擎是否另有一条完全独立的"从 MIX 内读 `BATTLE*.INI` / `RULE*.INI`"路径。**
   - 已排除的旁证（强但不是全路径穷举）：两个通配符字面串各只有 1 处代码引用，且都在散装枚举函数（`0x52CB90`/`0x52CD70`）里；这两个函数只用 `FindFirstFileA/FindNextFileA`（文件系统 API）。
   - 下一条最有区分力的证据：对 `FUN_0065CBF0` / `FUN_0065CAC0`（MIX/文件打开原语）做双通道 xref，看是否有以 `BATTLEMD`/`RULEMD` 拼接的调用路径；或真机在只留 MIX、删除全部散装 `BATTLEMD*.INI` 时看战役表是否还有条目（本卡禁止真机）。

2. **通用文件层"散装 vs MIX 同名条目"的优先级**（`FUN_0047AE10` → `FUN_00431E80`/`FUN_00431F10` → `FUN_0065CAC0`/`FUN_0065CBF0` 这条按显式文件名查找链，哪一层先被问、哪一层回落）。
   - 已查到字节级（`EVIDENCE/w168run4.clean.txt`）：exists 原语 `FUN_0065CBF0` 先 `vtable[+0x18]()`（对象 vtable `0x7E16B0`，槽目标 `0x473CD0`，只查 `[ecx+0x58]` 非空则 return 1，否则 `jmp 0x431F30`），非 0 即"存在"；否则回落 `CreateFileA` 真实文件系统。**`vtable[+0x18]` 是否为 MIX/档案层存在性检查未钉死** ⇒ 不下"MIX 先/散装先"的结论。
   - 本卡不需要裁决它就能回答 DLC 问题：通配枚举这条路径不查 MIX。已记 `docs/DESIGN.md:211` 有文件层实测（mixlib 扫 17 MIX 无散装 BATTLEMD.INI），本卡不重复。
   - 下一条证据：反编译 `0x431F30` 与 `0x473D10`（同 vtable 族的 Open），确认 `+0x58` 字段是否指向 MIX 索引对象。

3. **`BATTLEMD98.INI` 与 `BATTLEMD.INI` 在当前 NTFS 目录上实际谁先被 `FindNextFileA` 返回。**
   - 静态已证引擎无排序；"NTFS 通常近似字典序"是 `[静态推断]`，不是引擎保证。本卡禁止真机，未做目录枚举实测。
   - 现有包无键冲突，故该未证项不影响结论。若将来出现冲突 id，需真机 `FindNextFileA` 返回序实测或用不冲突 id。

4. **`FUN_004741F0` 内 SHA1 摘要分支**（`s_Digest_0081bfe0`、`0x67452301` 等常量）的触发条件与用途。
   - 本卡路径上调用时 `param_3=0`（`0x52CC40 push ebx` ⇒ 摘要分支 `if param_3 != 0` 不执行），故不影响 INI 合并结论。仅记录，未下钻。

## [已证但未展开]

- `FUN_0047AE10` 遍历 `DAT_0089E410` 搜索路径链表（path+filename 拼接）⇒ 找到候选即停；本卡只读到这一层，未确认该链表元素是 MIX 文件还是目录（按 Westwood 惯例是搜索目录/路径，非 MIX 索引）。
- RULE 路径的多文件 `DialogBoxParamA(...,0x93,...,&LAB_0052d430,...)` 选择器：`LAB_0052d430` 不是 Ghidra 建立的函数（`getFunctionAt` 返回 NULL），本卡未反编译该 dialog proc；不影响 BATTLE 结论。

## 排除（负结果也是交付）

- 枚举循环内排序/比较插入：BATTLE 全部 139 指令、RULE 443 指令审查，无 `qsort`/`strcmp` 插入（RULE 只有对 base 的固定前插，见 INI_MERGE §2.3）。
- `BATTLEMD.INI` 在 BATTLE 路径的"插到数组 0"：无此行为，只有 bool 标志 `bVar2`。
- 隐藏文件被枚举：掩码 `0x116` 过滤 HIDDEN。
- `BATTLEMD.INI.ra2forge.bak` 被枚举：文件名以 `.bak` 结尾，不匹配 `BATTLEMD*.INI`。
- 通配符字面串"各出现两次"：字节实测每个各 1 次（见 DISAGREE.md）。
