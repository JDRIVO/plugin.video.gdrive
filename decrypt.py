import os
import sys

import encryptor

saltFile = sys.argv[1]
password = sys.argv[2]
filePath = sys.argv[3]
destinationPath = sys.argv[4]

decrypt = encryptor.Encryptor(saltFile, password)

encryptedFilename = os.path.basename(filePath)
filename = decrypt.decryptString(encryptedFilename)

destinationPath = os.path.join(destinationPath, filename)
decrypt.decryptFile(filePath, destinationPath)
