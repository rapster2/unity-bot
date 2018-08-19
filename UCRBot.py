import discord
import roblox
import asyncio
import json
import requests
import psycopg2
import logging
import sqlite3
import random
import datetime
import time
import math

logging.basicConfig(level=logging.INFO)

# Info #
channel_mutes = []
user_mutes = []
prefix = "!"
alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
eryn = "https://verify.eryn.io/api/user/"
group_id = 18
server_id = "286206768051257345"
url = 'https://script.google.com/macros/s/AKfycbxGTP1FVIglxwKbiyS5FDb8Ym-HEpcnj0KnjUG5f4EUV7DgNHQ/exec'
key = 'XaIVit9BukzU0nLDpzHg1YK4Qn5oIwm5GFrJjyuUn4jjZA8CJMK8BnwsGuoyJ2USrhhgjZFs8soy3Bd5e35yDFlnMncJT3Z1mwPXIFCKOj8YQHuN5tcmi9ZPjOWM57vHFhsSgDwerUmnXEXN3bsWsNHTESLJ4L6ynGDR2a3TnBfOtpSfOQ5eILCwmJcgAklkcMDiNxRo'
promo_bot_url = "http://ucr.herokuapp.com"
promo_bot_key = "9cHly11LQw4rCiVywORJhzYPNK2afdnKiuOSy9QOvNLt1Mf882t3IePB67PoLYzf"
max_awardable_unity = 5
discord_unity_reward = 5
shout_channel_id = "286207895341760513"
logs_channel_id = "286207965747347457"
cooldown_length = 5 # Length in seconds between commands by the same user

replaceable_roles = {
	"[H3] Vice President": "Vice President",
	"[H2] Cabinet": "Cabinet",
	"[H1] Senator": "Senator",
	"[X] Honorary": "Honorary",
	"[M] Operator": "Operator",
	"7013": "RAT",
	"14638": "RSF",
	"72321": "FEAR",
	"287660": "The Black Shield",
	"420935": "The Fall Force",
	"2654474": "IA",
	"18": "UCR"
}

unity_for_rank = {
	"25": "[L2] Intermediate",
	"50": "[L3] Advanced",
	"75": "[L4] Vanguard",
	"110": "[L5] Specialist",
	"150": "[L6] Warrior",
	"250": "[L7] Unifier",
	"500": "[L8] Excelsior"
}

insults = []

with open("insults.txt", "r") as file:
	insults = file.readlines()

# Client #
client = discord.Client()

# Database #
conn = sqlite3.connect("UCRBotDatabase.db")
db = conn.cursor()

# ROBLOX Session #
roblox_session = roblox.RobloxSession(username="Huffst", password="shadow")
ucr = roblox_session.get_group(group_id)

# Fun Phrases #
phrases = {
	"o7": "o7"
}

# Utility Functions #
async def msg(channel, message, embed=None):
	'''
	Wrapper for sending messages.
	'''
	return await client.send_message(channel, message, embed=embed)

async def edit(message, newinfo=None, embed=None):
	'''
	Wrapper for editing messages.
	'''
	return await client.edit_message(message, new_content=newinfo, embed=embed)

async def delete(message):
	'''
	Wrapper for deleting messages.
	'''
	await client.delete_message(message)

async def get(url, params=None):
	'''
	Wrapper for sending generic GET requests.
	'''
	ret = requests.get(url, params=params)
	print(ret.text)
	return json.loads(ret.text)

async def is_int(string):
	'''
	Tests if a string can be converted to an int.
	'''
	try:
		int(string)
		return True
	except ValueError:
		return False

async def query(msg, args):
	'''
	Wrapper for executing SQL queries.
	'''
	return db.execute(msg, args).fetchone()

async def make_embed(title=None, desc=None):
	'''
	Creates a generic embed object in the style I want.
	'''
	embed = discord.Embed(colour=discord.Colour(65535), timestamp=datetime.datetime.utcnow(), description=desc, title=title)
	embed.set_footer(text="Unity Bot by FractalGeometry", icon_url="https://i.imgur.com/0yqiRqY.png")
	return embed

async def get_unity(action, userid):
	'''
	Gets a user's unity from the Unity spreadsheet.
	'''
	data = {
		'key': key, 
		'package': json.dumps({
			'action': action, 
			'userId': userid
		})
	}
	ret = requests.get(url, params=data).text
	print(ret)
	return json.loads(ret)

