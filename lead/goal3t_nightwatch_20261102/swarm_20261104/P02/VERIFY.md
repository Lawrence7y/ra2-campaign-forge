# P02-VERIFY · 核验报告：焦点旗标睡眠自旋（REPORT.md 全 keyFact 字节复算）

**核验员**：P02-V（独立复算，不采信原报告结论，全部从 gamemd.exe 字节重解）
**日期**：2026-11-04 · 对象：`P02/REPORT.md`（swarm_20261104）
**总裁决**：**CONFIRMED**（8 条 keyFact 全部字节复现；3 处措辞/口径瑕疵已逐条列出，均不动摇结论）
**核验探针**：`_p02v_probe.py` / `_p02v_probe2.py`（本目录，只读镜像，只写本目录），输出 `_p02v_out.txt` / `_p02v_out2.txt`

---

## 0. 现场自证（亲跑）

| 项 | 复算值 | 命令 |
|---|---|---|
| 真机零占用 | gamemd.exe / ra2loader.exe / YURI.exe 均无任务 | `tasklist //FI "IMAGENAME eq gamemd.exe"`（另两同名）→ `信息: 没有运行的任务匹配指定标准。` |
| SHA256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` = 冻结件 | `python -I -X utf8 _p02v_probe.py` |
| eng.coverage | `(99.99837567729335, 1394120, 66)` = 99.9984% / 1,394,120 insns / 66 重同步 | 同上（与原报告自报值逐位一致） |

---

## 1. 逐条裁决

| # | keyFact | 裁决 | 复算要点 |
|---|---|---|---|
| KF1 | MLF 等待块字节（0x55D37C 闩 / 0x55D385 jne 跳整块 / 唯一回边 0x55D3AE / Sleep(10) 支单发 / 环仅 GameMode∈{0,5}） | **CONFIRMED**（1 处窗口口径瑕疵，见 §3-N1） | 见 §2.1 |
| KF2 | 泵 0x5D4D50=真消息泵：DispatchMessageA IAT 亲解、闭包 [0x5D4D50,0x5D4E6E) 恰 1 ret、hwnd==0 短路且计数不加 | **CONFIRMED** | 见 §2.2 |
| KF3 | [0xAA0444] 6 写者、置 1/2 需 "wb"/"rb"+0x40 成功、BSS 初值 0、mode2 仅分派 WM_PAINT | **CONFIRMED**（"_fsopen" 身份保持原报告的 [推导] 标注，正确） | 见 §2.3 |
| KF4 | hwnd 恰 3 写者 + 0x7778CE 写链 al≡(wParam!=0)，与 r063a T2 逐字节一致 | **CONFIRMED** | 见 §2.4 |
| KF5 | 时间量级：{0,5} 周期≈0.500–0.516s、21.156s≈42–43 轮、3/4 单发无冻结能力 | **CONFIRMED**（24.73s 轮数上限口径见 §3-N2） | 见 §2.5 |
| KF6 | 普查 46=45R+1W / CurrentFrame 1007 / GameMode 570 vs doc:88 571 / 泵计数 7 写者=r063a RA4 / Focus 字符串 | **CONFIRMED** | 见 §2.6 |
| KF7 | 文档裁决：r063a 对、「快进」错、doc:216-217 漏回边=结构错、doc:26 以偏概全、doc:477 内部已自我纠正 | **CONFIRMED**（并新发现 doc:477 自身字节笔误 a1/a0，见 §3-N3） | 见 §2.7 |
| PRED | 真机判别式（[0xA8ED80]==0、[0xAA0430] +4/2s、栈签名 0x55D3A2/A7、点击 ≤500ms 解冻、可证伪条件） | **CONFIRMED（仅逻辑/字节自洽审计，零真机未执行）** | 见 §2.8 |

---

## 2. 复算证据（逐条 VA + 字节，全部亲跑 `_p02v_probe.py`/`_p02v_probe2.py`）

### 2.1 KF1 等待块（[字节]）

亲解 `0x55D360..0x55D3D0` 与原报告 §2.1 逐指令一致：

```
0x55D377 a080eda800     mov al,[0xA8ED80]
0x55D37C c60558cdab0001 mov byte [0xABCD58],1      ; 每调用写闩 ✓
0x55D385 7534           jne 0x55D3BB               ; 跳过 0x55D387–0x55D3BA 整块 ✓（含两 Sleep+两泵）
0x55D387 8b35f0117e00   mov esi,[0x7E11F0]          ; IAT 亲解 = KERNEL32!Sleep ✓
0x55D38D a138b2a800     mov eax,[0xA8B238]          ; ←循环顶
0x55D394 7405           je 0x55D39B                 ; ==0 → 500 支 ✓
0x55D396 83f805 / 0x55D399 7517 jne 0x55D3B2       ; ==5 落 500 支 ✓
0x55D39B push 0x1F4 / 0x55D3A0 call esi / 0x55D3A2 call 0x5D4D50
0x55D3A7 a080eda800     mov al,[0xA8ED80]           ; 重查 ✓
0x55D3AE 74dd           je 0x55D38D                 ; 回边 ✓（0x55D3AE+2-0x23=0x55D38D）
0x55D3B2 6a0a / ffd6 / 0x55D3B6 call 0x5D4D50       ; Sleep(10) 支
0x55D3BB a184eda800     mov eax,[0xA8ED84]          ; 直落帧体 ✓
```

- 原始字节抽查 `0x55D377..0x55D391` = `a0 80 ed a8 00 c6 05 58 cd ab 00 01 84 c0 75 34 8b 35 f0 11 7e 00 a1 38 b2 a8` —— 与原报告引用串逐字节相同。
- **回边计数（复算）**：`loop_backedges(0x55D387,0x55D3BB)` = `[(0x55D3AE→0x55D38D, je)]` **恰 1 条**；`loop_backedges(0x55D3B2,0x55D3BB)` = `[]` —— Sleep(10) 支单发不回跳 ✓。全 MLF `loop_backedges(0x55D360,0x55DEE0)` = **6 条**（另 5 条为帧体 `jl` 环 0x55D5ED/0x55D9B7/0x55DA1E/0x55DAEF/0x55DB83，均不在等待块）。见 §3-N1。
- 闩不被环内清除：`disp_hits(0xABCD58)` 共 11 处，写者 = 0x55CC00(1)/0x55CC10(0)/0x55D15F/0x55D1ED/0x55D245/0x55D292(bl)/0x55D37C(1)/0x55D866(0)/0x55DEB6(0)/0x55DEC8(0) —— 等待块 [0x55D387,0x55D3BB) 内 0 处 ✓，环内恒 1。
- 冻结出口①：`0x55D371 je 0x55DECF` → `pop edi/esi/ebp; mov al,1; pop ebx; add esp,0x1b4; ret @0x55DEDB` 亲见 ✓。inc 块 `0x55DE73 8b1584eda800 / 0x55DE7E 42 / 0x55DE81 891584eda800` 亲见 ✓。

### 2.2 KF2 泵（[字节]）

- 边界闭包（复算，逐指令）：`[0x5D4D50,0x5D4E6E)` 内 98 条，**ret 恰 1 条 = 0x5D4E6D**，jcc/jmp 目标 0 逃逸；`0x5D4E6E/6F = 90 90` 填充；下函数 0x5D4E70 ✓。
- 短路序：`0x5D4D50 mov eax,[0xB73550]` → `0x5D4D58 test` → `0x5D4D5E je 0x5D4E66` → 计数链 `0x5D4D64 mov ebx,[0xAA0430] / 0x5D4D6C inc ebx / 0x5D4D77 mov [0xAA0430],ebx` **全部在 je 之后（地址序）** ⇒ hwnd==0 时计数不加 ✓；0x5D4E66–0x5D4E6C = `5f 5e 5d 5b 83 c4 1c`（四弹+退栈）→ 0x5D4E6D ret ✓。
- IAT 亲解 11/11 全中：0x7E14C0=USER32!DispatchMessageA、0x7E14BC=TranslateMessage、0x7E14F4=IsDialogMessageA、0x7E14F8=TranslateAcceleratorA、0x7E1484=PeekMessageA、0x7E14D4=CreateWindowExA、0x7E14D8=RegisterClassA、0x7E13C0=GetCursorPos、0x7E11E8/EC=Enter/LeaveCriticalSection、0x7E11F0=Sleep、0x7E1530=timeGetTime ✓。`0x5D4E47 ff15c0147e00` ✓；0x5D4E40 call ebp(TranslateMessage) ✓；过滤链双循环（[0xABFC94] 数组/[0xABFCA0] 计数；[0xABFCBC]/[0xABFCC8]）亲见 ✓；`[0xABFD34]` 全镜像恰 1 处引用（0x5D4E28 R，0 写）+ 该址属 BSS（.data vsz 0x367BE4 > raw 0x6C000，inraw=False）⇒ 恒 NULL ✓。
- 直呼泵者：对齐流 `call 0x5D4D50` 扫描 = **43 处**，含 0x55D3A2/0x55D3B6/0x55D830 与 WinMain 0x6BDD03/0x6BDD2E ✓。
- WinMain 忙等环：`0x6BDD03 call 泵 / 0x6BDD08 mov al,[0xA8ED80] / 0x6BDD0D test / 0x6BDD0F je 0x6BDD03`；第二环 `0x6BDD2E / 0x6BDD33 / 0x6BDD38 / 0x6BDD3A je 0x6BDD2E` —— 环体无 Sleep ✓。

### 2.3 KF3 队列模式（[字节]+[推导]）

- `disp_hits(0xAA0444)`：23 处引用；写者恰 6：0x53E2BD(esi)/0x53E527(1)/0x53E59D(2)/0x53E67A(0)/0x53E958(ebp)/0x53EAD8(ebp) ✓。
- 置 1 前置（0x53E510–0x53E527）：`push 0x828138("wb") / push esi / call 0x7CA845 / mov [0xAA0468],eax / test / je 跳过 / mov [0xAA0444],1` ✓；置 2 前置（0x53E574–0x53E59D）：`push 0x82813C("rb") / push esi / call 0x7CA845 / … / mov [0xAA0444],2` ✓（字符串亲读 `b'wb'` / `b'rb'`）。0x7CA845 = `push 0x40 / push [esp+0xc]×2 / call 0x7CA814` ✓ —— 0x40=_SH_DENYNO 形态成立；**0x7CA814 到底是否 _fsopen 未解入 IAT**，维持原报告的 [推导] 标注（诚实账一致）。
- 0x53E958/0x53EAD8 的 ebp=0 复算坐实：函数头 0x53E770 序言 `0x53E781 33ed xor ebp,ebp`，至两写点间无 `pop ebp`/重定义 ✓（原报告的「=0 复位」由 [推导] 升为 [字节+CFG]）。
- BSS 初值：0xAA0444 ∈ .data（vsz 0x367BE4 > raw 0x6C000，inraw=False）⇒ 载入零填充，静态初值 0 ✓（0xABCD58/0xB73550/0xAA0430/0xA8ED80 同判 5/5）。
- mode0 路径：`0x53EB16 call [0x7E1484]`（Peek 探针）→ `0x53EB1E cmp [0xAA0444],1 / 0x53EB25 jne 0x53EBE8` → 直接 `mov eax,ebx; ret 0xc`（ebx=Peek 结果）带「有消息」返回 ✓；包装 B `0x53E740 push 1(PM_REMOVE) / call 0x53E770 / test / je 0x53E740` 循环取到 + `0x53E757 cmp ecx,0x12(WM_QUIT) → xor eax,eax` ✓。主泵侧探针实参 edx=0（0x5D4D71 `xor edx,edx`）= PM_NOREMOVE ✓。
- mode2 路径（0x53E86C–0x53E8B1）：`cmp [0xAA0444],2 / jne 0x53EB01` → PeekMessageA(PM_REMOVE, push 1) 循环；`0x53E88E cmp eax,0x100 / 0x53E895 cmp [esi+8],0x1B → je 0x53E8E0`（ESC 特判块在）✓；`0x53E89B cmp eax,0xF(WM_PAINT) / 0x53E8A0 push esi / 0x53E8A1 call [0x7E14C0]=DispatchMessageA` —— **仅 WM_PAINT 分派，其余消息取走不分派（0x53E8A7 直取下一条）** ✓。

### 2.4 KF4 hwnd 与旗标写链（[字节]）

- `disp_hits(0xB73550)`：197 处引用，写者**恰 3**：0x777CD6 / 0x777D7E / 0x77780E ✓。
  - 0x777CD0 / 0x777D78 `call [0x7E14D4]=CreateWindowExA`（IAT 亲解）→ `a35035b700` ✓；支 B `0x777D76 push 8`（dwExStyle=8）✓；全屏门 `0x777CAB a078f98900 mov al,[0x89F978]` ✓；注册点 `0x777C79 c7442428 c0757700`（lpfnWndProc=0x7775C0）+ `0x777CA5 call [0x7E14D8]=RegisterClassA` ✓；WndProc 头 16 字节 `51 8b0d28768800 53 33db 56 3bcb 57 7457` 逐字节同 ✓（`33db`→ebx=0，销毁路径写 0 的源）。
  - 0x77780E `891d5035b700 mov [0xB73550],ebx`，同块 `0x777803 mov [0x887368],ebx`（清 CCToolTip 单例）、`0x777809 mov eax,[0xA8EDD8]` → `0x777818 mov dword [0xA8EDD8],2` ✓ —— 与原报告 §2.4 表全同（「WM_DESTROY」标签原报告已自标 [推导]）。
- 写链 0x77782B–0x777949 全部亲解，与 r063a T2.1 逐指令一致：`0x77783C 83f81c / 0x77783F 745f(je 0x7778A0) / 0x7778A0 3b3d5035b700(门①) / 0x7778AC 8b44241c(wParam) / 0x7778B4 0f95c1(setne cl) / 0x7778B9 8a1580eda800(旧值) / 0x7778BF 3bd1 + 0x7778C1 je 0x777949(门②去重) / 0x7778C7 3bc3 / 0x7778C9 0f95c0(setne al) / 0x7778CC 3ac3 / 0x7778CE a280eda800 ★ / 0x7778D3 755b(jne 0x777930)` ✓。**al≡(wParam!=0)**：al 唯一定义点 0x7778C9 setne，输入 eax 仅由 0x7778AC 装载、门① jne 至写点间无重定义 ✓。激活沿后继 `0x777930 call 0x777420 / 0x777935 push 0x849EF8 / 0x777942 c605a0008a0001` ✓；失焦沿 `0x7778D5 push 0x849E94` ✓。
- 字符串亲读：0x849E94=`Focus_Loss()\n`、0x849ECC=`Focus_Restore()\n`、0x849EF8=`Focus gained\n`、0x849F08=`Focus lost\n`、0x849F48=`Yuri's Revenge` ✓。SC_MINIMIZE 位：`0x777874 mov byte [0xA8ED81],1`（0xF020）/ `0x777880 mov [0xA8ED81],bl`（0xF120）亲见 ✓。

