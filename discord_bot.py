import os
import discord
from chat import print_messages, get_init_messages, chat

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

    if message.content.strip() == "!reset":
        histories[uid] = []
        await message.channel.send("Chat has been reset.")
        return

    async def cmd_callback(cmd):
        await message.channel.send(f"Executing command: `{cmd}`")

    async with message.channel.typing():
        message_content = ("[" + message.author.name + "] " if message.guild else "") + message.content
        print_messages([{"role": message.author.name, "content": message.content}])
        histories[uid] = await chat(
            histories[uid],
            message_content,
            cmd_callback=cmd_callback,
            log_id=f"discord_{uid}",
        )

    await send_long_message(message.channel, histories[uid][-1]["content"])

client.run(os.getenv("DISCORD_BOT_TOKEN"))