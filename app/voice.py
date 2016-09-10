import sys
from os import system
from collections import defaultdict
import imaplib
import getpass
import email
import datetime
import speech_recognition as sr
import pyaudio
import time
import json
import mysql.connector
from mysql.connector import Error
import uuid
from flask import Flask, render_template, request

# from flask.ext.mysqldb import MySQL

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def home():

    return render_template('index.html')

@app.route("/value", methods=['GET', 'POST'])
def mail():
    M = imaplib.IMAP4_SSL('imap.gmail.com')
    # db = MySQLdb.connect("127.0.0.1","root","","voice" )
    db = mysql.connector.connect(host='mail.cxfqvtil1ire.us-west-2.rds.amazonaws.com',database='voice',user='Vivek',password='Vivek0293')
    print "DB connection successful"
    try:
        #x=raw_input("Email Id:")
        id = request.form['id']
        pas = request.form['pass']
        M.login(id, pas)
    except imaplib.IMAP4.error:
        print "LOGIN FAILED!!! "
        a = "LOGIN FAILED!!!"
        return render_template('index.html', a=a)
    rv, data = M.select()
    if rv == 'OK':
        print "Processing mailbox...\n"
        start = time.time()
        print start
        Authenticate(M) # ... do something with emails, see below ...
        db.commit()
        M.close()
    M.logout()


