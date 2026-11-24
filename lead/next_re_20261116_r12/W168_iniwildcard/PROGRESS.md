# W168 PROGRESS

> 时间均为 2026-11-16（Asia/Shanghai），采样时间来自会话提示与操作顺序。

- **21:10** 开工。整份读 `R11_COMMON.md`、`R12_FACTS.md`（§6.2 双通道至少一条不依赖 atlas 边界；§10.3 栈参数须给 `[esp+N]` 上界）；读 `DESIGN.md:206-218`、`DLC_CAPABILITY_AUDIT.md` 第 3 行（L168-196）。
- **21:15** 环境检查：Python 3.12.10 / pefile 2024.8.26 / capstone 5.0.7；Ghidra 项目副本 `_ghidra\W168` 存在；无运行中 java 进程。建卡目录 `work\`、`EVIDENCE\`。
- **21:20** 读主台账 §740/§742/§751/§755/§910 与 W122 既有脚本日志（`iniload.log`/`merge.log`）作为线索；确认 §910 由 Lead 亲做并标"W168 复核中"，§910-5 列出待补三项。
- **21:30** 写并跑 `work\byte_verify.py`（`EVIDENCE\byte_verify.txt`）：复核 4 个字符串字节、全 `.text` dword 字面量扫描、IAT 解析、IAT call 站点。确认两个通配符各 1 处字面量命中；IAT `FindFirstFileA/FindNextFileA/FindClose/GetFileAttributesA` 地址。
- **21:35** 写并跑 `work\boundary_check.py`（`EVIDENCE\boundary_check.txt`）：从函数入口 `0x52CB90`/`0x52CD70` 用 capstone `skipdata=True` 验证边界，确认 `push 0x8261a8`/`push 0x82626c` 是指令；附带复核"各出现两次"说法（每个通配符字面串只 1 次）。
- **21:40** 写并跑 `work\disasm_battle.py`（`EVIDENCE\disasm_battle.txt`）：`fn 0x52CB90` 全 139 指令反汇编，确认枚举骨架、属性掩码 0x116、`stricmp(base)` 只设 bool、合并调用点 `0x52CC67 call 0x46CE10`、fallback `0x52CCCD/0x52CD2C`。
- **21:45–22:00** Ghidra run1 `W168Main.java`（`EVIDENCE\w168main.log/.clean.txt`）：双通道 xref（Ghidra `getReferencesTo` 1 处 each，与字节通道一致）；反编译 `0x52CB90`/`0x52CD70`/`0x4739F0`/`0x4741F0`/`0x7C8D20`；IAT xref；caller 站点列表。
- **22:05** Ghidra run2 `W168Run2.java`（`EVIDENCE\w168run2.log/.clean.txt`）：反编译合并函数 `0x46CE10`（按战役名 stricmp 复用对象 + `call [vptr+100]`）、文件查找 `0x47AE10`、INI 读 `0x525A60`；用 `getFunctionContaining` 正确定位 4 个 BATTLE caller + 1 个 RULE caller 所属函数（`0x52BA60`/`0x52D9A0`/`0x6851F0`）。
- **22:15** Ghidra run3 `W168Run3.java`（`EVIDENCE\w168run3.log/.clean.txt`）：反编译虚方法 `0x46CCD0`（逐键以当前字段值为默认值写回 ⇒ 后写覆盖）、完整 init `0x52BA60`、文件存在层 `0x431E80`/`0x431F10`。
- **22:20** 写并跑 `work\disasm_init_order.py`（`EVIDENCE\disasm_init_order.txt`）+ 字符串读取：确认 `0x52C605 call 0x52cb90` 前打 `Init Campaigns\n`、`0x52C95C call 0x52cd70` 前打 `Init Rules\n` ⇒ BATTLE 先于 RULE。
- **22:25** 复核三个 INI 文件大小/SHA-256 与内容；确认 `.bak` 以 `.bak` 结尾不匹配 `BATTLEMD*.INI`。
- **22:28** Ghidra run4 `W168Run4.java`（`EVIDENCE\w168run4.log/.clean.txt`）：反编译 exists 原语 `0x65CBF0`、set-name `0x65CAC0`；查到"先 vtable[+0x18] 后 CreateFileA"的字节事实，但 vtable 方法身份未钉死 ⇒ Q3 通用 MIX 优先级保守标 `[未证]`，不影响 DLC 结论。
- **22:30** 交付 INI_MERGE.md / UNKNOWNS.md / DISAGREE.md / PROGRESS.md；收尾。

**没做的（诚实记录）**：未启动游戏、未 attach/读活进程、未改任何游戏文件、未改主台账、未 git commit。未展开 `FUN_0065CBF0` 等更深的 MIX 原语去裁决通用"散装 vs MIX"文件层优先级（本卡问题不需要；通配枚举不查 MIX 已足够）。
