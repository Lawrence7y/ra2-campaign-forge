# -*- coding: utf-8 -*-
"""Append §568: verify D-19's retry-stamp counter-evidence + W3 erratum (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7568"

head = subprocess.run(["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
                      cwd=REPO, capture_output=True).stdout
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.replace(b"\r\n", b"\n").startswith(head.replace(b"\r\n", b"\n")):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
if b"\r" in wt:
    print("REFUSE: bare CR in worktree")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = u"""
## §568 · 亲验 D-19 的反证据：`0x42CC80` 确实在**重试循环内**再次推进代际戳（2026-11-05）

> **本节的地位**：把 §567 里「采信核证底稿、我未反汇编」的那一条**补成亲验**，
> 并据此在 W3 写域追加传播勘误。

### 一、我实跑的反汇编（`_leader/_v_retry_stamp_probe.py`）

```
0042CC72  47                 inc edi
0042CC75  897C2440           mov [esp+0x40],edi      ; 重试计数
0042CC79  e852000000         call 0x42CCD0
0042CC7E  8bcd               mov ecx,ebp
0042CC80  e82bd9ffff         call 0x42A5B0           ; ★ 代际戳递增函数（再次调用）
0042CC85  8a5538             mov dl,[ebp+0x38]       ; bIsBusy
0042CC88  8b4c241c           mov ecx,[esp+0x1C]      ; 重试上限
0042CC8C  84d2               test dl,dl
0042CC8E  0f95c0             setne al
0042CC91  3bf9               cmp edi,ecx
0042CC97  7d27               jge 0x42CCC0
0042CC99  84c0               test al,al
0042CC9B  0f8404ffffff       je  0x42CBA5           ; ★ 回重试
```

原始字节复核：
```
0x42CC80: e82bd9ffff        （= call 0x42A5B0，相对位移 0xFFFFD92B）
0x42CC9B: 0f8404ffffff      （= je 0x42CBA5，相对位移 0xFFFFFF04）
```

**结论成立**：`0x42A5B0` 是 §567 引用的「代际戳递增函数」（其 `0x42A5FB 8B 41 28` /
`0x42A5FE 40` / `0x42A5FF 89 41 28` 已在前序核证中确认），
而它**在重试循环体内被再次调用**，且 `0x42CC9B` 明确回跳到 `0x42CBA5`。

⇒ **同一次 `FindPath` 调用内，代际戳可被推进多次。**
⇒ W3 `Q3_SAMPLE_PLAN.md:206-211` 的「相邻两逻辑帧之间**所有**业务计数器**完全冻结**」
与「83 次读取中 **82 次完全不变**、**信息熵增益严格为 0**」**均不成立**。

### 二、已执行的传播勘误（W3 写域）

产出 `lead/re_line_20261105/W3_COSTBOUND/ERRATA_D19_20261105.md`：
- 逐字抄录被推翻的原文（`:206-211`）；
- 给出反证据（本节第一节的字节）；
- 列连带影响：**「500 Hz 过度设计」降为未证**；**1 Hz 充分性进一步削弱**；
  **两档设计的存在性不受影响**；**帧沿触发档反而更被支持**；
- **明确不解决的问题**：应采多高频率、帧内变化幅度、`300–1500 次/秒` 不可引用。

**`Q3_SAMPLE_PLAN.md` 与 `W3_COSTBOUND.md` 原文一字未改**（append-only）。

### 三、这条勘误的**方向**值得单独指出

勘误**不是**在削弱 W3 的全部结论，而是**在削弱它「1 Hz 够用」的那一侧、加强它「帧沿触发档」的那一侧**：

- W3 原本用「帧内冻结」论证**不需要高频**；
- 现在「帧内不冻结」⇒ **帧沿触发档（自适应 6–31 Hz）比 1 Hz 基线更有信息量**；
- 这与 D-19 定谳「**优先完善帧沿触发候选规格**」**方向一致**。

⇒ **D-19 的裁决不依赖这条反证据**（它另有 alpha 未校准、冻结前提不足两条理由），
但这条反证据**独立地支持了同一个取向**。

### 四、诚实账

1. **我亲验**：`0x42CC72..0x42CCA5` 的 15 条反汇编、`0x42CC80`/`0x42CC9B` 的原始字节。
2. **我未验**：`0x42CCD0`（`0x42CC79` 调的那个函数）是什么——**未查**，不影响本节结论。
3. **我未验**：`0x42CC80` 这条重试路径的**实际触发频率**
   ——「帧内不冻结」是定性结论，**「变化有多快」仍未定**。
4. **我未验**：`0x42A5B0` 是否只递增代际戳（采信前序核证：`0x42A5FB..0x42A5FF` 三段字节）。
5. 本节**不改变** D-19 定谳（裁 A 限定版）；只把其中一条**采信项**补成亲验，并落实 W3 传播勘误。
6. 本轮**零真机**、**零主台账以外的母本改动**、**未 commit**。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
