"""
This is HTTP Server for test website with css, js, gif, ico files and also GET request with parameters
To run the server:
    * run the file http_server.py
    * open browser and type: http://127.0.0.1:80/webroot/index.html or 127.0.0.1/home

Author: Noam Shushan
"""

import datetime
import os
import socket

# Constants:
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 0.1
CLOSE_SERVER_STATUS_CODE = 1
DEFAULT_URL = 'webroot/index.html'
REDIRECTION_DICTIONARY = {
    "webroot/home.html": "webroot/index.html",
    "home": "webroot/index.html",
    "home.html": "webroot/index.html",
    "webroot/home": "webroot/index.html"
}
STATUS_CODE = {
    200: "HTTP/1.1 200 OK\r\n",
    404: "HTTP/1.1 404 Not Found\r\n",
    302: "HTTP/1.1 302 Moved Temporarily\r\n",
    500: "HTTP/1.1 500 Internal Server Error\r\n"
}


def main():
    # Open a socket and loop forever while waiting for clients
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((IP, PORT))
        server_socket.listen()
        print(f"Listening for connections on port {PORT}...")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print('New connection received\n')
                client_socket.settimeout(SOCKET_TIMEOUT)

                if handle_client(client_socket) == CLOSE_SERVER_STATUS_CODE:
                    break  # Close server for debugging purposes
            except socket.timeout:
                print('Connection timed out\n')
                client_socket.close()
                continue
            except Exception as e:
                print(e)
                client_socket.close()
                break
    finally:
        print('Closing server')
        server_socket.close()


def handle_client(client_socket):
    """ Handles client requests: verifies client's requests are legal HTTP, calls function to handle the requests """
    print('Client connected\n')
    close_sever = False
    while True:
        # receive client request
        client_request = client_socket.recv(1024).decode()

        # check if request is valid HTTP request
        valid_http, resource = validate_http_request(client_request)
        if valid_http:
            print('Got a valid HTTP request\n')
            print(f'client request: {resource}\n')
            if handle_client_request(resource, client_socket) == CLOSE_SERVER_STATUS_CODE:
                close_sever = True
                break
        else:
            print(f'Error: Not a valid HTTP request\n{client_request}\n')
            break

    print('Closing client connection\n')
    client_socket.close()
    if close_sever:
        return CLOSE_SERVER_STATUS_CODE


def validate_http_request(request):
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and the requested URL
    """
    # check if request is a valid HTTP GET request
    first_line = request.split('\r\n')[0]
    if not first_line.startswith('GET'):
        return False, ''

    split_request = first_line.split()
    if len(split_request) != 3:
        return False, ''
    if 'HTTP' not in split_request[2]:
        return False, ''

    url = split_request[1]
    return True, url


def handle_client_request(resource, client_socket):
    """ Check the required resource, generate proper HTTP response and send to client"""
    #  add code that given a resource (URL and parameters) generates the proper response
    #  and sends it to the client

    url = DEFAULT_URL if resource == '' or resource == '/' else resource.strip('/')

    if url.endswith("exit"):  # Close server for debugging purposes
        return CLOSE_SERVER_STATUS_CODE

    if not url.startswith('webroot/'):
        url = 'webroot/' + url

    # handle Moved temporarily:
    if url in REDIRECTION_DICTIONARY:
        return moved_temporarily(client_socket, url)

    server_function = url.split("/")[-1]
    # handle area calculation
    if 'calculate-area' in server_function:
        return calculate_area(client_socket, server_function)

    #  if the resource is not found, send a 404 response
    if not os.path.isfile(url):
        return not_found(client_socket)

    # handle OK:
    return ok(client_socket, url=url)


def not_found(client_socket):
    """ Send 404 Not Found to client """
    massage = "404 Not Found\r\n"
    http_response = STATUS_CODE[404] + get_http_header(content_length=len(massage)) + massage
    client_socket.sendall(http_response.encode())
    return 404


def ok(client_socket, data=b'', url=''):
    """ Send 200 OK to client """
    if url != '' and data == b'':
        data = get_file_data(url)
    http_header = get_http_header(content_length=len(data), url=url)
    http_response = STATUS_CODE[200] + http_header
    client_socket.sendall(http_response.encode() + data)
    return 200


def moved_temporarily(client_socket, url):
    """ Send 302 Moved Temporarily to client """

    #  if the resource is not found, send a 404 response
    if not os.path.isfile(REDIRECTION_DICTIONARY[url]):
        return not_found(client_socket)

    data = get_file_data(REDIRECTION_DICTIONARY[url])
    location = f"Location: http://{REDIRECTION_DICTIONARY[url]}\r\n"
    http_header = get_http_header(content_length=len(data), url=REDIRECTION_DICTIONARY[url])
    http_response = STATUS_CODE[302] + location + http_header
    client_socket.sendall(http_response.encode() + data)
    return 302


def internal_server_error(client_socket, message):
    """ Send 500 Internal Server Error to client """
    http_response = STATUS_CODE[500] + get_http_header(content_length=len(message)) + message
    client_socket.sendall(http_response.encode())
    return 500


def calculate_area(client_socket, request):
    """ Calculate area and send to client """
    parameters = request.split('?')[-1].split('&')
    if not len(parameters) == 2:
        return internal_server_error(client_socket, f'Many or less parameters, expected 2, got {len(parameters)}')

    height = parameters[0].split('=')[-1]
    width = parameters[1].split('=')[-1]

    if not height.isnumeric() or not width.isnumeric():
        return internal_server_error(client_socket, 'Not numeric value for height or width')

    area = str((int(height) * int(width)) / 2)
    # check if area is float of int
    if area.endswith('.0'):
        area = area[:-2]
    return ok(client_socket, data=area.encode())


def get_file_data(filename):
    """ Get data from file """
    with open(filename, 'rb') as f:
        file_data = f.read()
        return file_data


def get_http_header(content_length, url=''):
    """ Generate HTTP header """
    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    http_header = f"Date: {date}\r\n" + \
                  f"Content-Length: {content_length}\r\n"
    accept_bytes = "Accept-Ranges: bytes\r\n\r\n"

    file_type = 'html' if url == '' else url.split('.')[-1]
    if file_type == 'html' or file_type == 'txt':
        http_header += "Content-Type: text/html\r\n\r\n"
    elif file_type == 'css':
        http_header += "Content-Type: text/css\r\n\r\n"
    elif file_type == 'js':
        http_header += "Content-Type: text/javascript\r\n\r\n"
    elif file_type == 'jpg':
        http_header += "Content-Type: image/jpeg\r\n" + accept_bytes
    elif file_type == 'png':
        http_header += "Content-Type: image/png\r\n" + accept_bytes
    elif file_type == 'ico':
        http_header += "Content-Type: image/icon\r\n" + accept_bytes
    elif file_type == 'gif':
        http_header += "Content-Type: image/gif\r\n" + accept_bytes

    return http_header


if __name__ == "__main__":
    # Call the main handler function
    main()
