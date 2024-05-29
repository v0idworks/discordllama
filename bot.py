import discord
from discord.ext import commands
from discord.ext.commands import Bot
import httpx
import asyncio
import json
import random

# Dictionary to store user histories
user_histories = {}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='?', description="cope and seethe ai", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged into {bot.user} (ID: {bot.user.id})')
    print('github.com/v0idworks/discordllama')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ваши вопросы."))

@bot.command(description='спросить лламу3')
async def ask(ctx, *, question: str):
    await ctx.defer()  # anti-timeout bc shitty gpu

    user_id = str(ctx.author.id)

    # Retrieve the user's conversation history, or start a new one
    history = user_histories.get(user_id, [])
    
    # Add the user's current message to the conversation history
    history.append({
        "role": "user",
        "content": question
    })

    data = { # payload for prompt
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
            print(f"Raw response: {response_text}")  # Debugging: Print the raw response
            
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
                user_histories[user_id] = history

                embed = discord.Embed(title="discordllama 1.1", url="https://github.com/v0idworks/discordllama", description="simple python script for integrating ollama as a discord bot", color=random.randint(0, 0xFFFFFF))
                embed.set_author(name="v0idworks", url="https://github.com/v0idworks", icon_url="insert image here")
                embed.add_field(name="Response", value=content, inline=False)
            except json.JSONDecodeError as e:
                content = f"Failed to parse JSON response: {str(e)}"
            
            await ctx.send(embed=embed)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 500:
            await ctx.send('Timeout Error, ask for the ai to answer shorter')
            print('timeout error.')
        else:
            await ctx.send(f"Server is angry, heres your http response: {exc.response.status_code}")
            print(f"http error: {exc.response.status_code}")
    except Exception as e:
        await ctx.send(f"Epic fail, heres what caused the error: {str(e)}")
        print(f"error: {str(e)}")
bot.run('')

