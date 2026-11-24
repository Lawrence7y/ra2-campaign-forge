// W122v: decompile FUN_004fc0b0 (sole entry into the crash path)
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class Entry4fc extends GhidraScript {
    public void run() throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x004fc0b0L);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f==null) { println("no fn"); return; }
        println("### " + a + " size=" + f.getBody().getNumAddresses());
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 90, monitor);
        if (r==null || !r.decompileCompleted()) { println("(failed)"); return; }
        int k=0;
        for (String ln : r.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k>150) { println("C| ..."); break; }
        }
    }
}