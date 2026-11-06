import socket
from threading import Thread, Lock
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

clients ={}
clients_lock = Lock()

HOST = ''
PORT = 12345

s=socket.socket()
s.bind((HOST,PORT))
s.listen()

print(f'listening on {HOST} : {PORT}')

def broadcast(message, exclude=None):
    with clients_lock:
        connected_clients = list(clients.keys())

    for client in connected_clients:
        if client == exclude:
            continue

        try:
            client.sendall(message.encode('utf-8'))
        except OSError:
            pass

def sendMessageToClient(sender,receiver, message):
    with clients_lock:
        recipient_conn = next(
            (
                conn for conn, username in clients.items()
                if username.casefold() == receiver.casefold()
            ),
            None
        )
        sender_username = clients.get(sender)

    if recipient_conn is None:
        response = f'User {receiver} not found.\n'
        target = sender

    else:
        response = f'[Private from {sender_username}]: {message}\n'
        target = recipient_conn

    try:
        target.sendall(response.encode('utf-8'))
    except OSError:
        pass




def handleConnection(conn, addr):
    username = None
    try:
        with conn.makefile('r', encoding='utf-8') as reader:
            username = reader.readline().strip()
            
            if not username:
                print(f'No username received from {addr}')
                return

            with clients_lock:
                clients[conn] = username

            print(f'User {username} connected from {addr}')
            broadcast(f'--{username} has joined the chat--\n')

            while True:
                data = reader.readline()

                if not data:
                    break

                message = data.rstrip('\r\n')
                if message.lower() == 'leave':
                    break
                    
                print(f'[{username}]: {message}')

                if message.startswith('@'):
                    command, separator, body = message.partition(' ')

                    recipient = command[1:]

                    if recipient.lower() == 'all':
                        broadcast(f'[{username}]: {message}\n', exclude = conn)
                    else:
                        sendMessageToClient(conn,recipient, message)

    except (ConnectionError, OSError) as e:
        print(f'Connection error: {e}')
    finally:
        with clients_lock:
            clients.pop(conn, None)
        if username:
            broadcast(f'*{username} has left the chat\n')
        conn.close()
        print(f'Connection closed with {addr}')


def acceptConnection(s):
    while True:
           conn, addr = s.accept()
           print(f'connected with {str(addr)}')
           t=Thread(target=handleConnection,args = (conn,addr,))
           t.start()

session = PromptSession()

startConnectionThread = Thread(target=acceptConnection,args = (s,), daemon=True)

startConnectionThread.start()

with patch_stdout():  
    while True:
        command = session.prompt('(type "exit" to stop the server): ')
        
        if command.lower() == 'exit':
            print('Stopping the server...')
            break

s.close()

