import sys,os

##
##  String Manipulation
##

def CSS(n,m=0):
            out = ''
            for number in range(n-m+1):
                out += str(n-number) + (',' if number != (n-m) else '')
            return out

def find_substring(string, substring):
    substring_length = len(substring)    
    def recurse(locations_found, start):
        location = string.find(substring, start)
        if location != -1:
            return recurse(locations_found + [location], location+substring_length)
        else:
            return locations_found
    return recurse([], 0)

##
## File Manipulation
## 

def MakeDir(Path):
        line = 'mkdir -p '+Path
        if os.path.exists(Path):
            print("\33[31mError\33[0m: MakeDir:",Path,"already exists")
            sys.exit()
        os.system(line)
    
def WriteFile(Path,Content):
    F = open(Path,"w+")
    F.write(Content)
    F.close()

def CopyFile(Orig,Dest):
    cmd = 'cp '+Orig+' '+Dest
    os.system(cmd)