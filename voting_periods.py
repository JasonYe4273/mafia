import requests
import sqlite3
import time
import datetime
import random
import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TIME_PER_DAY = datetime.timedelta(minutes = 1)

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "mitmafia608@gmail.com"  # Enter your address
password = "608design"
receiver_email = 'kms20@mit.edu'

def request_handler(request):
#    print(request['method'])
    if request['method']=='GET':
        return send_updates(request['values']['gameID'])
    return "there was an error with your request needs to be get"


def send_email(receiver_email, id, sender_email=sender_email):
    try:
        receiver_email = receiver + "@mit.edu"
        message = MIMEMultipart("alternative")
        message["Subject"] = "multipart test"
        message["From"] = sender_email
        message["To"] = receiver_email

        text = """
        Hi {name},
        How are you?
        Real Python has many great tutorials:
        www.realpython.com"""
        text = text.format(name=receiver)
        html = """\
        <html>
          <body>
            <p>Hi {name},<br>
               Click this link for game updates:
               <a href="http://608dev.net/sandbox/sc/kms20/mafia/getStatus.py?kerberos={name}&gameID={id}">mafia updates!</a>
            </p>
          </body>
        </html>
        """
        html = html.format(name=receiver, id = id)
        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)
        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )
    except:
        print('email failed')

def end_voting(gameID, cursor, potential=None, days_ago=0):
    c = cursor
    best = c.execute('''SELECT kerberos FROM rolesTe WHERE gameID=? AND status=?;''',(gameID, 'alive')).fetchall()
    users = []
#        append the users to the list of users in a random order
    for tup in set(best):
        if tup[0]!="":
            users.append(tup[0])
    dead_dict = {}
    if potential is None:
        potential = users
    for player in potential:
        dead_dict[player] = 0
    max = 0
    given_votes = ""
    start = datetime.datetime.now()-(VOTING_PERIOD*(days_ago+1))
    end = datetime.datetime.now()-(VOTING_PERIOD*days_ago)
    dead = []
    for voter in users:
        vote = c.execute('''SELECT vote FROM votes WHERE gameID=? AND timing>? AND timing<? AND kerberos=? ORDER BY timing DESC;''',(gameID, start, end, voter)).fetchone()
        if vote is not None:
            vote = vote[0]
        if vote in dead_dict:
            dead_dict[vote] += 1
            if dead == [] or dead_dict[vote]>max_:
                dead = [vote]
                max_ = dead_dict[vote]
            elif dead_dict[vote]==max_:
                dead.append(vote)
    if len(dead)==1:
        return dead[0]
    elif len(dead)>1:
        prev_most = end_voting(gameID, cursor, dead, days_ago+1)
        if prev_most != None:
            return prev_most
        else:
            return dead[0]

def check_win_condition(game_id, c):
    maf = None
    alive = []
    for player, role, status in c.execute('''SELECT kerb, role, status FROM rolesTe WHERE gameID=?;''',(game_id,)).fetchall():
        if status == "alive":
            if maf is None:
                maf = role in mafia
            elif maf != role in mafia:
                return (False,None)
    return (True, maf)

def send_updates(game_id):
    example_db = "__HOME__/playersT.db" # just come up with name of database
    conn = sqlite3.connect(example_db)  # connect to that database (will create if it doesn't already exist)
    c = conn.cursor()
    timer = datetime.datetime.now()
    maf = None
    while True:
        if datetime.datetime.now()-timer>=TIME_PER_DAY:
            print("new day")
            timer = datetime.datetime.now()
            death = end_voting(game_id, c)
            for role in c.execute('''SELECT kerb FROM rolesTe WHERE gameID=?;''',(game_id,)).fetchall():
                send_email(role, game_id)
            if death != None:
                c.execute('''UPDATE rolesTe SET status = "dead" WHERE kerberos=? AND gameID=?;''',(death,game_id))
                win, maf = check_win_condition(game_id,c)
                if win:
                    break

    if maf == True:
        print("maf")
        return "maf win"
    return "citizen win"
