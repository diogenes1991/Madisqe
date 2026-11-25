#ifndef __MONTECARLOINTEGRATOR_H__
#define __MONTECARLOINTEGRATOR_H__

#include <functional>
#include <iostream>
#include <memory>

class Montecarlo_Integrator{

    public:

        size_t Dimension;

        struct Specifications{
            int RNGSeed = 1;
            void *Params = NULL;
            const int NVec = 1;
            size_t MaxEval = 1000000;
            size_t NStart = 1000;
            size_t NIncrease = 1000;
            double RelErr = 1E-4;
            double AbsErr = 1E-18;
            std::string Method = "";
        };

        virtual ~Montecarlo_Integrator(){};
        virtual void Integrate(Specifications * mc_specs, double* result, double* error) = 0;

};

using ScalarIntegrand = double (*)(double*, size_t, void*);
using VectorIntegrand = int (*)(const int*, const double*, const int*, double*, void*);
using IntegratorFactory = std::function<std::unique_ptr<Montecarlo_Integrator>(
    ScalarIntegrand, VectorIntegrand, size_t)>;

#endif
