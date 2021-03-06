#ifndef __XSECTION_INTEGRATOR_H__
#define __XSECTION_INTEGRATOR_H__

#include "XSection.h"
#include "GSL_Integrator.h"
#include "CUBA_Integrator.h"
#include "Analysis.h"

class XSection_Integrator{

    size_t NVarB = 3*NextV-4+2;
    size_t NVarP = 3*NextV-3+2;
    size_t NVarS = 3*NextR-4+2;

    Model * model;
    OLP * Provider;
    PDF_Set * PDF;
    Montecarlo_Integrator *BIntegrator, *SIntegrator, *PIntegrator;
    std::vector<Histogram> Histograms;

    public:

        static XSection * XSec;

        struct XSection_Selector{
        std::string Channel;
        std::string Integrand;
        std::string Coupling;
        std::string Catalog;
        size_t NVars;
        };

        XSection_Integrator(Model * mod, OLP * prov, PDF_Set * pdf, std::string Integrator){
            
            model = mod;
            PDF = pdf;
            Provider = prov;

            Analysis::InitializeHistograms(&Histograms);
            XSec = new XSection(&Histograms,model,Provider,PDF);
            
            if(Integrator=="GSL"){
                BIntegrator = new GSL_Integrator(GSL_Integrand,NVarB);
                SIntegrator = new GSL_Integrator(GSL_Integrand,NVarS);
                PIntegrator = new GSL_Integrator(GSL_Integrand,NVarP);
            }
            else if(Integrator=="CUBA"){
                BIntegrator = new CUBA_Integrator(CUBA_Integrand,NVarB);
                SIntegrator = new CUBA_Integrator(CUBA_Integrand,NVarS);
                PIntegrator = new CUBA_Integrator(CUBA_Integrand,NVarP);
            }
            else{
                std::cout<<"Error: Integrator interface not supported:"<<Integrator<<std::endl;
                throw "Unrecognized Integrator Interface";
            }
        }

        ~XSection_Integrator(){
            delete XSec;
            delete BIntegrator;
            delete SIntegrator;
            delete PIntegrator;
        }
            
        static double GSL_Integrand(double *x, size_t dim, void* param){
            double rval;
            XSection_Selector xs;
            xs = *(XSection_Selector*)(param);
            XSec->SetXSection(xs.Catalog,xs.Integrand,xs.Channel,xs.Coupling,x,xs.NVars,&rval);
            return rval;
        }

        static int CUBA_Integrand(const int *ndim, const double x[], const int *ncomp, double f[], void* param){
            double rval;
            XSection_Selector xs;
            xs = *(XSection_Selector*)(param);
            size_t dim = *ndim;
            double y[dim];
            for(size_t i=0;i<dim;i++)y[i]=x[i];
            XSec->SetXSection(xs.Catalog,xs.Integrand,xs.Channel,xs.Coupling,y,xs.NVars,&rval);
            f[0] = rval;
            return 0;
        }

        void ComputeXSection(XSection_Selector XS, Montecarlo_Integrator::Specifications MC){
            Montecarlo_Integrator::Specifications mc;
            mc.Method = MC.Method;
            mc.NStart = MC.NStart;
            mc.NIncrease = MC.NIncrease;
            mc.MaxEval = MC.MaxEval;
            mc.RelErr = MC.RelErr;

            Montecarlo_Integrator * MCI;    
            Clock C1;

            if (XS.Integrand=="Born"||XS.Integrand=="Virtual"){
                MCI = BIntegrator;
                XS.Catalog = "Virtuals";
                XS.NVars = MCI->Dimension;
            }
            else if (XS.Integrand=="Endpoint"){
                MCI = BIntegrator;
                XS.Catalog = "Reals";
                XS.NVars = MCI->Dimension;
            }
            else if (XS.Integrand=="PlusDistribution"){
                MCI = PIntegrator;
                XS.Catalog = "Reals";
                XS.NVars = MCI->Dimension;
            }
            else if (XS.Integrand=="Subtracted"){
                MCI = SIntegrator;
                XS.Catalog = "Reals";
                XS.NVars = MCI->Dimension;
            }
            else{
                std::cout<<"Error: Unavailable integrand "<<XS.Integrand<<" for "<<XS.Channel<<" channel"<<std::endl;
                throw "Unrecognized Integrand";
            }

            mc.Params = &XS;
            double res,err;
            MCI->Integrate(&mc,&res,&err);
            std::cout<<"XSection = "<<res<<" +/- "<<err<<std::endl;
            std::cout<<"\nThe integration took: ";
            C1.ShowTime(); 
            std::cout<<std::endl;

            for(Histogram H : Histograms){
                std::string Title = XS.Channel+" @ "+XS.Coupling; 
                H.Write(Title);
            } 
        }
};

XSection * XSection_Integrator::XSec = NULL;

#endif
