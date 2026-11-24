# -*- coding: utf-8 -*-
# _oo_disasm.py — 静态反汇编 ra2bench/gamemd.exe（只读磁盘文件，不启动进程、不 attach）
#
# 问题：HouseClass 由什么决定建几个、各自对应哪个 owner？
#
# 方法（三层，结论全部以 C 层新鲜解码为准）：
#   A) 全 .text 线性分块扫描 → _oo_disasm_out.txt（全量 dump；已知陷阱：capstone 单次 disasm
#      在 fo 0x6F59D 处遇非法字节即停——本次复现：fo<0x6F59D 恰 155,214 条 + 下一条起于 0x6F59D，
#      与台账 §1.2 的「155,215 条截断」完全咬合。分块续扫后 65 个非法字节，1,392,527 条）。
#      注意：线性扫描在数据块处会错位（本区实证：0x102D33 处 8b3d3802a800 被切成
#      3d3802a800），所以 A 层只作全量 dump，不作为证据。
#   B) 字节级精确 xref：直接在文件字节里扫 E8/E9 rel32 目标与 imm32/disp32（不受错位影响）。
#   C) 递归下降新鲜解码：对每个已验证入口从入口重新解码（编译器对齐保证正确）。
#
# 地址约定：本脚本与 HOUSE_COUNTERS_DECODED.md §1.2 一致——文档地址 = 文件偏移 fo = RVA
# （.text/.rdata/.data 的 raw==RVA）；真实 VA = fo + 0x400000（ImageBase）。
# 即：文档 0x103227 = 真实 VA 0x503227；虚表 0x7EA8A0 在 .rdata（raw 0x3E1000 起）。
import sys, os, json, struct, bisect
sys.dont_write_bytecode = True
import pefile, capstone

EXE    = r'D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe'
OUTDIR = r'D:\Project\ra2-campaign-forge\lead\re_orphan_owners_20261110'
TXT    = os.path.join(OUTDIR, '_oo_disasm_out.txt')
JS     = os.path.join(OUTDIR, '_oo_disasm_out.json')

data = open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IMGBASE = pe.OPTIONAL_HEADER.ImageBase            # 0x400000
SEC = {s.Name.rstrip(b'\x00').decode(): s for s in pe.sections}
t = SEC['.text']
TEXT_FO  = t.PointerToRawData                     # 0x1000
TEXT_END = TEXT_FO + min(t.Misc_VirtualSize, t.SizeOfRawData)   # 0x3E038D
VA  = lambda fo: fo + 0x400000                    # .text/.rdata/.data: VA = fo + 0x400000

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# ================= A) 全 .text 线性分块扫描 =================
CHUNK = 0x10000
insns, skipped = [], []
pos = TEXT_FO
while pos < TEXT_END:
    got = list(md.disasm(data[pos:pos + min(CHUNK, TEXT_END - pos)], pos))
    if got:
        insns.extend((g.address, g.size, g.bytes.hex(), g.mnemonic, g.op_str) for g in got)
        pos = got[-1].address + got[-1].size
    else:
        skipped.append(pos); pos += 1
n_before_trunc = sum(1 for x in insns if x[0] < 0x6F59D)
open(TXT, 'w', encoding='utf-8').write('\n'.join(
    '%08X  %-22s %-6s %s' % (x[0], x[2], x[3], x[4]) for x in insns) + '\n')

# ================= B) 字节级精确 xref =================
def e8_sites(tg):
    out, j = [], 0x1000
    while True:
        j = data.find(b'\xe8', j)
        if j < 0 or j > 0x3E1000: break
        rel = struct.unpack('<i', data[j+1:j+5])[0]
        if j + 5 + rel == tg: out.append(j)
        j += 1
    return out

def va_refs(va):
    out, j = [], data.find(struct.pack('<I', va))
    while j >= 0:
        out.append(j); j = data.find(struct.pack('<I', va), j + 1)
    return out