def Authenticate(M):
    db = mysql.connector.connect(host='127.0.0.1', database='voice', user='root', password='')
    print "DB connection successful"
    rv, data = M.search(None, "ALL")

    if rv != 'OK':
        print "No messages found!"
        return

    final = defaultdict(list)
    sub = dict()
    line = dict()

    person = []
    c = []
    arrival = []
    some = []
    day = []
    days = []
    for num in data[0].split():
        # print num
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            print "ERROR getting message", num
            return
        b = list()
        lines = []
        id = uuid.uuid1()
        print id
        id = str(id)
        msg = email.message_from_string(data[0][1])

        nam = []
        name = msg['From']
        print name
        for i in range(0, len(name) - 1):
            if (name[i] == '<'):
                break
            else:
                nam.append(name[i])
                # print nam
        nam = ''.join(nam)
        print nam
        nam = nam.rstrip()
        if nam.startswith('"') and nam.endswith('"'):
            nam = nam[1:-1]
        nam = nam.lower()
        print nam
        person.append(nam)
        if msg.get_content_maintype() == 'multipart':  # If message is multi part we only want the text version of the body, this walks the message and gets the body.
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    # body = map(lambda s: s.strip(), body)
                    body = body.replace('\n', ' ')
                    body = body.replace('\r', ' ')
                    # body = ''.join(body)
                    b.append(body)
                    for i in range(0, len(body) - 1):
                        if (body[i] == '.'):
                            break
                        else:
                            lines.append(body[i])
                    lines = ''.join(lines)
                    some.append(lines)
                    # print lines
                else:
                    continue
        else:
            body = msg.get_payload(decode=True)
            # body = map(lambda s: s.strip(), body)
            body = body.replace('\n', '')
            body = body.replace('\r', '')
            # body = ''.join(body)
            b.append(body)
            for i in range(0, len(body) - 1):
                if (body[i] == '.'):
                    break
                else:
                    lines.append(body[i])
            lines = ''.join(lines)
            some.append(lines)
            # print lines
        mess = msg['Subject']
        mess = mess.lower()
        c.append(mess)
        # print c

        date_tuple = email.utils.parsedate_tz(msg['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            b.append(local_date.strftime("%a, %d %b %Y %H:%M:%S"))
            arrival.append(local_date.strftime("%a, %d %b %Y %H:%M:%S"))
            # print arrival

        final[id] = b
        cur = db.cursor()
        sub[nam] = c
        # line[nam] = lines
        # print line
    day = []
    d = ""
    for i in range(0, len(arrival)):
        print arrival[i]

        for j in range(0, len(arrival[i])):
            if arrival[i][j] == ",":
                break
            else:
                d = d + arrival[i][j]
        day.append(d)
        d = ""

        print day

    end = time.time()
    print end
    #total = end - start
    #print "The total time taken:", total, "secs"
    print "Total mails:", num
    # print arrival

    # print person
    cur.execute('truncate voice')
    i = 0
    for key, value in sorted(final.iteritems()):
        # print key
        # print value
        value = ''.join(value)
        # print value
        # print person[i]
        # print key, person[i], c[i], arrival[i], value
        cur.execute("""INSERT INTO Voice (id,person,subject,arrival,daay,line,message) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (key, person[i], c[i], arrival[i], day[i], some[i], value))
        i = i + 1
        cur.execute('commit')
        print "inserted"

    while True:
        # Record Audio
        week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        r = sr.Recognizer()
        with sr.Microphone() as source:
            system('say "Email by name or email by subject"')
            print("Say something!")
            audio = r.listen(source)

        print("You said: " + r.recognize_google(audio))
        var = r.recognize_google(audio)
        var = var.lower()
        if var == "name":
            with sr.Microphone() as source:
                system('say "Whose mail do you want me to read"')
                print("Say something!")
                audio = r.listen(source)

            print("You said: " + r.recognize_google(audio))
            varia = r.recognize_google(audio)
            varia = varia.lower()
            if (varia in sub):
                lol = []
                cur.execute("""SELECT count(subject) from Voice where person = %s""", (varia,))
                count = cur.fetchall()
                cur.execute('commit')
                print count[0]
                system('say "There are totally" %s "mails"' % (count[0]))
                cur.execute("""SELECT subject from Voice where person = %s""", (varia,))
                sub = cur.fetchall()
                sub = list(sub)
                cur.execute('commit')
                for i in sub:
                    lol.append(i[0])
                cur.execute("""SELECT subject, arrival from Voice where person = %s""", (varia,))
                content = cur.fetchall()
                content = list(content)
                cur.execute('commit')
                # system('say "The subjects of the mails are"')
                print "Subjects:"
                system('say "The subjects are"')

                for i in content:
                    system('say %s' % (i[0]))
                    time.sleep(1)
                    print i[0], "-", i[1]
                # print i[0]
                time.sleep(2)
                while True:
                    system('say "Which subject do you want me to read"')
                    with sr.Microphone() as source:
                        print("Say something!")
                        audio = r.listen(source)

                    print("You said: " + r.recognize_google(audio))
                    var = r.recognize_google(audio)
                    var = var.lower()
                    if var in lol:
                        while True:

                            system('say "Which day?"')
                            with sr.Microphone() as source:
                                print("Say something!")
                                audio = r.listen(source)

                            print("You said: " + r.recognize_google(audio))
                            vari = r.recognize_google(audio)
                            vari = vari[:3]
                            cur.execute(
                                """SELECT count(subject) from Voice where subject = %s and daay = %s and person = %s""",
                                (var, vari, varia))
                            count = cur.fetchall()
                            cur.execute('commit')
                            cur.execute(
                                """SELECT count(daay) from Voice where subject = %s and daay = %s and person = %s""",
                                (var, vari, varia))
                            count1 = cur.fetchall()
                            cur.execute('commit')
                            count1 = list(count)
                            print count
                            print count1
                            w = [x[0] for x in count]
                            y = [x[0] for x in count1]
                            print w, y
                            if w[0] > 1 and y[0] > 1:
                                if vari in week:

                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and person = %s""",
                                        (var, vari, varia))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    content = list(content)
                                    print content
                                    system('say "Which number?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    num = r.recognize_google(audio)
                                    num = int(num)
                                    print num
                                    # x = [x[1] for x in content]
                                    system('say "The first line of the mail says" %s' % (content[num]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and person = %s""",
                                            (var, vari, varia))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content
                                        # x = [x[1] for x in content]
                                        system('say "The mail says" %s' % (content[num]))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)
                                print "It works"
                            else:
                                if vari in week:
                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and person = %s""",
                                        (var, vari, varia))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    print content
                                    system('say "The first line of the mail says" %s' % (content[0]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and person = %s""",
                                            (var, vari, varia))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content
                                        system('say "The mail says" %s' % (content))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)
                    elif (var not in lol and var == 'exit'):
                        break

                    else:
                        system('say Sorry, there is no such subject')
                        time.sleep(1)


            elif (varia == 'my email'):
                lol = []
                cur.execute(
                    """SELECT count(subject) from Voice where person = 'vivek rahul' or person = 'vivek sundararajan' or person = 'viveksundararajan'""")
                count = cur.fetchall()
                cur.execute('commit')
                print count[0]
                system('say "There are totally" %s "mails"' % (count[0]))
                cur.execute(
                    """SELECT subject from Voice where person = 'vivek rahul' or person = 'vivek sundararajan' or person = 'viveksundararajan'""")
                sub = cur.fetchall()
                sub = list(sub)
                cur.execute('commit')
                for i in sub:
                    lol.append(i[0])
                cur.execute(
                    """SELECT subject, arrival from Voice where person = 'vivek rahul' or person = 'vivek sundararajan' or person = 'viveksundararajan'""")
                content = cur.fetchall()
                content = list(content)
                cur.execute('commit')

                print "Subjects:"
                system('say "The subjects are"')
                bla = 1
                for i in content:
                    if bla > 3:
                        system('say "Say yes if want to continue"')
                        with sr.Microphone() as source:
                            print("Say something!")
                            audio = r.listen(source)

                        print("You said: " + r.recognize_google(audio))
                        var = r.recognize_google(audio)
                        var = var.lower()
                        if var == "yes":
                            a = i[1]
                            system('say %s on %s' % (i[0], a[0:3]))
                            print i[0], "-", i[1]
                            bla = 2
                        else:
                            break
                    else:
                        a = i[1]
                        system('say %s on %s' % (i[0], a[0:3]))
                        time.sleep(1)
                        print i[0], "-", i[1]
                        bla = bla + 1

                time.sleep(2)
                while True:
                    system('say "Which subject do you want me to read"')
                    with sr.Microphone() as source:
                        print("Say something!")
                        audio = r.listen(source)

                    print("You said: " + r.recognize_google(audio))
                    var = r.recognize_google(audio)
                    var = var.lower()
                    if var in lol:
                        while True:

                            system('say "Which day?"')
                            with sr.Microphone() as source:
                                print("Say something!")
                                audio = r.listen(source)

                            print("You said: " + r.recognize_google(audio))
                            vari = r.recognize_google(audio)
                            vari = vari[:3]
                            cur.execute(
                                """SELECT count(subject) from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan')""",
                                (var, vari))
                            count = cur.fetchall()
                            cur.execute('commit')
                            cur.execute(
                                """SELECT count(daay) from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan')""",
                                (var, vari))
                            count1 = cur.fetchall()
                            cur.execute('commit')
                            count1 = list(count)
                            print count
                            print count1
                            w = [x[0] for x in count]
                            y = [x[0] for x in count1]
                            print w, y
                            if w[0] > 1 and y[0] > 1:
                                if vari in week:

                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan' or person = 'viveksundararajan')""",
                                        (var, vari))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    content = list(content)
                                    print content
                                    system('say "Which number?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    num = r.recognize_google(audio)
                                    num = int(num)
                                    print num

                                    system('say "The first line of the mail says" %s' % (content[num]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan'or person = 'viveksundararajan')""",
                                            (var, vari))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content

                                        system('say "The mail says" %s' % (content[num]))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)
                                print "It works"
                            else:
                                if vari in week:
                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan' or person = 'viveksundararajan')""",
                                        (var, vari))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    print content
                                    system('say "The first line of the mail says" %s' % (content[0]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan'or person = 'viveksundararajan')""",
                                            (var, vari))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content
                                        system('say "The mail says" %s' % (content[0]))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)
                    elif (var not in lol and var == 'exit'):
                        break

                    else:
                        system('say Sorry, there is no such subject')
                        time.sleep(1)

            elif (var == 'exit'):
                system('say Thank you, Have a nice day')
                sys.exit()

            else:
                system('say Sorry, there is no such mail')
                time.sleep(1)

        elif (var == "subject"):
            lol = []

            cur.execute("""SELECT subject from Voice""")
            sub = cur.fetchall()
            sub = list(sub)
            cur.execute('commit')
            for i in sub:
                lol.append(i[0])
            cur.execute("""SELECT  subject, arrival, person from Voice""")
            content = cur.fetchall()
            content = list(content)
            cur.execute('commit')
            # system('say "The subjects of the mails are"')
            print "Subjects:"
            system('say "The subjects are"')

            for i in content:
                system('say %s' % (i[0]))
                time.sleep(1)
                print i[0], "-", i[1], "-", i[2]
            # print i[0]
            time.sleep(2)
            while True:
                system('say "Which subject do you want me to read"')
                with sr.Microphone() as source:
                    print("Say something!")
                    audio = r.listen(source)

                print("You said: " + r.recognize_google(audio))
                var = r.recognize_google(audio)
                var = var.lower()
                if var in lol:
                    while True:
                        system('say "Which person?"')
                        with sr.Microphone() as source:
                            print("Say something!")
                            audio = r.listen(source)

                        print("You said: " + r.recognize_google(audio))
                        varia = r.recognize_google(audio)
                        varia = varia.lower()
                        if varia == "me":
                            system('say "Which day?"')
                            with sr.Microphone() as source:
                                print("Say something!")
                                audio = r.listen(source)

                            print("You said: " + r.recognize_google(audio))
                            vari = r.recognize_google(audio)
                            vari = vari[:3]

                            cur.execute(
                                """SELECT count(subject), count(daay) from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan')""",
                                (var, vari))
                            count = cur.fetchall()
                            cur.execute('commit')
                            count = list(count)
                            y = [x[0] for x in count]
                            z = [x[1] for x in count]
                            print y, z
                            if y[0] > 1 and z[0] > 1:
                                if vari in week:

                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan' or person = 'viveksundararajan')""",
                                        (var, vari))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    content = list(content)
                                    print content
                                    system('say "Which number?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    num = r.recognize_google(audio)
                                    num = int(num)
                                    print num
                                    # x = [x[1] for x in content]
                                    system('say "The first line of the mail says" %s' % (content[num]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan'or person = 'viveksundararajan')""",
                                            (var, vari))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content
                                        # x = [x[1] for x in content]
                                        system('say "The mail says" %s' % (content[num]))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)
                                print "It works"
                            else:
                                if vari in week:
                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan' or person = 'viveksundararajan')""",
                                        (var, vari))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    print content
                                    system('say "The first line of the mail says" %s' % (content[0]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and (person = 'vivek rahul' or person = 'vivek sundararajan'or person = 'viveksundararajan')""",
                                            (var, vari))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content
                                        system('say "The mail says" %s' % (content[0]))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)
                        elif varia in sub:
                            system('say "Which day?"')
                            with sr.Microphone() as source:
                                print("Say something!")
                                audio = r.listen(source)

                            print("You said: " + r.recognize_google(audio))
                            vari = r.recognize_google(audio)
                            vari = vari[:3]

                            cur.execute(
                                """SELECT count(subject), count(daay) from Voice where subject = %s and daay = %s and person = %s""",
                                (var, vari, varia))
                            count = cur.fetchall()
                            cur.execute('commit')
                            count = list(count)
                            y = [x[0] for x in count]
                            z = [x[1] for x in count]
                            print y, z
                            if y[0] > 1 and z[0] > 1:
                                if vari in week:

                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and person = %s """,
                                        (var, vari, varia))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    content = list(content)
                                    print content
                                    system('say "Which number?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    num = r.recognize_google(audio)
                                    num = int(num)
                                    print num
                                    # x = [x[1] for x in content]
                                    system('say "The first line of the mail says" %s' % (content[num]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and person = %s """,
                                            (var, vari, varia))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content
                                        # x = [x[1] for x in content]
                                        system('say "The mail says" %s' % (content[num]))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)
                                print "It works"
                            else:
                                if vari in week:
                                    cur.execute(
                                        """SELECT line from Voice where subject = %s and daay = %s and person = %s """,
                                        (var, vari, varia))
                                    content = cur.fetchall()
                                    cur.execute('commit')
                                    print content
                                    system('say "The first line of the mail says" %s' % (content[0]))
                                    time.sleep(1)
                                    system('say "Do you want me to continue?"')
                                    with sr.Microphone() as source:
                                        print("Say something!")
                                        audio = r.listen(source)

                                    print("You said: " + r.recognize_google(audio))
                                    opt = r.recognize_google(audio)
                                    if (opt == 'yes'):
                                        cur.execute(
                                            """SELECT message from Voice where subject = %s and daay = %s and person = %s """,
                                            (var, vari, varia))
                                        content = cur.fetchall()
                                        cur.execute('commit')
                                        print content
                                        system('say "The mail says" %s' % (content[0]))
                                    else:
                                        continue

                                elif (vari not in week and vari == 'exi'):
                                    break

                                else:
                                    system('say Sorry, there is no such day')
                                    time.sleep(1)

                        elif (varia not in sub and varia == 'exit'):
                            break

                        else:
                            system('say Sorry, there is no such person')
                            time.sleep(1)
                elif (var not in lol and var == 'exit'):
                    break

                else:
                    system('say Sorry, there is no such subject')
                    time.sleep(1)



        elif (var == 'exit'):
            system('say Thank you, Have a nice day')
            sys.exit()

        else:
            system('say Sorry, Wrong input')
            time.sleep(1)


if __name__ == "__main__":
    app.debug = True
    app.run()