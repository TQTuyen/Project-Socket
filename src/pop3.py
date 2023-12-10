import socket
import re

CR = b'\r'
LF = b'\n'
CRLF = CR + LF
MAX_LINE = 2048

class POP3:
    
    def __init__(self, host='127.0.0.1', port=110, time_out=socket._GLOBAL_DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.encoding = 'utf8'
        self.socket = self.create_socket(time_out)
        self.file = self.socket.makefile('rb')
        self.welcome = self.get_response()
    
    
    def create_socket(self, time_out):
        if time_out is not None and not time_out:
            raise ValueError('time out is 0 not support')
        return socket.create_connection((self.host, self.port), time_out)
    
    
    def put_line(self, line):
        self.socket.sendall(line + CRLF)
       
        
    def put_command(self, line):
        line = bytes(line, self.encoding)
        self.put_line(line)
        
        
    def get_line(self):
        line = self.file.readline(MAX_LINE + 1)
        octets = len(line)
        if octets > MAX_LINE: 
            raise Exception('line too long')
        if not line:
            raise Exception('no message')
        if line[-2:] == CRLF:
            return line[:-2], octets
        if line[:1] == CR:
            return line[1:-1], octets
        return line[:-1], octets
    
    
    def get_response(self):
        response, octets = self.get_line()
        if not response.startswith(b'+'):
            raise Exception(response)
        return response
    
    
    def get_long_response(self):
        response = self.get_response()
        list = []
        line, o = self.get_line()
        octets = 0
        while line != b'.':
            octets += o
            list.append(line)
            line, o = self.get_line()
        return response, list, octets
    
    
    def short_command(self, line):
        self.put_command(line)
        return self.get_response()


    def long_command(self, line):
        self.put_command(line)
        return self.get_long_response()
    
    
    def get_welcome(self):
        return self.welcome
    
    
    def user(self, user):
        return self.short_command(f'USER {user}')
    
    
    def password(self, password):
        return self.short_command(f'PASS {password}')
    
    
    def stat(self):
        response = self.short_command('STAT')
        response = response.split()
        number_message, size_message = int(response[1]), int(response[2])
        return number_message, size_message
    
    
    def list(self, msg_num=None):
        if msg_num is not None:
            return self.short_command(f'LIST {msg_num}')
        return self.long_command('LIST')
    
    
    def retr(self, msg_num):
        return self.long_command(f'RETR {msg_num}')
        
    
    
    def dele(self, msg_num):
        return self.short_command(f'DELE {msg_num}')
    
    
    def noop(self):
        return self.short_command('NOOP')
    
    
    def rset(self):
        return self.short_command('RSET')
    
    
    def quit(self):
        response = self.short_command('QUIT')
        self.close()
        return response
    
    
    def close(self):
        try:
            file = self.file
            self.file = None
            if file is not None:
                file.close()
        finally:
            sock = self.socket
            self.socket = None
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError as exception:
                    raise exception
                finally:
                    sock.close() 
       
                    
    def top(self, msg_num, line_num):
        return self.long_command(f'TOP {msg_num} {line_num}')
    
    
    def uidl(self, msg_num=None):
        if msg_num is not None:
            return self.short_command(f'UIDL {msg_num}')
        return self.long_command('UIDL')
    
    
    def capa(self):
        def parse_capa(line):
            line = line.decode(self.encoding).split()
            return line[0], line[1:]
        
        caps = {}
        try:
            response = self.long_command('CAPA')
            raw_caps = response[1]
            for cap_line in raw_caps:
                cap_option, cap_args = parse_capa(cap_line)
                caps[cap_option] = cap_args
        except Exception:
            raise Exception('CAPA not supported by server')
        return caps
    
