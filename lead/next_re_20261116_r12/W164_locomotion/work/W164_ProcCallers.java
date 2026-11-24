// W164: xrefs to off4 slot16 Process wrappers
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W164_ProcCallers extends GhidraScript {
    void xrefs(long t,String label)throws Exception{
        Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        println("=== "+label+" @"+a+" ===");
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(a);
        int n=0;while(it.hasNext()){Reference r=it.next();if(!r.getReferenceType().isCall())continue;
            Function cf=currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            println("  call@"+r.getFromAddress()+" in "+(cf==null?"?":cf.getEntryPoint())+
                (cf==null?"":" size="+cf.getBody().getNumAddresses()));n++;}
        if(n==0)println("  (no direct callers - vtable only)");
    }
    public void run()throws Exception{
        xrefs(0x004B0500L,"Drive Process wrapper off4+40");
        xrefs(0x0075AC80L,"Walk Process wrapper off4+40");
        xrefs(0x00514310L,"Hover Process wrapper off4+40");
        xrefs(0x0069FC10L,"Ship Process wrapper off4+40");
        xrefs(0x004CCB40L,"Fly Process wrapper off4+40");
    }
}
