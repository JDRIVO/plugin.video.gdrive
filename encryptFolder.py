from resources.lib import  encryption
#from subprocess import call

import sys
import re
import os

saltFile = str(sys.argv[1])
password = str(sys.argv[2])
source = str(sys.argv[3])
target = str(sys.argv[4])

encrypt = encryption.encryption(saltFile,password)
#encrypt.encryptString(file)
#print encrypt.decryptString(file)


def encrypt_dir(source, target):

  current, dirs, files = os.walk(source).next()

  for file in files:
    encFile = encrypt.encryptString(file)
    encrypt.encryptFile(str(source) + '/' + str(file), str(target) +'/'+ str(encFile))
    print str(source) + '/' + str(file)  + ' -> ' +  str(target) +'/'+ str(encFile)
  for dir in dirs:
    encDIR = encrypt.encryptString(dir)
    os.mkdir(str(target) + '/' + str(encDIR))
    encrypt_dir(str(source) + '/' + str(dir), str(target) +'/'+str(encDIR))
    print str(source) + '/' + str(dir) + ' -> ' + str(target) + '/' + str(encDIR)

#print encrypt.generateSalt()

encrypt_dir(source, target)
