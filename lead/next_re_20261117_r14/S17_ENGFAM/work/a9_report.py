# a-S17-ENGFAM audit, script a9: regenerate verdict.tsv (fixed offsets) + emit VERDICT.md + SUMMARY.md
import pefile, capstone, struct, os, hashlib
from capstone import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM"
IB = 0x400000
pe = pefile.PE(EXE, fast_load=True)
d = bytes(pe.__data__)
def va2off(va): return pe.get_offset_from_rva(va - IB)
def read(va, n): return d[va2off(va):va2off(va)+n]

TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
md = capstone.Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True

ROWS = [
 (1,0x0067FDF0,0x0067DF0F,0xA83E30,0x004E6E7D,0x7E9FA4,"FactoryClass"),
 (2,0x0067FE70,0x0067DF29,0xA8EB28,0x004E767D,0x7EA3A4,"VoxelAnimTypeClass"),
 (3,0x0067FEF0,0x0067DF43,0x887388,0x0040EE5D,0x7E1E2C,"VoxelAnimClass"),
 (4,0x0067FF70,0x0067DF5D,0x8874C0,0x0040F4AD,0x7E1E84,"WarheadTypeClass"),
 (5,0x0067FFF0,0x0067DF77,0x887568,0x0040FB4D,0x7E1ED4,"WeaponTypeClass"),
 (6,0x00680070,0x0067DF91,0xA83D98,0x004E777D,0x7EA424,"ParticleTypeClass"),
 (7,0x006800F0,0x0067DFAB,0xA83DC8,0x004E697D,0x7E9D64,"ParticleClass"),
 (8,0x00680170,0x0067DFC5,0xA83D68,0x004E77FD,0x7EA464,"ParticleSystemTypeClass"),
 (9,0x006801F0,0x0067DFDF,0xA80208,0x004E66FD,0x7E9C64,"ParticleSystemClass"),
 (10,0x00680270,0x0067DFF9,0xA83C80,0x004E75FD,0x7EA364,"BulletTypeClass"),
 (11,0x006802F0,0x0067E013,0xA8ED40,0x004E687D,0x7E4678,"BulletClass"),
 (12,0x00680370,0x0067E02D,0xB72608,0x007635AD,0x7F6E04,"WaypointPathClass"),
 (13,0x006803F0,0x0067E047,0xA8EC18,0x004E727D,0x7EA1A4,"SmudgeTypeClass"),
 (14,0x00680470,0x0067E061,0xA83D80,0x004E71FD,0x7EA164,"OverlayTypeClass"),
 (15,0x006804F0,0x0067E07B,0xABCA10,0x0055465D,0x7ECF7C,"LightSourceClass"),
 (16,0x00680570,0x0067E095,0x8B4190,0x004E667D,0x7E9C24,"BuildingLightClass"),
 (18,0x00680670,0x0067E0C9,0xB0F4E8,0x0072165D,0x7F56BC,"TiberiumClass"),
 (19,0x006806F0,0x0067E0E3,0x8A3870,0x004C522D,0x7E873C,"EMPulseClass"),
 (20,0x00680770,0x0067E0FD,0xA8E330,0x004E787D,0x7EA4A4,"SuperWeaponTypeClass"),
 (21,0x006807F0,0x0067E117,0xA83CB8,0x004E78FD,0x7EA4E4,"SuperClass"),
 (22,0x00680870,0x0067E1E7,0xA8E318,0x004E72FD,0x7EA1E4,"TerrainTypeClass"),
 (23,0x006808F0,0x0067E201,0xA8E988,0x004E6A7D,0x7E9DE4,"TerrainClass"),
 (24,0x00680970,0x0067E21B,0x8B3D10,0x004D076D,0x7E44F4,"FoggedObjectClass"),
 (25,0x006809F0,0x0067E235,0x88A0F0,0x004208FD,0x7E3238,"AlphaShapeClass"),
 (26,0x00680A70,0x0067E24F,0xA8EC38,0x004E67FD,0x7E9CE4,"WaveClass"),
 (27,0x00680AF0,0x0067E28F,0x89E0F0,0x0047176D,0x7E4AD4,"CaptureManagerClass"),
 (28,0x00680B70,0x0067E2A9,0x8A0208,0x004A6C8D,0x7E5EDC,"DiskLaserClass"),
 (29,0x00680BF0,0x0067E2C3,0xAC4910,0x006291AD,0x7EF824,"ParasiteClass"),
 (30,0x00680C70,0x0067E2DD,0xB0EC60,0x0071A3ED,0x7F5114,"TemporalClass"),
 (31,0x00680CF0,0x0067E2F7,0x889FB8,0x0041D29D,0x7E293C,"AirstrikeClass"),
 (32,0x00680D70,0x0067E311,0xB0B880,0x006B6C2D,0x7F35E4,"SpawnManagerClass"),
 (33,0x00680DF0,0x0067E32B,0xB0B5F0,0x006AF13D,0x7F315C,"SlaveManagerClass"),
 (34,0x00680E70,0x0067E390,0x89C668,0x0043856D,0x7E17CC,"BombClass"),
 (35,0x00680EF0,0x0067E3AA,0xB04BD0,0x0065B17D,0x7F07A4,"RadSiteClass"),
]

