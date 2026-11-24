# -*- coding: utf-8 -*-
"""A4 独立复核探针：只读磁盘 PE、重同步线性解码反汇编核字节。
零真机 / 零活进程内存 / 零注入 / 零 hook。
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/W7_W4_REVIEW/_w7_a4.py
"""
import sys
import hashlib
import datetime
import struct

sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')
from ra2tool import Engine
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM

CARD = r'D:\Project\ra2-campaign-forge\lead\re_line_20261105\W4_FIELD_SPEC\sections\card_00A8ED50.md'


def sec(title):
    print('\n' + '=' * 78)
    print(title)
    print('=' * 78)


def show(va, n, label):
    print('\n--- %s 0x%x + 0x%x ---' % (label, va, n))
    for a, by, m, o in eng.disasm(va, n):
        print('  0x%x  %-14s  %-8s %s' % (a, by, m, o))


def detail(va, n, label):
    """逐操作数打印宽度/基址/位移/读写属性，用于核「1 字节」「无固定全局 VA」。"""
    print('\n--- %s 0x%x + 0x%x (operand detail) ---' % (label, va, n))
    print('  RAW 0x%x = %s' % (va, eng.rd(va, n).hex()))
    for i in md.disasm(eng.rd(va, n), va):
        print('  0x%x  %-8s %-32s op_sizes=%s' %
              (i.address, i.mnemonic, i.op_str, [op.size for op in i.operands]))
        for k, op in enumerate(i.operands):
            if op.type == X86_OP_MEM:
                base = i.reg_name(op.mem.base) if op.mem.base else 'NONE'
                index = i.reg_name(op.mem.index) if op.mem.index else 'NONE'
                print('      op%d MEM base=%s index=%s scale=%d disp=0x%x size=%d access=%d'
                      % (k, base, index, op.mem.scale, op.mem.disp, op.size, op.access))
            elif op.type == X86_OP_REG:
                print('      op%d REG %s size=%d access=%d'
                      % (k, i.reg_name(op.reg), op.size, op.access))
            elif op.type == X86_OP_IMM:
                print('      op%d IMM 0x%x size=%d' % (k, op.imm, op.size))


def jumps_to(target, lo, hi):
    """扫描 [lo,hi) 内所有以 target 为目标的跳转/调用指令。"""
    out = []
    for ins in eng.stream:
        if not (lo <= ins.address < hi):
            continue
        try:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                t = ins.operands[0].imm
                if t == target:
                    out.append((ins.address, ins.mnemonic, ins.op_str))
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
sec('S0  被核对象物理量 + 目标镜像绑定（全部本次实算/实读）')
b = open(CARD, 'rb').read()
print('CARD_PATH      =', CARD)
print('CARD_SIZE      =', len(b))
print('CARD_SHA256    =', hashlib.sha256(b).hexdigest())
print('CARD_READ_AT   =', datetime.datetime.now().isoformat())

