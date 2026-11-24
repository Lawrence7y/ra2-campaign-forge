"""W178-PATCH deliverable generator: PATCH_MAP.tsv, CANDIDATES.md, RISKS.md,
UNKNOWNS.md, DISAGREE.md, PROGRESS.md, coverage_delta.tsv.
Reads EVIDENCE/core.json / UNIT_TEST.json / baseline.json. Writes only card dir.
"""
from __future__ import annotations
import json, os, struct
import capstone, pefile
class _Bin:
    def __init__(self,p):
        self.pe=pefile.PE(p,fast_load=True); self.ib=self.pe.OPTIONAL_HEADER.ImageBase; self.secs=[]
        for s in self.pe.sections:
            n=s.Name.decode(errors='replace').rstrip('\x00')
            self.secs.append(dict(name=n,va=self.ib+s.VirtualAddress,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
    def read(self,va,n):
        for s in self.secs:
            if s['va']<=va and va+n<=s['va']+s['rawsize']:
                o=s['raw']+va-s['va']; return self.pe.__data__[o:o+n]
        raise ValueError
b=None  # initialized after EXE below
ROOT=r"D:\Project\ra2-campaign-forge"
CARD=os.path.join(ROOT,"lead","next_re_20261117_r14","W178_PATCH")
EV=os.path.join(CARD,"EVIDENCE")
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
b=_Bin(EXE)
CORE=json.load(open(os.path.join(EV,'core.json'),encoding='utf-8'))
UT=json.load(open(os.path.join(EV,'UNIT_TEST.json'),encoding='utf-8'))
BL=json.load(open(os.path.join(EV,'baseline.json'),encoding='utf-8'))
TARGET=0x724730

# 0x6CD8CD P1 design: insert test eax,eax / jz before push 0 @0x6CD8C7
S6A=0x6CD8C7; S6BLOCK_END=0x6CD8D8  # after call 0x750E20
S6XX=S6BLOCK_END-S6A  # 0x11=17
S6BYTES=bytes([0x85,0xC0,0x74,S6XX]).hex(' ')

utmap={x['site']:x for x in UT['results']}

# ---- PATCH_MAP.tsv ----
pm=["call_site\tfunction\tbytes_before\tinsert_at\tinsert_bytes\tjump_target\tbytes_after\tpatch_class(A/B/C)\tspace_ok(Y/N)\tevidence"]
for r in CORE['sites']:
    if 'error' in r: continue
    u=utmap.get(r['site'],{})
    C=r['site']; fn=r['fn']; ib=u.get('patch_bytes','').replace(' ','').upper()
    tgt=u.get('targets',{})
    jt=f"jz:{tgt.get('jz','')};jmp:{tgt.get('jmp','')}"
    # bytes_after = original next-insn bytes (first 8) after the 5-byte call
    C_i=int(C,16)
    try:
        _na=b.read(C_i+5,8).hex(' ')
    except Exception:
        _na='(out of section)'
    pm.append("\t".join([C,fn,r['call_bytes'],C,ib,jt,_na,'A','N',
                         'EVIDENCE/core.json;EVIDENCE/UNIT_TEST.txt;EVIDENCE/BASELINE.txt']))
# 0x6CD8CD row
pm.append("\t".join(['006CD8CD','006CC390','8b 88 50 02 00 00',f'{S6A:08X}',S6BYTES,
                     f'jz:{S6BLOCK_END+4:#x}',b.read(0x6CD8D8,8).hex(' '),'A','N',
                     'EVIDENCE/core.json;EVIDENCE/DESIGN_FACTS.txt']))
open(os.path.join(CARD,'PATCH_MAP.tsv'),'w',encoding='utf-8').write("\n".join(pm)+"\n")

# ---- CANDIDATES.md ----
nA=len([r for r in CORE['sites'] if 'error' not in r])+1
retarget_sites=[x for x in UT['results'] if x.get('retarget')]
cand=[]
cand.append("# W178-PATCH 候选补丁件（静态设计，不落地）")
cand.append("")
cand.append("> 卡号 W178-PATCH｜目标 `ra2youli\\gamemd.exe` SHA-256 全值一致｜**只写本卡目录**；未改游戏目录、未注入、未写进程内存、未跑真机。")
cand.append("> 授权依据：`lead\\PENDING_DECISIONS.md` D-13（写候选件 + 离线单测获授权）与 D-34（真机常设授权，但禁区仍含写进程内存/注入/改 `ra2youli\\`）。本卡为静态卡，不调用任何真机授权。")
cand.append("")
cand.append("## 0 关键发现：调用约定决定补丁形状")
cand.append("")
cand.append("`0x724730` 序言 `mov ebp,ecx`（thiscall），首访 `0x724737 mov eax,[ebp+0x250]`；若 `ecx=0` ⇒ fault `0x250`。")
cand.append("**callee 唯一 ret = `0x7248AE ret 4`**（`EVIDENCE/core.json:callee`）——它清掉调用者压入的 1 个栈 dword 参数。")
cand.append("⇒ 任何只跳过 `call` 而不清栈的守卫会**泄漏 4 字节/次**（`BASELINE.txt` B2: 30/30 证明朴素 4 字节设计失败）。")
cand.append("")
cand.append("## P1（首选，A 级，可离线验证）：调用点内守卫式调用")
cand.append("")
cand.append("把 5 字节 `E8 rel32` **就地替换为 14 字节**：")
cand.append("```asm")
cand.append("C+0  85 C9            test ecx, ecx        ; ecx=this，最后一次写入为 [0x887368]")
cand.append("C+2  74 07            jz  C+11")
cand.append("C+4  E8 <rel32-4>     call 0x724730        ; 原调用，rel32 减 4 补偿前插 4 字节")
cand.append("C+9  EB 03            jmp C+14             ; 非 NULL 汇合")
cand.append("C+11 83 C4 04         add esp, 4           ; NULL 路径补做 ret 4 的清栈")
cand.append("C+14 <原 C+5 指令>                          ; 两条路径同 ESP 汇合")
cand.append("```")
cand.append("")
cand.append("- **适用场景**：`ecx` 在调用点即 this（`EVIDENCE/DESIGN_FACTS.txt` 30/30 `this=mem [0x887368]`），NULL 可达但希望只把\"崩溃\"降级为\"跳过该次调用\"。")
cand.append("- **插入字节/位置/跳转目标**：逐处见 `PATCH_MAP.tsv`；`jz→C+11`（add esp,4），`jmp→C+14`（汇合点）。")
cand.append("- **对指令长度/相对跳转的影响**：在原 5 字节位置就地改写，**原 C 之前的指令不动**；原 C+5 起全部后移 **+9 字节**（14−5），函数内所有跨越 C 的相对跳转须重定位。")
cand.append(f"- **空间核查（T3）**：`space_ok=N`（30/30）。目标位置现有 5 字节就是 `call` 本身，**无 ≥2 字节可覆盖 nop/int3** ⇒ 无就地填充空间；必须整函数重链（re-link）。")
cand.append(f"- **跳转冲突**：{len(retarget_sites)}/{len(CORE['sites'])} 处原本有相对跳转指向 C+5（落在 14 字节体内），须从 `C+5` 重定向到 `C+14`（+9 增量）；`BASELINE.txt` RETARGET {BL['RETARGET']['ok']}/{BL['RETARGET']['total']} 全部在 rel8/rel32 范围内。逐处清单见 `EVIDENCE/UNIT_TEST.txt`（`retarget` 字段）。")
cand.append("- **候选件之间的字节区间争用**：**0**。31 个 P1 的 `insert_at` 两两不同（30 个 `call` 地址 + `0x6CD8C7`），无两个候选件覆盖同一字节区间。唯一\"相邻\"via 同宿主多站点（如 `0x6ABD30` 6 处）不构成字节重叠，只影响重链顺序（见 `RISKS.md` G1）。")
cand.append(f"- **离线验证**：`work/unit_test.py` 对 30 处各跑 8 项检查，**{UT['passed']}/{UT['total']} PASS**（`EVIDENCE/UNIT_TEST.txt`）；基线 `work/baseline.py`（`EVIDENCE/BASELINE.txt`）显示 BNUL 0/200、B2 30/30、F1 30/30，判据有鉴别力、非 N/N 自证。")
cand.append("")
cand.append("### P1 逐处清单（26 处可达 + 4 处零静态引用；后者先按同形状给出，是否生效取决于真机入边）")
cand.append("")
cand.append("| call_site | host | 路径长 | 宿主级 | 变体 | P1 字节 | jz 目标 | 冲突跳转数 | 等级 |")
cand.append("|---|---|---|---|---|---|---|---|---|")
for r in CORE['sites']:
    if 'error' in r: continue
    u=utmap.get(r['site'],{})
    nret=len(u.get('retarget',[]))
    cand.append(f"| {r['site']} | {r['fn']} | {r['path_len']} | {r['host_grade']} | {u.get('status','?')} | {u.get('patch_bytes','')} | {u.get('targets',{}).get('jz','')} | {nret} | A |")
cand.append("")
cand.append("### P1：0x6CD8CD（非 call，直接解引用）")
cand.append("")
cand.append("```asm")
cand.append("006CD8C2  A1 E0 71 88 00     mov eax, [0x8871E0]     ; 保留")
cand.append("--- 在 006CD8C7（push 0）处插入 4 字节 ---")
cand.append("          85 C0              test eax, eax")
cand.append(f"          74 {S6XX:02X}              jz  0x{S6BLOCK_END+4:X}      ; 跳过 push/lea/deref/call")
cand.append("006CD8C7  6A 00              push 0                  ; 原")
cand.append("006CD8C9  8D 54 24 14        lea edx,[esp+0x14]      ; 原")
cand.append("006CD8CD  8B 88 50 02 00 00  mov ecx,[eax+0x250]     ; 原（NULL 时崩溃点）")
cand.append("006CD8D3  E8 ...             call 0x750E20           ; 原")
cand.append("006CD8D8  <原下一指令>                               ; 汇合")
cand.append("```")
cand.append(f"插入字节 `{S6BYTES}`；`jz` 目标 `0x{S6BLOCK_END+4:X}`（重链后）。NULL 路径跳过整块，未 push 故 ESP 平衡；`ecx` 来源在 `DESIGN_FACTS.txt`。等级 A；`space_ok=N`。")
cand.append("⚠️ `0x750E20` 的 ret 是路径相关的（`ret 4` ×3、`ret` ×2，`EVIDENCE/query_750e20.txt`）；NULL 路径整块跳过故不走它，但被跳过的副作用（edx/ecx、调用 0x750E20）须在 `RISKS.md` 评估。")
cand.append("")
cand.append("## P2（调用点替换，C 级）：代码洞桩")
cand.append("")
cand.append("把 5 字节 `call 0x724730` 换成 `E8 rel32 → cave`，cave 内 `test ecx,ecx / jz add_esp4 / call 0x724730 / ret`。")
cand.append("**需额外空间（代码洞或新增段），很可能不在授权范围**；且新增段改变 PE 布局与所有绝对寻址，风险最高 ⇒ 建议不做（C）。本卡不生成可用字节，仅在 `RISKS.md` 登记。")
cand.append("")
cand.append("## P3（上游修复，C 级）：在 NULL 写入处保证非 NULL")
cand.append("")
cand.append("`[0x887368]` 3 个写者：`0x7777B8`（存 esi=成功对象）、`0x7777C3`/`0x777803`（存 ebx，宿主入口 `xor ebx,ebx` ⇒ 写 NULL，分配失败/析构清零）。")
cand.append("把后两处改成\"保留旧非 NULL 值/回退默认对象\"可根除全部 30 处，但：写者函数 `0x7775C0` 的入边只由回调取址 `0x777C79` 支撑、语义是资源生命周期；改动影响面远大于 30 处调用点，且会掩盖真实分配失败 ⇒ **语义有风险，建议不做（C）**。")
cand.append("`[0x8871E0]` 同理（`0x52BAFA`/`0x6BEABD` 写 NULL）。")
cand.append("")
cand.append("## 证据索引")
cand.append("- `EVIDENCE/core.json`：30 站点全字段、callee ret、跳表、NULL 写者。")
cand.append("- `EVIDENCE/UNIT_TEST.txt` / `.json`：30/30 八项离线检查 + 逐处 retarget。")
cand.append("- `EVIDENCE/BASELINE.txt` / `.json`：BNUL 0/200、B1/B2/F1/U7/RETARGET 基线。")
cand.append("- `EVIDENCE/DESIGN_FACTS.txt`：逐处 push/this/nop 与 gap 边界。")
cand.append("- `work/`：全部脚本可复跑（`explore.py`→`analyze.py`→`unit_test.py`→`baseline.py`→`make_deliverables.py`）。")
open(os.path.join(CARD,'CANDIDATES.md'),'w',encoding='utf-8').write("\n".join(cand)+"\n")

# ---- RISKS.md ----
risks=[]
risks.append("# W178-PATCH 全局风险清单（T5）")
risks.append("")
risks.append("## 1 改变行为语义（C 级：崩溃 → 静默不做事）")
risks.append("")
risks.append("**全部 31 个 P1 候选**（30 处 call + `0x6CD8CD`）都把 `this==NULL` 时的 AV 崩溃改成\"跳过这次调用\"。这必然改变语义：")
risks.append("1. **30 处 call**：被跳过的 `0x724730` 是一次带栈参数的对象操作（callee `ret 4`）。跳过 = 该次操作未执行，但调用方后续代码假定它已执行 ⇒ 游戏状态可能不一致（例如某个队列/计数器未更新）。逐处：`004A8B75`、`00640427`、`00654413`、`00654469`、`006AC00B`…`006D1744`（见 `PATCH_MAP.tsv` 全表）。")
risks.append("2. **`0x6CD8CD`**：跳过块含 `call 0x750E20`（ret 路径相关）与 `edx`/`ecx` 赋值。NULL 路径下这些副作用全部消失 ⇒ 下游 `0x6CD8D8` 起的逻辑拿到未初始化的 `edx`/`ecx`。")
risks.append("3. **掩盖真实分配失败**：`[0x887368]` 的 NULL 来自 `0x7777C3`/`0x777803`（分配失败/析构后清零）。守卫只避开崩溃，不恢复对象 ⇒ 后续可能二次崩溃或静默错误。")
risks.append("")
risks.append("## 2 空间/重链风险（影响可用性）")
risks.append("")
risks.append("- **`space_ok=N`（31/31）**：无就地 nop/int3 填充，P1 把 5 字节换成 14 字节 ⇒ 原 C+5 起 +9 位移，整函数相对跳转须重链。")
risks.append(f"- **必须重定向的跳转**：{len(retarget_sites)} 处站点（{', '.join(x['site'] for x in retarget_sites)}）有原指向 C+5 的相对跳转，须改到 C+14（+9）。`BASELINE.txt` RETARGET {BL['RETARGET']['ok']}/{BL['RETARGET']['total']} 在范围内，但重链本身须复核。")
risks.append("- **可离线验证 ≠ 可部署**：`UNIT_TEST.txt` 的 30/30 PASS 只证明逻辑（栈平衡、无跳入插入体、非 NULL 路径不变），不证明字节已安全落地。本卡明确不落地。")
risks.append("")
risks.append("## 3 需成对/成组修改才生效")
risks.append("")
risks.append("- **组 G1（同宿主多站点）**：`0x6ABD30` 含 6 处（`006AC00B/006AC03E/006AC0ED/006AC140/006AC193/006AC1E6`）；`0x6D04F0` 含 4 处；`0x6D0680` 含 4 处；`0x6D1200` 含 4 处；`0x6D1660` 含 3 处。同宿主重链时须一次性处理全部站点，否则相对跳转半新半旧。")
risks.append("- **组 G2（P3 才成立）**：要根除 NULL，须同时改 `0x7777C3`+`0x777803`（`[0x887368]`）与 `0x52BAFA`+`0x6BEABD`（`[0x8871E0]`）；只改一半无意义。P3 已判 C 级不建议做。")
risks.append("- **组 G3（零静态引用 4 处）**：`006D1541/006D155C/006D15CB/006D1605` 的宿主入边未证（`core.json` `host_grade=zero-static-ref`）。即使 P1 字节正确，若这些站点运行期不可达则补丁无的放矢；若可达则需真机确认（见 `UNKNOWNS.md`）。")
risks.append("")
risks.append("## 4 授权/范围风险")
risks.append("- P2 需代码洞/新增段，**可能不在授权范围**（D-13/D-34 禁区：改 `ra2youli\\`、注入、写进程内存）⇒ C 级建议不做。")
risks.append("- 本卡未跑真机；任何\"补丁在真机是否稳定\"的结论均不在本卡范围，需 W179-x 真机卡。")
open(os.path.join(CARD,'RISKS.md'),'w',encoding='utf-8').write("\n".join(risks)+"\n")

# ---- UNKNOWNS.md ----
unk=[]
unk.append("# W178-PATCH UNKNOWNS")
unk.append("")
unk.append("1. **4 处零静态引用站点** `006D1541/006D155C/006D15CB/006D1605`：宿主函数 `0x6D14F0`/`0x6D1570`/`0x6D15F0` 的 direct call + dword 指针 + 立即数引用全 0（`core.json`）。局部 CFG 可达、NULL 态可达，但运行期入边未证。P1 字节已给，是否生效**建议真机卡 W179-x**。")
unk.append("2. **NULL 写入后引擎仍运行并再次调用站点的时序**：`[0x887368]` 由 `0x7777C3`/`0x777803` 写 NULL（分配失败/析构），写者入口 `0x7775C0` 入边仅由回调取址 `0x777C79` 支撑。W178 审计亦标此环节为 `[静态推断]`。本卡沿用，不越级。")
unk.append("3. **`0x750E20` 的 ret 路径相关**（`ret 4`×3 / `ret`×2，`EVIDENCE/query_750e20.txt`）：在 `0x6CD8CD` 的**非 NULL** 原路径上它按当前 ecx 符号选择 ret；P1 的 NULL 路径整块跳过它，故不受影响，但原路径语义完整性未在本卡穷举。")
unk.append("4. **重链后的真机稳定性**：P1 是重链候选（space_ok=N），离线单测只证逻辑。`0x6CD8CD` 跳表 case 9 路径 48 节点（`core.json:s6`），重链后该路径是否仍完整须集成期复核。")
unk.append("5. **atlas 空洞宿主定界**：`0x6D1570`/`0x6D15F0` 由 `ret`+`nop` 填充独立定界（`EVIDENCE/DESIGN_FACTS.txt` gap_verification），未用 `entry_at_or_before`。`0x6D1570` 的 ret 在 `0x6D15E3`（函数尾），本脚本扫 `gs..gs+0x20` 未捕获（记为 `ret_va=None`），但边界字节序列已逐字符落盘；归属判定仍满足区间包含。")
open(os.path.join(CARD,'UNKNOWNS.md'),'w',encoding='utf-8').write("\n".join(unk)+"\n")

# ---- DISAGREE.md ----
dis=[]
dis.append("# W178-PATCH DISAGREE / 一致性核对")
dis.append("")
dis.append("## 与 W178 / §933 的核心数字核对：**无 DISAGREE**")
dis.append("")
dis.append("| 项 | W178/§933 | 本卡独立复核 | 一致 | 证据 |")
dis.append("|---|---|---|---|---|")
dis.append("| `call 0x724730` 命中 | 30 | 30 | ✓ | `EVIDENCE/core.json:call_count`；全 `.text` skipdata 线性反汇编 |")
dis.append("| 可达 NULL 站点 | 26 | 26 | ✓ | `core.json` `reachable∧static-ref`=26；`EVIDENCE/BASELINE.txt` BNUL 0/200 证明非基线假象 |")
dis.append("| 零静态引用站点 | 4 | 4 | ✓ | `006D1541/006D155C/006D15CB/006D1605` |")
dis.append("| `ecx` 最后写入 `[0x887368]` | 30/30 | 30/30 | ✓ | `DESIGN_FACTS.txt` `this=mem [0x887368]` |")
dis.append("| 零守卫 | 0/30 | 0/30 | ✓ | `core.json` `zero_guard`=0 |")
dis.append("| `0x6CD8CD` 可达 | 是（48 节点/12 项跳表 case 9） | 是（path_len=48，跳表 12 项） | ✓ | `core.json:s6` |")
dis.append("| 崩溃点 | `EIP=0x724737` fault `0x250` | 同（`mov eax,[ebp+0x250]`, ebp=ecx=0） | ✓ | `core.json:callee` |")
dis.append("")
dis.append("## 引节号 / 文件")
dis.append("- `R14_COMMON.md` §0 表格 ②-a 行：\"`0x724730` 的 30 个无守卫调用点与 `0x6CD8CD` 仍是已知缺口\" —— 本卡数字一致；本卡在其上补候选件，不改缺口结论。")
dis.append("- `STATUS_BOARD.md` ②-a 段与「Lead 口径裁定」：W178 记 26/30 —— 一致。")
dis.append("- `W178_guards\\PROGRESS.md` §核心数字 1/2/3、`W178_guards\\_audit\\VERDICT.md` §1 —— 本卡全部独立复现。")
dis.append("- **沿用 W178 的措辞更正**：30 处是 `E8 rel32` **直接 thiscall**，非\"虚调用\"（`VERDICT.md` §2）。本卡一律写\"无守卫直接调用点\"。")
dis.append("")
dis.append("## 与 W178 的方法差异（非结论冲突）")
dis.append("- W178 做风险分级（26 `[静态推断]` + 4 `[未证]`）；本卡在其上做**补丁候选件设计**与离线单测，不重判证据等级。")
dis.append("- 本卡新增发现：callee `ret 4` 决定朴素守卫会泄漏栈参数（`BASELINE.txt` B2 30/30）；此点 W178 未涉及，非冲突。")
open(os.path.join(CARD,'DISAGREE.md'),'w',encoding='utf-8').write("\n".join(dis)+"\n")

# ---- coverage_delta.tsv (header only, may be empty) ----
open(os.path.join(CARD,'coverage_delta.tsv'),'w',encoding='utf-8').write(
    "entry(hex8)\tsubsystem(S02)\tname\tone_line_semantics\tgrade\tevidence_path\n")

# ---- PROGRESS.md (<=60 lines) ----
pr=[]
pr.append("# W178-PATCH · PROGRESS（②-a 收尾件：候选补丁，不落地）")
pr.append("")
pr.append("> 卡号 W178-PATCH｜`ra2youli\\gamemd.exe` SHA-256 全值一致｜**只写本卡目录**；未改游戏目录、未注入、未写进程内存、未跑真机。授权：D-13（候选件+离线单测）+ D-34（静态卡不调用）。")
pr.append("")
pr.append("## 结论表（分级 + 证据路径）")
pr.append("| 项 | 分级 | 结论 | 证据 |")
pr.append("|---|---|---|---|")
pr.append("| 30 处 `call 0x724730` 复核 | `[已证]` | 全 `.text` skipdata 线性反汇编得 30 命中、全为指令边界、直接 E8 thiscall | `EVIDENCE/core.json`, `EVIDENCE/EXPLORE.txt` |")
pr.append("| 26 处可达 NULL | `[静态推断]` | CFG 从宿主入口可达 + 宿主静态引用 + 全局 NULL 写者；BNUL 基线 0/200 排除基线假象 | `EVIDENCE/core.json`, `EVIDENCE/BASELINE.txt` |")
pr.append("| 4 处零静态引用 | `[未证]` | `006D1541/006D155C/006D15CB/006D1605` 宿主三通道全零，运行期入边未证 | `EVIDENCE/DESIGN_FACTS.txt` |")
pr.append(f"| P1 候选（31 处） | A（可离线验证） | `work/unit_test.py` 8 项检查 {UT['passed']}/{UT['total']} PASS；`space_ok=N`（无就地空间），重链后方可部署 | `EVIDENCE/UNIT_TEST.txt`, `EVIDENCE/BASELINE.txt` |")
pr.append("| P2 代码洞桩 | C（建议不做） | 需额外空间/新增段，可能不在授权范围 | `CANDIDATES.md` §P2, `RISKS.md` §4 |")
pr.append("| P3 上游 NULL 修复 | C（建议不做） | 改 4 处全局写者，语义影响面大且掩盖分配失败 | `CANDIDATES.md` §P3 |")
pr.append(f"| `0x6CD8CD` | A（P1）/`[静态推断]`（可达） | 无判据解引用 `[0x8871E0]+0x250`；跳表 case 9 可达 48 节点；P1 `85 C0 74 11` | `EVIDENCE/core.json:s6`, `EVIDENCE/DESIGN_FACTS.txt` |")
pr.append("")
pr.append("## 给审计员的 3 个核心数字（可独立复算）")
pr.append("**① 复核后可达 NULL 的处数 = 26（30 中）**")
pr.append("复算：跑 `python -X utf8 work\\analyze.py`；`EVIDENCE/core.json` 中 `sites[]` 过滤 `reachable==true AND host_grade=='static-ref'` 计数。基线对照：`python -X utf8 work\\baseline.py` 的 `BNUL`（200 个随机直接调用点中同判据命中 0）。")
pr.append("**② A 级候选件数 = 31（30 处 call + `0x6CD8CD`）**")
pr.append("复算：跑 `python -X utf8 work\\unit_test.py`；`EVIDENCE/UNIT_TEST.json` 的 `passed` 应为 31，`results[]` 全 `status=PASS`（30 处 call + 1 处 `0x6CD8CD`）。")
pr.append("**③ 就地空间不足的处数 = 31（全部）**")
pr.append("复算：`EVIDENCE/CalleeAndSpace.txt` 的 `nop/int3 runs` 在各 call 点 `[]`；`PATCH_MAP.tsv` `space_ok` 列全 N。P1 需 14 字节替换 5 字节，无填充可覆盖 ⇒ 必须重链。")
pr.append("")
pr.append("## 复跑命令（全部只读目标、只写本卡目录）")
pr.append("```bash")
pr.append("python -X utf8 lead\\next_re_20261117_r14\\W178_PATCH\\work\\explore.py")
pr.append("python -X utf8 lead\\next_re_20261117_r14\\W178_PATCH\\work\\analyze.py")
pr.append("python -X utf8 lead\\next_re_20261117_r14\\W178_PATCH\\work\\callee_space.py")
pr.append("python -X utf8 lead\\next_re_20261117_r14\\W178_PATCH\\work\\unit_test.py")
pr.append("python -X utf8 lead\\next_re_20261117_r14\\W178_PATCH\\work\\baseline.py")
pr.append("python -X utf8 lead\\next_re_20261117_r14\\W178_PATCH\\work\\make_deliverables.py")
pr.append("```")
pr.append("")
pr.append("## 交付文件")
pr.append("`PROGRESS.md` / `CANDIDATES.md` / `PATCH_MAP.tsv` / `RISKS.md` / `UNKNOWNS.md` / `DISAGREE.md` / `coverage_delta.tsv`（表头） / `EVIDENCE\\`（不截断） / `work\\`（可复跑）。")
open(os.path.join(CARD,'PROGRESS.md'),'w',encoding='utf-8').write("\n".join(pr)+"\n")
print("deliverables written; PROGRESS lines=",len(pr))
