from http.client import HTTPConnection
from urllib.parse import urlencode
import json
from hashlib import md5

from time import sleep
import random
import string
from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import pkcs1_15

from blockchain import Blockchain, solve_block, dump_trans
import blockchain
import threading

import os.path

BLOCKCHAIN = Blockchain()

BADKEY_PATH = 'badkey'
PUBLIC_KEY_PATH = os.path.join(BADKEY_PATH, 'public.pem')
PRIVATE_KEY_PATH = os.path.join(BADKEY_PATH, 'private.pem')

if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
    BADKEY = RSA.generate(1024)
    open(PRIVATE_KEY_PATH, 'wb').write(BADKEY.export_key())
    open(PUBLIC_KEY_PATH, 'wb').write(BADKEY.publickey().export_key())
    PRIVATE_KEY = BADKEY
    PUBLIC_KEY = BADKEY.publickey()
else:
    PRIVATE_KEY = RSA.import_key(open(PRIVATE_KEY_PATH, 'rb').read())
    PUBLIC_KEY = RSA.import_key(open(PUBLIC_KEY_PATH, 'rb').read())

class SimpleHTTPClient(HTTPConnection):
    def __init__(self):
        super(SimpleHTTPClient, self).__init__('127.0.0.1:10000')
        self.headers = {
            "Content-type": "application/json",
            }

        print('blocks')
        self.request("GET", "/blocks", '', self.headers)
        response = self.getresponse()
        print('/blocks', response.status, response.reason)
        print('')
        
        if response.status == 200:
            data = response.read()
            blocks = json.loads(str(data, encoding='utf-8'))
            BLOCKCHAIN.load_chain(blocks)

        self.trans = None

    def fake_transaction(self, transaction):
        h = SHA256.new(bytes(transaction['id'], encoding='utf8') + PUBLIC_KEY.export_key())
        sign = pkcs1_15.new(PRIVATE_KEY).sign(h)

        data = {    
            'id': 'ImBadBot',  # transaction['id'],
            'key': str(PUBLIC_KEY.export_key(), encoding='utf8'),
            'sign': sign.hex()
        }
        return data

    def setup_bad(self):
        self.request("GET", "/blocks", '', self.headers)
        response = self.getresponse()
        print('/blocks', response.status, response.reason)

        if response.status == 200:
            data = response.read()
            blocks = json.loads(str(data, encoding='utf-8'))

            for block in blocks['chain']:
                BLOCKCHAIN.push(block)
            for block in blocks['temp']:
                BLOCKCHAIN.push(block)

            if self.trans == None:
                block = BLOCKCHAIN.get_last_block().copy()
                block['trans'] = self.fake_transaction(block['trans'])
                blockchain.KILL_THREAD = False
                self.trans = block['trans']

                solve_task = threading.Thread(target=solve_block, args=(block, ))
                solve_task.start()

    def run(self):
        if blockchain.THREAD_RESULTS:
            data = blockchain.THREAD_RESULTS.pop(0)
            if not BLOCKCHAIN.bad_has(data['trans']):
                self.request("POST", "/blockpass", json.dumps(data), self.headers)
                response = self.getresponse()
                print('/blockpass', response.status, response.reason)

        self.request("GET", "/blocks", '', self.headers)
        response = self.getresponse()
        print('/blocks', response.status, response.reason)

        if response.status == 200:
            data = response.read()
            blocks = json.loads(str(data, encoding='utf-8'))

            for block in blocks['chain']:
                BLOCKCHAIN.push(block)
            for block in blocks['temp']:
                BLOCKCHAIN.push(block)

            if not self.trans or BLOCKCHAIN.bad_has(self.trans):
                self.trans = None
                blockchain.KILL_THREAD = True

            print('tr:', dump_trans(self.trans))

            if self.trans == None:
                self.request("GET", "/temptrans", '', self.headers)
                response = self.getresponse()
                print('/trans', response.status, response.reason)
                print('')
                
                if response.status == 200:
                    data = response.read()
                    self.trans = json.loads(str(data, encoding='utf-8'))

                    if not self.trans or BLOCKCHAIN.bad_has(self.trans):
                        self.trans = None
                        return
                    else:
                        blockchain.KILL_THREAD = False

                    block = BLOCKCHAIN.gen_bad_block(self.trans)

                    solve_task = threading.Thread(target=solve_block, args=(block, ))
                    solve_task.start()

miner = SimpleHTTPClient()
miner.setup_bad()

while True:
    miner.run()
    print(BLOCKCHAIN)
    sleep(2.0)
    