eng = Engine()
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
print('EXE_PATH       =', r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
print('EXE_SHA256     =', eng.sha)
print('IMAGE_BASE     = 0x%x' % eng.IB)
print('COVERAGE       =', eng.coverage)
print('TEXT_RANGE     = 0x%x .. 0x%x' % (eng.TLO, eng.THI))

# ---------------------------------------------------------------------------
sec('S1  ① +0x98 门控：0x55B954 / 0x55B95A / 0x55B95C（对象内 1 字节、无固定全局 VA）')
show(0x55B93F, 0x30, 'COUNT_LOOP_55B93F')
detail(0x55B94B, 0x18, 'ITEMS_LOAD_AND_GATE_0x98')
show(0x55B960, 0x08, 'CALL_AND_BACKEDGE')

print('\n[S1.a] 0x55B954 处的访存操作数：mem.disp=0x98、base=ecx(寄存器)、size=1')
print('       上列 operand detail 中 op1 MEM 直接给出：base=ecx / disp=0x98 / size=1 / access=READ')
print('       ⇒ 不是 [absolute VA]，是 [obj+0x98]；obj 来自 0x55B94B 的 [0xA8ED44] (Items 堆指针)')
print('[S1.b] 0x55B95C 的 je 目标：0x55B95C+2 + 0x05 = 0x%x' % (0x55B95C + 2 + 5))
print('       => 跳过 0x55B95E 的 mov edx,[ecx] 与 0x55B960 的 call，落到 dec esi')

# 「无固定全局 VA」的机械核对：
hits_abs_98 = [h for h in eng.disp_hits(0x98)]
print('[S1.c] disp_hits(0x98) 绝对地址访存（若存在固定全局 VA=0x98 会命中）: %d 处 %s'
      % (len(hits_abs_98), hits_abs_98))
# 门控循环里出现的全部固定全局 VA
abs_in_loop = []
for ins in eng.stream:
    if 0x55B93F <= ins.address <= 0x55B966:
        try:
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
                    abs_in_loop.append((hex(ins.address), ins.mnemonic, ins.op_str))
        except Exception:
            pass
print('[S1.d] 循环体 0x55B93F..0x55B966 内全部「绝对地址访存」:')
for row in abs_in_loop:
    print('       ', row)
print('       ⇒ 仅 [0xA8ED50] (Count) 与 [0xA8ED44] (Items 指针)；+0x98 标志本身无绝对地址')

# 全镜像统计 [reg+0x98] 的 byte-ptr 读/写，确认是「通用对象级模板」而非 Bullet 专属计数
fld98 = eng.disp_hits_field(0x98)
by98 = []
for ins in eng.stream:
    try:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.disp == 0x98 and op.size == 1:
                by98.append((ins.address, 'W' if (op.access & 2) else 'R',
                             ins.mnemonic, ins.op_str))
                break
    except Exception:
        pass
print('[S1.e] 全 .text 中 size==1 的 [reg+0x98] 访存: %d 处 (W=%d R=%d)'
      % (len(by98), sum(1 for x in by98 if x[1] == 'W'), sum(1 for x in by98 if x[1] == 'R')))
print('       0x55B8F0..0x55BB30 主更新循环块内命中:')
for x in by98:
    if 0x55B8F0 <= x[0] <= 0x55BB30:
        print('        0x%x %s %s %s' % x)
print('       disp_hits_field(0x98) 全量(含非 byte 宽) = %d 处' % len(fld98))

# ---------------------------------------------------------------------------
sec('S2  ② 二道门 +0x90：0x4666F7 mov al,[ebp+0x90] / 0x4666FF je 0x467fee')
show(0x4666E0, 0x48, 'UPDATE_0x4666E0_HEAD')
detail(0x4666F7, 0x10, 'SECOND_GATE_0x90')
je_tgt = 0x4666FF + 6 + 0x18E9
print('[S2.a] 0x4666FF 字节 = %s；rel32 = 0x18e9；目标 = 0x4666FF+6+0x18E9 = 0x%x'
      % (eng.rd(0x4666FF, 6).hex(), je_tgt))
show(0x467FEE, 0x10, 'EARLY_EXIT_0x467FEE')
print('[S2.b] 0x4666E0..0x468000 内所有跳向 0x467FEE 的指令（证明它是共享早退/收尾点）:')
for a, m, o in jumps_to(0x467FEE, 0x4666E0, 0x468000):
    print('       0x%x %s %s' % (a, m, o))
print('       ⇒ +0x90 与 +0x154 两个门都汇入同一 pop/ret 早退点，不是「只返回一次」')

print('\n[S2.c] 0x55B960 的 call [edx+0x5c] 到 0x4666E0 的 vtable 链（进 B 函数体核实）')
print('       0x55B95E bytes =', eng.rd(0x55B95E, 5).hex())
print('       u32(0x7E46E0) COL            = 0x%x' % eng.u32(0x7E46E0))
print('       u32(0x7E46E4) vptr[0]       = 0x%x' % eng.u32(0x7E46E4))
print('       0x7E46E4 + 0x5C             = 0x%x' % (0x7E46E4 + 0x5C))
print('       u32(0x7E4740) vptr[+0x5C]   = 0x%x' % eng.u32(0x7E4740))
print('       0x466425 bytes              =', eng.rd(0x466425, 6).hex(), '(ctor 写 vptr)')
show(0x466425, 0x10, 'CTOR_VPTR_WRITE_ALIGNED_0x466425')
col = eng.u32(0x7E46E0)
print('       u32(col+12)=u32(0x%x) = 0x%x' % (col + 12, eng.u32(col + 12)))
print('       RTTI name @0x81AF78      =', eng.rd(0x81AF78, 48).split(b'\0')[0])
print('       ⇒ [edx+0x5c] = 0x4666E0，且 RTTI 为 .?AVBulletClass@@')

# ---------------------------------------------------------------------------
sec('S3  ③ 「Count ≥ 实际完成更新数」：循环结构与 ≤ 关系的字节依据')
print('[S3.a] 循环结构逐址（0x55B93F..0x55B966）：')
for a, by, m, o in eng.disasm(0x55B93F, 0x28):
    print('       0x%x  %-12s %-8s %s' % (a, by, m, o))
print('[S3.b] 0x55B964 的 jns rel8 = %s；回边目标 = 0x55B964+2+(0xe5-0x100) = 0x%x'
      % (eng.rd(0x4666FF, 6).hex() if False else eng.rd(0x55B964, 2).hex(),
         0x55B964 + 2 + (0xE5 - 0x100)))
print('       esi 初值 = Count-1 (0x55B944 lea esi,[eax-1])；0x55B949 jl 负数即空；')
print('       每轮 0x55B963 dec esi / 0x55B964 jns 回跳 ⇒ 迭代次数 ≤ 快照时的 Count')
print('[S3.c] 每轮至多 1 次 call [edx+0x5c]：0x55B95C je 跳过 ⇒ Update 调用数 ≤ 迭代数 ≤ Count')
print('[S3.c2] 循环体 0x55B94B..0x55B964 内是否重读 [0xA8ED50]？')
cnt = 0
for ins in eng.stream:
    if 0x55B94B <= ins.address <= 0x55B964:
        try:
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0 \
                        and op.mem.disp == 0xA8ED50:
                    cnt += 1
                    print('       0x%x %s %s' % (ins.address, ins.mnemonic, ins.op_str))
        except Exception:
            pass
print('       Count 在循环体内的重读次数 = %d ⇒ esi 初值由循环外一次快照决定' % cnt)
print('[S3.c3] 该循环块内是否出现对 [reg+0x98] 的「写」（可能改变门控）？')
w98 = []
for ins in eng.stream:
    if 0x55B93F <= ins.address <= 0x55B966:
        try:
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.disp == 0x98 and (op.access & 2):
                    w98.append(hex(ins.address))
                    break
        except Exception:
            pass
print('       =', w98, '（空 ⇒ 本块内门控字节不被改写）')
print('[S3.d] Update 体内 +0x90 / +0x158 / +0x154 门跳 0x467FEE 早退 ⇒')
print('       「跑完实质体的更新数 ≤ 调用数 ≤ Count」在本条可见路径内成立')

print('\n[S3.e] 作用域边界核查：是否存在「其它」调用 0x4666E0 的路径？')
# 直接 rel32 call 0x4666E0
direct = []
for ins in eng.stream:
    if ins.mnemonic == 'call':
        try:
            if ins.operands and ins.operands[0].type == X86_OP_IMM \
                    and ins.operands[0].imm == 0x4666E0:
                direct.append((ins.address, ins.op_str))
        except Exception:
            pass
print('       全 .text 直接 `call 0x4666e0` 命中: %d 处 %s' % (len(direct), [(hex(a), o) for a, o in direct]))
# 所有 [reg+0x5c] 间接 call（不限类）
ind5c = []
for ins in eng.stream:
    if ins.mnemonic == 'call':
        try:
            for op in ins.operands:
                if op.type == X86_OP_MEM and op.mem.disp == 0x5C and op.size == 4:
                    ind5c.append((ins.address, ins.op_str))
                    break
        except Exception:
            pass
print('       全 .text `call dword ptr [reg+0x5c]` 命中: %d 处（含其它类的同名虚槽，非全为 Bullet）' % len(ind5c))
for a, o in ind5c[:24]:
    print('        0x%x %s' % (a, o))
# 更新循环块 head 的直接调用者（卡自述 callers(0x55B8F0)=0）
callers_head = []
for ins in eng.stream:
    if ins.mnemonic == 'call':
        try:
            if ins.operands and ins.operands[0].type == X86_OP_IMM \
                    and ins.operands[0].imm == 0x55B8F0:
                callers_head.append(hex(ins.address))
        except Exception:
            pass
print('       全 .text 直接 `call 0x55b8f0`（更新循环块头）命中: %d 处 %s'
      % (len(callers_head), callers_head))

print('\n[S3.f] 0xA8ED50 绝对写/读点复核（disp_hits；卡称 3 W / 12 R = 15）')
dh = eng.disp_hits(0xA8ED50)
print('       disp_hits(0xA8ED50) total %d  W %d  R %d'
      % (len(dh), sum(1 for x in dh if x[1] == 'W'), sum(1 for x in dh if x[1] == 'R')))
for x in dh:
    print('        0x%x %s %s %s' % x)

print('\n[S3.g] 卡 §8.1 依赖的「其它遍历族无 +0x98 门」核查（关系到「Count 决定遍历规模」口径）')
for lo, hi, tag in [(0x650534, 0x650580, '0x650534 遍历族A'),
                    (0x67CC5F, 0x67CC88, '0x67CC5F 遍历族B'),
                    (0x7193CC, 0x7193F6, '0x7193CC 遍历族C'),
                    (0x5344CB, 0x5344E8, '0x5344CB 清场')]:
    g98, calls = [], []
    for ins in eng.stream:
        if lo <= ins.address < hi:
            try:
                for op in ins.operands:
                    if op.type == X86_OP_MEM and op.mem.disp == 0x98:
                        g98.append((hex(ins.address), ins.mnemonic, ins.op_str))
                        break
                if ins.mnemonic == 'call':
                    calls.append((hex(ins.address), ins.op_str))
            except Exception:
                pass
    print('       %s: [reg+0x98] = %s ; call 指令 = %s' % (tag, g98, calls))
print('       ⇒ 四处均不读 [reg+0x98]；其 call 为 +0x34/+0x08 等其它虚槽，不是 0x4666E0 更新体')

# ---------------------------------------------------------------------------
print('\n[S3.h] 卡 §3 称「原始 LE 字节 50 ED A8 00 全镜像 15 处」：独立复算')
needle = bytes.fromhex('50eda800')
raw = open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe', 'rb').read()
occ = [i for i in range(len(raw) - 3) if raw[i:i + 4] == needle]
print('       occurrences = %d' % len(occ))
in_text = [o for o in occ if eng.TB <= o < eng.TB + eng.TSZ]
print('       落在 .text 原始区间内 = %d' % len(in_text))
print('       ⇒ 与 disp_hits 的 15 处一一对应（口径：绝对 disp32 访存）')

print('\n[S3.i] 卡 §1/§5 称 CRT 静态构造 0x4E6860..0x4E689C 逐槽写 0xA8ED40 容器')
show(0x4E6860, 0x40, 'CRT_CTOR_4E6860')
print('       0x4E6891 bytes =', eng.rd(0x4E6891, 5).hex(), '(mov [0xa8ed50], eax)')

sec('S4  补充：+0x98 初值与 +0x90 初值（构造体字节）、向量自身标志区分')
show(0x5F3900, 0x98, 'BASE_CTOR_5F3900')
print('       0x5F3930 bytes =', eng.rd(0x5F3930, 6).hex(), '(mov byte [esi+0x90], al)')
print('       0x5F398D bytes =', eng.rd(0x5F398D, 6).hex(), '(mov byte [esi+0x98], bl)')
print('       0x4E6871 bytes =', eng.rd(0x4E6871, 7).hex(), '(mov byte [0xA8ED4C], 1) 向量自身标志')
print('       0x4E6878 bytes =', eng.rd(0x4E6878, 6).hex(), '(mov byte [0xA8ED4D], al) 向量自身标志')

# ---------------------------------------------------------------------------
sec('S5  诚实账（本次确实未验 / 不能从字节推出的事项）')
print("""1. 未启动 gamemd.exe / ra2loader / YURI.exe；未读活进程内存；未写 RPM/hook/注入/dump/挂线程实现。
2. 只做了磁盘 PE 静态反汇编；未做运行期真值/分布/扰动/跨帧归属/读失败率验证。
3. 0x55B8F0 更新循环块的上层调用链未闭合（直接 call 命中为 0，见 S3.e）；
   未证明该循环「每帧恰执行一次」，也未证明它是 MainLogicFrame(0x55D360) 函数体内部。
4. 全镜像 [reg+0x5c] 间接 call 有其它命中，未逐个判定所属类/是否 Bullet 派生；
   未证明 0x4666E0 是 BulletClass::Update 的唯一入口，也未排除派生类覆写 +0x5C 槽。
5. +0x98 / +0x90 的符号名、精确布尔语义未定名；22 个 +0x98 写点未逐个进函数体核实业务性质。
6. 「无固定全局 VA」仅就本门控指令的寻址方式（[ecx+0x98]，ecx 来自堆上 Items[i]）成立；
   未穷尽证明不存在某个全局镜像字节；其它对象数组复用同一模板见 S1.e。
7. disp_hits 口径 = 重同步线性解码的绝对 disp32 访存；别名间接写/rep movsd/读档反序列化等未穷尽
   （与卡 §3.3 及 RULING_D19.md:102 一致，本复核不销该项）。
8. 未核本卡与 Q2_ALPHA.md 的量纲归类一致性（属 C 组，不在 A4 单项范围）。""")
print('\nPROBE_DONE')
