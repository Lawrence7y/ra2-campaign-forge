// W122q: who references EXPANDMD%02d.MIX (0x82668C) and RA2MD.MIX (0x82667C)?
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class MixOpen extends GhidraScript {
    public void run() throws Exception {
        long[] ts = { 0x0082668CL, 0x0082667CL };
        String[] nm = { "EXPANDMD%02d.MIX", "RA2MD.MIX" };
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        for (int i=0;i<ts.length;i++) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(ts[i]);
            ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
            java.util.LinkedHashSet<Long> fns = new java.util.LinkedHashSet<>();
            int n=0;
            while (it.hasNext()) {
                Reference r = it.next(); n++;
                Function cf = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                if (cf!=null) fns.add(cf.getEntryPoint().getOffset());
            }
            println("### " + nm[i] + " refs=" + n + " fns=" + fns.size());
            for (Long f : fns) {
                Address fa = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(f.longValue());
                Function fn = currentProgram.getFunctionManager().getFunctionAt(fa);
                println("  FN " + fa + " size=" + (fn==null?-1:fn.getBody().getNumAddresses()));
            }
        }
    }
}