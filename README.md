# ACE-Bot #

Discord Bot for ACE

Written by John Mascagni

### Purpose ###

This is the script for the ACE Discord bot. It's main purpose (for now) is to relay messages from #officers channel in the Discord to the officer GroupMe.

If you need a machine to host the bot, you can use something simple like Linode or Vultr. I don't think Tech allows you to use their VM's for perpetual use. You could also use a RaspPi and stick it in the corner of your dorm or something.

### For Future Officers ###

You need to do this every year (probably):

There's a new officer GroupMe every year (presumably), so you need to make a new GroupMe bot for the channel.

Create a new bot token at https://dev.groupme.com/ and select the new officer GroupMe. If the Discord bot is lost, then make another one at https://discord.com/developers/applications.

Also note if you're testing on Windows, shutting the script down will most likely spew an error. It's harmless so ignore it.

If you want to be cool, you can set up a public facing webserver to receive post requests from GroupMe instead of pinging the channel every few seconds.


#### YAML Config ####

Note that comments will disappear as the file is overwritten during runtime.

```yaml
# Discord Section
discord:
  # Discord bot token
  bot_token: BOT_TOKEN
  # #officers channel id
  officer_channel: CHANNEL_ID
  # Discord presence
  presence:
    gametype: 3
    presence: The Cyberspace
    url: null

# GroupMe section
groupme:

  # Group Id of the bot found at dev.groupme.com
  bot_groupid: GROUP_ID
  # Bot ID
  bot_id: BOT_ID

  # YOUR Access Token. Do not share this with anyone as they can impersonate you on GroupMe!
  bot_token: YOURACCESSTOKEN

  # DO NOT TOUCH, this is for dynamic message handling. Script starts reading new messages from last_msg.
  # This is so restarting the bot doesn't re-relay a bunch of messages back into the Discord
  last_msg: 0

  # Second interval between pinging the GroupMe for new messages
  sleep_time: 10.0
```
