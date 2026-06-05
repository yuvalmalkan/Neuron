import socket, struct

TCP_DEBUG = True


def send_one_message(sock, data):
    """
    Send a message with a 4-byte prefix representing the size.
    Conforms exactly to the Neuron specs.
    """
    try:
        if type(data) != bytes:
            data = data.encode()

        # 'I' is an unsigned 32-bit integer (exactly 4 bytes)
        length = len(data)
        sock.sendall(struct.pack('!I', length) + data)

        data_part = data[:100]
        if TCP_DEBUG and len(data) > 0:
            print(f"\nSent({length})>>>{data_part}")
    except Exception as e:
        print(f"ERROR in send_one_message: {e}")


def recv_one_message(sock, return_type="string"):
    """
    Receive one message by first reading a 4-byte size header,
    and then reading the rest of the message.
    """
    # Read exactly 4 bytes for the header
    len_section = __recv_amount(sock, 4)
    if not len_section:
        return None

    # Unpack the 4 bytes back into an integer
    len_int, = struct.unpack('!I', len_section)

    # Read the rest of the chunks based on the extracted size
    data = __recv_amount(sock, len_int)
    if TCP_DEBUG and len(data) != 0:
        print(f"\nRecv({len_int})>>>{data[:100]}")

    if len_int != len(data):
        data = b''  # Partial data is like no data!

    if return_type == "string":
        return data.decode()
    return data


def __recv_amount(sock, size=4):
    """
    Helper function that collects TCP chunks until the expected size is met.
    """
    buffer = b''
    while size:
        new_buffer = sock.recv(size)
        if not new_buffer:
            return b''
        buffer += new_buffer
        size -= len(new_buffer)
    return buffer