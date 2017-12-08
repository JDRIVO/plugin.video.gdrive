from resources.lib import  encryption
#from subprocess import call

import sys

saltFile = str(sys.argv[1])
password = str(sys.argv[2])
stringToEncrypt = str(sys.argv[3])

encrypt = encryption.encryption(saltFile,password)
#encrypt.encryptString(file)
print encrypt.encryptString(stringToEncrypt)
#encrypt.decryptStream
#encrypt.encryptFile(file)
#encrypt.decryptFile(file+'.enc')

