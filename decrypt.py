import os
import sys
import encryption

saltFile = sys.argv[1]
password = sys.argv[2]
filePath = sys.argv[3]
destinationPath = sys.argv[4]

decrypt = encryption.Encryption(saltFile, password)

encryptedFileName = os.path.basename(filePath)
fileName = decrypt.decryptString(encryptedFileName)

destinationPath = os.path.join(destinationPath, fileName.decode("utf-8"))
decrypt.decryptFile(filePath, destinationPath)