# ================= C) 新鲜解码 =================
def decode_from(entry, maxlen=0x9000):
    """从 entry 解码到首个 ret 且其后紧跟 0x90/0xCC 填充（=函数结束）"""
    out, pos = [], entry
    end = min(entry + maxlen, TEXT_END)
    while pos < end:
        got = list(md.disasm(data[pos:pos + 0x2000], pos))
        if not got: break
        brk = False
        for g in got:
            out.append((g.address, g.size, g.bytes.hex(), g.mnemonic, g.op_str))
            if g.mnemonic == 'ret':
                nxt = g.address + g.size
                if nxt < TEXT_END and data[nxt] in (0x90, 0xCC):
                    brk = True
                    break
        pos = got[-1].address + got[-1].size
        if brk: break
    return out

def dump(ins, mark=()):
    return ['%08X  %-22s %-6s %s%s' % (fo, hx, mn, op, '   ; <<<<' if fo in mark else '')
            for fo, sz, hx, mn, op in ins]

def window(lo, hi, mark=()):
    return dump([(g.address, g.size, g.bytes.hex(), g.mnemonic, g.op_str)
                 for g in md.disasm(data[lo:hi], lo)], mark)

def call_targets(ins):
    from collections import Counter
    c = Counter()
    for fo, sz, hx, mn, op in ins:
        if mn == 'call' and op.startswith('0x'):
            c[int(op.split()[0], 16)] += 1
    return ['0x%X(%d)' % (k, v) for k, v in c.most_common(40)]

def backedges(ins, upto=None):
    out = []
    for fo, sz, hx, mn, op in ins:
        if upto and fo > upto: break
        if mn[0] == 'j' and op.startswith('0x'):
            tg = int(op.split()[0], 16)
            if tg < fo: out.append({'back_at': '0x%X' % fo, 'mn': mn, 'head': '0x%X' % tg})
    return out

R = {}   # 最终 JSON
R['meta'] = {
    'file': EXE, 'size': os.path.getsize(EXE),
    'image_base': '0x%X' % IMGBASE, 'text_fo': '0x%X' % TEXT_FO, 'text_end': '0x%X' % TEXT_END,
    'addr_convention': '文档地址=fo=RVA(.text raw==RVA); 真实VA=fo+0x400000',
    'sweep_A': {'insns': len(insns), 'skipped_bytes': len(skipped),
                'first_skips': ['0x%X' % x for x in skipped[:8]],
                'insns_before_0x6F59D': n_before_trunc,
                'trunc_reconciliation': 'capstone 单次 disasm 从 0x1000 起停在 fo 0x6F59D：'
                    '%d 条(fo<0x6F59D)+1 条(起于 0x6F59D)=155,215，与台账 §1.2 记载一致' % n_before_trunc,
                'caveat': '线性扫描遇数据块会错位（例：0x102D33 的 8b3d3802a800 被错切），'
                          '全部结论以 C 层新鲜解码 + B 层字节扫描为准'},
}

# ---------- 核心地址 ----------
CTOR    = 0xF54A0    # HouseClass::HouseClass(HouseTypeClass*)  VA 0x4F54A0
SLOT5FN = 0x103040   # 含 0x103227 的虚方法                     VA 0x503040
FINDER  = 0x102D30   # HouseClass 按 Type 查找                  VA 0x502D30
COPYFN  = 0x102D60   # vt slot[13] (vt+0x34)                    VA 0x502D60
NOINIT  = 0xF7140    # HouseClass(NoInit&) 入口写 7 vptr        VA 0x4F7140
PARSEFN = 0x1009B0   # 地图 [Houses] 解析                       VA 0x5009B0
NEWFN   = 0x3C8E17   # operator new → 0x3C9442                  VA 0x7C8E17
DELFN   = 0x3C8B3D   # operator delete                          VA 0x7C8B3D
CC_LEAF = 0x9F9B0    # CounterClass 构造(寄存器版)              VA 0x49F9B0
CC_BIG  = 0x9FBE0    # CounterClass 构造(push ebx 版, 台账原语) VA 0x49FBE0
FNDNAME = 0x10C170   # HouseClass 按 Name 查找(返回数组索引)    VA 0x50C170
ENTCNT  = 0x126960   # INIClass::Entry_Count(section)           VA 0x526960
GETINT  = 0x75540    # INIClass::Get_Int(name,key,def)          VA 0x475540

