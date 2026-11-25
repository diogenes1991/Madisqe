from Physics import *
from Template import *

##
##  Dipoles overhead classes to build the Dipole Structures 
##

class Dipole:

    DipoleType = ''

    def __init__(self,Type,Indices,UBMap,Mapping,Parent,DecayChannel,UnderlyingBorn,Model):
        self.Type=Type
        self.Indices=Indices
        self.Parent=Parent
        self.DecayChannel=DecayChannel
        self.UnderlyingBorn=UnderlyingBorn
        self.Model=Model
        self.Map=Mapping
        self.UBMap=UBMap
        self.GetSpectators()

    def __str__(self):
        Name =self.DipoleType+' Dipole of '+self.Type+' type ('+str(self.Indices)+')\n'
        Name+='Parent          : '+str(self.Parent)+'\n'
        Name+='Decay Channel   : '+str(self.DecayChannel)+'\n'
        Name+='Underlying Born : '+str(self.UnderlyingBorn)+'\n'
        Name+='Mapping         : '+str(self.Map)+'\n'
        Name+='\n'
        return Name

    ## 
    ##  This version grabs the spectator from the parent
    ##
    
    def GetSpectators(self):
        count = -1
        self.Spectators=[]
        for Particle in self.Parent.Particles:
            count+=1
            if count in self.Indices:
                continue
            if self.CanSpectate(Particle):
                self.Spectators.append({'Particle':Particle,'Index':count})

class EWKDipole(Dipole):

    DipoleType = 'EWK'
    OLPCall = 'Evaluate'

    def CanSpectate(self,Particle):
        if 'Charge' in Particle.sym:
            return True

    def UBCoupling(self,Coupling):
        return {'as':Coupling['as'],'ae':Coupling['ae']-1}

class QCDDipole(Dipole):

    DipoleType = 'QCD'
    OLPCall = 'Evaluate_CC'

    def CanSpectate(self,Particle):
        if Particle in self.Model.QCDPars:
            return True

    def UBCoupling(self,Coupling):
        return {'as':Coupling['as']-1,'ae':Coupling['ae']}

