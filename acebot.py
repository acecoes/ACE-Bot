#!/usr/bin/env python3

import json
import requests
import yaml
import discord
import asyncio
import datetime
import urllib.request
from time import sleep, time
from random import randint
from discord.ext import tasks, commands

client = None

# TODO; inherit from the new Discord command system thing
class Bot(discord.Client):
	class GroupMeInfo(object):
		def __init__(self, **kwargs):
			self.id = kwargs.get("groupme", {}).get("bot_id", "")
			self.token = kwargs.get("groupme", {}).get("bot_token", "")
			self.groupid = kwargs.get("groupme", {}).get("bot_groupid", 0)
			self.sleeptime = kwargs.get("groupme", {}).get("sleep_time", 10.0)
			self.lastmsg = kwargs.get("groupme", {}).get("last_msg", 0)

			if self.token == "GROUPME_TOKEN" or self.token == "":
				print("WARNING: No GroupMe token specified. Relay will *not* work!")

		async def send_msg(self, **kwargs):
			author = kwargs.get("author", None)
			message = kwargs.get("message", None)
			attachments = kwargs.get("attachments", [])
			url = "https://api.groupme.com/v3/bots/post"

			msg = f"#officers\n{author}:"
			if message != None:
				msg = f"{msg} {message}"

			params = {}

			# SO
			# This actually is exactly how you're supposed to attach images
			# in groupme. Literally exactly.
			# But for some reason it doesn't fricking work, so
			# for now just append a link to images to the text
			for i in range(len(attachments)):
				atchurl = str(attachments[i])
				try:
					data = requests.get(atchurl).content
					atchurl = "https://image.groupme.com/pictures/"
					response = requests.post(url = atchurl, data = data, headers = {"X-Access-Token": self.token, "Content-Type": "application/octet-stream"})

					# Now try to force an exception to assert that this is a flawless download
					picture_url = response.json()["payload"]["url"]
					attachments[i] = {"type": "image", "url": picture_url}

					# FIXME; If/when attachments magically start to work, remove this
					msg += f"\n{picture_url}"
				except Exception as e:
					attachments[i] = None
					print(e)

			params = {
				"bot_id": self.id,
				"text": msg
			}

			params["attachments"] = [x for x in attachments if x != None]
			# print(params)
			requests.post(url, params = params)

		async def check_msgs(self):
			# GroupMe relay disabled
			if self.groupid == 0:
				return

			try:
				# print("check_msgs")
				params = {
					"token": self.token,
				}
				if self.lastmsg != 0:
					params["since_id"] = self.lastmsg

				msg = f"https://api.groupme.com/v3/groups/{self.groupid}/messages"

				data = requests.get(msg, params = params)
				if data.status_code != 200:
					return

				msgdata = data.json()["response"]
				# print(json.dumps(msgdata, indent = 4))

				if msgdata.get("count", 0) == 0:
					return

				messages = msgdata["messages"]

				# Reversed because iteration goes from newest message to oldest
				# which is not what we want
				for m in reversed(messages):
					if not m["user_id"].isnumeric() or m["user_id"] == 0:
						continue

					if m.get("sender_type", None) == "bot" or m.get("system", True):
						continue

					message = m.get("text", None)

					# Just use the first attachment, fix me later I guess
					attachments = m.get("attachments", [])
					for i in range(len(attachments)-1, -1, -1):
						atch = attachments[i]

						# No vids or anything else silly
						if atch.get("type", "") != "image":
							del attachments[i]
							continue

					attachmenturl = None
					if len(attachments):
						attachmenturl = attachments[0].get("url", None)

					# Empty message?
					if message == None and attachmenturl == None:
						continue

					author = m.get("name", None)
					if author == None:
						continue

					# print(message)
					avatar = m.get("avatar_url", None)
					# print(avatar)
					await client.discord.send_msg(author = author, message = message, avatar = avatar, attachmenturl = attachmenturl)

				# It'd be wiser to just dump on shutdown but
				# this is basically idiot proof
				self.lastmsg = int(messages[0]["id"])
				client.yaml["groupme"]["last_msg"] = self.lastmsg
				with open("acebot.yml", "w") as f:
					yaml.dump(client.yaml, f)
			except Exception as e:
				print(e)


	class DiscordInfo(object):
		class DiscordPresence(object):
			def __init__(self, **kwargs):
				self.presence = kwargs.get("presence", {}).get("presence", "The Cyberspace")
				self.gametype = kwargs.get("presence", {}).get("gametype", 3)
				self.url = kwargs.get("presence", {}).get("url", None)

		def __init__(self, **kwargs):
			self.token = kwargs.get("discord", {}).get("bot_token", "")
			self.office = kwargs.get("discord", {}).get("officer_channel", 0)
			self.presence = self.DiscordPresence(**kwargs.get("discord", {}))

		async def send_msg(self, **kwargs):
			author = kwargs.get("author", None)
			message = kwargs.get("message", None)
			avatar = kwargs.get("avatar", None)
			attachmenturl = kwargs.get("attachmenturl", None)

			channel = discord.utils.get(client.get_all_channels(), id = self.office)
			embed = discord.Embed(colour = discord.Colour(0x279eff), timestamp = datetime.datetime.utcfromtimestamp(time()))

			# Strange why I can't just pass None to it, w/e
			if message != None:
				embed.description = message

			embed.set_author(name = author, icon_url = avatar)
			if attachmenturl != None:
				embed.set_image(url = attachmenturl)

			await channel.send(embed = embed)

	def __init__(self, **kwargs):
		self.groupme = self.GroupMeInfo(**kwargs)
		self.discord = self.DiscordInfo(**kwargs)
		self.yaml = kwargs
		super().__init__()

with open("acebot.yml") as f:
	client = Bot(**yaml.safe_load(f))


# Task handler, checks for messages every x seconds
# A publicly facing webserver would probably be easier,
# but I am lazy
@tasks.loop(seconds = client.groupme.sleeptime)
async def check_msgs():
	await client.groupme.check_msgs()

@check_msgs.before_loop
async def before_check_msgs():
	await client.wait_until_ready()

@client.event
async def on_message(message):
	if message.author.bot:
		return

	if message.channel.id != client.discord.office:
		return

	if not message.content and len(message.attachments) == 0:
		return

	author = message.author.nick
	msg = message.content
	attachments = message.attachments
	await client.groupme.send_msg(author = author, message = msg, attachments = attachments)

@client.event
async def on_ready():
	print('------')
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	print('------')

	await client.change_presence(activity = discord.Activity(name = client.discord.presence.presence, type = client.discord.presence.gametype, url = client.discord.presence.url))
	check_msgs.start()

client.run(client.discord.token)