async def post_unity(action, username, userId, sender, senderId, unity, discord):
	'''
	Sends a post request to the Unity spreadsheet, used mainly to increment a
	user's unity.
	'''
	data = {
		'key': key,
		'package': json.dumps({
			'action': action,
			'username': username,
			'userId': int(userId),
			'sender': sender,
			'senderId': senderId,
			'unity': int(unity),
			'discord': discord,
			'placeName': "Discord Server",
			'timestamp': "{:%m/%d/%Y %I:%M %p UTC}".format(datetime.datetime.utcnow())
		})
	}
	ret = requests.post(url, data=data).text
	print(ret)
	return json.loads(ret)

# Helper Functions #
async def promote_user(user):
	'''
	Promotes a user in UCR
	'''
	roles = ucr.roles
	user_role = ucr.role_of(user)
	new_role = None
	for i in range(len(roles)):
		if roles[i] == user_role and i != len(roles):
			new_role = roles[i+1]
			break
	if new_role != None:
		ret = roblox_session.set_rank(group_id, user.id, new_role.roleset_id)
		return (ret, new_role.name)
	else:
		return False

async def demote_user(user):
	'''
	Demotes a user in UCR
	'''
	roles = ucr.roles
	user_role = ucr.role_of(user)
	new_role = None
	for i in range(len(roles)):
		if roles[i] == user_role and i != 0:
			new_role = roles[i-1]
			break
	if new_role != None:
		ret = roblox_session.set_rank(group_id, user.id, new_role.roleset_id)
		return (ret, new_role.name)
	else:
		return False

async def set_rank(user, rank):
	'''
	Sets a user's rank to the given rank
	'''
	new_role = None
	roles = ucr.roles
	for role in roles:
		if role.name == rank:
			new_role = role
			break
	if new_role != None:
		ret = roblox_session.set_rank(group_id, user.id, new_role.roleset_id)
		return ret
	else:
		return False

async def is_verified(discord_id):
	'''
	Tests to see if the user's Discord account is linked to their ROBLOX account
	in our database.
	'''
	count, verified = await query("SELECT count(*),verified FROM discord WHERE id=?", (discord_id,))
	if count == 0 or verified == 0:
		return (False, count != 0)
	return (True, True)

async def get_permission(discord_id):
	'''
	Gets a Discord member's permission level.
	'''

	# Bot has highest permission
	if discord_id == client.user.id:
		return 3

	# If the user is verified, return their permission
	verified, created = await is_verified(discord_id)
	if verified:
		attempt = await query("SELECT permission FROM discord WHERE id=?", (discord_id,))
		return attempt[0]

	# If they are not verified, don't let them do anything.
	else:
		return -1

async def log_unity(sender, target, unity, new_unity):
	'''
	Logs unity transactions
	'''
	embed = await make_embed()
	logging_channel = client.get_channel(logs_channel_id)
	embed.set_author(name="UNITY LOG", icon_url="https://i.imgur.com/0yqiRqY.png")
	embed.add_field(name="ACTION", value=sender + (" gave " if unity >= 0 else " removed ") + str(unity) + " unity " + ("to " if unity >= 0 else "from ") + target, inline=False)
	embed.add_field(name="NEW TOTAL", value=str(new_unity), inline=False)
	await msg(logging_channel, "", embed=embed)

async def remove_replaceable_roles(user):
	'''
	Removes all the replaceable roles from a Discord member.
	'''
	roles_to_remove = [user]

	# Gather all replaceable roles and remove them
	for role in user.roles:
		if role.name in replaceable_roles:
			roles_to_remove.append(role)
	await client.remove_roles(*roles_to_remove)

async def get_groups(user):
	'''
	Returns a list of groups a user is in on ROBLOX.
	'''
	groups = []
	for group in user.groups():
		groups.append(group)
	return groups

async def match_names_to_roles(names):
	'''
	Returns a list of roles based on their names.
	'''
	roles = []
	server_roles = client.get_server(server_id).roles
	for role in server_roles:
		if role.name in names:
			roles.append(role)
	return roles

async def get_roles_from_groups(user):
	'''
	Returns a list of roles based on what groups the user is in and what rank
	they are in UCR.
	'''
	groups = await get_groups(user)
	roles = []

	# Iterate group a users groups and match to UCR and her allies
	for group in groups:
		if str(group.id) in replaceable_roles:
			roles.append(replaceable_roles[str(group.id)])

		# If the user is in UCR, see if their rank comes with a role
		if group.id == group_id:
			rank = group.role_of(user=user).name
			if rank in replaceable_roles:
				roles.append(replaceable_roles[rank])

	roles = await match_names_to_roles(roles)
	return roles

async def get_past_usernames(user_id):
	'''
	Gets a list of all of a user's past usernames
	'''
	text = requests.get('https://www.roblox.com/users/%d/profile' % user_id).text
	location = text.find("ProfileHeaderData=")
	begin = location + 18
	end = text.find("}", begin)
	table = json.loads(text[begin:end+1])
	return table["previoususernames"]

