import socket
import email
import time
from email.header import decode_header
import os
import re
import json
import pop3
import threading

config = open('./config.json', 'rt')

config = json.load(config)

host = config['General']['MailServer']
port = config['General']['POP3']
username = config['General']['Username']
password = config['General']['Password']
FOLDER_NAME = config['FilterEmail']['Folder']
FILTER_EMAIL = config['FilterEmail']['KeyWord']
AUTO_LOAD = config['General']['AutoLoad']
uidl_messages = {}


def parser_email(message):
    message = email.message_from_bytes(message)
    part_message = {}
    if message['Subject']:
        subject_message = decode_header(message['Subject'])[0]
        if isinstance(subject_message, bytes):
            subject_message = subject_message[0].decode(subject_message[1])
        else: 
            subject_message = subject_message[0]
        part_message['Subject'] = subject_message
    if message['From']:
        address_sender = decode_header(message['From'])[0]
        if isinstance(address_sender, bytes):
            address_sender = address_sender[0].decode(address_sender[1])
        else:
            address_sender = address_sender[0]
    else:
        address_sender = ''
    
    if address_sender:
        search = re.search(r'<(.+)>', address_sender)
        address_sender = search.group()[1:-1]
    part_message['From'] = address_sender
        
    files = []
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        body_part = part.get_payload(decode=True)
        if part.get('Content-Disposition') is None and part.get_content_type() == 'text/plain':            
            part_message['Content'] = body_part
        else:
            file = (part.get_filename(), body_part)
            files.append(file)
    part_message['Attached-Files'] = files
    return part_message
    
    
def write_file(data, file_name, path='./'):
    if not os.path.exists(path):
        os.mkdir(path)
    with open(path + file_name, 'wb') as file:
        file.write(data)
        

def filter_email(body, address_sender, subject_message, file_name):
    check = False
    if address_sender in FILTER_EMAIL['AddressSender']:
        path = FOLDER_NAME['Project']
        write_file(body, file_name, path)
        check = True
    if [msg for msg in FILTER_EMAIL['Subject'] if msg in subject_message]:
        path = FOLDER_NAME['Important']
        write_file(body, file_name, path)
        check = True
    if [msg for msg in FILTER_EMAIL['Body'] if bytes(msg, 'utf8') in body]:
        path = FOLDER_NAME['Work']
        write_file(body, file_name, path)
        check = True
    if [msg for msg in FILTER_EMAIL['Key'] if bytes(msg, 'utf8') in body or msg in subject_message]:
        path = FOLDER_NAME['Spam']
        write_file(body, file_name, path)
        check = True
    if not check:
        path = FOLDER_NAME['Inbox']
        write_file(body, file_name, path)





        
    

def download_email():
    try:
        while True:
            pop3_email = pop3.POP3(host = host, port = port)
            pop3_email.user(username)
            pop3_email.password(password)
            number_messages, size_email = pop3_email.stat()
            response, uidl, _ = pop3_email.uidl()
            for uidl_message in uidl:
                line = uidl_message.split()
                uidl_messages[int(line[0].decode())] = line[1].decode()
                
            for i in range(1, number_messages + 1):
                response, content_message, _ = pop3_email.retr(i)
                data = pop3.CRLF.join(content_message)
                message = parser_email(data)
                filter_email(data, message['From'], message['Subject'], uidl_messages[i])
                pop3_email.dele(i)
            pop3_email.quit()
            time.sleep(AUTO_LOAD)
    except KeyboardInterrupt as err:
        print(err)
    except OSError as err:
        print(err)
    finally:
        pop3_email.quit()


def read_file(file_name, path='./'):
    with open(path + file_name, 'rb') as file:
        data = file.read()
    return data


def read_emails(folder):
    if not os.path.exists(folder):
        return []
    files = os.listdir(folder)
    messages = []
    for file in files:
        message = read_file(file, folder)
        message = parser_email(message)
        messages.append(message)
    return messages



def read_email():
    path_folder = {}
    i = 1
    for folder in FOLDER_NAME.values():
        path_folder[i] = folder
        i += 1
    while True:
        i = 1
        for folder in FOLDER_NAME:
            print(f'{i}. {folder}')
            i += 1
        path = input('Nhap thu muc muon doc email(nhan enter de bo qua): ')
        if not path or int(path) > i or int(path) < 1:
            continue
        
        path = path_folder[int(path)]   
            
        messages = read_emails(path)
        
        i = 1
        for message in messages:
            sender = message['From']
            subject = message['Subject']
            print(f'{i}. <{sender}>, <{subject}>')
            i += 1
        
        i = input('Ban muon doc tin nhan thu may(nhan enter de thoat ra ngoai): ')
        if not i:
            continue
        elif int(i) > len(messages) or int(i) < 1:
            print('Invalid values')
        else:
            message = messages[int(i) - 1]
            print(f'Noi dung email thu {i}:')
            print(message['Content'].decode())
            check = False
            if message['Attached-Files']:
                select = input('Co file dinh kem, ban co muon tai khong(y, yes, co)? ')
                if select in ['y', 'yes', 'co']:
                    check = True
                    path = input('Nhap duong dan muon tai ve: ')
                    if not path:
                        continue
                    if path[-1:] != '/':
                        path += '/'
            if check:
                for file in message['Attached-Files']:
                    write_file(file[1], file[0], path)

        



            


if __name__ == '__main__':
    for folder in FOLDER_NAME.values():
        print(folder)
        if not os.path.exists(folder):
            os.mkdir(folder)
    download_email()
    # down_mail = threading.Thread(target = download_email)
    # read_mail = threading.Thread(target = read_email)
    down_mail.start()
    # read_mail.start()
    down_mail.join()
    # read_mail.join()
    
    
    








    

    
    


