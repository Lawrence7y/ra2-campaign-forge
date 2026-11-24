D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe | sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R27-SLOT107-V2 · 正向入口集重做 slot #107 调用方追查

## 0. R25 作废原因

- R25 用「R12 hit host ∩ R23 ctor host」精确相等求交得 0，据此报 `0x449440` 未取得；该交集的两个输入都不可信，结论作废。
- R12 `hits.tsv` 的 host 靠字节扫 `C3` 判入口：`0x5A680D 0F BF C3` (`movsx eax,bx`) 中的 `C3` 是 modrm，被当成 ret，真 host `0x5A6510` 误记 `0x5A6810`，且 `0x5A66D9 8B E8` 证明基址来自构造对象而非栈，R12 的 `NON_TARGET` 亦误判。
- 本卡复看实际 `R17_R23_CALLER_PATH/ctor_sites.tsv`：其 `call_target` 列才是 `0x43B740/0x43B680`；`host` 列本身也不是可信函数入口集，15 行中有 4 行与本卡逐点定界的真实 host 不同（0x5A66D4, 0x5A96F8, 0x5CAB60, 0x7396C3）。R25 把该列当交集键，所以零交集无证明力。

## 1. 可信入口集与扫描口径

- 镜像：D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe；sha256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；size 4825360 B。
- `.rdata` raw 扫描 200704 B（50176 个对齐 dword）；RTTI 正向索引：TD 961、COL 1211、vtable 1211，重算 vtable 槽值 **14039 个**（去重 6687 个；卡面“约 14044”按实测报数）。`.data` 为 TD 扫描 442368 B。
- 入口集 = 全部 `6687` 个 vtable 槽值（去重后）+ `0x43B740`/`0x43B680` + `.text` 起点 + 正向 padding 锚点（NOP run>=4 / CC run>=2）= **16917** 个；**未用 C3/C2 字节扫入口**。
- `.text` raw `4063232` B 用于定位 15 个 `E8` 直接构造点；每个点都从其 host 锚点解码验证为指令边界。
- 派发扫描只在 15 个真实 host 的 **10687 个唯一函数 / 10687 B** 内进行，解码 **3241 条指令**；反汇编函数个数 **13**（15 个构造点落在 13 个唯一 host）。

## 2. 15 个构造点的真实 host（逐点字节定界）

| ctor site | target | R23 host 列 | 真实 host | fn_end | 锚点 | 位置断言 | 与 R23 不同 |
|---|---|---|---|---|---|---|---|
| 0x44FB22 | 0x43B740 | 0x44F820 | 0x44F820 | 0x44FE52 | POST_PADDING | PASS 0x44F820 <= 0x44FB22 < 0x44FE52 | SAME |
| 0x44FD8A | 0x43B740 | 0x44F820 | 0x44F820 | 0x44FE52 | POST_PADDING | PASS 0x44F820 <= 0x44FD8A < 0x44FE52 | SAME |
| 0x453ECF | 0x43B680 | 0x453E20 | 0x453E20 | 0x454186 | VTABLE_SLOT | PASS 0x453E20 <= 0x453ECF < 0x454186 | SAME |
| 0x45E81F | 0x43B740 | 0x45E800 | 0x45E800 | 0x45E876 | VTABLE_SLOT | PASS 0x45E800 <= 0x45E81F < 0x45E876 | SAME |
| 0x45E89C | 0x43B740 | 0x45E880 | 0x45E880 | 0x45E8AB | VTABLE_SLOT | PASS 0x45E880 <= 0x45E89C < 0x45E8AB | SAME |
| 0x473866 | 0x43B740 | 0x4737F0 | 0x4737F0 | 0x47391E | POST_PADDING | PASS 0x4737F0 <= 0x473866 < 0x47391E | SAME |
| 0x590574 | 0x43B740 | 0x5904B0 | 0x5904B0 | 0x5905C4 | POST_PADDING | PASS 0x5904B0 <= 0x590574 < 0x5905C4 | SAME |
| 0x5954A1 | 0x43B740 | 0x595400 | 0x595400 | 0x595674 | POST_PADDING | PASS 0x595400 <= 0x5954A1 < 0x595674 | SAME |
| 0x5A66D4 | 0x43B740 | 0x5A652D | 0x5A6510 | 0x5A691C | POST_PADDING | PASS 0x5A6510 <= 0x5A66D4 < 0x5A691C | DIFF |
| 0x5A84B1 | 0x43B740 | 0x5A82E0 | 0x5A82E0 | 0x5A8719 | POST_PADDING | PASS 0x5A82E0 <= 0x5A84B1 < 0x5A8719 | SAME |
| 0x5A94FC | 0x43B740 | 0x5A8F00 | 0x5A8F00 | 0x5A9916 | POST_PADDING | PASS 0x5A8F00 <= 0x5A94FC < 0x5A9916 | SAME |
| 0x5A96F8 | 0x43B740 | 0x5A95B0 | 0x5A8F00 | 0x5A9916 | POST_PADDING | PASS 0x5A8F00 <= 0x5A96F8 < 0x5A9916 | DIFF |
| 0x5CAB60 | 0x43B740 | 0x5CA800 | 0x5CAAC0 | 0x5CABC4 | VTABLE_SLOT | PASS 0x5CAAC0 <= 0x5CAB60 < 0x5CABC4 | DIFF |
| 0x6C35D3 | 0x43B740 | 0x6C3590 | 0x6C3590 | 0x6C3609 | VTABLE_SLOT | PASS 0x6C3590 <= 0x6C35D3 < 0x6C3609 | SAME |
| 0x7396C3 | 0x43B740 | 0x7393F2 | 0x7393C0 | 0x739AB8 | POST_PADDING | PASS 0x7393C0 <= 0x7396C3 < 0x739AB8 | DIFF |

