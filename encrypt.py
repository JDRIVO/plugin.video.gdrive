import os
import sys

import encryptor

saltFile = sys.argv[1]
password = sys.argv[2]
filePath = sys.argv[3]
destinationPath = sys.argv[4]

encrypt = encryptor.Encryptor(saltFile, password)

filename = os.path.basename(filePath)
encryptedFilename = encrypt.encryptString(filename)
print(encryptedFilename)

destinationPath = os.path.join(destinationPath, encryptedFilename)
encrypt.encryptFile(filePath, destinationPath)
