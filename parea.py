#!/bin/python

import sys
import socket
import selectors
import json
import messages as m
import hashlib
import random
import time
import Colors
import random
import hmac
from player import *
from caller import *
from keys import *

counter =0
max_clients = 4
players= []


def valid_clients(nickname,public_key,signature,seq_number): 
    global counter
    message = nickname + str(public_key) + str(seq_number)
    hashed_message = hashlib.sha256(message.encode()).hexdigest()
    if hmac.compare_digest(signature,hashed_message):
        return True
    else:
        return False

# def __init__(self, caller=None, players=None):
#         self.caller = caller if caller != None else None
#         self.players = [] if players == None else players
        
# def add_caller(self, caller):
#     self.caller = caller

# def add_player(self, player):
#     self.players.append(player)

# def start_game(self):
#     Caller.expose_key(self.players)
#     Caller.validatecards(self.players)
#     Caller.showcards(self.players)
#     print('The game has started!!!\n')
#     deck = self.caller.deck
#     random.shuffle(deck)
#     for number in deck:
#         for player in self.players:
#             won = player.play(number)
#             if won:
#                 print(f'Player {player.nickname} won the game!')
#                 response = input("Wanna see the user list? (yes/no): ")
#                 if response.lower() in ['yes', 'yessir', 'ya', 'y']: print(names)
#                 response = input("Wanna see the actions log? (yes/no): ")
#                 if response.lower() in ['yes', 'yessir', 'ya', 'y']: print(entries) 
#                 print('\n')
#                 print("Game is over, press any bind to leave")
#                 input() 
#                 exit() 


def dispatch( srv_socket ):
    global counter
    selector = selectors.DefaultSelector()

    clientsockets = [None] * max_clients
    srv_socket.setblocking(False)
    selector.register( srv_socket, selectors.EVENT_READ, data=None )
    print('Começa a autenticação: \n')
    exists_caller = False

    while counter<max_clients:
       
        events = selector.select( timeout=None )
        for key, mask in events:

            if key.fileobj == srv_socket:
                clt_socket, clt_addr = srv_socket.accept()
                clt_socket.setblocking( True )
                data = m.recv_msg(clt_socket) 
                data = json.loads(data.decode('UTF-8'))
                nickname = data['nickname']
                public_key = data['public_key']
                seq_number = data['sequence']
                signature = data['sign']
                
                if not valid_clients(nickname,public_key,signature,seq_number):
                    print(f'O utilizador {nickname} não foi aceite')
                    clt_socket.close()
                    continue
                print(f'O utilizador {nickname} foi aceite')

                if not exists_caller:
                    caller_socket = clt_socket
                    Deck = data['deck']
                    print(f'{nickname} é o caller, podemos agora aceitar jogadores')
                    caller = Caller(nickname)
                    exists_caller = True

                    
                else: 
                    clientsockets[counter] = clt_socket
                    counter +=1
                    card = data['card']
                    print( f'O jogador {nickname} juntou-se {counter}/{max_clients}' )
                    players.append(Player(nickname))

                
                selector.register( clt_socket, selectors.EVENT_READ, data=None )
                message_info=({'msg':'Foste aceite'})
                message_json = json.dumps(message_info).encode('UTF-8')
                m.send_msg(clt_socket,message_json)
                

            else:
                data = m.recv_msg( key.fileobj )

                if data == None: 
                    selector.unregister( key.fileobj )
                    key.fileobj.close()
                    counter -=1
                    print('Alguém saiu, '+ str(counter) + '/' + str(max_clients))
                    continue


                data = json.loads( data.decode( 'UTF-8' ) )
                print( data )

                data['body']  = data['body'].upper()
                data = json.dumps( data )
                data = data.encode( 'UTF-8' )
                m.send_msg( key.fileobj, data )

    print('Jogo começou: \n')
    winner= ''
    print("A baralhar...")


    for client in clientsockets:
       
        message_info= {'deck' : Deck}
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(client,message_json)

  
        data = m.recv_msg(client)
        data = json.loads(data.decode('UTF-8'))
        nickname = data['nickname']
        public_key = data['public_key']
        newdeck = data['deck']
        seq_number = data['sequence']
        signature = data['sign']
        
 
        if not valid_clients(nickname,public_key,signature,seq_number):
            print(f'Player {nickname} não foi aceite!')
            clt_socket.close()
            continue
            
  
        Deck = newdeck

    print("A enviar o deck para o Caller...")
    message_info= {'deck' : Deck}
    message_json = json.dumps(message_info).encode('UTF-8')
    m.send_msg(caller_socket,message_json)
    data = m.recv_msg(caller_socket)
    data = json.loads(data.decode('UTF-8'))
    nickname = data['nickname']
    public_key = data['public_key']
    newdeck = data['deck']
    seq_number = data['sequence']
    signature = data['sign']
    Deck = newdeck


    print("A obter as chaves...")
    deck_keys = [None] * max_clients
    i = 0
    for client in clientsockets:
        message_info={'msg' : 'Return private key'}
        message_json = json.dumps(message_info).encode('UTF-8')
        m.send_msg(client,message_json)

        data = m.recv_msg(client) #retrieve the data from the client socket
        data = json.loads(data.decode('UTF-8'))
        priv_key = data['priv_key']
        deck_keys[i] = priv_key
        i += 1

    message_info={'msg' : 'Return private key'}
    message_json = json.dumps(message_info).encode('UTF-8')
    m.send_msg(caller_socket,message_json)
    data = m.recv_msg(caller_socket) #retrieve the data from the client socket
    data = json.loads(data.decode('UTF-8'))
    caller_key = data['priv_key'] 
    
    
    print("A devolver os decks Decks...")
    message_info = {'caller_key':caller_key, 'deck_keys':deck_keys,'deck':Deck,'max_clients':max_clients}
    message_json = json.dumps(message_info).encode('UTF-8')
    m.send_msg(caller_socket,message_json)
    for client in clientsockets:
        m.send_msg(client,message_json)


    print("A validar os Cartões...")
    card_list = []
    for client in clientsockets:
        data = m.recv_msg(client) 
        data = json.loads(data.decode('UTF-8'))
        card_list.append(data['card'])
    message_info = {'card_list':card_list}
    message_json = json.dumps(message_info).encode('UTF-8')
    m.send_msg(caller_socket,message_json)
    data = m.recv_msg(caller_socket) 
    data = json.loads(data.decode('UTF-8'))
    if valid_clients(caller.nickname,caller.publickey,data['sign'],caller.seq_number):
        i = 0
        for client in clientsockets:
            message_info = data
            message_json = json.dumps(message_info).encode('UTF-8')
            m.send_msg(client,message_json)
            data = m.recv_msg(client) 
            data = json.loads(data.decode('UTF-8'))
            if not valid_clients(players[i].nickname,players[i].publickey,data['sign'],players[i].seq_number):
                print("Autenticação Falhada...")
            i+=1

    print("Todos os Players estão autenticados, começem o bingo!")
    print("A calcular o resultado...")
    players_cards = [d.card for d in players]
    message_info = {'players_cards':players_cards}
    message_json = json.dumps(message_info).encode('UTF-8')
    m.send_msg(caller_socket,message_json)
    for client in clientsockets:
        m.send_msg(client,message_json)

    print("A receber o vencedor para validar com o Caller!")
    for client in clientsockets:
        data = m.recv_msg(client) 
        data = json.loads(data.decode('UTF-8'))
        message_json = json.dumps(data).encode('UTF-8')
        m.send_msg(caller_socket,message_json)
    
    data = m.recv_msg(caller_socket) 
    data = json.loads(data.decode('UTF-8'))
    disqualified = data['disqualified']
    winner = data['winner']
    i = 0
    for p in disqualified:
        if p != 0: 
            print("Player ",players[i].nickname, " Desclassificado!")
            break
        i+=1
    print("Vencedor é o/a: ",players[winner].nickname)
    i = 0
    for client in clientsockets:
        if i != winner:
            message_info = {'msg': "Perdeste, lamento."}
            message_json = json.dumps(message_info).encode('UTF-8')
            m.send_msg(client,message_json)
        else:
            message_info = {'msg': "Parabéns, ganhaste!!!"}
            message_json = json.dumps(message_info).encode('UTF-8')
            m.send_msg(client,message_json)
        i+=1

    caller_socket.close()
    for clt_socket in clientsockets:
        clt_socket.close()