### 2.5 KF5 GameMode 与时间量级（[字节]+算术）

- `disp_hits(0xA8B238)`：**570 处引用**；立即数写者 0x52DD7F(**3**) / 0x52DD61(**4**) / 0x52E10F(**5**) / 0x5EFDC3(**0**) ✓；0x48CF94 `mov [0xA8B238],ebx` —— **ebx=0 复算坐实**：所在函数头 0x48CCC0（call 入边 0x6BE041/0x6BE061），`0x48CCD4 33db xor ebx,ebx`，经 `0x48CCD8 jmp 0x48CD91`（SEH 序言）至 0x48CF94，路径上无任何 ebx 重定义（唯一 `pop ebx`@0x48CD8C 位于终止于 0x48CD90 ret 的另一段，不在达路径上）✓。
- 分支-模式映射：0x55D394（==0）/0x55D396–99（==5 落 500 支、≠5 萰 10 支）✓；Sleep(10) 支单发（§2.1）✓ ⇒ GameMode=3/4 无循环 ⇒ 无秒级冻结能力 ✓；{0,5} 有界等待环唯一形态 ✓。
- 时间算术（python 复算）：T∈[0.500,0.516] ⇒ 21.156s → 轮数 [41.00, 42.31]（原报告合并口径 42±1 = 41–43 ✓，headline「42–43」为标称 0.500 侧 21.156/0.500=42.31 ✓）；2.56s → [4.96, 5.12]（「5–6 轮」✓）；24.73s → **[47.93, 49.46]**（headline「49–50 轮」为标称 0.500 侧数字，量化感知包络为 48–50，见 §3-N2）；三值均满足 k×0.5 ≤ T < (k+1)×0.5（k=5/42/49）✓。
- 冻结时长出处（本仓在案）：`GOAL_THREE_TARGETS_20261018.md:2478/2481/2970` —— archive_T34 w0 = 24.7348s、l3_20261023q w2 = 21.156s、区间 2.556–24.735s；原报告引用的 2.56/21.156/24.73 为其截断舍入 ✓。

