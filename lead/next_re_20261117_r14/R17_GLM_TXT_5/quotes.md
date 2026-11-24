# quotes · R17-GLM-TXT-5 引证清单（一句原文 + 文件与行号）

1. lead/next_re_20261117_r14/STATUS_BOARD.md:234 — 「🔴 **host 纠正**：应为 **`0x5A6510`**（`83 EC 70` 正常序言）、fn_end `0x5A691C`。执行方原报 `0x5A652D` **落在 `0x5A652A C1 E8 1F` 指令内部**，不是函数入口」
2. lead/next_re_20261117_r14/STATUS_BOARD.md:235 — 「🔴 **覆盖边界（必须与结论同引）**：只证「**存在至少一个**派发点会到达」，**不证唯一**、**不证运行期真的执行到**。**且不改变 ②-b 的 `[静态推断]` 收口（D-53(A)）**」
3. lead/next_re_20261117_r14/STATUS_BOARD.md:237 — 「→ 第3版 **双口径并列**：**口径 S（严格基名）397/32/383**、**口径 C（`X_Y`↔`X@Y`）403/26/377**；复合名 **660** 条（模板 634 + 非模板 26）」
4. lead/next_re_20261117_r14/STATUS_BOARD.md:238 — 「🔴 **「26 还是 32」不是对错，是两个口径**。**引用必须写明口径；只写数字不写口径不可引用**」
5. lead/GOAL_THREE_TARGETS_20261018.md:40401 — 「链：`0x5A66D4 E8 67 50 E9 FF`（call `0x43B740`，rel32 解出目标）→ `0x5A66D9 8B E8`（mov ebp,eax）→ `0x5A684D 8B 55 00`（mov edx,[ebp]）→ **`0x5A6860 FF 92 24 01 00 00`**（call [edx+0x124]）→ `[0x7E3EBC+0x124]=0x43F180`」
6. lead/next_re_20261117_r14/STATUS_BOARD.md:233 与 lead/GOAL_THREE_TARGETS_20261018.md:40402 — 均为「`.text` 内直接 `call 0x43B740` **14** 处 + `call 0x43B680` **1** 处 = **15**」
7. lead/LEAD_LOCK:908-909 与 lead/GOAL_THREE_TARGETS_20261018.md:40422 — AC4：「口径 S（严格基名）：BOTH 397 / COVERAGE_ONLY 32 / RTTI_ONLY 383」「口径 C（X_Y ↔ X@Y 复合名匹配）：BOTH 403 / COVERAGE_ONLY 26 / RTTI_ONLY 377」；台账：「口径 S（严格基名）= BOTH 397 / COVERAGE_ONLY 32 / RTTI_ONLY 383；口径 C（显式复合名 `X_Y`↔`X@Y` 匹配）= BOTH 403 / COVERAGE_ONLY 26 / RTTI_ONLY 377」
8. lead/LEAD_LOCK:923-924 — 「AC6. 🔴 台账勘误（引用旧值必同引 §1062）：§1061 的 COVERAGE_ONLY 220 已取代；§1060 的「0x4264C0 在 17 个类」实为 15」
附. lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md:45 — 「3. **`0x43F180` 调用方字节链（首次）**：…host `0x5A6510`、fn_end `0x5A691C`；构造点 15 处（`0x43B740` 14 + `0x43B680` 1）」
附. lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md:59 — 「第 3 版定谳为**双口径**：**口径 S（严格基名）397/32/383**、**口径 C（`X_Y`↔`X@Y`）403/26/377**。**只写数字不写口径 ＝ 不可引用**」
