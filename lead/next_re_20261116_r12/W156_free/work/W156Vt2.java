// W156: correct 4-byte vtable dump + find callers of FindIndex and Delete.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W156Vt2 extends GhidraScript {
    AddressFactory af;
    FunctionManager fm;
    ReferenceManager rm;
    DecompInterface di;
    ArrayList<Long> methods = new ArrayList<Long>();

    void dumpVt(long vt, String label) throws Exception {
        println("=== VTABLE " + label + " @ " + Long.toHexString(vt) + " (4-byte slots) ===");
        Address a = af.getDefaultAddressSpace().getAddress(vt);
        for (int i = 0; i < 16; i++) {
            long val = currentProgram.getMemory().getInt(a.add(i*4L)) & 0xFFFFFFFFL;
            println("  [" + i + "] " + a.add(i*4L) + " -> " + String.format("%08x", val));
            if (val >= 0x400000L && val < 0x7C0000L && !methods.contains(val)) methods.add(val);
        }
    }
    void callers(long addr, String label) throws Exception {
        Address a = af.getDefaultAddressSpace().getAddress(addr);
        println("=== CALLERS of " + label + " @ " + a + " ===");
        ReferenceIterator it = rm.getReferencesTo(a);
        TreeSet<String> s = new TreeSet<String>();
        int n=0;
        while (it.hasNext()) {
            Reference r = it.next();
            if (!r.getReferenceType().isCall()) continue;
            Function f = fm.getFunctionContaining(r.getFromAddress());
            String fn = (f==null)?"NOFUNC":f.getEntryPoint().toString();
            s.add("  " + fn + " @" + r.getFromAddress());
            n++;
        }
        println("  total calls=" + n);
        for (String x : s) println(x);
    }
    public void run() throws Exception {
        af = currentProgram.getAddressFactory();
        fm = currentProgram.getFunctionManager();
        rm = currentProgram.getReferenceManager();
        di = new DecompInterface();
        di.openProgram(currentProgram);
        dumpVt(0x007E9E24L, "Array.vptr(init)");
        dumpVt(0x007E9E44L, "Array.vptr(cleared)");
        callers(0x004E9690L, "FindIndex");
        callers(0x004E95E0L, "Resize");
        // decompile each distinct method, shorter cap
        for (long f : methods) {
            Address fa = af.getDefaultAddressSpace().getAddress(f);
            Function fn = fm.getFunctionAt(fa);
            if (fn==null) fn = fm.getFunctionContaining(fa);
            println("--- METHOD " + fa + " size=" + (fn==null?-1:fn.getBody().getNumAddresses()) + " ---");
            if (fn==null) continue;
            DecompileResults res = di.decompileFunction(fn, 60, monitor);
            if (res==null || !res.decompileCompleted()) { println("   FAILED"); continue; }
            String[] lines = res.getDecompiledFunction().getC().split("\n");
            int k=0;
            for (String ln : lines) { println("C| " + ln); if (++k>70){println("C| ...");break;} }
        }
        println("W156Vt2 DONE");
    }
}
