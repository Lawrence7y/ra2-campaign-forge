// W127: tooltip region function table + decompile the functions that own the
// no-check call sites. @category W127
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class RegionDump extends GhidraScript {

    static final long LO = 0x006D0000L, HI = 0x006D2000L;
    static final long[] DECOMP = {
        0x006D04F0L, 0x006D0680L, 0x006D09C0L, 0x006D1200L, 0x006D14F0L,
        0x006D1570L, 0x006D15F0L, 0x006D1610L, 0x006D1660L,
        0x006ABD30L, 0x00654320L, 0x006922E0L
    };
    static final byte[] NEEDLE = { (byte)0x68, 0x73, (byte)0x88, 0x00 }; // disp32 0x00887368

    FunctionManager fm;
    Map<Long, Set<Long>> up = new HashMap<>();
    Set<Long> fnptr = new HashSet<>();

    Address a(long va) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
    }
    long key(Function f) { return f == null ? -1L : f.getEntryPoint().getOffset(); }

    void buildUp() {
        InstructionIterator it = currentProgram.getListing().getInstructions(true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            for (Reference r : ins.getReferencesFrom()) {
                if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) continue;
                Function ft = fm.getFunctionAt(r.getToAddress());
                if (ft == null) ft = fm.getFunctionContaining(r.getToAddress());
                Function ff = fm.getFunctionContaining(ins.getAddress());
                if (ft == null || ff == null) continue;
                long x = key(ff), y = key(ft);
                if (x < 0 || y < 0 || x == y) continue;
                up.computeIfAbsent(y, k -> new HashSet<>()).add(x);
            }
        }
    }

    void buildFnPtr() {
        Memory mem = currentProgram.getMemory();
        for (MemoryBlock blk : mem.getBlocks()) {
            if (!blk.isInitialized()) continue;
            String n = blk.getName();
            if (!n.equals(".rdata") && !n.equals(".data")) continue;
            long s = blk.getStart().getOffset(), sz = blk.getSize();
            for (long o = 0; o + 4 <= sz; o += 4) {
                long v;
                try { v = mem.getInt(a(s + o)) & 0xffffffffL; } catch (Exception e) { continue; }
                if (v < 0x401000L || v > 0x900000L || (v & 3) != 0) continue;
                if (fm.getFunctionAt(a(v)) != null) fnptr.add(v);
            }
        }
    }

    int countNeedle(Function f) {
        if (f == null) return -1;
        AddressSetView body = f.getBody();
        int hits = 0;
        Memory mem = currentProgram.getMemory();
        for (AddressRange r : body.getAddressRanges()) {
            long len = r.getLength();
            byte[] buf = new byte[(int) Math.min(len, 200000)];
            try {
                int n = mem.getBytes(r.getMinAddress(), buf);
                for (int i = 0; i + 4 <= n; i++) {
                    if (buf[i] == NEEDLE[0] && buf[i+1] == NEEDLE[1]
                        && buf[i+2] == NEEDLE[2] && buf[i+3] == NEEDLE[3]) hits++;
                }
            } catch (Exception e) { /* BSS / uninitialized */ }
        }
        return hits;
    }

    public void run() throws Exception {
        fm = currentProgram.getFunctionManager();
        buildUp();
        buildFnPtr();

        println("### REGION TABLE 0x6D0000..0x6D2000 ###");
        println("entry\tsize\tnCallers\tisFnPtr\thas887368\tcallers");
        for (Function f : fm.getFunctions(true)) {
            long e = f.getEntryPoint().getOffset();
            if (e < LO || e >= HI) continue;
            Set<Long> ps = up.get(e);
            StringBuilder sb = new StringBuilder();
            int n = 0;
            if (ps != null) for (Long p : ps) {
                if (n++ > 6) { sb.append("..."); break; }
                sb.append(String.format("%08x", p)).append(" ");
            }
            println(String.format("%08x\t%d\t%d\t%s\t%d\t%s",
                    e, f.getBody().getNumAddresses(),
                    ps == null ? 0 : ps.size(),
                    fnptr.contains(e) ? "Y" : "N",
                    countNeedle(f), sb.toString()));
        }

        println("");
        println("### DECOMPILE ###");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (long va : DECOMP) {
            Function f = fm.getFunctionAt(a(va));
            if (f == null) f = fm.getFunctionContaining(a(va));
            println("");
            println("=== FN " + String.format("%08x", va) + " "
                    + (f == null ? "<NOT A FUNCTION>" :
                       ("entry=" + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses()
                        + " fnptr=" + fnptr.contains(key(f)))));
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 90, monitor);
            if (r == null || !r.decompileCompleted()) { println("   (decompile failed)"); continue; }
            String[] lines = r.getDecompiledFunction().getC().split("\n");
            int cap = Math.min(lines.length, 90);
            for (int i = 0; i < cap; i++) println("C| " + lines[i]);
            if (lines.length > cap) println("C| ... (" + lines.length + " lines total)");
        }
    }
}
