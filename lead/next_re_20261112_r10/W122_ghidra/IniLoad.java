// W122o: xrefs to the INI filename block (0x826254 ARTMD.INI, 0x826260 RULESMD.INI, 0x82626C RULEMD*.INI)
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class IniLoad extends GhidraScript {
    public void run() throws Exception {
        long[] ts = { 0x00826254L, 0x00826260L, 0x0082626CL };
        String[] nm = { "ARTMD.INI", "RULESMD.INI", "RULEMD*.INI" };
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        for (int i=0;i<ts.length;i++) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(ts[i]);
            ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
            println("### " + nm[i] + " @ " + a + " ###");
            java.util.LinkedHashSet<Long> fns = new java.util.LinkedHashSet<>();
            int n=0;
            while (it.hasNext()) {
                Reference r = it.next(); n++;
                Function cf = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                println("   ref@" + r.getFromAddress() + " in " + (cf==null?"?":cf.getEntryPoint()));
                if (cf!=null) fns.add(cf.getEntryPoint().getOffset());
            }
            if (n==0) println("   (none)");
            for (Long f : fns) {
                Address fa = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(f.longValue());
                Function fn = currentProgram.getFunctionManager().getFunctionAt(fa);
                if (fn==null) continue;
                println("--- FN " + fa + " size=" + fn.getBody().getNumAddresses() + " ---");
                DecompileResults res = di.decompileFunction(fn, 50, monitor);
                if (res==null || !res.decompileCompleted()) { println("   (failed)"); continue; }
                int k=0;
                for (String ln : res.getDecompiledFunction().getC().split("\n")) {
                    println("C| " + ln);
                    if (++k>60) { println("C| ..."); break; }
                }
            }
        }
    }
}