### 2.6 KF6 普查（[字节]）

- 0xA8ED80：**46 引用 = 45R + 1W**，唯一写者 0x7778CE ✓（与 probe3_out、r063a §0 三方一致）。
- 0xA8ED84：**1007 引用** ✓。0xA8B238：**570 引用** vs `clock_frame_loop.md:88`「571 处」——差 1 实存、未归因（原报告如实记）✓。
- 0xAA0430：17 引用，写者**恰 7 组** = 0x432CDD / 0x5D4D77 / 0x5DC459 / 0x759210 / 0x759A3F / 0x775A7F / 0x77F925 —— 与 r063a RA4「0x432CDD / 0x5D4D77 / 0x5DC44E-59 / 0x759210 / 0x759A3F / 0x775A7F / 0x77F925」逐组全同（0x5DC44E-59 为 RMW 序列，写回点 0x5DC459）✓。

### 2.7 KF7 文档裁决（亲读 `docs/re/clock_frame_loop.md` 与 `re_atlas/evidence/r063a_flag_writer_closure.md`）

- doc:86 = 「`0xA8ED80`｜**「快进/跳过 Sleep」标志**（=1 时 `0x55D360` 跳过 Sleep 块）」、doc:433 = 「快进（跳过 Sleep）标志」——旧标签在案 ✓；doc:88 = 「**571 处**」✓；doc:26 = 「`0x55D360` 的 `Sleep(10)` 是固定值，不随帧耗时自适应」✓。
- doc:215–217 §3.2 伪码亲读：
  ```
  if (![0xA8ED80]) {                       // 非快进
      if (state==0 || state==5)  { Sleep(0x1F4=500ms); MessagePump(0x5D4D50); }
      else                       { Sleep(0x0A=10ms);   MessagePump(0x5D4D50); }
  }
  ```
  ——确为**单发**，无 0x55D3A7 重查、无 0x55D3AE 回边 ⇒ 「结构错误（新裁决）」成立 ✓（分支映射 state==0||5→500 与字节一致，错的只是缺环）。
