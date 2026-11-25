#ifndef __VIRTUAL_STRUCTURE_H__
#define __VIRTUAL_STRUCTURE_H__

#include "OLP.h"
#include <Model.h>
#include <string>
#include <unordered_map>

class VirtualStructure {

    public:

        OLP * Provider;
        Model * model;
        int nPar;
        Particle ** Particles;
        FVector   * Momenta;

        virtual ~VirtualStructure(){
            delete [] Particles;
            delete [] Momenta;
        }
        
        void BGenerate(double sqrts, double* rand, double* Jac){
            
            FVector P(sqrts,0,0,0);
            double dummy;

            FVector PIn[2];
            double mIn[2] = {Particles[0]->Mass,Particles[1]->Mass};
            double rIn[2]={0.0,0.0};
            dummy = 1.0;
            Recursive_PSP(P,2,PIn,mIn,rIn,dummy);
            Momenta[0] = PIn[0];
            Momenta[1] = PIn[1];
            
            FVector PFi[nPar-2];
            double mFi[nPar-2];
            for (int i=0;i<nPar-2;i++) mFi[i] = Particles[i+2]->Mass;
            dummy = 1.0;
            Recursive_PSP(P,nPar-2,PFi,mFi,rand,dummy);
            for (int i=0;i<nPar-2;i++) Momenta[i+2] = PFi[i];
            *Jac = dummy;   

        }

        void GetMomenta(FVector* p){

            for(int i=0;i<nPar;i++)p[i]=Momenta[i];
        }

        void GetMasses(double* m){

            for(int i=0;i<nPar;i++)m[i]=Particles[i]->Mass;
        }

        void GetPID(int* pid){

            for(int i=0;i<nPar;i++)pid[i]=Particles[i]->PID;
        }

        virtual void Born(std::string cp, double sqrts,  double* rand, double mu, double* rval) = 0;
        virtual void Virtual(std::string cp, double sqrts,  double* rand, double mu, double* rval) = 0;

    };

#endif