async def update_user(user, message):
	'''
	Updates a user's roles in the Discord as well as their username in the SQL
	database.
	'''
	if (await is_verified(user.id))[0]:
		await remove_replaceable_roles(user)

		# Update their username in our database
		roblox_id = (await query("SELECT roblox FROM discord WHERE id=?", (user.id,)))[0]
		roblox_user = roblox_session.get_user(user_id=roblox_id)
		await query("UPDATE discord SET username=? WHERE id=?", (roblox_user.username, user.id,))
		conn.commit()

		# Assign them the proper discord roles
		roles = await get_roles_from_groups(roblox_user)
		roles.insert(0, user)
		await client.add_roles(*roles)
		await msg(message.channel, user.mention + ", updated.")
	else:
		await msg(message.channel, user.mention + ", you are not verified.")

async def get_user_unity(user):
	'''
	Returns a user's unity, a bool representing if they have recieved their
	Discord unity, and their roblox user.
	'''
	roblox_id, discord_unity = await query("SELECT roblox,unity FROM discord WHERE id=?", (user.id,))
	roblox_user = roblox_session.get_user(user_id=roblox_id)
	info = await get_unity("single", roblox_id)
	if info["result"] == True:
		return (info["unity"], discord_unity == 1, roblox_user)
	else:
		return (-1, None, None)

async def match_unity_to_rank(unity):
	'''
	Matches unity to the highest rank it can represent
	'''
	highest = None
	for amt in unity_for_rank:
		if int(amt) <= unity:
			highest = unity_for_rank[amt]
	return highest

async def getunity_helper(user, sent, embed, message):
	'''
	Helper function for getting a user's unity.
	'''
	if (await is_verified(user.id))[0]:
		unity, discord_unity, roblox_user = await get_user_unity(user)
		if unity > 0:
			embed.set_author(name=roblox_user.username, icon_url="https://www.roblox.com/bust-thumbnail/image?userId=" + str(roblox_user.id) + "&width=420&height=420&format=png")
			embed.set_thumbnail(url=user.avatar_url)
			embed.add_field(name="Unity", value=str(unity), inline=True)
			embed.add_field(name="Received Discord Unity", value=("Yes" if discord_unity == 1 else "No"), inline=True)
			await edit(sent, newinfo=message.author.mention, embed=embed)
		else:
			await edit(sent, newinfo="Error retrieving unity info for " + user.mention)
	else:
		await edit(sent, newinfo=user.mention + ", please verify.")

async def giveunity_helper(user, sent, embed, unity, message):
	'''
	Helper function for giving a user unity.
	'''
	if (await is_verified(user.id))[0]:
		sender, senderId = await query("SELECT username,roblox FROM discord WHERE id=?", (message.author.id,))
		target, targetId = await query("SELECT username,roblox FROM discord WHERE id=?", (user.id,))
		info = await post_unity("increment", target, targetId, sender, senderId, unity, False)
		if info['result'] == True:
			await log_unity(sender, target, int(unity), info['unity'])
			embed.set_author(name="Unity Change")
			embed.set_thumbnail(url="https://imgur.com/MDvzGUL.png")
			embed.add_field(name="Admin", value=sender, inline=True)
			embed.add_field(name="Receiver", value=target, inline=True)
			embed.add_field(name="Unity", value=str(unity))
			roblox_user = roblox_session.get_user(user_id=targetId)
			new_rank = await match_unity_to_rank(info['unity'])
			old_rank = ucr.role_of(roblox_user).name
			if old_rank[:2] == "[L" and new_rank is not None and new_rank != ucr.role_of(roblox_user).name:
				info2 = await set_rank(roblox_user, new_rank)
				if info2 is not False and info2['success'] == True:
					await msg(message.channel, user.mention + " had their rank changed to " + new_rank + "!")
				else:
					await msg(message.channel, user.mention + " had an error occur when attempting to promote them.")
			await edit(sent, newinfo=message.author.mention, embed=embed)
		else:
			await edit(sent, newinfo="Error giving unity info to " + user.mention)
	else:
		await edit(sent, newinfo=user.mention + ", please verify.")

async def check_cooldown(discord_id):
	'''
	Returns either how much time is left on command cooldown or True if cooldown is passed
	'''
	last = (await query("SELECT cooldown FROM discord WHERE id=?", (discord_id,)))[0]
	now = time.time()
	if (now - last >= cooldown_length):
		return True
	else:
		return now - last

# Commands #
async def ping(message):
	'''
	A test command to see if the bot is working.
	'''
	await msg(message.channel, "Pong!")

