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

def set_fileType(type_file,path):
    if(type_file=="txt"):
        part=MIMEBase('text','plain')
    if(type_file=="pdf"):
        part=MIMEBase('application','pdf')
    if(type_file=="docx"):
        part=MIMEBase('application','vnd.openxmlformats-officedocument.wordprocessingml.document')
    if(type_file=="jpg"):
        part=MIMEBase('image','jpeg')
    if(type_file=='zip'):
        part=MIMEBase('application','x-zip-compressed')
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



if __name__ == "__main__":
    # Configuration
    file=open('config.json','rt')
    config=json.load(file)
    name_email = config['General']['Username']
    parts=name_email.split('<') # split string become 2 part, one before and one afer char('<'). both of them don't cotain that char
    user_name=parts[0].strip() #remove white space before and after string
    userEmail=parts[1].replace('>','') 
    userPassword = config['General']['Password']
    mail_server = config['General']['MailServer']
    smtp_port = config['General']['SMTP']
    pop3_port = config['General']['POP3']
    autoload_time = config['General']['AutoLoad']
    print("This is your information I've got. If there is something wrong, then move to fileConfig.json file to change")
    print(f"Username: {user_name}")
    print(f"Email: {userEmail}")
    print(f"Password: {userPassword}")
    print(f"Mail Server: {mail_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"POP3 Port: {pop3_port}")
    print(f"Autoload Value: {autoload_time}")

    #Get input from user
    DestinationEmail=input("Enter Email Destination:")
    cc_Destination=input("Enter CC address if not just type 'Enter' ")
    bcc_Destination=input("Enter BCC address if not just type 'Enter' ")
    Subject=input("Enter Subject:")
    userMessage=input("Enter content you want to send:")
    message='{}.\r\n'.format(userMessage)
    flag_attachment=int(input("Co muon gui file dinh kem khonng(1.Co, 2.Khong)"))
    path_arr=[]
    total_file=0
    if(flag_attachment==1):
        total_file=int(input("So luong file muon gui"))
        for i in range(total_file):
            string=input("Nhap vao duong dan toi file cua ban (Luu y chi chap nhan forwardslash.EX: D:/test.pdf)")
            while(get_filesize(string)>3):
                string=input("Your file is too big, please enter another file(<=3MB)")
            path_arr.append(string)

    #xu li msg
    msg=MIMEMultipart()
    msg['Message-ID']=make_msgid(domain=userEmail[userEmail.rfind('@')+1:])
    msg['Date'] = formatdate(localtime=True)
    msg['User-Agent']="Fast-Mailer"
    msg['Content-Language']="en-US"
    msg['To']=DestinationEmail
    if(len(cc_Destination)!=0):
        msg['Cc']=cc_Destination
    msg['From']=name_email
    msg['Subject']=Subject
    msg.attach(MIMEText(userMessage))
    #msg.as_string()
    if(flag_attachment==1):
        for i in range(total_file):
            path=path_arr[i]
            type_file=path[path.rfind('.')+1:]  
            attachment=open(path,"rb")
            part=set_fileType(type_file,path)
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment",filename=os.path.basename(path))
            msg.attach(part)
    #create and connect socket to server    
    clientSocket=socket(AF_INET,SOCK_STREAM)
    clientSocket.connect((mail_server,smtp_port))
    recv0=clientSocket.recv(1024).decode()
    if(recv0[:3]!='220'):
        print("220 reply not received from server")

    #helo command    
    helloCommand='EHLO [{}]\r\n'.format(mail_server) #protocol here #EHLO [domain name]
    clientSocket.send(helloCommand.encode())
    recv1=clientSocket.recv(1024).decode()
    if(recv1[:3]!='250'):
        print("250 reply not received from server")

    #send mail from
    mailFrom="MAIL FROM:<{}>\r\n".format(userEmail)
    clientSocket.send(mailFrom.encode())
    recv6=clientSocket.recv(1024).decode()

    #RCP TO
    rcpto="RCPT TO:<{}>\r\n".format(DestinationEmail)
    clientSocket.send(rcpto.encode())
    recv7=clientSocket.recv(1024)
    if(len(cc_Destination)!=0):
        clientSocket.send("RCPT TO:<{}>\r\n".format(cc_Destination).encode())
        recv7=clientSocket.recv(1024)
    if(len(bcc_Destination)!=0):
        clientSocket.send("RCPT TO:<{}>\r\n".format(bcc_Destination).encode())
        recv7=clientSocket.recv(1024)

    #Send data
    clientSocket.send('DATA\r\n'.encode())
    recv8=clientSocket.recv(1024)
    clientSocket.sendall(msg.as_bytes())
    endmsg='.\r\n'
    clientSocket.send(endmsg.encode()) #endMsg
    recv9=clientSocket.recv(1024)

    #Quit socket
    quitCommand='QUIT\r\n'
    clientSocket.send(quitCommand.encode())
    recv9=clientSocket.recv(1024)
    clientSocket.close()

