// W122k: who references the logic-tick counter 0x00A8ED84 ? decompile top referencers.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class TickDriver extends GhidraScript {
    public void run() throws Exception {
        long[] targets = { 0x00A8ED84L };
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (long t : targets) {
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
            ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
            Map<Long,Integer> cnt = new HashMap<>();
            int total = 0;
            while (it.hasNext()) {
                Reference r = it.next();
                total++;
                Function cf = currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
                if (cf == null) continue;
                long e = cf.getEntryPoint().getOffset();
                cnt.put(e, cnt.getOrDefault(e,0)+1);
            }
            println("### refs to " + a + " = " + total + " across " + cnt.size() + " fns");
            List<Map.Entry<Long,Integer>> es = new ArrayList<>(cnt.entrySet());
            es.sort((x,y) -> y.getValue() - x.getValue());
            int shown = 0;
            for (Map.Entry<Long,Integer> e : es) {
                Address fa = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(e.getKey().longValue());
                Function fn = currentProgram.getFunctionManager().getFunctionAt(fa);
                println(String.format("  fn %s refs=%d size=%d", fa, e.getValue(),
                        fn==null? -1 : fn.getBody().getNumAddresses()));
                if (shown < 2 && fn != null) {
                    shown++;
                    DecompileResults res = di.decompileFunction(fn, 60, monitor);
                    if (res != null && res.decompileCompleted()) {
                        int k = 0;
                        for (String ln : res.getDecompiledFunction().getC().split("\n")) {
                            println("D| " + ln);
                            if (++k > 70) { println("D| ..."); break; }
                        }
                    }
                }
            }
        }
    }
}