async def verify(message):
	'''
	Uses the eryn.io verification system (RoVer) to link a user's Discord
	account to their ROBLOX account in a SQL database.
	'''
	args = message.content.split(' ')

	# Check to make sure command is formatted properly
	if len(args) == 1:

		# Make sure user is not already verified
		verified, created = await is_verified(message.author.id)
		print(verified)
		print(created)

		# User is not verified with me
		if not verified:
			attempt = await get(eryn + message.author.id, None)

			print(attempt)

			# User is verified with eryn but not me yet
			if attempt['status'] == "ok":
				if not created:
					await query("INSERT INTO discord (id, roblox, username, permission, verified) VALUES (?,?,?,?,?)", (message.author.id, attempt["robloxId"], attempt["robloxUsername"], 1, True,))
				else:
					await query("UPDATE discord SET roblox=?,username=?,permission=?,verified=? WHERE id=?", (attempt["robloxId"], attempt["robloxUsername"], 1, True, message.author.id,))
				conn.commit()
				# TODO: fancy message
				await msg(message.channel, message.author.mention + " verified.")

			# User is not verified with eryn or me
			else:
				await query("INSERT INTO discord (id,verified) VALUES (?,?)", (message.author.id, False,))
				conn.commit()
				await msg(message.channel, message.author.mention + ", you are not yet verified. Please verify at this link: https://verify.eryn.io/\nOnce you have verified using that link, please re-run the verify command.")

		# User is already verified, no need to re-verify
		else:
			await msg(message.channel, message.author.mention + ", you are already verified.")

	# Command is not correct
	else:
		await msg(message.channel, message.author.mention + ", usage: " + prefix + "verify")

async def update(message):
	'''
	Updates a user's information, including roles and username.
	'''
	args = message.content.split(' ')

	# If no mention, update the message sender
	if len(args) == 1:
		user = message.author

		# If the user is verified, update their stored username and roles
		await update_user(user, message)

	# If one or more mentions is present, update those users
	else:
		mentions = message.mentions
		if len(mentions) > 0:
			for user in mentions:
				await update_user(user, message)
		else:
			await msg(message.channel, message.author.mention + ", incorrect usage. Usage: " + prefix + "update [mention, mention, ...]")

async def kick(message):
	'''
	Kicks a member from the Discord server.
	'''
	mentions = message.mentions
	string = ""
	if len(mentions) > 0:
		for user in mentions:
			name = user.mention
			try:
				await client.kick(user)
				string = string + name + " was kicked from the server.\n"
			except discord.Forbidden:
				await msg(message.channel, "This bot has insufficient permissions to kick " + user)
		await msg(message.channel, string)
	else:
		await msg(message.channel, message.author.mention + ", you must provide members to kick.")

async def ban(message):
	'''
	Bans a member from the Discord server.
	'''
	mentions = message.mentions
	string = ""
	if len(mentions) > 0:
		for user in mentions:
			name = user.mention
			try:
				await client.ban(user, 7)
				string = string + name + " was banned from the server.\n"
			except discord.Forbidden:
				await msg(message.channel, "This bot has insufficient permissions to ban " + user)
		await msg(message.channel, string)
	else:
		await msg(message.channel, message.author.mention + ", you must provide members to ban.")

async def getunity(message):
	'''
	Retreives a user or users unity and displays it.
	'''
	mentions = message.mentions
	sent = await msg(message.channel, "Querying the unity database...")
	embed = await make_embed()

	# If no mentions, get the author's unity.
	if len(mentions) == 0:
		user = message.author
		await getunity_helper(user, sent, embed, message)

	# If one mention, display similar to above
	elif len(mentions) == 1:
		user = mentions[0]
		await getunity_helper(user, sent, embed, message)

	# Multiple mentions, gotta do something special
	else:
		for user in mentions:
			if (await is_verified(user.id))[0]:
				unity, discord_unity, roblox_user = await get_user_unity(user)
				string = ""
				if unity > 0:
					string = "Unity: " + str(unity) + ", " + ("has recieved their 5 Discord unity." if discord_unity else "has not recieved their 5 Discord unity.")
				else:
					string = "Error retrieving unity information."
				embed.add_field(name=roblox_user.username, value=string)
			else:
				embed.add_field(name=roblox_user.username, value="Not verified.")
		await edit(sent, newinfo=message.author.mention, embed=embed)

