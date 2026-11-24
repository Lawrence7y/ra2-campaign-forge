// S19-F1 independent xref channel (Ghidra Java). Run as analyzeHeadless -noanalysis -postScript.
//@category S19F1
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class xref_check_java extends GhidraScript {
    @Override
    public void run() throws Exception {
        long[] targets = {0x750920L, 0x7509E0L, 0x750E20L, 0x406F70L, 0x752700L,
                          0x752480L, 0x752760L, 0x759C30L, 0x407B60L, 0x409470L,
                          0x7C89DAL, 0x7209D0L, 0x720EA0L};
        for (long va : targets) {
            try {
                Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
                ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(addr);
                List<String> sites = new ArrayList<String>();
                while (it.hasNext()) {
                    Reference r = it.next();
                    sites.add(r.getFromAddress().toString());
                }
                Collections.sort(sites);
                println(String.format("S19F1_XREF %08X %d", va, sites.size()));
                for (String s : sites) println(String.format("S19F1_SITE %08X %s", va, s));
            } catch (Exception e) {
                println(String.format("S19F1_XREF %08X ERROR %s", va, e));
            }
        }
    }
}