L = []
A = L.append
A("# a-S17-ENGFAM — 审计 S17 英文措辞族 34 行的四环实质（VERDICT）")
A("")
A("审计人：agent-128（a-S17-ENGFAM 卡）。全部证据为本审计自有反汇编产出；")
A("`S17-F1/EVIDENCE/analysis_deep2.txt` 仅作线索（读过，其结论未作为任何 PASS 依据）。")
A("")
A("## 0. 自校验与方法")
A("")
A("- 目标二进制 SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，与卡面期望一致。")
A("- pefile 实测段表：ImageBase 0x400000；`.text` VirtualSize=0x3DF38D → `[0x401000,0x7E038D)`，与卡面一致；34 个入口全部落在该区间内（另核：`.data` raw 背书区 `[0x812000,0x87E000)`，`0x87E000` 以上为 .bss 零初始化区——35 个向量实参全部位于 `0x87E000` 以上，真 .bss）。")
A("- 工具链：Python 3.12.10 + capstone 5.0.7（**skipdata=True**）+ pefile 2024.8.26，无 venv、无安装。")
A("- 自有脚本（本目录 `work/`）：a1_bodies / a2_xrefs / a3_rtti / a4_core / a5_alive / a6_root / a7_ctor / a8_final / a9_report。自有证据文件（`EVIDENCE/`）：bodies.txt（34+1 槽全量逐条反汇编）、xrefs.txt、rtti.txt、chain.txt、alive.txt、root.txt、ctors.txt、rows_fragment.md。")
A("- 34 行清单过滤命令（照实执行，得 34 行，全部 grade `[已证]`、全部 evidence_path 指向 analysis_main.txt+analysis_deep2.txt）：")
A("")
A("  ```powershell")
A('  Select-String -Path "D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261117_r14\\COVERAGE\\coverage.tsv" -Pattern \'unproven|unverified|not proven\' | Where-Object { $_.Line -match "`tS17`t" }')
A("  ```")
A("")
A("## 1. 模板体（35 个槽逐字节同体，本审计独立 md5/逐字节 diff 复核）")
A("")
A("35 个物理实例（01–35 含 #17 空缺槽 0x6805F0）的 127 字节体两两 diff = **0 字节**，统一 md5(127B)=`9f6770a9cd27b9fa49558adf28c92f10`（a1 自算，非引自任何普查文件）。体长 0x7F、+0x7E=`C3`、+0x7F=填充 `90`、槽距 0x80。以下为体逐字节语义注释（以 #1 入口 0x67FDF0 为基准，偏移 +xx 对全部实例同构；字节见 `EVIDENCE/bodies.txt`）：")
A("")
A("```")
A("+00 83 EC 08              sub esp,8 ; push ebx/esi/edi          ; 序言（栈平衡自洽）")
A("+06 8B FA / 8B D9         mov edi,edx ; mov ebx,ecx             ; edi=arg2 向量(.bss) ebx=arg1 IStream*")
A("+0A 6A 00                 push 0                                ; pcbWritten=NULL")
A("+0C 8B 47 10              mov eax,[edi+0x10]                    ; vec->Count（DynamicVectorClass 布局 +0x10）")
A("+0F 8D 54 24 14           lea edx,[esp+0x14]                    ; &局部Count槽")
A("+13 8B 0B                 mov ecx,[ebx]                         ; IStream vftable")
A("+15..+19 push 4 / push edx / push ebx / mov [esp+0x20],eax ; 装参：this=ebx, pv=&Count, cb=4")
A("+1D FF 51 10              call [ecx+0x10]                       ; IStream::Write(&Count,4,NULL)  ← 栈外写")
A("+20 85 C0 / +22 7C 54     test eax,eax ; jl 失败出口            ; HRESULT 可证伪传播")
A("+24 8B 44 24 10           mov eax,[esp+0x10]                    ; 重读 Count")
A("+28 33 F6 / +2A 85 C0 / +2C 7E 48   xor esi,esi ; test ; jle +0x76   ; i=0；Count<=0 跳过（边界）")
A("+2E 8B 47 04              mov eax,[edi+4]                       ; vec->Items（数组 +4）")
A("+31 C7 44 24 0C 00000000  mov [esp+0xC],0 / +39 lea edx         ; &out")
A("+3D 8B 04 B0              mov eax,[eax+esi*4]                   ; eax=Items[i]（元素）")
A("+40..+47 push edx / push 0x7F7C80 / push eax / mov ecx,[eax]")
A("+49 FF 11                 call [ecx]                            ; 元素 QueryInterface(IID)")
A("                                                                ; IID@0x7F7C80={00000109-0000-0000-C000-000000000046}")
A("                                                                ;   = IID_IPersistStream（a2 自读字节）")
A("+4B 85 C0 / +4D 7C 29     test eax,eax ; jl 失败")
A("+4F..+54  mov eax,[esp+0xC] ; push ebx ; push eax")
A("+55 FF 15 F4 15 7E 00     call [0x7E15F4]                       ; IAT→ole32!OleSaveToStream(pPersist,pStm)")
A("                                                                ;   （a2 自解 IAT，非引自普查）")
A("+5B 85 C0 / +5D 7C 19     test eax,eax ; jl 失败")
A("+5F..+66  mov eax,[esp+0xC] ; push eax ; mov ecx,[eax] ; call [ecx+8]   ; Release(out)")
A("+69 85 C0 / +6B 7C 0B     test eax,eax ; jl 失败")
A("+6D 8B 44 24 10 / +71 46 / +72 3B F0 / +74 7C B8  ; 重读 Count；inc i；cmp；**jl +0x2E 回边（界：i<Count）**")
A("+76 33 C0                 xor eax,eax                           ; S_OK")
A("+78 5F 5E 5B 83 C4 08 C3  pop×3 ; add esp,8 ; ret               ; 体止于 +0x7E")
A("```")
A("")
A("## 2. 逐行五点复核（34 节）")
A("")
A("共同依据（对每行均成立，行专属地址在下表/各节中）：")
A("")
A("- **① 入口**：地址在 `.text` 内；序言 `sub esp,8; push ebx; push esi; push edi` 与尾声 `pop edi/esi/ebx; add esp,8; ret` 平衡；体 0x7F 止于 `C3`，+0x7F 填充 `90`，槽距 0x80 无越界、无重叠。")
A("- **② 类身份**：本函数族为自由函数（自有扫描：0x67FDF0–0x680F70 区间 0 个虚表条目），函数自身无 RTTI/虚表归属（D-41 形态，物理查不到）；但其服务对象（edx 传入的 .bss 向量）经**构造链**定死：每向量存在 `mov dword ptr [vec], vt` 构造写入，vt 的 RTTI TD 名给出精确类 `DynamicVectorClass<PAV<元素>Class>`（a7 全 35 个向量逐个定死并逐字节复核写入）。**故语义尾缀「class name unproven (arg .bss obj)」属『当时没查』而非『查不到』**——本审计已把 34 行（含 #17 槽）的向量类与元素类全部定死（见下）。")
A("- **③ 整体合同（只认 ③b）**：体即 **③b④ 完整循环 I/O 带边界检查**：`Write(&Count,4,NULL)` → `i=0..Count-1`（`jl` 有界回边）→ 元素 `QI(IID_IPersistStream)` → `OleSaveToStream`（栈外写：写入流对象）→ `Release`；且 **③b② 可证伪返回约定**同时成立：四处 `test/jl` 失败即携 HRESULT 提前返回，成功路径 `xor eax,eax`（S_OK）；上层 Save_Core `test/jge` 再映射为 bool。**写为栈外写**（IStream::Write 经 COM 虚表派发 + ole32!IAT 导入，写对象是流），非「写栈/累加槽/寄存器推进」。与已知陷阱 `0045A640` 类（循环内只 push、非栈写 0）**形态相反**，不适用该陷阱。")
A("- **④ 使用见证**：每行恰有 **1 个 E8 直接调用点**（全部位于 Save_Core `0x67D300`，jmp=0、data 引用=0——a2 有界重扫修正后确认 a2 初版对 `0x88F03C/0x88F19C` 的命中系越界映射伪迹，已作废）；该调用链为**活链**：从 PE 入口 `0x7CD80F` 正向可达性扫描（6366 函数）**同时到达**全部 3 个上游根（0x4C6CB0/0x559C20/0x55D360）；反向闭包 1144 函数中含 **81 个 RTTI 虚表成员**（FootClass/BuildingClass/MouseClass/MapClass/AnimClass 等）。非 direct-only 死链。")
A("- **⑤ 家族**：见 §3——模板成立；`Save_VectorBlock_NN` 为 slotN 式名字，按卡面不构成判行不成立的理由。")
A("")
A("行专属数据表（每行各自的入口/调用点/向量/构造写入/RTTI 类；md5 同上）：")
A("")
A("| # | entry | call site（E8，site+5+rel32==entry） | edx=.bss 向量 | 构造写入 | RTTI 类（TD 名） | 元素类 |")
A("|---|-------|--------------------------------------|----------------|----------|------------------|--------|")
for n, va, site, vec, csite, vt, el in ROWS:
    rel = struct.unpack("<i", read(site+1, 4))[0]
    tgt = site + 5 + rel
    assert tgt == va
    e8 = read(site, 5).hex(" ").upper()
    td = ".?AV?$DynamicVectorClass@PAV%s@@@@" % el
    A("| %02d | 0x%08X | 0x%08X `%s`→0x%08X ✓ | 0x%08X | 0x%08X | `%s` | %s |" % (
        n, va, site, e8, tgt, vec, csite, td, el))
