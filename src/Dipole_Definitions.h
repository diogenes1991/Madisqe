#ifndef __DIPOLES_DEFINITIONS_H__
#define __DIPOLES_DEFINITIONS_H__

#include "Four_Vector.h"
#include "Constants.h"

double PolyLog2(double x);

#define TESTMODE 0

// 
//   II Functions and Maps 
// 

template <class T>
T x_ab(FVectorT<T> pa, FVectorT<T> pb, FVectorT<T> k){
    T out = pa*pb - pa*k - pb*k;
    out = out / (pa*pb);
    return out;
}

template <class T>
T xab_cut(T sab, T ma, T mb){ 
    return ((2*ma*mb)/(sab-ma*ma-mb*mb));
}

template <class T>
T Rab(FVectorT<T> pa, FVectorT<T> pb, T x){
    T aux = pow(2*(pa*pb)*x,2)-((pa*pa)*(pb*pb));
    aux = aux / (pow(2*(pa*pb),2)-((pa*pa)*(pb*pb)));
    return sqrt(aux);
}

template <class T>
FVectorT<T> pa_II(FVectorT<T> pa, FVectorT<T> pb, T xab){
    T sbar = 2*(pa*pb);
    FVectorT<T> aux = (2*sbar*(pa*pa)*(1.0-xab*xab))*pb;
    aux = 1.0/((Rab(pa,pb,xab)+xab)*(sbar*sbar-4*(pa*pa)*(pb*pb)))*aux;
    aux = Rab(pa,pb,xab)*pa + aux;
    return aux;
}

template <class T>
FVectorT<T> pa_II(FVectorT<T> pa, FVectorT<T> pb, FVectorT<T> k){
    return pa_II(pa,pb,x_ab(pa,pb,k));
}

template <class T>
FVectorT<T> Boost_II(FVectorT<T> pa, FVectorT<T> pb, FVectorT<T> k, FVectorT<T> ki){
    FVectorT<T> Pab = pa + pb - k;
    FVectorT<T> Pab_tilde = pa_II(pa,pb,k) + pb;
    FVectorT<T> out = Pab_tilde;
    out = out * (2*(Pab*ki)/(Pab*Pab));
    FVectorT<T> aux = Pab+Pab_tilde;
    aux = ((aux*ki)/(aux*Pab))*aux;
    return ki - aux + out;
}

template <class T>
void Build_II_Momenta(std::vector<FVectorT<T>> P_DAT, std::vector<FVectorT<T>>* P_TIL, int EMIT, int SPEC, int RADI){
    P_TIL->clear();
    int count = 0;
    for(FVectorT<T> v: P_DAT){
        if(count != RADI) P_TIL->push_back(v);
        count++;
    }
    P_TIL->at(EMIT) = pa_II(P_DAT.at(EMIT),P_DAT.at(SPEC),P_DAT.at(RADI));
    for(unsigned int II=2;II<P_TIL->size();II++){
        P_TIL->at(II) = Boost_II(P_DAT.at(EMIT),P_DAT.at(SPEC),P_DAT.at(RADI),P_DAT.at(II));
    }
    #if TESTMODE
        count = 0;
        std::cout<<"IF Momenta Validation:"<<std::endl;
        for (FVectorT<T> v : *P_TIL){
            std::cout<<"p"<<count+1<<" = ";
            v.print();
            int i = count;
            if (i>=RADI) i++;
            std::cout<<"m"<<count+1<<"^2 = "<<v*v<<"  ("<<P_DAT.at(i)*P_DAT.at(i)<<")"<<std::endl;
            count++;
        }
        std::cout<<std::endl;
    #endif
}

template <class T>
T g_ab_ffb(FVectorT<T> pa, FVectorT<T> pb, FVectorT<T> k, T ma, T mb){
    T xab = x_ab(pa,pb,k);
    T sab = ma*ma+mb*mb+2*(pa*pb);
    if (xab<xab_cut(sab,ma,mb)) return 0;
    T out = 2.0/(1.0-xab);
    out  = out - (1.0+xab);
    out  = out - (xab*(pa*pa)/(pa*k));
    out  = out / (xab*(pa*k));
    return out;   
}

