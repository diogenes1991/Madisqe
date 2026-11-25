#ifndef MADISQE_PRODUCTION_ADAPTERS_H
#define MADISQE_PRODUCTION_ADAPTERS_H

#include "Montecarlo_Integrator.h"
#include "OLP.h"
#include "PDF_Set.h"

std::unique_ptr<OLP> MakeOLP(const std::string& name, Model* model);
std::unique_ptr<PDF_Set> MakePDF(const std::string& name);
IntegratorFactory MakeIntegratorFactory(const std::string& name);

#endif
