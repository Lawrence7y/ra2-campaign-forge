# PATCH-D35R · 站点接线字节级报告

卡号 PATCH-D35R｜目录 `lead\next_re_20261117_r14\PATCH_D35R\`｜2026-11-20
目标（只读、SHA 未变）：`ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · 4,825,360 B · ImageBase `0x400000`
最终副本：`work\gamemd_r2.exe` SHA-256 `36A875775DA89239E370AAF091DBE5D3D3C5F2F8017D9EFA6A15FCDD4801C7F4`

## 1 复用上一张成果（PATCH_D35）
- 上一张副本 `PATCH_D35\work\gamemd_patched.exe`（SHA `4EBC5195…C593BB`）已在洞内 `[0x7DF781,0x7DF7A0)` 写入 13B 共享桩 + 19B 块守卫。本卡不搬用其字节作为基底，而是**从原 exe 重建**（结果等价但携带只读观测副作用），保证差异集合可控。
- 桩核心逻辑与上一张一致：`test ecx,ecx / jz → add esp,4 / jmp 0x724730 / ret`（ecx=this=`[0x887368]`；NULL 路径补做 `ret 4` 的清栈）。块守卫（针对 `0x6CD8CD`）逻辑与上一张一致，仅 rel32 按新位置重算；本卡未接 `0x6CD8C2` 站点，故块守卫本卡不执行。

## 2 站点清单（8 个，指令边界，全部 `E8 rel32 call 0x724730`）
文件偏移 = VA − ImageBase（.text VA==RawPtr==0x1000）。站点前的 `mov ecx,[0x887368]` 是 NULL 路径 this 传递，全 8 处静态证据见 `W178_PATCH/_audit/out/reach.txt`（30/30 ecx←[0x887368] 且无 NULL 守卫）。

| 站点VA | 文件偏移 | 原5B | 新5B | 新目标 | why NULL path |
|---|---|---|---|---|---|
| 0x6D1632 | 0x2D1632 | e8 f9 30 05 00 | e8 4a e1 10 00 | 0x7DF781 | host 0x6D1610: mov ecx,[0x887368] 紧接 call |
| 0x6D09FA | 0x2D09FA | e8 31 3d 05 00 | e8 82 ed 10 00 | 0x7DF781 | host 0x6D09C0: ecx←[0x887368] 无守卫 |
| 0x640427 | 0x240427 | e8 04 43 0e 00 | e8 55 f3 19 00 | 0x7DF781 | host 0x6403A0: mov ecx,[0x887368] 紧接 call |
| 0x6D059B | 0x2D059B | e8 90 41 05 00 | e8 e1 f1 10 00 | 0x7DF781 | host 0x6D04F0: ecx←[0x887368] 无守卫 |
| 0x6D0634 | 0x2D0634 | e8 f7 40 05 00 | e8 48 f1 10 00 | 0x7DF781 | host 0x6D04F0: ecx←[0x887368] 无守卫 |
| 0x6D1293 | 0x2D1293 | e8 98 34 05 00 | e8 e9 e4 10 00 | 0x7DF781 | host 0x6D1200: ecx←[0x887368] 无守卫 |
| 0x6D0940 | 0x2D0940 | e8 eb 3d 05 00 | e8 3c ee 10 00 | 0x7DF781 | host 0x6D0680: ecx←[0x887368] 无守卫 |
| 0x4A8B75 | 0xA8B75 | e8 b6 bb 27 00 | e8 07 6c 33 00 | 0x7DF781 | host 0x4A8960: mov ecx,[0x887368] 紧接 call（PATCH_MAP 首行，reach=True） |

