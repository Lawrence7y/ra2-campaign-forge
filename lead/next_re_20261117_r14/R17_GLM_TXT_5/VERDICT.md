# VERDICT · 卡 R17-GLM-TXT-5 · 纯文本一致性 + 表内算术第二意见（8 项）

自报身份（原始字符串）：provider = `bigmodel-api`，model = `GLM-5.3-Flash`（完整自报标识 `bigmodel-api/GLM-5.3-Flash`）。
边界遵守：仅文字一致性与表内算术；未做字节级、装配形态、宿主身份、函数边界、类名正确性判定；恰好 8 项；除本目录两产物外只读未改。

#1 AGREE —— STATUS_BOARD.md:234 写明 host 纠正：`应为 **`0x5A6510`**（`83 EC 70` 正常序言）…执行方原报 `0x5A652D` **落在 `0x5A652A C1 E8 1F` 指令内部**，不是函数入口`。
#2 AGREE —— STATUS_BOARD.md:235 写明两条边界：`只证「**存在至少一个**派发点会到达」，**不证唯一**、**不证运行期真的执行到**。**且不改变 ②-b 的 `[静态推断]` 收口（D-53(A)）`。
#3 AGREE —— STATUS_BOARD.md:237 写明双口径并列且数字逐位相符：`第3版 **双口径并列**：**口径 S（严格基名）397/32/383**、**口径 C（`X_Y`↔`X@Y`）403/26/377**`。
#4 AGREE —— STATUS_BOARD.md:238 写明等价表述：`**引用必须写明口径；只写数字不写口径不可引用**`。
#5 AGREE —— GOAL_THREE_TARGETS_20261018.md:40401 五地址齐全且顺序正确：``0x5A66D4` …→ `0x5A66D9` …→ `0x5A684D` …→ **`0x5A6860`**（call [edx+0x124]）→ ``[0x7E3EBC+0x124]=0x43F180``。
#6 AGREE —— STATUS_BOARD.md:233 与台账 GOAL_THREE_TARGETS_20261018.md:40402 同写 `call 0x43B740` **14** 处 + `call 0x43B680` **1** 处 = **15`，14+1=15 算术自洽、两处一致。
#7 AGREE —— LEAD_LOCK AC4（lead/LEAD_LOCK:908-909）`口径 S（严格基名）：BOTH 397 / COVERAGE_ONLY 32 / RTTI_ONLY 383；口径 C（X_Y ↔ X@Y 复合名匹配）：BOTH 403 / COVERAGE_ONLY 26 / RTTI_ONLY 377` 与台账 §1062 事项 3（GOAL_THREE_TARGETS_20261018.md:40422）`口径 S（严格基名）= BOTH 397 / COVERAGE_ONLY 32 / RTTI_ONLY 383；口径 C（显式复合名 X_Y↔X@Y 匹配）= BOTH 403 / COVERAGE_ONLY 26 / RTTI_ONLY 377` 六个数完全相同。
#8 AGREE —— LEAD_LOCK:923-924 AC6 写了两条勘误：`§1061 的 COVERAGE_ONLY 220 已取代；§1060 的「0x4264C0 在 17 个类」实为 15`。

附加只读检查（不计入 8 项）：R17_DELIVERY\DELIVERY_SUMMARY.md **已包含**两项 —— DELIVERY_SUMMARY.md:45 已有 `0x43F180 调用方字节链（首次）…host 0x5A6510、fn_end 0x5A691C；构造点 15 处`；DELIVERY_SUMMARY.md:59 已有 `第 3 版定谳为**双口径**：口径 S（严格基名）397/32/383、口径 C（`X_Y`↔`X@Y`）403/26/377。**只写数字不写口径 ＝ 不可引用**`。

OVERALL: CONSISTENT
