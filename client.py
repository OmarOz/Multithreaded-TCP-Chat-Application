import socket
from threading import Thread

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

HOST = '127.0.0.1'
PORT = 12345

def receiveMessages(sock):
    try:
        with sock.makefile('r', encoding='utf-8') as reader:
            for message in reader:
                if f'[{username}]' not in message:
                    print(f'\n{message.rstrip()}')
    except (ConnectionError, OSError) as e:
        print(f'Connection error: {e}')


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST,PORT))
    print(f'Connect to server({HOST}, {PORT})\n')

    username = input('Enter your username: ')
    s.sendall((username + '\n').encode('utf-8'))

    session = PromptSession()

    with patch_stdout():
        receiver = Thread(
            target=receiveMessages,
            args=(s,),
            daemon=True
        )
        receiver.start()

        try:
            while True:
                message = session.prompt(f'[{username} (You)]: ')
                if message.lower()  == 'leave':
                    break

                s.sendall((message + '\n').encode('utf-8'))
        except (ConnectionError, OSError) as e:
            print(f'Connection error: {e}')       
        
        print(f'closing connection with server({HOST}, {PORT})')
