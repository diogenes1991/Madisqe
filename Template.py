import os,sys
from Utilities import *

class Template():
    
    def __init__(self,Source,Path,Dictionary):

        self.tmp_arg_mrk="####"
        self.com_char="//"
        self.special_chars=[]

        self.Source=Source
        if not os.path.exists(self.Source):
            print('\33[31mError\33[0m: Template file:',self.Source,'not found')
            sys.exit()
        
        self.Path=Path
        if os.path.exists(self.Path):
            print('\33[31mError\33[0m: Target file:',self.Path,'already exists')
            sys.exit()

        self.Dictionary=Dictionary
        for Key in self.Dictionary:
            if not isinstance(self.Dictionary[Key],str):
                print('\33[31mError\33[0m: Replacement dictionary contains a non string for:',Key)
                sys.exit()

    def Fill(self,permissive=True):
        template_file = open(self.Source,'r')
        self.FilledTemplate = ''
        has_empty = False
        for template_line in template_file:
            if template_line.find(self.com_char)==0:
                continue
            template_args = find_substring(template_line,self.tmp_arg_mrk)
            line = template_line
            if len(template_args)%2 != 0:
                print('\33[31mError\33[0m: Template key marker error in:',template_line,'\n')
                print('The correct usage is:'+self.tmp_arg_mrk+'Some Template Argument'+self.tmp_arg_mrk)
                sys.exit()
            for index in range(len(template_args)//2):
                template_key = template_line[(template_args[2*index]+len(self.tmp_arg_mrk)):template_args[2*index+1]]
                template_pattern = self.tmp_arg_mrk+template_key+self.tmp_arg_mrk
                try:
                    line = line.replace(template_pattern,self.Dictionary[template_key])
                except:
                    print('\33[31mError\33[0m: Template key:',template_key,'requested by',self.Source,'was not found in dictionary')
                    sys.exit()        
                has_empty = (self.Dictionary[template_key] == '')
            for char in self.special_chars:
                line = line.replace(char,str('\\'+char))
            self.FilledTemplate += line
        if has_empty:
            wrn_msg = '\33[95mWarning\33[0m: '
            wrn_msg += 'data structure: '+str(self.Dictionary)+' has an empty template argument'
            if not permissive:
                wrn_msg += ', skkiped'
                self.FilledTemplate = ""
            else:
                wrn_msg += ', written with missing arguments'
            print(wrn_msg)
        template_file.close()

    def Write(self):
        self.Fill()
        WriteFile(self.Path,self.FilledTemplate)
