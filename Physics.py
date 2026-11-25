import sys,os,copy

class Particle(object):    
    def __init__(self,Nam,Sym,PID,Mas):
        self.nam = Nam
        self.pid = PID
        self.mas = Mas
        self.sym = Sym
        self.qnb = {}
        
    def __str__(self):
        return self.nam

    def QuantumNumber(self,QN):
        for QuantumNumber in QN:
            self.qnb[QuantumNumber] = QN[QuantumNumber]

class Boson(Particle):
    pass

class Fermion(Particle):
    pass

class CompositeParticle:
    def __init__(self,Name,Subparticles,Mother=None,Degree=2):
        self.nam = Name
        for particle in Subparticles:
            if not isinstance(particle,Particle):
                print("\33[31mError\33[0m: In composite particle",self.nam,"a non-particle constituent has been passed:",particle)
                sys.exit()
        self.sub = Subparticles
        
        if Mother!=None:
            if not isinstance(Mother,Particle):
                print("\33[31mError\33[0m: In composite particle",self.nam,"a non-particle parent has been passed:",Mother)
                sys.exit()
            self.parent = Mother
            self.degree = 2
            self.InheritSymmetries()
            
    def DaughterOf(self,parent,degree=2):
        if not isinstance(parent,Particle):
            print("\33[31mError\33[0m: In composite particle",self.nam,"a non-particle parent has been passed:",parent)
            sys.exit()
        self.parent = parent
        self.degree = degree
        self.InheritSymmetries()
            
    def __str__(self):
        return self.nam
    
    def InheritSymmetries(self):
        self.sym_weights = {}
        for index in range(len(self.sub)):
            #
            # If one wants to make use of the abstract symmetry engine to enforce 
            # parent -> daughters relations one must create a new set abstract symmetries that all the 
            # daughters of the parent have a non-zero weight under. The values of the 
            # weights are all the non-zero values of abstract symmetries that the daughters
            # have but the parent doesn't. For example "Zj" is daughter of "Z", "Z" has zero 
            # weight under "Charge" so for all particles in "Zj" we need to add a new abstract
            # symmetry "Zness" that takes the value of the charge of the daughter, this way 
            # only subsets of daughters that have zero total charge would be considered valid 
            # subsets of the decay "Z" -> "Zj" "Zj". The generation symmetry is also present, but 
            # it is a multiple of the charge symmetry and thus redundant, of course we don't know this
            # and a priori we include both.
            #
            new_particle = copy.deepcopy(self.sub[index])
            for symmetry in self.sub[index].sym.keys():
                new_sym_nam = self.parent.nam+"_"+self.nam+"_"+symmetry
                new_particle.sym[new_sym_nam] = self.sub[index].sym[symmetry]
                try:
                    self.sym_weights[new_sym_nam] = -float(self.parent.sym[symmetry])/self.degree
                except:
                    self.sym_weights[new_sym_nam] = 0
            self.sub[index] = copy.deepcopy(new_particle)

