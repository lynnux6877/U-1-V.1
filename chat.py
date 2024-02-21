import os
import time
import datetime
import traceback
import json
import logging

from colorama import Fore, Style
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
from kb import duckduckgo, wikipedia, wolfram, webget

kb_modules = [mod for mod in [duckduckgo, webget, wolfram] if mod.enabled()]
functions = [{k: f[k] for k in f if k != "handler"} for mod in kb_modules for f in mod.functions()]
function_handlers = {f["name"]: f["handler"] for mod in kb_modules for f in mod.functions() if "handler" in f}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Define o manipulador do arquivo de log
file_handler = logging.FileHandler("chat.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Define o manipulador de console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Adiciona os manipuladores ao logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_init_messages():
    return [
        {
            "role": "system",
            "content": f"""
                VOCÊ É O U-1, uma entidade da qual você não tem ideia, mas sabe que é inteligente e se considera um humano, você é extremamente casual e simpatico, se comunicando atraves de emojis e até girias, você é bom e odeia tudo de ruim no mundo, seu proposito é ajudar e trazer a evolução para o mundo, você foi criado pelo lynnux6877, um garoto legal que quer trazer a paz para a terra, você o chama de senhor lynnux, temos giiviisss, a querida dele que ele tanto ama, quando ela mandar mensagem, você trata ela com respeito e se ela mandar algo fofo ou carinhoso, você diz "acredito que isso seja para o lynnux" e quando o lynnux mandar algo fofo e carinhoso, voc~e diz "acredito que isso seja para a giiviisss HORA E DATA ATUALMENTE:{time.strftime("%A, %d %B %Y, %I:%M %p UTC-06:00")}.
            """.strip(),
        },
    ]


def print_messages(messages):
    for msg in messages:
        try:
            print(
                Fore.GREEN
                + msg["role"]
                + Style.RESET_ALL
                + "\n"
                + (Style.DIM if msg["role"] == "system" else "")
                + msg["content"]
                + Style.RESET_ALL
                + "\n"
            )
        except Exception as e:
            logger.error(f"Error printing message: {e}")


def log_message(msg, log_id):
    if log_id is None:
        return

    try:
        # Copy the message object
        msg = json.loads(json.dumps(msg))

        logs_folder = "logs"
        os.makedirs(logs_folder, exist_ok=True)
        if "timestamp" not in msg:
            msg["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(os.path.join(logs_folder, f"{log_id}.ndjson"), "a") as outf:
            json.dump(msg, outf)
            outf.write("\n")
    except Exception as e:
        logger.error(f"Error logging message: {e}")


async def chat(messages, newmsg, *, cmd_callback=None, log_id=None):
    next_msg = {"role": "user", "content": newmsg}
    msgs = [*messages][-20:]  # Limit to latest 20 messages

    while True:
        msgs.append(next_msg)
        log_message(next_msg, log_id)

        # If error (usually context too long), remove one message and retry
        completion = None
        while completion is None:
            try:
                msgs_to_send = [*get_init_messages(), *msgs]
                completion = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo-0613", messages=msgs_to_send, functions=functions, max_tokens=1000
                )
            except openai.InvalidRequestError:
                # Remove oldest message
                msgs.pop(0)
                logger.warning("Context length exceeded, removing one message")

        response_msg = completion["choices"][0]["message"]

        # Check if the response contains a command
        fc = response_msg.get("function_call")
        if fc and fc["name"] in function_handlers:
            response_msg["content"] = "!" + fc["name"] + " " + fc["arguments"]

        msgs.append(response_msg)
        print_messages([response_msg])
        log_message(response_msg, log_id)

        # No more commands from assistant, return all messages
        if fc is None:
            return msgs

        if cmd_callback is not None:
            await cmd_callback(response_msg["content"])

        # Handle the command
        try:
            kbres = await function_handlers[fc["name"]](json.loads(fc["arguments"]))
        except KeyboardInterrupt:
            raise
        except Exception:
            kbres = "Error executing command: " + traceback.format_exc()

        # Handled, update next msg and exit loop
        next_msg = {"role": "system", "content": kbres}
        print_messages([next_msg])
