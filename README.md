# FiveStack Bot

A lightweight Discord bot that helps users plan and organize 5-man gaming parties for cooperative play!

To install, click the link [here!](https://discord.com/oauth2/authorize?client_id=1399290217659105331)

## Features

- ✅ Create and manage 5-player parties in Discord
- 🧑‍🤝‍🧑 Allow users to join or leave parties via slash commands
- 🕒 Get notifications when the stack is full
- 📛 Prevent duplicate joins and enforce a 5-player cap

## Basic Commands

|  Command         | Description
|------------------|------------------------------------------------|
| /5stack start    | Begins a new FiveStack session                 |
| /5stack session  | Checks current status of the FiveStack session | 
| /5stack cleanup  | Deletes old FiveStack messages                 |
| /5stack reset    | Resets the FiveStack session                   |

## Installation (normal)

To install the bot on your own server, check the link [here!](https://discord.com/oauth2/authorize?client_id=1399290217659105331)

## Installation (local)

If you want to run the bot for yourself, complete the following steps:

1. Clone the repo
```bash
git clone git@github.com:jjstn-lee/5man-bot.git
cd fivestack-bot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a Discord bot on the Discover Developer portal and add set up environment variables [(official instructions found here)](https://discord.com/developers/docs/quick-start/getting-started)

```bash
# your .env file should look like this:
APP_ID=your_bots_id_here
DISCORD_TOKEN=your_discord_token_here
PUBLIC_KEY=your_bots_public_key_here
```

4. Run the bot!
```bash
# from the root directory
python3 bot.py
```

Note that a Dockerfile and GitHub Action workflow is also included. Tweaking these will allow you to use Github Actions for CI/CD and host it on AWS ECS.

## Future Features(?)

1. Auto-expiration on sessions based on the latest time given or after _n_ number of hours.
2. Implementation for multiple sessions.
3. Implementation for multiple games other than League of Legends.
4. Utilize 'dateparser' from Python to allow for natural language time inputs.
5. When creating a group, allow people to also sign up for others.
6. "On the bench" feature to let people fill in
