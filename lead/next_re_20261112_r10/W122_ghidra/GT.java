// W122w: decompile Greatest_Threat 0x006F8DF0 (mod hooks this) - check loop structure for O(N)/O(N^2)
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class GT extends GhidraScript {
    public void run() throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x006F8DF0L);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f==null) { println("no fn at 0x6F8DF0"); return; }
        println("### " + a + " size=" + f.getBody().getNumAddresses());
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 60, monitor);
        if (r==null || !r.decompileCompleted()) { println("(failed)"); return; }
        int k=0;
        for (String ln : r.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k>80) { println("C| ..."); break; }
        }
    }
}