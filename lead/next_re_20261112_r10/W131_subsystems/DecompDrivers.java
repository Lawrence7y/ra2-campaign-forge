// W131: decompile the candidate main-loop / init functions (milestone 4 evidence).
// @category W131
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class DecompDrivers extends GhidraScript {
    static final long[] TARGETS = { 0x006DD8B0L, 0x006BB9A0L };
    static final int CAP = 70;

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
            println("=== 0x" + Long.toHexString(va) + " "
                    + (f == null ? "<none>" : ("size=" + f.getBody().getNumAddresses())));
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 180, monitor);
            if (r == null || !r.decompileCompleted()) { println("(failed)"); continue; }
            String[] ls = r.getDecompiledFunction().getC().split("\n");
            // print the head (signature + first statements) and any loop keywords
            for (int i = 0; i < Math.min(ls.length, CAP); i++) println("C| " + ls[i]);
            println("C| ... total " + ls.length + " lines");
            for (int i = 0; i < ls.length; i++) {
                String s = ls[i];
                if (s.contains("while (") || s.contains("for (") || s.contains("Sleep")
                        || s.contains("do {")) {
                    println("LOOP| line " + i + ": " + s.trim());
                }
            }
        }
    }
}
