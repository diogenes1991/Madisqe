#!/usr/bin/env python3

import os
import sys
from time import localtime, mktime, strftime

from ChannelPlanning import ChannelPlanning
from ProcessGeneration import ProcessGeneration
from SchedulerConfig import SchedulerConfig


class Madisqe(SchedulerConfig, ChannelPlanning, ProcessGeneration):
    def __init__(self,CONFIGFILE):
        
        StartTime = localtime()

        LogFile = open('Madisqe.log','w')
        cmd = "git log --pretty=format:'commit %H%nDate:   %ad' -n 1 > Madisqe.log"
        os.system(cmd)
        LogFile.close()
        
        self.ReadConfig(CONFIGFILE)
        
        print('     Code Generation Started at '+strftime('%d %b %Y %H:%M:%S %Z',StartTime))
        print('                                                                   ')
        print('###################################################################')
        print('                                                                   ')
        print('     Sorting the necesary channels                                 ')
        print('                                                                   ')
        
        ##
        ##  Both the Born and Radiative processes are classified by
        ##  Processes which are the same up to sorting are not kept 
        ##  this must be all summed back by the c++ interface
        ##  
        ##  The veto here is on all processes that are not possible at tree level 
        ##  The issue is that if we allow these we can only compute them @ LO
        ##

        self.LoadConfig()
        self.VetoProcs()
        self.CreateDirectories()
        self.WriteModel()

        print('                                                                   ')
        print('     Sorting completed at '+strftime('%d %b %Y %H:%M:%S %Z',localtime()))
        print('     Total elapsed time: ' + str(mktime(localtime())-mktime(StartTime)) + ' s')
        print('                                                                   ')
        print('###################################################################')
        print('                                                                   ')
        print('     The Born and Virtuel include the channels('+str(len(self.BornProc.subproc))+'):')
        print('                                                                   ')
        
        for Ch in self.BornProc.subproc:
            print('     '+Ch)
        
        print('                                                                   ')
        print('###################################################################')
        print('                                                                   ')
        print('     The Radiative includes the channels ('+str(len(self.RadiProc.subproc))+'):')
        print('                                                                   ')
        
        for Ch in self.RadiProc.subproc:
            print('     '+Ch)

        print('                                                                   ')
        print('###################################################################')
        print('                                                                   ')
        print('     Building Real Integrands                                      ')
        print('                                                                   ')
        
        self.BuildDipoleTree()
        self.BuildRealIntegrands()
        self.Build_Dipole_Structures()
        self.BuildRealIntegrands_New()

        print('                                                                   ')
        print('     Dipole fetching completed at '+strftime('%d %b %Y %H:%M:%S %Z',localtime()))
        print('     Total elapsed time: ' + str(mktime(localtime())-mktime(StartTime)) + ' s')
        print('                                                                   ')
        print('###################################################################')
        print('                                                                   ')
        print('     Generating matrix elements and Virtual Integrands             ')
        print('                                                                   ')
        
        self.BuildOLP(False)
        self.BuildVirtualIntegrands()

        print('                                                                   ')
        print('     Generation of matrix elements completed at '+strftime('%d %b %Y %H:%M:%S %Z',localtime()))
        print('     Total elapsed time: ' + str(mktime(localtime())-mktime(StartTime)) + ' s')
        print('                                                                   ')
        print('###################################################################')
        print('                                                                   ')
        print('     Building Madisqe Interface                                    ')
        
        self.BuildInterface()
        
        print('                                                                   ')
        print('     Interface building completed at '+strftime('%d %b %Y %H:%M:%S %Z',localtime()))
        print('     Total elapsed time: ' + str(mktime(localtime())-mktime(StartTime)) + ' s')
        print('                                                                   ')
        print('###################################################################')
        print('                                                                   ')
        print('     Code generation finished at '+strftime('%d %b %Y %H:%M:%S %Z',localtime()))
        print('     Total elapsed time: ' + str(mktime(localtime())-mktime(StartTime)) + ' s')
        print('                                                                   ')
        print('###################################################################')
        
        ## 
        ##  TO DO: At the moment the code is a bit unstable 
        ##  We need to stabilize and clean as much as possible 
        ##  The next task will be to centralize masses into the 
        ##

        # for DipoleStrucure in self.DipoleStructures:
            # print self.DipoleStructures[DipoleStrucure]
            # self.DipoleStructures[DipoleStrucure].Show()


def main(CONFIGFILE):

    print(r'''
####################################################################
#                                                                  #        
#      __  __               _   _                                  #
#     |  \/  |   __ _    __| | (_)  ___    __ _    ___             #
#     | |\/| |  / _` |  / _` | | | / __|  / _` |  / _ \            #
#     | |  | | | (_| | | (_| | | | \__ \ | (_| | |  __/            #
#     |_|  |_|  \__,_|  \__,_| |_| |___/  \__, |  \___|            #
#                                            |_|                   #
#                                                                  #        
#                           Version 1.0.0                          #                   
#                          by D. Figueroa                          #                   
#                                                                  #        
#                                                                  #        
####################################################################
''')
    MADISQE = Madisqe(CONFIGFILE)

if __name__ == "__main__":
    if len(sys.argv)<2:
        print("\33[31mError\33[0m: No input file specified")
    elif len(sys.argv)==2:
        main(sys.argv[1])
    else:
        print("\33[31mError\33[0m: Too many arguments")
