'''
Author: Brian Sea

Implementation of simple blockchain using Proof Of Work (POW)
'''

# Allow Python 2 to work up to the python version check
from __future__ import print_function

import time
import hashlib
import base64
import encrypt

import json
import sys

# Python Version Check
if sys.version_info < (3,5):
    print('Python version detected: ' + str(sys.version_info[0]) + '.'+str(sys.version_info[1]))
    print('Python version required: 3.5 or higher')
    sys.exit(1)

"""
Represents a transaction on blockchain.
Attributes:
    timestamp: UNIX time this transaction was created
    recv: The account of the receiver (public key)
    sender: The account of the sender (public key)
    amount: number of coins sent from sender to recv
"""
class Transaction:

    """
    Constructs a timestamped transaction
        recv: the Wallet of the receiver
        amount: number of coins to send
        sender: Wallet of the sender; None indicates 
                a transaction by the System
        hash: the SHA256 hash of the transaction
            signed by the private key of the sender or, if the 
			transaction is a System transaction, by the private key
			of the receiver (a miner reward)
    """
    def __init__(self, recv, amount = 0, sender = None):
        self.timestamp = time.time()
        self.recv = recv.public+recv.n
        self.amount = amount
        self.sender = None

        if sender != None:
            self.sender = sender.public+sender.n

        # Calculate the SHA256 hash 
        self.hash = self.sha256()

        # Sign the hash if the sender is not the System
        if sender != None:
            self.hash = encrypt.encryptWithKey(sender.private+sender.n, self.hash)
        # System Transactions get signed with private key of the receiver
        # because this is a miner reward
        else:
            self.hash = encrypt.encryptWithKey(recv.private+recv.n, self.hash)

        # Verify the transaction was created correctly
        self.verify()


    """
        Validates the transaction; Throws an Exception if invalid

        Checks:
            Hash match -- unsigns and verify hash data
            Amount -- verifies that amount is greater than zero
    """
    def verify(self):

        # Unsigned the hash   
        unsigned_hash = self.hash
        if self.sender != None:
            unsigned_hash = encrypt.decryptWithKey(self.sender, self.hash)
        else:
        # If the sender is the System then unsign it with the receiver's ID
            unsigned_hash = encrypt.decryptWithKey(self.recv, self.hash)
        
        if self.sha256() != unsigned_hash:
            raise Exception('Hash Mismatch')
        
        if self.amount <= 0:
            raise Exception("Amount <= 0")

        return True
    
    """
        Calculates the SHA256 hash of the current state of data
        Data used in the hash:
            Receiver ID
            Sender ID
            Amount 
            Timestamp
    """
    def sha256(self):
        hasher = hashlib.sha256()
        hasher.update(self.recv.encode())

        if self.sender != None:
            hasher.update(self.sender.encode())
        else:
            hasher.update('System'.encode())

        hasher.update(str(self.amount).encode())
        hasher.update(str(self.timestamp).encode())
        return hasher.hexdigest()

    """
        returns a String in JSON format
    """
    def __repr__(self):
        return json.dumps(self.__dict__)

