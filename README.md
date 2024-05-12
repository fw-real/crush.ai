# crush.ai (no i don't own the domain)
just a side project i made for a friend. this project is basically a socket io based chat client and responses are handled by character.ai's characters which is made possible by [this library](https://github.com/kramcat/CharacterAI). if you want to self host skip to the next section.

### live demo: https://crush-ai.onrender.com/chat

# self host guide
1. login to character.ai , open a chat of the desired character the url will look like this -> https://character.ai/chat/{a_long_string_here} that long string is your char id, go ahead and paste it in the .env file

2. while you are on the chat window of the character, press ctrl+shift+i to open dev tools, navigate to the network tab, and click on "fetch/xhr", reload the page then on the network tab try to find the request which says "info/" in the headers find the "Authorization" field, the value next to it prolly looks like "Token your_token_string_here" that string there is your token only copy that and paste it in the .env file

3. you also need a postgres db, [get it here](https://www.postgresql.org/download/) and setup a db with the cmds in `db.sql` file. after that's done get the postgres url in format: `postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]` and paste in the .env file
3. run the program (if you want to adjust the server ip and port, you are free to do so by editing main.py's last line, for the port just add the port variable and assign it the port you need in the socketio.run() function as i have not by default passed it.)

4. yea that's all


# bugs and suggestions
if you got some to share yk what to do drop an issue/pr or hit me up on discord
