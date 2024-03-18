import os
import discord
from chat import print_messages, get_init_messages, chat
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

histories = {}

async def send_long_message(channel, message):
    while len(message) > 2000:
        msg = message[:2000]
        await channel.send(msg)
        message = message[2000:]
    if len(message) > 0:
        await channel.send(message)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.strip():
        return

    uid = message.author.id if not message.guild else message.channel.id

    if uid not in histories:
        histories[uid] = []

    # Verifica se a mensagem é exatamente "!oss"
    if message.content.strip() == "!oss":
        async with message.channel.typing():
            message_content = ("[" + message.author.name + "] " if message.guild else "") + message.content
            print_messages([{"role": message.author.name, "content": message.content}])

            histories[uid] = await chat(
                histories[uid],
                message_content,
                log_id=f"discord_{uid}",
            )

        await send_long_message(message.channel, histories[uid][-1]["content"])
        return

keep_alive()
client.run(os.getenv("DISCORD_BOT_TOKEN"))