- doc:477 = [实证] 勘误行「`0xA8ED80` 为 `AppHasFocus` 标志…`Sleep(500)`（单机暂停）与 `Sleep(10)`（联机后台保活）**仅在失去焦点后台运行时生效**」在案 ✓ —— 与 doc:86/215/433 同文件新旧未同步坐实 ✓。
- 「快进」命名的字节否定：旗标唯一写者 = WM_ACTIVATEAPP 激活沿（0x77783C→0x7778CE，本核验 §2.4 亲解），引擎自证字符串 Focus_Loss/Focus_Restore/Focus gained/Focus lost（§2.4 亲读），无任何输入路径置位 ⇒ 「快进」无字节支撑；「=1 跳 Sleep 块」字面对但跳的是含两处泵的整块（0x55D385 jne 目标 0x55D3BB）✓。r063a 裁决正确 ✓。

### 2.8 PRED 判别式（逻辑/字节自洽审计；零真机，未执行）

逐腿对字节：
- [0xA8ED80]==0：环继续条件即 `0x55D3AE je`（=1 必经 0x55D3B0 jmp 出环）✓；==1 反例成立 ⇒ 可证伪 ✓。
- [0xAA0430] 隔 2s 增≈4：每环迭代恰 1 次泵调用（0x55D3A2），泵内 inc 0x5D4D77 每调用恰 1 次（消息循环不再加）⇒ ≈2 次/s × 2s = +4 ✓。
- [0xA8ED84] 不变：唯一定常 inc 0x55DE7E 在环外（冻结出口后）✓。 [0xABCD58]==1：入口闩 0x55D37C，环内无清者（§2.1）✓。
- 栈签名 0x55D3A2（Sleep 返回址）/0x55D3A7（泵返回址）轮流：与 0x55D3A0 call esi / 0x55D3A2 call 泵的返回址精确对应 ✓。
- [0xA8ED81]==1 旁证：0x777874（SC_MINIMIZE=0xF020）✓；[0x8A00A0]=1 旁证：0x777942 ✓；[0xAA0444]==0 加读项与 mode2 吞消息机制闭环（§2.3）✓。
- 反证条件成对给出（==1 → 不在本环；计数冻结∧hwnd==0 → hwnd==0 死锁变体）⇒ 判别式可证伪性成立 ✓。执行本身被铁律 1 禁止，原报告亦如实标注「全部未真机执行」。

