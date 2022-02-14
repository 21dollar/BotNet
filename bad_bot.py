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

f = open('1.txt', 'rb')
lines = f.read().splitlines()


class SimpleHTTPClient(HTTPConnection):
    def __init__(self):
        super(SimpleHTTPClient, self).__init__('127.0.0.1:10000')
        
        self.id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        self.key = RSA.generate(1024)

        message = b'123456'    
        h = SHA256.new(message)
        signature = pkcs1_15.new(self.key).sign(h).hex()
        self.headers = {
            "Content-type": "application/json",
            'Authorization': self.id + signature 
            }

    def auth(self):
        key = self.key.publickey().export_key()

        h = SHA256.new(bytes(self.id, encoding='utf8') + key)
        sign = pkcs1_15.new(self.key).sign(h)

        data = {    
            'id': self.id,
            'key': str(key, encoding='utf8'),
            'sign': sign.hex()
        }

        self.request("POST", "/auth", json.dumps(data), self.headers)
        response = self.getresponse()
        print('AUTH:', response.status, response.reason)

    def run(self):
        key = self.key.publickey().export_key()

        h = SHA256.new(bytes(self.id, encoding='utf8') + key)
        sign = pkcs1_15.new(self.key).sign(h)

        data = {    
            'id': self.id,
            'key': str(key, encoding='utf8'),
            'sign': sign.hex()
        }

        self.request("POST", "/chel", json.dumps(data), self.headers)
        response = self.getresponse()
        print('chel:', response.status, response.reason)



        #self.request("GET", "/task", '', self.headers)
        response = self.getresponse()
        print(response.status, response.reason)
        print('')
        
        if response.status == 200:
            data = response.read()
            task = json.loads(str(data, encoding='utf-8'))

            hash_d = bytes.fromhex(task['hash'])
            offset = task['offset']
            print('task: %s, offset: %s - %s'% (hash_d.hex(), offset, offset + 10000))

            answer = None
            for line in lines[offset:offset + 10000]:
                if md5(line).digest() == hash_d:
                    answer = str(line, encoding='utf-8')
                    print('PASSWORD:', line)
                    
                    data = {'hash': hash_d.hex(), 'password': answer }
                    self.request("POST", "/pass", json.dumps(data), self.headers)
                    response = self.getresponse()
                    print(response.status, response.reason)
                    break
        
        else:
            sleep(2.0)


bot = SimpleHTTPClient()
bot.auth()

while True:
    bot.run()
    


