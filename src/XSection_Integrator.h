#ifndef __XSECTION_INTEGRATOR_H__
#define __XSECTION_INTEGRATOR_H__

#include "XSection.h"
#include "Montecarlo_Integrator.h"
#include "Analysis.h"

class XSection_Integrator{

    size_t NVarB = 3*NextV-4+2;
    size_t NVarP = 3*NextV-3+2;
    size_t NVarS = 3*NextR-4+2;

    std::vector<Histogram> Histograms;
    XSection XSec;
    std::unique_ptr<Montecarlo_Integrator> BIntegrator, SIntegrator, PIntegrator;

    public:

        struct XSection_Selector{
        std::string Channel;
        std::string Integrand;
        std::string Coupling;
        std::string Catalog;
        size_t NVars;
        };

        XSection_Integrator(Model* model, OLP* provider, PDF_Set* pdf,
                            const IntegratorFactory& makeIntegrator)
            : XSec(&Histograms, model, provider, pdf),
              BIntegrator(makeIntegrator(GSL_Integrand, CUBA_Integrand, NVarB)),
              SIntegrator(makeIntegrator(GSL_Integrand, CUBA_Integrand, NVarS)),
              PIntegrator(makeIntegrator(GSL_Integrand, CUBA_Integrand, NVarP)) {
            Analysis::InitializeHistograms(&Histograms);
        }

        void SetScales(double sqrts, double muRen, double muFac) {
            XSec.SetScales(sqrts, muRen, muFac);
        }

    private:
        struct Evaluation {
            XSection& section;
            const XSection_Selector& selector;
        };

        static double GSL_Integrand(double* x, size_t dim, void* param) {
            auto& evaluation = *static_cast<Evaluation*>(param);
            const auto& xs = evaluation.selector;
            double result;
            evaluation.section.SetXSection(xs.Catalog, xs.Integrand, xs.Channel,
                                            xs.Coupling, x, dim, &result);
            return result;
        }

        static int CUBA_Integrand(const int* ndim, const double x[],
                                  const int*, double f[], void* param) {
            std::vector<double> point(x, x + *ndim);
            f[0] = GSL_Integrand(point.data(), point.size(), param);
            return 0;
        }

    public:
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
                MCI = BIntegrator.get();
                XS.Catalog = "Virtuals";
                XS.NVars = MCI->Dimension;
            }
            else if (XS.Integrand=="Endpoint"){
                MCI = BIntegrator.get();
                XS.Catalog = "Reals";
                XS.NVars = MCI->Dimension;
            }
            else if (XS.Integrand=="PlusDistribution"){
                MCI = PIntegrator.get();
                XS.Catalog = "Reals";
                XS.NVars = MCI->Dimension;
            }
            else if (XS.Integrand=="Subtracted"){
                MCI = SIntegrator.get();
                XS.Catalog = "Reals";
                XS.NVars = MCI->Dimension;
            }
            else{
                std::cout<<"Error: Unavailable integrand "<<XS.Integrand<<" for "<<XS.Channel<<" channel"<<std::endl;
                throw "Unrecognized Integrand";
            }

            Evaluation evaluation{XSec, XS};
            mc.Params = &evaluation;
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

#endif
