# W150 PROGRESS

格式：`时间 | 做了什么 | 结论 / 下一步`
时间取自本卡的时间采样点（开场 16:50，末次 17:01）。**中途我一度在脑内"顺推"写下了 17:52/17:58/18:05 这类未测量的时刻，已全部删除并改正** —— 记在这里以免后人把这个错误当数据。

- 16:50 | 整份读完 `R11_COMMON.md`（170 行） | 禁令已登记：零真机、只写本卡目录、只用 `_ghidra\W150` 副本、不改主台账。
- 16:51 | 清点现场：`W150_navstate\` 空；`_ghidra\W150\gamemd_auto.rep` 存在；r10 里程碑产物齐全（W130 atlas / W131 subsystems / W132 arrays / W122 脚本模板）。
- 16:51 | grep 主台账 `A8B238`（25 命中）、`A8B230`、§695/§696/§698/§725/§882/§883/§886 | 台账已有：`0x6474C7` 是 6 路跳转表分派（`jmp [eax*4+0x6475D8]`）；§695-3「A8B238 是某列表计数」**已被 §696-1 自我推翻，不得引用**；`0xA8B230` 是大单例指针（`+0x34cc` 场景索引 / `+0x125c` 场景名 / `+0x62c` 挂起深度）。
- 16:52 | 查 W130/W131 表结构 | `function_atlas.tsv` 带 `strings` 列，`fn_subsystem_canonical.tsv` 带 subsystem 列 ⇒ 只需在 Ghidra 里产 (global, function, insn)，字符串与子系统归属用 Python 回联，省一次 Ghidra 运行。
- 16:53 | 查 `class_atlas_v2.tsv` 找 UI 框架类 | 发现 `GScreenClass`(主表 `0x007EA6FC`,23 槽)、`GraphicMenu`(`0x007EA5FC`)、`ProgressScreenClass`(`0x007F0064`)、`HouseTypeClass`(4 基表)`。
- 16:54 | 写 `work\W150Sweep.java`（PART1 12 个 watch 全局逐点读写+写点上下文；PART2 `[0xA70000,0xB90000)` 全量读写普查；PART3 跳转表；PART4 反编译 `0x647260`/`0x48CCC0`/`0x52D9A0` + 全部 `0xA8B238` 写者） | 一次运行取完全部主证据。
- 16:55 | 第 1 次 Ghidra：**exit=0 但脚本没跑**（`ERROR W150Sweep.java:130: incompatible types` + `skipping ...java`） | **教训：编译错不改退出码，判"跑完"只能看日志里有没有 `### ALLDONE`。**
- 16:56 | 修泛型错（`TreeMap<Long,Integer> m` → `TreeMap<Long,TreeMap<Long,Integer>> m`），并顺手加 PART2b（立即数写普查）与 PART2c（vtable xref）。
- 16:56 | 写 `work\w150_bytescan.py`（**纯 pefile+原始操作码**，不依赖 Ghidra），做第二条独立证据链。
- 16:57 | 跑 bytescan | **`0xA8B238` 写点 = 30**；立即数只有 `{4@52DD61, 3@52DD7F, 5@52E10F, 3@52E3C6, 0@5EFDC3}`。`0xA83D48`=6、`0xA8E9A0`=18、`0xA8ED84`=10、`0xA8B230`=3、`0xA8D5F8`=6。**负结果**：`0xA8ED80` 0 命中 ⇒ 该处用 `A2`(`mov [a],al`)，我的模式表缺 `A0..A3` moffs 组 —— 已登记为工具缺陷（U-9）。
- 16:58 | 第 2 次 Ghidra（`W150Sweep.java`，exit=0，日志 24,555 行） | `A8B238` **W=30 R=717（334 函数）**，与字节扫描**同数**；`A8B230` W=3 R=1206；`A83D48` W=6 R=3；`A8ED80` **W=1**（`0x7778CE`，`MOV [0xa8ed80],AL`）；`A8ED84` W=10 R=942。
- 16:58 | 读 PART3 跳转表 | **6 项只有 2 个目标**：`jt[0]=0x6474DC`、`jt[1..4]=0x6475C8`、`jt[5]=0x6474DC`；`jt[6]` 已是 `0x6475F0` 的指令字节 ⇒ 表恰好 6 项。
- 16:59 | 反编译 `0x647260` | `if ((A8D5F8&2)==0) switch(mode){0,5→0x6474DC; 1..4→FUN_006475F0(); default return;}`；`0x6475F0` 按 atlas = **Queue.CPP**（TXT_QUEUE_FULL/TXT_OUT_OF_SYNC）⇒ **泵本身不区分菜单/局内**。
- 16:59 | 反编译 `0x48CCC0`（Conquer.CPP 780 B）+ `0x52D9A0`（Init.CPP 4,536 B） | 外层"一个画面一次"、内层"一帧一次"；`DAT_00a8ed84 = 0` 在 `0x52D9A0` 循环顶 ⇒ **帧计数每个画面重置**；局部状态机 `iVar11 = (mode==0)?0x12:((mode==4)+0x10)`。
- 16:59 | 写 `work\w150_name.py` + `w150_range.py` | 识别 `0x6475F0/0x64C380`=Queue.CPP、`0x4C6CB0`=Event.CPP（写 `A83D48=1`）、`0x683AB0`=Scenario/VQA、`0x684620`=Scenario 载入进度条、`0x6980C0`=Session.CPP、`0x5B4EE0`=ModemGst.cpp、`0x5B82F0`=ModemHst.cpp。**关键空洞**：`0x5EF2C3..0x5EFF6F` 约 3.2 KB 无函数，而模式 1/2 的写点全在里面。
- 17:00 | 读 `0x5EF7xx` 写点上下文 | `MOV ESI,1; MOV [mode],ESI`⇒**模式 1**；`MOV EDI,2; MOV [mode],EDI`⇒**模式 2**；`MOV [mode],0`⇒0。**纠正我自己的印象**：模式 1/2 确实被写，先前"只有立即数 0/3/4/5"是"立即数"限定造成的错觉。
- 17:00 | 写 `work\w150_mine.py` 挖状态变量 | `[0xA8DB30]`（**单写者函数**，`{1,2,3}`，14 个读者函数）、`[0xA8D60E]`({0,1})、`[0xA8B24C]`(恒 2)、`[0xA8E9A0]`({0,1})、`[0xA8B554]`({5,10})。
- 17:00 | 第 3 次 Ghidra（`W150Sweep2.java`，exit=0，4,312 行） | 得到 `0xB0B59C`（局内模态 HWND，唯一写者 `0x6AE2C0`）、`0x5B49B0`=`"ModemGuest: Dialog enter"`、`0x5B77E0`=`"ModemHost: Dialog enter"`、`0x6AE2C0`=局内循环（`while(local_4!=0x617 && !=0x5C0) FUN_00532100();`）。
- 17:00 | **自我纠错**：`work\w150_vtclass.py` 查 vtable→类名 | `0x007EAB5{8,C},4,2C` = `.?AVHouseTypeClass@@` ⇒ `0xA83C98` **不是画面栈**，是 **HouseTypeClass 注册表**；`vtable+100` = `HouseTypeClass::Read_INI`，`[0x887048]` = CCINIClass。我在报告里按此改写并写进 `DISAGREE.md`。
- 17:01 | Lead 并入真机事实（§887）：**`0=A8B238` 主菜单、`5`=局内**、局内 31.13 帧/s、**菜单/局内窗口几何不同（533×400 → 910×512，DPI-aware）** | 直接把我最大的未证项（0 与 5 的语义）闭合，并把模式 5 的静态证据（`FUN_006AE2C0` = 局内循环）与真机对上；几何差异写成硬前置条件。
- 17:01 | 交付 `NAV_STATE.md` / `UNKNOWNS.md` / `DISAGREE.md` / `PROGRESS.md` | 决策表 V1–V9 + 真机探针 P-1..P-9。