template <class T>
FMatrixT<T> g_ab_bbb(FVectorT<T> pa, FVectorT<T> pb, FVectorT<T> k, T ma, T mb){
    FMatrixT<T> Matrix;
    T xab = x_ab(pa,pb,k);
    FVectorT<T> kproj = k - ((pa*k)/(pa*pb))*pb;
    Matrix.M[0][0] = 1;
    for (int j=1;j<=3;j++) Matrix.M[j][j] = -1;
    Matrix  = (xab*((1/(1-xab))+(1-xab)))*Matrix;
    FMatrixT<T> Aux = TensorProduct(kproj,kproj);
    Aux = (((1-xab)/xab)*((pa*pb)/((k*pa)*(k*pb))))*Aux;
    Matrix = Matrix + Aux;
    return Matrix;    
}

template <class T>
T CurlyG_ab_ffb(T sab, T ma, T mb, T mu, T x, T Ix, T I1){
    
    T Rval = 0;
    T Fx,F1;
    T sab_bar = sab - ma*ma - mb*mb;
    T Lambda_ab = Lambda(sab,ma*ma,mb*mb);
    T LOG_DR = /*log_4pi + */log(mu*mu*sab/(sab_bar*sab_bar));

    if (ma==0.0){
        Fx = (1.0-x)*(1.0-x)-(1.0+x*x)*LOG_DR*Ix/x;
        F1 = -2*LOG_DR*I1;
        Rval += (1.0/(1.0-x))*(Fx-F1);

        Fx = 2.0*(1.0+x*x)*LOG_DR*Ix/x;
        F1 = 4.0*LOG_DR*I1;
        Rval += (log(1.0-x)/(1.0-x))*(Fx-F1);
    }

    else{
        T BETA = sab_bar + 2*ma*ma - sqrt(Lambda_ab);
          BETA = BETA / (sab_bar + 2*ma*ma + sqrt(Lambda_ab));
        T  LOG = log(BETA);

        Fx = (2.0*x+(sab_bar/sqrt(Lambda_ab))*(1.0+x*x)*LOG)*Ix/x;
        F1 = 2.0*(1.0+sab_bar/sqrt(Lambda_ab)*LOG)*I1;
        Rval += (1.0/(1.0-x))*(Fx-F1);
    }
}

template <class T>
void G_ab_ffb(T sab, T ma, T mb, T mu, T* RVAL){

    // TODO: This template only works for T=double due to the gsl_sf_dilog call
 
    T sab_bar = sab - ma*ma - mb*mb;
    T x0 = xab_cut(sab,ma,mb);
    T LOG_DR = /*log_4pi + */log(mu*mu*sab/(sab_bar*sab_bar)) - 2*log(1.0-x0);

    if (ma==0.0){
        RVAL[0] = 1;
        RVAL[1] = - 3.0/2.0 - LOG_DR - x0*(1.0+x0)/2.0;
        RVAL[2] = LOG_DR*LOG_DR - pi2 / 4;
    }

    else{
        T BETA = sab_bar + 2*ma*ma - sqrt(Lambda(sab,ma*ma,mb*mb));
          BETA = BETA / (sab_bar + 2*ma*ma + sqrt(Lambda(sab,ma*ma,mb*mb)));
        T  LOG = log(BETA);
        
        RVAL[0] = 0;
        RVAL[1] = - 1 - sab_bar/Lambda(sab,ma*ma,mb*mb)*LOG;
        RVAL[2] = (2*PolyLog2(1-BETA) + (1.0/2.0)*LOG*LOG + ((sab_bar+2*ma*ma)/(sab_bar))*LOG);
        RVAL[2] = LOG_DR*RVAL[1]-(sab_bar/Lambda(sab,ma*ma,mb*mb))*RVAL[2];
    }
}

template <class T>
void G_ab_bbb(T sab, T ma, T mb, T mu, T* RVAL){

    // TODO: This template only works for T=double due to the gsl_sf_dilog call
 
    T sab_bar = sab - ma*ma - mb*mb;
    T x0 = xab_cut(sab,ma,mb);
    T LOG_DR = /*log_4pi + */log(mu*mu*sab/(sab_bar*sab_bar)) - 2*log(1.0-x0);

    if (ma==0.0){
        RVAL[0] = 1;
        RVAL[1] = - 3.0/2.0 - LOG_DR - x0*(1.0+x0)/2.0;
        RVAL[2] = LOG_DR*LOG_DR - pi2 / 4;
    }

    else{
        T BETA = sab_bar + 2*ma*ma - sqrt(Lambda(sab,ma*ma,mb*mb));
          BETA = BETA / (sab_bar + 2*ma*ma + sqrt(Lambda(sab,ma*ma,mb*mb)));
        T  LOG = log(BETA);
        
        RVAL[0] = 0;
        RVAL[1] = - 1 - sab_bar/Lambda(sab,ma*ma,mb*mb)*LOG;
        RVAL[2] = (2*PolyLog2(1-BETA) + (1.0/2.0)*LOG*LOG + ((sab_bar+2*ma*ma)/(sab_bar))*LOG);
        RVAL[2] = LOG_DR*RVAL[1]-(sab_bar/Lambda(sab,ma*ma,mb*mb))*RVAL[2];
    }
}

