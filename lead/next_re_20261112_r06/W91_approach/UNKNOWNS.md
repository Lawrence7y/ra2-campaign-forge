# W91_approach UNKNOWNS

## U-1：trip_P1 接触后 ~6 s 的 AV（Eip=0x00000000，Access=0x00000000）
- 现象：A8ED50 首非零 t=26.02 s；internal error 弹窗于 t≈32 s 被检测到；except.txt fresh（26,579 B，Evid F8F6BC24…）。EIP=0 ⇒ 经空函数指针调用；栈上出现数据地址 `0x0087F7E8`（紧邻 X87E8E0=0x0087E8E0 区域）与返回地址 `0x0047C500`。`[本次实测]`
- 触发语境：敌 200 MTNK Hunt 与 TESLA 火力圈首次接触后数秒（当时无 Crewed 覆盖）。候选链：建筑毁伤 / TESLA 击杀路径 / 生兵（未分离）。`[未证]`

## U-2：trip_P2 接触后 ~7 s 的 AV（Eip=0x006F36FE，Access=0x11378560）
- 现象：A8ED50 首非零 t=23.81 s；弹窗 t≈31 s；except.txt fresh（26,497 B，Evid 3429FF45…）。与 P1 **签名不同**（Eip 非 0，访问地址非 0）。P2 已带 `[NAPOWR] Crewed=no` ⇒ **生兵链不是该崩溃的必要环节**（W88 C7 同向）。`[本次实测]`
- 剩余候选链（未分离）：① TESLA 线圈对 MTNK 的击杀/充能路径；② Hunt 单位对**建筑**射击/建筑毁伤路径。注意 W88 C6（1522 对象、12 TESLA、有 300 玩家 MTNK 缓冲）300 s 全程无崩 —— P1/P2 与 C6 的结构差异是「敌人首个交战目标是**建筑**而非单位」。`[未证]`
- 两崩均发生在 **A8ED50 首非零 +6~7 s**，跨布局一致 ⇒ 高度疑似接触触发链，与地理距离无关。`[本次实测（N=2）]`

## U-3（承接 W90 U2，lead 子步骤）：`ddraw.dll` `0x5EE48` 参考上限 —— 运行时实测 = 210，与静态扫描矛盾（已定案为「未解释的写入/覆盖路径」）
- 静态（lead 离线查证）：`ddraw.dll`（85e0f7d5…03a9，ImageBase 0x10000000）内对 `0x1005EE48` 全文件仅 4 处引用，唯一立即数写入 `mov dword ptr [0x1005EE48], 0x3C`（0x10015E83）⇒ 静态启动值 = 60，无 `mov [abs],reg` 形态写入（0 处）。`[静态推断]`
- **trip_P3 运行时实测（只读 RPM，`out\trip_P3\ddraw_globals_probe.json/.txt`）**：ddraw.dll 基址 `0x54400000`（ASLR）；`0x5EE48` = **210 (0xD2)**；同 dump 窗口 `0x5EE3C=0xA00(2560)`、`0x5EE40=0x5A0(1440)`；maxfps(0x594E8)=60；interval(0x5F128)=16；last_t(0x5F120) 每帧变化；vsync(0x594EC)=**0**（lead 预期为全局默认 1，实测 0 —— 一并记录）。`[本次实测]`
- **判决**：按 lead 判据，运行时确实是 210 ⇒ 存在静态扫描未覆盖的写入路径（如经寄存器/`memcpy`/配置结构体的间接写）或配置覆盖。W90 的 clamp=210 **不是读取口径问题**。原始 dump 16 dword 已落盘（`ddraw_globals_probe.json` 的 `dump`/`dump_raw_hex`）。`[本次实测]`
- 过程记录：trip_P1/P2 探测失败（64 位观察者 Toolhelp 枚举 WOW64 模块列表为空，"ddraw.dll not found in module list"）；已改用 psapi `EnumProcessModulesEx(LIST_MODULES_ALL)` 兜底后在 P3 成功。`[本次实测]`

## U-4：v1 判读带（C6/CTRL_C6 跨趟比较）在本设计上不可用
- 对象数 7 倍差 ⇒ CPU 消耗率跨趟不可比（lead 采纳，DISAGREE D-2）。v1 两带仅对「对象数=1522」的布局有效。`[静态推断]`
