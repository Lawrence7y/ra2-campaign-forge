# C10 · UNKNOWNS（未证 / 待 P1 细化）

本文件记录本片（镜像尾段 0x773500–0x7E038D）普查中**未能证明**的部分。所有一行语义均为 `[未证]` 猜测，未写新 `[已证]` 发现。

## 1. 577 个零证据函数（source=none → S22 兜底）
- `EVIDENCE/classification_trace.tsv` 中 `source==none` 共 **577** 行：无 self_known 名、无 RTTI 虚表槽（真实槽数下）、无源文件模块、无强字符串、无亲戚名投票、无导入 API。
- 全部归 S22 仅为兜底，**不是已证归属**。集中在本片两个簇：0x77–0x7B 段（WOL 适配器/回调 small wrapper）与 0x7C8A–0x7DE0 段之后的 CRT 内联/数学/浮点辅助（如 `fld`/`emms`/`fstp` 开头的小块，疑 CRT 浮点转换/数学内部）。
- 另有 `relay_vote` 299 行（调用图邻居弱投票）、`import` 68 行、`vtable-unmapped` 若干，同为低置信，不计 high。
- 建议 P1 用 YRpp 头文件地址名 + re_atlas kb 具名方法二次扫描；WOL 段可结合 wonline.cpp 具名方法细化，CRT 段可按 MSVC CRT 符号表对照。

## 2. 三通道 atlas 空洞（call32 36 / jmp32 71 / jmp8 169 = 276 行 / 264 独立地址）
口径见 `PROGRESS.md` 核心数字 3–4。未证部分：
- **169 个 jmp8 洞目标**：引用站点绝大多数在洞内（`sites_in_fn=0`），首指令 mov/cmp/test/call/push/lea 等，形态为**未建模代码块内短跳分支标签**。按卡判据 (e)（16B 对齐 + prev∈{nop,ret,jmp,int3} + 非 jcc 目的 + push ebp/sub esp 序言）**不计入疑似真入口**。部分地址首指令 `test eax,eax ; jne`（如 `0x775E1B`）明确是判空分支标签。
- **jmp32 71 个洞目标中真入口 = 0**：全部因 align16=0 / prev=other / 无序言 / 是 jcc 目的被排除；多数首指令 `call 0x734e60`、`mov ecx,[esp+..]`、`lea`/`emms`/`xor ecx,ecx` 等，形态为洞内分支标签或内层跳板。这印证坑 (e)「jmp32 真入口判据极易过宽」——按宽松 C05/C06 口径会把其中一部分误计为真入口，本卡一律从严。
- **12 个 call32 严格真入口**：均满足判据 (e) 全部条件，序言实核见 `EVIDENCE/entry_criteria.tsv`（`sub esp,imm` / `push ebp`）。两条独立实现（struct 通道 + pefile 通道 CORE4）地址集合一致。但其调用方站点也多在洞内（owner=None），「调用方未被 atlas 建模」这一事实 `[未证]`，需 P1 证真。
- 宽松 r14 口径得 14：多出的 `0x7AEEC0`（首 `push ecx`，仅 22B 小函数无 push ebp/sub esp）、`0x7DD2E0`（首 `mov eax,[0x87dd70]` 无序言）因缺序言被判据 (e) 剔除，未为凑数放宽。
- boundary_check：本片 gaps_raw 2,040 目标中 0 例「未判定」bail；2 例 False 为真实指令内部命中（`add byte ptr[ebp+0x53],dl` size 3，目标 `0x7C7788`/`0x7C7B4C` 落在其中），且 owner 非 None（在 `0x7C7371` 函数体内），不入 gap 集。按纪律 #3 保留 unknown 不当 False 已落实。

## 3. 虚表直指、atlas 未收录入口 = 6（双通道一致）
- `0x7AC9C0`/`0x7B4310`/`0x7B9D90`/`0x7BC7D0`/`0x7BC870`/`0x7BC920`：RTTI 虚表槽直接指向、但不在 atlas 12916 入口中、且 owner()==None（真洞）。首指令均为 `mov eax,[ecx+4]` / `mov eax,[esp+N]` / `mov edx,[esp+0x1c]` 形态的小 getter/inline 方法（属 `WWMouseClass`/`WOnline` 邻接类）。
- 双通道（自写 struct PE RTTI vs pefile 重做 COL→TD→vtable）各自得 6，集合完全一致；两种口径（not-in-atlas-entries / owner()==None）均得 6（无落在已有函数体内者），故该数无歧义。
- 这 6 个入口与三通道 gap 的 12 个严格入口**不重叠**（它们是 vtable 引用而非 call/jmp 引用），说明 atlas 分母在本片至少漏 6 个 vtable 直指函数 + 12 个调用洞入口（两家集合并集 18，见核心数字 4–5）。P1 应把这 18 个补入函数基数。

## 4. 具名函数语义仍为猜测 / 本片已证地址照引不推翻
- 49 个 `[已证]` 仅证明「名字来自 YRpp/kb 地址名」，不证明其一行语义（如 `WWMouseClass::GetX`、`CRT::sprintf`、`YRDDraw::DDCreate` 的具体行为）。语义列均按名推测，标 `[未证]`。
- `CRT::int`（2 处）与 `Unsorted::sub_776D80` 系 YRpp/kb 提取噪声（类型名/未具名），已在 `clean_known` 剔除，不计 high。
- 写卡前已 grep 台账 `GOAL_THREE_TARGETS_20261018.md`：台账 §923–§928 的具名地址（矿石价值 0x485020、绘制链 0x5F4B10/0x5F4D30/0x5F5F40、DLC 0x52CB90 等）均在 C05/C06 片，本卡未触碰。本片地址段内台账无 direct 落点。WOL/CRT 相关 facts 台账未收录，本卡不新增 `[已证]`。

## 5. 通用模板包装器的归属（承 C08 修正）
- 本片 `T_DynamicVectorClass_PAUWinsockBufferType_WinsockInterfaceClass__`、`T_VectorClass_PAUtConnInfoStruct__`、`T_BlitTrans_E/G` 等模板容器/Blitter 包装类，按 C08 起的 `GENERIC_WRAPPERS` 优先判据归 S22 core=False（不按嵌入 T 虚高）。其中 WinsockBufferType/tConnInfoStruct 的实例化类型属 S18，但模板本身是容器基础设施 → S22。见 DISAGREE.md。
- 这批包装器对具体 T 的语义 `[未证]`；P1 可按其静态实例全局与调用链反推服务对象。
