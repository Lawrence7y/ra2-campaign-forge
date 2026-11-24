// W122r: decompile FUN_005301a0 (MIX loader driver)
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class MixDriver extends GhidraScript {
    public void run() throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x005301a0L);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        println("### " + a + " size=" + f.getBody().getNumAddresses());
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 60, monitor);
        if (r==null || !r.decompileCompleted()) { println("(failed)"); return; }
        int k=0;
        for (String ln : r.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k>90) { println("C| ..."); break; }
        }
    }
}