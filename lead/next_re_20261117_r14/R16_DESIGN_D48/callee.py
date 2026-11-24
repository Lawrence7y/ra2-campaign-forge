"""补充事实：
 1. 降级形态两个候选 entry（被派发者）自己的序言有没有 EBP 帧（决定能否用 [ebp+4] 取返回地址）；
 2. 「R = site+L」精确匹配通道的误报量级（候选集合大小 / 窗口字数）。
只读。
"""
import sys, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan
import capstone

img = plan.Image(plan.EXE)
text = plan.Text(img)
atlas = plan.load_atlas()
t = img.section('.text')
code = t['data']
LO = t['va']
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

def pro(entry):
    o = entry - LO
    ins = []
    for k, i in enumerate(md.disasm(code[o:o + 40], entry)):
        ins.append((i.mnemonic, i.op_str))
        if k >= 7:
            break
    fp = any(ins[k] == ('push', 'ebp') and ins[k + 1][0] == 'mov' and ins[k + 1][1] == 'ebp, esp'
             for k in range(len(ins) - 1))
    return atlas.get(entry, -1), fp, ins[:6]

for e in (0x706640, 0x70B570, 0x73B140):
    size, fp, ins = pro(e)
    print('entry %08X size=%-5s ebp_frame=%-5s %s' % (e, size, fp, ins))

base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
call_mem_all = text.sites
all_calls = len(base_only) + len(text.sites) - len(base_only)
print('\ncandidate return addresses: base_only sites = %d ; all call-mem sites = %d'
      % (len(base_only), len(call_mem_all)))
for n, name in ((len(base_only), 'base_only'), (len(call_mem_all), 'all call-mem')):
    p = n / 2 ** 32
    print('  %s: P(one random 32-bit word == some site+len) = %.3e ; 1KB window(256 words) = %.4f%%'
          % (name, p, 100 * 256 * p))
