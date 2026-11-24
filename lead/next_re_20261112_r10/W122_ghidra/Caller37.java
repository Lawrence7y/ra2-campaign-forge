// W122u: the 37-byte caller FUN_004f4450 and its callers
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class Caller37 extends GhidraScript {
    public void run() throws Exception {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x004f4450L);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f==null) { println("no fn at 004f4450"); return; }
        println("### FN " + a + " size=" + f.getBody().getNumAddresses());
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 60, monitor);
        if (r!=null && r.decompileCompleted()) {
            for (String ln : r.getDecompiledFunction().getC().split("\n")) println("C| " + ln);
        }
        println("--- callers of " + a + " ---");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        int n=0;
        while (it.hasNext()) {
            Reference ref = it.next();
            if (!ref.getReferenceType().isCall()) continue;
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
            println("   call@" + ref.getFromAddress() + " in " + (cf==null?"?":cf.getEntryPoint())
                    + " size=" + (cf==null?-1:cf.getBody().getNumAddresses()));
            if (++n>15) { println("   ..."); break; }
        }
        if (n==0) println("   (no callers)");
    }
}