D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe  sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R26-HOST-ROLE · 报告

## 范围与锚点（只读取证）
- 镜像 sha256 首段 `73201CC0`，尾段 `F67476`，与钉死值一致。
- 只读静态分析；未建进程、未调试、未启动 gamemd；产物仅写本目录。
- 反汇编边界：`[0x5A6510,0x5A691C)`，共 `0x40C = 1036` 字节、308 条指令；入口字节 `83 ec 70 53 8b 5c 24 78 b8 67 66 66 66 55 8b 4b`，末 16 字节 `09 50 e8 2a 22 22 00 83 c4 04 83 c4 70 c2 04 00`。
- 直接调用者入口反汇编：`0x5A5020..0x5A5323`（含调用点 `0x5A531E` 的 5 字节），771 字节；调用点在线性反汇编的指令边界上，断言 PASS。
- 数据扫描：`.text` raw `0x401000` 起 `4,063,232` 字节（只找 `E8 rel32`）；`.rdata` raw `0x7E1000` 起 `200,704` 字节；`.data` raw `0x812000` 起 `442,368` 字节。合计数据扫描 `643,072` 字节；未反汇编其它函数体。

## Q1 · `0x5A6510` 自己是不是某类 vtable 方法
**未取得（不在任何 vtable 槽内）。**

链条扫描：在 `.data` 中按 TD 头 `0x7F9594/0` 与 TD+8 内联名取得 `988` 个 TypeDescriptor；在 `.rdata` 中按 `COL+12 → TD`、`COL+16 → 合法 CH descriptor` 取得 `1214` 个 COL；对每个 `vtable[-4]` COL 引用取 `vbase=引用地址+4`，从 vbase 起逐 dword 读取连续 `.text` 函数指针。

- 枚举 vtable：`1214` 张（全部有至少 1 个连续槽）。
- 扫描槽值：`14,044` 个 dword。
- 槽值 `== 0x5A6510`：`0` 处。
- `.rdata` 对齐 dword 原文 `10 65 5A 00`：`0` 处。
- 因无命中，vtable 基址/槽号/类名均为**未取得**；不给出任何推测类名。

## Q2 · 直接 `call 0x5A6510` 的全部 site
`1` 处：

| site | 字节 | 目标 | 直接调用者入口 | 边界 |
|---|---|---|---|---|
| `0x5A531E` | `E8 ED 11 00 00` | `0x5A6510` | `0x5A5020` | PASS |

调用者入口字节可证：`0x5A530D mov esi,eax`、`0x5A530F test esi,esi`、`0x5A5313 push esi`、`0x5A5316 call 0x5A5B50`、`0x5A531B push esi`、`0x5A531E call 0x5A6510`。即同一个 `esi` 先经 `0x5A5B50`，再作为参数传给 `0x5A6510`。结论：不是 0 处，不是仅靠虚派发到达；在本镜像 `.text` 内是少数单点直接调用。

## Q3 · `0x5A6510` 在做什么（只报字节可证）

### 参数与 `this`
- 函数 `ret 4`，只有 1 个栈参数；未见 ecx 作为 `this` 的写法或向 `[this]` 装 vtable。
- 入口在仅 push ebx 后取 `mov ebx,[esp+0x78]`，即原始栈参数；四个 push 完成后同一参数在 `[esp+0x84]`，`0x5A66F3/0x5A68B7` 重新装入 ebx。
- 读参数偏移：`[arg+0x10]`（`0x5A651E`、`0x5A6707`）与 `[arg+4]`（`0x5A6747`）。前者参与两段除法/随机计数，后者按随机索引取数组元素并保存到 `[esp+0x28]`。
- 未见其它参数偏移读取。

### 构造 `0x5A66D4` 之前
- `0x5A6518..0x5A6596`：用 `0x66666667` 魔数除以 10/20，调用 `0x65C780`（ecx=`0xABE890`）与 `0x7C5F00`，并读浮点常量 `0x7ED898`；结果折半存入 ebp。
- `0x5A659A..0x5A65AC`：两个 0 入栈，`lea ecx,[esp+0x70]`，`call 0x5AD6F0`；返回值 `[esp+0x70]` 进入后续循环。
- `0x5A65CA..0x5A661F`：遍历 `0x82B138..0x82B17C` 的 dword，经 `call [0x7E5BC4+8]` 过滤，把通过项存入 `[esp+0x6c]` 指向的数组，计数在 `[esp+0x78]`。
- `0x5A6621..0x5A6634`：`mov ecx,0x82BA08`，`call 0x5117D0`，再 `call 0x502D30`，结果 eax 保存到 `[esp+0x30]`。`0x82BA08` 处 ASCII 原文为 `Neutral`。
- `0x5A6661..0x5A66A0`：按 `[esp+0x78]` 随机取索引，调用 `0x65C780`/`0x7C5F00`。
- `0x5A66A2..0x5A66D1`：从 `[esp+0x6c]` 数组取元素 → `call 0x45E7B0` → esi；`push 0x720; call 0x7C8E17; test eax,eax`。eax 为 0 时跳过构造。
- `0x5A66C3..0x5A66D4`：依次压入 `[esp+0x30]` 与 `[0xA83C6C + esi*4]`，令 `ecx=eax`，`call 0x43B740`（BuildingClass 构造点）；返回值 `eax → ebp`。

