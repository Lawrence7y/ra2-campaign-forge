// W122d: decompile FUN_004b6c30 (list walk from DAT_00a8b230) and report its callers.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class DumpHot extends GhidraScript {
    public void run() throws Exception {
        long target = 0x004b6c30L;
        Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(target);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f == null) { println("no function at " + a); return; }
        // callers
        println("=== CALLERS of " + f.getEntryPoint() + " ===");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        int n = 0;
        while (it.hasNext()) {
            Reference r = it.next();
            if (!r.getReferenceType().isCall()) continue;
            Address from = r.getFromAddress();
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(from);
            println("  call@" + from + "  in " + (cf == null ? "?" : cf.getEntryPoint() + " " + cf.getName())
                    + "  size=" + (cf == null ? -1 : cf.getBody().getNumAddresses()));
            if (++n > 20) { println("  ..."); break; }
        }
        // decompile
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        DecompileResults res = di.decompileFunction(f, 90, monitor);
        println("=== DECOMPILE " + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses() + " ===");
        if (res == null || !res.decompileCompleted()) { println("decompile failed"); return; }
        String c = res.getDecompiledFunction().getC();
        String[] lines = c.split("\n");
        int shown = 0;
        for (String ln : lines) {
            println("C| " + ln);
            if (++shown > 260) { println("C| ...(truncated)"); break; }
        }
    }
}