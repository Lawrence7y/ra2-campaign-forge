#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§434 台账追加：四条裁决入账 + Lead 判据修正静态核对成立 + c″ 验收判据 v2。"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

CONTENT = """# §434　★★ 四条裁决入账（Lead 2026-10-25）+ 判据失配修正坐实：c″ 后 exitstate 不经过写 2 点
#        ⇒「观测到 1→2」判据作废，验收判据 v2 = 干净退出 + 闩 1 至进程终

**性质**：裁决执行轮（零真机趟；快照只读核对一行）。

## 一、裁决入账（共用台账协议第 1/3 条；删除与记账同提交——L3 墙在，本轮落工作树）

- **D-09 已裁决（2026-10-25）**：授权本线制作 c″ **独立候选副本**（母本保留不动）；
  独立 `EnableRC4ExitBail` 开关、**默认关闭**（隔离对照+可回退）；**先离线核验、
  再串行真机 A/B**；**正常退出是硬门槛，不降为「无崩溃即过」**。
  执行：下一轮守卫件源只读复制→本线域改副本（9 号补丁点+独立开关）→离线编译+门禁
  →串行 A/B。PENDING 条目已删（连同 update 1–8，内容以本节+§431–433 为准）。
- **D-08 已裁决（2026-10-25）**：harness7 按「两臂通过、窗口臂 N/A-环境」**有限升格**
  为在用件；适用范围=全屏分支（窗口臂=与 boot 修复载体互斥的环境态，非 harness 缺陷）。
  执行：227 件积压**逐件**核对归属/内容/门禁结果，不一揽子提交（本线 140 件已过扩展
  审计，跨线件按归属拆分交各自线）。PENDING 条目已删。
- **D-07 已裁决（部分，条目归 RE-ATLAS 维护）**：**不整体放行、不要求整仓清零**；
  优先按写域、变更范围检查；**保留整仓告警记录**；真实缺陷交归属线修复；冻结件另裁；
  任何门禁调整须先验证有效，不得作绕闸手段。残余待决：归属线修复进度与验收、
  冻结件另裁、门禁调整方案（若做）的有效性验证。
- **D-06 维持**：继续独立核验，不阻塞上述路径（XVERIFY 自理，条目未动）。

## 二、★ Lead 判据修正静态核对——成立（照旧判据会错杀有效修复）

Lead 指出：c″ 不主动写退出状态值，「正常退出」与「观测到 1→2」不能未经核对划等号。
本轮快照复核（sha16 `73201cc021497c95` 断言过）：
- c″ 出环后唯一路径 A teardown `0x6BE0E9..0x6BE173`：**0 处 [0xA8EDD8] 引用**；
- B tail `0x6BEC9D..0x6BED40`：**0 处**；
- 全镜像唯一写 2 点 `0x777818` 在 WM_CLOSE 块内（本场景闩 1 前已跑过、被 je 跳过）。
⇒ **补丁后 exitstate 闩 1 直到进程终，「观测到 1→2」结构上不可满足**——§433 四的
判据行就此作废（横幅更正，零删除）。

## 三、c″ 串行 A/B 验收判据 v2（取代 §433 四）

| 臂 | 配置 | 判据（全过才算过；正常退出=硬门槛） |
|---|---|---|
| MAIN | 守卫开 + `EnableRC4ExitBail=1` | 关窗后**进程干净退出**（句柄信号/退出码观测）；无 #32770 对话框；except.txt 零新增；exitstate 观测 **0→1 后恒 1 至终**；a8 leftover=0；母本四哈希未变 |
| CTRL | 守卫开 + `EnableRC4ExitBail=0` | 僵尸复现（同窗不退、exitstate 闩 1）⇒ 差分归因 c″ |

- cave 命中的直接证据：默认**差分 A/B 即足**；如需插桩，cave 可加一次性命中计数
  （守卫 DLL 全局，detach 落日志）——**默认不加**（保持 cave 最小面，登记待 Lead 定）。
- 串行顺序：CTRL 先（装置自证+僵尸基线）→ MAIN 后（同会话同时段）。

## 四、执行排程（下一轮起）

1. 候选副本：守卫件源（他线域，只读）复制→本线域改副本（E9@0x6BE0E1 + cave +
   `EnableRC4ExitBail` 独立开关默认 0）；离线编译+门禁（镜像 v5 门禁风格）。
2. 离线核验：副本字节 vs `d09a_c2_patchspec.json`（`_verify_c2_cave.py` 直用；
   需补「副本安装后内存布局」级断言）。
3. 串行 A/B 真机（1 时段，CTRL+MAIN 至少各 1 趟）。
4. 227 件积压逐件审计（D-08 附带义务），与 1–3 并行。

## 五、卫生与勘误

- 零真机趟；PENDING 删 D-08/D-09（本线来源，协议第 1 条）；D-07/D-06 他线来源
  **原文未动**（归来源会话）；两条 SYNCPOINT 信标（H-1 趟 / 守卫首验）按历史信标
  原字节保留——其「待裁」字样已过时，以本节为准。
- §433 四判据行作废（本节三取代）；其余 §433 内容不变。
"""

def main():
    before = io.open(LEDGER, "rb").read()
    assert b"\xc2\xa7433" in before, "prev section missing"
    assert b"\xc2\xa7434" not in before, "duplicate"
    crlf_before = before.count(b"\r\n")
    add = CONTENT.replace("\n", "\r\n").encode("utf-8")
    after = before + b"\r\n" + add
    assert after.startswith(before)
    assert after.count(b"\r\n") == crlf_before + 1 + CONTENT.count("\n"), "crlf math off"
    tmp = LEDGER + ".tmp434"
    with io.open(tmp, "wb") as fh:
        fh.write(after)
    os.replace(tmp, LEDGER)
    check = io.open(LEDGER, "rb").read()
    assert check == after
    print("OK appended 434; ledger %d bytes crlf=%d" % (len(check), check.count(b"\r\n")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