"""
    Represents a block header (and linked transactions) on our blockchain
    Attributes:
        index: position on the blockchain (starts at one)
        timeStamp: UNIX time of block creation (when mined)
        prevHash: The hash of the block directly previous to this one
		currHash: The hash of this block
        transactions: All transactions linked with this block header
        nonce: During the mining process an integer is discovered such
            that the hash of the block has the number of leading zeros
            equal to or more than the 'difficulty' setting from our blockchain
        merkleRoot: The root of a Merkle tree created by a layered hashing
            of the transactions. This hash is used to verify order and
            data integrity of all linked transactions in a more computationally
            efficient manner
"""
class Block:

    """
        Constructs a block header for our blockchain.  Notes:
		(1) The block is NOT hashed -- it needs to be mined correctly first. 
		(2) Transactions are NOT verified, but the Merkle root is generated
		(3) The block is timestamped

        Parameters:
            transactions: the transactions to include in this block
            lastBlock: the block directly previous to this object; Used to link
                the current block to be directly ahead of lastBlock
    """
    def __init__(self, transactions, lastBlock ):
        self.index = 1
        self.timeStamp = time.time()
        self.prevHash = None

		# transactions are NOT verified immediately
        self.transactions = transactions
        self.nonce = 0
        self.merkleRoot = self.generateMerkleRoot()

        if lastBlock != None:        
            self.index = lastBlock.index+1
            self.prevHash = lastBlock.currHash
        

		# This block does not get hashed immediately
        self.currHash = None

    """
        Returns a JSON of the current block
    """
    def __repr__(self):
        return json.dumps(self.__dict__)

    """
        Generates the Merkle Root of a tree using the hashes
        of the transactions currently linked to this Block header
    """
    def generateMerkleRoot(self):
        
        # Treated as queue
        q = []
        
        # Hash each linked transaction and put it into the queue
        # The hash of each transaction includes the SIGNED 
        # transaction hash
        for trans in self.transactions:
            hasher = hashlib.sha256()
            hasher.update(trans.sha256().encode())
			# add in the current hash of the transaction
            hasher.update(trans.hash.encode())
            q.append(hasher.hexdigest())

        # Cycle through our hashes, combine each pair of hashes, and
        # enqueue the new hash.  Continue until only one is left
        while len(q) > 1:
            hasher = hashlib.sha256()
            hasher.update(q.pop(0).encode())
            hasher.update(q.pop(0).encode())
            q.append(hasher.hexdigest())

        # The last one is our Merkle Root!
        return q.pop(0)

    """
        Verifies an individudal block and any inter-transaction relationships
        Throws an exception if a validity check fails
        Checks:
            Hash match -- verifies hash data matches current data
            Transactions -- verifies each transaction (see Transaction class)
            Merkle Root -- regenerates the Merkele Root and verifies current data
    """
    def verify(self):
        id = 'Block {0}: '.format(self.index)
        
        # Check the current hash
        if self.sha256() != self.currHash:
            raise Exception(id+'Hash Mismatch')

        # verify each known transaction
        for idx, trans in enumerate(self.transactions):
            try:
                trans.verify()
            except Exception as err:
                raise Exception(id+'Transaction {0}: {1}'.format(idx+1, str(err)))

        # Check the Merkle Root
        if self.generateMerkleRoot() != self.merkleRoot:
            raise Exception(id+'Merkel Root mismatch')


        return True

    """
        Calculates the SHA256 hash of the data currently linked with this Block
        Data used in the hash:
            Block index
            Timestamp
            Hash of the previous block
            Merkle Root
            Nonce discovered during the mining process
    """
    def sha256(self):
        hasher = hashlib.sha256()
        
        hasher.update(str(self.index).encode())
        hasher.update(str(self.timeStamp).encode())
        hasher.update(str(self.prevHash).encode())
        hasher.update(str(self.merkleRoot).encode())
        hasher.update(str(self.nonce).encode())

        hash = hasher.hexdigest()
        return hash

