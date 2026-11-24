// W127: close the last unproven item of §825 -- semantics of FUN_00724580
// (the second routine that receives [0x887368] as `this`). @category W127
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class ContainerSem extends GhidraScript {
    static final long[] TARGETS = { 0x00724580L, 0x00724730L, 0x00724fa0L, 0x00724fc0L };

    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace as = currentProgram.getAddressFactory().getDefaultAddressSpace();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (long va : TARGETS) {
            Address a = as.getAddress(va);
            Function f = fm.getFunctionAt(a);
            if (f == null) f = fm.getFunctionContaining(a);
            println("");
            println("=== 0x" + Long.toHexString(va) + "  "
                    + (f == null ? "<NOT A FUNCTION>" :
                       ("entry=" + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses())));
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 90, monitor);
            if (r == null || !r.decompileCompleted()) { println("  (decompile failed)"); continue; }
            String[] lines = r.getDecompiledFunction().getC().split("\n");
            int cap = Math.min(lines.length, 120);
            for (int i = 0; i < cap; i++) println("C| " + lines[i]);
            if (lines.length > cap) println("C| ... (" + lines.length + " total)");
        }
    }
}
