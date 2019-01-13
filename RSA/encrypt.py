import getopt
import sys
import base64
import math

def load(filename):
    file = open(filename, 'r')
    str = file.read()
    file.close()

    key = str[0:len(str)//2]
    n = str[len(str)//2:]

    key = base64.b64decode(key.encode())
    n = base64.b64decode(n.encode())

    key = int.from_bytes(key, "little")
    n = int.from_bytes(n, "little")

    return (key,n)

def encrypt(e, n, msg):
    m = int.from_bytes(str.encode(msg), "little")
    m = pow(m, e, n)
    bMsg = base64.b64encode(m.to_bytes(math.ceil(m.bit_length()/8), 'little'))    
    return bMsg.decode()

def decrypt(d, n, msg):
    s = base64.b64decode(msg.encode())
    s = int.from_bytes(s, 'little')
    m = pow( s, d, n)

    msg = m.to_bytes(math.ceil(m.bit_length()/8), 'little')
    msg = msg.decode()
    return msg


shortOpts = 'sedhi:o:k:'
longOpts = ['sign', 'encrypt', 'decrypt', 'help', 'infile', 'outfile', 'keyfile']

opts = ('h', '')
opts, args = getopt.getopt( sys.argv[1:], shortOpts, longOpts)

inputFile = ''
outputFile = ''
keyFile = ''

encryptOpt, decryptOpt, signOpt = False, False, False
cntOptions = 0
for option, arg in opts:
    if option in ('-o', '--outfile'):
        outputFile = arg
    elif option in ('-i', '--infile'):
        inputFile = arg
    elif option in ('-k', '--keyfile'):
        keyFile = arg
    elif option in ('-s', '--sign'):
        signOpt = True
    elif option in ('-e', '--encrypt'):
        encryptOpt = True
        cntOptions += 1
    elif option in ('-d', '--decrypt'):
        decryptOpt = True
        cntOptions += 1
    else:
        print("Usage: {0} [-sedoikh] [file]".format(sys.argv[0]))
        print("Options:")
        print('-s\tSign a file')
        print('-e\tEncrypt a file')
        print('-d\tDecrypt a file')
        print('-o file\tOutput file')
        print('-i file\tInput file')
        print('-k file\tKey file')
        print('-h\tThis Output')
        sys.exit()

if cntOptions != 1:
    print("Only one option of encrypt or decrypt can be used")
    sys.exit()

if keyFile == '':
    print('You must select a key to encrypt or decrypt.  Use -k ')
    sys.exit()

msg = ''
txt = ''

if inputFile != '':
    f = open(inputFile, 'r')
    msg = f.read()
else:
    msg = input()

keyFunc = decrypt
if encryptOpt:
    keyFunc = encrypt

key, n = load( keyFile )
msg = keyFunc(key, n, msg )

if outputFile != '':
    f = open(outputFile, 'w')
    print(msg, file=f)
else:
    print(msg)