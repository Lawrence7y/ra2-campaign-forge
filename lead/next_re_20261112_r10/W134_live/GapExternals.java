// W134b: enumerate the 370 EXTERNAL functions to confirm they are the PE imports.
// @category W134
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class GapExternals extends GhidraScript {
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        List<String> names = new ArrayList<>();
        int n = 0;
        Set<String> thunkOfImport = new TreeSet<>();
        for (Function f : fm.getExternalFunctions()) {
            n++;
            String nm = f.getName();
            names.add(nm);
            if (f.isThunk()) thunkOfImport.add(nm);
        }
        println("### external function count = " + n);
        println("### of which flagged thunk = " + thunkOfImport.size());
        println("### first 25 names:");
        for (int i = 0; i < Math.min(25, names.size()); i++) {
            println("###   " + names.get(i));
        }
        // sanity: how many distinct names (duplicates would be suspicious)
        println("### distinct names = " + new TreeSet<>(names).size());

        // cross-check against the PE import table as Ghidra sees it
        SymbolTable st = currentProgram.getSymbolTable();
        int extSyms = 0;
        SymbolIterator it = st.getExternalSymbols();
        Set<String> libs = new TreeSet<>();
        while (it.hasNext()) {
            Symbol s = it.next();
            extSyms++;
            Namespace ns = s.getParentNamespace();
            if (ns != null) libs.add(ns.getName());
        }
        println("### external symbols    = " + extSyms);
        println("### import libraries   = " + libs);
        println("### DONE");
    }
}