A("")
A("### 2.1 ≥3 个不同实例的独立字节核验（卡面硬要求；bodies.txt 另含全部 34+1 槽逐条清单）")
A("")
for n, va, site, vec, csite, vt, el in [(1,0x0067FDF0,0x0067DF0F,0xA83E30,0x004E6E7D,0x7E9FA4,"FactoryClass"),
                                        (16,0x00680570,0x0067E095,0x8B4190,0x004E667D,0x7E9C24,"BuildingLightClass"),
                                        (35,0x00680EF0,0x0067E3AA,0xB04BD0,0x0065B17D,0x7F07A4,"RadSiteClass")]:
    e16 = read(va,16).hex(" ").upper()
    tail = read(va+0x70, 15).hex(" ").upper()
    A("- **#%02d @0x%08X**：入口 16 字节 `%s`；尾段 +0x70..+0x7E `%s`（`33 C0 5F 5E 5B 83 C4 08 C3` 止于 +0x7E）；md5(127B)=`9f6770a9…`；调用点 0x%08X `E8`→本入口 ✓；edx=0x%08X，构造写入 0x%08X `mov [vec],0x%08X` → `DynamicVectorClass<PAV%s>`。三处派发（+0x1D Write / +0x49 QI / +0x55 OleSaveToStream）字节在 bodies.txt 该槽清单内逐条在案。" % (
        n, va, e16, tail, site, vec, csite, vt, el))