---

## 3. 复算中发现的三处瑕疵（均不动摇结论）

- **N1（口径）**：REPORT.md §2.1 括注「loop_backedges 仅一条 0x55D3AE→0x55D38D」**未标窗口**。实测 MLF 全窗 [0x55D360,0x55DEE0) 回边 = **6 条**（等待块 1 条 je + 帧体 5 条 jl：0x55D5ED/0x55D9B7/0x55DA1E/0x55DAEF/0x55DB83）；原 probe1_scene.py:20 打印的正是全窗（会印 6 条）。「恰 1 条」仅在等待块窗口 [0x55D387,0x55D3BB) 成立（本核验实测成立）。结论不受影响——那 5 条是帧体自身的 jl 循环，与等待块无关——但行文应写「等待块内恰 1 条回边」。
- **N2（量化包络）**：headline「24.73s≈49–50 轮」为标称 T=0.500 的数字；量化感知包络（T 上限 0.516s）为 **48–50 轮**（24.73/0.516=47.93）。原报告 §2.6 对 21.156s 做了合并（42±1）却未对 24.73s 做同样处理，前后口径不一。差 ±1 轮，无机制影响。
- **N3（新发现，doc 侧）**：`clock_frame_loop.md:477` 勘误行自身把 0x55D377 的字节抄成 `a1 80 ed a8 00`（A1=`mov eax,moffs`）；实测为 `a0 80 ed a8 00`（A0=`mov al,moffs`）。属该文档笔误，反证其「内部未同步」，不影响 P02 对该行的裁决（其结论语义与字节一致）。
- 另：「0x55D37C 写闩（任务伪码未列）」一句的「任务伪码」指 P02 的任务文本；grep `swarm_20261104/*.dwf.ts`、`DISCIPLINE.md`、`A01/REPORT.md` 均无 `ABCD58` 字样，与「未列」相容（低风险脚注，未逐字比对任务全文）。

