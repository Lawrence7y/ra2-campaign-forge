// W128: locate the destruction path that frees a chain-registered object
// WITHOUT unlinking it (②-b 成因 B, ledger §836-4).
// @category W128
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class UnlinkAudit extends GhidraScript {

    static final long UNLINK_ADD  = 0x0047EA90L;  // RemoveObject (per-cell)
    static final long UNLINK_WRAP = 0x005687F0L;  // footprint-wide unlink wrapper
    static final long LINK_ADD    = 0x0047E8A0L;  // AddObject
    static final long LINK_WRAP   = 0x005683C0L;  // footprint-wide link wrapper
    static final long TERRAIN_VT  = 0x007F522CL;  // .?AVTerrainClass@@ vtable

    FunctionManager fm;
    ReferenceManager rm;

    void callers(String label, long target) {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(target);
        Function tgt = fm.getFunctionAt(a);
        println("");
        println("### CALLERS of " + label + " (0x" + Long.toHexString(target) + ")"
                + (tgt == null ? "" : "  [fn entry=" + tgt.getEntryPoint() + "]"));
        int n = 0;
        TreeSet<Long> inFns = new TreeSet<>();
        for (Reference r : rm.getReferencesTo(a)) {
            if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) continue;
            Function cf = fm.getFunctionContaining(r.getFromAddress());
            long k = cf == null ? -1 : cf.getEntryPoint().getOffset();
            inFns.add(k);
            println(String.format("    %s @%08x  in %s", r.getReferenceType(),
                    r.getFromAddress().getOffset(),
                    cf == null ? "?" : String.format("%08x", k)));
            n++;
            if (n > 60) { println("    ..."); break; }
        }
        if (n == 0) println("    (none)");
        println("    distinct containing functions: " + inFns.size());
    }

    void dumpVTableHead(long vt, int slots) {
        println("");
        println("### vtable 0x" + Long.toHexString(vt) + " slot 0.." + (slots - 1));
        try {
            ghidra.program.model.mem.Memory mem = currentProgram.getMemory();
            Address base = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(vt);
            for (int i = 0; i < slots; i++) {
                Address p = base.add(4L * i);
                long v = mem.getInt(p) & 0xffffffffL;
                println(String.format("    slot %2d (vt+0x%02X) = 0x%08X", i, 4 * i, v));
            }
        } catch (Exception e) { println("   (read failed: " + e + ")"); }
    }

    void decompileAt(long va, int cap) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
        Function f = fm.getFunctionAt(a);
        if (f == null) f = fm.getFunctionContaining(a);
        println("");
        println("### DECOMPILE 0x" + Long.toHexString(va) + " -> "
                + (f == null ? "<no function>" : f.getEntryPoint() + " size=" + f.getBody().getNumAddresses()));
        if (f == null) return;
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 120, monitor);
        if (r == null || !r.decompileCompleted()) { println("   (failed)"); return; }
        String[] ls = r.getDecompiledFunction().getC().split("\n");
        for (int i = 0; i < Math.min(ls.length, cap); i++) println("C| " + ls[i]);
        if (ls.length > cap) println("C| ... (" + ls.length + " lines)");
    }

    public void run() throws Exception {
        fm = currentProgram.getFunctionManager();
        rm = currentProgram.getReferenceManager();

        callers("RemoveObject (per-cell unlink)", UNLINK_ADD);
        callers("footprint unlink wrapper", UNLINK_WRAP);
        callers("AddObject", LINK_ADD);
        callers("footprint link wrapper", LINK_WRAP);

        dumpVTableHead(TERRAIN_VT, 4);

        // TerrainClass dtor (vtable slot 0 = scalar deleting destructor)
        ghidra.program.model.mem.Memory mem = currentProgram.getMemory();
        long dtor = mem.getInt(currentProgram.getAddressFactory()
                .getDefaultAddressSpace().getAddress(TERRAIN_VT)) & 0xffffffffL;
        println("");
        println("### TerrainClass slot0 (dtor) = 0x" + Long.toHexString(dtor));
        decompileAt(dtor, 120);
    }
}
