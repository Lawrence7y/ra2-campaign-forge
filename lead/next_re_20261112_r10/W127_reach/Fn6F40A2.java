// W127: profile the third crash signature (EIP=0x6F40A2, `mov al,[edx+0x155]`, EDX=0)
// @category W127
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class Fn6F40A2 extends GhidraScript {
    static final long FAULT = 0x006F40A2L;

    public void run() throws Exception {
        AddressSpace as = currentProgram.getAddressFactory().getDefaultAddressSpace();
        FunctionManager fm = currentProgram.getFunctionManager();
        Address a = as.getAddress(FAULT);
        Function f = fm.getFunctionContaining(a);
        println("### FAULT 0x" + Long.toHexString(FAULT)
                + " containing=" + (f == null ? "<none>" : f.getEntryPoint()
                + " size=" + f.getBody().getNumAddresses()));
        if (f == null) return;

        println("### offset in function = +0x" + Long.toHexString(FAULT - f.getEntryPoint().getOffset()));

        // callers of the enclosing function
        ReferenceManager rm = currentProgram.getReferenceManager();
        println("### direct callers:");
        int n = 0;
        for (Reference r : rm.getReferencesTo(f.getEntryPoint())) {
            if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) continue;
            Function cf = fm.getFunctionContaining(r.getFromAddress());
            println("    " + r.getReferenceType() + " @" + r.getFromAddress()
                    + " in " + (cf == null ? "?" : cf.getEntryPoint()));
            if (++n > 20) { println("    ..."); break; }
        }
        if (n == 0) println("    (none)");

        // who references the fault address as data (should be nobody)
        int rc = 0;
        for (Reference r2 : rm.getReferencesTo(a)) rc++;
        println("### references to the fault address itself: " + rc);

        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 120, monitor);
        if (r == null || !r.decompileCompleted()) { println("(decompile failed)"); return; }
        String[] lines = r.getDecompiledFunction().getC().split("\n");
        println("### DECOMPILED (" + lines.length + " lines)");
        int cap = Math.min(lines.length, 180);
        for (int i = 0; i < cap; i++) println("C| " + lines[i]);
        if (lines.length > cap) println("C| ...");
    }
}
