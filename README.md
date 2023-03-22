# twitchBot
Sorted out twitch API for python to requests and websockets, all processes are automated and described in detail.

For correct working set the initial values in the config file:
1. Client id
2. Client secret
3. AUTH_NICK
4. channel
The first two you can find in twitch dev console during creating your app. The third one is in the same place, it's a name of your app. And the fourth is the name of the target channel, the same as nickname of the streamer. In detail this and more is decribed below.

## How I created this

1. Create an application on https://dev.twitch.tv/console, name and category are arbitrary, redirect uri is your server address. If this app is planned to be launched from this PC, enter http://localhost:3000 address (I wiil use this one further). On the dashboard click "manage" against your app. Then copy and create variables in program, which are called "client_id" and "client_secret". The second one isn't saved on this page, so copy this to reliable storage.

2. We will send requests. It will be showed with "curl" (linux bash command). But it may be also realized with requests in your programming language or just in address-line in your browser. Of course, format is different for each way. NOTE: -X - method of request (GET/POST/etc custom methods), -H - headers with a request in format "Key: value", -d - data in json or uri (?{1}&{2}...) format.

request:
curl -X POST 'https://id.twitch.tv/oauth2/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'client_id=<client_id>&client_secret=<client_secret>&grant_type=client_credentials'

answer:
{"access_token":"<app_access_token>","expires_in":4738951,"token_type":"bearer"}

3. Copy to a variable a value by key "app_access_token".

4. Check if this token is working. Over time you'll need in this command to know user id of smbd, whose stream app visited.

request:
curl -X GET 'https://api.twitch.tv/helix/users?login=twitchdev' -H 'Authorization: Bearer <app_access_token>' -H 'Client-Id: <client_id>'

answer:
{"data":[{"id":"<user_id>","login":"twitchdev","display_name":"TwitchDev","type":"","broadcaster_type":"partner","description":"Supporting third-party developers building Twitch integrations from chatbots to game integrations.","profile_image_url":"https://static-cdn.jtvnw.net/jtv_user_pictures/8a6381c7-d0c0-4576-b179-38bd5ce1d6af-profile_image-300x300.png","offline_image_url":"https://static-cdn.jtvnw.net/jtv_user_pictures/3f13ab61-ec78-4fe6-8481-8682cb3b0ac2-channel_offline_image-1920x1080.png","view_count":19044088,"created_at":"2016-12-14T20:32:28Z"}]}

So we can get information about any user you want, just replace "twitchdev" with another login. Practice if you want some.

5. Now we want to get User Access Token. Just enter in your address-line (not curl, because you'll have to confirm getting token from your twitch account, you'll be redirected to official twitch page. Link has two incomprehensible parameters: scope and state. State is a random string, that consists of 16-bit numbers, redirecting link must include the same state, else it's a malicious answer. Scope consists of permissions from this: https://dev.twitch.tv/docs/authentication/scopes link. Different permissions are splited by pluses, colons in them are replaced by special web characters "%3A". The most common permissions are chat:read and chat:edit for read/write messages to stream room chat.

request:
https://id.twitch.tv/oauth2/authorize?client_id=<client_id>&redirect_uri=http://localhost:3000&response_type=code&scope=<scopes>&force_verify=false&state=c3ab8aa609ea11e793ae92361f002671

Then you'll be redirected to Twitch page, where you should confirm app access to account. Then you'll be redirected to your <redirect_uri> with some parameters.

answer:
http://localhost:3000/?code=<code>&scope=<scopes>&state=c3ab8aa609ea11e793ae92361f002671

6. From this answer we need to save parameter named "code" to variable. Then make request:

request:
curl -X POST 'https://id.twitch.tv/oauth2/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'client_id=<client_id>&client_secret=<client_secret>&grant_type=authorization_code&code=<code>&redirect_uri=http://localhost:3000'
 
answer (scopes in list format, not in uri with "+" and "%3A"):
{"access_token":"<user_access_token>","expires_in":15080,"refresh_token":"<user_refresh_token>","scope":[<scopes>],"token_type":"bearer"}

Save user access token and user refresh token to variables.

7.Then you can join to streams of person, who confirms access, and apply some of these commands, for which app has a corresponding permission: https://dev.twitch.tv/docs/api/reference, just make corresponding requests.
Three important moments.
1) Earlier we used app_access_token in Authorization header, now, after completing the app setup and getting user_access_token, we will use this one. Type is the same, "Bearer".
2) A user_access_token is alive for only about four hours! After that requests will return answer "{"error":"Unauthorized","status":401,"message":"Invalid OAuth token"}". If we get error 401, just refresh your user_access_token:
curl -X POST https://id.twitch.tv/oauth2/token -H 'Content-Type: application/x-www-form-urlencoded' -d 'grant_type=refresh_token&refresh_token=<user_refresh_token>&client_id=<client_id>&client_secret=<client_secret>'
answer:
{"access_token": "1ssjqsqfy6bads1ws7m03gras79zfr", "refresh_token": "eyJfMzUtNDU0OC4MWYwLTQ5MDY5ODY4NGNlMSJ9%asdfasdf=", "scope": ["channel:read:subscriptions", "channel:manage:polls"], "token_type": "bearer"}
3) User id (broadcaster_id and moderator_id) you can get from step 4 by request by a login. Broadcaster is a streamer, moderator is a moderator (suddenly).
As example:

