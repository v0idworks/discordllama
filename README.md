# discordllama
## Semi-decent discord - ollama integration
### Features:
    asking your llama model
    feedback from terminal(works once per ?ask command) for example timeout error, you can type "sorry the bot broke" and press enter
### TODO: 
    add separate history for each user
    command to wipe history
    turn messages into embed format
    model selector
    session selector
### Pre-requisites
     python3
     discord.py
     discord.ext
     asyncio
     httpx
     json
### Instalation
Run ollama serve 
make an init.py file containing the following:
from bot import botinit
botinit()
run init.py
