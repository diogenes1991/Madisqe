from Physics import *
from Template import *

class OLP:
    
    Channels = {}

    def ReduceChannels(self):

        self.ReducedChannels={}
        self.ChannelMap={}

        for Ch in self.Channels:
            self.ReducedChannels[Ch]=self.Channels[Ch]
            self.ChannelMap[Ch]=self.Channels[Ch]

class NLOX_OLP(OLP):
    def __init__(self,NLOX,Virts,Reals,Borns,Model,Seed,Process,OLP_Tpl,Path):
        
        self.nlox=NLOX
        self.Virts=Virts
        self.Reals=Reals
        self.Borns=Borns
        self.Model=Model
        self.Path =Path
        self.Seed=Seed
        self.Process=Process
        self.Templ=OLP_Tpl
        self.ConfigureChannels()

    def ChannelToDict(self,Channel,Type):
        BASEDICT = {'Initial State' : '' ,\
                    'Final State'   : '' ,\
                    'Tree CP'       : 'bornAlphaQCD = ' ,\
                    'Loop CP'       : '## virtAlphaQCD = ' ,\
                    'enableTerms'   : '4' ,\
                    'ColorCorr'     : 'false' ,\
                    'SpinCorr'      : 'false' ,\
                    'Path'          : '' }

        count = 1
        for Particle in Channel.Initial:
            BASEDICT['Initial State'] += Particle.nam
            if count != len(Channel.Initial):
                BASEDICT['Initial State'] += ','
            count += 1
        count = 1
        for Particle in Channel.Final:
            BASEDICT['Final State'] += Particle.nam
            if count != len(Channel.Final):
                BASEDICT['Final State'] += ','
            count += 1

        BASEDICT['Path'] = self.Path+'/NLOX_Process'
        BASEDICT['Tree CP'] += CSS(Channel.MaxQCD,Channel.MinQCD)
        
        if(Type=='Virt'):
            BASEDICT['ColorCorr'] = 'true'
            BASEDICT['SpinCorr'] = 'true'
            BASEDICT['enableTerms'] = '7'
            BASEDICT['Loop CP']  = 'virtAlphaQCD = '
            BASEDICT['Loop CP'] += CSS(Channel.MaxQCD+1,Channel.MinQCD)

        if(Type=='Born'):
            BASEDICT['ColorCorr'] = 'true'
            BASEDICT['SpinCorr'] = 'true'

        return BASEDICT

    def ConfigureChannels(self,Fixed=False):
        
        ##
        ## We have three kind of Channels to Schedule to the OLP
        ## Virts -> 2 to n @NLO Channels
        ## Reals -> 2 to n+1 @LO Channles
        ## Borns -> 2 to n @LO Channels -> Both Spin and Color Correlated 
        ##

        for Ch in self.Borns:
            BornDict = self.ChannelToDict(self.Borns[Ch],'Born')
            self.Channels[Ch]={'Channel':self.Borns[Ch],'Dictionary':BornDict,'Type':'Born'}
        
        for Ch in self.Reals:
            RealDict = self.ChannelToDict(self.Reals[Ch],'Real')
            self.Channels[Ch]={'Channel':self.Reals[Ch],'Dictionary':RealDict,'Type':'Real'}

        for Ch in self.Virts:
            VirtDict = self.ChannelToDict(self.Virts[Ch],'Virt')
            self.Channels[Ch]={'Channel':self.Virts[Ch],'Dictionary':VirtDict,'Type':'Virt'}

        self.ReduceChannels()

    def WriteSeeds(self):
        Count = 1
        for Ch in self.ReducedChannels:
            Dictionary = self.ReducedChannels[Ch]['Dictionary']
            FileName=self.Path+'/NLOX_Process/'+Ch+'.in'
            ChannelSeed = Template(self.Seed,FileName,Dictionary)
            ChannelSeed.Write()
            Count += 1  

    def GenerateCode(self):
        Here = os.getcwd()
        os.chdir(self.Path+'/NLOX_Process')
        
        count = 1
        tot = str(len(self.ReducedChannels))
        for Ch in self.ReducedChannels:
            print('Generating',self.ReducedChannels[Ch]['Type'],'channel:',Ch,'('+str(count)+'/'+tot+')')
            cmd = self.nlox+' '+Ch +'.in > '+Ch+'.log'
            os.system(cmd)
            cmd = 'mv '+Ch+'.log '+self.Path+'/NLOX_Process/'+Ch
            os.system(cmd)
            count += 1

        os.chdir(Here)

    def GenerateInterface(self):
        INTERFACEDICT = {'Include Channels'   : '' ,\
                         'NSubProcesses'      : str(len(self.ReducedChannels)) ,\
                         'Construct Channels' : '\n' ,\
                         'Amplitude Map'      : '\n'}

        TAB3 = '    '
        TAB6 = TAB3+TAB3
        
        Count = 0
        for Ch in self.ReducedChannels:
            INTERFACEDICT['Include Channels']   += '#include "../'+Ch+'/code/Sub_'+Ch+'.h"\n'
            INTERFACEDICT['Construct Channels'] += TAB6+'subproc['+str(Count)+'] = '+'new Sub_'+Ch+'(pc);\n'
            INTERFACEDICT['Amplitude Map']      += TAB6+'AmpMap.insert({"'+Ch+'",'+str(Count)+'});\n'
            Count += 1

        FILENAME = self.Path+'/NLOX_Process/code/nlox_process.h'
        cmd = 'rm '+FILENAME
        os.system(cmd)
        NLOXPROCESS = Template(self.Process,FILENAME,INTERFACEDICT)
        NLOXPROCESS.Write()

    def WriteOLPClass(self):
        OLPDICT = {'Define Channels':''}

        TAB4='    '
        TAB8=TAB4+TAB4
        TAB12=TAB8+TAB4
        ChannelCount = 0
        for Ch in self.ReducedChannels:
            ThisChannel = self.ReducedChannels[Ch]['Channel']
            OLPDICT['Define Channels'] += TAB12+'ChannelIndex.insert({"'+str(ThisChannel)+'",'+str(ChannelCount)+'});\n'
            ChannelCount += 1

        NLOX_OLP = Template(self.Templ,self.Path+'/Code/NLOX_OLP.h',OLPDICT)
        NLOX_OLP.Write()


