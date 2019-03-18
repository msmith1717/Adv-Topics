from __future__ import print_function
import sys
import json

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

import blockchain
import encrypt as RSA

# Python Version Check
if sys.version_info < (3,5):
    print('Python version detected: ' + str(sys.version_info[0]) + '.'+str(sys.version_info[1]))
    print('Python version required: 3.5 or higher')
    sys.exit(1)


# Initialize the System Wallet and main BlockChain
system_public = RSA.load('Creator_public.key')
system_private = RSA.load('Creator_private.key')

systemWallet = blockchain.Wallet('Creator', system_public, system_private)
MainChain = blockchain.BlockChain(systemWallet)

# flask server (start with 'flask run' command)
app = Flask(__name__)
app.config['TESTING'] = True


@app.route('/transactions', methods=['POST'])
def addTransactions(transactions=[]):
    try:
        transactionsJSON = request.get_json()
        transactions = []
        
        for transaction in transactionsJSON['transactions']:
            trans = blockchain.Transaction.parseJSON(transaction)
            transactions.append(trans)

        MainChain.mineBlock(transactions)
        return jsonify({'status':'ok', 'numAccepted':len(transactions)})
        
    except RuntimeError:
        pass

    return jsonify({'test':'apple'})

@app.route('/transactions/<blockID>', methods=['GET'])
def get_block(blockID, mode='html'):

    blockID = int(blockID)-1;
    it = MainChain.iterator(blockID)
    try:
        block = next(it);
        return render_template('displayblocks.html', blocks=[block])
    except StopIteration:
        return "Block {} does not exist".format(blockID+1)



@app.route('/transactions', methods=["GET"])
def get_blocks(start=0, mode='html'):

    # Handle start GET argument
    # We might be outside the Request context
    try:
        s = request.args.get('start')
        if s != None:
            s = int(s)
            if s >= 1:
                start = int(s) - 1
    except RuntimeError:
        pass

    blocks = []
    it = MainChain.iterator(start)
    for block in it:
        blocks.append(block)

    return render_template('displayblocks.html', blocks=blocks)