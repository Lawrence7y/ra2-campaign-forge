// W122e: (a) callers of FUN_00683ab0 ; (b) windowed context around every while() in FUN_004b6c30
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class Round35 extends GhidraScript {
    void callersOf(long t) {
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        println("### CALLERS of " + a + " ###");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        int n = 0;
        while (it.hasNext()) {
            Reference r = it.next();
            if (!r.getReferenceType().isCall()) continue;
            Address from = r.getFromAddress();
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(from);
            println("  call@" + from + " in " + (cf==null? "?": cf.getEntryPoint()+" "+cf.getName())
                    + " size=" + (cf==null? -1 : cf.getBody().getNumAddresses()));
            if (++n > 25) { println("  ..."); break; }
        }
        if (n == 0) println("  (no callers found)");
    }
    public void run() throws Exception {
        callersOf(0x00683ab0L);
        println("");
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(0x004b6c30L);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        DecompileResults res = di.decompileFunction(f, 120, monitor);
        if (res == null || !res.decompileCompleted()) { println("decompile failed"); return; }
        String[] lines = res.getDecompiledFunction().getC().split("\n");
        println("### windowed while() context in FUN_004b6c30 (total C lines " + lines.length + ") ###");
        for (int i = 0; i < lines.length; i++) {
            if (lines[i].contains("while")) {
                int s = Math.max(0, i-14), e = Math.min(lines.length-1, i+6);
                println("---- while at line " + i + " ----");
                for (int k = s; k <= e; k++) println("C| " + lines[k]);
            }
        }
    }
}