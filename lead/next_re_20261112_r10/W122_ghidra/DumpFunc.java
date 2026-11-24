// W122b: decompile the function containing a given address and dump its C.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class DumpFunc extends GhidraScript {
    public void run() throws Exception {
        long[] targets = { 0x0044F866L, 0x00442D90L, 0x00481180L };
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (long t : targets) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
            Function f = currentProgram.getFunctionManager().getFunctionContaining(a);
            if (f == null) { println("=== no function at " + a + " ==="); continue; }
            println("=== address " + a + " -> function " + f.getEntryPoint() + " " + f.getName()
                    + " size=" + f.getBody().getNumAddresses() + " ===");
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            if (r == null || !r.decompileCompleted()) { println("  decompile failed"); continue; }
            String c = r.getDecompiledFunction().getC();
            String[] lines = c.split("\n");
            int shown = 0;
            for (String ln : lines) {
                println("  " + ln);
                if (++shown > 120) { println("  ...(truncated)"); break; }
            }
            println("");
        }
    }
}