class Model:
    def __init__(self):
        pass

    def __str__(self):
        retval = '{'
        for particle in self.ParticleContent:
            retval += str(particle) + ' '
        retval += '}'
        return retval

    def BuildModel(self):
        self.sym = {}
        # print self.ParticleContent
        # for particle in self.ParticleContent.keys():
            # if isinstance(self.ParticleContent[particle],Particle):
                # self.sym[]

        self.CrossDictionary = {}
        for particle in self.ParticleContent:
            if not isinstance(self.ParticleContent[particle],Particle):
                continue
            self.CrossDictionary[self.ParticleContent[particle].nam] = self.ParticleContent[particle].nam
            for otherparticle in self.ParticleContent:
                if not isinstance(self.ParticleContent[otherparticle],Particle):
                    continue
                if self.ParticleContent[particle].pid == -self.ParticleContent[otherparticle].pid:
                    self.CrossDictionary[self.ParticleContent[particle].nam] = self.ParticleContent[otherparticle].nam

        self.Composites = {n:p for (n,p) in self.ParticleContent.items() if isinstance(p,CompositeParticle)}
        self.Fundamentals = {n:p for (n,p) in self.ParticleContent.items() if isinstance(p,Particle)}

    def CanMakeVertex(self,PAR1,PAR2):
            out = False
            for Set in self.Couplings:
                if (PAR1 in Set and PAR2 in Set):
                    out = True
            return out

    def ConnectedComponents(self,PARS,C):
            
            if len(PARS) == 0:
                return 0
            
            CC = [PARS[0]]
            cc = [PARS[0]]
            breakwhile = 0 
            while breakwhile == 0:
                breakwhile = 1
                aux = []
                for Par1 in cc:
                    for Par2 in PARS:
                        if self.CanMakeVertex(Par1,Par2) and Par2 not in aux:
                            aux.append(Par2)
                for Par in aux:
                    if Par not in CC:
                        CC.append(Par)
                        CC.sort(key=lambda particle: particle.nam)
                        breakwhile = 0
                cc = aux

            NCC = []
            for Par in CC:
                NCC.append(Par.nam)
            C.append(NCC)
            
            PARSNew = []
            for Par in PARS:
                if Par in CC:
                    continue
                PARSNew.append(Par)
            
            self.ConnectedComponents(PARSNew,C)

    def GetCPS(self,PARS):
        CPS = {}
        EWKc = 0
        QCDc = 0
        for particle in PARS:
            if particle in self.EWKPars:
                EWKc += 1
            if particle in self.QCDPars:
                QCDc += 1
        MaxQCD = QCDc - 2
        MinQCD = len(PARS) - EWKc         
        
        for n in range(MinQCD,MaxQCD+1):
            CPS['as'+str(n)+'ae'+str(len(PARS)-2-n)] = {'as':n,'ae':len(PARS)-2-n}
        return CPS

class Channel:
        def __init__(self,Initial,Final,Model):
            self.Initial=Initial
            self.Final=Final
            self.Particles=Initial+Final
            self.Model=Model
            self.ComputeBounds()
        
        def __str__(self):
            Name=''
            for Particle in self.Initial:
                Name+=Particle.nam
            Name+='_'
            for Particle in self.Final:
                Name+=Particle.nam
            return Name    

        def ComputeBounds(self):
            self.MaxQCD=0
            self.MinQCD=0
            EWKc = 0
            QCDc = 0
            for Particle in self.Particles:
                if Particle in self.Model.QCDPars:
                    QCDc += 1
                if Particle in self.Model.EWKPars or Particle in self.Model.YUKPars:
                    EWKc += 1
            self.MaxQCD = QCDc - 2
            self.MinQCD = len(self.Initial) + len(self.Final) - EWKc

        def IsPossibleAtTreeLevel(self):
            CC = []
            if self.IsPossible():
                self.Model.ConnectedComponents(self.Particles,CC)
                if len(CC)==1:
                    return True
                else:
                    return False
            else:
                return False

        def IsPossible(self):
            
            ##
            ##  We will check two things to determine if a given channel 
            ##  is possible within the Model if it respects the 
            ##  symmetries of the Model as in the conserved charges 
            ##  of the Model are indeed conserved by the channel.
            ##  and if the channel has an even number of fermions 
            ##  meaning it respects Lorentz Symmetry 
            ##

            NFermions = 0
            ChannelSymmetries = {}
            for Particle in self.Particles:
                
                ## Initialize the symmetries

                for Symmetry in Particle.sym:
                    ChannelSymmetries[Symmetry] = 0
                
                ## Count Fermions

                if isinstance(Particle,Fermion):
                    NFermions += 1

            if NFermions%2 == 1:
                ## Exit if NFermions is odd
                return False

            ## Compute Symmetries' Weights, exit if not equal to zero of parent's values

            count  = 0
            for Particle in self.Particles:
                for Symmetry in ChannelSymmetries:
                    if Symmetry in Particle.sym:
                        ChannelSymmetries[Symmetry] += Particle.sym[Symmetry] if count < len(self.Initial) else -Particle.sym[Symmetry]
                count += 1

            for Symmetry in ChannelSymmetries:
                w = 0
                try:
                    w = super().sym_weights[Symmetry]
                except:
                    w = 0
                if ChannelSymmetries[Symmetry] != w:
                    return False

            return True