//
//  IF & FI Functions and Maps 
//

template <class T>
T x_ia(FVectorT<T> pa, FVectorT<T> pi, FVectorT<T> k){
    
    return ((pa*pi) + (pa*k) - (pi*k)) / ( (pa*pi) + (pa*k) );
}

template <class T>
T z_ia(FVectorT<T> pa, FVectorT<T> pi, FVectorT<T> k){
    
    return (pa*pi) / ( (pa*pi) + (pa*k) );
}

template <class T>
T R_ia(FVectorT<T> pa, FVectorT<T> pi, FVectorT<T> k, T x){
    FVectorT<T> P_ai = pi - pa + k;
    T P_ai_bar = (P_ai*P_ai) - (pa*pa) - (pi*pi);   
    T out = (P_ai_bar + 2*(pa*pa)*x)*(P_ai_bar + 2*(pa*pa)*x);
    out = out - 4*(pa*pa)*(P_ai*P_ai)*x*x;
    out = out / (Lambda((P_ai*P_ai),(pa*pa),(pi*pi)));
    out = sqrt(out);
    return out;  
}

template<class T>
T Ria(T x, T PiaSq, T Ma, T Mi){
    T out  = (PiaSq-Ma*Ma-Mi*Mi+2*Ma*Ma*x);
      out  = out*out;
      out -= 4*Ma*Ma*x*x*PiaSq;
      out /= Lambda(PiaSq,Mi*Mi,Ma*Ma);
      out  = sqrt(out);
      return out;
}

template <class T>
T g_ai_ffb(FVectorT<T> pa, FVectorT<T> pi, FVectorT<T> k, T ma, T mi){
  
    T xai = x_ia(pa,pi,k);
    T zai = z_ia(pa,pi,k);
  
    T Ria = R_ia(pa,pi,k,xai);   
  
    T aux1 = 2.0 / (2.0 - xai - zai );
    T aux2 = (1.0 + xai) * Ria;
    T aux3 = xai*(pa*pa)/(k*pa);
  
    T out = aux1 - aux2 - aux3;
    out = out / ((pa*k)*xai);
    return out;
}

template <class T>
T g_ia_ffb(FVectorT<T> pi, FVectorT<T> pa, FVectorT<T> k, T mi, T ma){
    
    T xia = x_ia(pa,pi,k);
    T zia = z_ia(pa,pi,k);
    
    T out = 2./(2.-xia-zia);
    out = out - 1 - zia - (pi*pi)/(pi*k);
    out = out/(xia*(pi*k));
    
    return out;   
}

// NOTE: Currently g_ia(ai)_bbb are a placeholders and are overloaded to g_ia(ai)_ffb temporarily //
template <class T>
T g_ai_bbb(FVectorT<T> pa, FVectorT<T> pi, FVectorT<T> k, T ma, T mi){
    
    return g_ai_ffb(pa,pi,k,ma,mi);    
}

template <class T>
T g_ia_bbb(FVectorT<T> pi, FVectorT<T> pa, FVectorT<T> k, T mi, T ma){
    
    return g_ia_ffb(pi,pa,k,mi,ma);
}

template <class T>
FVectorT<T> pi_IFFI(FVectorT<T> pa, FVectorT<T> pi, FVectorT<T> k){
  FVectorT<T> P_ia = pi + k - pa;
  FVectorT<T> out1 = pa - ( P_ia*pa / ( P_ia * P_ia ) ) * P_ia ;
  FVectorT<T> out2 = ( ( P_ia*P_ia - pa*pa + pi*pi ) / (2*(P_ia*P_ia) ) ) * P_ia ;
  FVectorT<T> aux = (pi+k);
  T prefactor = sqrt( Lambda(P_ia*P_ia,pa*pa,pi*pi) ) / sqrt( Lambda(aux*aux,P_ia*P_ia,pa*pa));
  return prefactor*out1 + out2;  
}

