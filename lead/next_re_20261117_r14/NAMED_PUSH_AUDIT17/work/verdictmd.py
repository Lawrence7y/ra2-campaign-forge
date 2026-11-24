# -*- coding: utf-8 -*-
"""Generate VERDICT.md (per-row sections) from the same verified facts used for
EVIDENCE/ROW_*.txt and verdict.tsv."""
import os
import emit

OUT = emit.OUT

HEADER = """# VERDICT — NAMED_PUSH_AUDIT17（异族独立审计，agent-233）

## 0 · 审计身份与口径

- 身份：**异族独立审计员**。被审批次由执行器 **Hy4** 产出（S18_B5 9 行 + S17_B1 3 行，共 **12 行**）；本审计员不是 Hy4。
- 二进制：`D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe`
  实测 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✅（与卡面期望一致）
- 工具：Python 3.12.10（无 venv、未 pip install）、capstone **5.0.7**（`skipdata=True`）、pefile **2024.8.26**
- 扫描规模：`.text = [0x401000, 0x7E038D)`；线性反汇编 **1,392,592** 条指令，**覆盖率 100.00%**（㉖ 口径自洽）
- 只采信自写脚本从字节读出的结果；**未**引用执行器任何 `EVIDENCE/ROW_*.txt` 作证据；未修改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `NAMED_PUSH_*` 下任何文件。
- 技术前提（已在实现中落实）：`pTD` / `pCHD` 存**绝对 VA**（非 RVA）；装饰名在 **TD+8 内联**（不是指针）。

### 取数方法（12 行如何来）

两个 `delta.tsv` 的第 1 列 `entry` + 第 2 列 `subsystem` 全量读出，行数自核：
`NAMED_PUSH_S18_B5` = 9 行（007B13D0 / 007B1BC0 / 007B2630 / 007B26D0 / 007B30B0 / 007B31E0 / 007B3450 / 007B3890 / 007B3AA0，全 S18）、
`NAMED_PUSH_S17_B1` = 3 行（004A2CD0 / 006BEF10 / 006BF690，全 S17），合计 **12**，未增删。

### 本批三道陷阱的处置

| 陷阱 | 处置 | 结果 |
|---|---|---|
| 读写方向写反 | 把执行器点名的每个 API 调用经 **IAT 独立解析**成真实导入名（WSOCK32），再核该函数的参数方向 | 12/12 无反向（见 §3 API 汇总） |
| ④ 锚点落在析构器（㉓） | 对**每张持有虚表**枚举**全部** 写点，逐个判构造器/析构器/**标量删除析构器**，并扫 atexit 注册集合 | 12/12 锚在构造器；析构写点全部排除（见 §4） |
| 小成员表 vtable 不是主虚表 | 按 TD 归组枚举**每个 TD 的全部 COL→虚表**，并核对 slot0 是否为 QueryInterface | 无一行拿小表顶主表（CStreamClass 的两张表已分辨，见 §4） |

"""

