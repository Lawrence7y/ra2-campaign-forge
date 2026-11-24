## §6xx [待编号] gamemd.exe 静态调用面与地图预置实体因果链核定

> 依据：`lead/re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md`（六探针 100% 复现门 PASS）  
> 靶件：`ra2bench/gamemd.exe` (sha256 `73201cc02149...`, 4,825,360 B)  
> 性质：纯静态二进制与磁盘文件一手读数，严格剔除未证机制推论。

### 1. 【已证】全镜像虚派发与 slot2 调用面
1. **直接调用为零**：全 `.text` 针对 `0x54A4F0` 与 `0x54A630` 的 direct `call/jmp` 及绝对间接 `FF 15/25` 均为 0 处；全局仅在虚表 `0x7ECBFC` (基类) 与 `0x7ECBDC` (派生类) 的 slot2 分别物化一次（`slot2_fullscan_20261111/_sf_scan_out.txt:L13-L20`）。
2. **唯一实效调用点**：全镜像普查 `call/jmp [reg+8]` 共 1714 处，回溯与污点分析证实能指向上述 slot2 的调用点全镜像唯一：`0x00546069`（`call dword ptr [eax+8]`），其 this 来源固定为 `0xAA1078`，vptr 来源于 `[0xAA1078]`（`slot2_fullscan_20261111/_sf_scan_out.txt:L43-L47`）。
3. **0x0054A56E 静态覆盖**：`0x0054A56E`（`mov [esi+4], 0`）仅在旧缓冲已分配时执行；执行后 9 字节即被 `0x0054A577`（`mov [esi+4], edi`）无条件覆盖，两点间无读取与调用；`Vector==0` 时控制流直接跳过置零点（`re_crashwriter_static_20261110/_cw_disasm_out.txt:L66-L68`）。

### 2. 【已证】地图预置单位与文件独立性
1. **XMP29U2.MAP 实体计数**：`scratch/boot_probe/arm_a/XMP29U2.MAP` (311,822 B) 含 Units 3360、Infantry 2240、Structures 0，共 5600 预置单位；严格按 14 个 owner 分为 14 条带，每带恰 400 实体（240 车 + 160 步），14 组坐标范围与台账 §2.6 完全吻合（`re_orphan_owners_20261110/_oo_map_out.txt:L56-L101`）。
2. **文件对应关系**：该地图 `[Houses]` 声明的 14 个 house 与文件中 14 个带 `Country=` 的 house 节严格一一对应；14 节中 `PlayerControl=no` 全为 no（`re_orphan_owners_20261110/_oo_map_out.txt:L28-L48`）。
3. **三份地图物理互异**：XMP29U2.MAP (311,822 B)、大版 yrm (92,332 B，含 41 建筑) 与小版 yrm (25,604 B，0 建筑) 为彼此独立的不同文件，排除压缩/变换等价性（`re_loadbench_diff_20261110/_ld_diff_out.txt:L88-L103`）。

### 3. 【已证】控制字段静态字面语义
1. **PlayerControl**：位于 `0x824E28`，由 `HouseClass::Read_INI` (`0x500B40`) 写入 `HouseClass+0x1ED`，仅作用于战役起始资金计算与 AI 难度分支，全镜像 8 处 `HouseClass` 创建点均未读取此标志（`playerctrl_semantics_20261111/_ps_disasm_out.txt:L113-L147`）。
2. **PercentBuilt**：位于 `0x8189A0`，解析写入 `HouseClass+0x571C`，全 `.text` 直接读指令数为 0（`playerctrl_semantics_20261111/_ps_disasm_out.txt:L36-L39`）。

### 4. 【待证】（严禁以机制入账）
1. **0x0084F2BA 故障性质**：该地址仅为历史真机崩溃弹窗记录值，其是否为 DEP 取指违规或受 vtable 破坏触发【未定谳】（缺活体转储/栈回溯证据）。
2. **引擎 HouseClass 运行期实例数**：单图文本一一对应推不出引擎机制；遭遇战路径（meta_count=4）与战役路径（14 实例）的运行期驱动【未证】（缺 0x4F54A0 动态拦截日志）。
3. **PercentBuilt 间接读点**：全镜像是否存在基类指针别名或虚函数回调读取【未验】（缺全量间接读点普查）。