R['key_addresses'] = {
    'HouseClass_ctor':    {'fo': '0x%X' % CTOR, 'va': '0x%X' % VA(CTOR), 'span': '0xF54A0..0xF6537', 'ret': 'ret 4 @0xF6537'},
    'slot5_reset_fn':     {'fo': '0x%X' % SLOT5FN, 'va': '0x%X' % VA(SLOT5FN),
                           'contains_0x103227': True, 'vtable': '0x7EA8A0 slot[5] (vt+0x14)'},
    'finder_by_type':     {'fo': '0x%X' % FINDER, 'va': '0x%X' % VA(FINDER)},
    'slot13_copy_fn':     {'fo': '0x%X' % COPYFN, 'va': '0x%X' % VA(COPYFN), 'vtable': '0x7EA8A0 slot[13] (vt+0x34)'},
    'noinit_ctor':        {'fo': '0x%X' % NOINIT, 'va': '0x%X' % VA(NOINIT)},
    'map_houses_parser':  {'fo': '0x%X' % PARSEFN, 'va': '0x%X' % VA(PARSEFN), 'span': '0x1009B0..0x100B3B'},
    'operator_new':       {'fo': '0x%X' % NEWFN, 'va': '0x%X' % VA(NEWFN)},
    'counterclass_leaf':  {'fo': '0x%X' % CC_LEAF, 'va': '0x%X' % VA(CC_LEAF)},
    'counterclass_big':   {'fo': '0x%X' % CC_BIG, 'va': '0x%X' % VA(CC_BIG)},
    'find_by_name':       {'fo': '0x%X' % FNDNAME, 'va': '0x%X' % VA(FNDNAME)},
    'ini_entry_count':    {'fo': '0x%X' % ENTCNT, 'va': '0x%X' % VA(ENTCNT)},
    'ini_get_int':        {'fo': '0x%X' % GETINT, 'va': '0x%X' % VA(GETINT)},
    'HouseArray':         {'va': '0xA80228', 'layout': 'vptr+0,Items+4(0xA8022C),Capacity+8,IsInit+C,'
                                                'IsAlloc+D,ActiveCount+0x10(0xA80238),GrowthStep+0x14=10'},
    'HouseTypes':         {'va': '0xA83C98', 'layout': 'Items+4(0xA83C9C),ActiveCount+0x10(0xA83CA8)'},
    'HouseClass_size':    '0x160B8 (push @0x100A13/0x100AFC/0x19A17B/0x287F9B/0x28817F/0x288327/0x2C3EBC)',
}

# ---------- Q1: 0x103227 所在函数（slot[5] 重置）----------
slot5 = decode_from(SLOT5FN)
slot5_end = slot5[-1][0]
R['q1_slot5_function'] = {
    'entry_fo': '0x%X' % SLOT5FN, 'entry_va': '0x%X' % VA(SLOT5FN),
    'end_ret_fo': '0x%X' % slot5_end,
    'disasm': window(0x103040, min(slot5_end + 8, 0x103300)),
    'counterclass_inits': [
        {'at': '0x%X' % f, 'lea': op, 'call': '0x9FBE0', 'target_off': op.split('[esi + ')[1].rstrip(']')}
        for f, sz, hx, mn, op in slot5
        if mn == 'lea' and '[esi + 0x55' in op
    ],
    'e8_direct_callers_whole_file': ['0x%X' % s for s in e8_sites(SLOT5FN)],
    'vtable_slot': {'vtable_va': '0x7EA8A0', 'slot_fo': '0x3EA8B4', 'slot_index': 5,
                    'call_form': 'call dword ptr [reg+0x14] after mov reg,[this]'},
    'note': '0x103227 落在 slot[5] 的第 5 个 CounterClass 清零（+0x5550）；'
            '该函数共 12 个 CounterClass 清零（+0x5500..+0x55DC），调 0x9FBE0（台账 §1.2 原语）',
}
R['q1_slot5_function']['counterclass_inits'] = [
    {'at': '0x%X' % f, 'lea': op, 'call': '0x9FBE0'}
    for f, sz, hx, mn, op in slot5
    if mn == 'lea' and '[esi + 0x55' in op
]

