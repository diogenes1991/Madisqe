#ifndef __INTEGRAND_H__
#define __INTEGRAND_H__

#include "OLP.h"
#include <Model.h>

class Integrand{
            
    public:
        
        int nChannels;
        std::unordered_map<std::string,int> ChannelMap;     
        OLP * Provider;
        Model * model;

        virtual ~Integrand(){}
        
        int ChannelSelect(std::string CH){
            int Channel;
            try {Channel = ChannelMap.at(CH);}
            catch (const std::out_of_range& oor) {
                std::cerr<<"Error: Channel "<<CH<<" not found in Process"<<std::endl;
                std::cout<<"The available processes are:"<<std::endl;
                for ( auto& x : ChannelMap ) std::cout<<x.first<<" => "<<x.second<<std::endl;
                throw "Unrecognized Channel";
            }
            return Channel;
        }

        virtual void GetMomenta(std::string ch, FVector* p) = 0;
        virtual void GetMasses(std::string ch, double* m) = 0;
        virtual void GetPID(std::string ch, int* pid) = 0;
        virtual void Call(std::string in, std::string ch, std::string cp, double sqrts, double* rand, double mu, double* rval) = 0;

};

#endif


