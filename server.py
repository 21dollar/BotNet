import http.server

from http.server    import HTTPServer, BaseHTTPRequestHandler
from hashlib        import sha256
from urllib.parse   import urlparse, parse_qs

import json
import httpx
import random
import blockchain
from blockchain import Blockchain, dump_block

from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import pkcs1_15


f = open('1.txt', 'rb')
lines = len(f.read().splitlines())
hash_d = 'fcea920f7412b5da7be0cf42b8c93759'
TASKS = [{
    'hash': hash_d,
    'offset': offset_d
} for offset_d in range (0, lines, 10000)]

TRANSACTIONS = []
TEMP_TRANSACTIONS = []

BLOCKCHAIN = Blockchain()

def print_stat():
    print('Transactions:')
    print('\n'.join(
        trans['id'] + ' : ' + trans['sign'][:8]
        for trans in TRANSACTIONS
        )
    )
    print(BLOCKCHAIN)

print_stat()


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def Authorization(self):
        auth_data = self.headers.get('Authorization', None)
        uid, sign = auth_data[:8], auth_data[8:]
        
        if not BLOCKCHAIN.verify(uid, sign, b'123456'):
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str.encode(json.dumps({ 'status' : 'incorrect password' })))
            return False
        return True

    def do_GET(self):

        args = parse_qs(urlparse(self.path).query)

        if self.path.startswith('/trans'):
            if TRANSACTIONS:
                task = TRANSACTIONS[0]
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str.encode(json.dumps(task), encoding='utf-8'))
            else:
                self.send_response(204)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str.encode(json.dumps({ 'status' : 'no transactions' })))

        if self.path.startswith('/temptrans'):  
            if TEMP_TRANSACTIONS:
                task = TEMP_TRANSACTIONS[0]
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str.encode(json.dumps(task), encoding='utf-8'))
            else:
                self.send_response(204)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str.encode(json.dumps({ 'status' : 'no transactions' })))

        elif self.path.startswith('/blocks'):
            blocks = {
                'chain': BLOCKCHAIN.chain,
                'temp': BLOCKCHAIN.temp
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str.encode(json.dumps(blocks), encoding='utf-8'))

        elif self.path.startswith('/task'):
            if not self.Authorization():
                return

            if TASKS:
                task = TASKS.pop(0)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str.encode(json.dumps(task), encoding='utf-8'))
            else:
                self.send_response(204)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(str.encode(json.dumps({ 'status' : 'no tasks' })))

    def do_POST(self):
        args = parse_qs(urlparse(self.path).query)

        body    = self.rfile.read(int(self.headers['content-length']))
        payload = json.loads(body)

        if self.path.startswith('/pass'):
            if not self.Authorization():
                return
            hash = payload['hash']
            password = payload['password']

            print('PASSWORD:', password)
            f = open('answers.txt', 'a+')
            f.write("%s: '%s'\n"%(hash, password))
            f.close()
            TASKS.clear()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str.encode(json.dumps({'status' : 'task complete'}), encoding='utf-8'))

        elif self.path.startswith('/auth'):

            TRANSACTIONS.append(payload)
            TEMP_TRANSACTIONS.append(payload)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'ok')
            pass

        elif self.path.startswith('/blockpass'):
            
            BLOCKCHAIN.push(payload)
            if TRANSACTIONS and BLOCKCHAIN.has(TRANSACTIONS[0]):
                TRANSACTIONS.pop(0)
            if TEMP_TRANSACTIONS and BLOCKCHAIN.bad_has(TEMP_TRANSACTIONS[0]):
                TEMP_TRANSACTIONS.pop(0)

            print_stat()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'ok')




#1234567,  7,        fcea920f7412b5da7be0cf42b8c93759      
#Capslock, 1057431,  b3e38568360f5f7ad2e74bc44328fd11
#ikaika17, 7436857,  4c71933a3d4f2e9ef7dd9e1ac111fa37
#WEAVER6,  10503226, 313d5bd5f7040e5c4d60ab243188d25b



print("Server start")
httpd = HTTPServer(('localhost', 10000), SimpleHTTPRequestHandler)
httpd.serve_forever()