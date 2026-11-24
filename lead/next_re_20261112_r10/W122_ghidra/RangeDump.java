// W122l: decompile all functions whose entry lies in a given range; print C.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class RangeDump extends GhidraScript {
    public void run() throws Exception {
        long lo = 0x004BC000L, hi = 0x004BE000L;
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressIterator it = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddressSet(
                currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(lo),
                currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(hi)).getAddresses(true);
        java.util.LinkedHashSet<Long> entries = new java.util.LinkedHashSet<>();
        FunctionIterator fit = fm.getFunctions(true);
        for (Function f : fit) {
            long e = f.getEntryPoint().getOffset();
            if (e >= lo && e < hi) entries.add(e);
        }
        println("### functions with entry in [0x4BC000,0x4BE000): " + entries.size());
        for (Long e : entries) {
            Address fa = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(e.longValue());
            Function fn = fm.getFunctionAt(fa);
            println("--- FN " + fa + " size=" + (fn==null?-1:fn.getBody().getNumAddresses()) + " ---");
            if (fn == null) continue;
            DecompileResults res = di.decompileFunction(fn, 45, monitor);
            if (res == null || !res.decompileCompleted()) { println("   (failed)"); continue; }
            String[] lines = res.getDecompiledFunction().getC().split("\n");
            int k = 0;
            for (String ln : lines) {
                println("C| " + ln);
                if (++k > 60) { println("C| ..."); break; }
            }
        }
    }
}