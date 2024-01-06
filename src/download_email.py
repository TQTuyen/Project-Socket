import socket
import email
import time
from email.header import decode_header
import os
import re
import json
import pop3
import threading



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
    else:
        part_message['Subject'] = ''
    
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
        

def filter_email(body, address_sender, subject_message, file_name, config):
    check = False
    if address_sender in config['KeyWordFilter']['AddressSender']:
        path = config['FolderFilter']['Project']
        write_file(body, file_name, path)
        check = True
    if [msg for msg in config['KeyWordFilter']['Subject'] if msg in subject_message]:
        path = config['FolderFilter']['Important']
        write_file(body, file_name, path)
        check = True
    if [msg for msg in config['KeyWordFilter']['Body'] if bytes(msg, 'utf8') in body]:
        path = config['FolderFilter']['Work']
        write_file(body, file_name, path)
        check = True
    if [msg for msg in config['KeyWordFilter']['Key'] if bytes(msg, 'utf8') in body or msg in subject_message]:
        path = config['FolderFilter']['Spam']
        write_file(body, file_name, path)
        check = True
    if not check:
        path = config['FolderFilter']['Inbox']
        write_file(body, file_name, path)





def download_email():
    while True:
        uidl_messages = {}
        seen_messages = read_list_seen_message()
        config = read_file_config()
        pop3_email = None
        check = False
        
        try:
            pop3_email = pop3.POP3(host = config['Host'], port = config['Port'])
            pop3_email.user(config['Username'])
            pop3_email.password(config['Password'])
            number_messages, size_email = pop3_email.stat()
            response, uidl, _ = pop3_email.uidl()
            for uidl_message in uidl:
                check = True
                line = uidl_message.split()
                uidl_messages[int(line[0].decode())] = line[1].decode()
                seen_messages[line[1].decode()] = False
                
            for i in range(1, number_messages + 1):
                response, content_message, _ = pop3_email.retr(i)
                data = pop3.CRLF.join(content_message)
                message = parser_email(data)
                filter_email(data, message['From'], message['Subject'], uidl_messages[i], config)
                pop3_email.dele(i)
                
        except KeyboardInterrupt as err:
            print(err)
        finally:
            if pop3_email:
                pop3_email.quit()
        if check:
            with open('./seen.json', 'wt') as file:
                json.dump(seen_messages, file)
        time.sleep(config['AutoLoad'])
        


def read_file_config():
    config_content = open('./config.json', 'rt')
    config_content = json.load(config_content)
    config = {}
    
    config['Host'] = config_content['General']['MailServer']
    config['Port'] = config_content['General']['POP3']
    username = config_content['General']['Username']
    config['Username'] = re.search(pattern="<(.+)>", string=username).group(1)
    config['Password'] = config_content['General']['Password']
    config['FolderFilter'] = config_content['FilterEmail']['Folder']
    config['KeyWordFilter'] = config_content['FilterEmail']['KeyWord']
    config['AutoLoad'] = config_content['General']['AutoLoad']
    return config

            

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
        message['UID'] = file
        messages.append(message)
    return messages


def read_list_seen_message():
    seen = open('./seen.json', 'rt')
    seen = json.load(seen)
    return seen


def read_email():
    seen_messages = read_list_seen_message()
    config = read_file_config()
    for folder in config['FolderFilter'].values():
        if not os.path.exists(folder):
            os.mkdir(folder)
    path_folder = {}
    i = 1
    for folder in config['FolderFilter'].values():
        path_folder[i] = folder
        i += 1
    
    i = 1
    for folder in config['FolderFilter']:
        print(f'{i}. {folder}')
        i += 1
    path = input('Nhap thu muc muon doc email(nhan enter de bo qua): ')
    if not path or int(path) > i or int(path) < 1:
        return
    
    path = path_folder[int(path)]   
        
    messages = read_emails(path)
    
    i = 1
    for message in messages:
        sender = message['From']
        subject = message['Subject']
        uid = message['UID']
        seen =  "Seen" if seen_messages[uid] == True else "Unseen" 
        print(f'{i}.({seen}) <{sender}>, <{subject}>')
        i += 1
    

    i = input('Ban muon doc tin nhan thu may(nhan enter de thoat ra ngoai): ')
    if not i:
        return
    elif int(i) > len(messages) or int(i) < 1:
        print('Invalid values')
    else:
        message = messages[int(i) - 1]
        if seen_messages[message['UID']] == False:
            seen_messages[message['UID']] = True
            with open('./seen.json', 'wt') as file:
                json.dump(seen_messages, file)
                
        print(f'Noi dung email thu {i}:\n')
        print(message['Content'].decode(),'\n')
        check = False
        if message['Attached-Files']:
            select = input('Co file dinh kem, ban co muon tai khong(y, yes, co)? ')
            if select in ['y', 'yes', 'co']:
                check = True
                path = input('Nhap duong dan muon tai ve: ')
                if not path:
                    return
                if path[-1:] != '/':
                    path += '/'
        if check:
            for file in message['Attached-Files']:
                write_file(file[1], file[0], path)




if __name__ == '__main__':
    down_mail = threading.Thread(target = download_email)
    down_mail.start()
    down_mail.join()
    
    
    








    

    
    


