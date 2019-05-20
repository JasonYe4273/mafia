import sqlite3
import sys
sys.path.append("__HOME__/mafia")
import updateGame
from getStatus import HTMLHEAD, HEAD, urls

#idea for redirects from: https://www.poftut.com/how-to-redirect-html-web-page-into-another-url/

LOGIN = "http://608dev.net/sandbox/sc/kms20/mafia/login.html"
STATUS = "http://608dev.net/sandbox/sc/kms20/mafia/getStatus.py?kerberos="
HOME = "http://608dev.net/sandbox/sc/kms20/mafia/home.py?kerberos="

REDIRECT = ''' <html>
                <head>
                    <meta http-equiv="refresh" content="0; URL='{}'"/>
                </head>
                <body>

                Redirecting...
                </body>
                </html>
            '''
LOGIN_TEXT = '''
<html> 
<head> 
<link rel="icon" type = "image/jpg" href = "http://clipart-library.com/img/1762322.jpg" />
<title>  Mafia </title> 
          
</head>

<body>

<h1> <font style="font-size: 55px"> 
Welcome to live action mafia! </font> </h1>
                                     
<p>
{}
</p>

Login: <br>
<!-- be sure to change this address if you're running it on another server location -->
<form method="POST" action="http://608dev.net/sandbox/sc/kms20/mafia/login_verify.py">  <br>
Kerberos: <input type="text" name="kerberos"/> <br>
Password: <input type="password" name="password"/> <br>
<input type = "hidden" name = "new" value ="False"/> <br>
<input type="submit" value="submit"/>
</form>  <br>  <br>  <br>

Don't have an account? Make one here!
<form method="POST" action="http://608dev.net/sandbox/sc/kms20/mafia/login_verify.py">  <br>
Kerberos: <input type="text" name="kerberos"/> <br>
Password: <input type="password" name="password1"/> <br>
Retype password: <input type="password" name="password2"/> <br>
<input type = "hidden" name = "new" value ="True"/> <br>
<input type="submit" value="submit"/>


</body>
</html>
'''

def request_handler(request):
    '''
    '''
    if request['method'] == 'POST':
        return post_handler(request)
    return "Something is wrong with your request."


def post_handler(request):
    '''
    '''
    conn = updateGame.get_db_connection()  # connect to that database (will create if it doesn't already exist)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Login (kerberos text, password text);''')
    kerberos = request['form']['kerberos']
    if request['form'].get('new') == 'True':
        pw1 = request['form']['password1']
        pw2 = request['form']['password2']
        if pw1 == pw2:
            c.execute('''INSERT into Login VALUES (?,?);''',(kerberos,pw1))
            conn.commit()
            conn.close()
            return REDIRECT.format(HOME + kerberos)
        return LOGIN_TEXT.format("Sorry, passwords do not match! Please try again.")
    pw = c.execute('''SELECT password FROM Login WHERE kerberos=?;''',(kerberos,)).fetchone()
    if not pw:
        conn.commit()
        conn.close()
        return LOGIN_TEXT.format("Sorry, this user does not exist. Please make an account.")
    password = request['form']['password']
    if pw[0] == password:
        conn.commit()
        conn.close()
        return REDIRECT.format(HOME + kerberos)
    conn.commit()
    conn.close()
    return LOGIN_TEXT.FORMAT("Sorry,wrong password.")
