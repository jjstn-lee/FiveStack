INCOMPLETE README

# Discord 5man Bot

A Discord bot for organizing 5-player gaming groups with persistent session management and automatic refresh capabilities. Perfect for games like League of Legends, Valorant, CS2, or any other 5v5 team-based games.

## Features

- **Interactive Group Management**: Create, join, leave, and manage 5-player groups through Discord slash commands and buttons
- **Persistent Sessions**: Bot remembers active groups even after restarts (within 1 hour)
- **Automatic Refresh**: Prevents Discord's 15-minute interaction timeout with background refresh tasks
- **Availability Tracking**: Players can specify when they're available to play
- **Role Mentions**: Automatically mentions configured roles when new groups are created
- **Real-time Updates**: Live embed updates showing group progress and member list
- **Anti-Spam**: Automatically deletes non-command messages in the channel

## Commands

- `/5man start` - Create a new 5-player group
- `/5man session` - Check current session status (debug command)
- `/5man force_refresh` - Manually refresh the current group (debug command)

## Interactive Buttons

- **Join** - Join the current group with optional availability time
- **Leave** - Leave the current group
- **Reset Group** - Clear all members (creator only)
- **Close Group** - Close the group and allow new ones to be created (creator only)

## Requirements

- Python 3.8+
- Discord.py 2.0+
- aiofiles
- python-dotenv
- Docker (for containerization)
- AWS account (for hosting)

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd discord-5man-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create and configure environment file**
   
   First, create the environment file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Discord bot credentials:
   ```env
   APP_ID=your_application_id
   DISCORD_TOKEN=your_bot_token
   PUBLIC_KEY=your_public_key
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Discord Bot Setup

1. **Create a Discord Application**
   - Go to https://discord.com/developers/applications
   - Click "New Application" and give it a name
   - Note down the Application ID

2. **Create a Bot**
   - Go to the "Bot" section
   - Click "Add Bot"
   - Copy the bot token (keep this secret!)
   - Enable "MESSAGE CONTENT INTENT" if your bot needs to read messages

3. **Get Public Key**
   - Go to "General Information"
   - Copy the Public Key

4. **Bot Permissions**
   Required permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Manage Messages (for auto-delete feature)
   - Read Message History

5. **Invite Bot to Server**
   - Go to "OAuth2" > "URL Generator"
   - Select "bot" and "applications.commands" scopes
   - Select the required permissions
   - Use the generated URL to invite the bot

## Docker Deployment

### Build Docker Image

```bash
docker build -t discord-5man-bot .
```

### Run Locally with Docker

```bash
docker run -d \
  --name 5man-bot \
  --env-file .env \
  discord-5man-bot
```

### Docker Compose (Optional)

```yaml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./data:/app/data  # For persistent session storage
```

## AWS ECS Deployment

### Prerequisites

- AWS CLI configured
- ECR repository created
- ECS cluster set up

### Step 1: Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push image
docker tag discord-5man-bot:latest <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/discord-5man-bot:latest
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/discord-5man-bot:latest
```

### Step 2: Create Task Definition

### Step 3: Create ECS Service

## Configuration

### Bot Customization

- **Role Mention**: Change `league-of-legends` role name in the code to match your server's role
- **Session Timeout**: Modify the 1-hour session timeout in `SessionManager.load_session()`
- **Refresh Interval**: Adjust the 10-minute refresh task interval in `@tasks.loop(minutes=10)`

## File Structure

```
discord-5man-bot/
├── bot.py                 # Main bot code
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── session_data.json    # Auto-generated session persistence (don't commit)
```

## Monitoring & Debugging

### CloudWatch Logs

The bot logs important events and errors to CloudWatch when deployed on AWS ECS. Key log patterns to watch:

- `✅ Session restored!` - Successful session recovery
- `🔄 Refreshing view` - Automatic refresh working
- `ERROR:root:` - Python errors that need attention

### Debug Commands

- `/5man session` - Shows current group status, member count, and system health
- `/5man force_refresh` - Manually triggers view refresh if needed

### Common Issues

1. **"Interaction Failed" Errors**
   - Check CloudWatch logs for specific error messages
   - Ensure ECS task has sufficient memory (512MB minimum)
   - Verify all environment variables are set correctly

2. **Bot Doesn't Respond**
   - Check if bot has proper permissions in the Discord server
   - Verify slash commands are synced (`🔃 Synced X command(s)` in logs)
   - Ensure bot is online and ECS service is running

3. **Session Not Restoring**
   - Check if `session_data.json` exists and is readable
   - Verify the original message still exists in Discord
   - Session expires after 1 hour automatically

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Designed for AWS ECS deployment
- Optimized for gaming communities
- README written with assistance from Claude