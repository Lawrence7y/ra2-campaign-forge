"""skipdata-safe instruction iterator: yields only real (non-.byte) instructions."""
import capstone

def real_insns(md, code, addr):
    for insn in md.disasm(code, addr):
        if insn.id == 0:  # capstone skipdata pseudo-instruction (.byte)
            continue
        yield insn
