# W150 DISAGREE — 与既有结论/Lead 预期不符之处

格式：「我预期 X，实测 Y，因此 X 错」。

## D-1（我的自我纠错，最重要）

**我预期**：`0xA83C98` 是一个 `DynamicVectorClass<Screen*>` —— "画面栈"，元素是各 UI 屏，
`0x52D9A0` 每屏遍历它并 `call [vtable+100]`，因此"当前屏"可从这个数组推出。
支持这个预期的证据看起来很强：`0xA83C98+4=0xA83C9C(Items)`、`+8=0xA83CA0(Capacity)`、
`+0xC=0xA83CA4(IsInitialized)`、`+0xD=0xA83CA5(IsAllocated)`、`+0x10=0xA83CA8(Count)`、`+0x14=0xA83CAC(CapacityIncrement)`
—— **与 R11_COMMON §3.3 记载的 `DynamicVectorClass` 布局逐字段吻合**，且 `FUN_005113F0` 确实把 `this` 追加进该表。

**实测**：查 `W130_atlas\vtables_canonical.json`（`work\w150_vtclass.py`，`EVIDENCE\w150_vtclass.log`）：

```
0x007EAB58  class=.?AVHouseTypeClass@@   col_offset=0
0x007EAB3C  class=.?AVHouseTypeClass@@   col_offset=4
0x007EAB34  class=.?AVHouseTypeClass@@   col_offset=8
0x007EAB2C  class=.?AVHouseTypeClass@@   col_offset=12
0x007EAC08  class=.?AV?$TypeList@PBVInfantryTypeClass@@@@
0x007EABE8  class=.?AV?$TypeList@PBVUnitTypeClass@@@@
0x007EABC8  class=.?AV?$TypeList@PBVAircraftTypeClass@@@@
```

⇒ `FUN_005113F0` 是 **`HouseTypeClass` 的构造器**（4 基表 vptr + 3 个 `TypeList` 成员），
`0xA83C98` 是 **HouseTypeClass 注册表**，`vtable+100` 是 `HouseTypeClass::Read_INI(CCINIClass&)`，
`[0x887048]` 是 `CCINIClass` 实例。这段代码是**开局重读所有房型 INI**。

**因此 X 错**：`0xA83C98` 不是画面栈，"遍历数组 call vtable+100" 不是"每屏更新"。
**推论教训**：`DynamicVectorClass` 布局吻合只能证明"这是个动态数组"，**不能证明元素类型**；
元素类型必须查 vtable → COL 类名。这与台账"§3'7 已累积 9 类形态/规模近似失败"是同一族错误，
我差点贡献第 10 类。

## D-2（对台账 §883-3 表述的一处限定）

**台账 §883-3 写**：`0x6474C7` 末尾**无条件**调用消费者 `0x64C380`（2,474 B，遍历全环）。

**实测**（`EVIDENCE\w150_sweep.log` PART4 的 `0x647260` 反编译）：消费者只在
`(A8D5F8 & 2) != 0` **或** `[0xA8B238] ∈ {0,5}` 的路径上被调用。
当 `(A8D5F8 & 2) == 0`（默认）且 `[0xA8B238] ∈ {1,2,3,4}` 时，走的是 `FUN_006475F0()`（Queue.CPP 泵）**然后 return**，
**不经过 `0x64C380`**。

**因此**"无条件"这个限定在**正常游戏（非 -ATTRACT/-MPDEBUG）的多人模式**下不成立。
不影响 §883 对①的主结论（那条路径确实每帧跑），但**引用时必须加条件**。

## D-3（对台账 §886-6-2 的进展，非推翻）

**台账 §886-6-2 写**：「未找到"当前画面 ID"这种内部量」。

**实测**：我确认了这条**在"单一 dialog ID 全局"意义上仍然成立**（见 NAV_STATE §4.1：换屏状态机是 `0x52D9A0` 的
**局部变量** `iVar11`，各对话是模态 HWND，"当前屏"只活在栈上）。
但**进展**是：找到了两个**可外部读**的替代量 —— `[0xA8B238]`（模式，其中 0/5 已由 Lead 真机定死）
与 `[0xB0B59C]`（局内模态循环 HWND，`[静态推断]`）。

⇒ 这不是"推翻 §886-6-2"，而是把它精确化为："没有 dialog ID 全局；但模式选择器 + 局内 HWND 两个量足够做导航判别"。

## D-4（对 Lead §887-1 的一处补注，不矛盾）

**Lead 报**：`[0xA8B238]` 实测 `0`=主菜单、`5`=局内。

**静态侧完全一致**，但要提醒一处**反直觉**：
每帧泵 `0x647260` 的 6 路分派**把 `{0,5}` 当同一类**（`jt[0]=jt[5]=0x6474DC`）。
即：**"泵在跑/事件在产"不能证明"在局内"**，因为主菜单与局内走的是同一条泵路径
（`jt[1..4]` 的 `Queue.CPP` 泵反而是网络画面专用）。
⇒ 若要判"是否在局内"，只能读 `[0xA8B238]` 的**数值**或 `[0xA8ED84]` 的**增量**，不能读泵的活跃度。

## D-5（对我自己工具的一处缺陷）

**我预期**：`work\w150_bytescan.py` 能独立复现**全部**写点。
**实测**：`0xA8ED80` 字节扫描 **0 命中**，而 Ghidra 报 `write=1`（`0x7778CE` `MOV [0x00a8ed80],AL`）。
原因是该指令用 **`A2`（`mov [disp32],al`）** moffs 形式，而我的模式表只收了 `A3`（`mov [disp32],eax`）。
⇒ **我的扫描器不完整**（另缺 `81/83` 组的 `or/and/xor [a],imm`）。
本卡未重扫，登记为 `UNKNOWNS.md` U-9。凡本卡"写点数"结论，凡涉及 byte 全局的，都以 Ghidra 侧为准并注明。

---

## 无异议的部分（供 Lead 对账）

以下既有结论本卡独立复核**一致**，无异议：
- `[0xA8B238]` 有 **30 个写者**（§3.4 / §883-1）：本卡用两条独立证据链各得 30。
- 写者分布在 `0x52D9A0`(Init.CPP)、`0x48CCC0`(Conquer.CPP)、`0x5EF7xx`、`0x67E440`、`0x77B2A0`：与台账 §883-1 列的 `0x5EF7xx/0x67E440/0x77B2A0` 一致。
- `0x52D9A0` 与 `0x48CCC0` 写入 **0/3/4/5**（§3.4）：本卡确认 `0x52D9A0` 写 3/4/5/0，`0x48CCC0` 写 0。
- `[0xA8ED80]` 全镜像**唯一写者 `0x7778CE`**（§3689 行）：本卡 Ghidra 侧 `write=1` @`0x7778CE`，一致。
- `0x55DE6A` 是 `[0xA8ED84]` 唯一的 inc 型推进点（§3.4）：本卡侧 `0x55D360` 内 `mov [0xA8ED84],edx` @`0x55DE81`，与"每帧 +1"相容（写点 VA 差异属指令起始/操作数位置口径）。