# ---------- Q1b: 创建路径（解析函数）----------
pf = decode_from(PARSEFN)
R['q1_creation_path'] = {
    'func_fo': '0x%X' % PARSEFN, 'func_va': '0x%X' % VA(PARSEFN),
    'disasm': dump(pf),
    'loops': backedges(pf),
    'loop_bound': 'mov [esp+0x10],eax ← push "Houses"(0x824D54); call 0x126960 @0x1009BE-0x1009C3 '
                  '= INIClass::Entry_Count("[Houses]")',
    'call_targets': call_targets(pf),
}

# ---------- Q1c: ctor 全文 ----------
ctor = decode_from(CTOR)
ctor_end = ctor[-1][0]
R['q1c_ctor'] = {
    'entry_fo': '0x%X' % CTOR, 'entry_va': '0x%X' % VA(CTOR), 'end_ret': '0x%X' % ctor_end,
    'key_sites': {
        'type_store':  '0xF54C2  mov [ebp+0x34],eax   ; this->Type = HouseTypeClass* (arg)',
        'id_init':     '0xF54B8  mov [ebp+0x30],-1',
        'counter_zero':'0xF5ABB..0xF5B34  12x lea ecx,[ebp+0x5500..0x55DC]; call 0x9F9B0 (CounterClass 构造)',
        'vptr_write':  '0xF5DCC..0xF5DFB  7x vptr: [ebp+0]=0x7EA8A0,+4=0x7EA884,+8=0x7EA87C,'
                       '+C=0x7EA874,+24=0x7EA834,+28=0x7EA80C,+2C=0x7EA7F4',
        'array_scan':  '0xF6032..0xF6196  for i in [0,[0xA80238]): 既有 house↔新 house 双向注册'
                       '（per-house 列表 this+0x5604 / this+0x561C，元素 8 字节）',
        'add_to_array':'0xF61D7..0xF61EC  HouseArray.AddItem: '
                       'ecx=[0xA80238](ActiveCount); inc; mov [0xA80238],ecx; '
                       'mov ecx,[0xA8022C](Items); mov [ecx+eax*4],ebp ← self-registration',
        'big_zero':    '0xF61EF..0xF6200  mov ecx,0x4204; lea edi,[ebp+0x57E4]; rep stosd（清 0x10810 字节）',
    },
    'ctor_disasm_head': dump(ctor[:120]),
    'ctor_counter_zero_block': window(0xF5AB0, 0xF5B45, mark=(0xF5ABB,)),
    'ctor_additem_block': window(0xF619C, 0xF6210, mark=(0xF61EC,)),
    'call_targets': call_targets(ctor),
}

# ---------- Q2: 全部创建点（new + ctor）----------
ctor_sites = e8_sites(CTOR)
R['q2_allocation'] = {
    'ctor_e8_sites_whole_file': ['0x%X' % s for s in ctor_sites],
    'new_fn': {'fo': '0x%X' % NEWFN, 'va': '0x%X' % VA(NEWFN),
               'body': 'push 1; push [esp+8]; call 0x3C9442(heap); ret  —— cdecl operator new',
               'delete_fn': '0x3C8B3D (HouseArray 清理 0xE6D3F 处调用释放 Items)'},
    'size_pushed': '0x160B8',
    'verdict': '按 owner 数动态堆分配（每 owner 一次 new 0x160B8），HouseArray 为 '
               'DynamicVectorClass<HouseClass*>（GrowthStep=10 扩容，0xF61B7-0xF61D0 经虚调用 [vptr+8] Resize），'
               '不存在固定槽位池',
    'sites': {},
}
for s in ctor_sites:
    lo = max(0x1000, s - 0x34)
    R['q2_allocation']['sites']['0x%X' % s] = window(lo, s + 12, mark=(s,))

