// W122h: xrefs to 0x00B0CF64 (the 12-byte-stride array) + decompile enclosing functions.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class XrefB0CF64 extends GhidraScript {
    public void run() throws Exception {
        long[] targets = { 0x00B0CF64L, 0x00B0CF5CL, 0x00B0CF60L };
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (long t : targets) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
            println("### XREFS to " + a + " ###");
            ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
            int n = 0;
            java.util.LinkedHashSet<Long> fns = new java.util.LinkedHashSet<>();
            while (it.hasNext()) {
                Reference r = it.next();
                Address from = r.getFromAddress();
                Function cf = currentProgram.getFunctionManager().getFunctionContaining(from);
                println("  ref@" + from + " type=" + r.getReferenceType()
                        + " in " + (cf==null? "?" : cf.getEntryPoint()+" "+cf.getName()));
                if (cf != null) fns.add(cf.getEntryPoint().getOffset());
                if (++n > 40) { println("  ..."); break; }
            }
            if (n == 0) println("  (none)");
            for (Long f : fns) {
                Address fa = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(f.longValue());
                Function fn = currentProgram.getFunctionManager().getFunctionAt(fa);
                if (fn == null) continue;
                println("--- decompile " + fa + " size=" + fn.getBody().getNumAddresses() + " ---");
                DecompileResults res = di.decompileFunction(fn, 60, monitor);
                if (res == null || !res.decompileCompleted()) { println("   (decompile failed)"); continue; }
                String[] lines = res.getDecompiledFunction().getC().split("\n");
                int shown = 0;
                for (String ln : lines) {
                    println("D| " + ln);
                    if (++shown > 90) { println("D| ..."); break; }
                }
            }
            println("");
        }
    }
}