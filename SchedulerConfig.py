"""Configuration loading for the Madisqe scheduler."""

import os
import sys

from Physics import Process


class SchedulerConfig:
    def LoadPaths(self):
        PATHS = { 'GSL PATH'    : [''], \
                  'CUBA PATH'   : [''], \
                  'LHAPDF PATH' : [''], }

        PATHSFILE=os.getcwd()+'/util/utils.path'
        COMMCHAR = '#'
        REQUIRED = set([])

        f = open(PATHSFILE,'r')
        configfile= []
        for l in f:
            if l.find(COMMCHAR)==0 or len(l)==0 or l=='\n':
                continue
            configfile.append([False,l])

        for configuration in PATHS.keys():
            warn = True
            for line in configfile:
                if configuration in line[1]:
                    thisconfig = line[1].strip().split('=')
                    PATHS[thisconfig[0].strip()] = (thisconfig[1].strip()).split(',')[0]
                    warn = False
                    line[0] = True
            if warn:
                if configuration not in REQUIRED:
                    print("\33[95mWarning\33[0m: Configuartion",configuration,"not found in configuration file, using default:",PATHS[configuration][0])
                else:
                    print("\33[31mError\33[0m: Configuration",configuration,"not found in configuration, this is a required configuration.")
                    sys.exit()

        for line in configfile:
            if not line[0]:
                print("\33[95mWarning\33[0m: Configuartion",(((line[1].strip()).split('='))[0]).strip(),"is not a valid configuration setting, please check the syntax")
        f.close()
        self.paths = PATHS

    def ReadConfig(self,CONFIGFILE):
        CONFIG = {'INITIAL STATE': [0],\
                  'FINAL STATE'  : [0],\
                  'RADIATIVE'    : [0],\
                  'MODEL FILE'   : ['StandardModel'],\
                  'PATH'         : [os.getcwd()],\
                  'NLOX PATH'    : [0] ,\
                  'RECOLA PATH'  : [0] ,\
                  'SEED TEMP'    : ['tpl/NLOX_seed_tpl.in'] ,\
                  'VERBOSE'      : [0] ,\
                  'STAGE'        : [0] }

        REQUIRED = set(['INITIAL STATE','FINAL STATE','NLOX PATH','RECOLA PATH','RADIATIVE'])

        COMMCHAR = '#'

        f = open(CONFIGFILE,'r')
        configfile= []
        for l in f:
            if l.find(COMMCHAR)==0 or len(l)==0 or l=='\n':
                continue
            configfile.append([False,l])

        for configuration in CONFIG.keys():
            warn = True
            for line in configfile:
                if configuration in line[1]:
                    thisconfig = line[1].strip().split('=')
                    CONFIG[thisconfig[0].strip()] = (thisconfig[1].strip()).split(',')
                    warn = False
                    line[0] = True
            if warn:
                if configuration not in REQUIRED:
                    print("\33[95mWarning\33[0m: Configuartion",configuration,"not found in configuration file, using default:",CONFIG[configuration][0])
                else:
                    print("\33[31mError\33[0m: Configuration",configuration,"not found in configuration, this is a required configuration.")
                    sys.exit()

        for line in configfile:
            if not line[0]:
                print("\33[95mWarning\33[0m: Configuartion",(((line[1].strip()).split('='))[0]).strip(),"is not a valid configuration setting, please check the syntax")
        f.close()
        self.config = CONFIG

    def LoadConfig(self):

        self.verbose = int(self.config['VERBOSE'][0])

        try:
            LoadedModel = __import__(self.config['MODEL FILE'][0])
        except:
            print("\33[31mError\33[0m: Model file",self.config['MODELFILE'][0],"not found.")
            sys.exit()

        self.Model = LoadedModel.WorkingModel
        self.ParticleContent = self.Model.ParticleContent

        self.ini = []
        for particle in self.config['INITIAL STATE']:
            try:
                self.ini.append(self.ParticleContent[particle])
            except:
                print("\33[31mError\33[0m: Particle class",particle,"not defined.")
                sys.exit()

        self.fin = []
        self.finrad = []
        for particle in self.config['FINAL STATE']:
            try:
                self.finrad.append(self.ParticleContent[particle])
                self.fin.append(self.ParticleContent[particle])
            except:
                print("\33[31mError\33[0m: Particle class",particle,"not defined.")
                sys.exit()

        try:
            self.finrad.append(self.ParticleContent[self.config['RADIATIVE'][0]])
        except:
            print("\33[31mError\33[0m: Particle class",self.config['RADIATIVE'][0],"not defined")
            sys.exit()

        self.RadiProc = Process(self.ini,self.finrad,self.Model)
        self.BornProc = Process(self.ini,self.fin,self.Model)
        self.path = self.config['PATH'][0]+"/"+str(self.RadiProc)

        self.seed_tpl = self.config['SEED TEMP'][0]
        if not os.path.exists(self.seed_tpl):
            print('\33[31mError\33[0m: NLOX input seed',self.seed_tpl,'not found')
            sys.exit()

        self.nlox = self.config['NLOX PATH'][0]+'/nlox.py'
        if not os.path.exists(self.nlox):
            print('\33[31mError\33[0m: NLOX executable',self.nlox,'not found')
            sys.exit()

        self.recola = self.config['RECOLA PATH'][0]
        if not os.path.exists(self.recola+'/recola2-2.2.2/librecola.so'):
            print('\33[31mError\33[0m: RECOLA library: librecola.so not found at',self.recola+'/recola2-2.2.2')
            sys.exit()

        self.stage = int(self.config['STAGE'][0])

        if self.verbose:
            print('Configuartion loaded succesfuly')
            for conf in self.config:
                print(conf,'=',(self.config[conf] if len(self.config[conf]) > 1 else self.config[conf][0]))

        self.TplDir = 'tpl'
        self.IntDir = 'src'
        self.Inputs = 'input'
        self.SrcDir = self.path
