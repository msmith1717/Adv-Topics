# Allow Python 2 to work up to the python version check
from __future__ import print_function

import getopt
import sys
import base64
import math

# Python Version Check
if sys.version_info < (3,5):
    print('Python version detected: ' + str(sys.version_info[0]) + '.'+str(sys.version_info[1]))
    print('Python version required: 3.5')
    sys.exit(1)


"""
    Utilities for using, encrypting, and decrypting data using the
    RSA algorithm.  Keys must be in Base64.
"""

"""
    Loads and returns the keys from a file
    Returns: a tuple of the (Key, N) as integers
"""
def load(filename):
    file = open(filename, 'r')
    str = file.read()
    file.close()

    key = str[0:len(str)//2]
    n = str[len(str)//2:]

    key = base64StringToInt(key)
    n = base64StringToInt(n)

    return (key,n)


"""
    Converts a Base64 String to an integer
"""
def base64StringToInt(s):
    return int.from_bytes(base64.b64decode(s.encode()), 'little')

"""
    Converts an integer to a Base64 String
"""
def intToBase64String(n):
    return base64.b64encode(n.to_bytes(math.ceil(n.bit_length()/8), 'little')).decode()

"""
    Encrypts msg using a complete Base64 key
"""
def encryptWithKey(s, msg):
    key = s[0:len(s)//2]
    n = s[len(s)//2:]
    return encrypt(base64StringToInt(key), base64StringToInt(n), msg)

"""
    Decrypts msg using a complete Base64 key
"""
def decryptWithKey(s, msg):
    key = s[:len(s)//2]
    n = s[len(s)//2:]

    return decrypt(base64StringToInt(key), base64StringToInt(n), msg)

"""
    Encrypts msg using two integers e and n from the RSA algorithm
    Parameters:
        e: an integer representing the encryption key from RSA
        n: an integer representing the base from RSA
        msg: the message to encrypt as a UTF-8 string
    Returns: a Base64 String representing the encrypted message

    RSA: C = M^e mod n 
"""
def encrypt(e, n, msg):
    m = int.from_bytes(str.encode(msg), "little")
    m = pow(m, e, n)
    return intToBase64String(m)

"""
    Decrypts msg using two integers d and n from the RSA algorithm
    Parameters:
        d: an integer representing the decryption key from RSA
        n: an integer representing the base from RSA
        msg: the message to decrypt as a Base64 encoded UTF-8 string
    Returns: a UTF-8 encoded String representing the decrypted message
"""
def decrypt(d, n, msg):
    s = base64.b64decode(msg.encode())
    s = int.from_bytes(s, 'little')
    m = pow( s, d, n)

    msg = m.to_bytes(math.ceil(m.bit_length()/8), 'little')
    msg = msg.decode()
    return msg


"""
    Used if we want to encrypt/decrypt/sign messages as a stand-alone program
"""
if __name__ == '__main__':

    # Set up our command-line options (see getopt for format)
    shortOpts = 'edhi:o:k:'
    longOpts = ['encrypt', 'decrypt', 'help', 'infile', 'outfile', 'keyfile']

    opts = ('h', '')
    opts, args = getopt.getopt( sys.argv[1:], shortOpts, longOpts)

    # File to read from
    inputFile = ''
    outputFile = ''
    keyFile = ''

    # Remember if we need to encrypt, decrypt, or sign
    # Only one of encrypt/decrypt is allowed
    encryptOpt, decryptOpt, signOpt = False, False, False
    cntOptions = 0

    # Handle any command-line arguments provided
    for option, arg in opts:
        if option in ('-o', '--outfile'):
            outputFile = arg
        elif option in ('-i', '--infile'):
            inputFile = arg
        elif option in ('-k', '--keyfile'):
            keyFile = arg
        elif option in ('-e', '--encrypt'):
            encryptOpt = True
            cntOptions += 1
        elif option in ('-d', '--decrypt'):
            decryptOpt = True
            cntOptions += 1
        else:  # Unknown command-line argument was provided
            print("Usage: {0} [-sedoikh] [file]".format(sys.argv[0]))
            print("Options:")
            print('-e\tEncrypt a file')
            print('-d\tDecrypt a file')
            print('-o file\tOutput file')
            print('-i file\tInput file')
            print('-k file\tKey file')
            print('-h\tThis Output')
            sys.exit()

    # User provided both encrypt and decrypt options
    if cntOptions != 1:
        print("Only one option of encrypt or decrypt can be used")
        sys.exit()

    # No keys provided.  We don't support keys on the command-line
    if keyFile == '':
        print('You must select a key to encrypt or decrypt.  Use -k ')
        sys.exit()

    msg = ''
    txt = ''

    # Have an input file; Read it into our message
    # If there's no input file, then read from stdin
    f = sys.stdin
    if inputFile != '':
        try:
            f = open(inputFile, 'r')
        except FileNotFoundError:
            print('File Not Found: {}'.format(inputFile))
            print('Exiting...')
            sys.exit()
    else:
        print("Type message to encrypt (Control-D to end):\n")
    msg = f.read()
    print()

    # Pick with function to use...
    keyFunc = decrypt
    if encryptOpt:
        keyFunc = encrypt

    # load our key and encrypt/decrypt the message
    key, n = load( keyFile )
    msg = keyFunc(key, n, msg)

    # Output to the file or stdout if not provided
    f = sys.stdout
    if outputFile != '':
        f = open(outputFile, 'w')
    print(msg, file=f)
    