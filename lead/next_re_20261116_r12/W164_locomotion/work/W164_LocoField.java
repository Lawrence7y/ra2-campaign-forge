// W164: Identify Locomotor field. Find callers of Locomotion constructors + writes to FootClass+0x278/+0x694
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W164_LocoField extends GhidraScript {
    void xrefs(long t,String label)throws Exception{
        Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        Function f=currentProgram.getFunctionManager().getFunctionContaining(a);
        println("=== callers of "+label+" @"+(f==null?a:f.getEntryPoint())+" ===");
        if(f==null) return;
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint());
        int n=0;while(it.hasNext()){Reference r=it.next();if(!r.getReferenceType().isCall())continue;
            Function cf=currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            println("  call@"+r.getFromAddress()+" in "+(cf==null?"?":cf.getEntryPoint())+
                (cf==null?"":" size="+cf.getBody().getNumAddresses()));n++;}
        if(n==0)println("  (none)");
    }
    public void run()throws Exception{
        // constructors that write Drive vtables at 0x4AF5C0 region
        xrefs(0x004AF5C0L,"DriveLocomotion ctor region");
        xrefs(0x0075AAA0L,"WalkLocomotion ctor region");
        xrefs(0x0055A6D0L,"LocomotionClass base ctor region");
        xrefs(0x004B4D00L,"Drive main-slot8 (ctor?)");
    }
}