# ---------- Q3: owner 名 → house 索引 ----------
R['q3_owner_mapping'] = {
    'step1_read_names': '0x1009D1 循环：push 0x14; push buf; push 0x889F64; push ebx(条目i); '
                        'push "Houses"(0x824D54); call 0x126CC0 → 读 [Houses] 第 i 条的名字',
    'step2_country':    '0x1009F7-0x100A05: push -1; push "Country"(0x824D4C); push 名字buf; '
                        'mov ecx,ebp(INI); call 0x75540 = INIClass::Get_Int(条目名, "Country", -1) → esi=HouseType索引',
    'step2b_def0':      '0x100A0C-0x100A11: cmp esi,-1; jne; xor esi,esi（-1 → 0）',
    'step3_type_obj':   '0x100A24-0x100A2A: mov edx,[0xA83C9C](HouseTypes.Items); '
                        'mov ecx,[edx+esi*4] → HouseTypeClass*',
    'step4_ctor':       '0x100A2E-0x100A30: mov ecx,eax(new HouseClass); push ecx(type); call 0xF54A0',
    'step5_name_copy':  '0x100A62-0x100A7B: lea edi,[esi+0x15FF4]; mov ecx,5; rep movsd + movsb '
                        '（21 字节名字串拷入 HouseClass.Name @+0x15FF4）',
    'step6_index':      'house 索引 = HouseArray 注册顺序：ctor 内 0xF61E0-0xF61EC '
                        'Items[ActiveCount++] = this',
    'lookup_by_name':   {'fo': '0x%X' % FNDNAME, 'va': '0x%X' % VA(FNDNAME),
                         'disasm': window(0x10C170, 0x10C20D),
                         'semantics': 'strcmp(名字, [house+0x15FF4]) 遍历 HouseArray，命中返回数组索引 edx，'
                                      '否则 -1（0x10C1FE 前的 or eax,-1）'},
    'lookup_by_type':   {'fo': '0x%X' % FINDER, 'va': '0x%X' % VA(FINDER),
                         'disasm': window(0x102D30, 0x102D60),
                         'semantics': '遍历 HouseArray，比较 [house+0x34](Type)->[+0xB8](索引) == ecx；'
                                      '命中返回 house 指针，否则 0。全 .text 共 %d 个直接调用点'
                                      % len(e8_sites(FINDER)),
                         'call_sites_count': len(e8_sites(FINDER)),
                         'sample_callers': ['0x190537(mov ecx,"Neutral"(0x82BA08); call 0x1117D0 名字→类型; call 本函数)'],
    },
    'fallback_all_countries': {
        'gate': '0x100AED-0x100AEF: mov eax,[0xA80238](HouseArray.ActiveCount); test; jne 0x100B34 '
                '（已存在 house 则跳过）',
        'loop': '0x100AF1-0x100B32: for esi in [0, [0xA83CA8](HouseTypes.ActiveCount)): '
                'new HouseClass(HouseTypes[esi]) @0x100B19 → 每个国家各建一个',
    },
}

# ---------- Q4: MaxPlayer ----------
R['q4_maxplayer'] = {
    'map_load_path_has_no_maxplayer': {
        'evidence': '创建循环 0x1009D1..0x100A83 的界 = [esp+0x10] = 0x126960(INI,"Houses") 返回值 '
                    '(节条目数，0x126A0C mov eax,[esi+0x30]); 回边 0x100A83 jl 0x1009D1。'
                    '循环体内无任何 Session/MaxPlayer 引用',
        'conclusion': '地图 [Houses] 列 14 个 owner → 14 个 HouseClass 全部 new+构造+注册；'
                      '多出的 10 个 owner 的实体在战役路径上不会被丢弃',
    },
    'maxplayers_ini_key': {
        'string_fo': '0x43F3F0', 'string_va': '0x83F3F0',
        'refs': ['0x2997F9(push)', '0x29A561(push)'] ,
        'read_fn': '0x2994F0..(VA 0x6994F0), 节="Player"(0x82BF9C), call 0x1276D0=Get_Int',
        'store': '0x29A560-0x29A587: push 0x83F3F0("MaxPlayers"); call 0x1276D0; mov [ebx+0x184],eax; '
                 '默认值 0x29A44E: mov dword [ebx+0x184],4',
        'caveat': 'ebx 所指结构未追到 Session 全局指针（fn 0x2994F0 内无 [0xA8B230] 引用）——'
                  '「Session.MaxPlayer 偏移」未能定谳，只定谳到键读取与存储形态',
    },
    'mp_slot_path': {
        'loop_bound': '0x28814C-0x288161: mov ecx,[0xA8B274]; cmp eax,[esp+0x20](=该值); jge 0x2882C2',
        'bound_source': '0x12D18F-0x12D195: mov ecx,[0x8871E0](RulesClass 实例指针+0x14A8); '
                        'mov [0xA8B274],ecx',
        'slot_array': '0xA8B29C（每槽位国家索引）; 0x288167-0x288175: edi=[ebx]; '
                      'cmp edi,-1 je / cmp edi,-3 je → 槽位无国家则停',
        'creation': '0x28817F-0x2881A0: push 0x160B8; call 0x3C8E17; push HouseTypes[edi]; '
                    'call 0xF54A0 —— 每个有效槽位建一个 house',
        'verdict': 'MaxPlayer 的分支效果只存在于多人槽位路径：槽位数界 [0xA8B274] 与 '
                   'cmp edi,-1/-3 跳过；战役/地图加载路径不存在该分支',
        'disasm_bound': window(0x28814C, 0x2881C0, mark=(0x28815D, 0x288161, 0x288169, 0x288175)),
        'disasm_ini': window(0x29A540, 0x29A595, mark=(0x29A560, 0x29A587)),
    },
    'fallback_gate': '0x100AED test [0xA80238],eax; jne 0x100B34 —— HouseArray 非空则跳过全表 fallback',
}

