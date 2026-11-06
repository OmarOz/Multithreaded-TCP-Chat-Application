# Multithreaded TCP Chat Application

A command line chat application built with Python socket programming and multithreading. It allows multiple clients to connect to a central server, exchange public messages, and send private messages to specific users simultaneously.

The application uses TCP for reliable communication and `prompt_toolkit` to provide a better terminal experience when sending and receiving messages concurrently.

## Features

- **Multiple Clients:** Supports multiple clients connecting to the server simultaneously.
- **Public Messaging:** Broadcast messages to all connected clients using `@all`.
- **Private Messaging:** Send messages directly to a specific user using `@username`.
- **Case Insensitive Usernames:** Private message recipient lookup is case insensitive.
- **Join and Leave Notifications:** Notify connected users when someone joins or leaves the chat.
- **Concurrent Communication:** Send and receive messages simultaneously without blocking user input.
- **Thread Synchronization:** Protect shared client information using Python's `Lock`.
- **Terminal Interaction:** Use `prompt_toolkit` to manage terminal input and output while messages arrive.

## Technologies Used

- **Python 3**
- **Socket Programming:** TCP client server communication.
- **Threading:** Concurrent client handling and message receiving.
- **Thread Synchronization:** Protecting shared resources using locks.
- **Prompt Toolkit:** Handling terminal input and asynchronous output.

## Project Structure

```text
multithreaded-TCP-Chat-Application/
│
├── client.py       # Client application
├── server.py       # Server application
└── README.md       # Project documentation
```

## Installation and Setup

### Prerequisites

- Python 3 installed on your machine.
- `pip` package manager.

Check your Python version:

```bash
python --version
```

### 1. Clone the Repository

```bash
git clone https://github.com/OmarOz/Multithreaded-TCP-Chat-Application
cd /Multithreaded-TCP-Chat-Application
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Install Dependencies

Install `prompt_toolkit`:

```bash
pip install prompt_toolkit
```

### 3. Configure the Connection

The server listens on port `12345`:

```python
HOST = ''
PORT = 12345
```

The client connects using:

```python
HOST = '127.0.0.1'
PORT = 12345
```

The default configuration allows the client and server to run on the same machine.

To connect from other machines on the same network, change the client's `HOST` to the server's IP address and ensure the server port is accessible through the network firewall.

## Running the Application

### 1. Start the Server

Open a terminal and execute:

```bash
python server.py
```

The server starts listening for incoming TCP connections.

```text
listening on  : 12345
```

### 2. Start the Clients

Open separate terminal windows for each client and execute:

```bash
python client.py
```

Enter a username when prompted.

Multiple client instances can connect to the same server and communicate with each other.

## Usage

### Public Messaging

To send a message to all connected clients, use `@all` followed by your message:

```text
@all Hello everyone!
```

The server broadcasts the message to all connected clients except the sender.

### Private Messaging

To send a private message to a specific user, use `@username` followed by your message:

```text
@Ahmed Hello, how are you?
```

The server searches for the recipient's username and forwards the message directly to their socket connection.

Username matching is case insensitive, so `@ahmed`, `@Ahmed`, and `@AHMED` refer to the same username.

If the recipient does not exist or is not connected, the sender receives an error message.

### Leaving the Chat

To disconnect from the chat, enter:

```text
leave
```

The server removes the client's connection from its collection and notifies the remaining users.

### Stopping the Server

Enter the following command in the server terminal:

```text
exit
```

This stops the main server command loop and closes the listening socket.

## Multithreading Architecture

Multithreading is a fundamental part of this application. Socket operations such as `accept()`, `readline()`, and terminal input can block while waiting for external events.

Using separate threads allows the application to handle multiple clients and perform sending, receiving, and server interaction concurrently.

### 1. Server Side Multithreading

The server uses a dedicated thread for accepting new connections and creates a separate handler thread for every connected client.

#### A. Connection Accepting Thread

```python
startConnectionThread = Thread(
    target=acceptConnection,
    args=(s,),
    daemon=True
)

startConnectionThread.start()
```

The `acceptConnection()` function continuously waits for new clients:

```python
def acceptConnection(s):
    while True:
        conn, addr = s.accept()

        t = Thread(
            target=handleConnection,
            args=(conn, addr)
        )

        t.start()
