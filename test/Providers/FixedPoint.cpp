#include "gg_Zbbbar_Virtual.h"

#include <cassert>
#include <cmath>
#include <stdexcept>

class RecordingProvider final : public OLP {
public:
    std::string order;
    int strongPower = -1;
    int electromagneticPower = -1;
    int calls = 0;

    void UpdateParameters() override {}

    void Evaluate(Arguments* args) override {
        assert(args->SubProc == "gg_Zbbbar");
        assert(args->mu_ren == 91.0);
        assert(args->NExt == 5);
        auto* p = args->Momenta;
        const auto imbalance = p[0] + p[1] - p[2] - p[3] - p[4];
        assert(std::abs(imbalance.p0) < 1e-9);
        assert(std::abs(imbalance.p1) < 1e-9);
        assert(std::abs(imbalance.p2) < 1e-9);
        assert(std::abs(imbalance.p3) < 1e-9);
        order = args->Order;
        strongPower = args->CouplingPower[0];
        electromagneticPower = args->CouplingPower[1];
        ++calls;
        *args->RVal = order == "LO" ? 2.0 : 3.0;
    }

    void Evaluate_CC(Arguments*) override {
        throw std::logic_error("Unexpected color-correlated evaluation");
    }

    void Evaluate_SC(Arguments*) override {
        throw std::logic_error("Unexpected spin-correlated evaluation");
    }
};

int main() {
    RecordingProvider provider;
    Model model;
    gg_Zbbbar_Virtual integrand(provider, model);
    double random[] = {0.35, 0.41, 0.52, 0.63, 0.74};
    double born = 0.0;
    double loop = 0.0;

    integrand.Born("as2ae1", 500.0, random, 91.0, &born);
    assert(provider.calls == 1 && provider.order == "LO");
    assert(provider.strongPower == 2 && provider.electromagneticPower == 1);
    assert(std::isfinite(born) && born > 0.0);

    integrand.Virtual("as2ae2", 500.0, random, 91.0, &loop);
    assert(provider.calls == 2 && provider.order == "NLO");
    assert(provider.strongPower == 2 && provider.electromagneticPower == 2);
    assert(std::abs(loop / born - 1.5) < 1e-12);

    integrand.Virtual("as3ae1", 500.0, random, 91.0, &loop);
    assert(provider.calls == 3 && provider.order == "NLO");
    assert(provider.strongPower == 3 && provider.electromagneticPower == 1);
}
