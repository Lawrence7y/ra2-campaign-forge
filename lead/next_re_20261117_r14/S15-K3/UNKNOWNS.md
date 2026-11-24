# UNKNOWNS.md — S15-K3 未决/不可定清单

## U1 · named(S) 补 2 后仍差 4（未达标，如实报）
- 盘上基线 137/158；本卡 +2 ⇒ 139/158 = 87.97%；门槛 143（90%）⇒ **差 4 个名字不可定**。
- 当前不够 named(S) 的 21 行（全 `sub_` + `[未证]`）：
  `006D0F00,006D6070,006E1830,006E2A10*,006E2AA0*,006E4790,006E47C0,006E6310,006EA3E0,006F1920,0070F120,0071FA30,00721270,00726910,00727AA0,0072DDB0,0072DEF0,00751590,00752460,00763610,00763690`
  （`*` = 本卡已命名 2 条）。剩 19 条未具名。

## U2 · S15-K2 的 5 条"非唯一-call 动作候选"——复核后仍不可定（不编名）
S15-K2 U2 点名的 5 条，本卡逐条真取证，结论：**均保持 `sub_`，不可定**。证据见
`EVIDENCE/handler_calls_dump.txt`、`EVIDENCE/handler_detail.txt`、`EVIDENCE/candidates_disasm.txt`、`EVIDENCE/xref_sweep.txt`。
- `006D6070`（疑 CenterCameraAtWaypoint/ID112）：handler `0x6DF795` 内 6 个 call，此函数仅为
  waypoint→cell 坐标换算 + 写相机目标字段 `[edi+0xd64/+0xd68/+0xd74/+0xd78]` 的子步；调用者 14 处
  （跨 HouseClass/MapClass 等多个类，非 TActionClass 专属），`this` 字段偏移 `+0xb0/+0xb4/+0xd64`
  远超 TActionClass size 0x94 ⇒ 不是动作实现体，是共享 helper。无权威名 ⇒ 不可定。
- `006E1830`（疑 PlaySoundEffectAtWaypoint/ID99）：n_callers=1（唯一来自 ACT99 handler `0x6DE871`），
  但函数体 = waypoint 双字→packed CellStruct→`MapClass::TryGetCellAt(0x5657A0)` 取格，再 `0x47C520/0x47C550`
  取格状态；是"坐标→Cell"子步，非声音播放本身（播放由同 handler 的 `VocClass::PlayIndexAtPos` 完成）。
  YRpp 该动作为 `PlayAudioAtSpecificWP=0x6E18B0`（另一地址），本行无权威名 ⇒ 不可定。
- `0070F120`（疑 TalkBubble/ID105）：handler `0x6DF588` 内 2 次调用本行；本行体写全局
  `[0xB0EB38/3C]`、`[0xB0EA70/74/78]` + 虚调 `[eax+0x48]` + `0x5673A0`；YRpp `TalkBubble=0x6E4040`
  是 wrapper（size 54）调本行两次，属 talk-bubble 显示子步；本行无权威名 ⇒ 不可定。
- `0072DDB0` / `0072DEF0`（疑 PlayMovie/ID10）：同一 handler `0x6DE72F` 内两次不同调用。字节自证
  二者是**配对初始化/清理**：DD-B0 首检查 `byte[0xB0FBE0]`、末置 1，内部 11×`call 0x4A38D0` 载串指针；
  DE-F0 首清零 `[0xB0FBE0]`、8×`call 0x7C8B3D`(free) 释放、`call 0x534DE0` 收尾。二者确为同一状态机的
  begin/end，但 YRpp `PlayMovie=0x6E16D0`（第三个地址），两者皆非该 ACTION_FUNC 本体，无可引用权威名；
  给任一叫 "PlayMovie" 都会错配另一半 ⇒ 不可定。

## U3 · 事件派发 L1 的 12 个 handler 不是 atlas 入口，不能补 named
- L1 `0x71F218` 12 项 = `0x71EC33/EBE9/EB53/EB75/EB9E/EBC0/EAE7/EB06/EB28/E96B/EA30/EC63`，
  实测**均不在 atlas、不在 coverage**（`EVIDENCE/vtable_scan.txt` 前段）。它们是
  `TEventClass::HasOccured(0x71E940)` 函数体内的跳表目标（内部标签），非独立入口 ⇒
  派卡提示的"若 L1 有无名直接定"在本盘面不成立（12 个都已由覆盖 `HasOccured` 名涵盖，无 named 增量）。

## U4 · 虚表/字符串路径对 21 条全空
- `.rdata` 全节扫 21 条 entry 作虚表槽值：**全 0 命中**（`EVIDENCE/vtable_scan2.txt`）⇒ 无 vtable 槽语义可借。
- YRpp 全树 1,675 个地址字面量精确匹配 21 条：**仅 2 命中**（DeleteTrigger/ForceTrigger，本卡已用）。

## U5 · 完整字段布局 / INI 键 / 真机
- 继承 S15-K2 U3/U4/U5：字段表、INI 键枚举、真机验证非本卡范围；本卡静态取证足够支撑 2 条命名与 T3。