A("- **（加验）#17 空缺槽 @0x6805F0**：同体同 md5（diff vs #1 = 0 字节）；调用点 0x67E0AF `E8`→0x6805F0 ✓；edx=0x8B4120，构造写入 0x004E6F7D `mov [0x8B4120],0x7EA024` → `DynamicVectorClass<PAVSideClass>`——即「Sides」向量；coverage 缺 #17 号是把该槽命名/归档分离所致，物理上模板实为 35 连号。")
A("")
A("## 3. 整族结论（模板是否成立、成立范围）")
A("")
A("**模板成立。** 成立范围 = **35 个物理实例**（0x67FDF0 起、槽距 0x80、至 0x680EF0 止，含被 coverage 排除在名族外的 #17 槽 0x6805F0）。模板形态：**「写 4 字节 Count → 有界循环（i<Count）逐元素 { QI(IID_IPersistStream) → OleSaveToStream → Release } → HRESULT 可证伪返回」**，实例间**唯一差异是 Save_Core 传入的 edx（各自独立的 .bss 向量，35 个互不相同，已逐个用构造写入定死类）**。因此「模板成立可替代逐行成立」的适用方式是：逐行 PASS 的依据 = 同体字节核验（每行自己的入口在 bodies.txt 有独立清单）+ 每行自己的调用点/向量/构造写入核验（上表），而不是「同族所以都成立」一句带过。")
A("")
A("## 4. 已知陷阱对照")
A("")
A("- `0045A640` 类（循环内只 push 写栈、非栈写 0）：**不适用**——本体循环内有两个栈外写派发（IStream::Write、OleSaveToStream），非栈写 ≥2。")
A("- 多路进同一 call 仅参数不同（不计细则#1）：**未引用细则#1**——③b 走 ④（完整循环 I/O）+②（可证伪返回），不走跳表/闸道路径。")
A("- slotN 式名字：`Save_VectorBlock_NN` 属之；按卡面记为 `named_pct_S(R14)` 满足、不构成 FAIL 理由。")
A("")
A("## 5. 逐行判定")
A("")
for n, va, site, vec, csite, vt, el in ROWS:
    A("### Save_VectorBlock_%02d — 0x%08X — **PASS**" % (n, va))
    A("")
    A("- ① 入口：0x%08X ∈ .text ✓；体 0x7F 止 C3、+0x7F=90、槽界自洽 ✓" % va)
    A("- ② 类身份：函数自身无虚表（物理）；服务对象定死——edx=0x%08X，构造写入 0x%08X：`mov dword ptr [0x%08X],0x%08X` → RTTI `%s`，元素 %s（原语义「class name unproven」= 当时没查，现已查实）" % (vec, csite, vec, vt, ".?AV?$DynamicVectorClass@PAV%s@@@@" % el, el))
    A("- ③ 合同（③b）：③b④ 成立（Write(&Count,4,NULL)@+0x1D → 有界循环 jl@+0x74 → QI(IID_IPersistStream)@+0x49 → ole32!OleSaveToStream@+0x55（栈外写）→ Release@+0x66）；③b② 同时成立（4 处 test/jl HRESULT 可证伪传播，成功 S_OK）")
    A("- ④ 见证：唯一调用点 0x%08X（E8→0x%08X ✓，jmp/data 引用 0）；调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）+ 反向闭包含 81 个 RTTI 虚表成员 → 真实调用者成立" % (site, va))
    A("- 判定：**PASS**（四环齐；③ 只计 ③b，成立）")
    A("")
