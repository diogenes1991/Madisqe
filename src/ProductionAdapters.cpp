#include "ProductionAdapters.h"

#include "CUBA_Integrator.h"
#include "Dummy_PDF.h"
#include "GSL_Integrator.h"
#include "LHA_PDF.h"
#include "NLOX_OLP.h"
#include "RECOLA_OLP.h"
#include <gsl/gsl_sf_dilog.h>

std::unique_ptr<OLP> MakeOLP(const std::string& name, Model* model) {
    if (name == "NLOX") return std::unique_ptr<OLP>(new NLOX_OLP(model));
    if (name == "RECOLA") return std::unique_ptr<OLP>(new RECOLA_OLP(model));
    throw "Unsupported OLP";
}

std::unique_ptr<PDF_Set> MakePDF(const std::string& name) {
    if (name == "Dummy") return std::unique_ptr<PDF_Set>(new Dummy_PDF);
    return std::unique_ptr<PDF_Set>(new LHA_PDF(name));
}

IntegratorFactory MakeIntegratorFactory(const std::string& name) {
    if (name == "GSL") {
        return [](ScalarIntegrand scalar, VectorIntegrand, size_t dim) {
            return std::unique_ptr<Montecarlo_Integrator>(new GSL_Integrator(scalar, dim));
        };
    }
    if (name == "CUBA") {
        return [](ScalarIntegrand, VectorIntegrand vector, size_t dim) {
            return std::unique_ptr<Montecarlo_Integrator>(new CUBA_Integrator(vector, dim));
        };
    }
    throw "Unrecognized Integrator Interface";
}

double PolyLog2(double x) {
    return gsl_sf_dilog(x);
}
