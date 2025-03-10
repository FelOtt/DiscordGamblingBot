# Discord Gambling Bot

A feature-rich Discord bot that allows users to engage in various gambling games using virtual chips. Users can earn, bet, and transfer chips, participate in prediction polls, and compete on leaderboards.

## Table of Contents
- [Features](#features)
- [Setup Instructions](#setup-instructions)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [User Commands](#user-commands)
  - [General Commands](#general-commands)
  - [Chip Management](#chip-management)
  - [Gambling Games](#gambling-games)
  - [Prediction Polls](#prediction-polls)
- [Admin Commands](#admin-commands)
- [Game Rules](#game-rules)
  - [Coin Flip](#coin-flip)
  - [Dice Roll](#dice-roll)
  - [Roulette](#roulette)
  - [Slots](#slots)
  - [Prediction Polls](#prediction-polls-1)
- [Testing](#testing)
  - [Running Tests](#running-tests)
  - [Test Structure](#test-structure)
  - [Test Coverage](#test-coverage)
- [Technical Details](#technical-details)
- [License](#license)

## Features

- **Virtual Chip Economy**: Users earn and bet with virtual chips
- **Multiple Games**: Flip, Roll, Roulette, and Slots
- **Prediction Polls**: Create polls for users to bet on outcomes
- **Leaderboard System**: Track top users
- **Admin Controls**: Manage the economy and prediction polls

## Setup Instructions

### Prerequisites
- Python 3.8+ installed
- Discord account and a registered Discord application/bot
- Bot permissions: Send Messages, Read Message History, Use Slash Commands

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/DiscordGamblingBot.git
   cd DiscordGamblingBot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Copy .env.example to .env and fill in your information:
   ```
   BOT_TOKEN=your_discord_bot_token_here
   SUPERUSER_ID=your_discord_user_id
   SUPERUSER_ALWAYS_WIN=False
   STARTING_CHIPS=1000
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## User Commands

All regular user commands use slash commands (`/`):

### General Commands
- `/help` - Shows all available commands
- `/ping` - Check the bot's latency
- `/uptime` - See how long the bot has been running

### Chip Management
- `/chips` - Check your chip balance
- `/pay <user> <amount>` - Transfer chips to another user
- `/broke` - View all users with 0 chips
- `/leaderboard` - See the top 10 users with the most chips

### Gambling Games
- `/flip <bet> <heads/tails>` - Flip a coin with a bet
- `/roll <bet> <number>` - Roll a dice (1-6) with a bet
- `/roulette <bet> <number>` - Place a bet on a number (0-36)
- `/slots <bet>` - Play a slot machine game

### Prediction Polls
- `/poll` - View the current active prediction poll
- `/bet <option> <amount>` - Place a bet on a poll option

## Admin Commands

Admin commands use the `!` prefix and are only available to the superuser defined in the .env file:

- `!adminhelp` - Shows all admin commands
- `!setchips <user> <amount>` - Set a user's chips to a specific amount
- `!resetbroke` - Reset chip balances for all users with 0 chips
- `!togglesuwin` - Toggle whether the superuser automatically wins games

### Slash Commands for Admins

- `/create_poll <question> <option1> <option2>` - Create a prediction poll
- `/close_poll` - Close an active poll (no more bets)
- `/end_poll <winning_option>` - End a poll and distribute winnings

## Game Rules

### Coin Flip
- Correctly guess heads or tails to double your bet

### Dice Roll
- Correctly guess a number from 1-6 to win 5x your bet

### Roulette
- Correctly guess a number from 0-36 to win 35x your bet

### Slots
- Three matching symbols: Win 14x your bet
- Two matching symbols: Win 2x your bet

### Prediction Polls
1. An admin creates a poll with a question and two options
2. Users bet chips on their predicted outcome
3. Admin closes the poll when betting should end
4. Admin ends the poll with the winning option
5. Chips are distributed proportionally among winners

## Testing

The bot includes a comprehensive test suite to ensure functionality works as expected.

### Running Tests

To run all tests using the test runner:

```bash
python -m tests.run_tests
```

This will execute all test cases and provide detailed output about passing and failing tests.

To run specific test modules individually:

```bash
python -m unittest tests.test_chip_manager
python -m unittest tests.test_poll_manager
python -m unittest tests.test_game_mechanics
```

### Test Structure

The test suite is organized into three main modules:

```
tests/
├── run_tests.py          # Main test runner
├── test_chip_manager.py  # Tests for chip economy
├── test_poll_manager.py  # Tests for prediction polls
└── test_game_mechanics.py # Tests for gambling games
```

### Test Coverage

Tests are organized into three main categories:

1. **Chip Manager Tests** - Test the virtual chip economy functionality
   - Chip balance management
   - Transfers between users
   - Leaderboard functionality

2. **Poll Manager Tests** - Test prediction poll functionality
   - Poll creation and management
   - Betting mechanics
   - Reward distribution

3. **Game Mechanics Tests** - Test gambling game logic
   - Slots win/loss conditions 
   - Payout calculations
   - Superuser functionality

Each test uses mocking to isolate components and simulate various scenarios, ensuring that functionality works correctly even under unusual conditions.

## Technical Details

- Data is stored in JSON files: chips.json for user balances and poll.json for active polls
- The ChipManager class handles all chip-related operations
- Each user starts with 1000 chips by default
- Asynchronous design with proper locking for data integrity
- Singleton pattern used for managers to ensure consistency

## License

MIT License