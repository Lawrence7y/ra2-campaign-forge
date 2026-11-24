"""Generate SEMFIX_SLOTS/coverage_delta.tsv (36 rows).

- name copied verbatim from coverage.tsv (never renamed)
- grade = [已证] for all 36 (each has a byte-evidenced ③b tier in a prior audit)
- only the first '（槽语义未证...）' span is replaced by the ③b contract + anchor;
  the leading class/slot description and any trailing audit note are preserved.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

COVERAGE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_SLOTS\coverage_delta.tsv"

# entry -> (③b contract sentence WITH anchor, evidence_path note)
CONTRACT = {
"0045A680": ("③b④ 按目标容量整体重建迷雾对象向量：6 道守卫校验外部缓冲/新分配/旧数组后逐项深拷贝元素并回写容量标志〔锚 +0x54 mov edx,[edx+eax*4-4] / +0x58 mov [edi+eax*4-4],edx / +0x5C jl 回边〕", "S08_KPROVED2/_audit/VERDICT.md#18"),
"0045A730": ("③b②+④ 在迷雾对象向量中线性查找目标指针、按命中返回下标或 -1 哨兵〔锚 +0x13 cmp [ecx],esi / +0x1D jl 回边 / +0x1F or eax,0xffffffff〕", "S08_KPROVED2/_audit/VERDICT.md#19"),
"004A9840": ("③b② 按传入单元指针与标志三路分派、经 0x6DA230 返回的 -1 哨兵换算成败布尔〔锚 +0x26 call 0x6DA230 / +0x2D cmp eax,-1 / +0x30 setne dl〕", "S09_KPROVED3/_audit/VERDICT.md#19"),
"004A9DD0": ("③b④ 对最多 8 个候选格双层有界循环比对坐标与状态标志、命中后分派到对应 tab 处理并写回 [esi+0x121]〔锚 +0x1C8 cmp edi,8 / +0x222 cmp eax,8 / +0x84 call [edx+0xc]〕", "S09_KPROVED3/_audit/VERDICT.md#20"),
"004AA050": ("③b④ 同 slot38 双层 8 项循环骨架、比对坐标/标志后按状态分派并写回 [esi+0x120]〔锚 +0x1B4 cmp edi,8 / +0x207 cmp eax,8 / +0x43 cmp [esi+0x120],al〕", "S09_KPROVED3/_audit/VERDICT.md#21"),
"004AAD30": ("③b①细则#1 按 7 个状态标志选择 7 个互异 helper 之一做取消/复位、各支路互斥收尾后统一经 [vt+0x48] 刷新〔锚 +0xC test [esi+0x11a4],eax / +0x60 call 0x4AC8C0 / +0x4A call [edx+0x48]〕", "S09_KPROVED3/_audit/VERDICT.md#22"),
"004AAE90": ("③b① 按操作码经 4 张界跳表分派到各输入处理器、处理完统一经虚调用收尾〔锚 +0x12B jmp [ecx*4+0x4AB79C] / +0x216 jmp [edx*4+0x4AB7B8] / +0x4EB jmp [ecx*4+0x4AB7D0]〕", "S09_KPROVED/_audit/VERDICT.md#17"),
"004ACE70": ("③b④ 遍历可用 tab/侧栏候选、对每个经 RNG 取值写回品质字段并逐项推进直到耗尽〔锚 +0x135 call 0x65C7E0 / +0x14C mov [esi+0x38],eax / +0x166 jne 回边〕", "S09_KPROVED/_audit/VERDICT.md#23"),
"004D24A0": ("③b④ 按 0x10 步长逐单元遍历迷雾可见性数组、对每个单元调用虚方法并在任一负返回时整批中止〔锚 +0x4F call [ecx+0x10] / +0x5B add edi,0x10 / +0x60 jl 回边〕", "S08_KPROVED2/_audit/VERDICT.md#20"),
"004D2510": ("③b④ 跨多来源枚举迷雾单元、逐段虚调用汇总可见性并对负返回提前退出〔锚 +0x84 call [edx+0xc] / +0x14F jl 回边 / +0x207 jl 回边〕", "S08_KPROVED2/_audit/VERDICT.md#21"),
"004D27D0": ("③b② 取全局 16 字节可见性配置到输出指针：入参为空返回 E_POINTER(0x80004003)、否则逐字拷贝并返回成功码〔锚 +0x8 mov eax,0x80004003 / +0x10 mov [eax],ecx / +0x33 xor eax,eax / +0x35 ret 8〕", "S08_KPROVED2/_audit/VERDICT.md#22"),
"004D2810": ("③b③ 把对象 14 个迷雾相关成员一次性登记到传入上下文、14 次互斥布局断言式调用覆盖 [esi+0x24..0x6C]〔锚 +0x14/+0x1F/…/+0xA3 call 0x4A1D50 ×14 / +0xAA ret 4〕", "S08_KPROVED2/_audit/VERDICT.md#25"),
"004D7170": ("③b④ 按 8 项上限循环扫描相邻格、逐项虚调用判定后递增 [eax+0x122] 计数推进、最后调用可达性虚方法〔锚 +0x12A mov dl,[eax+0x122] / +0x136 mov [eax+0x122],dl / +0x13C jl〕", "S10_KPROVED2/_audit/VERDICT.md#17"),
"004D74E0": ("③b① 按 0x46 界跳表把单位 Mission 事件分派到 13 条处理路径之一〔锚 +0x44 cmp eax,0x46 / +0x47 ja / +0x5C jmp [ecx*4+0x4D7CD0]〕", "S10_KPROVED2/_audit/VERDICT.md#15"),
"004D7D50": ("③b① 按 0x3e 界跳表把单位输入/命令分派到 11 条处理路径之一〔锚 +0x7F cmp eax,0x3e / +0x82 ja / +0x90 jmp [ecx*4+0x4D8244]〕", "S10_KPROVED2/_audit/VERDICT.md#16"),
"004D9960": ("③b④ 对单位前向/后向引用数组做有界搜索与左移整理、按多道状态闸校验目标合法性〔锚 +0x213 cmp eax,edx / +0x227 jl 回边 / +0x233 cmp ecx,eax / +0x235 jl 回边〕", "S10_KPROVED2/_audit/VERDICT.md#20"),
"004DB3C0": ("③b④ 遍历单位列表、逐项做可见性/占据校验后把合法项写入 count/Items 缓冲〔锚 +0x9B call [esi+0x4c] / +0xDA cmp eax,ecx / +0xE0 jl 回边 / +0x18E jl 回边〕", "S10_KPROVED2/_audit/VERDICT.md#19"),
"004DB690": ("③b② 按 E_NOINTERFACE(0x80004002) 可证伪错误码与负返回闸校验单位可达性：命中错误码即跳过候选、合法路径经 [vt+8] 收尾〔锚 +0x11A cmp edi,0x80004002 / +0x120 je / +0xF3 call [ecx+8]〕", "S10_KPROVED2/_audit/VERDICT.md#22"),
"004DF040": ("③b④ 按 [vt+0x52c] 评分遍历候选选最优：以栈累加槽 [esp+0x10] 记 best、-1 为无效哨兵、[eax+0x3d3] 标志过滤并按边界推进〔锚 +0x40 call [eax+0x52c] / +0x5A cmp edx,-1 / +0x6B mov [esp+0x10],ecx / +0x73 jl〕", "S10_KPROVED2/_audit/VERDICT.md#21"),
"004E2690": ("③b①细则#1 把 gauge 值域按字节/字两种字形源之一绘制到裁剪矩形内、必要时上拉刷新显示〔锚 +0xC0 cmp [eax+4],ebx / +0xCD mov bl,[eax+ecx] / +0xDC mov ax,[ebx+ecx*2] / +0x166 call [edx+0x14]〕", "S09_KPROVED2/_audit/VERDICT.md#27"),
"00552490": ("③b④ 按 4 字节头长校验逐块从 LCW 流读入、解压并写入输出缓冲、流尽或短读即止〔锚 +0x8C test ebx,ebx / +0x94 cmp [esi+0xc],1 / +0x13F jg 回边〕", "S03_C4/_audit/VERDICT.md#21"),
"00557730": ("③b④ 按下标从 ListClass 移除一项：计数减一并左移后续元素覆盖空位、再把两个选中索引夹回合法范围〔锚 +0x1C jge 越界闸 / +0x25 mov [ecx+eax*4-4],edx / +0x2E jl / +0x77 jge 夹取〕", "S09_KPROVED2/_audit/VERDICT.md#29"),
"0055C7C0": ("③b④ 按 4 字节头长校验逐块从 LZO 流读入、解压并写入输出缓冲、真回边推进且短读即止〔锚 +0xAA cmp eax,4 / +0x18E test eax,eax / +0x190 jg 回边至 +0x34〕", "S03_C5/_audit/VERDICT.md#20"),
"005BDF70": ("③b④ 遍历鼠标持有对象数组、逐项读标志→虚调用→释放(0x7C8B3D)→清指针→推进直到数组尾〔锚 +0xDD 循环头 / +0xF0 call 0x7C8B3D / +0x102 jne 回边〕", "S09_KPROVED/_audit/VERDICT.md#18"),
"00631CC0": ("③b①细则#1 对称解除旧 pipe 与 straw 的双向绑定并把 straw 重新绑定到新 pipe：解绑走 vt+0xC、对旧 straw 发 vt+4 虚通知、再双向写回指针〔锚 +0xB je 幂等闸 / +0x1C call [vt+0xC] / +0x39 call [vt+4] / +0x43 mov [esi+8],edi〕", "S03_C4/_audit/VERDICT.md#23"),
"0063FB20": ("③b④ 按 4 段计数分段循环绘制电力条文本、每段调用 0x4AED70 后推进 3 字节并受边界检查约束〔锚 +0xFB call 0x4AED70 / +0x100 add esi,3 / +0x104 jne 回边〕", "S09_KPROVED2/_audit/VERDICT.md#25"),
"0063FEA0": ("③b② 按全局开关与 -1 字段哨兵决定电力条状态：两处 cmp eax,-1 跳过无效取项、再经属性比较选择显示路径〔锚 +0x37 cmp eax,-1 / +0x1A0 cmp eax,-1〕", "S09_KPROVED/_audit/VERDICT.md#21"),
"0065CAC0": ("③b② 若 RawFile 句柄与打开标志均有效则释放句柄并清两个状态字段、按布尔入参返回结果〔锚 +0x7 test eax,eax / +0xE test cl,cl / +0x13 call 0x7C93E8 / +0x1B mov [esi+0x18],0 / +0x2A test edi,edi〕", "S03_C4/_audit/VERDICT.md#19"),
"0065CB50": ("③b①+② 按 mode 1/2/3 三套互斥实参打开底层文件、句柄无效时以错误码 2 返回、否则经虚调用完成打开并归零结果〔锚 +0xD jne 错误路径 / +0x13 push 2 / +0x17 call [edx+0x40] / +0x1A xor eax,eax〕", "S03_C5/_audit/VERDICT.md#22"),
"0065CCE0": ("③b④ 若文件未打开则以 read 模式调用 Open、失败返回负错误码、成功返回零，含夹紧与 abort 的完整 I/O 循环〔锚 +0x13 call [eax+0x18] / +0x20 call [edx+0x1c] / +0xC4→+0x68 回边〕", "S03_C5/_audit/VERDICT.md#24"),
"0065D150": ("③b② 把 CD 文件回绕到起点：先经 seek-to-end 校验，FileSize=-1 哨兵或失败返 0、否则 seek 到起点并返 1〔锚 +0xE call [vptr+0x1c] arg2 / +0x15 cmp [esi+0x10],-1 / +0x2D mov eax,1 / +0x34 xor eax,eax〕", "S03_C4/_audit/VERDICT.md#24"),
"006A5310": ("③b④ 遍历侧栏按钮数组、对每个候选施加 4 道标志过滤后按类型分派选中/重排〔锚 +0x293..+0x2C5 循环 / +0x29E cmp [ebp+0x1a6],1 / +0x2A7 cmp [0xac1198] / +0x2AF cmp [eax+0x1ec],0〕", "S09_KPROVED/_audit/VERDICT.md#19"),
"006A5840": ("③b④ 遍历侧栏/工具条单元并对每个执行固定的取色/布局调用序列〔锚 +0x146 cmp esi,0xB07DC8 / +0x14C jl 回边 / 15× call 0x4A38D0〕", "S09_KPROVED2/_audit/VERDICT.md#23"),
"006A7780": ("③b④ 按命令 ID 与 0x3c 步长循环处理侧栏输入、命中路径调用对应处理器并返回结果〔锚 +0x1DF cmp edi,0x3c / +0x206 jl / +0x121 cmp eax,0x8065 / +0x184 cmp eax,0x80cb〕", "S09_KPROVED/_audit/VERDICT.md#22"),
"006C9890": ("③b①细则#1 对称解除旧 pipe 与 straw 的双向绑定并把 straw 绑定到新 pipe：5 道互斥闸覆盖幂等/解绑/清回指/双向写四类动作〔锚 +0xB je 幂等闸 / +0x1C call [vt+4] / +0x2D mov [eax+8],0 / +0x3B mov [esi+8],edi〕", "S03_C4/_audit/VERDICT.md#22"),
"006D0680": ("③b①+④ 按 TabClass 命令 ID 经比较式 switch 分派到各菜单处理器、并以 0x19 步有界循环兜底〔锚 +0x88 cmp eax,0x80D6 / +0x93 cmp eax,0x80EF / +0x223 cmp edi,0x19 / +0x226 jl〕", "S09_KPROVED2/_audit/VERDICT.md#24"),
}


def replace_span(sem, contract):
    """Replace the first '（槽语义未证...）' span; preserve prefix and trailing note."""
    start = sem.find("（槽语义未证")
    if start < 0:
        raise ValueError("no 槽语义未证 span: " + sem)
    end = sem.find("）", start)
    if end < 0:
        raise ValueError("no closing paren: " + sem)
    return sem[:start] + "（" + contract + "）" + sem[end + 1:]


def main():
    with open(COVERAGE, encoding="utf-8") as f:
        f.readline()
        rows = [p for p in (l.rstrip("\n").split("\t") for l in f)
                if len(p) == 8 and "槽语义未证" in p[3] and p[4] == "[已证]" and p[1] != "S22"]
    assert len(rows) == 36, len(rows)

    out_lines = ["entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"]
    for p in rows:
        entry, sub, name, sem, grade, evpath = p[0], p[1], p[2], p[3], p[4], p[5]
        contract, audit = CONTRACT[entry]
        new_sem = replace_span(sem, contract)
        assert "槽语义未证" not in new_sem, entry
        new_ev = f"EVIDENCE/disasm_{entry}.txt | 原审计:{audit}"
        out_lines.append(f"{entry}\t{sub}\t{name}\t{new_sem}\t[已证]\t{new_ev}")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    print(f"wrote {len(rows)} rows to {OUT}")
    # self-check: names byte-identical to coverage.tsv
    for src, dst in zip(rows, out_lines[1:]):
        d = dst.split("\t")
        assert d[2] == src[2], (src[0], src[2], d[2])
    print("name-verbatim check: PASS (36/36)")


if __name__ == "__main__":
    main()