```

**Why use a separate thread?**

The `accept()` operation is blocking. It waits until a client establishes a connection.

If the main server thread handled this operation, it would be unable to process terminal commands while waiting for new connections.

Moving connection acceptance to a separate thread allows the main thread to remain available for server commands.

#### B. Dedicated Thread for Each Client

Whenever a client connects, the server creates a new thread:

```python
Thread(
    target=handleConnection,
    args=(conn, addr)
).start()
```

Each handler thread is responsible for:

- Reading incoming messages from its client.
- Processing public and private messaging commands.
- Forwarding messages to the appropriate recipients.
- Handling client disconnections.
- Removing disconnected clients from the shared collection.

**Why use a separate thread for each client?**

Reading messages from a client is a blocking operation.

Without separate handler threads, the server could become stuck waiting for one client to send a message, preventing it from processing messages from other clients.

With a dedicated handler thread per client, one thread can wait for incoming data while other threads continue processing their respective clients.

### 2. Client Side Multithreading

The client uses two concurrent activities: sending and receiving messages.

#### A. Main Thread – Sending Messages

The main thread handles user input through `PromptSession`:

```python
while True:
    message = session.prompt(f'[{username} (You)]: ')

    if message.lower() == 'leave':
        break

    s.sendall((message + '\n').encode('utf-8'))
```

It waits for the user to enter a message and sends it to the server.

#### B. Receiver Thread – Receiving Messages

A separate thread continuously listens for incoming messages:

```python
receiver = Thread(
    target=receiveMessages,
    args=(s,),
    daemon=True
)

receiver.start()
```

The receiver function reads messages from the server:

```python
def receiveMessages(sock):
    with sock.makefile('r', encoding='utf-8') as reader:
        for message in reader:
            if f'[{username}]' not in message:
                print(f'\n{message.rstrip()}')
```

**Why use a separate receiver thread?**

Reading incoming messages is a blocking operation.

If sending and receiving were handled sequentially in the same thread, the client could get stuck waiting for incoming data and become unable to accept new user input.

The receiver thread allows the client to:

- Wait for user input in the main thread.
- Receive messages from the server concurrently.
- Display incoming messages while the user is typing.

### 3. Thread Synchronization and Shared Resources

The server maintains a shared dictionary containing connected clients:

```python
clients = {}
clients_lock = Lock()
```

The dictionary maps each client's socket connection to its username:

```python
{
    client_socket_1: "Omar",
    client_socket_2: "Ahmed",
    client_socket_3: "Mohamed"
}
```

Since multiple client handler threads may access or modify this dictionary concurrently, a `Lock` protects shared access.

For example, registering a new client:

```python
with clients_lock:
    clients[conn] = username
```

Removing a disconnected client:

```python
with clients_lock:
    clients.pop(conn, None)
```

Searching for a recipient:

```python
with clients_lock:
    recipient_conn = next(
        (
            conn for conn, username in clients.items()
            if username.casefold() == receiver.casefold()
        ),
        None
    )
```

The lock ensures that protected dictionary operations do not execute concurrently.

#### Keeping Critical Sections Short

An important design consideration is avoiding network operations while holding the shared lock.

For example, the `broadcast()` function first retrieves a snapshot of the connected sockets:

```python
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
```

The lock is released before calling `sendall()`.

This is important because sending data over a socket is a potentially blocking operation. Holding the lock during a network operation could prevent other threads from accessing or modifying the shared client dictionary while that operation is waiting.

By keeping the critical section short, the server reduces lock contention and allows client handlers to proceed more independently.

## Communication Protocol

The application uses TCP (Transmission Control Protocol) to exchange data between clients and the server.

TCP provides a reliable, ordered byte stream, but it does not preserve application level message boundaries.

To distinguish individual messages, the application uses a newline delimited protocol.

Each message is encoded as UTF-8 and terminated with `\n`:

```python
s.sendall((message + '\n').encode('utf-8'))
```

On the receiving side, the application uses a file like socket reader:

```python
reader = sock.makefile('r', encoding='utf-8')

for message in reader:
    print(message)
```

The reader extracts messages line by line, allowing the application to process complete messages instead of arbitrary chunks of received bytes.

## Application Workflow

1. The server creates a TCP socket, binds it to a port, and starts listening.
2. A dedicated connection accepting thread waits for incoming clients.
3. When a client connects, the server creates a handler thread for that client.
4. The client sends its username to the server.
5. The server registers the client's socket and username in the shared dictionary.
6. The client starts a receiver thread to listen for incoming messages.
7. The client main thread accepts user input and sends messages to the server.
8. The server processes each message and either broadcasts it or forwards it to a specific recipient.
9. When a client leaves, the server removes its connection and broadcasts a disconnection notification.

## Learning Objectives

This project demonstrates practical concepts in:

- TCP client server architecture.
- Python socket programming.
- Blocking and non blocking application behavior.
- Multithreading and concurrent execution.
- Shared resources and thread synchronization.
- Lock contention and critical sections.
- Message framing over TCP.
- Basic network application design.
