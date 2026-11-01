#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§431 台账追加（字节级）：RC-4 守卫挂死机制闭合——关守卫=崩在 1，开守卫=等一个永不到来的 2。"""
import io, os, hashlib, sys

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

CONTENT = """# §431　★★ RC-4 守卫挂死机制闭合（离线静态，零趟）：泵循环 0x6BE0DC 的出环唯一通道 =
#        exitstate 1→2 bump（0x777818，住在被守卫跳过的单例消息派发下游）；
#        「崩（无守卫）」与「僵尸（有守卫）」是同一循环的两个面

**性质**：纯静态（快照 `73201cc021497c95`，§430 同件）。承接 §430 四的遗留问题
（`call esi` 是谁、exitstate 谁来推进）。件 `_exitstep_chain_dissect.py` v1-v6
（v1 名字串解码未走段表=坑、v3 拿 VA 当 file 索引=死、v6 修正版）。

## 一、函数 A 的全貌（含 WRITER=0x6BE0B6 的长函数）

- 块区起点 0x6BD7C7，每 ~0x3D 字节一块、共 ≥33 块；序言区 0x6BD7xx 有
  `mov esi,[0x81C1D0]`（0x6BD76E 邻域实测）⇒ **`call esi` 的 callee = 全局函数指针
  [0x81C1D0]，全镜像仅 2 个写者**：0x4790B9 写哨兵 0xFFFFFFFE（当 [0x89E3A0]==1，
  停机标志），0x4790CD 写 ecx（值由调用方给）。它不是「26 个不同守卫函数」——
  §430 四的猜测**部分修正**：块级 `call 0x6C14C0..0x6C3740` 直调（24 个不同目标）
  才是被 `0x6C7400` 存进来的对象（eax=handler 对象）上的方法；两条链都消费 esi/对象。
- **WRITER 之后是退出泵**（0x6BE0DC 起）：
  ```
  0x6BE0DC  call 0x5D4D50      ; 泵体（0x6BEC50/0x6BE0DC 同址调用互证）
  0x6BE0E1  cmp [0xA8EDD8], edi ; edi=1
  0x6BE0E7  je 0x6BE0DC         ; ==1 ⇒ 回环等「非 1」
  ```
  ⇒ **链卡死 = 循环等 exitstate 变成非 1；出环唯一通道 = 1→2 写**。
  泵体头三条：`mov eax,[0xB73550]; test eax,eax; je 0x5D4E66` ⇒ **hwnd==0 时泵空转**
  （0x5D4E60 回边，§398/ab24 已知），不干活、只占 CPU。

## 二、全镜像 exitstate[0xA8EDD8] 站点普查（v6 字节先决 + 对齐定性）

| 站点 | 指令 | 角色 |
|---|---|---|
| 0x6BE0B6 | `mov [0xA8EDD8],edi`(=1) | **闩 1**（§430 硬件断点坐实） |
| 0x6BE0E1 | `cmp [0xA8EDD8],edi` | 泵闸门 |
| 0x6BEC72 | `mov [0xA8EDD8],esi`(esi=1) | 兄弟函数 B 的闩 1（同构另一条等待） |
| 0x6BEC8C | `cmp [0xA8EDD8],esi` | B 的闸门；B 尾有 [0x887640] 双虚表调用（带 test 守卫） |
| 0x777809 | `mov eax,[0xA8EDD8]` | **0x777803 清零块内读**（hwnd 同块清零，相隔 11B 再证） |
| **0x777818** | `mov [0xA8EDD8],2` | **全镜像唯一 1→2 写**——census v2 曾判「幻影」，**本轮函数头对齐解码推翻**：0x777800 块自 0x7777F3 起解码完全自洽（`je 0x777809 / mov [0x887368],ebx / mov eax,[0xA8EDD8] / mov [0xB73550],ebx / cmp eax,ebx / je.. / mov [0xA8EDD8],2`，尾 `ret 0x10`），且 P1 断点 EIP=0x777814 与该对齐严丝合缝 ⇒ 真指令。 |

⇒ **0x777803 块是「WM_CLOSE 处理器」**：置单例=0、hwnd=0，且**仅当 exitstate 已==1
才 bump 到 2**。它是泵的唯一解药；§430 的「写 2 从未发生」不是写点不存在，
是**执行流没跑到它**——原因见三。

## 三、★★ 机制闭合（一句话）

**守卫把「崩在 1」换成了「等一个永不到来的 2」**：
0x777818 住在 0x5D4D50 泵体所派发消息的处理链下游，而该处理链要经
`[0x887368]`（RC-4 单例）派发——守卫拦截单例成员（ecx=0 → 返回 0），
派发不发生 ⇒ bump 不执行 ⇒ 泵 `je` 永远成立 ⇒ 静默僵尸。
**无守卫**：同一条派发解引用 null → AV（即 RC-4 本体）。
⇒ 两现象同源；修复的「视为完成」点 = 让 1→2 这一步在停机+单例已 null 时照常发生。

## 四、D-09-A 候选修正（取代 §430 四的 a/b/c 排序）

- **c′（新首选）**：0x777803 块本身已有「exitstate==1 才 bump」分支——守卫在拦截
  单例派发**且 [0xA8EDD8]==1 且 [0x887368]==0**（停机态）时，补写 `mov [0xA8EDD8],2`
  （等价于把 0x777818 的效果就地执行）。改守卫件=他线写域，仍需 Lead 派/授权。
- a（原案）：在 0x6BE0B6 之后强制推进 exitstate 序列——现降级，因唯一合法「推进」
  就是那个 2；1→2→…是臆造（B 的 0x6BEC72 写 1 说明值域不是递增流水）。
- b（原案）：放行特定调用点——需要点名「消息派发族」，静态上可钉但守卫粒度要细化。
- **附带风险登记**：兄弟函数 B@0x6BEC60（E8 调用者 0x54A8C5/0x5B3C75/0x647372/0x6BDD03，
  最后一个就在 A 的块区里）同构闩 1；若 A 出环后又进 B 的等待，需同判据复查。

## 五、卫生

本轮零真机趟；探针只读快照（sha16 `73201cc021497c95` 断言通过）；
产物 `_exitstep_chain_dissect*.py` 六件 + `.out.txt` 六件，全在本线目录。
census v2「0x777818 幻影」结论**由本轮对齐解码推翻**（横幅级更正：受影响=
§429 三、§430 三两处；「一趟内没捕到写 2」的实测**不变**，变的是解释——
写点真实存在，只是运行时没执行到）。
"""

def main():
    before = io.open(LEDGER, "rb").read()
    assert b"\xc2\xa7430" in before, "prev section missing"
    crlf_before = before.count(b"\r\n")
    add = CONTENT.replace("\n", "\r\n").encode("utf-8")
    after = before + b"\r\n" + add
    assert after.startswith(before), "append broke prefix"
    assert after.count(b"\r\n") == crlf_before + 1 + CONTENT.count("\n"), "crlf math off"
    tmp = LEDGER + ".tmp431"
    with io.open(tmp, "wb") as fh:
        fh.write(after)
    os.replace(tmp, LEDGER)
    check = io.open(LEDGER, "rb").read()
    assert check == after, "writeback mismatch"
    print("OK appended, ledger now %d bytes, crlf=%d" % (len(check), check.count(b"\r\n")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
