import random
import re
import requests
import socket
import string
from time import sleep


def editConfig(param: str, value: str):
    with open('config.txt', 'r') as f1:
        data = f1.read()
    findStr = re.compile(param + r'="\w*",')
    match = re.search(findStr, data)
    start, final = match.start(), match.end()
    with open('config.txt', 'w') as f2:
        f2.write(data[:start] + f'{param}="{value}",' + data[final:])


class TwitchHandler:
    def __init__(self, consts, cid, secret, scopes, code="", aac="", uac="", urc="", uid="", server="http://localhost"
                                                                                                    ":3000"):
        self.CONSTS = consts

        self.CID = cid  # need for WHAT BOT do
        self.secret = secret  # as a password without auth
        self.code = code  # for getting UAC/URC
        self.AAC = aac  # for auth without UAC/URC and
        self.UAC = uac  # need for ON WHOSE BEHALF do
        self.CONSTS['AUTH_PASS'] += self.UAC
        self.URC = urc  # for refresh UAC
        self.scopes = scopes  # permissions
        self.target = self.CONSTS['channel']  # nick of target channel
        self.UID = uid  # id of target channel
        self.server = server  # redirect uri

        self.botAuth()

    def botAuth(self):
        if not self.AAC:
            responseAAC = requests.post('https://id.twitch.tv/oauth2/token', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={'client_id': self.CID, 'client_secret': self.secret, 'grant_type': 'client_credentials'})
            self.AAC = responseAAC.json()['access_token']
            editConfig('aac', self.AAC)
        if not self.UID:
            responseTarget = requests.get('https://api.twitch.tv/helix/users?login=' + self.target, headers={'Authorization': 'Bearer ' + self.AAC, 'Client-Id': self.CID})
            self.UID = responseTarget.json()['data'][0]['id']
        if not self.URC:
            state = ''.join(random.choices(string.ascii_lowercase[:6] + string.digits, k=32))
            print(f"https://id.twitch.tv/oauth2/authorize?client_id={self.CID}&redirect_uri={self.server}&response_type=code&scope={'+'.join(list(map(lambda s: s.replace(':','%3A'), self.scopes)))}&force_verify=false&state={state}")
            self.code = input()
            editConfig('code', self.code)
            respUAC = requests.post('https://id.twitch.tv/oauth2/token', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={'client_id': self.CID, 'client_secret': self.secret, 'grant_type': 'authorization_code', 'code': self.code, 'redirect_uri': self.server})
            self.UAC = respUAC.json()['access_token']
            editConfig('uac', self.UAC)
            self.URC = respUAC.json()['refresh_token']
            editConfig('urc', self.URC)
        self.refresh(requests.get, 'https://api.twitch.tv/helix/users?login=' + self.target, headers={'Authorization': 'Bearer ' + self.UAC, 'Client-Id': self.CID})
        self.run()

    def refresh(self, func, *args, **kwargs):
        response = func(*args, **kwargs)
        if 'error' in response.json().keys():
            respFresh = requests.post('https://id.twitch.tv/oauth2/token', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'refresh_token', 'refresh_token': self.URC, 'client_id': self.CID, 'client_secret': self.secret})
            self.UAC = respFresh.json()['access_token']
            self.CONSTS['AUTH_PASS'] = self.CONSTS['AUTH_PASS'].split(':')[0] + ':' + self.UAC
            editConfig('uac', self.UAC)
            response = func(*args, **kwargs)
        return response

    def createPoll(self, question: str, answers: list[str], duration: int):
        return self.refresh(requests.post, 'https://api.twitch.tv/helix/polls', headers={'Authorization': 'Bearer ' + self.UAC, 'Client-Id': self.CID, 'Content-Type': 'application/json'}, data={"broadcaster_id": self.UID, "title": question, "choices": [{"title": el} for el in answers], "duration": duration})

    def createPred(self, question: str, answers: list[str], duration: int):
        return self.refresh(requests.post, 'https://api.twitch.tv/helix/predictions', headers={'Authorization': 'Bearer ' + self.UAC, 'Client-Id': self.CID, 'Content-Type': 'application/json'}, data={"broadcaster_id": self.UID, "title": question, "outcomes": [{"title": el} for el in answers], "prediction_window": duration})

    def getChatters(self):
        return self.refresh(requests.get, f'https://api.twitch.tv/helix/chat/chatters?broadcaster_id={self.UID}&moderator_id={self.UID}', headers={'Authorization': 'Bearer ' + self.UAC, 'Client-Id': self.CID})

    def getModerators(self):
        return self.refresh(requests.get, f'https://api.twitch.tv/helix/moderation/moderators?broadcaster_id={self.UID}', headers={'Authorization': 'Bearer ' + self.UAC, 'Client-Id': self.CID})

    def sendMessage(self, s: socket.socket, msg: str):
        s.send("PRIVMSG #{} :{}\r\n".format(self.target, msg).encode("utf-8"))

    def run(self):
        s = socket.socket()
        s.connect((self.CONSTS['HOST'], int(self.CONSTS['PORT'])))
        s.send("PASS {}\r\n".format(self.CONSTS['AUTH_PASS']).encode("utf-8"))
        s.send("NICK {}\r\n".format(self.CONSTS['AUTH_NICK']).encode("utf-8"))
        s.send("JOIN #{}\r\n".format(self.CONSTS['channel']).encode("utf-8"))
        CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

        while True:
            response = s.recv(2048).decode("utf-8")
            print(response)
            username = re.search(r"\w+", response)
            message = CHAT_MSG.sub("", response)
            if username:
                username = username.group(0)

            if response == "PING :tmi.twitch.tv\r\n":
                s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))

            if message.strip() == '!ping':
                self.sendMessage(s, 'pong')
            elif message.strip() == '!quit' and (username in list(map(lambda x: x['user_name'], self.getModerators().json()['data'])) or username == self.target):
                self.sendMessage(s, 'Bye!')
                break

            sleep(0.05)


if __name__ == "__main__":
    fileVars = {}
    dictS = re.compile(r'(?:\w|\.|:)+')
    strS = re.compile(r'(?:\w|\.|:)+')
    f = open('config.txt', 'r')
    nameOfVar = ''
    isInDict = False
    isInList = False
    for line in f.readlines():
        strLine = re.findall(strS, line)
        if '}' in line:
            isInDict = False
            nameOfVar = ''
        elif ']' in line:
            isInList = False
            nameOfVar = ''
        elif len(strLine) == 1 and '=' in line:
            nameOfVar = strLine[0]
        elif isInDict:
            fileVars[nameOfVar][strLine[0]] = strLine[2]
        elif isInList:
            fileVars[nameOfVar].append(strLine[0])
        elif '{' in line:
            isInDict = True
            fileVars[nameOfVar] = {}
        elif '[' in line:
            isInList = True
            fileVars[nameOfVar] = []
        else:
            fileVars[strLine[0]] = strLine[1]
    f.close()

    TwitchHandler(**fileVars)
