// W122l2: decompile functions whose entry is in [0x4BC000,0x4BE000)
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class RangeDump2 extends GhidraScript {
    public void run() throws Exception {
        long lo = 0x004BC000L, hi = 0x004BE000L;
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        java.util.List<Function> sel = new java.util.ArrayList<>();
        for (Function f : fm.getFunctions(true)) {
            long e = f.getEntryPoint().getOffset();
            if (e >= lo && e < hi) sel.add(f);
        }
        println("### functions in range: " + sel.size());
        for (Function fn : sel) {
            println("--- FN " + fn.getEntryPoint() + " size=" + fn.getBody().getNumAddresses() + " ---");
            DecompileResults res = di.decompileFunction(fn, 45, monitor);
            if (res == null || !res.decompileCompleted()) { println("   (failed)"); continue; }
            int k = 0;
            for (String ln : res.getDecompiledFunction().getC().split("\n")) {
                println("C| " + ln);
                if (++k > 55) { println("C| ..."); break; }
            }
        }
    }
}