import discord
from discord.ext import commands
import json
import os
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=";", intents=intents, help_command=None)

ID_SALON_VOCAL = 1367268760486023300
AUTHORIZED_ADMINS = [670301667341631490, 1359569212531675167]

USER_WL_FILE = "whitelist_users.json"
ROLE_WL_FILE = "whitelist_roles.json"
LOCK_FILE = "lock_state.json"

def load_list(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return set(json.load(f))
    return set()

def save_list(file, data):
    with open(file, "w") as f:
        json.dump(list(data), f)

whitelisted_user_ids = load_list(USER_WL_FILE)
whitelisted_role_ids = load_list(ROLE_WL_FILE)

if os.path.exists(LOCK_FILE):
    with open(LOCK_FILE, "r") as f:
        lock_active = json.load(f).get("locked", False)
else:
    lock_active = False

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

def is_whitelisted(member):
    if member.id in whitelisted_user_ids:
        return True
    return any(role.id in whitelisted_role_ids for role in member.roles)

@bot.event
async def on_ready():
    print(f"Bot prêt : {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    if lock_active and after.channel and after.channel.id == ID_SALON_VOCAL:
        print(f"🔍 [LOG] {member} a rejoint le vocal.")
        print(f"→ Rôles : {[role.name for role in member.roles]}")
        print(f"→ Est whitelisté ? {is_whitelisted(member)}")
        if not is_whitelisted(member):
            try:
                await member.move_to(None)
                print(f"✅ Expulsé : {member}")
            except Exception as e:
                print(f"❌ Erreur lors de l'expulsion de {member} : {e}")
        else:
            print(f"⏭️ Non expulsé (whitelist) : {member}")

@bot.command(name="lock")
async def lock(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = True
    save_lock_state()
    await reply_temp(ctx, "🔒 Salon vocal verrouillé.")

@bot.command(name="unlock")
async def unlock(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = False
    save_lock_state()
    await reply_temp(ctx, "🔓 Salon vocal déverrouillé.")

@bot.command(name="add")
async def add(ctx, membre: discord.Member):
    if not is_authorized(ctx):
        return
    whitelisted_user_ids.add(membre.id)
    save_list(USER_WL_FILE, whitelisted_user_ids)
    await reply_temp(ctx, f"✅ {membre.display_name} ajouté à la whitelist.")

@bot.command(name="rm")
async def rm(ctx, membre: discord.Member):
    if not is_authorized(ctx):
        return
    whitelisted_user_ids.discard(membre.id)
    save_list(USER_WL_FILE, whitelisted_user_ids)
    await reply_temp(ctx, f"❌ {membre.display_name} retiré de la whitelist.")

@bot.command(name="addrole")
async def addrole(ctx, role: discord.Role):
    if not is_authorized(ctx):
        return
    whitelisted_role_ids.add(role.id)
    save_list(ROLE_WL_FILE, whitelisted_role_ids)
    await reply_temp(ctx, f"✅ Rôle {role.name} ajouté à la whitelist.")

@bot.command(name="rmrole")
async def rmrole(ctx, role: discord.Role):
    if not is_authorized(ctx):
        return
    whitelisted_role_ids.discard(role.id)
    save_list(ROLE_WL_FILE, whitelisted_role_ids)
    await reply_temp(ctx, f"❌ Rôle {role.name} retiré de la whitelist.")

@bot.command(name="wl")
async def wl(ctx):
    if not is_authorized(ctx):
        return
    user_lines = []
    role_lines = []
    for uid in whitelisted_user_ids:
        member = ctx.guild.get_member(uid)
        if member:
            user_lines.append(f"- {member.name}#{member.discriminator}")
        else:
            user_lines.append(f"- ID: {uid}")
    for rid in whitelisted_role_ids:
        role = ctx.guild.get_role(rid)
        if role:
            role_lines.append(f"- @{role.name}")
        else:
            role_lines.append(f"- ID: {rid}")
    message = "**📋 Whitelist actuelle :**\n"
    message += "\n**Utilisateurs :**\n" + ("\n".join(user_lines) if user_lines else "Aucun.") + "\n"
    message += "\n**Rôles :**\n" + ("\n".join(role_lines) if role_lines else "Aucun.")
    await reply_temp(ctx, message, delay=10)

@bot.command(name="help")
async def help_cmd(ctx):
    if not is_authorized(ctx):
        return
    help_message = (
        "**🛠️ Commandes disponibles :**\n"
        "- `;lock` → active la surveillance\n"
        "- `;unlock` → désactive la surveillance\n"
        "- `;add @user` → ajoute un utilisateur\n"
        "- `;rm @user` → retire un utilisateur\n"
        "- `;addrole @role` → ajoute un rôle\n"
        "- `;rmrole @role` → retire un rôle\n"
        "- `;wl` → affiche la whitelist\n"
        "- `;help` → affiche cette aide"
    )
    await reply_temp(ctx, help_message, delay=10)

bot.run(os.getenv("DISCORD_TOKEN"))