async def giveunity(message):
	'''
	Gives a user or users unity.
	'''
	args = message.content.split(' ')
	mentions = message.mentions
	sent = await msg(message.channel, "Processing request...")
	embed = await make_embed()

	# Make sure command is formatted properly for one person
	if len(mentions) == 1 and len(args) == len(mentions) + 2 and await is_int(args[len(args) - 1]):
		await giveunity_helper(mentions[0], sent, embed, args[len(args) - 1], message)

	# Make sure command is formatted properly for multiple people
	elif len(mentions) > 1 and len(mentions) <= 10 and len(args) == len(mentions) + 2 and await is_int(args[len(args) - 1]):
		embed.set_author(name="Unity Change")
		embed.set_thumbnail(url="https://imgur.com/MDvzGUL.png")
		sender, senderId = await query("SELECT username,roblox FROM discord WHERE id=?", (message.author.id,))
		unity = args[len(args) - 1]
		for user in mentions:
			if (await is_verified(user.id))[0]:
				target, targetId = await query("SELECT username,roblox FROM discord WHERE id=?", (user.id,))
				info = await post_unity("increment", target, targetId, sender, senderId, unity, False)
				if info['result'] == True:
					await log_unity(sender, target, int(unity), info['unity'])
					embed.add_field(name=target, value=sender + " gave " + target + " " + unity + " unity.")
					roblox_user = roblox_session.get_user(user_id=targetId)
					new_rank = await match_unity_to_rank(info['unity'])
					old_rank = ucr.role_of(roblox_user).name
					if old_rank[:2] == "[L" and new_rank is not None and new_rank != ucr.role_of(roblox_user).name:
						info2 = await set_rank(roblox_user, new_rank)
						if info2 is not False and info2['success'] == True:
							await msg(message.channel, user.mention + " had their rank changed to " + new_rank + "!")
						else:
							await msg(message.channel, user.mention + " had an error occur when attempting to promote them.")
				else:
					embed.add_field(name=target, value="Error giving unity to " + target)
			else:
				embed.add_field(name=target, value="User not verified.")
		await edit(sent, newinfo=message.author.mention, embed=embed)

	else:
		await msg(message.channel, message.author.mention + ", improper format. Usage: " + prefix + "giveunity <@mention> [@mention ...] <unity>")

async def mute(message):
	'''
	Mutes a member or channel in the Discord server.
	'''
	mentions = message.mentions
	string = ""

	if len(mentions) > 0:
		for user in mentions:
			if user.id not in user_mutes:
				user_mutes.append(user.id)
				string = string + "Muted " + user.mention + "\n"
	else:
		if message.channel.id not in channel_mutes:
			channel_mutes.append(message.channel.id)
			string = "Muted " + message.channel.mention

	await msg(message.channel, string)

async def unmute(message):
	'''
	Unmutes a member or channel in the Discord server.
	'''
	mentions = message.mentions
	string = ""

	if len(mentions) > 0:
		for user in mentions:
			if user.id in user_mutes:
				user_mutes.remove(user.id)
				string = string + "Unmuted " + user.mention + "\n"
	else:
		if message.channel.id in channel_mutes:
			channel_mutes.remove(message.channel.id)
			string = "Unmuted " + message.channel.mention

	await msg(message.channel, string)

async def join_unity(message):
	'''
	Gives a member unity for joining the Discord if they have not already been
	awarded that unity.
	'''
	args = message.content.split(' ')
	sent = await msg(message.channel, "Working...")

	# Should only have !unity as the command
	if len(args) == 1:
		if (await is_verified(message.author.id))[0]:

			# Check to see if they have already received their join unity
			has_unity, target, targetId = await query("SELECT unity,username,roblox FROM discord WHERE id=?", (message.author.id,))
			if not has_unity:

				# Give them join unity
				info = await post_unity("increment", target, targetId, "Discord", "Discord", discord_unity_reward, True)
				if info["result"] == True:
					await query("UPDATE discord SET unity=? WHERE id=?", (True, message.author.id,))
					conn.commit()
					await edit(sent, message.author.mention + ", you have been awarded " + str(discord_unity_reward) + " unity for joining the Discord!")
				else:
					await edit(sent, message.author.mention + ", an error has occurred while trying to award unity.")
			else:
				await edit(sent, message.author.mention + ", you have already recieved your unity for joining the Discord.")
	else:
		await edit(sent, message.author.mention + ", incorrect usage. Usage: " + prefix + "unity")

async def setpermission(message):
	'''
	Sets a user's permission level for the bot.
	'''
	mentions = message.mentions
	args = message.content.split(' ')

	# Make sure only 1 person and that a valid integer was given for permission level
	if len(mentions) == 1 and len(args) == 3 and await is_int(args[2]):
		user = mentions[0]
		old_permission = await get_permission(user.id)
		my_permission = await get_permission(message.author.id)
		permission = int(args[2])

		# Target must be verified, and you can't change permissions of someone above you or
		# to a level above you
		if (await is_verified(user.id))[0] and my_permission >= old_permission and my_permission >= permission:
			await query("UPDATE discord SET permission=? WHERE id=?", (permission, user.id,))
			conn.commit()
			await msg(message.channel, message.author.mention + " set " + user.mention + "'s permission level to " + str(permission))
		else:
			await msg(message.channel, user.mention + " is not verified or " + message.author.mention + " does not have a high enough permission level.")
	else:
		await msg(message.channel, message.author.mention + ", incorrect usage. Usage: " + prefix + "setpermission <@mention> <permission>")

