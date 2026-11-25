"""Provider adapters and C++ process source generation."""

import os

from OLP import NLOX_OLP, RECOLA_OLP
from Template import Template
from Utilities import CopyFile, MakeDir


class ProcessGeneration:
    def WriteModel(self):
        MOD_DICT = {'Build Model' : '' ,\
                    'NParticles'  : '' ,\
                    }

        TAB4 = '    '
        TAB8 = TAB4+'    '

        MOD_DICT['NParticles'] += str(len(self.Model.Fundamentals))

        for Particle in self.Model.Fundamentals:
            P = self.Model.Fundamentals[Particle]
            Charge = '0'
            if 'Charge' in P.sym:
                ##
                ## The charges in SandardModel have a relative factor of 3 with respect to the real world
                ## this is to enforce charge conservation using integers
                ##
                Charge = str(P.sym['Charge'])+'/3'
            MOD_DICT['Build Model'] += TAB8+'Particle '+P.nam+' = Particle("'+P.nam+'",0.0,0.0,'+Charge+','+str(P.pid)+');\n'


        MODEL = Template(self.TplDir+'/Model_tpl.h',self.SrcDir+'/Code/Model.h',MOD_DICT)
        MODEL.Write()

    def BuildOLP(self,GenerateCode):

        ## Here we will collect the Channels
        ## and pass them to the OLP Schedulers
        ## and Interface constructors to weave
        ## it all up

        self.CollectChannels()

        ##
        ##  Generate code using NLOX : Since NLOX is an analytical code
        ##  we fisrt generate the source code and then build the OLP interface
        ##

        self.nlox_process = self.TplDir+'/nlox_process_tpl.h'
        self.nlox_olp = self.TplDir+'/NLOX_OLP_tpl.h'
        self.NLOX_OLP = NLOX_OLP(self.nlox,self.Virts,self.Reals,self.Borns,self.Model,self.seed_tpl,self.nlox_process,self.nlox_olp,self.SrcDir)
        self.NLOX_OLP.WriteSeeds()
        if GenerateCode:
            self.NLOX_OLP.GenerateCode()
            self.NLOX_OLP.GenerateInterface()
        self.NLOX_OLP.WriteOLPClass()

        ##
        ##  Generate RECOLA inerface : Since RECOLA is numerical
        ##  we simply need to write the OLP interface and the actual
        ##  generation of code will be done at runtime
        ##

        self.recola_olp = self.TplDir+'/RECOLA_OLP_tpl.h'
        self.RECOLA_OLP = RECOLA_OLP(self.recola,self.Virts,self.Reals,self.Borns,self.Model,self.recola_olp,self.SrcDir)
        self.RECOLA_OLP.WriteOLPClass()

    ##
    ##  Build the Interface
    ##

    def CreateDirectories(self):
        MakeDir(self.SrcDir)
        MakeDir(self.SrcDir+'/NLOX_Process')
        MakeDir(self.SrcDir+'/Code')

    def BuildInterface(self):

        ##
        ## OLD Deprecated, this lightens the load on generated processes.
        ## They now all point to the same directory inside src.
        ## This could possibly impede the swift test at a PSP like we were
        ## doing by simply editting Virtual_Structure's BGenerate to be
        ## a cosntant. This also makes it more difficult to have process dependent
        ## PSP remappings.
        ##
        ## The solution to this would be to have an implementation file per process
        ## to define an in-house PSP Generator, then each integrand can use the
        ## implementation it pleases, this would be controlled by Vrtual.h and Real.h
        ##
        ## The makefiles have also been edited for this reason
        ##

        ## CODEFILES = ['Dipole_Structure.h','Dipole_Definitions.h', \
        ##              'PSP_Generator.h','Utilities.h','Virtual_Structure.h',\
        ##              'Montecarlo_Integrator.h','GSL_Integrator.h','CUBA_Integrator.h', \
        ##              'PDF_Set.h','LHA_PDF.h','Kinematics.h','Analysis.h', \
        ##              'Dummy_PDF.h' ,\
        ##              'Constants.h','XSection.h','XSection_Integrator.h',\
        ##              'Integrand.h','OLP.h','Four_Vector.h','Input.h']

        INPUTFILES = ['Run_Settings.input']

        TOPLAYERFILES  = ['Main.cpp','Analysis.cpp','Model.cpp']

        ## for file in CODEFILES:
        ##     CopyFile(self.IntDir+'/'+file,self.SrcDir+'/Code/'+file)

        for file in TOPLAYERFILES:
            CopyFile(self.IntDir+'/'+file,self.SrcDir+'/'+file)

        for file in INPUTFILES:
            CopyFile(self.Inputs+'/'+file,self.SrcDir+'/'+file)

        self.LoadPaths()
        self.paths['NLOX PATH']=self.config['NLOX PATH'][0]
        self.paths['RECOLA PATH']=self.config['RECOLA PATH'][0]
        self.paths['MADISQE PATH']=os.getcwd()

        Makefile = Template(self.TplDir+'/makefile',self.SrcDir+'/makefile',self.paths)
        Makefile.Write()

    ##
    ##  Build the Integrands Classes: Virtual and Real
    ##

    def BuildRealIntegrands_New(self):
        for DipoleStructure in self.DipoleStructures:
            ChlDir = self.SrcDir+'/Real/'+str(self.DipoleStructures[DipoleStructure].Radiative)
            MakeDir(ChlDir)
            self.DipoleStructures[DipoleStructure].Show(self.TplDir,ChlDir)


    def BuildRealIntegrands(self):

        ##
        ##  This function has waaaay too many reponsabilities....
        ##

        TAB3 = '    '
        TAB6 = TAB3+TAB3
        TAB9 = TAB6+TAB3

        INTDICT = {'Include Integrands' : '' ,\
                   'nRadiative'         : str(len(self.RadiProc.subproc)) ,\
                   'Integrand Catalogue': ''}

        Count = 0
        for Radiative in self.RadiProc.subproc:

            ClassName = Radiative+'_Real'

            INTDICT['Include Integrands'] += '#include "../Real/'+Radiative+'/'+ClassName+'.h"\n'
            INTDICT['Integrand Catalogue'] += TAB9+'Channels['+str(Count)+'] = new '+ClassName+'(*Provider,*model);\n'
            INTDICT['Integrand Catalogue'] += TAB9+'ChannelMap.insert({"'+Radiative+'",'+str(Count)+'});\n'

            Count += 1
            ChlDir = self.SrcDir+'/Real_Old/'+Radiative
            MakeDir(ChlDir)

            DICT={'SubProcHeader'    : '' ,\
                  'SubProcConst'     : '' ,\
                  'SubProcName'      : '' ,\
                  'Next'             : str(self.RadiProc.nex) ,\
                  'SubProcMat'       : '' ,\
                  'SubProcSub'       : '' ,\
                  'SubProcPlu'       : '' ,\
                  'SubProcEnd'       : '' ,\
                  'Model'            : self.Model.Name}

            DICT['SubProcHeader'] = Radiative.upper()
            DICT['SubProcName'] = ClassName

            ##
            ##  Integrands constructor
            ##

            count = 0
            for particle in self.RadiProc.subproc[Radiative]:
                DICT['SubProcConst'] += TAB3+'Masses['+str(count)+'] = model->'+particle.nam+'.Mass;\n'
                DICT['SubProcConst'] += TAB3+'PID['+str(count)+'] = model->'+particle.nam+'.PID;\n'
                count += 1

            DICT['SubProcConst'] += '\n'
            DICT['SubProcConst'] += TAB3+'nBorn = '+str(len(self.Linked[Radiative]))+';\n'
            DICT['SubProcConst'] += TAB3+'BornMasses = new double* [nBorn];\n'
            DICT['SubProcConst'] += TAB3+'BornPID = new int* [nBorn];\n'
            DICT['SubProcConst'] += TAB3+'for(int i=0;i<nBorn;i++) BornPID[i]= new int[NextR-1];\n\n'
            DICT['SubProcConst'] += TAB3+'for(int i=0;i<nBorn;i++) BornMasses[i]= new double[NextR-1];\n\n'

            Bcount = 0
            for Born in self.Linked[Radiative]:
                count = 0
                DICT['SubProcConst'] += TAB3+'BornMap.insert({"'+Born+'",'+str(Bcount)+'});\n'
                for particle in self.Linked[Radiative][Born]:
                    DICT['SubProcConst'] += TAB3+'BornMasses['+str(Bcount)+']['+str(count)+']= model->'+particle.nam+'.Mass;\n'
                    DICT['SubProcConst'] += TAB3+'BornPID['+str(Bcount)+']['+str(count)+']= model->'+particle.nam+'.PID;\n'
                    count += 1
                Bcount += 1

            RadiCPS = self.Model.GetCPS(self.RadiProc.subproc[Radiative])
            Next = self.RadiProc.nex

            ##
            ##   Split all dipoles into EWK and QCD
            ##

            EWKDipoles = []
            QCDDipoles = []
            for dipole in self.DipoleTree[Radiative]:
                if dipole['DIPTYP']=='EWK':
                    EWKDipoles.append(dipole)
                elif dipole['DIPTYP']=='QCD':
                    QCDDipoles.append(dipole)

            def BORNTAG(Dipole):
                return Dipole['SBORNTAG']
            EWKDipoles.sort(key=BORNTAG)
            QCDDipoles.sort(key=BORNTAG)

            DIPDIC = {'II':'ab','IF':'ai','FI':'ia','FF':'ij'}

            ##
            ##  The DipoleTree has in it all the information we require:
            ##  The postprocessing of the Dipole tree is as follows:
            ##   - Fisrt we split the tree in two: QCD and EWK, mainly beca
            ##
            ##

            CPHEAD = ''

            for CP in RadiCPS:

                if len(CPHEAD):
                    CPHEAD = TAB3+'else if (cp =="'+CP+'"){\n'
                else:
                    CPHEAD = TAB3+'if (cp =="'+CP+'"){\n'

                CACHEDTAG = ''

                if len(EWKDipoles):
                    CPHEAD += TAB6+'double born[3];\n'
                if len(QCDDipoles):
                    CPHEAD += TAB6+'double borncc['+str(1+(self.RadiProc.nex-1)*(self.RadiProc.nex-2)//2)+'];\n'
                    CPHEAD += TAB6+'ColorAndSpinMatrix BornCCSC('+str(1+(self.RadiProc.nex-1)*(self.RadiProc.nex-2)//2)+');\n'


                DICT['SubProcSub'] += CPHEAD
                DICT['SubProcSub'] += TAB6+'i = Proc->AmpMap.at("'+Radiative+'");\n'
                DICT['SubProcSub'] += TAB6+'for(int j=0;j<NextR;j++){pp[5*j]=p.at(j).p0;pp[5*j+1]=p.at(j).p1;pp[5*j+2]=p.at(j).p2;pp[5*j+3]=p.at(j).p3;pp[5*j+4]=0.0;}\n'
                DICT['SubProcSub'] += TAB6+'Proc->evaluate_alpha(i,"tree_tree","'+CP+'",pp,'+str(Next)+',mu,radiative,&acc);\n'
                DICT['SubProcSub'] += TAB6+'*rval = radiative[2];\n\n'

                DICT['SubProcPlu'] += CPHEAD

                DICT['SubProcEnd'] += CPHEAD
                DICT['SubProcEnd'] += TAB6+'double aux[3];\n'

                ##
                ##   EWK Dipoles
                ##

                for Emitter in EWKDipoles:
                    for Spectator in EWKDipoles:
                        if Emitter == Spectator:
                            continue

                        ## This throws away any CP combination that has no Born counterpart
                        if RadiCPS[CP]['ae'] <= 0:
                            continue
                        CPB = 'as'+str(RadiCPS[CP]['as'])+'ae'+str(RadiCPS[CP]['ae']-1)

                        K = []

                        try:
                            K = [ i for i in Emitter['IJ'] if i in Spectator['IJ']][0]
                        except:
                            # print Emitter['NAME'],Spectator['NAME'],'-> Skipped: Different Radiation'
                            continue

                        I = [ i for i in Emitter['IJ'] if i != K ][0]
                        J = [ i for i in Spectator['IJ'] if i != K ][0]

                        QI=0
                        QJ=0

                        SigmaIJ = ( -1 if Emitter['SUBTYP'] != Spectator['SUBTYP'] else 1 )

                        try:
                            QI = self.RadiProc.subproc[Radiative][I].sym['Charge']
                            QJ = self.RadiProc.subproc[Radiative][J].sym['Charge']
                        except:
                            continue

                        if CACHEDTAG != Emitter['SBORNTAG']:
                            AMPMAPLINE   = TAB6+'i = Proc->AmpMap.at("'+Emitter['SBORNTAG']+'");\n'
                            BORNMAPLINE  = TAB6+'j = BornMap.at("'+Emitter['SBORNTAG']+'");\n'
                            BORNMAPLINE += TAB6+'BGenerate("'+Emitter['SBORNTAG']+'",sqrts,rand,&J);\n'
                            BORNMAPLINE += TAB6+'for(int j=0;j<NextR-1;j++){pp[5*j+0]=BornMomenta[j].p0;pp[5*j+1]=BornMomenta[j].p1;pp[5*j+2]=BornMomenta[j].p2;pp[5*j+3]=BornMomenta[j].p3;pp[5*j+4]=0.0;}\n'
                            CACHEDTAG = Emitter['SBORNTAG']
                        else:
                            AMPMAPLINE = ''
                            BORNMAPLINE = ''

                        ##
                        ## There is a factor of 3 between each charge in StandardModel.py vs RealWorld!
                        ## Hence the (1/9) for squared charges.
                        ## StandardModel uses Charges*3 to enforce charge conservation using integers.
                        ##

                        AMPMAPLINE  += TAB6+'DipFac = '+str(SigmaIJ*QI*QJ)+'.0/9*EWKFac;\n'

                        ##
                        ##  Subtracted Function
                        ##

                        PREFIX = Emitter['SUBTYP']+Spectator['SUBTYP']
                        DIPFUN = DIPDIC[PREFIX]
                        TYP = Emitter['PARTYPS']

                        DICT['SubProcSub'] += AMPMAPLINE
                        DICT['SubProcSub'] += TAB6+'Build_'+PREFIX+'_Momenta(p,&p_tilde,'+str(I)+','+str(J)+','+str(K)+');\n'
                        DICT['SubProcSub'] += TAB6+'for(int j=0;j<NextR-1;j++){pp_tilde[5*j+0]=p_tilde.at(j).p0;pp_tilde[5*j+1]=p_tilde.at(j).p1;pp_tilde[5*j+2]=p_tilde.at(j).p2;pp_tilde[5*j+3]=p_tilde.at(j).p3;pp_tilde[5*j+4]=0.0;}\n'
                        DICT['SubProcSub'] += TAB6+'Proc->evaluate_alpha(i,"tree_tree","'+CPB+'",pp_tilde,'+str(Next-1)+',mu,born,&acc);\n'
                        DICT['SubProcSub'] += TAB6+'*rval += DipFac*g_'+DIPFUN+'_'+TYP+'(p['+str(I)+'],p['+str(J)+'],p['+str(K)+'],Masses['+str(I)+'],Masses['+str(J)+'])*born[2];\n\n'

                        ##
                        ##  Plus Distribution
                        ##

                        DICT['SubProcPlu'] += AMPMAPLINE
                        DICT['SubProcPlu'] += BORNMAPLINE
                        DICT['SubProcPlu'] += TAB6+'Invariant = BornMasses[j]['+str(I)+']*BornMasses[j]['+str(I)+']'\
                                                              '+ BornMasses[j]['+str(J)+']*BornMasses[j]['+str(J)+']'\
                                                              +('+' if (PREFIX=='II'or PREFIX=='FF') else '-')+\
                                                              '2*(BornMomenta['+str(I)+']*BornMomenta['+str(J)+']);\n'
                        DICT['SubProcPlu'] += TAB6+'Proc->evaluate_alpha(i,"tree_tree","'+CPB+'",pp,'+str(Next-1)+',mu,born,&acc);\n'
                        DICT['SubProcPlu'] += TAB6+'CurlyG_'+DIPFUN+'_'+TYP+'(Invariant,BornMasses[j]['+str(I)+'],BornMasses[j]['+str(J)+'],mu,aux);\n'
                        DICT['SubProcPlu'] += TAB6+'for(int k=0;k<=2;k++) rval[k] += DipFac*aux[k]*born[2];\n\n'
                        DICT['SubProcPlu'] += TAB6+';\n'

                        ##Channel
                        ##  Endpoint Function
                        ##

                        DICT['SubProcEnd'] += AMPMAPLINE
                        DICT['SubProcEnd'] += BORNMAPLINE
                        DICT['SubProcEnd'] += TAB6+'Invariant = BornMasses[j]['+str(I)+']*BornMasses[j]['+str(I)+']'\
                                                              '+ BornMasses[j]['+str(J)+']*BornMasses[j]['+str(J)+']'\
                                                              +('+' if (PREFIX=='II'or PREFIX=='FF') else '-')+\
                                                              '2*(BornMomenta['+str(I)+']*BornMomenta['+str(J)+']);\n'
                        DICT['SubProcEnd'] += TAB6+'Proc->evaluate_alpha(i,"tree_tree","'+CPB+'",pp,'+str(Next-1)+',mu,born,&acc);\n'
                        DICT['SubProcEnd'] += TAB6+'G_'+DIPFUN+'_'+TYP+'(Invariant,BornMasses[j]['+str(I)+'],BornMasses[j]['+str(J)+'],mu,aux);\n'
                        DICT['SubProcEnd'] += TAB6+'for(int k=0;k<=2;k++) rval[k] += DipFac*aux[k]*born[2];\n\n'

                ##
                ##  QCD Dipoles
                ##

                for Emitter in QCDDipoles:
                    for Spectator in QCDDipoles:
                        if Emitter == Spectator:
                            continue

                        ## This throws away any CP combination that has no Born counterpart
                        if RadiCPS[CP]['as'] <= 0:
                            continue
                        CPB = 'as'+str(RadiCPS[CP]['as']-1)+'ae'+str(RadiCPS[CP]['ae'])

                        K = []
                        try:
                            K = [ i for i in Emitter['IJ'] if i in Spectator['IJ']][0]
                        except:
                            continue

                        I = [ i for i in Emitter['IJ'] if i != K ][0]
                        J = [ i for i in Spectator['IJ'] if i != K ][0]

                        FIRST = min(I,J)
                        SECON = max(I,J)

                        ## Offset to shift the color-correlator counter to the correct value

                        if K < FIRST:
                            FIRST -= 1
                        if K < SECON:
                            SECON -= 1

                        if CACHEDTAG != Emitter['SBORNTAG']:
                            AMPMAPLINE = TAB6+'i = Proc->AmpMap.at("'+Emitter['SBORNTAG']+'");\n'
                            BORNMAPLINE  = TAB6+'j = BornMap.at("'+Emitter['SBORNTAG']+'");\n'
                            BORNMAPLINE += TAB6+'BGenerate("'+Emitter['SBORNTAG']+'",sqrts,rand,&J);\n'
                            BORNMAPLINE += TAB6+'for(int j=0;j<NextR-1;j++){pp[5*j+0]=BornMomenta[j].p0;pp[5*j+1]=BornMomenta[j].p1;pp[5*j+2]=BornMomenta[j].p2;pp[5*j+3]=BornMomenta[j].p3;pp[5*j+4]=0.0;}\n'
                            CACHEDTAG = Emitter['SBORNTAG']
                        else:
                            AMPMAPLINE = ''
                            BORNMAPLINE = ''

                        ## This unflattens a symmetric (non-repeating) matrix, which borncc is

                        WHICHCC = (self.RadiProc.nex-2)*FIRST + SECON - FIRST - FIRST*(FIRST-1)//2

                        PREFIX = Emitter['SUBTYP']+Spectator['SUBTYP']
                        DIPFUN = DIPDIC[PREFIX]
                        # TYP = ('fermion' if isinstance(Emitter['DIPOLE'][0],Fermion) else 'boson')
                        TYP     = Emitter['PARTYPS']
                        BORNTYP = ('cc'     if TYP == 'ffb' else 'cc_and_sc')
                        BORNPTR = ('borncc' if TYP == 'ffb' else str(I)+',BornCCSC.ccsc')
                        TR      = (''       if TYP == 'ffb' else 'Trace')
                        INI     = (''       if TYP == 'ffb' else 'FMatrixT<double>')
                        BORN    = ('borncc' if TYP == 'ffb' else 'BornCCSC.ccsc')

                        ##
                        ##  Subtracted Function
                        ##

                        DICT['SubProcSub'] += AMPMAPLINE
                        DICT['SubProcSub'] += TAB6+'Build_'+PREFIX+'_Momenta(p,&p_tilde,'+str(I)+','+str(J)+','+str(K)+');\n'
                        DICT['SubProcSub'] += TAB6+'for(int j=0;j<NextR-1;j++){pp_tilde[5*j+0]=p_tilde.at(j).p0;pp_tilde[5*j+1]=p_tilde.at(j).p1;pp_tilde[5*j+2]=p_tilde.at(j).p2;pp_tilde[5*j+3]=p_tilde.at(j).p3;pp_tilde[5*j+4]=0.0;}\n'
                        DICT['SubProcSub'] += TAB6+'Proc->evaluate_alpha_'+BORNTYP+'(i,"tree_tree","'+CPB+'",pp_tilde,'+str(Next-1)+','+BORNPTR+');\n'
                        DICT['SubProcSub'] += TAB6+'*rval += QCDFac*'+TR+'(g_'+DIPFUN+'_'+TYP+'(p['+str(I)+'],p['+str(J)+'],p['+str(K)+'],Masses['+str(I)+'],Masses['+str(J)+'])*'+INI+'('+BORN+'['+str(WHICHCC)+']));\n\n'

                        ##
                        ##  Plus Distribution
                        ##

                        DICT['SubProcPlu'] += AMPMAPLINE

                        ##
                        ##  Endpoint Function
                        ##

                        DICT['SubProcEnd'] += AMPMAPLINE
                        DICT['SubProcEnd'] += BORNMAPLINE
                        DICT['SubProcEnd'] += TAB6+'Invariant = BornMasses[j]['+str(I)+']*BornMasses[j]['+str(I)+']'\
                                                              '+ BornMasses[j]['+str(J)+']*BornMasses[j]['+str(J)+']'\
                                                              +('+' if (PREFIX=='II'or PREFIX=='FF') else '-')+\
                                                              '2*(BornMomenta['+str(I)+']*BornMomenta['+str(J)+']);\n'
                        DICT['SubProcEnd'] += TAB6+'Proc->evaluate_alpha_cc(i,"tree_tree","'+CPB+'",pp,'+str(Next-1)+',borncc);\n'
                        DICT['SubProcEnd'] += TAB6+'G_'+DIPFUN+'_'+TYP+'(Invariant,BornMasses[j]['+str(I)+'],BornMasses[j]['+str(J)+'],mu,aux);\n'
                        DICT['SubProcEnd'] += TAB6+'for(int k=0;k<=2;k++) rval[k] += QCDFac*aux[k]*borncc['+str(WHICHCC)+'];\n\n'


                DICT['SubProcSub'] += TAB3+'}\n'
                DICT['SubProcPlu'] += TAB3+'}\n'
                DICT['SubProcEnd'] += TAB3+'}\n'


            SubFunctionH = Template(self.TplDir+'/Dipole_Functions_tpl.h',ChlDir+'/'+Radiative+'_Real.h',DICT)
            SubFunctionC = Template(self.TplDir+'/Dipole_Functions_tpl.cpp',ChlDir+'/'+Radiative+'_Real.cpp',DICT)

            SubFunctionH.Write()
            SubFunctionC.Write()

        RealIntegrand = Template(self.TplDir+'/Real_tpl.h',self.SrcDir+'/Code/Real.h',INTDICT)
        RealIntegrand.Write()

    def BuildVirtualIntegrands(self):

        TAB3 = '    '
        TAB6 = TAB3+TAB3
        TAB9 = TAB6+TAB3

        VIRTDICT = {'Include Virtuals' : '' ,\
                    'nChannels'         : str(len(self.Borns)) ,\
                    'Virtual Catalogue': ''}

        Count = 0
        for Born in self.Borns:

            ClassName = Born+'_Virtual'

            VIRTDICT['Include Virtuals'] += '#include "../Virtual/'+Born+'/'+ClassName+'.h"\n'
            VIRTDICT['Virtual Catalogue'] += TAB9+'Channels['+str(Count)+'] = new '+ClassName+'(*Provider,*model);\n'
            VIRTDICT['Virtual Catalogue'] += TAB9+'ChannelMap.insert({"'+Born+'",'+str(Count)+'});\n'

            Count += 1
            ChlDir = self.SrcDir+'/Virtual/'+Born
            MakeDir(ChlDir)

            DICT={'SubProcHeader'    : '' ,\
                  'SubProcConst'     : '' ,\
                  'SubProcName'      : '' ,\
                  'Next'             : str(self.RadiProc.nex-1) ,\
                  'SubProcBorn'      : '',\
                  'SubProcVirt'      : ''}

            DICT['SubProcHeader'] = Born.upper()
            DICT['SubProcName'] = ClassName

            count = 0
            for particle in self.Borns[Born].Particles:
                DICT['SubProcConst'] += TAB3+'Particles['+str(count)+']= &(model->'+particle.nam+');\n'
                count += 1

            BornCPS = self.Model.GetCPS(self.Borns[Born].Particles)
            VirtCPS = {}
            for CP in BornCPS:
                asp = BornCPS[CP]['as']
                aep = BornCPS[CP]['ae']
                asc = 'as'+str(asp+1)+'ae'+str(aep)
                aec = 'as'+str(asp)+'ae'+str(aep+1)
                VirtCPS[asc] = {'as':asp+1,'ae':aep}
                VirtCPS[aec] = {'as':asp,'ae':aep+1}

            CPHEAD = ''
            for CP in BornCPS:
                if len(CPHEAD):
                    CPHEAD = TAB3+'else if (cp =="'+CP+'"){\n'
                else:
                    CPHEAD = TAB3+'if (cp =="'+CP+'"){\n'

                DICT['SubProcBorn'] += CPHEAD
                DICT['SubProcBorn'] += TAB6+'Args.SubProc = "'+Born+'";\n'
                DICT['SubProcBorn'] += TAB6+'Args.CouplingPower[0] = '+str(BornCPS[CP]['as'])+';\n'
                DICT['SubProcBorn'] += TAB6+'Args.CouplingPower[1] = '+str(BornCPS[CP]['ae'])+';\n'
                DICT['SubProcBorn'] += TAB6+'Provider->Evaluate(&Args);\n'
                DICT['SubProcBorn'] += TAB6+'}\n'

            CPHEAD = ''
            for CP in VirtCPS:
                if len(CPHEAD):
                    CPHEAD = TAB3+'else if (cp =="'+CP+'"){\n'
                else:
                    CPHEAD = TAB3+'if (cp =="'+CP+'"){\n'

                DICT['SubProcVirt'] += CPHEAD
                DICT['SubProcVirt'] += TAB6+'Args.SubProc = "'+Born+'";\n'
                DICT['SubProcVirt'] += TAB6+'Args.CouplingPower[0] = '+str(VirtCPS[CP]['as'])+';\n'
                DICT['SubProcVirt'] += TAB6+'Args.CouplingPower[1] = '+str(VirtCPS[CP]['ae'])+';\n'
                DICT['SubProcVirt'] += TAB6+'Provider->Evaluate(&Args);\n'
                DICT['SubProcVirt'] += TAB6+'}\n'

            SubFunctionH = Template(self.TplDir+'/Virtual_Functions_tpl.h',ChlDir+'/'+Born+'_Virtual.h',DICT)
            SubFunctionC = Template(self.TplDir+'/Virtual_Functions_tpl.cpp',ChlDir+'/'+Born+'_Virtual.cpp',DICT)

            SubFunctionH.Write()
            SubFunctionC.Write()

        VirtualIntegrand = Template(self.TplDir+'/Virtual_tpl.h',self.SrcDir+'/Code/Virtual.h',VIRTDICT)
        VirtualIntegrand.Write()
