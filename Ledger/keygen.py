'''
Author: Brian Sea

Implementation of RSA key generation 
'''
# Allow Python 2 to work up to the python version check
from __future__ import print_function

import random
import base64
import math
import time
import sys

# Python Version Check
if sys.version_info < (3,5):
    print('Python version detected: ' + str(sys.version_info[0]) + '.'+str(sys.version_info[1]))
    print('Python version required: 3.5 or higher``')
    sys.exit(1)

# range returns an entire array... this is too memory intensive
# return one range element at a time
def yRange( start, stop, step = 1 ):
    while start < stop:
        yield start
        start += step    


# Provides a random prime of at maximum numBits length
def getPrime(numBits):
    upperBound = 2**(numBits)
    lowerBound = 2**(numBits-2)

    # Pick a random integer in our range to start with
    num = random.randrange(lowerBound, upperBound, 1)
    # if the number is even and not two, then add one
    # because even numbers (expect two) cannot be prime        
    if (not num & 1) and (num != 2):
        num = num + 1
    
    
    # Fermat's Primality Test
    # Others:
    # (a) Solobay-Strassen,
    # (b) Miller-Rabin,
    # (c) Baillie-PSW
    #
    # I understand Fermat's best for now
    def isPrime(num):
        if num == 2:
            return True

        if not num & 1:
            return False
        
        return pow(2, num-1, num) == 1

    # Keeps track of the number of rounds of division we need to complete
    wentOver = 1
    # Find the prime directly after this integer
    while not isPrime(num):

        num = num + 2

        # If we went over our bit-length, divide by two and keep going
        while num.bit_length() > numBits:
			# The number got too large so we divide by
			# 2*the number of rounds we went over
            num = num >> (wentOver*1)
            wentOver += 1

            # if the number is even and not two, then add one
            # because even numbers (expect two) cannot be prime        
            if (not num & 1) and (num != 2):
                num = num + 1
    return num

def gcd(m, n):
    r = 1

    if m > n:
        m,n = n,m    

    while r != 0:
        r = m % n
        m = n
        n = r

    return m

def pickE( totient ):
    lowerBound = pow( 2, 3000)

    e = random.randrange(lowerBound, totient)
    while e <= 1 or gcd(e, totient) != 1:
        e = e + 1
        if e > totient:
            e = e // 2
    return e

def calcD( e, totient ):

    if e > totient:
        tmp = e
        e = totient
        totient = tmp

    # Answers the question m = a * (n) + b
    def extEuclid(m, n):
        # Our Ending conditions
        a0, a1, b0, b1 = 1, 0, 0, 1

        while n != 0:
             r, m, n = m // n, n, m % n
             a0, a1 = a1, a0 - r*a1
             b0, b1 = b1, b0 - r*b1
        
        return m, a0, b0


    goal, a, b = extEuclid( totient, e )
    if goal != 1:
        raise Exception("No Mod Inverse!")

    return b % totient

if __name__ == '__main__':
    numBits = 2048
    start_time = time.time()
    q = p = getPrime(numBits)
    while p == q: 
        q = getPrime(numBits)

    n = p*q
    totient = (p-1)*(q-1)

    e = pickE( totient )
    d = calcD( totient, e )
    end_time = time.time()

    # Encoded E, D, and N to Base-64 strings
    eEncoded = base64.b64encode(e.to_bytes( math.ceil(e.bit_length()/8), 'little'))
    dEncoded = base64.b64encode(d.to_bytes( math.ceil(d.bit_length()/8), 'little'))
    nEncoded = base64.b64encode(n.to_bytes( math.ceil(n.bit_length()/8), 'little'))
    eEncoded = eEncoded.decode()
    dEncoded = dEncoded.decode()
    nEncoded = nEncoded.decode()

    # Print to files
    print( eEncoded+nEncoded, file=open('public.key', 'w'))
    print( dEncoded+nEncoded, file=open('private.key', 'w'))


    '''
    Test output for RSA encryption
    print( "({0} bits) P: {1}\n({2} bits) Q: {3}".format(p.bit_length(), p, q.bit_length(), q) )
    print( "({0} bits) N: {1}".format(n.bit_length(), n) )
    print( "({0} bits) Totient: {1}".format(totient.bit_length(), totient) )
    print( "({0} bits) E: {1}".format(e.bit_length(), e) )
    print( "({0} bits) D: {1}".format(d.bit_length(), d) )
    '''
    print( "Time Elased: {0} seconds".format(end_time - start_time))
    '''
    # Test Encryption
    M = 14

    C = M**e % n
    aM = C**d % n

    print("Test M:{0}, C:{1}, aM:{2}".format(M, C, aM))
    if( aM == M ):
        print("Passed")
    else:
        print("Failed")
    '''
