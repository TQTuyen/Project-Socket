import socket
import base64
import email
from email import policy
from email.parser import BytesFeedParser
import time
import mimetypes
from email.header import decode_header
import os
import re
import json
import pop3

config = open('./config.json', 'rt')

config = json.load(config)

host = config['General']['MailServer']
port = config['General']['POP3']
username = config['General']['Username']
password = config['General']['Password']
FOLDER_NAME = config['FilterEmail']['Folder']
FILTER_EMAIL = config['FilterEmail']['KeyWord']
SUBJECT = {}
AUTO_LOAD = config['General']['AutoLoad']



def parser_email(message):
    msg_parser = email.message_from_bytes(message)
    if msg_parser['Subject']:
        subject = decode_header(msg_parser['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject[0].decode(subject[1])
        else: 
            subject = subject[0]
    if msg_parser['From']:
        address_sender = decode_header(msg_parser['From'])[0]
        if isinstance(address_sender, bytes):
            address_sender = address_sender[0].decode(address_sender[1])
        else:
            address_sender = address_sender[0]
    else:
        address_sender = ''
    
    folder_name = f'{subject}/'
    if not SUBJECT.get(subject):
        SUBJECT[subject] = 0
    else:
        SUBJECT[subject] += 1
    if address_sender:
        search = re.search(r'<(.*)>', address_sender)
        address_sender = search.group()[1:-1]
        
    return subject, address_sender, folder_name, msg_parser


def download_content(body, address_sender, subject, folder_name):
    file_name = f'{address_sender}-{SUBJECT[subject]}.txt'
    filter_email = {}
    if address_sender in FILTER_EMAIL['AddressSender']:
        path = FOLDER_NAME['Project'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wt') as file:
            file.write(body.decode())
        filter_email['Project'] = True
    if [msg for msg in FILTER_EMAIL['Subject'] if msg in subject]:
        path = FOLDER_NAME['Important'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wt') as file:
            file.write(body.decode())
        filter_email['Important'] = True
    if [msg for msg in FILTER_EMAIL['Body'] if bytes(msg, 'utf8') in body]:
        path = FOLDER_NAME['Work'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wt') as file:
            file.write(body.decode())
        filter_email['Work'] = True
    if [msg for msg in FILTER_EMAIL['Key'] if bytes(msg, 'utf8') in body or msg in subject]:
        path = FOLDER_NAME['Spam'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wt') as file:
            file.write(body.decode())
        filter_email['Spam'] = True
    if not filter_email:
        path = FOLDER_NAME['Inbox'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wt') as file:
            file.write(body.decode())
    return filter_email

def download_file(body, address_sender, subject, folder_name, file_name, filter):
    if filter.get('Project'):
        path = FOLDER_NAME['Project'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wb') as file:
            file.write(body)
    if filter.get('Important'):
        path = FOLDER_NAME['Important'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wb') as file:
            file.write(body)
    if filter.get('Work'):
        path = FOLDER_NAME['Work'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wb') as file:
            file.write(body)
    if filter.get('Spam'):
        path = FOLDER_NAME['Spam'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wb') as file:
            file.write(body)
    if not filter:
        path = FOLDER_NAME['Inbox'] + folder_name
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + file_name, 'wb') as file:
            file.write(body)


def download_email(msg, address_sender, subject, folder_name):
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        body = part.get_payload(decode=True)
        if part.get('Content-Disposition') is None and part.get_content_type() == 'text/plain':            
            filter = download_content(body, address_sender, subject, folder_name)
        else:
            download_file(body, address_sender, subject, folder_name, part.get_filename(), filter)
        



if __name__ == '__main__':
    for folder in FOLDER_NAME.values():
        print(folder)
        if not os.path.exists(folder):
            os.mkdir(folder)
    try:
        while True:
            pop3_email = pop3.POP3(port = port)
            print(pop3_email.get_welcome().decode())
            optional_capa = pop3_email.capa()
            print(pop3_email.user(username).decode())
            print(pop3_email.password(password).decode())
            number_messages, size_email = pop3_email.stat()
            print(number_messages, size_email)
            content_messages = []  
            for i in range(1, number_messages + 1):
                response, content_message, _ = pop3_email.retr(i)
                print(response.decode())
                content_message = pop3.CRLF.join(content_message)
                content_messages.append(content_message)
                pop3_email.dele(i)
            for message in content_messages:
                subject, address_sender, folder_name, msg_parser = parser_email(message)
                download_email(msg_parser, address_sender, subject, folder_name)
            pop3_email.quit()
            time.sleep(AUTO_LOAD)
    except KeyboardInterrupt as err:
        raise err
    finally:
        pop3_email.quit()
    








    

    
    


