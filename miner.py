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

BLOCKCHAIN = Blockchain()

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

    def run(self):
        if blockchain.THREAD_RESULTS:
            data = blockchain.THREAD_RESULTS.pop(0)
            sleep(1.0)
            if not BLOCKCHAIN.has(data['trans']):
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

            if BLOCKCHAIN.has(self.trans):
                self.trans = None
                blockchain.KILL_THREAD = True

            print('tr:', dump_trans(self.trans))

            if self.trans == None:
                self.request("GET", "/trans", '', self.headers)
                response = self.getresponse()
                print('/trans', response.status, response.reason)
                print('')
                
                if response.status == 200:
                    data = response.read()
                    self.trans = json.loads(str(data, encoding='utf-8'))

                    if BLOCKCHAIN.has(self.trans):
                        self.trans = None
                        return
                    else:
                        blockchain.KILL_THREAD = False

                    block = BLOCKCHAIN.gen_block(self.trans)

                    solve_task = threading.Thread(target=solve_block, args=(block, ))
                    sleep(1.0)
                    solve_task.start()

miner = SimpleHTTPClient()

while True:
    miner.run()
    print(BLOCKCHAIN)
    sleep(2.0)
    






