import os
import discord
import requests
import json
from chat import print_messages, get_init_messages, chat
from keep_alive import keep_alive
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="estou aqui para servir :) "))

histories = {}
def get_quote(cidade):
  url = "https://weatherapi-com.p.rapidapi.com/forecast.json"
  querystring = {"q":cidade,"days":"3"}
  headers = {
  "X-RapidAPI-Key": "f77c5bde9bmsh775458a2f3f1651p175e25jsn8b6a2f52c501",
  "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com"
  }
  response = requests.get(url, headers=headers, params=querystring)
  json_data = json.loads(response.text)
  return json_data

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

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith('tempo em'):
    cidade = message.content.split("tempo em ",1)[1]
    clima = get_quote(cidade)
    nome = clima['location']['name']
    região = clima['location']['region']
    país = clima['location']['country']
    hora_local = clima['location']['localtime']
    temp = clima['current']['temp_c']
    condição = clima['current']['condition']['text']
    velocidade_vento = clima['current']['wind_kph']
    sensação_térmica = clima['current']['feelslike_c']
    data1 = clima['forecast']['forecastday'][0]['date']
    previsão1_maxtemp = clima['forecast']['forecastday'][0]['day']['maxtemp_c']
    previsão1_mintemp = clima['forecast']['forecastday'][0]['day']['mintemp_c']
    previsão1_chance_chuva = clima['forecast']['forecastday'][0]['day']['daily_chance_of_rain']
    data2 = clima['forecast']['forecastday'][1]['date']
    previsão2_maxtemp = clima['forecast']['forecastday'][1]['day']['maxtemp_c']
    previsão2_mintemp = clima['forecast']['forecastday'][1]['day']['mintemp_c']
    previsão2_chance_chuva = clima['forecast']['forecastday'][1]['day']['daily_chance_of_rain']
    data3 = clima['forecast']['forecastday'][2]['date']
    previsão3_maxtemp = clima['forecast']['forecastday'][2]['day']['maxtemp_c']
    previsão3_mintemp = clima['forecast']['forecastday'][2]['day']['mintemp_c']
    previsão3_chance_chuva = clima['forecast']['forecastday'][2]['day']['daily_chance_of_rain']

    # Envia uma mensagem com as informações do clima
    # Envia uma mensagem com as informações do clima em formato de embed
    embed = discord.Embed(title=f"Informações sobre o clima em {nome}", color=0xFF0000)  # Cor vermelha
    embed.add_field(name="Cidade", value=nome, inline=True)
    embed.add_field(name="Região", value=região, inline=True)
    embed.add_field(name="País", value=país, inline=True)
    embed.add_field(name="Hora Local", value=str(hora_local), inline=True)
    embed.add_field(name="Temperatura", value=f"{temp}℃", inline=True)
    embed.add_field(name="Condição", value=condição, inline=True)
    embed.add_field(name="Velocidade do Vento", value=f"{velocidade_vento} kph", inline=True)
    embed.add_field(name="Sensação Térmica", value=f"{sensação_térmica}℃", inline=True)
    embed.add_field(name="Previsão", value=f"{data1}: {previsão1_maxtemp} ~ {previsão1_mintemp}, Chance de Chuva: {previsão1_chance_chuva}\n{data2}: {previsão2_maxtemp} ~ {previsão2_mintemp}, Chance de Chuva: {previsão2_chance_chuva}\n{data3}: {previsão3_maxtemp} ~ {previsão3_mintemp}, Chance de Chuva: {previsão3_chance_chuva}", inline=False)
    embed.set_image(url="https://i.gifer.com/8Osq.gif")  # Substitua "URL_DA_IMAGEM_AQUI" pela URL da imagem

    await message.channel.send(embed=embed)
      
keep_alive()
client.run(os.getenv("DISCORD_BOT_TOKEN"))