"""
    Represents a single Block Chain.  Each block chain is a 
        doubly-linked list of Blocks which is iterable.
    Static Attributes:
        difficulty: The current difficulty level hashes must meet
            during the mining process
        MINER_REWARD: The current reward this chain provides for each block
            mined for this chain
    Internal Class -- Node: represents an internal Node in our doubly-linked list
    Attributes:
        tail: the last block of the chain
        head: the first block the chain
"""
class BlockChain:
    difficulty = 2
    MINER_REWARD = 10
    SEED = 100
    
    """
        Internal containers for our doubly-linked list
    """
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None
            self.prev = None

    class List_Iterator:
        def __init__(self, list):
            self.__iter = list.head

        def __iter__(self):
            return self

        def __next__(self):
            if self.__iter == None:
                raise StopIteration
            
            block = self.__iter.data
            self.__iter = self.__iter.next
            return block

    """
        Constructs a Block Chain and creates a Genesis Block signed by 
        the creator.  The Genesis Block provides 100 coins to the creator.
    """
    def __init__(self, creator):
        
        self.tail = None
        originalTransaction = [Transaction(creator, BlockChain.SEED)]
        genData, rejected = self.mineBlock(originalTransaction)
    
        self.head = BlockChain.Node(genData)
        self.tail = self.head

    # Return an iterator for the list
    def __iter__(self):
        return BlockChain.List_Iterator(self)
        
    def iterator(self, start=0):
        it = iter(self)
        
        s = 0
        while s < start:
            next(it)
        return it

    # Grab the first block of the chain
    def getFirstBlock(self):
        if self.head == None:
            return None
        return self.head.data

    # Grab the last block of the chain
    def getLastBlock(self):
        if self.tail == None:
            return None
        return self.tail.data

    # Add a block to the end of the chain
    def addBlock(self, block):
        if self.tail == None:
            self.head = BlockChain.Node(block)
            self.tail = self.head
        else:
            self.tail.next = BlockChain.Node(block)
            self.tail = self.tail.next

    """
        Verifies the Block Chain and all inter-block checks
        Throws an exception if a validity check fails
        Checks:
            Individual Block checks (see Block class)
            Verifies that each Transaction in each block can be completed
                (i.e. checks that senders have enough coin to complete each)
            Verifies that each block's prevHash matches the computed hash of the
                previous block
    """
    def verify(self):
        prevBlock = None
        for block in self:
            # Block self-verifies
            try:
                block.verify()
            except Exception as err:
                raise Exception('Chain Verify Failure: {0}'.format(str(err)))
            
            # Verify transaction amount with block chain
            for idx,transaction in enumerate(block.transactions):
                try:
                    self.verifyTransaction(transaction, block.index-1)
                except Exception as err:
                    raise Exception('Block {0}: Transaction {1}: {2}'.format(block.index, idx, str(err)))

            # Verify previous hash linkage
            if block.prevHash != None:
                if block.prevHash != prevBlock.currHash:
                    raise Exception('Block {0}: Previous hash does not match current hash'.format(block.index))
            else:
                # Genesis Block is the only one allowed to
                # not have a previous hash
                if block != self.getFirstBlock():
                    raise Exception('Block {0}: Previous hash missing!'.format(block.index))
            prevBlock = block

        return True

    """
        Verifies that a transaction can be completed on this BlockChain.
        Exceptions are thrown if a validity check fails
            transaction: the transaction to check against balance
            blockNumber: the final block to include in our check; None
                indicates the we should include the entire block chain.
                This parameter allows the checking of transaction validity on
                partial chains (used in check validity of transactions
                which are in the middle of a block chain)
    """
    def verifyTransaction(self, transaction, blockNumber = None):
        verified = True

        # System transactions always work
        if transaction.sender != None:
            if blockNumber == None:
                blockNumber = self.getLastBlock().index
            
            balance = self.getBalance(transaction.sender, blockNumber)
            if balance < transaction.amount:
                raise Exception("Invalid Transaction: Balance too low: Have {0} but need {1}".format(balance, transaction.amount))

            try:
                transaction.verify()
            except Exception as err:
                raise Exception( 'Invalid Transaction: ' + str(err) )

        return verified

    """
        Attempts to mine a new block on this Block Chain
        Parameters:
            transactions: the transactions to include on this chain; These
                are re-verified before being put into the block
            miner:  the Wallet of the current miner; Used to sign
                our reward so that other miners can't easily steal the 
                reward since this included in calculating the nonce and in
                the generation of the Merkle Root
        Returns: A tuple of the block created and all all rejected transactions
    """
    def mineBlock(self, transactions, miner = None):

        rejectedTransactions = []

        # Sent one transaction, so put it into a list
        if not isinstance(transactions, list):
            transactions = [transactions]

        # Verify that each transaction can happen. Otherwise, remove it.
        # We do not include other transactions currently being considered
        # so that we can avoid some double-spending scenarios
        for idx,trans in enumerate(transactions):
            try:
                self.verifyTransaction(trans)
            except Exception as err:
                rejectedTransactions.append(trans)
                del transactions[idx]

        # We only start mining if there are enough transactions to include
        block = None      
        if len(transactions) > 0:
            # add the miner reward
            if miner != None:
                reward = Transaction(miner, BlockChain.MINER_REWARD)
                transactions.insert(0, reward)

            block = Block(transactions, self.getLastBlock())
            block.currHash = block.sha256()

            # Find the correct nonce such that the hash has at least the number
            # of leadering zero indicated by the current difficulty of 
            # the Block Chain
            while block.currHash[:BlockChain.difficulty] != BlockChain.difficulty*'0':
                block.nonce = block.nonce + 1
                block.currHash = block.sha256()

            # Add the Block to the end of the Chain
            self.addBlock(block)

        # Return the created block and all rejected Transactions
        return (block, rejectedTransactions)

    """
        Gets the balance of an ID
        Parameters:
            id: The account ID to check
            blockNumber: The final block to include; None indicates to check 
                the entire chain.  This parameter allows for the checking
                of a balance on a partial chain.
    """
    def getBalance(self, id, blockNumber = None):
        balance = 0

        # if None then check whole chain
        if blockNumber == None and self.getLastBlock() != None:
            blockNumber = self.getLastBlock().index

        # Go up to and INCLUDE the block indicated by blockNumber
        idx = self.getFirstBlock().index
        for block in self:
            if idx > blockNumber:
                break

            # Add or subtract to our running balance according to IDs
            for transaction in block.transactions:
                if transaction.sender == id:
                    balance -= transaction.amount
                if transaction.recv == id:
                    balance += transaction.amount
            idx += 1

        return balance
