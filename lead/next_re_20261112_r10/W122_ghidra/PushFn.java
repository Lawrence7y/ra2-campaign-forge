// W122j: decompile FUN_006cf240 (push into container 0xB0C110) + find sibling size/pop.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class PushFn extends GhidraScript {
    void dump(long t, int cap) throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f == null) { println("no function at " + a); return; }
        println("### " + a + " size=" + f.getBody().getNumAddresses() + " ###");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 60, monitor);
        if (r == null || !r.decompileCompleted()) { println("  (decompile failed)"); return; }
        String[] lines = r.getDecompiledFunction().getC().split("\n");
        int k = 0;
        for (String ln : lines) {
            println("D| " + ln);
            if (++k > cap) { println("D| ..."); break; }
        }
        // callers of this function (to spot the family)
        println("--- callers of " + a + " ---");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        int n = 0;
        while (it.hasNext()) {
            Reference ref = it.next();
            if (!ref.getReferenceType().isCall()) continue;
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
            println("   call@" + ref.getFromAddress() + " in " + (cf==null?"?":cf.getEntryPoint()));
            if (++n > 6) { println("   ..."); break; }
        }
    }
    public void run() throws Exception {
        dump(0x006cf240L, 80);
    }
}