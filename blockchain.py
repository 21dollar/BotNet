from random import getrandbits, randint
from Cryptodome.Hash import SHA256
from time import sleep
from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import pkcs1_15

def dump_trans(trans):
    return ' : '.join([
            trans['id'],
            trans['sign'][:8]
        ]) if trans else '[' + '_'*17 + ']'

def dump_block(block):
    return ' | '.join([
        block['previous'][:12],
        ' : '.join([
            block['trans']['id'],
            block['trans']['sign'][:8]
        ]) if block['trans'] else '[' + '_'*17 + ']',
        block['hash'][:12]
    ])

HASH_DIFFICULT = 2
CHAIN_DIFF = 3

THREAD_RESULTS = []
KILL_THREAD = False

def solve_block(block):
    data = bytes.fromhex(block['previous']) +\
        bytes(block['trans']['id'], encoding='utf8') +\
        bytes(block['trans']['key'], encoding='utf8') +\
        bytes.fromhex(block['trans']['sign'])

    sha = SHA256.new(data)

    number = getrandbits(256).to_bytes(32, 'big')
    sha.update(number)

    while not sha.digest().startswith(b'\x00'*HASH_DIFFICULT):
        number = getrandbits(256).to_bytes(32, 'big')
        sha.update(number)
        if KILL_THREAD: return

    block['hash'] = sha.hexdigest()

    THREAD_RESULTS.append(block)


class Blockchain():
    def __init__(self):
        genesis_block = {
            'previous': (b'\x00'*32).hex(),
            'trans': {}
        }

        genesis_block['hash'] = SHA256.new(b'\x00'*32).hexdigest()
        self.chain = [genesis_block]
        self.temp = []

    def has(self, trans):
        for block in self.chain[1:]:
            if block['trans'] == trans:
                return True
        return False

    def bad_has(self, trans):
        for block in self.temp[1:]:
            if block['trans']['id'] == trans['id']:
                return True
        return False

    def load_chain(self, data):
        self.chain = data['chain']
        self.temp = data['temp']

    def push(self, new_block):

        for block in self.chain:
            if block['previous'] == new_block['previous'] and block['trans'] == new_block['trans']:
                return
        for block in self.temp:
            if block['previous'] == new_block['previous'] and block['trans'] == new_block['trans']:
                return

        if self.chain[-1]['hash'] == new_block['previous']:
            self.chain.append(new_block)
            
        elif self.temp and self.temp[-1]['hash'] == new_block['previous']:
            self.temp.append(new_block)
        else:
            for i in range(len(self.chain) - 1):
                if self.chain[i]['hash'] == new_block['previous']:
                    self.temp = self.chain[:i + 1]
                    self.temp.append(new_block)
                    break

        if len(self.temp) - len(self.chain) > CHAIN_DIFF:
            self.chain, self.temp = self.temp, []
        elif len(self.chain) - len(self.temp) > CHAIN_DIFF:
            self.temp = []
    
    def gen_block(self, trans):
        return {
            'previous': self.chain[-1]['hash'],
            'trans': trans
        }

    def gen_bad_block(self, trans):
        return {
            'previous': self.temp[-1]['hash'],
            'trans' : trans
        }

    def get_last_block(self):
        return self.chain[-1]

    def get_key_by_id(self, uid):
        for block in self.chain:
            trans = block['trans'] 
            if trans and trans['id'] == uid:
                return trans['key']
        return None

    def verify(self, uid, sign, password):
        public = self.get_key_by_id(uid)
        if not public:
            return False
        key = RSA.import_key(public)
        h = SHA256.new(password)
        try:
            pkcs1_15.new(key).verify(h, bytes.fromhex(sign))
            return True
        except (ValueError, TypeError):
            return False

    def __str__(self):
        return 'Blockchain:\n' + '\n'.join(dump_block(block) for block in self.chain) +\
             '\nTemp:\n' + '\n'.join(dump_block(block) for block in self.temp)

