import discord
from discord.ext import commands
import json
import os
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=";", intents=intents, help_command=None)

ID_SALON_VOCAL = 1367268760486023300
AUTHORIZED_ADMINS = [670301667341631490, 1359569212531675167]
BLOCKED_ADMIN_ROLE_ID = 1365837084233039932

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
    return (
        member.id in whitelisted_user_ids or
        any(role.id in whitelisted_role_ids for role in member.roles) or
        member.id in AUTHORIZED_ADMINS
    )

@bot.event
async def on_ready():
    print(f"Bot prêt : {bot.user}")
@bot.event
async def on_voice_state_update(member, before, after):
    if lock_active and after.channel and after.channel.id == ID_SALON_VOCAL:
        print(f"🔍 {member} a rejoint le vocal.")
        print(f"→ Rôles : {[r.name for r in member.roles]}")
        print(f"→ Whitelisté ? {is_whitelisted(member)}")
        if not is_whitelisted(member):
            try:
                await member.move_to(None)
                print(f"✅ Expulsé : {member}")
            except Exception as e:
                print(f"❌ Échec expulsion : {e}")
        else:
            print(f"⏭️ Autorisé : {member}")

@bot.command(name="lock")
async def lock(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = True
    save_lock_state()
    await reply_temp(ctx, "🔒 Expulsion automatique activée.")

@bot.command(name="unlock")
async def unlock(ctx):
    global lock_active
    if not is_authorized(ctx):
        return
    lock_active = False
    save_lock_state()
    await reply_temp(ctx, "🔓 Expulsion automatique désactivée.")
@bot.command(name="add")
async def add(ctx, membre: discord.Member):
    if not is_authorized(ctx):
        return
    whitelisted_user_ids.add(membre.id)
    save_list(USER_WL_FILE, whitelisted_user_ids)
    await reply_temp(ctx, f"✅ {membre.display_name} ajouté à la whitelist.")

@bot.command(name="del")
async def delete(ctx, membre: discord.Member):
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

@bot.command(name="delrole")
async def delrole(ctx, role: discord.Role):
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
        user_lines.append(f"- {member.name}#{member.discriminator}" if member else f"- ID: {uid}")
    for rid in whitelisted_role_ids:
        role = ctx.guild.get_role(rid)
        role_lines.append(f"- @{role.name}" if role else f"- ID: {rid}")
    msg = "**📋 Whitelist :**\n"
    msg += "\n**Utilisateurs :**\n" + ("\n".join(user_lines) if user_lines else "Aucun.") + "\n"
    msg += "\n**Rôles :**\n" + ("\n".join(role_lines) if role_lines else "Aucun.")
    await reply_temp(ctx, msg, delay=10)
@bot.command(name="help")
async def help_cmd(ctx):
    if not is_authorized(ctx):
        return
    msg = (
        "**🛠️ Commandes :**\n"
        "- `;lock` / `;unlock` → activer/désactiver l'expulsion auto\n"
        "- `;add @user` / `;del @user` → gérer la whitelist utilisateurs\n"
        "- `;addrole @role` / `;delrole @role` → gérer la whitelist rôles\n"
        "- `;wl` → voir les whitelistés\n"
        "- `;locksalon` / `;unlocksalon` → verrouiller/déverrouiller le salon vocal\n"
        "- `;help` → afficher cette aide"
    )
    await reply_temp(ctx, msg, delay=10)
@bot.command(name="locksalon")
async def locksalon(ctx):
    if not is_authorized(ctx):
        return

    channel = bot.get_channel(ID_SALON_VOCAL)
    if not isinstance(channel, discord.VoiceChannel):
        await reply_temp(ctx, "❌ Salon introuvable.")
        return

    await channel.edit(sync_permissions=False, overwrites={})

    await channel.set_permissions(ctx.guild.default_role, overwrite=discord.PermissionOverwrite(connect=False))

    # Bloque explicitement le rôle admin (PA)
    role = ctx.guild.get_role(BLOCKED_ADMIN_ROLE_ID)
    if role:
        await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(connect=False))

    for uid in whitelisted_user_ids.union(set(AUTHORIZED_ADMINS)):
        member = ctx.guild.get_member(uid)
        if member:
            await channel.set_permissions(member, overwrite=discord.PermissionOverwrite(connect=True))

    for rid in whitelisted_role_ids:
        role = ctx.guild.get_role(rid)
        if role:
            await channel.set_permissions(role, overwrite=discord.PermissionOverwrite(connect=True))

    await reply_temp(ctx, "🔐 Salon verrouillé : accès uniquement whitelistés + admins autorisés.")

@bot.command(name="unlocksalon")
async def unlocksalon(ctx):
    if not is_authorized(ctx):
        return

    channel = bot.get_channel(ID_SALON_VOCAL)
    if not isinstance(channel, discord.VoiceChannel):
        await reply_temp(ctx, "❌ Salon introuvable.")
        return

    await channel.edit(overwrites={})
    await reply_temp(ctx, "🔓 Salon vocal déverrouillé.")
bot.run(os.getenv("DISCORD_TOKEN"))