template <class T>
FVectorT<T> pa_IFFI(FVectorT<T> pa, FVectorT<T> pi, FVectorT<T> k){
  return pi_IFFI(pa,pi,k)- pi - k + pa ;  
}

template <class T>
void Build_IF_Momenta(std::vector<FVectorT<T>> P_DAT, std::vector<FVectorT<T>>* P_TIL, int EMIT, int SPEC, int RADI){
    P_TIL->clear();
    int count = 0;
    for(FVectorT<T> v: P_DAT){
        if(count != RADI) P_TIL->push_back(v);
        count++;
    }
    int e = EMIT;
    int s = SPEC;
    if (EMIT>RADI) e-=1;
    if (SPEC>RADI) s-=1;
    P_TIL->at(e) = pa_IFFI(P_DAT.at(EMIT),P_DAT.at(SPEC),P_DAT.at(RADI));
    P_TIL->at(s) = pi_IFFI(P_DAT.at(EMIT),P_DAT.at(SPEC),P_DAT.at(RADI));
    #if TESTMODE
        count = 0;
        std::cout<<"IF Momenta Validation:"<<std::endl;
        for (FVectorT<T> v : *P_TIL){
            std::cout<<"p"<<count+1<<" = ";
            v.print();
            int i = count;
            if (i>=RADI) i++;
            std::cout<<"m"<<count+1<<"^2 = "<<v*v<<"  ("<<P_DAT.at(i)*P_DAT.at(i)<<")"<<std::endl;
            count++;
        }
        std::cout<<std::endl;
    #endif

}

template <class T>
void Build_FI_Momenta(std::vector<FVectorT<T>> P_DAT, std::vector<FVectorT<T>>* P_TIL, int EMIT, int SPEC, int RADI){
    P_TIL->clear();
    int count = 0;
    for(FVectorT<T> v: P_DAT){
        if(count != RADI) P_TIL->push_back(v);
        count++;
    }
    int e = EMIT;
    int s = SPEC;
    if (EMIT>RADI) e-=1;
    if (SPEC>RADI) s-=1;
    P_TIL->at(e) = pi_IFFI(P_DAT.at(SPEC),P_DAT.at(EMIT),P_DAT.at(RADI));
    P_TIL->at(s) = pa_IFFI(P_DAT.at(SPEC),P_DAT.at(EMIT),P_DAT.at(RADI));
    #if TESTMODE
        std::cout<<"FI Momenta Validation:"<<std::endl;
        count = 0;
        for (FVectorT<T> v : *P_TIL){
            std::cout<<"p"<<count+1<<" = ";
            v.print();
            int i = count;
            if (i>=RADI) i++;
            std::cout<<"m"<<count+1<<"^2 = "<<v*v<<"   ("<<P_DAT.at(i)*P_DAT.at(i)<<")"<<std::endl;
            count++;
        }
        std::cout<<std::endl;
    #endif
}

template <class T>
T Curly_G_ia_ffb(T  P_ia, T mi, T ma, T mu, T x, T Ix, T I1){
    
    T P_ia_bar = P_ia - mi*mi - ma*ma;
    
    T aux1 = 1 - (2*mi*mi*x)/(P_ia_bar*(1-x)) + z(P_ia,ma,mi,x,-1)/2;
    aux1 = aux1 * (-z(P_ia,ma,mi,x,-1));
    aux1 = aux1 - 2*Log( 2 - x - z(P_ia,ma,mi,x,-1));
    
    T aux2 = 1 - (2*mi*mi*x)/(P_ia_bar*(1-x)) + z(P_ia,ma,mi,x,1)/2;
    aux2 = aux2 * (-z(P_ia,ma,mi,x,1));
    aux2 = aux2 - 2*Log( 2 - x - z(P_ia,ma,mi,x,1));
    
    aux1 = aux1 - aux2;
    aux1 = aux1 * (-P_ia_bar)/(Sqrt(Lambda(P_ia,mi*mi,ma*ma))*R_ia(P_ia,ma,mi,x)*(1-x));
    
    return aux1;
       
    
}