"""
    Represents the known identities and keys of a person.  The values can
    be, an usually are, None because not all information can (or should be)
    known at all times.  For example, the only time private keys are known
    will be by the issuer of each Transaction.
"""
class Wallet:
    def __init__(self, realname, public, private, n):
        self.name = realname
        self.public = public
        self.private = private
        self.n = n
    
    def __repr__(self):
        return json.dumps(self.__dict__)

"""
    Testing the Block Chain
"""
if __name__ == '__main__':
    
    # Identities of our three personalities
    # Setup a dictionary of the keys
    names = ['A', 'B', 'Miner']
    keys = dict()
    for person in names:
        print('Reading Pair {0}...'.format(person))
        privKey,n = encrypt.load(person+'_private.key')
        pubKey,n = encrypt.load(person+'_public.key')

        pubKey = encrypt.intToBase64String(pubKey)
        privKey = encrypt.intToBase64String(privKey)        
        n = encrypt.intToBase64String(n)

        keys[person] = Wallet(person, pubKey, privKey, n)
    
    """
    Test Transactions beyond the Genesis Block 
    ** One transaction per block
        Transaction 1: A->B 40 (PASSES)
        Transaction 2: B->A 15 (PASSES)
        Transaction 3: A->B 60 (PASSES)
        Transaction 4: A->B 20 (FAILS)
        Transaction 5: B->A 50 (PASSES)
    """

    # Transactions are organized as lists of lists
    testTransactions = [
        Transaction( keys['B'], 40, keys['A'] ),
        Transaction( keys['A'], 15, keys['B'] ),
        Transaction( keys['B'], 60, keys['A'] ),
        Transaction( keys['B'], 20, keys['A'] ),
        Transaction( keys['A'], 50, keys['B'] )
    ]

    creator = keys['A']
    print('Creating BlockChain with {0} as Creator...'.format(creator.name))
    sys.stdout.flush()

    chain = BlockChain(creator)
    for idx, transaction in enumerate(testTransactions):
        
        # If it's a single transaction, put it into a list
        if not isinstance(transaction, list):
            transaction = [transaction]
        
        # assign the sender and receiver IDs
        for trans in transaction:
            sender = None
            recvr = None
            for name, key in keys.items():
                ID = key.public+key.n
                if ID == trans.sender:
                    sender = name
                if ID == trans.recv:
                    recvr = name

            # Print out the status of each Transaction
            print('Transaction (Amount: {0}): {1}->{2}'.format(
                trans.amount, sender, recvr
            ), end=' ')
            sys.stdout.flush()
        
            try:
                chain.verifyTransaction(trans)
                print('Accepted')
            except Exception as err: 
                print('Declined: ' + str(err))

        print('Mining Block {0}...'.format(idx+1), end=' ')
        sys.stdout.flush()

        block, rejected = chain.mineBlock(transaction, keys['Miner'])

        # Print out the result of the Block being Mined
        if block != None:
            print( '({0}, {1})'.format(block.nonce, block.currHash))
        else:
            print("No Block Mined (All Transactions Rejected)")
        
        print()
    print()

    # Verify our chain
    print('Chain Verification... ', end=' ')
    sys.stdout.flush()
    try:
        chain.verify()
        print('Verified')
    except Exception as err:
        print(str(err))
        
    print('Blocks in Chain: {}'.format(chain.getLastBlock().index))
    # Print out final balances of our three identities
    for name, wallet in keys.items():
        print("Amount in {0}'s Wallet: {1}".format(name, chain.getBalance(wallet.public+wallet.n)))
