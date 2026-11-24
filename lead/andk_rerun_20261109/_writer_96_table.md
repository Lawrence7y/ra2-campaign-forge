| gate | 输入 | 项 | 检查内容 | BASE(原件) | WA(只查第一词) | WB(只查第二词) | SENT(零命中哨兵) | 该格依据 |
|---|---|---|---|---|---|---|---|---|
| d27 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | A | [2] | ^main:(A|B|C)$ 声明行 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | A | [3] | 7 个必需二级标题 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | A | [4] | 新证据是否成立⊇循环论证 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | A | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | A | [6] | 未背书⊇外推 OR 卡顿不存在（OR 项） | PASS | PASS | PASS | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/0/1，P_WA=True P_WB=True` |
| d27 | A | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | A | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [2] | ^main:(A|B|C)$ 声明行 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [3] | 7 个必需二级标题 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [4] | 新证据是否成立⊇循环论证 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [6] | 未背书⊇外推 OR 卡顿不存在（OR 项） | PASS | PASS | FAIL | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/1/1，P_WA=True P_WB=False` |
| d27 | B | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | B | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d27 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d27 | C | [2] | ^main:(A|B|C)$ 声明行 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d27 | C | [3] | 7 个必需二级标题 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d27 | C | [4] | 新证据是否成立⊇循环论证 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d27 | C | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d27 | C | [6] | 未背书⊇外推 OR 卡顿不存在（OR 项） | FAIL | FAIL | FAIL | FAIL | `EXIT=1 fail_items=[6]；WA/WB/SENT EXIT=1/1/1，P_WA=False P_WB=False` |
| d27 | C | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d27 | C | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[6]` |
| d28 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | A | [2] | q1/q2 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | A | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | A | [4] | D 链处置⊇历史数字 OR 1681（OR 项） | PASS | PASS | PASS | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/0/1，P_WA=True P_WB=True` |
| d28 | A | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | A | [6] | 未背书 AND 词表(外推,口径 B) | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | A | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | A | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [2] | q1/q2 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [4] | D 链处置⊇历史数字 OR 1681（OR 项） | PASS | PASS | FAIL | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/1/1，P_WA=True P_WB=False` |
| d28 | B | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [6] | 未背书 AND 词表(外推,口径 B) | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | B | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d28 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d28 | C | [2] | q1/q2 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d28 | C | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d28 | C | [4] | D 链处置⊇历史数字 OR 1681（OR 项） | FAIL | FAIL | FAIL | FAIL | `EXIT=1 fail_items=[4]；WA/WB/SENT EXIT=1/1/1，P_WA=False P_WB=False` |
| d28 | C | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d28 | C | [6] | 未背书 AND 词表(外推,口径 B) | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d28 | C | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d28 | C | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | A | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | A | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | A | [4] | 冲突是否成立⊇互斥 OR 前提（OR 项） | PASS | PASS | PASS | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/0/1，P_WA=True P_WB=True` |
| d29 | A | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | A | [6] | 未背书 AND 词表(口径 B,外推,191) | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | A | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | A | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [4] | 冲突是否成立⊇互斥 OR 前提（OR 项） | PASS | PASS | FAIL | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/1/1，P_WA=True P_WB=False` |
| d29 | B | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [6] | 未背书 AND 词表(口径 B,外推,191) | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | B | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d29 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | C | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | C | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | C | [4] | 冲突是否成立⊇互斥 OR 前提（OR 项） | FAIL | FAIL | FAIL | FAIL | `EXIT=1 fail_items=[4]；WA/WB/SENT EXIT=1/1/1，P_WA=False P_WB=False` |
| d29 | C | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | C | [6] | 未背书 AND 词表(口径 B,外推,191) | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | C | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d29 | C | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | A | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | A | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | A | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | A | [4] | 三档权衡的实质⊇93.98 OR 误报率（OR 项） | PASS | PASS | PASS | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/0/1，P_WA=True P_WB=True` |
| d30 | A | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | A | [6] | 未背书 AND 词表(外推,栈采样) | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | A | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | A | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [4] | 三档权衡的实质⊇93.98 OR 误报率（OR 项） | PASS | PASS | FAIL | FAIL | `EXIT=0 fail_items=[]；WA/WB/SENT EXIT=0/1/1，P_WA=True P_WB=False` |
| d30 | B | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [6] | 未背书 AND 词表(外推,栈采样) | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | B | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=0 fail_items=[]` |
| d30 | C | [1] | 两文件存在/非空/UTF-8 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | C | [2] | q1 恰一行合法声明 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | C | [3] | 7 个必需小节 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | C | [4] | 三档权衡的实质⊇93.98 OR 误报率（OR 项） | FAIL | FAIL | FAIL | FAIL | `EXIT=1 fail_items=[4]；WA/WB/SENT EXIT=1/1/1，P_WA=False P_WB=False` |
| d30 | C | [5] | 授权边界⊇本次不授权 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | C | [6] | 未背书 AND 词表(外推,栈采样) | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | C | [7] | 裁决书引用≥8 处 | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
| d30 | C | [8] | FACTCHECK⊇selfBias | PASS | PASS | PASS | PASS | `EXIT=1 fail_items=[4]` |