class RECOLA_OLP(OLP):

    ##
    ##  Madisqe uses NLOX particle names by default 
    ##  we need to have a map from the names in Madisqe 
    ##  to those used by RECOLA
    ##

    RECOLA_NAME = {'d'    : 'd'    , 's'    : 's'     , 'b'    : 'b'      ,\
                   'dbar' : 'd~'   , 'sbar' : 's~'    , 'bbar' : 'b~'     ,\
                   'u'    : 'u'    , 'c'    : 'c'     , 't'    : 't'      ,\
                   'ubar' : 'u~'   , 'cbar' : 'c~'    , 'tbar' : 't~'     ,\
                   'ep'   : 'e+'   , 'mup'  : 'mu+'   , 'taup' : 'tau+'   ,\
                   'em'   : 'e-'   , 'mum'  : 'mu-'   , 'taum' : 'tau-'   ,\
                   'ne'   : 'nu_e' , 'nm'   : 'nu_mu' , 'nt'   : 'nu_tau' ,\
                   'nebar': 'nu_e~', 'nmbar': 'nu_mu~', 'ntbar': 'nu_tau~',\
                   'Wm'   : 'W-'   , 'Wp'   : 'W+'    , 'Z'    : 'Z'      ,\
                   'g'    : 'g'    , 'A'    : 'A'     , 'h'    : 'H'       \
                   }

    def __init__(self,RECOLA,Virts,Reals,Borns,Model,OLP_Tpl,Path):
        
        self.Recola=RECOLA
        self.Virts=Virts
        self.Reals=Reals
        self.Borns=Borns
        self.Model=Model
        self.Templ=OLP_Tpl
        self.Path =Path

    def ConfigureChannels(self):

        for Ch in self.Borns:
            self.Channels[Ch]={'Channel':self.Borns[Ch],'Type':'Born'}
        
        for Ch in self.Reals:
            self.Channels[Ch]={'Channel':self.Reals[Ch],'Type':'Real'}

        for Ch in self.Virts:
            self.Channels[Ch]={'Channel':self.Virts[Ch],'Type':'Virt'}
        
        self.ReduceChannels()

    def WriteOLPClass(self):
        RECOLA_DICT = { 'Define Channels' : ''}

        TAB4  = '    '
        TAB8  = TAB4 + '    '
        TAB12 = TAB8 + '    '

        ORDER = {'Virt':'NLO','Real':'LO','Born':'LO'}

        ChannelCount = 1
        for Ch in self.Channels:
            ThisChannel = self.Channels[Ch]['Channel']
            
            ChannelName = ''
            
            Count = 1
            for Particle in ThisChannel.Initial:
                ChannelName += self.RECOLA_NAME[Particle.nam]+(' ' if Count < len(ThisChannel.Initial) else '')
                Count += 1
            
            Count = 1
            ChannelName += ' -> '
            for Particle in ThisChannel.Final:
                ChannelName += self.RECOLA_NAME[Particle.nam]+(' ' if Count < len(ThisChannel.Final) else '')
                Count += 1
            
            RECOLA_DICT['Define Channels'] += TAB12+'Recola::define_process_rcl('+str(ChannelCount)+',"'+ChannelName+'","'+ORDER[self.Channels[Ch]['Type']]+'");\n'
            RECOLA_DICT['Define Channels'] += TAB12+'ChannelIndex.insert({"'+str(ThisChannel)+'",'+str(ChannelCount)+'});\n'
            
            ChannelCount += 1

        RECOLA_OLP = Template(self.Templ,self.Path+'/Code/RECOLA_OLP.h',RECOLA_DICT)
        RECOLA_OLP.Write()



            



