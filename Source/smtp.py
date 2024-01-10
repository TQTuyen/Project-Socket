import json
from socket import *
from base64 import *
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import make_msgid
from email.mime.application import MIMEApplication
from email import encoders
from email.utils import COMMASPACE, formatdate
import sys

def Create_Socket(mail_server_ip,smtp_port):
    clientSocket=socket(AF_INET,SOCK_STREAM)
    try:
        clientSocket.connect((mail_server_ip,smtp_port))
        return clientSocket
    except Exception as e:
        sys.exit("Không thể kết nối tới server, vui lòng kiểm tra lại")

def Greeting_Server(userEmail,clientSocket,mail_server_ip,Rcpt_arr):
    recv=clientSocket.recv(1024).decode()
    if(recv[:3]!='220'):
        print("220 reply not received from server")
    helloCommand='EHLO [{}]\r\n'.format(mail_server_ip)
    clientSocket.send(helloCommand.encode())
    recv0=clientSocket.recv(1024).decode()
    if(recv0[:3]!='250'):
        print("250 reply not received from server")
    mailFrom="MAIL FROM:<{}>\r\n".format(userEmail)
    clientSocket.send(mailFrom.encode())
    recv1=clientSocket.recv(1024).decode()
    for i in range(len(Rcpt_arr)):
        if(len(Rcpt_arr[i])==0):
            continue
        rcpto="RCPT TO:<{}>\r\n".format(Rcpt_arr[i])
        clientSocket.send(rcpto.encode())
        receive=clientSocket.recv(1024)
    clientSocket.send('DATA\r\n'.encode())
    recv2=clientSocket.recv(1024)

def Sending_msg(clientSocket,msg):
    clientSocket.sendall(msg.as_bytes())
    clientSocket.send('.\r\n'.encode())
    receive=clientSocket.recv(1024)

def Stopping_socketConnection(clientSocket):
    clientSocket.send('QUIT\r\n'.encode())
    receive=clientSocket.recv(1024)
    clientSocket.close()

def set_fileType(type_file,path):
    part=MIMEBase('application','octet-stream')
    part.set_param('name',os.path.basename(path))
    return part

def get_filesize(file_path):
    try:
        return os.path.getsize(file_path)/(1024*1024)
    except FileNotFoundError:
        print("Find not found\r\n")
        return -1
    except OSError:
        print("OS error occured\r\n")
        return -1

def Read_ConfigFile():
    file=open('config.json','r')
    config=json.load(file)
    name_email = config['General']['Username']
    parts=name_email.split('<') # split string become 2 part, one before and one afer char('<'). both of them don't cotain that char
    user_name=parts[0].strip() #remove white space before and after string
    userEmail=parts[1].replace('>','') 
    userPassword = config['General']['Password']
    mail_server_ip = config['General']['MailServer']
    smtp_port = config['General']['SMTP']
    pop3_port = config['General']['POP3']
    autoload_time = config['General']['AutoLoad']
    return name_email, user_name, userEmail, userPassword, mail_server_ip, smtp_port, pop3_port, autoload_time

def Get_RcptArr(Destinationemail,cc_Destination,bcc_Destination):
    rcpt_arr=[]
    to=Destinationemail.split(',')
    cc=cc_Destination.split(',')
    bcc=bcc_Destination.split(',')
    for i in range(len(to)):
        rcpt_arr.append(to[i])
    for i in range(len(cc)):
        rcpt_arr.append(cc[i])
    for i in range(len(bcc)):
        rcpt_arr.append(bcc[i])
    for i in range(len(rcpt_arr)):
        rcpt_arr[i]=rcpt_arr[i].strip()
    return rcpt_arr

def Get_Input_FromUser():
    DestinationEmail=input("To: ")
    cc_Destination=input("CC: ")
    bcc_Destination=input("BCC: ")
    Rcpt_arr=Get_RcptArr(DestinationEmail,cc_Destination,bcc_Destination)
    Subject=input("Nhập Subject: ")
    userMessage=input("Nhập vào nội dung muốn gửi: ")
    flag_attachment=int(input("Có muốn gửi file đính kèm không (1.Có, 2.Không): "))
    total_file=0
    path_arr=[]
    if(flag_attachment==1):
        total_file=int(input("Số lượng file muốn gửi: "))
        for i in range(total_file):
            string=input("Nhập địa chỉ file: ")
            while(os.path.exists(string)==False):
                string=input("Đường dẫn không tồn tại, vui lòng nhập lại đường dẫn mới\n")
            while(get_filesize(string)>3):
                string=input("File của bạn vừa nhập có kích thước vượt quá 3MB, vui lòng nhập lại đường dẫn khác\n")
            path_arr.append(string)
    return DestinationEmail, cc_Destination, bcc_Destination, Subject, userMessage, path_arr, Rcpt_arr

def Create_msg(userEmail,name_email,DestinationEmail, cc_Destination, bcc_Destination, Subject,userMessage,path_arr):
    msg=MIMEMultipart()
    msg['Message-ID']=make_msgid(domain=userEmail[userEmail.rfind('@')+1:])
    msg['Date'] = formatdate(localtime=True)
    msg['User-Agent']="Fast-Mailer"
    msg['Content-Language']="en-US"
    if len(DestinationEmail)==0 and len(cc_Destination)==0:
        msg['To']="undisclosed-recipients: ;"
    else:
        msg['To']=DestinationEmail
    if(len(cc_Destination)!=0):
        msg['Cc']=cc_Destination
    msg['From']=name_email
    msg['Subject']=Subject
    msg.attach(MIMEText(userMessage, _charset='utf-8'))
    if(len(path_arr)):
        for i in range(len(path_arr)):
            path=path_arr[i]
            type_file=path[path.rfind('.')+1:]  
            attachment=open(path,"rb")
            part=set_fileType(type_file,path)
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment",filename=os.path.basename(path))
            msg.attach(part)
    return msg

def main():
    name_email=""
    user_name=""
    userEmail=""
    userPassword=""
    mail_server_ip=""
    smtp_port=0
    pop3_port=0
    autoload_time=0
    DestinationEmail=""
    cc_Destination=""
    bcc_Destination=""
    Subject=""
    userMessage=""
    path_arr=[] 
    Rcpt_Arr=[]

    name_email, user_name, userEmail, userPassword,mail_server_ip,smtp_port,pop3_port,autoload_time=Read_ConfigFile()
    DestinationEmail,cc_Destination,bcc_Destination,Subject,userMessage,path_arr,Rcpt_Arr=Get_Input_FromUser()
    msg=Create_msg(userEmail,name_email,DestinationEmail,cc_Destination,bcc_Destination,Subject,userMessage,path_arr)  
    clientSocket=Create_Socket(mail_server_ip,smtp_port)
    Greeting_Server(userEmail,clientSocket,mail_server_ip,Rcpt_Arr)
    Sending_msg(clientSocket,msg)
    Stopping_socketConnection(clientSocket)