每行的前 16 字节、前序 16 字节、末尾真 `ret` 字节、fn_end 后 `90|CC` 填充、下一可信入口、从 host 到 ctor 的解码步数见 `ctor_hosts.tsv`。所有 `padding_check=PASS`，所有 `host <= site < fn_end` 断言成立。

## 3. host 内 `[reg+0x124]` / `[reg+0x1AC]` 派发

- `0x1AC` 命中：**0 条**。`0x124` 命中：**6 条**（作为正控/对照，说明扫描器能命中已知形态）。
- 形态覆盖：`call dword ptr [reg+disp32]` 与 `mov reg2,[reg+disp32]` 后 12 条内 `call reg2`；由 Capstone 在锚定函数体内解码，不按字节猜边界。

| site | disp | bytes | base | host | ctor 关系 | 基址是否构造对象 | 覆写与写点 |
|---|---|---|---|---|---|---|---|
| 0x5A6860 | 0x124 | `ff 92 24 01 00 00` | edx | 0x5A6510 | CTOR_BEFORE_HIT | YES_DERIVED_FROM_CTOR_OBJECT | CTOR_PATH_NO_EBP_OVERWRITE (0x5A66C1 74 23 bypasses ctor to 0x5A66E6 xor ebp,ebp); EDX had 3 earlier writes, final 0x5A684D not overwritten before dispatch |
| 0x739428 | 0x124 | `ff 90 24 01 00 00` | eax | 0x7393C0 | CTOR_AFTER_HIT | NO | BASE_NOT_DERIVED_FROM_CTOR_OBJECT; base loaded from incoming this/member vptr; ctor_site=0x7396C3 is downstream |
| 0x739565 | 0x124 | `ff 90 24 01 00 00` | eax | 0x7393C0 | CTOR_AFTER_HIT | NO | BASE_NOT_DERIVED_FROM_CTOR_OBJECT; base loaded from incoming this/member vptr; ctor_site=0x7396C3 is downstream |
| 0x7395B4 | 0x124 | `ff 92 24 01 00 00` | edx | 0x7393C0 | CTOR_AFTER_HIT | NO | BASE_NOT_DERIVED_FROM_CTOR_OBJECT; base loaded from incoming this/member vptr; ctor_site=0x7396C3 is downstream |
| 0x739670 | 0x124 | `ff 92 24 01 00 00` | edx | 0x7393C0 | CTOR_AFTER_HIT | NO | BASE_NOT_DERIVED_FROM_CTOR_OBJECT; base loaded from incoming this/member vptr; ctor_site=0x7396C3 is downstream |
| 0x739AA1 | 0x124 | `ff 92 24 01 00 00` | edx | 0x7393C0 | CTOR_BEFORE_HIT | NO | BASE_NOT_DERIVED_FROM_CTOR_OBJECT; base loaded from incoming this/member vptr; ctor_site=0x7396C3 in host but not source of base |

逐条字节链与完整寄存器写点统计见 `dispatch_hits.tsv`。要点：
- `0x5A6860`：构造路径 `0x5A66D4 E8 67 50 E9 FF call 0x43B740` → `0x5A66D9 8B E8 mov ebp,eax` → `0x5A684D 8B 55 00 mov edx,[ebp]` → `0x5A6860 FF 92 24 01 00 00 call [edx+0x124]`。构造成功路径上 EBP 无覆写：`0x5A66C1 74 23` 的失败分支跳到 `0x5A66E6 xor ebp,ebp`，绕过构造点；EDX 在到达最终写点前有 3 次早写，最终写点后到派发无覆写。
- `0x7393C0` host 的 5 条 `0x124` 均以传入 `this` 的 `[ebp]`（或经 `[ebp+0x674]`）取 vptr：其中 4 条在构造点 `0x7396C3` 之前，1 条 `0x739AA1` 在之后但基址来自 `[ebp]`，构造出的对象在 `EBX`（`0x7396C8 8B D8`）并用于成员写入，未成为这些派发的基址。即：这些 host 命中不构成该构造对象到 `0x449440` 的链。

## 4. 结论与覆盖边界

- **在这 15 个构造点的真实 host 内，未发现 `[reg+0x1AC]` 派发；`0x449440 (BuildingClass vtable #107, +0x1AC)` 的调用方本轮未取得。**
- 本轮只证明「在这 15 个 host 内未发现」；不证明不存在、不证明唯一、不证明运行期真的执行到；**不改变 ②-b 的 `[静态推断]` 收口（D-53(A)）**。
- 覆盖边界：对象经全局/成员字段长距离传递、跨函数传入、由非 `0x43B740`/`0x43B680` 构造，或采用先算目标地址、跳板、索引型、disp8、段覆盖、跨节代码，均不在本轮 15-host 定偏移扫描内；因此本轮负面结论不外推为全镜像不存在。

## 5. 未取得项

- `0x449440` 的字节证实调用方：未取得。
- 唯一性与运行期实际执行证据：按卡不证明，未取得（不是待补缺陷）。

## 6. 产物

- `REPORT.md`、`ctor_hosts.tsv`、`dispatch_hits.tsv`、`work.py`。