**为何是 `E8` 而非卡面示例 `E9`**：站点原指令是 5B `E8 rel32 call 0x724730`。洞内桩尾部 `jmp 0x724730` + 终点 `ret 4` 依赖站点 `call` 压入的返回地址；若改成 `E9`(jmp) 则不压返回地址，桩末尾 `ret` 会跳到错误地址。卡面「5B E9 rel32 或等效」中的「等效」即此处保留 `E8`、仅改 rel32 指向洞内桩（`E8` 操作码字节未变，故每站点实际差异 3–4 B）。这是实现桩语义正确的必要条件，已在 DISAGREE.md 登记。

## 3 洞内桩（63B 洞 [0x7DF781,0x7DF7C0)，30B 桩 + 19B 块守卫 + 14B int3）
```
0x7DF781: 50               push eax              ; 保存
0x7DF782: 8B 44 24 04      mov eax,[esp+4]       ; 站点 call 压入的返回地址 (= site+5)
0x7DF786: A3 00 50 9F 00   mov [0x9F5000],eax    ; 只读观测槽：最后调用者返回地址
0x7DF78B: FF 05 04 50 9F 00 inc dword [0x9F5004]  ; 只读观测槽：累计命中数
0x7DF791: 58               pop eax               ; 恢复
0x7DF792: 85 C9            test ecx,ecx          ; NULL 判定（与上一张一致）
0x7DF794: 74 05            jz +5 → 0x7DF79B      ; NULL → add esp,4
0x7DF796: E9 95 4F F4 FF   jmp 0x724730          ; 非NULL 尾跳原 callee
0x7DF79B: 83 C4 04         add esp,4             ; 补做 ret 4 的 1 个参数清栈
0x7DF79E: C3               ret                   ; 复用站点压入的返回地址返回
0x7DF79F: A1 E0 71 88 00 / 85 C0 / 74 05 / E9→0x6CD8C7 / E9→0x6CD8D8   (19B 块守卫)
```
- 观测副作用驻留 `.data` 零填充区 `[0x9F5000,0x9F5004]`：该 VA 段 VirtualSize 0x367BE4 > RawSize 0x6C000，运行时零初始化、**文件中无对应字节** ⇒ 写它不改变文件 diff 集合。全 `.text` 反汇编扫描：该地址 0 条指令引用、0 处 dword 字面量，±0x100 无引用（安全填充区）。
- ASLR 关闭（`DllCharacteristics` 无 DYNAMIC_BASE）⇒ 进程基址固定 0x400000，观测槽 VA 绝对可用。

## 4 严格 diff（EVIDENCE/hashes.txt + byte_diff_full.tsv）
- 全文件逐字节比对：差异 **73 B** = 洞内 49 B + 站点 24 B；**越界差异 0**（`outside_allowed_set_diff_count=0`）。
- 允许集合 = 洞 `[0x3DF781,0x3DF7C0)` ∪ 8 站点 `[site_off,site_off+5)`。每个站点实际差异 3 B（`E8` 与 rel32 低字节恰好与原相同）。
- 洞外、站点外任何偏移改变 = FAIL；本卡实测 0。

## 5 有界真机冒烟（见 SMOKE_TABLE_R2.tsv）
- 副本从 `work\run\` 启动，最小启动集 11 MB（原始 890 MB mix 未复制；冒烟阶段用硬链接临时提供 16 个大 mix 使游戏到达 "Yuri's Revenge" 主菜单，收尾已删除全部硬链接，run 恢复 11 MB）。
- 只读采样：`OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION)` + `ReadProcessMemory` 读 `0x9F5000/0x9F5004`，从不写进程内存、不注入、不设断点。
- **1/8 站点取得桩执行证据**：0x4A8B75，`hit_count 0→2`、`last_ret=0x4A8B7A`（=站点+5），证据 `EVIDENCE/smoke_r2_diag_sites.json`（641 次连续采样）。其余 7 站点未捕获其返回地址，按铁规写「无法证明桩被执行」，「未崩」不计为有效证据。
- 限定：常规 GUI 未把 `[0x887368]` 置 NULL；即使桩被执行，NULL 分支是否走、是否能防崩，本卡无法验证。冒烟结论仅报「已观测」，不外推。