async def getpermission(message):
	'''
	Displays a user's permission level.
	'''
	mentions = message.mentions

	if len(mentions) == 1:
		permission = await get_permission(mentions[0].id)
		await msg(message.channel, mentions[0].mention + " is a level " + str(permission) + " member.")
	else:
		await msg(message.channel, message.author.mention + ", incorrect usage. Usage: " + prefix + "getpermission <@mention>")

async def profile(message):
	'''
	Displays a profile of the member, including information found on their
	ROBLOX profile, their rank in the main group, and their unity.
	'''
	mentions = message.mentions
	embed = await make_embed()
	sent = await msg(message.channel, "Working...")

	# Can only show 1 profile at a time, either author's or one mention
	if len(mentions) <= 1:
		user = message.author if len(mentions) == 0 else mentions[0]
		if (await is_verified(user.id))[0]:
			unity, has_discord, roblox_user = await get_user_unity(user)
			usernames = await get_past_usernames(roblox_user.id)
			usernames = usernames.replace("\r\n", ", ")
			embed.set_thumbnail(url="https://www.roblox.com/bust-thumbnail/image?userId=%d&width=420&height=420&format=png" % roblox_user.id)
			embed.set_author(name=roblox_user.username, url="https://www.roblox.com/users/%d/profile" % roblox_user.id, icon_url="https://www.roblox.com/headshot-thumbnail/image?userId=%d&width=420&height=420&format=png" % roblox_user.id)
			embed.add_field(name="Primary Group", value="[%s](https://www.roblox.com/groups/group.aspx?gid=%d)" % (roblox_user.primary_group.name, roblox_user.primary_group.id), inline=True)
			embed.add_field(name="Rank in UCR", value=ucr.role_of(roblox_user).name, inline=True)
			embed.add_field(name="Unity", value=str(unity), inline=True)
			embed.add_field(name="Recieved Discord Unity", value=("Yes" if has_discord == 1 else "No"), inline=True)
			embed.add_field(name="Join Date", value=datetime.datetime.strftime(roblox_user.join_date, "%B %d, %Y"), inline=True)
			embed.add_field(name="Past Usernames", value=(usernames if usernames != "" else "None"), inline=True)
			await edit(sent, newinfo=message.author.mention, embed=embed)
		else:
			await edit(sent, newinfo=user.mention + " is not verified.")
	else:
		await edit(sent, newinfo=message.author.mention + ", please specify at most 1 person.")

async def promote(message):
	'''
	Promotes a user in UCR
	'''
	mentions = message.mentions
	sent = await msg(message.channel, "Working...")

	# Can only promote 1 person at a time
	if len(mentions) == 1:
		user = mentions[0]
		if (await is_verified(user.id))[0]:
			roblox_id = (await query("SELECT roblox FROM discord WHERE id=?", (user.id,)))[0]
			roblox_user = roblox_session.get_user(user_id=roblox_id)

			# Only allow Low ranks to be promoted
			if ucr.role_of(roblox_user).name[:2] == "[L":
				info, new_rank = await promote_user(roblox_user)
				if (info is not False) and (info['success'] == True):
					await edit(sent, newinfo=message.author.mention + " promoted " + user.mention + " to " + new_rank)
				else:
					await edit(sent, newinfo=message.author.mention + ", an error occurred.")
			else:
				await edit(sent, newinfo=message.author.mention + ", cannot promote a non-LR.")
		else:
			await edit(sent, newinfo=user.mention + " is not verified.")
	else:
		await edit(sent, newinfo=message.author.mention + ", incorrect usage. Usage: " + prefix + "promote @mention")

async def demote(message):
	'''
	Demotes a user in UCR
	'''
	mentions = message.mentions
	sent = await msg(message.channel, "Working...")

	# Only allow 1 person to be demoted at a time
	if len(mentions) == 1:
		user = mentions[0]
		if (await is_verified(user.id))[0]:
			roblox_id = (await query("SELECT roblox FROM discord WHERE id=?", (user.id,)))[0]
			roblox_user = roblox_session.get_user(user_id=roblox_id)

			# Make sure the person is at a rank below Automation
			if ucr.role_of(roblox_user).name[:2] == "[L" or ucr.role_of(roblox_user).name[:2] == "[X" or ucr.role_of(roblox_user).name[:2] == "[M":
				info, new_rank = await demote_user(roblox_user)
				if (info is not False) and (info['success'] == True):
					await edit(sent, newinfo=message.author.mention + " demoted " + user.mention + " to " + new_rank)
				else:
					await edit(sent, newinfo=message.author.mention + ", an error occurred.")
			else:
				await edit(sent, newinfo=message.author.mention + ", cannot demote user.")
		else:
			await edit(sent, newinfo=user.mention + " is not verified.")
	else:
		await edit(sent, newinfo=message.author.mention + ", incorrect usage. Usage: " + prefix + "demote @mention")

