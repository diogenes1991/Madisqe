#include <cstdio>
#include <iostream>
#include "Input.h"
#include "XSection_Integrator.h"
#include "ProductionAdapters.h"

void ShowLetterHead(){
    std::cout<<"###################################################################"<<std::endl;
    std::cout<<"                                                                   "<<std::endl;
    std::cout<<"                                                                   "<<std::endl;
    std::cout<<"          __  __               _   _                               "<<std::endl;
    std::cout<<"         |  \\/  |   __ _    __| | (_)  ___    __ _    ___         "<<std::endl;
    std::cout<<"         | |\\/| |  / _` |  / _` | | | / __|  / _` |  / _ \\       "<<std::endl;
    std::cout<<"         | |  | | | (_| | | (_| | | | \\__ \\ | (_| | |  __/       "<<std::endl;
    std::cout<<"         |_|  |_|  \\__,_|  \\__,_| |_| |___/  \\__, |  \\___|     "<<std::endl; 
    std::cout<<"                                                |_|                "<<std::endl;
    std::cout<<"                                                                   "<<std::endl;
    std::cout<<"                                                                   "<<std::endl;
    std::cout<<"                           Version 1.0.0                           "<<std::endl;
    std::cout<<"                           by D.Figueroa                           "<<std::endl;
    std::cout<<"                                                                   "<<std::endl;
    std::cout<<"                                                                   "<<std::endl;
    std::cout<<"###################################################################"<<std::endl;
}

class CommandHandler{

    public:

        std::string Name;
        std::unordered_map<std::string,int> CommandMap = {{"Exit",-1}};

        CommandHandler(){};
        ~CommandHandler(){};

        int GetCommand(std::string Command){
            int CommandInt;
            try{CommandInt = CommandMap.at(Command);}
            catch(const std::out_of_range& oor){CommandInt = -2;}
            return CommandInt;
        }

        void BeginLoop(){
            std::string Command;
            bool Stay = true;
            do{
                std::cout<<Name<<" \\> ";
                std::cin>>Command;
                Stay = HandleCommand(Command);
            
            } while(Stay);
        }

        virtual bool HandleCommand(std::string Command) = 0;

};

class MatrixElementTester : public CommandHandler{

    std::unique_ptr<Model> model;
    std::unique_ptr<OLP> NLOX_Proc;
    std::unique_ptr<OLP> RECOLA_Proc;
    std::unique_ptr<VirtualIntegrands> NLOX_Virt;
    std::unique_ptr<VirtualIntegrands> RECOLA_Virt;

    static constexpr double sqrts = 13000;
    static constexpr double fixed_mu = 1000;
    static const int NRandom = 3*NextV-10;
    double r[NRandom];
    
    public:

        std::string Order;
        std::string Coupling;
        std::string Channel;

        MatrixElementTester(){
            Name = "Madisqe Tester";
            CommandMap.insert({"SetAll",0});
            CommandMap.insert({"SetChannel",1});
            CommandMap.insert({"SetOrder",2});
            CommandMap.insert({"SetCoupling",3});
            CommandMap.insert({"SetRandom",4});
            CommandMap.insert({"Test",5});
            model.reset(new Model);
            NLOX_Proc = MakeOLP("NLOX", model.get());
            RECOLA_Proc = MakeOLP("RECOLA", model.get());
            NLOX_Virt.reset(new VirtualIntegrands(NLOX_Proc.get(), model.get()));
            RECOLA_Virt.reset(new VirtualIntegrands(RECOLA_Proc.get(), model.get()));
            Start();
        }

        void Start(){
            std::cout<<"Entering Testing Envionment"<<std::endl;
            BeginLoop();
        }

        bool HandleCommand(std::string Command){
            bool Stay = true;
            int CommandInt = GetCommand(Command);
            
            switch(CommandInt){
                case 0:
                    SetAll();
                    break;
                case 1:
                    SetChannel();
                    break;
                case 2:
                    SetOrder();
                    break;
                case 3:
                    SetCoupling();
                    break;
                case 4:
                    SetRandom();
                    break;
                case 5:
                    Test();
                    break;
                case -1:
                    std::cout<<"Exiting Testing Environment"<<std::endl;
                    Stay = false;
                    break;
                default:
                    std::cout<<"Unrecognized Option, the recognized ones are:"<<std::endl;
                    for(auto C : CommandMap)std::cout<<C.first<<std::endl;
            }

            return Stay;
        }

        void SetChannel(){
            std::cout<<"Channel \\>";
            std::cin>>Channel;
        }

        void SetOrder(){    
            std::cout<<"Order \\>";
            std::cin>>Order;
        }

        void SetCoupling(){
            std::cout<<"Coupling \\>";
            std::cin>>Coupling;
        }

        void SetAll(){
            SetChannel();
            SetOrder();
            SetCoupling();
        }

        void SetRandom(){
            std::cout<<"Enter "<<NRandom<<" random numbers \\>"<<std::endl;
            for(int i=0;i<NRandom;i++){
                std::cout<<"r["<<i<<"] \\>  ";
                std::cin>>r[i];
            }
        }