template <class T>
T Curly_G_ai_ffb(T  P_ia, T mi, T ma, T mu, T x, T Ix, T I1){
    
    T P_ia_bar = P_ia - mi*mi - ma*ma;
    
    T aux1 = 1 - (2*mi*mi*x)/(P_ia_bar*(1-x)) + z(P_ia,ma,mi,x,-1)/2;
    aux1 = aux1 * (-z(P_ia,ma,mi,x,-1));
    aux1 = aux1 - 2*Log( 2 - x - z(P_ia,ma,mi,x,-1));
    
    T aux2 = 1 - (2*mi*mi*x)/(P_ia_bar*(1-x)) + z(P_ia,ma,mi,x,1)/2;
    aux2 = aux2 * (-z(P_ia,ma,mi,x,1));
    aux2 = aux2 - 2*Log( 2 - x - z(P_ia,ma,mi,x,1));
    
    aux1 = aux1 - aux2;
    aux1 = aux1 * (-P_ia_bar)/(Sqrt(Lambda(P_ia,mi*mi,ma*ma))*R_ia(P_ia,ma,mi,x)*(1-x));
    
    return aux1;
       
    
}

template <class T>
void Build_FI_Tilde_Momenta(T sqrts, T* rand, T Ma, T Mb, T Mi, T Mia, FVectorT<T>& pa, FVectorT<T>& pb, FVectorT<T>& pi, FVectorT<T>& Kia, T& Jac){

    // The convention for rand is {x,Pia,phi} ...

    T x = rand[0];

    T Ei = (sqrts*sqrts+Mi*Mi-Mia*Mia)/(2*sqrts);
    T Ea = (sqrts*sqrts+Ma*Ma-Mb*Mb)/(2*sqrts);
    T Pa = sqrt(Lambda(sqrts*sqrts,Ma*Ma,Mb*Mb))/(2*sqrts);
    T Pi = sqrt(Lambda(sqrts*sqrts,Mi*Mi,Mia*Mia))/(2*sqrts);
    T PiaSq_min = Ma*Ma+Mi*Mi-2*Ea*Ei-2*Pi*Pa;

    T PiaSq = (1-rand[1])*PiaSq_min;
    T PiaBar = PiaSq-Mi*Mi-Ma*Ma;

    T s_tilde  = x*(sqrts*sqrts-Ma*Ma-Mb*Mb)+(PiaBar+2*Ma*Ma*x)*(Mb*Mb+PiaSq-Mia*Mia)/(2*PiaSq);
      s_tilde /= Ria(x,PiaSq,Ma,Mi);
      s_tilde -= (PiaSq+Ma*Ma-Mi*Mi)*(Mb*Mb+PiaSq-Mia*Mia)/(2*PiaSq);
      s_tilde += Ma*Ma+Mb*Mb;

    Ei = (s_tilde+Mi*Mi-Mia*Mia)/(2*sqrt(s_tilde));
    Ea = (s_tilde+Ma*Ma-Mb*Mb)/(2*sqrt(s_tilde));
    Pa = sqrt(Lambda(s_tilde,Ma*Ma,Mb*Mb))/(2*sqrt(s_tilde));
    Pi = sqrt(Lambda(s_tilde,Mi*Mi,Mia*Mia))/(2*sqrt(s_tilde));
    T cos_i = (PiaSq - Ma*Ma - Mi*Mi + 2*Ei*Ea)/(2*Pa*Pi);

    FVectorT<T> P_tilde(sqrt(s_tilde),0,0,0);
    T Mass[2] = {Mia,Mi};
    T Rand[2] = {(cos_i+1)/2,rand[2]};
    FVectorT<T> Mom[2];
    T J=1;

    Recursive_PSP(P_tilde,2,Mom,Mass,Rand,J);
    pi = Mom[1];
    Kia = Mom[0];
    Jac=J;

    Rand[0]=0.0;
    Rand[1]=0.0;
    Mass[0]=Ma;
    Mass[1]=Mb;
    Recursive_PSP(P_tilde,2,Mom,Mass,Rand,J);
    pa=Mom[0];
    pb=Mom[1];

}

template <class T>
void G_ia_ffb(T Pia, T mi, T ma, T mu, T* RVAL){

    if (mi==0){
        RVAL[0] = 0;
        RVAL[1] = 0;
        RVAL[2] = 0;
    }

    else{

    }

}

