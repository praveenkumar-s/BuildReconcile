import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.charset import Charset, BASE64
from email.mime.nonmultipart import MIMENonMultipart
from email import charset
import json



flight_plan = json.load(open('flight_plan.json'))


def sendmail_msg(msg):
    mailserver = smtplib.SMTP(
        flight_plan['mail_config']['smtp'], flight_plan['mail_config']['port'])
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.send_message(msg)
    mailserver.quit()


def create_msg(mailing_list, attachment_file_path, subject, body ):
    msg = MIMEMultipart("mixed")
    if(attachment_file_path != None):
        attachment = MIMENonMultipart('text', 'csv', charset='utf-8')
        attachment.add_header('Content-Disposition', 'attachment', filename=attachment_file_path)
        cs = Charset('utf-8')
        cs.body_encoding = BASE64
        fp = open(attachment_file_path,'rb')
        attachment.set_payload(fp.read(), charset=cs)       
        fp.close()            
        msg.attach(attachment)
    
    body_t = MIMEMultipart('alternative')
    body_t.attach(MIMEText(body.encode('utf-8'),
                            'plain', _charset='utf-8'))

    
    msg.attach(body_t)
    msg['Subject'] = subject
    msg['From'] = flight_plan['mail_config']['from']
    msg['To'] = flight_plan['mail_config'][mailing_list]
    return msg

def perform_send_mail(mailing_list, attachment_file_path, subject,  body ):
    if(flight_plan['mail_config']['is_notification_service']):
        pass
        #send Mail using notification service | Not implemented yet 
        raise NotImplementedError
    else:
        sendmail_msg( create_msg(mailing_list, attachment_file_path, subject, body) )

