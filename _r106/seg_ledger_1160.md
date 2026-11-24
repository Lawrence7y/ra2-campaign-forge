
## §1160 R17 第 106 轮 · 19 张 switch 分派表的函数界定与选择子来源：19/19 找到被 call 的入口（17 个不同）、6 张 LEA_SUB、7 张 DEC（第三种 idiom）、2 张结构体偏移 0xc/0x5c；修掉 1 处 OOM 事故（exit 137）与 1 组写死旧数的断言

**轮首先修故障，不硬推进度**。上一会话 #170 异常退出（interrupted by harness restart），遗留下 `_r106/` 半成品。
盘上核查发现两处必须修：①`r106e_recheck.py` 把 `detail=True` 的同一解码器用于整段 .text 的 `md.disasm()`，
实测被内核 OOM Killer 杀掉（**exit 137**，输出只停在 S0 一行）—— 这正是任务卡「防 OOM 内存硬红线」明文禁止的写法，
也是 #170 异常退出的直接嫌疑；改 `detail=False + disasm_lite + 64KB 分块` 后铺满 1,392,592 条、停滞点 0。
②`r106b_switchmap.py` 的 M4a/M4b/M4c 写死成「7 组/6 张表/1 组例外」，被 r106d 全 19 张表普查推翻，实测 8 组/5 张表/3 组。

**主攻 R105 待办①**（「19 张表所属的 19 个函数本身未逐个命名，未证每个 switch 的语义」）——
语义命名需要符号或运行期（win-main 仍 OFFLINE），故本轮只交三件可机械核验的字节事实：

### 一 · 函数界定：三条判据里只有第三条成立

初版用 CALLTGT（`<=holder` 最近 call 直接目标）与 RETPAD（`<=holder` 最近 ret 之后第一条起点）两法
并要求一致，实测**只 1/18 一致**。根因是判据不成立：switch 分派常写在大公共函数中段，最近的 call 目标
是这个函数内部调用的别的函数；MSVC case 体内部大量以 ret 收尾，最近的 ret 常是本函数内某 case 的 ret。
改用**「函数入口必须被 call 直接引用」**（正是 R105 A3 已证「292 项值 0 个是 call 目标」的同一集合，方向相反）：
**19/19 全部找到**入口候选，去重 **17 个不同地址**（0x71f2c0 与 0x71f328 共用 0x71e940、
0x728e08 与 0x7291ac 共用 0x728a00）。

### 二 · 选择子来源：必须看 cmp 的判界寄存器，不是跳转表的索引寄存器

初版回看「写跳转表索引寄存器的指令」，18/19 只拿到 MOV_IMM/MOV_REG 噪声，0 张 LEA_SUB。
根因是两级压缩 idiom 有**两个不同寄存器**：
```
lea  eax, [input - K]        <- 真正的输入来源
cmp  eax, BOUND
ja   default
xor  ecx, ecx
mov  cl, byte ptr [eax + BYTETAB]   <- 字节表用 eax 索引
jmp  dword ptr [ecx*4 + TABLE]      <- 跳转表用 ecx 索引
```
改为先定位 `cmp reg,imm` 取判界寄存器、再回看写它的指令。形态分布：
**LEA_SUB 6 / DEC（OTHER）7 / MEM_LOAD 2 / MOV_IMM 4**，共 19，无 UNKNOWN。
- **DEC 7 张是第三种 idiom**（R105 只记了两种）：判界寄存器写入点全是 `dec reg`，
  输入域 `[1,BOUND+1]` 平移到 `[0,BOUND]`。
- **MEM_LOAD 2 张给出结构体偏移 0xc 与 0x5c** —— R105 待办① 要的「判别输入字段」的第一个字节级答案。

### 三 · 规则 D 复算跨家族审计的反驳

deepseek `#176` 状态 **failed / error_max_turns / 61 回合 / 8.82' vs 预算 8' ⇒ [OVERTIME]**，
`AUDIT106.md` 未落盘但 21 个脚本/JSON 在盘（与 R100 #150、R105 #169 同型）。它的实质反击：
我方判 CALL_CLOBBER 的 2 组里，**0x4c6cde 实际等价**（call 后到 ret 不读 eax，旧索引不可观察），
**0x4c71ca 不可判**（call 后有 `mov edi,eax`）。主会话 `r106g_recheck.py` **25 项 FAIL 0** 独立复算：
V4a 0x4c6cde call 后不读 eax（n_calls=1）；V4b 0x4c71ca 在 **0x4c71d2 `mov edi,eax`** 读 eax；
V5/V6 用状态 worklist（275/85 状态全覆盖、无截断）证两 callee 均无「eax 未写就读」路径、
且每条可达返回都写过 eax ⇒ **反驳成立**。

### 四 · 本轮自错 6 处（全部由断言当场抓住）

E-rc2 OOM(exit 137) / E-rc3 字节表索引寄存器匹配错(5/10) / E-sw1 M4 写死窄口径数(7组→8组) /
E-f1+E-f2 find_holder 窗口法漏 1/19（根因是窗口内数据字节致整段错位，非窗口大小）/
E-g1+E-g2 逐点 dec 慢到超时、V5/V6 遇分支即停只覆盖 1 条路径 / E-f5 7 张记 OTHER 等于没定性。

### 五 · 收口

五个带断言机制的脚本合计 **115 项断言 FAIL 0**（b 25 / d 26 / e 27 / f 12 / g 25）；
`r106a_probe` / `r106a2_probe` / `r106c_idxdep` 三个是探索性探针，不带断言机制，不记入断言数。
`check_disc.py` exit 0；五项 CR 全绿（R14_COMMON 1081 / LEAD_LOCK 137 / 台账 337 / 看板 0 / 归档 2952）；
看板 196→ 行（< 260 未触归档线）。产物 `_r106/r106*.json` 八个。
