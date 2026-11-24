// W122m: decompile FUN_00683ab0 (sole caller of FUN_004b6c30) + its callers.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class AiEntry extends GhidraScript {
    public void run() throws Exception {
        long t = 0x00683ab0L;
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        Function fn = currentProgram.getFunctionManager().getFunctionAt(a);
        if (fn == null) { println("no fn"); return; }
        println("### FN " + a + " size=" + fn.getBody().getNumAddresses() + " params=" + fn.getParameterCount());
        println("--- callers ---");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        int n = 0;
        while (it.hasNext()) {
            Reference r = it.next();
            if (!r.getReferenceType().isCall()) continue;
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            println("   call@" + r.getFromAddress() + " in " + (cf==null?"?":cf.getEntryPoint()) 
                    + " size=" + (cf==null?-1:cf.getBody().getNumAddresses()));
            if (++n > 12) { println("   ..."); break; }
        }
        if (n==0) println("   (no callers)");
        println("--- decompile ---");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        DecompileResults res = di.decompileFunction(fn, 60, monitor);
        if (res == null || !res.decompileCompleted()) { println("(failed)"); return; }
        int k = 0;
        for (String ln : res.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k > 130) { println("C| ..."); break; }
        }
    }
}