def parea_signature():
    string = 'Playing area signature'
    hasher = hashlib.sha256()
    hasher.update(string.encode('utf-8'))
    signature = hasher.hexdigest()
    return signature


def log(array, text):
    
    if not array:
        sequence = 0
        timestamp = int(time.time())
        entry = {
        'sequence': sequence,
        'timestamp': timestamp,
        'prev_hash': 'First one',
        'text': text,
        'parea signature': parea_signature()
    }
       
    else:
        sequence = int(array[-1]['sequence']) + 1
        prev_entry = array[-1]['prev_hash']
        timestamp = int(time.time())
        prev_hash = hashlib.sha256(json.dumps(prev_entry).encode()).hexdigest() if prev_entry else None
        entry = {
            'sequence': sequence,
            'timestamp': timestamp,
            'prev_hash': prev_hash,
            'text': text,
            'parea signature': parea_signature()
        }
    array.append(entry)

#function to show all players and their actions     
# def show_players(players):
#     for player in players:
#          print(f'nickname: {player["nickname"]}, Action: {player["action"]}')




# def is_portuguese():
   
#     lib = '/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so'

#     pkcs11 = PyKCS11.PyKCS11Lib()

#     pkcs11.load(lib)
#     slots = pkcs11.getSlotList(tokenPresent= True)
#     slot = slots[0]
#     session = pkcs11.openSession(slot)

    
#     session.login(PyKCS11.CKU_USER, "0000")
#     objects = session.findObjects()
#     for obj in objects:
        
#         attrs = session.getAttributeValue(obj, [PyKCS11.CKA_CERTIFICATE_COUNTRY])
        
#         if attrs[0][0] == "PT":
#             return True

#     return False

# def get_public_key():
#     lib = '/usr/lib/x86_64-linux-gnu/pkcs11/opensc-pkcs11.so'

#     pkcs11 = PyKCS11.PyKCS11Lib()

#     pkcs11.load(lib)
#     slots = pkcs11.getSlotList(tokenPresent= True)
#     slot = slots[0]
#     session = pkcs11.openSession(slot)

    
#     session.login(PyKCS11.CKU_USER, "0000")
#     objects = session.findObjects()
#     for obj in objects:
            
#             attrs = session.getAttributeValue(obj, [PyKCS11.CKA_CERTIFICATE_COUNTRY])
            
#             if attrs[0][0] == "PT":
#                 attrs = session.getAttributeValue(obj, [PyKCS11.CKA_PUBLIC_KEY_INFO])
#                 return attrs[0]

# def set_caller(players):
#     players[0]['caller'] = True





def main():
    if len(sys.argv) == 1:
        port = 10
    elif len(sys.argv) == 2:
        port = int(sys.argv[1])
    else: 
        print('Wrong number of arguments')
        sys.exit(1)

    with socket.socket( socket.AF_INET, socket.SOCK_STREAM ) as s:
        s.bind( ('0.0.0.0', port) )
        s.listen()
        dispatch( s )

if __name__ == '__main__':
    main()