class Process:           
        def __init__(self,Initial_State,Final_State,Model):
            self.ini = Initial_State
            self.fin = Final_State
            self.nex = len(Initial_State)+len(Final_State)
            self.lni = len(Initial_State)
            self.lnf = len(Final_State)
            self.Model = Model

            self.finfun = [ p for p in self.fin if isinstance(p,Particle)]
            
            self.proc = []
            for i in self.ini:
                self.proc.append(i)
            for i in self.fin:
                self.proc.append(i)
               
            self.InheritSymmetries()
            self.BuildSubProcesses()
            self.BuildChannels()
            
        def __str__(self):
            aux = ""
            for i in self.ini:
                aux += i.nam +""
            aux += "_"
            for i in self.fin:
                aux += i.nam + ""
            return aux
        
        ##
        ##  These functions (Print,write) were written for NLOX/aux_beta and is never used 
        ##  elsewhere
        ##

        def Print(self):
            line = ""
            for subprocess in self.scatters:
                count = 0
                for particle in subprocess:
                    if count == len(self.ini):
                        line += "-> "
                    line += particle.nam+" "
                    count += 1
                line += "\n"
            print(line)
         
        def write(self):
            name = str(self)
            f = open(name+".subprocesses","w+")
            
            for subprocess in self.scatters:
                w = ''
                count = 0
                l = ''
                for particle in subprocess:
                    if count == len(self.ini):
                        w += '-> '
                    w += particle.nam+' '
                    count += 1
                w += '\n'
                f.write(w)
            print(len(self.scatters),"subprocesses written")
            
        def InheritSymmetries(self): 
            self.sym_weights = {}
            for particle in self.proc:
                try: 
                    particle.sym_weights
                except:
                    continue
                for symmetry in particle.sym_weights.keys():
                    try:
                        self.sym_weights[symmetry] += particle.sym_weights[symmetry]
                    except:
                        self.sym_weights[symmetry] = particle.sym_weights[symmetry]

        def BuildScatters(self):
            EVEN_FER = True
            SORT_SYM = True
            ABST_SYM = True
            
            self.subproc = []
            
            for i in self.proc:
                if isinstance(i,CompositeParticle):
                    self.subproc.append(i.sub)
                else:
                    self.subproc.append([i])
           
            self.scatters = []
            l = 1
            bounds = []
            for particle in self.subproc:
                l *= len(particle)
                bounds.append(len(particle))
            
            for i in range(l):
                addres = []
                ac = i
                for j in bounds:
                    addres.append(ac%j)
                    ac //= j
                    
                pars = []
                for j in range(len(bounds)):
                    pars.append(self.subproc[j][addres[j]])
                
                self.scatters.append(pars)
            
            if EVEN_FER:
                aux = []
                for tent in self.scatters:
                    par = 0
                    for p in tent:
                        if isinstance(p,Fermion):
                            par += 1
                    par = par%2
                    if(par==0):
                        aux.append(tent)
                self.scatters = aux
                
            if ABST_SYM:
                aux = []
                for tentative in self.scatters:
                    
                    ## Symmetries Initialization
                    proc_syms = {}
                    for particle in tentative:
                        for symmetry in particle.sym:
                            proc_syms[symmetry] = 0
                    
                    ## Computes the symmetry weight
                    count = 0
                    for particle in tentative:
                        for symmetry in proc_syms.keys():
                            if symmetry in particle.sym:
                                proc_syms[symmetry] += particle.sym[symmetry] if count < len(self.ini) else -particle.sym[symmetry]
                        count += 1
                    
                    ## Checks if all weights are zero or what the value they inherited from their parents
                    respects_symmetries = True
                    for symmetry in proc_syms.keys():
                        w = 0
                        try:
                            w = self.sym_weights[symmetry]
                        except:
                            w = 0
                        if proc_syms[symmetry] != w:
                            respects_symmetries = False
                    
                    ## If the tentative process respects all symmetries is stored 
                    if respects_symmetries:
                            aux.append(tentative)
                    
                self.scatters = aux       
                
            if SORT_SYM:
                def myf(e):
                    return -e.pid
                
                aux = []
                for tent in self.scatters:
                    sortedins = []
                    sortedouts = []
                    count = 0
                    for par in tent:
                        if count < len(self.ini):
                            sortedins.append(par)
                        else:
                            sortedouts.append(par)
                        count += 1
                    
                    sortedins.sort(key=myf)        
                    sortedouts.sort(key=myf)
                    
                    sortedins.extend(sortedouts)
                    
                    if len(aux):
                        shouldadd = True
                        for subproc in aux:
                            areequal = True
                            for n in range(len(subproc)):
                                if subproc[n].nam != sortedins[n].nam:
                                    areequal = False
                            if areequal:
                               shouldadd = False
                        if shouldadd:
                            aux.append(sortedins)
                    else:
                        aux.append(sortedins)
                        
                self.scatters = aux
                
                def SortFunction(Proc):
                    n = 0
                    for i in Proc:
                        if isinstance(i,Boson):
                            n += len(Proc)
                        if i.pid > 0:
                            n += -1
                        else:
                            n += 1
                    return n
                self.scatters.sort(key=SortFunction)

        def BuildSubProcesses(self):
            self.BuildScatters()
            self.subproc = {}
            for scatter in self.scatters:
                count = 0
                key = ""
                for particle in scatter:
                    count += 1
                    key += particle.nam
                    if count == len(self.ini):
                        key += "_"
                self.subproc[key] = scatter

        def BuildString(self,LIST):
            key = ""
            count = 0
            for particle in LIST:
                count += 1
                key += particle.nam
                if count == len(self.ini):
                    key += "_"
            return key    

        def BuildChannels(self):

            ##
            ## Fisrt we put all particles on the same footing
            ##

            self.SubProc = []
            for Particle in self.proc:
                if isinstance(Particle,CompositeParticle):
                    self.SubProc.append(Particle.sub)
                else:
                    self.SubProc.append([Particle])
           
            ##
            ##  Now we build the address space for the process
            ##  This algorithm is very similar to an algorithm 
            ##  that converts a time in seconds into years,days,hours,minutes,seconds...
            ## 

            Scatters = []
            NumberOfChannels = 1
            Bounds = []
            for Particle in self.SubProc:
                NumberOfChannels *= len(Particle)
                Bounds.append(len(Particle))
            
            self.Channels = {}
            for ChannelNumber in range(NumberOfChannels):
                Addres = []
                LocalAddress = ChannelNumber
                for LocalPlace in Bounds:
                    Addres.append(LocalAddress%LocalPlace)
                    LocalAddress //= LocalPlace
                    
                Particles = []
                for ParticleSelector in range(len(Bounds)):
                    Particles.append(self.SubProc[ParticleSelector][Addres[ParticleSelector]])
                
                ##
                ## Sorting both initials and finals
                ##

                def sortfunction(p):
                    return -p.pid

                Ini = Particles[:self.lni]
                Fin = Particles[self.lni:]
                Ini.sort(key=sortfunction)
                Fin.sort(key=sortfunction)

                Ch = Channel(Ini,Fin,self.Model)
                if Ch.IsPossible():
                    self.Channels[str(Ch)] = Ch