#!/usr/bin/env python3
"""Append §831 (third defect profile) and §832 (user decision; blocking item closed)."""
import io
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

extra = r"""
## §831 · **第三条缺陷画像：`FUN_006f3f40` 内同一"子对象指针未判空"模式重复 3 次**（2026-11-15 11:40）

- **§831-1 [已证·故障事实（来自 12 份日志，4 份内容各异）]**
  - `Eip:006F40A2`、`Access address:00000155`（读）、`EXCEPTION_ACCESS_VIOLATION`。
  - 崩溃指令：`006F40A2: 8A 82 55 01 00 00` = `mov al, byte ptr [edx+0x155]`，**EDX = 0**。
  - 寄存器（`sandbox_game\except.txt`）：`Eax=1065AE98  Ecx=03B01B20  Edx=00000000  Esi=10FDC110  Edi=FFFFFFFF`。

- **§831-2 [已证·指令级上下文（原始字节）]**
  ```asm
  006F4083  FF 92 F8 03 00 00     call [edx+0x3f8]      ; 虚调用
  006F4089  83 38 00              cmp  dword [eax],0    ; ★ 唯一的守卫：判的是"结果首 dword"
  006F408C  74 6A                 je   0x6F40F8         ;   为 0 才跳过
  006F408E  8B 06                 mov  eax,[esi]
  006F4090  6A 00 / 8B CE         push 0 / mov ecx,esi
  006F4094  FF 90 F8 03 00 00     call [eax+0x3f8]      ; 再取一次（结果 EAX=0x1065AE98）
  006F409A  8B 08                 mov  ecx,[eax]        ; ECX = [0x1065AE98] = 0x03B01B20
  006F409C  8B 91 AC 00 00 00     mov  edx,[ecx+0xAC]   ; EDX = [0x03B01B20+0xAC] = 0  ★
  006F40A2  8A 82 55 01 00 00     mov  al,[edx+0x155]   ; ⇒ 读 0x155 ⇒ AV
  ```
  - ⇒ **守卫判的是 `[eax]`（结果的首 dword），而不是随后用到的 `[ecx+0xAC]`** ⇒ 对该子对象指针**没有任何空检查**。

- **§831-3 [已证·同一模式在函数内重复 3 次]**（反编译 `FUN_006f3f40`，953 B）
  ```c
  piVar3 = (*(vtbl+0x3f8))(0);
  if (*piVar3 != 0) {
      piVar3 = (*(vtbl+0x3f8))(0);
      if (*(char *)(*(int *)(*piVar3 + 0xac) + 0x155) != 0) { ... }   // ★ 本次崩溃点
  }
  ...
  if (*(char *)(*(int *)(*piVar3 + 0xac) + 0x159) != 0) { ... }       // 同型（未崩，只因先崩了）
  ...
  if (*(char *)(*(int *)(*piVar3 + 0xac) + 0x15a) != 0) { ... }       // 同型
  ```
  - ⇒ **同一次 NULL 会在三个偏移上各自崩一次**（`0x155` / `0x159` / `0x15A`）。
    将来若修掉 `0x155`，崩溃会平移到 `0x159`，再到 `0x15A` —— **与 ②-a 的"崩溃点平移"是同一类问题**。

- **§831-4 [已证·宿主函数]** `FUN_006f3f40`（`0x006F3F40`，953 B），5 个直接调用者：
  `@0x00442C43`（`0x00442C40`）、`@0x00413F85`（`0x00413F80`）、`@0x00517CC4`（`0x00517CC0`）、
  `@0x007355F1`（`0x007353C0`）、`@0x00746814`（`0x00746810`）——全是很小的包装函数。
  函数体开头另有 `[0xA83D4C]`（与 ②-a 同族的地图/主题对象全局）作为判定条件，说明它属"地图对象初始化/切换"路径。

- **§831-5 [未证]**
  1. `[obj]`（结果的首 dword）与 `+0xAC` 字段的**确切语义**（是不是 `ObjectClass → TypeClass` 指针）。
     崩溃现场 `ECX=0x03B01B20` 与 `EAX=0x1065AE98` **都是堆地址**（映像范围外），故不能静态断言。
  2. 该子对象指针为何为 NULL：对象仍在构造中？类型未载入？或又一次 UAF（与 §829 同源）？**三种都未被证伪**。
  3. 修复位置：应在 `0x6F409C` 之前判 `edx != 0`，或在 3 处读取前统一判 `[ecx+0xAC]`。
     与 ②-a 一样，**静态改 exe 需 code cave**；运行时 hook 则是一个函数级 detour 即可（包住整个 `0x6F3F40` 或在 `0x6F409C` 处 inline hook）。

## §832 · **用户裁定：主崩溃无法确认 ⇒ 按"三种都修"准备；阻塞项关闭**（2026-11-15 11:45）

- **§832-1 [已证·用户输入原文要点]** 对"你的主崩溃是哪一种签名"的回答是
  **「不确定 / 日志已不在，就按"三种都修"准备」**。
  - ⇒ **自 §688 起挂起的"② 可达性 / 主崩溃归属"这一唯一外部输入项，就此关闭**（不是被证实，而是被裁定为"不需要再等"）。
  - ⇒ 今后**不得**再以"等用户确认崩溃场景"为理由推迟修复设计。

- **§832-2 [已证·用户指定的四条工作项]**（全选）
  1. 实施 ②-a 修复（G2 双入口守卫）；
  2. 深入 ②-b 制度性修复（禁止重叠 + 链结构校验）；
  3. 分析第三条缺陷（`0x6F40A2` / EDX=0）——本节 §831 已完成画像；
  4. 先把本轮结果固化成文档，再决定后续真机动作。

- **§832-3 [推论·"三种都修"的实际工作量排序（按风险/成本）]**
  | 优先级 | 修法 | 载体 | 风险 |
  |---|---|---|---|
  | 1 | ②-a：`0x724730` + `0x724580` 双入口守卫（G2） | 运行时 hook | 低（空 this 本无意义） |
  | 2 | 第三条：`0x6F3F40` 内 3 处 `[ecx+0xAC]` 判空 | 运行时 hook（inline @`0x6F409C`）或函数级 detour | 低-中（需匹配 `ret`/语义） |
  | 3 | ②-b：禁止多格建筑重叠（数据层） | 地图/规则层，不动 exe | **零**（但需先澄清触发条件，见 §832-4） |
  | 4 | ②-b：链结构校验 | 代码层，改动面大 | 高，仅作兜底 |
- **§832-4 [未证·必须先澄清的冲突]** 交接文档 1.2 写"触发 = 多格建筑 + footprint 内有其他占用者（重叠）"，
  而台账 `§630-3` 记录 **"重叠本身不崩（零交战对照同样重叠却全绿）⇒ 机制是「重叠 且 被摧毁」"**。
  两者**不一致**。落地"禁止重叠"前必须先判定哪个成立；否则可能修掉一个不是崩溃必要条件的因素。
"""

src = io.open(LEDGER, encoding="utf-8").read()
if "## §831" in src:
    sys.exit("ABORT: §831 already present")
n0 = len(src)
src = src.rstrip("\r\n") + "\r\n" + extra
io.open(LEDGER, "w", encoding="utf-8", newline="").write(src)
back = open(LEDGER, "rb").read().decode("utf-8")
print("chars %d -> %d" % (n0, len(back)))
for k in ("## §831", "## §832", "0x6F3F40", "三种都修"):
    print("  %-12s %d" % (k, back.count(k)))
# escape sanity: no stray control chars introduced
bad = [(hex(ord(c)), back.count(c)) for c in set(back) if ord(c) < 0x20 and c not in "\r\n\t"]
print("control chars:", bad)