FOOTER = """
---

## 3 · API 身份独立复核（IAT 实测，用于「读写方向 / 形态」判据）

执行器点名的每个被调 API，本审计经 `DIRECTORY_ENTRY_IMPORT` 把 `.text` 里的 thunk 解到真实导入名：

| thunk | IAT 槽 | 真实导入 | 被本批哪行使用 |
|---|---|---|---|
| 0x7C89B0 | 0x7E1558 | **WSOCK32!sendto** | 007B13D0（007B14C6）、007B3AA0（007B3D75） |
| 0x7C89AA | 0x7E154C | **WSOCK32!recvfrom** | 007B13D0（007B1586） |
| 0x7C89BC | 0x7E156C | **WSOCK32!WSAAsyncSelect** | 007B1BC0（007B1BDB/007B1C1F）、007B3890（007B38C6） |
| 0x7C89A4 | 0x7E1554 | **WSOCK32!setsockopt** | 007B2630（007B2652/007B2690）、007B30B0（007B31B3） |
| 0x7C89CE | 0x7E1560 | **WSOCK32!gethostname** | 007B26D0（007B26DB）、007B3450（007B349D） |
| 0x7C899E | 0x7E157C | **WSOCK32!socket** | 007B30B0（007B30E4）、007B31E0（007B3234）、007B3450（007B35F8） |
| 0x7C8998 | 0x7E1580 | **WSOCK32!bind** | 007B30B0（007B315F）、007B31E0（007B3295）、007B3450（007B3653） |
| 0x7C8992 | 0x7E1584 | **WSOCK32!closesocket** | 007B31E0（007B32A0）、007B30B0（经 call [eax+4]）、007B1B80 |
| 0x7C897A | 0x7E1574 | **WSOCK32!WSAGetLastError** | 多行 |
| 0x4068E0 | — | 进程内**单字节 `c3 ret`**（日志被编译为空 stub） | 多行（执行器称「空 stub」，实测正确） |

⇒ 执行器所报 API 身份**无一错认**，故「把 send 写成 recv / 把 bind 写成 socket」这类方向性错误在本批**不存在**。

---

## 4 · ㉓ 析构器锚点审计：三张虚表的**全部**写点与判定

三张相关虚表（族结构实测）：

```
IPX      vt=007F794C  23 槽  COL=0080EA60  TD=0084D8F8  .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
Winsock  vt=007F79BC  23 槽  COL=0080EAF8  TD=0084D8D0  .?AVWinsockInterfaceClass@@  chd numBase=1（根）
UDP      vt=007F7A6C  31 槽  COL=0080EBE0  TD=0084E1C0  .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
```

每个 TD **只有 1 个 COL** ⇒ 每类各 1 张虚表 ⇒「小成员表顶替主虚表」在本族不成立。

全部写点（整镜像 dword 出现，逐个判定）：

| 虚表 | 写点(指令) | 所在函数 | 判定 | 依据 |
|---|---|---|---|---|
| 007F794C | 007B0DA4 | 007B0D90 | **构造器** | 先 `call 0x7B19C0`(Winsock 基类构造) 再装 vt，尾 `mov eax,esi; ret`；5 个直调者 |
| 007F79BC | 007B1A20 | 007B19C0 | **构造器** | 大体量字段初化 + 0x80 次表清零，尾 `mov eax,esi; ret`；2 个直调者(007B0D93/007B2DB3) |
| 007F79BC | 007B1ABC | 007B1AB0 | 析构器（排除） | 装 vt 后拆 3 个成员子对象 vt(0x7F7A3C) + 4 次 `call 0x7C8B3D` 释放 |
| 007F79BC | 007B278C | 007B2780 | **标量删除析构**（排除） | 同上，且尾 `test al,1; je; push esi; call 0x7C8B3D`（条件释放 this） |
| 007F7A6C | 007B2E2D | 007B2DB0 | **构造器** | `call 0x7B19C0` 后初化，尾 `mov eax,esi; ret`；1 个直调者(0052F456) |
| 007F7A6C | 007B2E56 | 007B2E50 | 析构器（排除） | 装 vt 后 `call 0x7C8B3D` 释放 |
| 007F7A6C | 007B4176 | 007B4170 | **标量删除析构**（排除） | 该函数即 UDP 虚表 **slot0**；装 vt 后 `call 0x7C8B3D` |

**atexit 排除**：全 `.text` 扫 `push imm32 ; call 0x7C978A` 得注册点 **152** 个；
`007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170` **均不在**该集合。
**静态实例排除**：三张表的 VA 作为 dword 在 `.data` 中出现 **0 次** ⇒ 无全局静态对象（不存在 ㉓ 的「atexit 全局析构器写的死表」形态）。

⇒ 12 行里 **没有一行**把 ④ 锚在析构器上。执行器自报的排除名单（CStreamClass 的 007B2E56/007B4176、007B2880/007B3110、007B1ABC/007B278C 等）与本审计逐个复核一致。

### 4.1 S17 的另一组 ㉓ 复核（CStreamClass / TClassFactory）

CStreamClass 有两个虚表（同 TD 0081FC30）：`007E5DAC`（15 槽，slot0=004A2990=**QueryInterface**，主表）与 `007E5D94`（5 槽次基表）。
本批 entry `004A2CD0` **只在主表** ⇒ 不存在「拿 5 槽小表顶主表」。
`007E5DAC` 三个写点：`004A285E`(构造器 004A2820) / `004A2889`(析构器 004A2880) / `004A3119`(删除析构 = 本表 **slot14** = 004A3110)。
三者均不在 152 个 atexit 注册集合。TClassFactory<VCStreamClass>/<SuperClass> 各只有 1 个 COL，写点各 1 处，均为构造器。

---

## 5 · ③b② 判定标准（本批实际用法，供复核）

本批 12 行的 ③b 全部落在 **③b② 可伪证返回约定**，判据统一为：

1. **被调函数的返回值域必须是多值状态码**，不是 `{0,1}` 布尔：
   S18 九行全部以 **WSOCK32 的 `SOCKET_ERROR = -1`** 为哨兵，`cmp eax,-1` + `jcc` 真分支；
   其中 `007B13D0`（sendto/recvfrom）、`007B3AA0`（sendto）还进一步 `cmp eax,0x2733`（WSAEWOULDBLOCK）做**三级判别**
   ⇒ 返回域至少三态，明确不是布尔。
2. **调用方真的拿它分支**，且两路动作不同（关 socket / 记日志失败 vs 继续组包·遍历·返回成功）。
3. **无 eax 覆写**：`call` 与 `cmp` 之间无写 `eax` 的指令（逐行核）。
4. 凡「布尔主输出 / 空指针判断」一律按 **③a** 排除，不计入 ③b：
   例如 `007B3450` 的 `call [eax+0x64]` 后 `test al,al/jne`、`007B3890` 的 `007B3895 call 0x7B1BC0` 后 `test al,al/je`、
   各构造函数入口的 `operator new` 空判断。

**与 D-46「bool 主输出不算」的关系**：D-46 排除的是「函数自身返回 bool 且无错误码契约」那一形态（`0045A640`）。
本批九行的 ③b② 证据不是函数自身的布尔返回，而是**被调 WSOCK32 API 的可伪证错误约定**驱动了真分支；
函数自身的布尔返回只是另加事实。故不适用 D-46 的排除，也不因此放宽。

---

## 6 · 对 ④ 的强弱分级（照实记，供 Lead 二次裁量）

| 强度 | 行 | ④ 依据 |
|---|---|---|
| 最强（派发点与构造点同函数） | **007B3450** | `0052F474 call [edx+0x3c]`（slot15）；同一函数 0052F456 处正构造 UDP 对象并存入 0x887628 |
| 强（真实派发点，槽号与 ② 一致） | **007B3890**(0052F4AC `call [eax+0x1c]` slot7)、**007B30B0**(0069C457 `[edx+0x5c]` slot23)、**007B31E0**(005D90A9 `[eax+0x68]` slot26)、**007B3AA0**(007775FF `[eax+0x40]` slot16)、**007B13D0**(同上 007775FF；该槽 IPX/UDP 两侧分别正是 007B13D0/007B3AA0) | 对象取自全局 **0x887628**（构造后落点） |
| 强（真实调用者） | **007B1BC0**(007B3895 `call 0x7b1bc0`)、**007B2630**(4 条：007B13AB/007B31BC/007B32EA/007B36A1) | 直调目标钉死 |
| 中（仅活虚表安装点） | **007B26D0** | 直调 0 条；`call [reg+0x44]`（slot17）全镜像 131 处、无一可钉到本类实例 ⇒ **本行 ④ 最弱**，执行器所写「+ 派发」我复现不出来 |
| 中（仅活虚表安装点） | **004A2CD0**、**006BEF10**、**006BF690**（S17 三行） | 直调 0 条；无该槽派发点，④ = 构造器装活表 |

⇒ 若 Lead 采「④ 必须有派发点或调用者」的严格读法，**只有 `007B26D0` 与 S17 三行**会掉；其余 8 行不受影响。
本审计的 PASS 沿用已入账 16 批的先例（ctor 安装点 = 活虚表见证），并把强弱显式列出以便一次性重裁。
"""


