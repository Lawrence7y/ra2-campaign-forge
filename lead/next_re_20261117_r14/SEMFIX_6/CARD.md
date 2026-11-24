# SEMFIX-6 · 补写 **6 行**语义栏（`SEMFIX-REST` 漏掉的）

## 为什么是这 6 行
`SEMFIX-REST` 卡面列 48 行、交了 41 行，声称「另 7 行已有正确语义未动」。**但其中 6 行并非如此**：
它们的语义栏是 **43~48 字符的模板语**，且**前缀还写着 `[静态推断]`**（与 grade `[已证]` 自相矛盾）：
| entry | 现语义栏 |
|---|---|
| `0040F0A0` | `[静态推断] Particles/Anim member (rtti-vftable)` |
| `0040F150` | `[静态推断] Particles/Anim member (rtti-vftable)` |
| `00417FE0` | `[静态推断] ObjectModel/Vtables member (rtti-vftable)` |
| `0041A5C0` | `[静态推断] ObjectModel/Vtables member (rtti-vftable)` |
| `0041FB10` | `[静态推断] House/AI/Team member (rtti-vftable)` |
| `0044ACF0` | `[静态推断] Production/Economy member (rtti-vftable)` |

（第 7 行 `0064DAB0` 确有 102 字符的真 CRC 描述，**不需要改**。）

## 审计已给的 ③ 判据（原料在 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\ROW_VERDICTS.tsv` 的 `criterion` 列）
- `0040F0A0`（S20）：`完整复制循环 0x40F0EE..0x40F0FC（读 [edx+eax*4-4]→写 [edi+eax*4-4]→inc eax→cmp/jl 回边），伴 0x7C8E17 分配、0x7C8B3D 释放、字段 +4/+8/+0xC/+0xD 形状；§8.4 slot2=SetC`
- `0040F150`（S20）：`查找循环 0x40F163..0x40F16D（cmp [ecx],esi → inc eax/add ecx,4/cmp/jl）+ 未命中 or eax,-1(0x40F16F) 可证伪返回约定；§8.4 slot4=FindItemIndex`
- `00417FE0`（S05）：`跳表：0x417FF9 cmp eax,0xa + 0x417FFC ja 0x418D1D(越界守卫) + 0x417FFF jmp dword[eax*4+0x418D58]，表 10 槽目标全落 .text`
- `0041A5C0`（S05）：`多路守卫链 + 15 次调用 + RNG 尾；[+0x6C4]虚调与 vt[+0x1c8] 比较决定分支，结局互斥`
- `0041FB10`（S14）：`[+0xA0] 三路分派(dec/je/dec/jne，值 1/2/其它)选 owner 指针；[+0xA8] 带 cmp -1 索引 0xA83C9C`
- `0044ACF0`（S12）：`跳表 0x44B728 共 11 槽、cmp bound=0xA，各目标落 .text 可逐路核`

## 每行新语义栏必须含
1. **一句话总述**：这函数整体做什么。
2. **D-42 ③b 的哪个充分条件**（`R14_COMMON §8.6`）：① 跳表/多路守卫链 ② 可证伪错误码 ③ 内存形状断言 ④ 完整循环 I/O。
3. **指令偏移**（如 `0x40F0EE..0x40F0FC` 回边）。
4. **不许**出现 `[静态推断]`/`[未证]` 前缀，**不许**出现「槽语义未证」「rtti-vftable」这类模板语。

## 硬要求
- **只改第 4 列（one_line_semantics）**：grade 保持 `[已证]`、name 保持原样、subsystem 不动。
- **⑮ 体内出现**：语义里引用的每个偏移必须在体内真出现（自己反汇编核，不只抄 criterion）。
- **⑲**：capstone 5.0.7 无 `op.index`（`op.mem.index`，无 index 返 0 非 None）。
- **⑨**：这 6 行盘上均应为 `[已证]`，自己核对。

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_6\`：`PROGRESS.md`（≤30 行）/ `EVIDENCE\` / `work\` / `coverage_delta.tsv`（8 列 6 行，**第 8 列必须为 `[已证]→[已证]`**）
**开工 10 分钟内先落骨架。严禁建 venv / pip install。**

## 核心数字
① 补写行数（目标 6）② 每行新语义字符数（应 ≥80）③ 每行引用的偏移 + 体内命中自证 ④ grade/name 零变更自证