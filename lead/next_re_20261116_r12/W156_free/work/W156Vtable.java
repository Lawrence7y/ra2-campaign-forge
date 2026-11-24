// W156: dump DynamicVectorClass vtables used by BuildingClass::Array and decompile methods.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import java.util.*;

public class W156Vtable extends GhidraScript {
    AddressFactory af;
    DecompInterface di;
    void dumpVt(long vt, String label) throws Exception {
        println("=== VTABLE " + label + " @ " + Long.toHexString(vt) + " ===");
        Address a = af.getDefaultAddressSpace().getAddress(vt);
        ArrayList<Long> fns = new ArrayList<Long>();
        for (int i = 0; i < 16; i++) {
            long val = currentProgram.getMemory().getLong(a.add(i*8L));
            val = val & 0xFFFFFFFFL;
            println("  slot " + i + " @" + a.add(i*8L) + " -> " + String.format("%08x", val));
            if (val >= 0x400000L && val < 0x7C0000L) fns.add(val);
        }
        for (long f : fns) {
            Address fa = af.getDefaultAddressSpace().getAddress(f);
            Function fn = currentProgram.getFunctionManager().getFunctionAt(fa);
            if (fn == null) fn = currentProgram.getFunctionManager().getFunctionContaining(fa);
            println("  --- method @ " + fa + " size=" + (fn==null?-1:fn.getBody().getNumAddresses()) + " ---");
            if (fn == null) continue;
            DecompileResults res = di.decompileFunction(fn, 60, monitor);
            if (res == null || !res.decompileCompleted()) { println("     FAILED"); continue; }
            String c = res.getDecompiledFunction().getC();
            String[] lines = c.split("\n");
            int k=0;
            for (String ln : lines) { println("  C| " + ln); if (++k>80){println("  C| ...");break;} }
        }
    }
    public void run() throws Exception {
        af = currentProgram.getAddressFactory();
        di = new DecompInterface();
        di.openProgram(currentProgram);
        dumpVt(0x007E9E24L, "BuildingClass::Array.vptr(init)");
        dumpVt(0x007E9E44L, "BuildingClass::Array.vptr(cleared)");
        println("W156Vtable DONE");
    }
}