async def cmds(message):
	'''
	Displays a list of all the commands.
	'''
	embed = await make_embed()
	embed.set_author(name="Commands List")
	for command in commands:
		embed.add_field(name=prefix + command + " | Level " + str(commands[command][1]), value=commands[command][2], inline=False)
	await msg(message.channel, message.author.mention, embed=embed)

async def oriion(message):
	'''
	Displays a link to ORIION
	'''
	await msg(message.channel, message.author.mention + ", ORIION can be found here: https://www.roblox.com/games/257784240/UCR-Fort-ORIION")

async def luo(message):
	'''
	Displays a link to Luo
	'''
	await msg(message.channel, message.author.mention + ", Luo can be found here: https://www.roblox.com/games/367414516/UCR-Training-Facility-Luo")

async def bomber(message):
	'''
	Displays a link to Bomber
	'''
	await msg(message.channel, message.author.mention + ", Bomber can be found here: https://www.roblox.com/games/1243590921/UCR-Rally-Center-Bomber")

async def initiation(message):
	'''
	Displays a link to Bomber
	'''
	await msg(message.channel, message.author.mention + ", The initiation course can be found here: https://www.roblox.com/games/269789846/UCR-Initiation-Course")

async def shout(message):
	'''
	Shouts a message to the shouting channel as well as the UCR group page.
	'''
	args = message.content.split(' ')
	string = ' '.join(args[1:])
	shout_channel = client.get_channel(shout_channel_id)
	embed = await make_embed()
	roblox_id = (await query("SELECT roblox FROM discord WHERE id=?", (message.author.id,)))[0]
	roblox_user = roblox_session.get_user(user_id=roblox_id)
	embed.set_author(name=roblox_user.username, url="https://www.roblox.com/users/%d/profile" % roblox_user.id, icon_url="https://www.roblox.com/headshot-thumbnail/image?userId=%d&width=420&height=420&format=png" % roblox_user.id)
	embed.add_field(name="There is a new shout!", value=string)
	ucr.post_shout(string + " - shouted by " + roblox_user.username)
	await msg(shout_channel, "@here", embed=embed)

async def clear_shout(message):
	'''
	Clears the current UCR shout.
	'''
	shout_channel = client.get_channel(shout_channel_id)
	roblox_id = (await query("SELECT roblox FROM discord WHERE id=?", (message.author.id,)))[0]
	roblox_user = roblox_session.get_user(user_id=roblox_id)
	ucr.post_shout("")
	await msg(shout_channel, roblox_user.username + " has cleared the shout.")

async def insult(message):
	'''
	Replies with a random insult from a list of insults specified in insults.txt
	'''
	mentions = message.mentions
	if len(mentions) <= 1:
		user = message.author if len(mentions) == 0 else mentions[0]
		insult_text = insults[random.randrange(0, len(insults))]
		await msg(message.channel, user.mention + ", " + insult_text)
	else:
		await msg(message.channel, message.author.mention + ", you can only insult one person at a time you stupid idiot!")

async def rank(message):
	'''
	Displays the person's rank in UCR.
	'''
	mentions = message.mentions
	if len(mentions) <= 1:
		user = message.author if len(mentions) == 0 else mentions[0]
		if (await is_verified(user.id))[0]:
			roblox_id = (await query("SELECT roblox FROM discord WHERE id=?", (user.id,)))[0]
			roblox_user = roblox_session.get_user(user_id=roblox_id)
			rank = ucr.role_of(roblox_user).name
			await msg(message.channel, user.mention + " is a " + rank + " in UCR.")
		else:
			await msg(message.channel, user.mention + " is not verified.")
	else:
		await msg(message.channel, message.author.mention + ", only do one at a time please.")

async def char(message):
	'''
	Displays the person's ROBLOX character.
	'''
	mentions = message.mentions
	embed = await make_embed()
	if len(mentions) <= 1:
		user = message.author if len(mentions) == 0 else mentions[0]
		if (await is_verified(user.id))[0]:
			roblox_id = (await query("SELECT roblox FROM discord WHERE id=?", (user.id,)))[0]
			embed.set_image(url="https://www.roblox.com/Thumbs/Avatar.ashx?x=420&y=420&userId=%d" % roblox_id)
			await msg(message.channel, user.mention, embed=embed)
		else:
			await msg(message.channel, user.mention + " is not verified.")
	else:
		await msg(message.channel, message.author.mention + ", only do one at a time please.")