template <class T>
void G_ai_ffb(T Pia, T ma, T mi, T mu, T* RVAL){

    if (ma==0){
        RVAL[0] = 0;
        RVAL[1] = 0;
        RVAL[2] = 0;
    }

    else{
        
    }

}

template <class T>
void G_ia_bbb(T Pia, T mi, T ma, T mu, T* RVAL){

    RVAL[0] = 0;
    RVAL[1] = 0;
    RVAL[2] = 0;
}

template <class T>
void G_ai_bbb(T Pia, T ma, T mi, T mu, T* RVAL){

    RVAL[0] = 0;
    RVAL[1] = 0;
    RVAL[2] = 0;
}


// 
//  FF Functions and Maps
//

template <class T>
T y_ij(FVectorT<T> pi,FVectorT<T> pj, FVectorT<T> k){
    T aux = pi*k;
           aux = aux / (pi*pj+pi*k+pj*k);
    return aux;
}

template <class T>
T z_ij(FVectorT<T> pi,FVectorT<T> pj, FVectorT<T> k){
    T aux = pi*pj;
           aux = aux / (pi*pj+pj*k);
    return aux;
}

template <class T>
T R_ij(FVectorT<T> pi, FVectorT<T> pj, FVectorT<T> k,T y){
    FVectorT<T> Pij = pi + pj + k;
    T Pijbar = Pij*Pij - pi*pi - pj*pj;
    T aux = (2*(pj*pj)-Pijbar*(1.0-y));
           aux = aux*aux;
           aux = aux - 4*(Pij*Pij)*(pj*pj);
           aux = aux / Lambda(Pij*Pij,pi*pi,pj*pj);
           aux = sqrt(aux);
           return aux;
}

template <class T>
T g_ij_ffb(FVectorT<T> pi, FVectorT<T> pj, FVectorT<T> k, T mi, T mj){
    T zij = z_ij(pi,pj,k);
    T yij = y_ij(pi,pj,k);
    T aux = zij*(1.0-yij);
           aux = 1.0 - aux;
           aux = 2.0 / aux;
           aux = aux - (1.0+zij);
           aux = aux - (pi*pi)/(pi*k);
           aux = aux / (R_ij(pi,pj,k,yij)*(pi*k));
           return aux;      
}

template <class T>
T g_ij_bbb(FVectorT<T> pi, FVectorT<T> pj, FVectorT<T> k){
    return g_ij_ffb(pi,pj,k);  
}

template <class T>
FVectorT<T> pj_FF(FVectorT<T> pi, FVectorT<T> pj, FVectorT<T> k){
    FVectorT<T> Pij = pi + pj + k;
    T yij = y_ij(pi,pj,k);
    FVectorT<T> aux = ((Pij*pj)/(Pij*Pij))*Pij;
           aux = pj - aux;
           aux = aux *(1.0/R_ij(pi,pj,k,yij));
           aux = aux + ((Pij*Pij+pj*pj-pi*pi)/(2*(Pij*Pij)))*Pij;
           return aux;           
}

template <class T>
FVectorT<T> pi_FF(FVectorT<T> pi, FVectorT<T> pj, FVectorT<T> k){
    return pi + pj + k - pj_FF(pi,pj,k);
}

template <class T>
void Build_FF_Momenta(std::vector<FVectorT<T>> P_DAT, std::vector<FVectorT<T>>* P_TIL, int EMIT, int SPEC, int RADI){
    P_TIL->clear();
    int count = 0;
    for(FVectorT<T> v: P_DAT){
        if(count != RADI) P_TIL->push_back(v);
        count++;
    }
    P_TIL->at(EMIT) = pi_FF(P_DAT.at(EMIT),P_DAT.at(SPEC),P_DAT.at(RADI));
    P_TIL->at(SPEC) = pj_FF(P_DAT.at(EMIT),P_DAT.at(SPEC),P_DAT.at(RADI));
    // for(unsigned int II=0;II<P_TIL->size();II++){
    //     if ( II!=EMIT && II!=SPEC ){
    //         P_TIL->at(II) = P_DAT.at(II);
    //     }
    // }
}

template <class T>
void G_ij_ffb(T sij, T mi, T mj, T mu, T* RVAL){

    RVAL[0] = 0;
    RVAL[1] = 0;
    RVAL[2] = 0;
}

#endif
