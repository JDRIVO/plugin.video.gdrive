import os
import sys
import encryption

saltFile = sys.argv[1]
password = sys.argv[2]
filePath = sys.argv[3]
destinationPath = sys.argv[4]

encrypt = encryption.Encryption(saltFile, password)

fileName = os.path.basename(filePath)
encryptedFileName = encrypt.encryptString(fileName)
print(encryptedFileName)

destinationPath = os.path.join(destinationPath, encryptedFileName.decode("utf-8"))
encrypt.encryptFile(filePath, destinationPath)
