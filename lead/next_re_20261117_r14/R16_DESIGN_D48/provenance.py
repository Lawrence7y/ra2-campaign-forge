"""Q3 支撑：`call [reg+disp]` 站点的基址寄存器「定义点」是什么形态。
方法：在函数体内线性反汇编，取站点之前最后一次写 base 的指令，分类。
这是**静态**局部事实，用来量化「只读采样拿不到、但静态数据流或许能拿到」的那一环。
只读。
"""
import sys, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan
import capstone
from capstone import x86 as X

img = plan.Image(plan.EXE)
text = plan.Text(img)
atlas = plan.load_atlas()
t = img.section('.text')
code = t['data']
LO = t['va']
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
starts = sorted(atlas)
asz = [atlas[s] for s in starts]

base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]

# 按函数分组，线性解码一次
by_fn = collections.defaultdict(list)
for s in base_only:
    f = plan.body_of(asz, starts, s['va'])
    if f is not None:
        by_fn[f].append(s)

def classify(prev, base):
    """prev 是站点前一条（最近的）写 base 的指令。"""
    if prev is None:
        return 'no_write_within_window'
    mn, ops = prev.mnemonic, prev.operands
    if mn == 'mov' and ops and ops[0].type == X.X86_OP_REG:
        src = ops[1]
        if src.type == X.X86_OP_MEM:
            if src.mem.base and not src.mem.index:
                return 'mem_obj_field' if (src.mem.disp or 0) else 'mem_obj_field_off0'
            if src.mem.base and src.mem.index:
                return 'mem_indexed'
            return 'mem_absolute'
        if src.type == X.X86_OP_IMM:
            return 'immediate'
        if src.type == X.X86_OP_REG:
            return 'reg_copy'
    if mn == 'lea':
        return 'lea'
    if mn == 'pop':
        return 'pop'
    if mn == 'xor' and prev.op_str.replace(' ', '') == '%s, %s' % (base, base):
        return 'zeroing'
    if mn in ('add', 'sub', 'inc', 'dec', 'and', 'or', 'shl', 'shr', 'imul'):
        return 'modified_in_place'
    return 'other:' + mn

stat = collections.Counter()
site_cnt = collections.Counter()
WINDOW = 200
for f, sites in by_fn.items():
    size = atlas[f]
    end = f + size
    o = f - LO
    insns = list(md.disasm(code[o:o + size], f))
    if not insns:
        continue
    addr_to_i = {i.address: k for k, i in enumerate(insns)}
    for s in sites:
        i = addr_to_i.get(s['va'])
        if i is None:
            continue
        base = s['base']
        prev = None
        for k in range(i - 1, max(-1, i - WINDOW), -1):
            q = insns[k]
            if not q.operands:
                continue
            d = q.operands[0]
            if d.type == X.X86_OP_REG and q.reg_name(d.reg) == base:
                # 只认「整体写」：mov/lea/pop/xor reg,reg
                prev = q
                break
        c = classify(prev, base)
        stat[c] += 1
        site_cnt[(c, s['disp'])] += 1

tot = sum(stat.values())
print('classified sites = %d / %d (in-atlas base-only)' % (tot, len(base_only)))
for k, v in stat.most_common():
    print('  %-22s %5d  %5.2f%%' % (k, v, 100.0 * v / tot))

# 只看「单值偏移」那 84 个 disp 的站点
cov = plan.load_coverage()
cov_by_entry = {int(r['entry'], 16): r for r in cov}
uniq_disp = {0xEC, 0x128, 0x134, 0x150, 0x190, 0x1B8, 0x1BC, 0x1C0, 0x1C4, 0x1C8, 0x1CC}
sub = collections.Counter()
for (c, d), n in site_cnt.items():
    if d in uniq_disp:
        sub[c] += n
print('\n其中属于首批单值偏移 disp 的站点：', sum(sub.values()))
for k, v in sub.most_common():
    print('  %-22s %5d' % (k, v))

# 基址寄存器分布（Q3：谁在当 base）
regs = collections.Counter(s['base'] for s in base_only)
print('\nbase register distribution:', regs.most_common())
print('disp==0 sites:', sum(1 for s in base_only if s['disp'] == 0))
print('negative disp sites:', sum(1 for s in base_only if s['disp'] < 0))
