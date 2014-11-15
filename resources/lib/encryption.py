#http://stackoverflow.com/questions/6425131/encrpyt-decrypt-data-in-python-with-salt
import os, random, struct

try:
    import Crypto.Random
    from Crypto.Cipher import AES
    import hashlib
    ENCRYPTION_ENABLE = 1
except:
    ENCRYPTION_ENABLE = 0


# salt size in bytes
SALT_SIZE = 32

# number of iterations in the key generation
NUMBER_OF_ITERATIONS = 20

# the size multiple required for AES
AES_MULTIPLE = 16

def generate_key(password, salt, iterations):

    if ENCRYPTION_ENABLE == 0:
        return
    assert iterations > 0

    key = password + salt

    for i in range(iterations):
        key = hashlib.sha256(key).digest()

    return key

def pad_text(text, multiple):
    extra_bytes = len(text) % multiple

    padding_size = multiple - extra_bytes

    padding = chr(padding_size) * padding_size

    padded_text = text + padding

    return padded_text

def unpad_text(padded_text):
    padding_size = ord(padded_text[-1])

    text = padded_text[:-padding_size]

    return text

def encrypt(string):
    if ENCRYPTION_ENABLE == 0:
        return
    import base64

    return base64.b64encode(string)
def decrypt(string):
    if ENCRYPTION_ENABLE == 0:
        return
    try:
        import base64
        return base64.b64decode(string)
    except:
        return ''

def decrypt_file(key, in_filename, out_filename=None, chunksize=24*1024):
    """ Decrypts a file using AES (CBC mode) with the
        given key. Parameters are similar to encrypt_file,
        with one difference: out_filename, if not supplied
        will be in_filename without its last extension
        (i.e. if in_filename is 'aaa.zip.enc' then
        out_filename will be 'aaa.zip')
    """
    if ENCRYPTION_ENABLE == 0:
        return
    if not out_filename:
        out_filename = os.path.splitext(in_filename)[0]

    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        #iv = infile.read(16)
#        decryptor = AES.new(key, AES.MODE_CBC, iv)
#        key = generate_key(password, salt, NUMBER_OF_ITERATIONS)
        decryptor = AES.new(key, AES.MODE_ECB)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)

def decrypt_stream(key, response, out_filename, chunksize=24*1024):
        if ENCRYPTION_ENABLE == 0:
            return
#    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', response.read(struct.calcsize('Q')))[0]
        decryptor = AES.new(key, AES.MODE_ECB)

        with open(out_filename, 'w') as outfile:
            while True:
                chunk = response.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)

def encrypt_file(key, in_filename, out_filename=None, chunksize=64*1024):
    """ Encrypts a file using AES (CBC mode) with the
        given key.

        key:
            The encryption key - a string that must be
            either 16, 24 or 32 bytes long. Longer keys
            are more secure.

        in_filename:
            Name of the input file

        out_filename:
            If None, '<in_filename>.enc' will be used.

        chunksize:
            Sets the size of the chunk which the function
            uses to read and encrypt the file. Larger chunk
            sizes can be faster for some files and machines.
            chunksize must be divisible by 16.
    """
    if ENCRYPTION_ENABLE == 0:
        return
    if not out_filename:
        out_filename = in_filename + '.enc'

#    key = generate_key(key, salt, NUMBER_OF_ITERATIONS)

#    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(key, AES.MODE_ECB)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            #outfile.write(iv)

            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))

def read_salt(salt_filename):
    if ENCRYPTION_ENABLE == 0:
        return
    with open(salt_filename, 'rb') as infile:
        salt = infile.read(SALT_SIZE)

    return salt

def decrypt_dir(key,path,dir):
  if ENCRYPTION_ENABLE == 0:
        return
  current, dirs, files = os.walk(path+'/'+dir).next()

  for file in files:
    dec_file = decrypt(file)
    if (dec_file != ''):
      if not os.path.exists(path + '/'+dir+'/'+dec_file + '.JPG'):
        decrypt_file(key, path + '/' + dir + '/' + file,path + '/' + dir + '/' + dec_file + '.JPG')
      else:
        print "skipping " + file + ' ' + dec_file + "\n"