---

## 4. 诚实账

1. **零真机**：PRED 判别式未执行（铁律 1），本核验只做字节锚定与逻辑自洽审计——「CONFIRMED」指判别式成立性与字节一致性，不指真机结果。
2. **0x7CA814 是否 _fsopen 未闭环**：该函数先 call 0x7D2DA6 再三次 push 转调，未解入 IAT；原报告标 [推导]，本核验维持 [推导]（形态证据 push 0x40 + "wb"/"rb" 充分，身份不钉）。
3. **GameMode 570 vs 571 差 1 未归因**：本核验同样只能确认差值实存，不能归因（可能为口径或台账笔误）。
4. **0x53EB16 探针的 PM_NOREMOVE 值来自调用方实参（[esp+0x50] 链）**，本核验未回追全部调用方；但主泵直呼侧（0x5D4D71 `xor edx,edx`→PM_NOREMOVE）已亲见，机制结论不受影响。
5. **0x55DEC7（第三个 ret）未亲见**，沿用台账在案记载（与原报告诚实账第 7 条一致）。
6. **泵包装合成事件段（0x53EA19–0x53EBE3）/0x49F740 的 0xBEEF 通道生产者**未展开（原报告诚实账第 2/4 条照录，未复算）。
7. 复算探针两次窗口切片曾从指令中间起解出乱码（0x53E585/0x53E860/0x48CF92），已用对齐流 `eng.by()` 重切修正——此即解码口径纪律（G-23）的现场教训，最终证据全部取自对齐流。

---

## 5. 复算入口

```bash
cd lead/goal3t_nightwatch_20261102/swarm_20261104/P02
python -I -X utf8 _p02v_probe.py    # 覆盖率+KF1/2/4/5/6 全量字节复算 → _p02v_out.txt
python -I -X utf8 _p02v_probe2.py   # KF3 补切（对齐流）+BSS 判定+寄存器源 → _p02v_out2.txt
tasklist //FI "IMAGENAME eq gamemd.exe"   # 真机零占用自证
```
共享引擎 `../ra2tool.py`（SHA256 断言 + 重同步线性解码）；裁决对象 `P02/REPORT.md`；对账件 `re_atlas/evidence/r063a_flag_writer_closure.md`、`docs/re/clock_frame_loop.md`（26/86/88/215-217/433/477 行亲读）、`lead/GOAL_THREE_TARGETS_20261018.md`（2478/2481/2970 行，冻结时长出处）。
