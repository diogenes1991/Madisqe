#include "####SubProcName####.h"

####SubProcName####::####SubProcName####(Process& process){

    
   Proc = &process;

####SubProcConst####

}

void ####SubProcName####::Subtracted(std::string cp, double* p, double mu, double* rval, double* acc){

    int i;
    double radiative[3];
    std::vector<FourVector> p_tilde;
    double EWKFac = 4*M_PI*(Proc->pc.alpha_e);
    double QCDFac = 4*M_PI*(Proc->pc.alpha_s);

####SubProcSub####

   else{
        std::cout << "Error: Coupling power"<<cp<<"not found in process"<<std::endl;
        abort();
   }

}

void ####SubProcName####::PlusDistribution(std::string cp, double* p, double mu, double* rval, double* acc){

####SubProcPlu####

}

void ####SubProcName####::Endpoint(std::string cp, double* p, double mu, double* rval, double* acc){

####SubProcEnd####

}