def main():
    parts = [HEADER]
    parts.append("## 1 · 逐行裁决（12 行）\n")
    parts.append("| entry | subsystem | name | verdict | ③b 形态 | same_source |")
    parts.append("|---|---|---|---|---|---|")
    for r in emit.ROWS:
        parts.append("| `%s` | %s | `%s` | **%s** | %s | %s |" % (
            r["entry"], r["sub"], r["name"], r["verdict"], r["r3f"], r["ss"]))
    parts.append("")
    parts.append("## 2 · 逐行一节（五项结论 + 地址字节）\n")
    for n, r in enumerate(emit.ROWS, 1):
        parts.append("### 2.%d `%s` — %s（%s）→ **%s**\n" % (n, r["entry"], r["name"], r["sub"], r["verdict"]))
        parts.append("**① ② 类身份（全表枚举；独立成立）**\n")
        parts.append("```")
        parts.append("  " + r["r2"])
        parts.append("```")
        parts.append(r["r2d"].rstrip())
        parts.append("")
        parts.append("**② ③b 具体形态：%s（可伪证返回约定）**\n" % r["r3f"])
        parts.append("```")
        parts.append(r["r3"].rstrip())
        parts.append("```")
        parts.append("")
        parts.append("**③ ④ 使用见证（独立成立；direct-only 不足）**\n")
        parts.append("```")
        parts.append("  " + r["r4"])
        parts.append("```")
        parts.append(r["r4d"].rstrip())
        parts.append("")
        parts.append("**④ ④ 与 ② 不同源 → `same_source = %s`**\n" % r["ss"])
        parts.append("")
        parts.append("**⑤ 语义与实测一致**\n")
        parts.append("```")
        parts.append(r["r5"].rstrip())
        parts.append("```")
        parts.append("")
        parts.append("---\n")
    parts.append(FOOTER)
    with open(os.path.join(OUT, "VERDICT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts) + "\n")
    print("VERDICT.md written, rows=%d" % len(emit.ROWS))


if __name__ == "__main__":
    main()
