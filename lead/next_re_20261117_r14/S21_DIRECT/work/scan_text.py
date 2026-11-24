#!/usr/bin/env python3
# S21-DIRECT full .text scanner. Read-only on target exe. Writes only under S21_DIRECT.
# Single capstone skipdata linear sweep over the whole .text raw section (100% coverage),
# deriving both RawSize and VirtualSize accountings from the same instruction stream.
import sys, os, json, struct, hashlib, io, time
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
import pefile, capstone

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
OUT = os.path.join(ROOT, "lead", "next_re_20261117_r14", "S21_DIRECT")
EV  = os.path.join(OUT, "EVIDENCE"); WK  = os.path.join(OUT, "work")
os.makedirs(EV, exist_ok=True); os.makedirs(WK, exist_ok=True)
SHA_EXPECTED = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

def main():
    t0=time.time()
    data=open(EXE,'rb').read()
    sha=hashlib.sha256(data).hexdigest().upper()
    assert sha==SHA_EXPECTED, f"EXE sha mismatch: {sha}"
    pe=pefile.PE(EXE,fast_load=True)
    ib=pe.OPTIONAL_HEADER.ImageBase
    sec=[s for s in pe.sections if s.Name.rstrip(b'\x00').decode(errors='replace')=='.text'][0]
    va=ib+sec.VirtualAddress
    vsize=sec.Misc_VirtualSize; rsize=sec.SizeOfRawData; raw=sec.PointerToRawData
    code=data[raw:raw+rsize]                 # full physical .text
    code_len=len(code); va_end=va+code_len
    vs_end=va+vsize
    print(f"ImageBase=0x{ib:X} .text VA=0x{va:X} VirtualSize=0x{vsize:X}({vsize}) RawSize=0x{rsize:X}({rsize})",flush=True)

    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    md.detail=True; md.skipdata=True

    counters={k:dict(n_insn=0,covered=0,e8_raw=code.count(b'\xE8'),e8_boundary=0,
                     true_calls=0,e8_other=0,mem_total=0,mem_index_zero=0,
                     mem_index_nonzero=0,has_op_index=0) for k in ('raw','vs')}
    call_sites=[]          # (addr,size,target,rel32) for full raw region
    seen_addr=set()
    last_offset=0
    for ins in md.disasm(code, va):
        off=ins.address-va
        size=ins.size if ins.size>0 else 1
        last_offset=max(last_offset,off+size)
        # which accounting buckets this instruction belongs to
        buckets=['raw']
        if ins.address < vs_end: buckets.append('vs')
        b=code[off:off+size]
        for bk in buckets:
            c=counters[bk]; c['n_insn']+=1; c['covered']=max(c['covered'],off+size)
        if b and b[0]==0xE8:
            for bk in buckets: counters[bk]['e8_boundary']+=1
            is_call=False
            if ins.id!=0:
                try:
                    is_call=(ins.id==capstone.x86.X86_INS_CALL and len(ins.operands)==1
                             and ins.operands[0].type==capstone.x86.X86_OP_IMM)
                except Exception:
                    is_call=False
            if len(b)>=5 and is_call:
                rel32=struct.unpack('<i',b[1:5])[0]
                target=(ins.address+5+rel32)&0xFFFFFFFF
                call_sites.append((ins.address,size,target,rel32))
                for bk in buckets: counters[bk]['true_calls']+=1
            else:
                for bk in buckets: counters[bk]['e8_other']+=1
        # 19 self-test (skipdata 'data' insns have id==0 and no operands)
        if ins.id!=0:
            try: ops=ins.operands
            except Exception: ops=[]
            for op in ops:
                if op.type==capstone.x86.X86_OP_MEM:
                    for bk in buckets:
                        c=counters[bk]; c['mem_total']+=1
                        if hasattr(op,'index'): c['has_op_index']+=1
                        try:
                            if op.mem.index==0: c['mem_index_zero']+=1
                            else: c['mem_index_nonzero']+=1
                        except Exception: pass
    covered=last_offset
    for bk in ('raw','vs'):
        c=counters[bk]
        c['text_bytes']=code_len if bk=='raw' else vsize
        c['coverage_pct']=100.0*covered/c['text_bytes'] if c['text_bytes'] else 0.0

    cr=counters['raw']; cv=counters['vs']
    print(f"[RawSize] insn={cr['n_insn']} covered={covered}/{code_len} ({cr['coverage_pct']:.4f}%) "
          f"E8raw={cr['e8_raw']} E8boundary={cr['e8_boundary']} true_calls={cr['true_calls']} other={cr['e8_other']}",flush=True)
    print(f"[VirtualSize] insn={cv['n_insn']} covered={covered}/{vsize} ({cv['coverage_pct']:.4f}%) "
          f"E8raw={cv['e8_raw']} E8boundary={cv['e8_boundary']} true_calls={cv['true_calls']} other={cv['e8_other']}",flush=True)
    print(f"[19-selftest raw] mem operands={cr['mem_total']} index==0:{cr['mem_index_zero']} "
          f"index!=0:{cr['mem_index_nonzero']} hasattr(op,'index'):{cr['has_op_index']}",flush=True)
    print(f"[coverage] last covered byte offset={covered} of {code_len} => {'100%' if covered>=code_len else 'PARTIAL'}",flush=True)
    print(f"[time] {time.time()-t0:.1f}s",flush=True)

    with open(os.path.join(WK,'all_direct_call_sites.tsv'),'w',encoding='utf-8',newline='\n') as f:
        f.write('site\tsize\ttarget\trel32\n')
        for a,s,t,r in call_sites:
            f.write(f'{a:08X}\t{s}\t{t:08X}\t{r}\n')
    stats=dict(sha=sha,image_base=ib,text_va=va,text_vsize=vsize,text_rawsize=rsize,primary='RawSize',
        covered_offset=covered,
        raw=dict(instructions=cr['n_insn'],covered_bytes=covered,text_bytes=code_len,coverage_pct=cr['coverage_pct'],
                 e8_raw=cr['e8_raw'],e8_at_boundary=cr['e8_boundary'],true_rel32_calls=cr['true_calls'],e8_other=cr['e8_other']),
        virtualsize=dict(instructions=cv['n_insn'],covered_bytes=covered,text_bytes=vsize,coverage_pct=cv['coverage_pct'],
                 e8_raw=cv['e8_raw'],e8_at_boundary=cv['e8_boundary'],true_rel32_calls=cv['true_calls'],e8_other=cv['e8_other']),
        selftest19=dict(mem_operands=cr['mem_total'],mem_index_zero=cr['mem_index_zero'],
                        mem_index_nonzero=cr['mem_index_nonzero'],has_op_index_attr=cr['has_op_index'],
                        note="capstone 5.0.7 x86 op has no .index attr; index at op.mem.index; no-index returns 0 not None"),
        baseline_instructions=1392592, baseline_e8=68253)
    json.dump(stats,open(os.path.join(EV,'scan_stats.json'),'w',encoding='utf-8'),indent=2)
    print('wrote scan_stats.json and work/all_direct_call_sites.tsv',flush=True)

if __name__=='__main__': main()
