import socket
import json
import messages as m
import sys
import hashlib
import random
from ast import literal_eval
import Colors
from player import *
from parea import *
from keys import *
from decks import *

CARD_SIZE=100
PlayersList = []
DisqualifiedPList = []

class Caller:
    def __init__(self,nickname):
        self.seq_number = 0
        self.nickname = nickname
        self.keys = Key.gen_key_pair()
        self.privatekey, self.publickey = self.keys
        self.strkey = str(self.publickey)
        self.symkey = Deck.gen_key()
        self.deck = create_deck()
        self.sign = self.nickname + self.strkey + str(self.seq_number)
        self.hashed_sign = hashlib.sha256(self.sign.encode()).hexdigest()

def print_card(card):

    total = int(len(card))
    raiz = int(math.sqrt(total))

    rows = []
            
    for i in range(0, total, raiz):
        group = card[i:i+raiz]
        group = ["{:02d}".format(n) for n in group]
        rows.append(" | ".join(group))

    return "\n".join(rows)



def verify_card(card):
    verify = True
    for c in card:
        array_set = set(c)
        if len(array_set)!=len(c):
            verify = False
    return verify

    
def create_deck():
    deck = list(range(CARD_SIZE))
    random.shuffle(deck)
    return deck


def player_shuffle(deck):
    random.shuffle(deck)
    return deck


def checkWin(deck,card):
    # print(self.card)
    i=0
    cnt=0
    for i in range(len(deck)):
            for j in range(len(card)):
                if card[j]==deck[i]:
                    # print("Number found in your card")
                    cnt +=1
                    break
                else:
                    continue
            if cnt == len(card):
                break
    return i #number of tries to fill de card





def main():
    if len(sys.argv) == 1:
        port = 10
    elif len(sys.argv) == 2:
        port = int(sys.argv[1])
    else: 
        print('Erro')
        sys.exit(1)

    message = { 'header': 'something', 'body': 'Caller wants to join' }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect( ( '127.0.0.1', port) )
        
        nick = input('Escolha o nome de utilizador: ')
        caller = Caller(nick)
        print("\nBaralho criado pelo caller: \n")
        print(print_card(caller.deck))
        print('\n')
        
        #c =  [x.encode('utf-8') for x in caller.deck]
        #print(c)
        deck = [str(x).encode('UTF-8') for x in caller.deck]
        encdeck = [Deck.encrypt_deck(x, caller.symkey) for x in deck]

        message_info={'nickname':caller.nickname,
                      'public_key': caller.strkey,
                      'deck' : repr(encdeck),
                      'sign' : caller.hashed_sign,  
                      'sequence': caller.seq_number} 

        message_json = json.dumps(message_info).encode('UTF-8')
        
        m.send_msg(s,message_json)

        
        data = m.recv_msg(s)
        if(data == None):
            print(f'O utilizador {caller.nickname} não tem permissões para ser caller')
            exit(1)
        data = json.loads(data.decode('UTF-8'))
        print(data['msg'])


        while 'deck' not in data:
            data = m.recv_msg(s)
            data = json.loads(data.decode('UTF-8'))
            datadeck = data['deck']
            deck = literal_eval(datadeck)
        print("Baralho recebido")

        encdeck2 = [Deck.encrypt_deck(x, caller.symkey) for x in deck]
        

        print("Baralho devolvido")
        message_info={'nickname':caller.nickname ,
                        'public_key': caller.strkey,
                        'deck' : repr(encdeck2),
                        'sign' : caller.hashed_sign,  
                        'sequence': caller.seq_number} 
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(s,message_json)

        
        print("Pedido da chave simétrica recebido")
        data = m.recv_msg(s)
        data = json.loads(data.decode('UTF-8'))
        #send private key
        message_info={'priv_key':repr(caller.symkey)}
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(s,message_json)
        print("Chave simétrica enviada")

        
        while 'caller_key' not in data: 
            data = m.recv_msg(s)
            data = json.loads(data.decode('UTF-8'))
            
        datadeck = data['deck']
        deck = literal_eval(datadeck)
        caller_key2 = data['caller_key']
        deck_keys2 = data['deck_keys']

        deck_keys = []
        for x in deck_keys2:
            aux = literal_eval(x)
            deck_keys.append(aux)

        caller_key = literal_eval(caller_key2)

        max_clients = data['max_clients']


        # decrypt the deck from caller
        decrypted_caller = [Deck.decrypt_deck(x, caller_key) for x in deck]

        times_decrypted = 0
        for x in deck_keys:
            if times_decrypted != max_clients:
                if times_decrypted==0: 
                    decrypted_player = [Deck.decrypt_deck(x, deck_keys[max_clients-times_decrypted-1]) for x in decrypted_caller]
                else:
                    decrypted_player = [Deck.decrypt_deck(x, deck_keys[max_clients-times_decrypted-1]) for x in decrypted_player]
                times_decrypted +=1
        
        almostfinaldeck = [Deck.decrypt_deck(x, caller_key) for x in decrypted_player]
        finaldeck = [int(x) for x in almostfinaldeck]

        print("Baralho recebido:\n")
        print(print_card(finaldeck))


        # exhanging cards
        print("A verificar os cartões")
        data = m.recv_msg(s)
        data = json.loads(data.decode('UTF-8'))
        if verify_card(data['card_list']):
            message_info={'card_list':data['card_list'],'sign':caller.hashed_sign}
            message_json = json.dumps(message_info).encode('UTF-8')
            m.send_msg(s,message_json)
        print("Cartões verificados")
        

        print("Quem é o vencedor?")
        data = m.recv_msg(s)
        data = json.loads(data.decode('UTF-8'))
        players_cards = data['players_cards']
        i = 0
        tries = 101
        for card in players_cards:
            if checkWin(deck,card)<tries:
                winner= i
                tries= checkWin(deck,card)
            i +=1
        print("Vencedor confirmado")

        disqualified = [0] * max_clients
        for p in range(max_clients):
            data = m.recv_msg(s)
            data = json.loads(data.decode('UTF-8'))
            if data['winner'] != winner:
                disqualified[p] = 1

        message_info={'winner':winner,'disqualified':disqualified}
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(s,message_json)
       
        s.close()
        
if __name__ == '__main__':
    main()