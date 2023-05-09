# Description: Player class
import sys
import socket
import json
import messages as m
from ast import literal_eval
import random
import hashlib
import math
import Colors
from caller import *
from keys import *
from decks import *
import datetime

class Player:
    next_seq_number =0

    def __init__(self,nickname):
        self.seq_number = Player.next_seq_number + 1
        Player.next_seq_number += 1
        self.nickname = nickname
        self.card = get_card()
        self.keys = Key.gen_key_pair()
        self.privatekey, self.publickey = self.keys
        self.strkey = str(self.publickey)
        self.symkey = Deck.gen_key()
        self.sign = self.nickname + self.strkey + str(self.seq_number)
        self.hashed_sign = hashlib.sha256(self.sign.encode()).hexdigest()


def get_card():
    k = 25
    card = random.sample(range(100), k)
    random.shuffle(card)
    return card


def print_card(card):

    total = int(len(card))
    raiz = int(math.sqrt(total))

    rows = []
            
    for i in range(0, total, raiz):
        group = card[i:i+raiz]
        group = ["{:02d}".format(n) for n in group]
        rows.append(" | ".join(group))

    return "\n".join(rows)




def checkWin(deck,card):
    i=0
    cnt=0
    for i in range(len(deck)):
            for j in range(len(card)):
                if card[j]==deck[i]:
                    cnt +=1
                    break
                else:
                    continue
            if cnt == len(card):
                break
    return i 



def player_shuffle(card):
    random.shuffle(card)
    return card

def main():
    if len(sys.argv) == 1:
        port = 10
    elif len(sys.argv) == 2:
        port = int(sys.argv[1])
    else: 
        print('Erro')
        sys.exit(1)

    message = { 'header': 'something', 'body': 'Player wants to join' }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect( ( '127.0.0.1', port) )
        n = input('Escolha o nome de utilizador: \n')
        player = Player(n) 
        message_info={'nickname':player.nickname,
                        'public_key': player.strkey,
                        'card' : player.card,
                        'sign' : player.hashed_sign,  
                        'sequence': player.seq_number} 
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(s,message_json)

        # wait for message with the deck
        data = m.recv_msg(s)
        data = json.loads(data.decode('UTF-8'))
        print(data['msg'])


        while 'deck' not in data:
            data = m.recv_msg(s)
            data = json.loads(data.decode('UTF-8'))
            datadeck = data['deck']
            deck = literal_eval(datadeck)
        print("Baralho recebido")

        encdeck = [Deck.encrypt_deck(x, player.symkey) for x in deck]
        shudeck = player_shuffle(encdeck)
        
        # send the deck back
        print("Baralho devolvido")
        message_info={'nickname':player.nickname ,
                        'public_key': player.strkey,
                        'deck' : repr(shudeck),
                        'sign' : player.hashed_sign,  
                        'sequence': player.seq_number} 
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(s,message_json)

        print("Pedido da chave simétrica recebido")
        data = m.recv_msg(s)
        data = json.loads(data.decode('UTF-8'))
        
        # send the private key
        message_info={'priv_key':repr(player.symkey)}
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


        print("Verificação de cartões")
        message_info={'card':player.card}
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(s,message_json)

        data = m.recv_msg(s)
        data = json.loads(data.decode('UTF-8'))
        print("Cartões verificados")
        print(f"Cartão do utilizador {player.nickname}:\n")
        print(print_card(player.card))


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
        print("Quem é o vencedor?")
        message_info={'winner':winner}
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(s,message_json)
        data = m.recv_msg(s)
        data = json.loads(data.decode('UTF-8'))
        print(data['msg'])

        s.close()


if __name__ == '__main__':
    main()
