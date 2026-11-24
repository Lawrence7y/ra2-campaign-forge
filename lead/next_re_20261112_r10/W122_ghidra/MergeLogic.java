// W122p: decompile FUN_0052cd70 ONCE, full body, and FUN_007c8d20 too.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class MergeLogic extends GhidraScript {
    void dump(long t, int cap) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f == null) { println("no fn at " + a); return; }
        println("### " + a + " size=" + f.getBody().getNumAddresses() + " ###");
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 90, monitor);
        if (r == null || !r.decompileCompleted()) { println("(failed)"); return; }
        int k=0;
        for (String ln : r.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k>cap) { println("C| ...TRUNCATED"); break; }
        }
    }
    public void run() throws Exception {
        dump(0x0052cd70L, 260);
        dump(0x007c8d20L, 80);
    }
}