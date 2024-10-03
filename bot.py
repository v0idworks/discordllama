import discord
from discord.ext import commands
from discord.ui import Select, View
import httpx
import json
import random
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Path to the file where user histories and sessions will be stored
HISTORY_FILE = "user_histories.json"

# Load user histories and sessions from the file if it exists
# Load user histories from the file if it exists
if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, "r") as f:
            user_histories = json.load(f)
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON from history file. Initializing an empty history.")
        user_histories = {}
else:
    user_histories = {}


def save_histories():
    logging.debug("Saving user histories to file.")
    with open(HISTORY_FILE, "w") as f:
        json.dump(user_histories, f, indent=4)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='?', description="cope and seethe ai", intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Logged into {bot.user} (ID: {bot.user.id})')
    logging.info('github.com/v0idworks/discordllama')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ваши вопросы."))

def get_user_sessions(user_id):
    """Retrieve a user's session list or create a new one."""
    if user_id not in user_histories:
        user_histories[user_id] = {"sessions": {}, "active_session": None}
        save_histories()
    return user_histories[user_id]

@bot.command(description='спросить лламу3')
async def ask(ctx, *, question: str):
    logging.debug(f"Received question: {question}")
    await ctx.defer()  # anti-timeout bc shitty gpu

    user_id = str(ctx.author.id)
    user_data = get_user_sessions(user_id)
    active_session_id = user_data.get("active_session")

    if not active_session_id:
        await ctx.send("Please select a session first using `?select_session`.")
        return

    # Retrieve the conversation history for the active session
    history = user_data["sessions"].get(active_session_id, [])
    
    # Add the user's current message to the conversation history
    history.append({
        "role": "user",
        "content": question
    })

    data = {  # payload for prompt
        "model": "llama3",
        "messages": history,
        "stream": False 
    }
    url = "http://localhost:11434/api/chat"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Handle response as text
            response_text = response.text
            logging.debug(f"Raw response: {response_text}")  # Debugging: Print the raw response
            
            try:
                # Attempt to find and parse the JSON part
                start_index = response_text.find('{')
                end_index = response_text.rfind('}') + 1
                json_part = response_text[start_index:end_index]
                response_data = json.loads(json_part)
                content = response_data.get("message", {}).get("content", "No content found.")
                
                # Add the assistant's response to the conversation history
                history.append({
                    "role": "assistant",
                    "content": content
                })
                
                # Save the updated history
                user_data["sessions"][active_session_id] = history
                user_histories[user_id] = user_data
                save_histories()

                embed = discord.Embed(title="discordllama 1.1", url="https://github.com/v0idworks/discordllama", description="simple python script for integrating ollama as a discord bot", color=random.randint(0, 0xFFFFFF))
                embed.set_author(name="v0idworks", url="https://github.com/v0idworks", icon_url="https://cdn.discordapp.com/app-assets/1243323068324249760/1243328165263441930.png")
                embed.add_field(name="Response", value=content, inline=False)
            except json.JSONDecodeError as e:
                content = f"Failed to parse JSON response: {str(e)}"
                logging.error(content)
            
            await ctx.send(embed=embed)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 500:
            await ctx.send('Timeout Error, ask for the AI to answer shorter')
            logging.error('Timeout error.')
        else:
            await ctx.send(f"Server is angry, here's your HTTP response: {exc.response.status_code}")
            logging.error(f"http error: {exc.response.status_code}")
    except Exception as e:
        await ctx.send(f"Epic fail, here's what caused the error: {str(e)}")
        logging.error(f"error: {str(e)}")

@bot.command(description='Select a conversation session')
async def select_session(ctx):
    user_id = str(ctx.author.id)
    user_data = get_user_sessions(user_id)

    sessions = user_data["sessions"]
    
    if not sessions:
        await ctx.send("You have no active sessions. Create one using `?create_session`.")
        return
    
    # Create a dropdown select menu
    options = [
        discord.SelectOption(label=session_id, description=f"Session {idx + 1}")
        for idx, session_id in enumerate(sessions)
    ]

    class SessionSelect(discord.ui.Select):
        def __init__(self):
            super().__init__(placeholder="Choose a session...", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            # Update the active session for the user
            selected_session = self.values[0]
            user_data["active_session"] = selected_session
            user_histories[user_id] = user_data
            save_histories()
            await interaction.response.send_message(f"Session `{selected_session}` is now active.")

    view = View()
    view.add_item(SessionSelect())

    await ctx.send("Please select a session:", view=view)

@bot.command(description='Create a new conversation session')
async def create_session(ctx):
    user_id = str(ctx.author.id)
    user_data = get_user_sessions(user_id)
    
    # Generate a unique session ID
    new_session_id = f"session_{len(user_data['sessions']) + 1}"
    user_data["sessions"][new_session_id] = []
    user_data["active_session"] = new_session_id
    user_histories[user_id] = user_data
    save_histories()

    await ctx.send(f"Created and activated new session `{new_session_id}`.")

@bot.command(description='Forget a session')
async def forget_session(ctx, session_id: str):
    user_id = str(ctx.author.id)
    user_data = get_user_sessions(user_id)

    if session_id in user_data["sessions"]:
        del user_data["sessions"][session_id]
        if user_data["active_session"] == session_id:
            user_data["active_session"] = None
        user_histories[user_id] = user_data
        save_histories()
        await ctx.send(f"Session `{session_id}` has been forgotten.")
    else:
        await ctx.send(f"Session `{session_id}` not found.")


bot.run('tokengoezhere')
