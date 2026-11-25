#include <Model.h>

Model::Model(){

    NLF = 4;
    NHF = 2;

    UseCMScheme = true;
    UseGMuScheme = true;

    alpha_e = 1.0;
    alpha_s = 0.118;
    GFermi  = 1.16637E-5;
        
    Wm.Mass = 80.379;
    Wp.Mass = 80.379;
    
    Z.Mass = 91.1876;
    
    b.Mass = 4.75;
    bbar.Mass = 4.75;
    
    h.Mass = 125;
    
    t.Mass = 172.76;
    tbar.Mass = 172.76;
    
}

