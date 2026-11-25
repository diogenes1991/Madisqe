#ifndef __XSECTION_H__
#define __XSECTION_H__

#include "Real.h"
#include "Virtual.h"
#include "Analysis.h"
#include "PDF_Set.h"
#include "Constants.h"

class XSection{

    bool usingpdfs = true;

    std::unordered_map<std::string,Integrand*> XSectionMap;
    std::unordered_map<std::string,int> XSectionNPar;

    public:

        double sqrts;
        double mu_ren;
        double mu_fac;

        OLP * Provider;
        Model * model;
        RealIntegrands * Reals;
        VirtualIntegrands * Virtuals;
        PDF_Set * PDF;
        Integrand * IntegrandPtr = NULL;
        std::vector<Histogram> * Histograms;

        XSection(std::vector<Histogram> * Histos, Model * mod, OLP * prov, PDF_Set * pdf){

            Provider = prov;
            model = mod;
            PDF = pdf;
            
            Reals  = new RealIntegrands(Provider,model);
            XSectionMap.insert({"Reals",Reals});
            XSectionNPar.insert({"Reals",NextR});
            
            Virtuals = new VirtualIntegrands(Provider,model);
            XSectionMap.insert({"Virtuals",Virtuals});
            XSectionNPar.insert({"Virtuals",NextV});

            Histograms = Histos;
            
        }

        ~XSection(){
            delete Virtuals;
            delete Reals;
        }

        void SetScales(double sqrts0, double mu_ren0, double mu_fac0){
            sqrts = sqrts0;
            mu_ren = mu_ren0;
            mu_fac = mu_fac0;
        }

        void SetXSection(std::string Catalog, std::string Integrand, std::string Channel, std::string Coupling, double* x, size_t nVars, double* xsec){
            
            IntegrandPtr = XSectionMap.at(Catalog);
            int Next = XSectionNPar.at(Catalog);

            *xsec = 0;

            double sqrtshat;
            double prefactor=1.0;
            double beta = 0.0;
            
            int PID[Next];
            IntegrandPtr->GetPID(Channel,PID);

            double mass[Next];
            IntegrandPtr->GetMasses(Channel,mass);
            
            double sqrtshat_min = 0;
            
            if(usingpdfs){
                for(int i=2;i<Next;i++)sqrtshat_min+=mass[i];
                double x1_min = mass[0]/sqrts;
                double x2_min = mass[1]/sqrts;
                double x1_max = 0.5 * (1.0+sqrt(1.0-4.0*mass[0]*mass[0]/sqrts/sqrts));
                double x2_max = 0.5 * (1.0+sqrt(1.0-4.0*mass[1]*mass[1]/sqrts/sqrts));
                double x1 = x1_min + x[nVars-2] * (x1_max-x1_min);
                double x2 = x2_min + x[nVars-1] * (x2_max-x2_min);
                beta     = (x1 - mass[0]*mass[0]/(sqrts*x1) - x2 + mass[1]*mass[1]/(sqrts*x2))/(x1 + mass[0]*mass[0]/(sqrts*x1) + x2 + mass[1]*mass[1]/(sqrts*x2)); 
                sqrtshat = sqrt(mass[0]*mass[0]+mass[1]*mass[1]+mass[0]*mass[0]*mass[1]*mass[1]/(sqrts*sqrts*x1*x2)+sqrts*sqrts*x1*x2);
                prefactor = PDF->Evaluate(PID[0],x1,mu_fac)*PDF->Evaluate(PID[1],x2,mu_fac);
                }
            else{
                sqrtshat = sqrts;
            }

            if(sqrtshat > sqrtshat_min){
                
                prefactor *= 1.0/(2.0*sqrt(Lambda(sqrtshat*sqrtshat,mass[0]*mass[0],mass[1]*mass[1])));
                
                double partxsec;
                FVector p[Next];
                IntegrandPtr->Call(Integrand,Channel,Coupling,sqrtshat,x,mu_ren,&partxsec);

                double reweight;
                IntegrandPtr->GetMomenta(Channel,p);
                Analysis::ReweightEvent(p,beta,mass,PID,Next,&reweight);

                if(reweight){ 
                    *xsec = GeVtoPB*reweight*prefactor*partxsec;
                    double xsec_val = *xsec;
                    Analysis::FillHistograms(p,beta,mass,PID,Next,xsec_val,Histograms);
                }
            }
            else *xsec = 0;
            

        }
};

#endif