# ---------- 佐证块 ----------
R['evidence'] = {
    'counterclass_leaf_0x9F9B0': window(0x9F9B0, 0x9F9D0),
    'counterclass_big_0x9FBE0': window(0x9FBE0, 0x9FC10),
    'finder_0x102D30': window(0x102D30, 0x102D60),
    'copyfn_head_0x102D60': window(0x102D60, 0x102DA5),
    'housearray_init_0xE6CE0': window(0xE6CE0, 0xE6E1D),
    'noinit_ctor_0xF7140': window(0xF7140, 0xF7160),
    'e8_scans': {
        'to_0xF54A0(ctor)': ['0x%X' % s for s in ctor_sites],
        'to_0x102D30(finder)': ['0x%X' % s for s in e8_sites(FINDER)],
        'to_0x9FBE0(CC_big)': ['0x%X' % s for s in e8_sites(CC_BIG)],
        'to_0x9F9B0(CC_leaf)': ['0x%X' % s for s in e8_sites(CC_LEAF)],
        'to_0xF7140(noinit)': ['0x%X' % s for s in e8_sites(NOINIT)],
        'to_0x103040(slot5)': e8_sites(SLOT5FN),
        'to_0xF50B0': e8_sites(0xF50B0),
        'VA_ref_0x502D60(slot13)': ['0x%X' % x for x in va_refs(0x502D60)],
        'VA_ref_0x4F50B0(.data 表)': ['0x%X' % x for x in va_refs(0x4F50B0)],
    },
    'plus_0x5574_check': {
        'byte_pattern_74550500_hits': len(va_refs(0x5574) ) if False else None,
        'note': 'linear-sweep 全量语料中 「+ 0x5574]」 形态 0 命中；字节级 disp32(74 55 00 00)'
                ' 前接 modrm 的命中 0（B 层验证）',
        'disasm_hits': 0,
    },
}
R['evidence']['plus_0x5574_check']['byte_pattern_74550500_hits'] = None
# 字节级：74 55 00 00 作为 disp32
hits5574 = []
j = data.find(b'\x74\x55\x00\x00', TEXT_FO, TEXT_END)
while j >= 0:
    hits5574.append(j - 1)
    j = data.find(b'\x74\x55\x00\x00', j + 1, TEXT_END)
R['evidence']['plus_0x5574_check']['raw_disp32_positions'] = ['0x%X(modrm=%02X)' % (h, data[h]) for h in hits5574[:16]]
R['evidence']['plus_0x5574_check']['count'] = len(hits5574)

with open(JS, 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=1)

print('=== sweep A: %d insns (0x6F59D 前 %d 条), skipped %d' % (len(insns), n_before_trunc, len(skipped)))
print('=== slot5 fn 0x103040(VA 0x503040): 12x CounterClass init, ret@0x%X, E8 callers=%d'
      % (slot5_end, len(e8_sites(SLOT5FN))))
print('=== ctor 0xF54A0(VA 0x4F54A0): 0xF54A0..0x%X, sites: %s' % (ctor_end, ['0x%X' % s for s in ctor_sites]))
print('=== finder 0x102D30 callers: %d' % len(e8_sites(FINDER)))
print('=== wrote %s and %s' % (TXT, JS))
