import discord
from discord.ext import commands
from discord.ext.commands import Bot
import httpx
import asyncio
import json

def botinit(): #shitty init for "optimization" im litteraly coding in python....
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    bot = commands.Bot(command_prefix='?', description="cope and seethe ai", intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'Logged into {bot.user} (ID: {bot.user.id})')
        print('canonical.lol')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ваши вопросы."))
    @bot.command(description='спросить лламу3')
    async def ask(ctx, *, question: str):
        await ctx.defer()  # anti-timeout bc shitty gpu
        
        data = { #payload 4 prompt
            "model": "llama3",
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "stream": False 
        }
        url = "http://localhost:11434/api/chat"
        print(question
        )
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
                except json.JSONDecodeError as e:
                    content = f"Failed to parse JSON response: {str(e)}"
                
                await ctx.send(content)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 500:
                  await ctx.send('Долго думал и сломался, попроси короче ответить.')
                  print('timeout error.')
            else:
                await ctx.send(f"http error code: {exc.response.status_code}")
                print(f"http error: {exc.response.status_code}")
        except Exception as e:
            await ctx.send(f"error: {str(e)}")
            print(f"error: {str(e)}")
        await ctx.send(input()) #additional feature for feedback, incase bot fails, so you can send msgs to user(works per ?ask command response)
        
    bot.run('')