### 构造 `0x5A66D4` 之后
- `[esp+0x14]=0`、byte `[esp+0x13]=0`；随后进入最多 `0x3C` 次的外层尝试（`0x5A66FC..0x5A68EB`）。
- `0x5A6747..0x5A675B`：再读 `[arg+4]` 选 ebx；读 `[ebp+0x520]` 取其 vptr，`call [vptr+0x90]`，入栈参数 1，返回 edi。
- `0x5A6768..0x5A67E3`：读 `word [edi]`、`word [edi+2]`，判 `0x7FFF` 哨兵；`ecx=0x87F7E8; call 0x5657a0`；`call 0x486670`、`call 0x486650`；读 `[esi+0xE4]`、比较 `[esi+0xEC]==3`；`push 1; push esi; ecx=0x87F7E8; call 0x578540`，结果写入 byte `[esp+0x12]`。
- `0x5A6810..0x5A6845`：读 `[ebp]` 的 vptr，压入坐标结构指针与 0，`call [vptr+0xD8]`；al 为 0 时跳过 slot73。
- `0x5A6847..0x5A6860`：读 `[ebp+0x520]`，令 `eax=[ecx+0xA0]`，写回 `[ebp+0x6C]` 与 `[ebp+0x70]`；读 `[ebp]` 的 vptr 到 edx，`push 2`，`mov ecx,ebp`，`call [edx+0x124]`。`0x124/4=73`，即 BuildingClass slot73（`0x43F180`）。
- `0x5A6866..0x5A68A0`：递增 `[esp+0x1c]`，置 byte `[esp+0x13]=1`；若随机类型序号 `>0x11` 且在数组界内，则左移 `[esp+0x6c]` 数组元素，即从候选表移除被选项。
- `0x5A68C2..0x5A68D5`：若 byte `[esp+0x13]==0` 且 ebp 非空，读 `[ebp]` vptr，`push 1`，`call [vptr+0x20]`。
- `0x5A68F1..0x5A6919`：读 `[esp+0x6c]`，置 `[esp+0x68]=0x7E5C24`，条件成立则 `push eax; call 0x7C8B3D`；最后 `ret 4`。

### `0x5A6860` 返回值去向
**丢弃。** 下一条 `0x5A6866 mov edx,[esp+0x1c]`，随后 `0x5A686A mov eax,[esp+0x28]`；`call [edx+0x124]` 留下的 EAX 未被 test/compare，也未被保存到局部变量，而是被 `[esp+0x28]` 覆盖。按字节数据流，这是一次**命令/副作用型**派发，不是查询返回值后分支。

### 字符串引用
- 有且仅有一处 bounded ASCII 引用：`0x82BA08` → `Neutral`，取用处 `0x5A6621 mov ecx,0x82BA08`（随后 `0x5A6626 call 0x5117d0`）。
- 被调函数内部字符串不在本卡反汇编边界内，未纳入。

## Q4 · 场景推断（均为推断，非事实）
1. **候选 A：地图生成/初始布景阶段的中立建筑放置。强度：中。** 依据：唯一直接调用者 `0x5A5020` 入口读 `[this+0x60]` 并用浮点/随机循环构造候选；`0x5A5308 call 0x5A5360` 得到非空 esi 后才传入本函数；本函数读 `Neutral`、随机选全局建筑类型、构造 BuildingClass，并在成功路径做 slot73 派发。缺少任何函数符号/语义字符串把 `[this+0x60]`、`0x5A5360` 定名为地图生成器，因此不升级为事实。
2. **候选 B：一次性批量尝试器，接受一个候选后从候选表移除并清理临时对象。强度：中。** 依据：外层循环上限 `0x3C`；成功路径置 `[esp+0x13]=1` 并左移 `[esp+0x6c]` 数组；全程未接受且 ebp 非空时走 `call [vptr+0x20]` 带参数 1；slot73 返回值被丢弃，表现为触发副作用而非取状态。可证伪观测：若运行时显示 `[esp+0x6c]` 数组并非候选集合，或 `call [vptr+0x20]` 不释放临时对象，则本条被削弱或证伪。

确切游戏语义名：**未取得**。不把 `0x5117D0`、`0x502D30`、`0x5A5360`、`0x5A5B50`、slot `0x90/0xD8/0x20` 猜成具名 API。

## 产物
- `REPORT.md`：本报告
- `disasm.txt`：`[0x5A6510,0x5A691C)` 锚点对齐全量反汇编
- `caller_entries.txt`：直接调用者入口到 call site 的 771 字节反汇编
- `callers.tsv`：Q2 直接调用点
- `vtable_hits.tsv`：Q1 命中表（空表，仅表头）
- `work.py`：可复跑脚本
- `_result.json`：机器可读中间结果
