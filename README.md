# 5man-bot (FiveStack)

A Discord bot designed to help organize 5-player groups for League of Legends. The bot provides an interactive interface for creating groups, joining with role preferences, and tracking progress until a full 5-man team is assembled.

## 1. General

The **5man-bot** (also known as **FiveStack**) is a Discord bot that streamlines the process of forming 5-player groups for League of Legends. Instead of manually coordinating in chat, users can:

- Create a new 5-man group with a single command
- Join groups by selecting their preferred role (Top, Jungle, Mid, ADC, Support, or Fill)
- Optionally specify their availability time
- See real-time progress as slots fill up
- Leave or reset groups as needed

The bot displays an interactive embed with buttons that update in real-time, showing who has joined, their roles, and availability. When all 5 slots are filled, the bot automatically notifies all members that the group is ready.

## 2. Code Architecture

The project follows a modular architecture using Discord.py's Cog system:

### Core Components

- **`main.py`**: Entry point that initializes the bot, loads cogs, and starts the Discord connection
- **`bot/FiveStack.py`**: Main bot class that manages the bot instance, active groups dictionary, and cog loading logic
- **`bot/instance.py`**: Singleton pattern implementation for accessing the bot instance globally
- **`config.py`**: Configuration management for environment variables, bot intents, and environment-specific settings (dev/prod)

### Cogs

- **`bot/cogs/session.py`**: Handles all slash commands for session management:
  - `/5stack fivestack` - Create a new 5-man group
  - `/5stack session-status` - Check current session status
  - `/5stack reset-fivestack` - Reset the active group for a guild
  - `/5stack cleanup-messages` - Delete old bot messages

### Models

- **`models/FiveManView.py`**: Discord UI View class that manages the interactive embed and button state. Tracks:
  - 5 slots (each can contain user_id, username, role, and time)
  - Group creator and guild ID
  - Closed status and timestamps
  - Embed generation with progress visualization

### UI Components (`ui/`)

- **`SlotButton.py`**: "Join" button that initiates the join flow
- **`RoleSelect.py`**: Dropdown menu for selecting League of Legends role
- **`TimeModal.py`**: Modal dialog for entering optional availability time
- **`LeaveButton.py`**: Allows users to leave the group
- **`ResetButton.py`**: Resets all slots in the group
- **`CloseButton.py`**: Closes the group and prevents further interactions

### Data Flow

1. User executes `/5stack fivestack` → `Session` cog creates a `FiveManView` instance
2. `FiveManView` is stored in `FiveStack.active_groups[guild_id]` (one per guild)
3. Users interact with buttons → UI components update the view's slot data
4. View updates the embed and edits the original message
5. When full, bot sends a notification message to the channel

## 3. Features of the Bot

### Group Management
- **Single Active Group**: Only one active 5-man group can exist per Discord server at a time
- **Persistent Views**: Groups remain interactive even after bot restarts (using persistent views)
- **Real-time Updates**: Embed and buttons update immediately when users join/leave

### User Interactions
- **Role Selection**: Users can select from Top, Jungle, Mid, ADC, Support, or Fill roles
- **Availability Time**: Optional text input for users to specify when they're available
- **Visual Progress**: Progress bar (✅/⬜) shows how many slots are filled (X/5)
- **Role Emojis**: Custom emojis displayed next to each role in the embed

### Commands
- `/5stack fivestack` - Create a new 5-man group
- `/5stack session-status` - Check the status of the current session (debug)
- `/5stack reset-fivestack` - Administratively reset the active group
- `/5stack cleanup-messages` - Delete old bot messages (requires manage messages permission)

### Group Actions
- **Join**: Select role and optionally provide availability time
- **Leave**: Remove yourself from the group
- **Reset Group**: Clear all slots (keeps the group active)
- **Close Group**: Permanently close the group and disable all buttons

### Notifications
- Automatic ping to "league-of-legends" role when a new group is created
- Notification message sent to channel when group reaches 5/5 members

### Environment Support
- Separate dev and production environments with different command prefixes (`/5test` vs `/5stack`)
- Environment-specific Discord tokens and configuration

## 4. How to Run

### Prerequisites

- Python 3.11 or higher
- Discord Bot Token (create a bot at https://discord.com/developers/applications)
- Discord Application ID and Public Key (from Discord Developer Portal)

### Installation

1. Clone the repository:
   ```bash
   cd /path/to/5man-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with the following variables:
   ```env
   BOT_ENV=dev  # or "prod" for production
   
   # Development environment
   DEV_APP_ID=your_dev_app_id
   DEV_PUBLIC_KEY=your_dev_public_key
   DEV_DISCORD_TOKEN=your_dev_bot_token
   
   # Production environment
   PROD_APP_ID=your_prod_app_id
   PROD_PUBLIC_KEY=your_prod_public_key
   PROD_DISCORD_TOKEN=your_prod_bot_token
   ```

4. Ensure your Discord bot has the following permissions:
   - Send Messages
   - Embed Links
   - Read Message History
   - Use Slash Commands
   - Manage Messages (for cleanup command)

5. Invite the bot to your Discord server with the appropriate OAuth2 scopes:
   - `bot`
   - `applications.commands`

### Running Locally

```bash
python main.py
```

### Running with Docker

1. Build the Docker image:
   ```bash
   docker build -t 5man-bot .
   ```

2. Run the container:
   ```bash
   docker run --env-file .env 5man-bot
   ```

**Note**: The Dockerfile currently references `bot.py` in the CMD, but the actual entry point is `main.py`. You may need to update the Dockerfile if using Docker.

### First Run

1. Start the bot - it will automatically:
   - Load all cogs from `bot/cogs/`
   - Sync slash commands with Discord
   - Print loaded commands to console

2. In your Discord server, use `/5stack fivestack` (or `/5test fivestack` in dev mode) to create your first group

3. Users can click the "Join" button to add themselves to the group

## 5. Known Bugs and Future Features

### Known Bugs

- No automatic cleanup of old groups (groups persist until manually closed/reset)
- Groups are not persisted between restarts, so unexpected crashes will cause interaction issues with views  
  
### Future Features

- **Automatic Group Expiration**: Groups automatically close after a set period of inactivity
- **Multiple Groups Per Guild**: Allow multiple active groups simultaneously
- **Queue System**: Queue for next available slot if group is full
- **Statistics**: Track how many groups have been formed, average fill time, etc.
- **Scheduled Groups**: Create groups that start at a specific time
- **Voice Channel Integration**: Automatically create/move users to a voice channel when group is full
- **Notification Preferences**: Allow users to opt-in/out of group notifications
- **Group Templates**: Create and save common group configurations (e.g., ranked vs. casual)
- **Leaderboard**: Track most active group creators/joiners