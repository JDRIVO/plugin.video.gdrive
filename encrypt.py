from resources.lib import  encryption
#from subprocess import call

import sys
import re
import os

saltFile = str(sys.argv[1])
password = str(sys.argv[2])
file = str(sys.argv[3])

encrypt = encryption.encryption(saltFile,password)
#encrypt.encryptFile(file)
encrypt.decryptFile(file+'1.enc')


def decrypt_dir(key,path,dir):

  current, dirs, files = os.walk(path+'/'+dir).next()

  for file in files:
    dec_file = decrypt(file)
    if (dec_file != ''):
      if not os.path.exists(path + '/'+dir+'/'+dec_file + '.JPG'):
        decrypt_file(key, path + '/' + dir + '/' + file,path + '/' + dir + '/' + dec_file + '.JPG')
      else:
        print "skipping " + file + ' ' + dec_file + "\n"

#print encrypt.generateSalt()