A("## 6. 统计")
A("")
A("- 34/34 PASS，0 FAIL。无一行属「措辞掩盖了实质」——措辞是保守尾缀，实质（③b④ 循环 I/O）在字节里真实存在；尾缀所声明的「class name unproven」经本审计为**当时没查**且现已查实。")
A("- 对 S17 计数的影响见 `SUMMARY.md`。")
A("")

with open(os.path.join(BASE, "VERDICT.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(L))

# verdict.tsv (fixed offsets)
with open(os.path.join(BASE, "verdict.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("entry\tverdict\thas_ring2\thas_ring3b\thas_ring4\treason\n")
    for n, va, site, vec, csite, vt, el in ROWS:
        reason = ("③b④ loop-I/O own-disasm: IStream::Write(&Count,4,NULL)@+0x1D; QI(IID_IPersistStream@0x7F7C80)@+0x49; "
                  "ole32!OleSaveToStream via IAT[0x7E15F4]@+0x55 (non-stack write); Release@+0x66; bounded loop jl@+0x74; "
                  "HRESULT falsifiable@+0x22/+0x4D/+0x5D/+0x6B; "
                  "ring2 ctor 0x%08X mov [0x%08X],0x%08X = DynamicVectorClass<PAV%s>; "
                  "ring4 sole caller 0x67D300 site 0x%08X, chain EP-reachable(0x7CD80F->3 roots), closure 81 vt members") % (
                  csite, vec, vt, el, site)
        f.write("0x%08X\tPASS\tyes\tyes\tyes\t%s\n" % (va, reason))

S = []
S.append("# a-S17-ENGFAM — SUMMARY")
S.append("")
S.append("**34 行中实质 PASS 34 行 / FAIL 0 行**（verdict.tsv 同步；无一行 FAIL，无一行属「措辞掩盖了实质」）。模板成立，范围 = 35 个物理实例（01–35 连号，含被名族排除的 #17 槽 0x6805F0 = `DynamicVectorClass<PAVSideClass>` 的「Sides」块）；实例间唯一差异是 Save_Core(0x67D300) 传入的 edx .bss 向量，35 个向量已逐个用构造写入 + RTTI TD 名定死元素类（FactoryClass…RadSiteClass）——语义尾缀「class name unproven (arg .bss obj)」属**当时没查**，现已查实。③ 按 ③b④（完整循环 I/O：Write(&Count,4,NULL) → 有界循环 QI(IID_IPersistStream)→OleSaveToStream→Release，栈外写）+ ③b②（HRESULT 可证伪返回）成立；④ 的调用链自 PE 入口 0x7CD80F 正向可达（3 根全达）且反向闭包含 81 个 RTTI 虚表成员，非 direct-only 死链。**计数：若按读法 Y 全剔，S17 为 21；若按实质复核结果，S17 为 21 + 34 = 55**（即原有 proved_strict=55 全数获得实质背书）。")
S.append("")
with open(os.path.join(BASE, "SUMMARY.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(S))

print("wrote VERDICT.md / SUMMARY.md / verdict.tsv")