        void Test(){
            try{
                std::string timen,timer;
                double rvaln,rvalr;
                FVector Mom[NextV];
                Clock C;
                NLOX_Virt->Call(Order,Channel,Coupling,sqrts,r,fixed_mu,&rvaln);
                timen = C.GetTime();
                C.Reset();
                RECOLA_Virt->Call(Order,Channel,Coupling,sqrts,r,fixed_mu,&rvalr);
                timer = C.GetTime();
                NLOX_Virt->GetMomenta(Channel,Mom);
                std::cout<<"Testing "<<Channel<<" @ "<<Coupling<<std::endl;
                std::cout<<"PSP for this comparison:"<<std::endl;
                for(int i=0;i<NextV;i++){std::cout<<"p"<<i+1<<" = ";Mom[i].print();}
                std::cout<<"NLOX   = "<<rvaln<<" ( "<<timen<<" )"<<std::endl;
                std::cout<<"RECOLA = "<<rvalr<<" ( "<<timer<<" )"<<std::endl;
            }
            catch(const char* se){
                std::cout<<"Catching an instance of \""<<se<<"\" Error"<<std::endl;
            }

        }
};

class XSectionTester : public Input{

    std::unique_ptr<Model> model;
    std::unique_ptr<OLP> Provider;
    std::unique_ptr<PDF_Set> PDF;
    std::unique_ptr<XSection_Integrator> XSec_Int;

    public:

        Montecarlo_Integrator::Specifications MC_SP;
        XSection_Integrator::XSection_Selector XS;

        XSectionTester(std::string InputFileName){
            
            LoadInput(InputFileName,InputFile);
            
            ShowLetterHead();
            
            std::cout<<"###################################################################"<<std::endl;
            std::cout<<"                                                                   "<<std::endl;
            std::cout<<"              Settings Loaded                                      "<<std::endl;
            std::cout<<"                                                                   "<<std::endl;
            
            for (auto Setting : InputFile){
                std::cout<<"           "<< Setting.first << " : " << Setting.second   <<std::endl;
            }

            std::cout<<"                                                                   "<<std::endl;
            std::cout<<"###################################################################"<<std::endl;
            
            std::string PDFSet       = InputFile.at("PDFSet");
            std::string ProviderName = InputFile.at("OLP");
            std::string Integrator   = InputFile.at("Integrator");
            
            MC_SP.Method    = InputFile.at("Method");
            MC_SP.MaxEval   = stoi(InputFile.at("NEvaluations"));
            MC_SP.NStart    = stoi(InputFile.at("NStart"));
            MC_SP.NIncrease = stoi(InputFile.at("NIncrease"));
            
            XS.Integrand = InputFile.at("Integrand");
            XS.Channel   = InputFile.at("Channel");
            XS.Coupling  = InputFile.at("Coupling");
                
            double sqrts = stod(InputFile.at("sqrts"));
            double muRen = stod(InputFile.at("muRen"));
            double muFac = stod(InputFile.at("muFac"));

            model.reset(new Model);
            Provider = MakeOLP(ProviderName, model.get());
            PDF = MakePDF(PDFSet);
            XSec_Int.reset(new XSection_Integrator(
                model.get(), Provider.get(), PDF.get(), MakeIntegratorFactory(Integrator)));
            XSec_Int->SetScales(sqrts, muRen, muFac);
        }

        void TestXSection(){
            try {
                XSec_Int->ComputeXSection(XS,MC_SP);
            }
            catch(const char* err){
                std::cout<<"Catching an instance of \""<<err<<"\" error"<<std::endl;
            }
            
        }
};

class Madisqe : public CommandHandler{

    public:

        Madisqe(){
            Name = "Madisqe";
            CommandMap.insert({"Test_ME",0});
            CommandMap.insert({"Test_XSec",1});
            BeginLoop();
        }

        bool HandleCommand(std::string Command){
            bool Stay = true;

            int CommandInt = GetCommand(Command);
            
            switch(CommandInt){
                case 0:
                    TestMatrixElements();
                    break;
                case 1:
                    TestXSection();
                    break;
                case -1:
                    std::cout<<"Exiting Testing Environment"<<std::endl;
                    Stay = false;
                    break;
                default:
                    std::cout<<"Unrecognized Option, the recognized ones are:"<<std::endl;
                    for(auto C : CommandMap)std::cout<<C.first<<std::endl;
            }

            return Stay;
        }

        void TestMatrixElements(){
            MatrixElementTester MET;
        }

        void TestXSection(){
            XSectionTester * XST = NULL;
            std::string InFile;
            std::cout<<"Please specify an input file for the Xsection Run: ";
            std::cin >> InFile;
            try{
                XST = new XSectionTester(InFile);
            }
            catch(const char* Err){
                std::cout<<"Catching an instance of \""<<Err<<"\" error"<<std::endl;
            }

            XST->TestXSection();
            delete XST;
        }

};

#define NEW_MODE 1

int main(int argc, char* argv[]){

    std::cout.precision(16);
    Madisqe M;

    return 0;
}