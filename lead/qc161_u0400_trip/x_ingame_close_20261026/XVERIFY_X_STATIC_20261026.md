# XVERIFY_X_STATIC_20261026 — 独立异族复核：C26-06 静态链 A–E + X 三臂设计

**核验模型身份**：`new-provider-3/qoder-cn:qfmodel`（异族于执行者 DeepSeek/dfmodel；本判定书为 qfmodel 亲验）。
**日期**：2026-10-26
**性质**：只读核验。零真机、零游戏进程、零 git、不改被审对象。唯一写入=本件。
**被审对象**：
- 镜像快照 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020/gamemd.exe`
- 设计件 `lead/qc161_u0400_trip/x_ingame_close_20261026/X_CONTROL_DESIGN_20261026.md`
- 驱动候选 `lead/qc161_u0400_trip/_drive_c2_x_probe.py` / GLM 探针 `_probe_x_glm_addr_check.py`

**开工断言（亲跑）**：`sha256(gamemd.exe)=73201cc021497c95 67742f718bf1dc78...` ⇒ 前缀 `73201cc021497c95` **PASS**。
工具：capstone 5.0.7 + pefile；image_base=0x400000（pefile 独立读出）；`.text` VA 0x401000..0x7E038D，`.detour` VA 0xB93000（仅数据，无可执行代码，无 exitstate 引用）。VA→file 走节表（非 `va-0x400000` 朴素式）。

---

## X1 — A 泵头（`0x5D4D50`）**CONFIRMED**

亲读字节（`b_at(0x5D4D50)`）：
```
005D4D50: a1 50 35 b7 00   mov eax, dword ptr [0xb73550]
005D4D55: 83 ec 1c         sub esp, 0x1c
005D4D58: 85 c0            test eax, eax
005D4D5A: 53               push ebx
005D4D5B: 55               push ebp
005D4D5C: 56               push esi
005D4D5D: 57               push edi
005D4D5E: 0f 84 02 01 00 00  je 0x5d4e66      ; 距离=0x102
```
je 目标 `0x5D4E66` 亲读=**完整函数收尾**：
```
005D4E66: 5f pop edi / 5e pop esi / 5d pop ebp / 5b pop ebx / 83 c4 1c add esp,0x1c / c3 ret
```
⇒ 「hwnd 全局 `[0xB73550]`==0 时泵直接返回、不取消息」是**字节级成立**（`test`/`je`→epilogue→`ret`，中间无任何 PeekMessage 调用）。
唯一口径瑕疵（不改判定）：断言件把「5 条指令」表述为 `mov/test/je` 紧邻，实际 `test eax,eax`(0x5D4D58) 与 `je`(0x5D4D5E) 间夹 4 条 `push`（寄存器保全）。**语义与 je 目标均字真**。CONFIRMED。

## X2 — B 写值 edi=1（`0x6BE08C` / `0x6BE0B6` / `0x6BE0E1`）**CONFIRMED**

三处亲验字节：
```
006BE08C: bf 01 00 00 00        mov edi, 1          ; edi=1 是该宿主常量
006BE0B6: 89 3d d8 ed a8 00     mov dword ptr [0xa8edd8], edi   ; 闩 1（写 edi）
006BE0E1: 39 3d d8 ed a8 00     cmp dword ptr [0xa8edd8], edi   ; ★ 第二操作数=edi 寄存器（不是立即数、不是别的寄存器）
006BE0E7: 74 f3                 je 0x6be0dc          ; 相等→回环（环头=call 泵）
```
`cmp [0xa8edd8], edi`：`39` = `cmp r/m32, r32`，modrm `3d` → reg 字段=`edi`，r/m=disp32 → `[0xa8edd8]`。**寄存器操作数亲验=edi**。
另核「edi 在 B6→E1 间不被覆写」：`0x6BE0B6..0x6BE0DC` 逐条反汇编，**无任何以 edi 为目的的写**（仅 mov ecx/call/push ebx）⇒ cmp 比较的确仍是 1。
「bail 站点判据=exitstate==1」的字节根**坐实**。CONFIRMED。

## X3 — C 块 `0x7777F3..0x777828`**CONFIRMED（字节逐条真）+ 一处口径修正（非 REFUTED）**

逐条亲读，与断言件严丝合缝：
```
007777F3: 8b 0d 68 73 88 00   mov ecx, [0x887368]        ; singleton
007777F9: 3b cb               cmp ecx, ebx
007777FB: 74 0c               je 0x777809
007777FD: 8b 01               mov eax, [ecx]
007777FF: 6a 01               push 1
00777801: ff 10               call dword ptr [eax]        ; slot0
00777803: 89 1d 68 73 88 00   mov [0x887368], ebx         ; ★ 清 singleton
00777809: a1 d8 ed a8 00      mov eax, [0xa8edd8]         ; exitstate 旧值
0077780E: 89 1d 50 35 b7 00   mov [0xb73550], ebx         ; ★ 清 hwnd
00777814: 3b c3               cmp eax, ebx                ; 旧==0?
00777816: 74 0a               je 0x777822
00777818: c7 05 d8 ed a8 00 02 00 00 00  mov [0xa8edd8], 2  ; 非0⇒写2
00777822: 5f/5e/33 c0/5b/59  pop edi/esi / xor eax,eax / pop ebx/ecx
00777828: c2 10 00            ret 0x10
```
(a) **清 singleton/hwnd 的无条件性**：`mov [0x887368],ebx`(0x777803) 在 `je 0x777809` 之后 —— je 恰**跳到** 0x777809，**绕过的只有 slot0 调用与 singleton 清零**；`mov [0xb73550],ebx`(0x77780E) 无条件执行（两条入环路径都经过它）。⇒ 「清 hwnd 无条件、清 singleton 依赖 singleton≠0」——与设计一致（设计称「进入即清两全局」，严格说 singleton 清零是「若原≠0 才清为 ebx=0」，结果仍归 0）。
(b) **写 2 仅当 exitstate≠0**：`cmp eax,ebx / je 0x777822`——旧值==ebx(0) 则跳过 `mov[..],2`。**字真**。
(c) **ebx==0 依据（进入块前）**：本块所在 WndProc 序言 `0x7775C0`：
```
007775C8: 33 db   xor ebx, ebx     ; ★ ebx=0，位于 push ecx/ebx/esi/edi 之后、cmp ecx,ebx 之前
00777687..: 消息分派 cmp eax,0x18 / lea ecx,[eax-1] / cmp ecx,0x13 / mov dl,[ecx+0x777a98] / jmp [edx*4+0x777a80]
```
分派到本块**唯一入口**=跳转表 `0x777A84` 槽位（全镜像无直接 `jmp/jcc` 目标=0x7777F3，仅索引表项→0x7777F3）。`xor ebx,ebx`(0x7775C8) 之后、块头之前，路径上**无以 ebx 为目的的写**（0x777826 等 `pop ebx` 属**兄弟 handler 收尾 epilogue，其后即 jmp 0x7779b5/ret**，不在通往 0x7777F3 的分派直路上）⇒ **块内 ebx 恒=0**，`cmp ecx,ebx`/`mov [..],ebx` 确在「比 0 / 写 0」。**成立**。

**★ 一处口径修正（不影响本块字节判定，须记入运行期语义）**：亲解分派映射（case-byte 表 `0x777A98`：`00 01 02 05 ...03 05 04`，idx=uMsg−1；跳转表 `0x777A80`：`[0x77778D,0x7777F3,0x7777CE,0x7776B5,0x777781,0x7779B9]`）：
- `cb==1 → 0x7777F3` 对应 **uMsg=2 = WM_DESTROY**，不是 WM_CLOSE；
- **WM_CLOSE(0x10, idx=15) → cb=5 → 0x7779B9（默认转发，call 0x54F790，非 DefWindowProcA）**。
⇒ 本块是 **WM_DESTROY 处理器**；WM_CLOSE 须经 DestroyWindow→WM_DESTROY 链（或引擎转发后触发）才到达此块。断言件/设计件 §1b-C 直接称「WM_CLOSE 处理块」为**过度标注**——但其字节、语义、及对菜单臂「两全局归零」的解释**仍字真**（菜单臂观察到的正是该链末端效果），且设计 §1b-D 已诚实记「支甲/支乙运行期未分、留 P3 判」。故 X3 判 **CONFIRMED（块字节真）+ 记「块绑定 WM_DESTROY 非直接 WM_CLOSE」的标签修正**。

## X4 — 第二宿主等待环 `0x6BEC60..0x6BEC9B`**CONFIRMED**

亲读字节：
```
006BEC60: a1 50 35 b7 00      mov eax, [0xb73550]
006BEC65: 56                  push esi
006BEC6A: be 01 00 00 00      mov esi, 1                     ; esi=1
006BEC71: 50                  push eax
006BEC72: 89 35 d8 ed a8 00   mov dword ptr [0xa8edd8], esi  ; 进环前写 1
006BEC78: ff 15 ac 14 7e 00   call dword ptr [PostMessageA]
006BEC7E: a1 50 35 b7 00      mov eax, [0xb73550]
006BEC83: 85 c0               test eax, eax
006BEC85: 74 16               je 0x6bec9d                    ; hwnd==0→出环
006BEC87: e8 c4 60 f1 ff      call 0x5d4d50                  ; ★ 环头=调同一泵
006BEC8C: 39 35 d8 ed a8 00   cmp dword ptr [0xa8edd8], esi  ; exitstate==1?
006BEC92: 75 09               jne 0x6bec9d                   ; ≠1→出环
006BEC94: a1 50 35 b7 00      mov eax, [0xb73550]
006BEC99: 85 c0               test eax, eax
006BEC9B: 75 ea               jne 0x6bec87                   ; hwnd!=0→回环
```
⇒ 环判据 = **hwnd≠0 且 exitstate==1**（双检 0x6BEC8C 与 0x6BEC94..9B），进环前 `mov esi,1@0x6BEC6A` + `mov [exitstate],esi@0x6BEC72`。与宿主 A **同构的另一条 bail 等待**。**引擎原生 bail 等价物坐实**。CONFIRMED。

## X5 — 支甲/支乙矩阵完备性**CONFIRMED，且结论被强化（非弱化）**

**本核独立普查（不抄断言件的「2」）**：全 `.text`+`.detour` 扫绝对寻址 `modrm(abs32)`（`mod=00,rm=5`）与 `mov acc,[abs]`（`A1/A3`）两式，disp32==`0xA8EDD8`：

| VA | 字节 | 助记 | 角色 |
|---|---|---|---|
| 0x6BE0B6 | `89 3d d8 ed a8 00` | mov [..],edi(=1) | **写**（闩 1） |
| 0x6BE0E1 | `39 3d d8 ed a8 00` | cmp [..],edi | 读（A 闸门） |
| 0x6BEC72 | `89 35 d8 ed a8 00` | mov [..],esi(=1) | **写**（闩 1） |
| 0x6BEC8C | `39 35 d8 ed a8 00` | cmp [..],esi | 读（B 闸门） |
| 0x777809 | `a1 d8 ed a8 00` | mov eax,[..] | 读（C 块旧值） |
| 0x777818 | `c7 05 ..02 00 00 00` | mov [..],2 | **写**（推进） |

**总计 = 6 个引用点（3 读 + 3 写），非 2。** 交叉验证：全镜像字节 `D8 ED A8 00` 出现 **6 次**（全为上述指令 disp32），`.detour`/`.rsrc` **0 次** ⇒ 无数据指针间接寻址、无 `lea reg,[abs]`、无隐藏第三/第四写者。
**(a) 「必先进入宿主」覆盖性**：写 exitstate=**1** 的点**恰两处**（0x6BE0B6/0x6BEC72），与两宿主一一对应，**无第三个写 1 的点**。写非零者另有 0x777818，但写的是 **2**（退出推进，且在 C/WM_DESTROY 块内，设计已列为 C）。
**★ 关键强化项（正是审稿点名要防的弱化）**：普查中**不存在任何把 exitstate 写 0 的点**（无 `mov [..],0`、无算术归零+store、`test [..],..`(0x85) 已排除非 store）。⇒ 局内 +149 s 观测 `exitstate=0` **不可能**是「曾被写 1 后又被清零」——只能是**从未被任何写者触碰**。
∴ 设计 §1b-D「局内 +149 s exitstate=0 ⇒ 两宿主均未进入」**成立且不弱化**：两宿主进入前必先写 1（X2/X4 字真）+ 无清零写者 ⇒ exitstate=0 ⟺ 两宿主未达。bail 站点 0x6BE0E1（宿主 A 环内）未达。**X5 判 CONFIRMED，独立性复核反而加固其结论**。（诚实附注：静态普查穷尽绝对寻址；相对间接寻址在本 PE 不存在，故完整。）
**(b) frame=0 读法漏项核查**：`G_FRAME=0xA8ED84` 独立普查 = **9 个写点**，含 **3 处显式 `mov [..],0`**（0x5B7329/0x5E747C/0x795234）⇒ frame=0 **确有其它复位路径**，单凭它**不能**断定泵停（可能是别处归零）。设计 §0/§1b-D **未在此过度主张**（明文「不凭 frame=0 断定卡死环节」，且只用它作「离战斗循环」相容旁证）。此口径**合规**。

## X6 — GLM 地址作废复核**CONFIRMED（作废这步本身正确）**

亲跑 `_probe_x_glm_addr_check.py`（内部含 `sha16==73201cc021497c95` 断言，PASS）+ 自读字节：
- **负控双锚 PASS**：`0x6BE0E1`=实读 `393dd8eda800`（cmp [..],edi）✓；`0x6BE0E7`=`74f3`✓ ⇒ 解码器/映射正确，未误杀真锚。
- **GLM 转述 FAIL**：`0x5F4855` 期望 `83f810`(cmp eax,0x10)，实读 `4a048b`（`dec edx`）✗；`0x5F4869` 期望 `e8`(call)，实读 `83`（`add esp,0x18`）✗。
⇒ 转述地址组字节不符、**作废正确**，负控证明作废非因解码错误。**CONFIRMED**。

## X7 — 设计口径审读**CONFIRMED（三处自陈与盘面实测一致）**

对照 REVIEW「必须纠正的证据口径」7 条，逐核设计 §0/§1b-D/§1c：
1. **exitstate 单通道定位断点**（禁）：§0 明文「不得宣布：不凭 exitstate 恒 0 定位断点」；§1b-D 只用字节链 + 存盘点，**未单通道定位**。✓ 无残留。
2. **关窗前证据替代关窗后**（禁）：§1b-D 明确「post-close singleton/hwnd 未采样」「~1489 行中间样本采而未存」「盘面证不了 frame 何时归零」；§2 每臂只读面含**关窗前 5 s + 关窗后截屏**双段。✓ 已改。
3. **静态可达=运行期必经**（禁）：§1b-D 标「静态+观测合成」「支甲/支乙运行期未分」「留 P3」；§0/§1b 未把可达当必经。✓ 无残留。
4. **缺省 0=显式 0**（禁）：§2 专列 **P2（键缺失/default）** 与 **P1（显式=0）** 双臂差分，正为实证「显式≠缺省」。✓ 已补。
5. **帧推进=零回归**（禁）：§0/§1b 无「帧推进即无回归」措辞；H4 明列「风险真实存在」。✓ 无残留。
6. **bare-LF=逐字节不变**（禁）：设计文 `逐字节不变` 出现 **0 次**、`帧推进` **0 次** ⇒ 无此类过度主张。✓ 无残留。
7. **投递≠处理**：§0 记「PostMessageW 返回值未记录（驱动缺陷，已补）」；§2 只读面要求 PostMessageW 返回+GetLastError。✓ 已补。

**执行者本轮连错三次之重点复验（§1b-D 自陈 vs 实测）**：
- 「close_rows **只存末 6 行**」：`_drive_c2_l1_regress.py:445-446` 实读 `rec["close_rows_n"]=len(rows)`；`rec["close_rows_tail"]=rows[-6:]`。**逐字命中**。
- 「**无 head**」：驱动全文**从未** `rec["close_rows_head"]=...`（grep 仅 tail@446、n@445）；200938 与 161412 两份 `_rec.json` 键集实测 **`close_rows_head` ABSENT**（两趟均无）。**自陈与盘面一致**。
- 「+149 s 唯一在盘时点」：200938 `close_rows_n=1495`、tail 6 行、`closed_at_s=137.103`、观察窗 150 s ⇒ tail 落在 ≈+149.4~149.9 s；6 行全 `exitstate=0/frame=0/wait=258`。161412 同形（n=1494, head ABSENT, tail 全 0）。**实测复现**。
- 「post-close 两全局未采样」：`close_rows_tail` 列集实测=`{t,wait_res,exitstate,frame}`，**无 singleton/hwnd 键**；两趟一致。**自陈属实**（pre-close 才采 singleton=0x887368/hwnd=0xb73550，见 404 行 `snapshot_globals`）。
⇒ **X7 CONFIRMED**：设计 §1b-D/§0/§1c 三处自陈与 `_drive_c2_l1_regress.py:446` 实际存盘代码、200938/161412 实际 `_rec.json` 键**完全一致**；7 条禁令无残留过度主张。

---

## 总判定

**静态链字节坐实（强）**：A（泵头 hwnd==0→epilogue→ret）、B（edi=1 常量 + B6 写 + E1 寄存器 cmp）、C（WM_DESTROY 块逐条真 + ebx==0 证成 + 清 hwnd 无条件 / 写 2 仅当旧≠0）、D 的**分支推演前提**（+149 s exitstate=0 ⇒ 两宿主未达，经**独立 6 点普查 + 零清零写者**加固）、E（修复域界定，符合 C26-06 禁止面）—— **A/B/C/X4 四环字节级 CONFIRMED**。

**须记的标签修正（非 REFUTED）**：§1b-C 把 0x7777F3 块**直接称为「WM_CLOSE 处理块」**——亲解分派映射证其为 **WM_DESTROY(2) 处理器**；WM_CLOSE(0x10) 走默认转发 0x54F790，须经 DestroyWindow 链才达本块。**块字节/语义/菜单臂归零解释均字真**，设计亦已把「支甲（C 已执行）」留 P3 判运行期，故此为**命名精度问题**，不推翻结论，但**交审阅前应将 §1b-C 标签改为「WM_DESTROY 处理块（经 WM_CLOSE→DestroyWindow 链到达）」**。

**三臂设计可交审阅=是**。X5 审稿最忧的「exitstate=0 或被写 0 清零」被本核证**不可能**（无零写者），故 §1b-D「局内失败不记 c″ 账 / 跨支鲁棒」在字节面稳固。X6 GLM 作废这步本身经负控双锚证真。X7 执行者本轮重点复验项（head/tail/两全局）**三处自陈与实测全一致**，无谎报。

**遗留（非本审 REFUTED，属下一轮义务）**：支甲 vs 支乙、本块是否真被 WM_CLOSE 链触发、PostMessageW 返回值、菜单态 frame=0 旁证仅 133604 `traj_frame` 单趟（`distinct_n=1`, 末 15.41 s=0）——均设计已声明「运行期未分、待 P3/P0/P3m」，符合 REVIEW。

**判定：X1 CONFIRMED / X2 CONFIRMED / X3 CONFIRMED（字节真）+ 标签修正记入 / X4 CONFIRMED / X5 CONFIRMED（独立数=6 引用点·3 写·0 清零写者，结论强化）/ X6 CONFIRMED / X7 CONFIRMED。零 REFUTED，零 UNVERIFIABLE（静态可达范围内）。**