# Commands List #
# Format: CommandName = [function, permission, description]
commands = {
	"ping": [ping, 1, "Pong!"],
	"verify": [verify, -1, "Connect your ROBLOX account with this bot. Usage: !verify"],
	"update": [update, 1, "Update your roles in the Discord. Usage: !update [@user]"],
	"kick": [kick, 2, "Kicks a user or users(s) from the discord. Usage: !kick @user [@user ...]"],
	"ban": [ban, 3, "Bans a user or users(s) from the discord. Usage: !ban @user [@user ...]"],
	"getunity": [getunity, 1, "Displays a user(s)'s unity. Usage: !getunity [@mention ...]"],
	"giveunity": [giveunity, 2, "Gives a user(s) unity. " + str(max_awardable_unity) + " is the maximum amount of unity that can be awarded. Usage: !giveunity <@mention> [@mention ...]"],
	"mute": [mute, 2, "Mutes a channel or user(s). Usage: !mute [@mention ...]"],
	"unmute": [unmute, 2, "Unmutes a channel or user(s). Usage: !unmute [@mention ...]"],
	"unity": [join_unity, 1, "Verified users can recieve 5 unity just for joining the discord! Usage: !unity"],
	"setpermission": [setpermission, 3, "Sets a user's permissions. Usage: !setpermission @mention permission"],
	"getpermission": [getpermission, 3, "Gets a user's permissions. Usage: !getpermission <@mention>"],
	"profile": [profile, 1, "Displays a multitude of information about a user."],
	"promote": [promote, 3, "Promotes a user in UCR. Usage: !promote @mention"],
	"demote": [demote, 3, "Demotes a user in UCR. Usage: !demote @mention"],
	"cmds": [cmds, 1, "Displays a list of commands for this Bot. Usage: !cmds"],
	"oriion": [oriion, 1, "Get a link to UCR's Fort ORIION."],
	"luo": [luo, 1, "Get a link to UCR's Training Facility Luo."],
	"bomber": [bomber, 1, "Get a link to UCR's Rally Center Bomber."],
	"initiation": [initiation, 1, "Get a link to UCR's Initiation Course."],
	"shout": [shout, 2, "Shouts a message to the UCR group page. Usage: !shout message"],
	"clearshout": [clear_shout, 2, "Clears the UCR shout."],
	"insult": [insult, 1, "Insult a fellow member or even yourself!"],
	"rank": [rank, 1, "Gets a person's rank in UCR. Usage: !rank [@mention]"],
	"char": [char, 1, "Shows a person's ROBLOX character. Usage: !char [@mention]"]
}

# Handler #	
@client.event
async def on_ready():
	'''
	Print something to let us know the bot is ready.
	'''
	print("Logged in as " + client.user.name)
	print("---------------------")

@client.event
async def on_message(message):
	'''
	Handle a message in the Discord. If the user or channel is muted and they
	are not a level 3 member, delete the message and ignore. Otherwise checks if
	the message begins with the command prefix and attempts to execute the
	command.
	'''
	# First, check mutes
	if (message.channel.id in channel_mutes) or (message.author.id in user_mutes):

		# Delete messages from those with permission level under 3
		if await get_permission(message.author.id) < 3:
			await delete(message)
			return
	
	# Next, check for command if message is from anyone except the client
	if message.author != client.user:
		if message.content.startswith(prefix):
			command = message.content.split(' ', 1)[0]
			command_info = None

			# Check to see if command exists
			try:
				command_info = commands[command[len(prefix):]]
			except KeyError:
				pass

			# If command exists, execute command based on permission
			if command_info is not None:
				if await get_permission(message.author.id) >= command_info[1]:

					# Check cooldown, if time has passed then execute command.
					check = await check_cooldown(message.author.id)
					if check == True:
						await query("UPDATE discord SET cooldown=? WHERE id=?", (time.time(), message.author.id,))
						conn.commit()
						await command_info[0](message)
					else:
						await msg(message.channel, message.author.mention + ", slow down! Try again in " + str(math.floor(cooldown_length - check)) + " seconds.")
				else:
					await msg(message.channel, message.author.mention + ", insufficient permissions. If you are not verified, please verify.")

		# If no command, check for key phrases
		else:
			for phrase in phrases:
				if message.content.find(phrase) >= 0:
					check = await check_cooldown(message.author.id)
					if check == True:
						await msg(message.channel, phrases[phrase])
						return

client.run("MzA0NDExNjQ0MzU5MDgxOTg4.DQfckQ.9dqTxcwfg0U7zZbVkmMmKmIm9v4")
client.close()