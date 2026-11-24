// W130: function atlas, second pass -- STRING references + explain 8948 vs 8578.
// @category W130
//
// Pass 1 (FuncAtlas.java) read getDataAt(codeAddr), which never yields a string:
// string literals live in .rdata and are reached through REFERENCES from code.
// This pass walks each instruction's references, and for every target that is a
// printable ASCII data item, records the text.
//
// It also reports why the function manager holds 8948 entries while only 8578 are
// non-external (the difference should be external/thunk pseudo-functions).
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class FuncStrings extends GhidraScript {

    boolean printable(String s) {
        if (s == null || s.length() < 5) return false;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < 0x20 || c > 0x7E) return false;
        }
        return true;
    }

    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();

        int ext = 0, nonExt = 0;
        for (Function f : fm.getFunctions(true)) {
            if (f.isExternal()) ext++; else nonExt++;
        }
        println("### fnmanager total=" + fm.getFunctionCount()
                + " external=" + ext + " non-external=" + nonExt
                + " thunks=" + countThunks(fm));

        println("entry\tn_strings\tstrings");
        int emitted = 0;
        for (Function f : fm.getFunctions(true)) {
            if (f.isExternal()) continue;
            LinkedHashSet<String> out = new LinkedHashSet<>();
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (Reference r : ins.getReferencesFrom()) {
                    Address to = r.getToAddress();
                    if (to == null) continue;
                    Data d = getDataAt(to);
                    if (d == null || !d.hasStringValue()) continue;
                    Object v = d.getValue();
                    if (v == null) continue;
                    String s = v.toString();
                    if (!printable(s)) continue;
                    if (s.length() > 120) s = s.substring(0, 120);
                    out.add(s);
                    if (out.size() >= 40) break;
                }
                if (out.size() >= 40) break;
            }
            String joined = String.join(" | ", out)
                    .replace('\t', ' ').replace('\n', ' ').replace('\r', ' ');
            println(String.format("%08x\t%d\t%s", f.getEntryPoint().getOffset(),
                    out.size(), joined));
            emitted++;
        }
        println("### DONE " + emitted);
    }

    int countThunks(FunctionManager fm) {
        int n = 0;
        for (Function f : fm.getFunctions(true)) if (f.isThunk()) n++;
        return n;
    }
}
