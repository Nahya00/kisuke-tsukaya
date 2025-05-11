import discord
from discord.ext import commands
import json
import os
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix=";", intents=intents, help_command=None)

ID_SALON_VOCAL = 1367268760486023300
AUTHORIZED_ADMINS = [670301667341631490, 1359569212531675167]

WHITELIST_FILE = "whitelist.json"
LOCK_FILE = "lock_state.json"

# Charger la whitelist
if os.path.exists(WHITELIST_FILE):
    with open(WHITELIST_FILE, "r") as f:
        whitelist_ids = set(json.load(f))
else:
    whitelist_ids = set()

# Charger l'état du verrouillage
if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "r") as f:
        lock_active = json.load(f).get("locked", False)
else:
    lock_active = False

def save_whitelist():
    with open(WHITELIST_FILE, "w") as f:
        json.dump(list(whitelist_ids), f)

def save_lock_state():
    with open(LOCK_FILE, "w") as f:
        json.dump({"locked": lock_active}, f)

def is_authorized(ctx):
    return ctx.author.id in AUTHORIZED_ADMINS

async def reply_temp(ctx, content, delay=5):
    try:
        msg = await ctx.send(content)
        await asyncio.sleep(delay)
        await msg.delete()
    except:
        pass

@bot.event
async def on_ready():
    print(f"Bot prêt : {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    if lock_active and after.channel and after.channel.id == ID_SALON_VOCAL:
        if member.id not in whitelist_ids:
            try:
                await member.move_to(None)
            except:
                pass

@bot.command()
async def verrouiller(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = True
    save_lock_state()
    await reply_temp(ctx, "🔒 Salon vocal verrouillé.")

@bot.command()
async def deverrouiller(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = False
    save_lock_state()
    await reply_temp(ctx, "🔓 Salon vocal déverrouillé.")

@bot.command()
async def ajouter(ctx, membre: discord.Member):
    if not is_authorized(ctx):
        return
    whitelist_ids.add(membre.id)
    save_whitelist()
    await reply_temp(ctx, f"✅ {membre.display_name} ajouté à la whitelist.")

@bot.command()
async def retirer(ctx, membre: discord.Member):
    if not is_authorized(ctx):
        return
    whitelist_ids.discard(membre.id)
    save_whitelist()
    await reply_temp(ctx, f"❌ {membre.display_name} retiré de la whitelist.")

@bot.command()
async def liste(ctx):
    if not is_authorized(ctx):
        return
    user_list = []
    for uid in whitelist_ids:
        member = ctx.guild.get_member(uid)
        if member:
            user_list.append(f"- {member.name}#{member.discriminator}")
        else:
            user_list.append(f"- ID: {uid} (hors ligne ou quitté)")
    message = "**📋 Whitelist actuelle :**\n" + "\n".join(user_list) if user_list else "La whitelist est vide."
    await reply_temp(ctx, message, delay=10)

@bot.command()
async def help(ctx):
    if not is_authorized(ctx):
        return
    help_message = (
        "**🛠️ Commandes disponibles :**\n"
        "- `;verrouiller` → active la surveillance du salon vocal\n"
        "- `;deverrouiller` → désactive la surveillance\n"
        "- `;ajouter @user` → ajoute un utilisateur à la whitelist\n"
        "- `;retirer @user` → enlève un utilisateur de la whitelist\n"
        "- `;liste` → affiche les membres whitelistés\n"
        "- `;help` → affiche cette aide"
    )
    await reply_temp(ctx, help_message, delay=10)

bot.run(os.getenv("DISCORD_TOKEN"))
