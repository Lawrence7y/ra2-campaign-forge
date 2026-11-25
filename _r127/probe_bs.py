import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import bslice as B
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
G={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
def slice_from(icall, ppvK, window=200):
    """从 QI 调用之后，收集所有 call dword ptr [R+K]，并对 R 做回溯，
       判断它是否派生自 ppv 槽（direct）或 QI 结果。"""
    out=[]
    for j in range(icall+1, min(len(ins), icall+window)):
        a,m,o=ins[j]
        if m=='ret': break
        if m=='call' and o.startswith('dword ptr [') and o.endswith(']'):
            inner=o[len('dword ptr ['):-1]
            base,disp=B.split_base(inner)
            if base not in B.REGS: continue
            chain=[]; cur=base; depth=0
            while depth<4:
                w=B.writer(ins,j,cur)
                if w is None: chain.append('?'); break
                ji,kind,det=w
                chain.append((kind,det))
                if kind=='from_reg': cur=det; depth+=1; j=j  # keep same j
                elif kind=='from_stack':
                    # 栈槽是否是 ppv？比较相对偏移：qi 的 lea 在 icall-b 处，
                    # 此处 writer 的 esp 基准与该处不同 ⇒ 只做「是不是栈」的判据
                    chain.append(('ppv' if det and det[1]==ppvK else 'stk', det))
                    break
                else: break
            out.append((hex(a),disp,chain))
    return out
for i,(a,m,o) in enumerate(ins):
    if m=='push' and B.num(o) in G and ins[i+1][1]=='push' and ins[i+2][1]=='call':
        ic=i+2; pk=B.ppv_slot_of(ins,ic)
        r=slice_from(ic,pk)
        print('%-7s %x pk=%s calls=%s'%(G[B.num(o)],a,pk,r[:4]))