class DipoleStructure:
    def __init__(self,Radiative,Dipoles):
        self.Radiative=Radiative
        self.Dipoles=Dipoles

    def __str__(self):
        Name='************************************************\n'
        Name+="Dipole Structures for "+str(self.Radiative)+"\n"
        for Dipole in self.Dipoles:
            Name+=str(Dipole)
        Name+='************************************************'
        return Name

    def CollectBorns(self):
        self.UnderlyingBorns={}
        for Dipole in self.Dipoles:
            self.UnderlyingBorns[str(Dipole.UnderlyingBorn)] = Dipole.UnderlyingBorn

    def Show(self,template_path,dest_path):

        DICT={'SubProcHeader'    : str(self.Radiative).upper() ,\
              'SubProcConst'     : '' ,\
              'SubProcName'      : str(self.Radiative)+'_Real' ,\
              'Next'             : str(len(self.Radiative.Particles)) ,\
              'SubProcMat'       : '' ,\
              'SubProcSub'       : '' ,\
              'SubProcPlu'       : '' ,\
              'SubProcEnd'       : '' }

        TAB4 = '    '
        TAB8 = TAB4+TAB4

        NInitials = len(self.Radiative.Initial)
        
        ## 
        ##  Fisrt we build the DipoleStructure Constructor 
        ##  Collecting all the Underlying Borns and allocating 
        ##  their masses withing the DipoleStructure class
        ##  Maybe it would be better to store pointers 
        ##  rather than the values.
        ##

        self.CollectBorns()
        count = 0 
        for Particle in self.Radiative.Particles:
            DICT['SubProcConst'] += TAB4+'RParticles['+str(count)+'] = &(model->'+Particle.nam+');\n'
            count += 1
    

        DICT['SubProcConst'] += '\n'   
        DICT['SubProcConst'] += TAB4+'nBorn = '+str(len(self.UnderlyingBorns))+';\n'   
        DICT['SubProcConst'] += TAB4+'BParticles = new Particle**[nBorn];\n'
        DICT['SubProcConst'] += TAB4+'for(int i=0;i<nBorn;i++) BParticles[i]= new Particle*[NextR-1];\n\n' 
             
        Bcount = 0
        for Born in self.UnderlyingBorns:
            count = 0
            DICT['SubProcConst'] += TAB4+'BornMap.insert({"'+str(Born)+'",'+str(Bcount)+'});\n'
            for Particle in self.UnderlyingBorns[Born].Particles:
                DICT['SubProcConst'] += TAB4+'BParticles['+str(Bcount)+']['+str(count)+']= &(model->'+Particle.nam+');\n'
                count += 1
            Bcount += 1

        ##
        ##
        ##

        print('************************************************')
        print('Dipole Structures for '+str(self.Radiative))
        
        RadiativeCouplings = self.Radiative.Model.GetCPS(self.Radiative.Particles)
        
        CPHEAD = ''
        for Coupling in RadiativeCouplings:
            
            if len(CPHEAD):
                CPHEAD = TAB4+'else if (cp =="'+Coupling+'"){\n'
            else:
                CPHEAD = TAB4+'if (cp =="'+Coupling+'"){\n'

            DICT['SubProcSub'] += CPHEAD
            DICT['SubProcSub'] += TAB8+'Args.SubProc = "'+str(self.Radiative)+'";\n'
            DICT['SubProcSub'] += TAB8+'Args.CouplingPower[0] = '+str(RadiativeCouplings[Coupling]['as'])+';\n'
            DICT['SubProcSub'] += TAB8+'Args.CouplingPower[1] = '+str(RadiativeCouplings[Coupling]['ae'])+';\n'
            DICT['SubProcSub'] += TAB8+'Provider->Evaluate(&Args);\n'
            DICT['SubProcSub'] += TAB8+'*rval += MatrixElement;\n\n'


            CACHEDTAG = ''
            for Dipole in self.Dipoles:

                UBCoupling = Dipole.UBCoupling(RadiativeCouplings[Coupling])
                BornCouplings = Dipole.UnderlyingBorn.Model.GetCPS(Dipole.UnderlyingBorn.Particles)

                if ('as'+str(UBCoupling['as'])+'ae'+str(UBCoupling['ae'])) not in BornCouplings:
                    continue
                
                if str(Dipole.UnderlyingBorn) != CACHEDTAG:
                    DICT['SubProcSub'] += TAB8+'Args.SubProc = "'+str(Dipole.UnderlyingBorn)+'";\n'
                    DICT['SubProcSub'] += TAB8+'BornIndex = BornMap.at("'+str(Dipole.UnderlyingBorn)+'");\n'
                    DICT['SubProcSub'] += TAB8+'Args.Momenta = BMomenta;\n'
                    DICT['SubProcSub'] += TAB8+'Args.CouplingPower[0] = '+str(UBCoupling['as'])+';\n'
                    DICT['SubProcSub'] += TAB8+'Args.CouplingPower[1] = '+str(UBCoupling['ae'])+';\n\n'
                    CACHEDTAG = str(Dipole.UnderlyingBorn)

                BPIndex = (0 if Dipole.Type == 'ij' else 1)
                BundledParticle = Dipole.DecayChannel.Particles[BPIndex]

                DipoleSubtype = ('I' if (Dipole.Type == 'ai' or Dipole.Type == 'ia') else 'F')
                print(Dipole.Type,DipoleSubtype)
                for Spectator in Dipole.Spectators:
                    if Spectator['Index'] < NInitials:
                        print(TAB4+'Add',Dipole.DipoleType,'D',Dipole.Type,',b')
                        print(Dipole)
                        print("BundledParticle = ",Dipole.DecayChannel.Particles[BPIndex],BPIndex)
                        DipoleSubtype += 'I'
                        print(DipoleSubtype)
                    else:
                        print(TAB4+'Add',Dipole.DipoleType,'D',Dipole.Type,',k')
                        print(Dipole)
                        print("BundledParticle = ",Dipole.DecayChannel.Particles[BPIndex],BPIndex)
                        DipoleSubtype += 'F'
                        print(DipoleSubtype)

                    DICT['SubProcSub'] += TAB8+'//'+str(Dipole.Parent)+' : (('+str(Dipole.DecayChannel)+' '+str(Dipole.Indices)+') -> '+str(Dipole.UnderlyingBorn)+')\n'
                    DICT['SubProcSub'] += TAB8+'//'+'Spectated by '+str(Spectator['Particle'])+'('+str(Spectator['Index'])+')\n'
                    DICT['SubProcSub'] += TAB8+'// Usorted Born Map = '+str(Dipole.UBMap)+' Sorting Map = '+str(Dipole.Map)+'\n'
                    DICT['SubProcSub'] += TAB8+'IndexMap.clear();\n'
                    IndexMap = 'IndexMap = {'
                    count = 1
                    for Index in Dipole.UBMap:
                        IndexMap += '{'+str(Index)+','+str(Dipole.Map[Dipole.UBMap[Index]])+'}'+(',' if count!=len(Dipole.UBMap) else '')
                        count += 1
                    IndexMap += '}'
                    DICT['SubProcSub'] += TAB8+IndexMap+';\n'
                    DICT['SubProcSub'] += TAB8+'Build_'+DipoleSubtype+'_Momenta(RMomenta,BMomenta,'+\
                                          str(Dipole.Indices[0])+','+str(Dipole.Indices[1])+','+str(Spectator['Index'])+',IndexMap);\n'
                    DICT['SubProcSub'] += TAB8+'Provider->'+Dipole.OLPCall+('_SC' if isinstance(BundledParticle,Boson) else '')+'(&Args);\n'
                    # DICT['SubProcSub'] += TAB8+'*rval += '++'\n\n'
                    
            DICT['SubProcSub'] += TAB4+'}\n\n'  


        print('************************************************')

        DIPOLESTRUCTUREC = Template(template_path+'/Dipole_Functions_tpl.cpp',dest_path+'/'+str(self.Radiative)+'_Real.cpp',DICT)
        DIPOLESTRUCTUREH = Template(template_path+'/Dipole_Functions_tpl.h',dest_path+'/'+str(self.Radiative)+'_Real.h',DICT)
        DIPOLESTRUCTUREC.Write()
        DIPOLESTRUCTUREH.Write()
        

    def Write(self,Template,Path):
    
        ChlDir = self.SrcDir+'/Real/'+Radiative
        # MakeDir(ChlDir)

        DICT={'SubProcHeader'    : str(self.Radiative).upper() ,\
              'SubProcConst'     : '' ,\
              'SubProcName'      : Radiative+'_Real' ,\
              'Next'             : str(len(self.Radiative.Particles)) ,\
              'SubProcMat'       : '' ,\
              'SubProcSub'       : '' ,\
              'SubProcPlu'       : '' ,\
              'SubProcEnd'       : '' }
            
        ## 
        ##  Integrands constructor 
        ##

        count = 0 
        for Particle in self.Radiative:
            DICT['SubProcConst'] += TAB3+'Masses['+str(count)+'] = model->'+Particle.nam+'.Mass;\n'
            DICT['SubProcConst'] += TAB3+'PID['+str(count)+'] = model->'+Particle.nam+'.PID;\n'
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