request (creating a poll):
curl -X POST 'https://api.twitch.tv/helix/polls' -H 'Authorization: Bearer <user_access_token>' -H 'Client-Id: <client_id>' -H 'Content-Type: application/json' -d '{"broadcaster_id":"<user_id>","title":"Streaming next Tuesday. Which time works best for you?","choices":[{"title":"9AM"},{"title":"10AM"},{"title":"7PM"},{"title":"8PM"},{"title":"9PM"}],"duration":300}'

request (start a raid):
curl -X POST 'https://api.twitch.tv/helix/raids?from_broadcaster_id=<user_id>&to_broadcaster_id=<another_user_id>' -H 'Authorization: Bearer <user_access_token>' -H 'Client-Id: <client_id>'

request (creating a prediction):
curl -X POST 'https://api.twitch.tv/helix/predictions' -H 'Authorization: Bearer <user_access_token>' -H 'Client-Id: <client_id>' -H 'Content-Type: application/json' -d '{"broadcaster_id":"<user_id>","title":"What level will I reach today?","outcomes":[{"title":"Level 1"},{"title":"Level 2"},{"title":"Level 3"},{"title":"Level 4"}],"prediction_window":300}'

request (get chatters):
curl -X GET 'https://api.twitch.tv/helix/chat/chatters?broadcaster_id=<user_id>&moderator_id=<user_id>' -H 'Authorization: Bearer <user_access_token>' -H 'Client-Id: <client_id>'
answer:
{"data":[{"user_id":"<user_id>","user_login":"<login>","user_name":"<name>"}, ...], "pagination": {"cursor": "???"}, "total": <number>}

request (get moderators, broadcaster isn't a moderator):
curl -X GET 'https://api.twitch.tv/helix/moderation/moderators?broadcaster_id=<user_id>' -H 'Authorization: Bearer <user_access_token>' -H 'Client-Id: <client_id>'
answer:
{"data":[{"user_id":"<user_id>","user_login":"<login>","user_name":"<name>"}, ...], "pagination": {"cursor": "???"}}

8. But chatting isn't so easy for apps unlike extensions. This is realized by library "socket", WebSocket technology. JWT, which is needed for PubSub messaging, forces us to use an extension, but we have only an app.
Make constants: {"HOST": "irc.chat.twitch.tv", "PORT": 6667, "AUTH_NICK": "<app_name>", "AUTH_PASS": "oauth:xxxxxxxxxxxx", "channel": "somechannel"}
Then code:
s = socket.socket()
s.connect((config['HOST'], config['PORT']))
s.send("PASS {}\r\n".format(config['AUTH_PASS']).encode("utf-8"))
s.send("NICK {}\r\n".format(config['AUTH_NICK']).encode("utf-8"))
s.send("JOIN #{}\r\n".format(config['channel']).encode("utf-8"))
CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
Then go into a loop.
response = s.recv(2048).decode("utf-8")
username = re.search(r"\w+", response).group(0)
message = CHAT_MSG.sub("", response)
Then check message and sleep until next loop iteration.
This string will send a message:
s.send("PRIVMSG #{} :{}\r\n".format(config['channel'], msg).encode("utf-8"))
Twitch will send PING signals sometimes. Answer to it to show, that you are alive.
if response == "PING :tmi.twitch.tv\r\n":
    s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))

9. Now you can see, that... you answer for your own commands?? What!? But don't be upset! Yes, bot speak for you, because bot gets permissions for itself in any room, where he can realize these permissions. This is a process of getting an user_access_token. Your app get permissions to act for you.
But if you want to bot act for itself, create an account for it, and then in its console create and authorize corresponding app.
Then you can promote your bot to moderator in your chat-room. Then it will be able to do smth, that exists in scopes, but allowed only for moderators.

For config.txt make backup.txt, because of data in this file is important!
