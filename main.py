import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Button, View
import json
import random
import os
import asyncio
from dotenv import load_dotenv

from chip_manager import ChipManager
from views import SlotsView
from poll_manager import PollManager

# Load environment variables
load_dotenv()

# Get values from environment
token = os.getenv('BOT_TOKEN')
superuser = os.getenv('SUPERUSER_ID')
superuser_always_win = os.getenv('SUPERUSER_ALWAYS_WIN', 'False').lower() == 'true'

# Check if 'chips.json' exists, if not, create it
try:
    with open('chips.json', 'r') as f:
        pass
except FileNotFoundError:
    with open('chips.json', 'w') as f:
        json.dump({}, f)

# Check if 'poll.json' exists, if not, create it
try:
    with open('poll.json', 'r') as f:
        pass
except FileNotFoundError:
    with open('poll.json', 'w') as f:
        json.dump({}, f)

uptime = None

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize the chip manager
chip_manager = ChipManager()

# Initialize the PollManager
poll_manager = PollManager()

# Modified to use proper async operations
async def play_slots(interaction: Interaction, bet: int):
    # Always defer immediately
    await interaction.response.defer(ephemeral=True)
    
    try:
        if bet < 1:
            await interaction.followup.send("You must bet at least 1 chip!")
            return
        
        # Check user chips
        user_chips = await chip_manager.get_chips(interaction.user.id)
        
        if bet > user_chips:
            await interaction.followup.send("You don't have enough chips! Use `/chips` to check your chips.")
            return
        
        # Create and use the SlotsView
        view = SlotsView(interaction.user.id, bet, chip_manager, superuser, superuser_always_win)
        
        # Process first spin
        if not await chip_manager.remove_chips(interaction.user.id, bet):
            await interaction.followup.send("You don't have enough chips!")
            return
            
        result, is_win, winnings, embed = await view._process_spin(interaction.user.id)
        await interaction.followup.send(embed=embed, view=view)
        
    except Exception as e:
        print(f"Error in play_slots: {e}")
        await interaction.followup.send("An error occurred while processing your request.")

# Event: When the bot is ready and logged in
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="/help | beta v0.9"))
    global uptime
    uptime = discord.utils.utcnow()
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()  # Sync the slash commands with Discord
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

# Slash Command: Help command
@bot.tree.command(name="help", description="Shows the help message")
async def help(interaction: discord.Interaction):
    # Defer immediately to prevent timeouts
    await interaction.response.defer(ephemeral=True)
    
    embed = discord.Embed(title="Help", description="Here are the available commands:", color=0x00ff00)
    embed.add_field(name="/ping", value="Replies with 'Pong!' and the latency of the bot", inline=False)
    embed.add_field(name="/uptime", value="Shows the uptime of the bot", inline=False)
    embed.add_field(name="/leaderboard", value="Shows the leaderboard of the top 10 users with the most chips", inline=False)
    embed.add_field(name="/chips", value="Check your chips", inline=False)
    embed.add_field(name="/pay", value="Pay chips to another user", inline=False)
    embed.add_field(name="/broke", value="Show all users with 0 chips", inline=False)
    embed.add_field(name="/flip", value="Flip a coin with a bet", inline=False)
    embed.add_field(name="/roll", value="Roll a dice with a bet", inline=False)
    embed.add_field(name="/roulette", value="Play a game of roulette", inline=False)
    embed.add_field(name="/slots", value="Play a game of slots", inline=False)
    embed.add_field(name="/poll", value="Show the current prediction poll", inline=False)
    embed.add_field(name="/bet", value="Place a bet on a poll option", inline=False)
    await interaction.followup.send(embed=embed)

# Slash Command: Ping command with latency
@bot.tree.command(name="ping", description="Replies with 'Pong!' and the latency of the bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    latency = round(bot.latency * 1000)
    await interaction.followup.send(f":ping_pong: Latency: {latency}ms")

# Slash Command: Display the uptime of the bot
@bot.tree.command(name="uptime", description="Shows the uptime of the bot")
async def uptime(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    global uptime
    if uptime is None:
        await interaction.followup.send("Uptime is not available yet.")
        return
    uptime_duration = discord.utils.utcnow() - uptime
    await interaction.followup.send(f"Uptime: {uptime_duration}")

@bot.tree.command(name="leaderboard", description="Shows the leaderboard of the top 10 users with the most chips")
async def leaderboard(interaction: discord.Interaction):
    # Defer the response immediately
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Get top users, excluding superuser
        top_users = await chip_manager.get_top_users(10, [superuser])
    
        embed = discord.Embed(title="Leaderboard", description="Top 10 users with the most chips", color=0x00ff00)
        for i, (user_id, chips) in enumerate(top_users):
            member = await bot.fetch_user(int(user_id))
            embed.add_field(name=f"{i + 1}. {member.name}", value=f"{chips} chips", inline=False)
    
        user_rank = await chip_manager.get_user_rank(interaction.user.id)
        user_chips = await chip_manager.get_chips(interaction.user.id)
        embed.add_field(name="Your Rank", value=f"{user_rank or 'Not ranked'}", inline=True)
        embed.add_field(name="Your Chips", value=f"{user_chips} chips", inline=True)
    
        # Send the deferred response
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in leaderboard command: {e}")
        await interaction.followup.send("An error occurred while retrieving the leaderboard.")

# Slash Command: Check chips
@bot.tree.command(name="chips", description="Check your chips")
async def chips(interaction: discord.Interaction):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        chips = await chip_manager.get_chips(interaction.user.id)
        if chips > 999:
            chips_display = "{:,}".format(chips).replace(",", ".")
        else:
            chips_display = str(chips)
        
        embed = discord.Embed(title="Chips", description=f"You have {chips_display} chips!", color=0x00ff00)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in chips command: {e}")
        await interaction.followup.send("An error occurred while checking your chips.")

@bot.tree.command(name="broke", description="Show all users with 0 chips")
async def broke(interaction: discord.Interaction):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Find all users with 0 chips
        broke_users = await chip_manager.get_broke_users()
    
        # If no users are broke, send a follow-up message
        if not broke_users:
            await interaction.followup.send("No users have 0 chips!")
            return
    
        # Create an embed with the list of broke users
        embed = discord.Embed(title="Broke Users", description="Users with 0 chips", color=0xff0000)
        for user_id in broke_users:
            member = await bot.fetch_user(int(user_id))
            embed.add_field(name=member.name, value=f"{user_id}", inline=False)
    
        # Send the embed as a follow-up response
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in broke command: {e}")
        await interaction.followup.send("An error occurred while checking broke users.")

# Slash Command: Pay chips to another user
@bot.tree.command(name="pay", description="Pay chips to another user")
async def pay(interaction: discord.Interaction, user: discord.User, chips: int):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        if chips < 1:
            await interaction.followup.send("You must pay at least 1 chip!")
            return
        
        # Ensure user_id is string (extra safety)
        from_user_id = str(interaction.user.id)
        to_user_id = str(user.id)
        
        # Transfer chips between users
        if await chip_manager.transfer_chips(from_user_id, to_user_id, chips):
            await interaction.followup.send(f"Successfully paid {chips} chips to {user.mention}!")
            try:
                await user.send(f"{interaction.user.mention} paid you {chips} chips!")
            except:
                # In case DM fails, we still completed the transaction
                pass
        else:
            await interaction.followup.send("You don't have enough chips! Use `/chips` to check your chips.")
    except Exception as e:
        print(f"Error in pay command: {e}")
        await interaction.followup.send("An error occurred while processing your payment.")

# Slash Command: Flip a coin with a bet, let the user choose heads or tails
@bot.tree.command(name="flip", description="Flip a coin with a bet")
@app_commands.describe(bet="Amount of chips to bet", side="Choose heads or tails")
@app_commands.choices(side=[
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails")
])
@commands.cooldown(1, 1, commands.BucketType.user)
async def flip(interaction: Interaction, bet: int, side: str):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        if bet < 1:
            await interaction.followup.send("You must bet at least 1 chip!")
            return
        
        # Check if user has enough chips
        if not await chip_manager.remove_chips(interaction.user.id, bet):
            await interaction.followup.send("You don't have enough chips! Use `/chips` to check your chips.")
            return
        
        number = random.randint(0, 999)
        result = "heads" if number % 2 == 0 else "tails"
        
        # Superuser always win logic
        user = str(interaction.user.id)
        if user == superuser and superuser_always_win:
            result = side
        
        if result == side:
            await chip_manager.add_chips(interaction.user.id, bet * 2)
            await interaction.followup.send(f"Result: {result}! You won {bet} chips!")
        else:
            await interaction.followup.send(f"Result: {result}! You lost {bet} chips!")
        
        # Notify user if they're broke
        current_chips = await chip_manager.get_chips(interaction.user.id)
        if current_chips == 0:
            await interaction.user.send("You lost all your chips! Use `/chips` to check your chips.\r\nAsk an admin to get you more chips, or ask a friend to pay you some chips.")
    except Exception as e:
        print(f"Error in flip command: {e}")
        await interaction.followup.send("An error occurred while processing your bet.")

# Slash Command: Roll a dice with a bet, let the user choose the number to bet on
@bot.tree.command(name="roll", description="Roll a dice with a bet")
@app_commands.choices(number=[
    app_commands.Choice(name="1", value=1),
    app_commands.Choice(name="2", value=2),
    app_commands.Choice(name="3", value=3),
    app_commands.Choice(name="4", value=4),
    app_commands.Choice(name="5", value=5),
    app_commands.Choice(name="6", value=6)
])
@commands.cooldown(1, 1, commands.BucketType.user)
async def roll(interaction: discord.Interaction, bet: int, number: int):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        if bet < 1:
            await interaction.followup.send("You must bet at least 1 chip!")
            return
        
        # Check if user has enough chips
        if not await chip_manager.remove_chips(interaction.user.id, bet):
            await interaction.followup.send("You don't have enough chips! Use `/chips` to check your chips.")
            return
        
        result = random.randint(1, 6)
        
        # Superuser always win logic
        user = str(interaction.user.id)
        if user == superuser and superuser_always_win:
            result = number
        
        if result == number:
            await chip_manager.add_chips(interaction.user.id, bet * 6)
            await interaction.followup.send(f"Result: {result}! You won {bet * 5} chips!")
        else:
            await interaction.followup.send(f"Result: {result}! You lost {bet} chips!")
            
        # Notify user if they're broke
        current_chips = await chip_manager.get_chips(interaction.user.id)
        if current_chips == 0:
            await interaction.user.send("You lost all your chips! Use `/chips` to check your chips.\r\nAsk an admin to get you more chips, or ask a friend to pay you some chips.")
    except Exception as e:
        print(f"Error in roll command: {e}")
        await interaction.followup.send("An error occurred while processing your bet.")

# Slash Command: Roulette game
@bot.tree.command(name="roulette", description="Play a game of roulette")
@app_commands.describe(bet="Amount of chips to bet", number="Choose a number from 0 to 36")
@commands.cooldown(1, 1, commands.BucketType.user)
async def roulette(interaction: Interaction, bet: int, number: int):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        if bet < 1:
            await interaction.followup.send("You must bet at least 1 chip!")
            return
        if number < 0 or number > 36:
            await interaction.followup.send("Please choose a number between 0 and 36!")
            return
        
        # Check if user has enough chips
        if not await chip_manager.remove_chips(interaction.user.id, bet):
            await interaction.followup.send("You don't have enough chips! Use `/chips` to check your chips.")
            return
        
        result = random.randint(0, 36)
        
        # Superuser always win logic
        user = str(interaction.user.id)
        if user == superuser and superuser_always_win:
            result = number
        
        if result == number:
            await chip_manager.add_chips(interaction.user.id, bet * 36)
            await interaction.followup.send(f"Result: {result}! You won {bet * 35} chips!")
        else:
            await interaction.followup.send(f"Result: {result}! You lost {bet} chips!")
            
        # Notify user if they're broke
        current_chips = await chip_manager.get_chips(interaction.user.id)
        if current_chips == 0:
            await interaction.user.send("You lost all your chips! Use `/chips` to check your chips.\r\nAsk an admin to get you more chips, or ask a friend to pay you some chips.")
    except Exception as e:
        print(f"Error in roulette command: {e}")
        await interaction.followup.send("An error occurred while processing your bet.")

# Slash Command: Slots game
@bot.tree.command(name="slots", description="Play a game of slots")
@app_commands.describe(bet="Amount of chips to bet")
async def slots(interaction: Interaction, bet: int):
    await play_slots(interaction, bet)

# Slash command: add a Prediction poll
@bot.tree.command(name="create_poll", description="Create a prediction poll")
@app_commands.describe(question="The question to bet on", option1="First option", option2="Second option")
async def create_poll(interaction: Interaction, question: str, option1: str, option2: str):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=False)
    
    try:
        if str(interaction.user.id) != superuser:
            await interaction.followup.send("You are not authorized to create a poll!", ephemeral=True)
            return
        
        success, error = await poll_manager.create_poll(question, option1, option2)
        if not success:
            await interaction.followup.send(error, ephemeral=True)
            return
        
        embed = discord.Embed(title="Prediction Poll", description=question, color=0x00ff00)
        embed.add_field(name="Option 1", value=option1, inline=True)
        embed.add_field(name="Option 2", value=option2, inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in create_poll command: {e}")
        await interaction.followup.send("An error occurred while creating the poll.")

@bot.tree.command(name="bet", description="Place a bet on a poll option")
@app_commands.describe(option="The option to bet on", amount="Amount of chips to bet")
async def bet(interaction: Interaction, option: str, amount: int):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Check if user has enough chips
        user_id = str(interaction.user.id)
        user_chips = await chip_manager.get_chips(user_id)
        
        if user_chips < amount:
            await interaction.followup.send("You don't have enough chips!")
            return
        
        # Place bet using poll manager
        success, error = await poll_manager.place_bet(user_id, option, amount)
        if not success:
            await interaction.followup.send(error)
            return
        
        # Remove chips from user
        await chip_manager.remove_chips(user_id, amount)
        
        await interaction.followup.send(f"You bet {amount} chips on {option}!")
    except Exception as e:
        print(f"Error in bet command: {e}")
        await interaction.followup.send("An error occurred while processing your bet.")

@bot.tree.command(name="close_poll", description="Close the prediction poll")
async def close_poll(interaction: Interaction):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        if str(interaction.user.id) != superuser:
            await interaction.followup.send("You are not authorized to close a poll!")
            return
    
        success, error = await poll_manager.close_poll()
        if not success:
            await interaction.followup.send(error)
            return
        
        await interaction.followup.send("The poll has been closed!")
    except Exception as e:
        print(f"Error in close_poll command: {e}")
        await interaction.followup.send("An error occurred while closing the poll.")

@bot.tree.command(name="end_poll", description="End the prediction poll and distribute winnings")
@app_commands.describe(winning_option="The correct option")
async def end_poll(interaction: Interaction, winning_option: str):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=False)
    
    try:
        if str(interaction.user.id) != superuser:
            await interaction.followup.send("You are not authorized to end a poll!", ephemeral=True)
            return
    
        success, result, payouts = await poll_manager.end_poll(winning_option)
        if not success:
            await interaction.followup.send(result)
            return
    
        if not payouts:
            message = "No one bet on the winning option!"
        else:
            for user_id, amount in payouts.items():
                await chip_manager.add_chips(user_id, amount)
            message = f"The poll has ended! Winning option: {winning_option}"
    
        await interaction.followup.send(message)
    except Exception as e:
        print(f"Error in end_poll command: {e}")
        await interaction.followup.send("An error occurred while ending the poll.")

# Slash Command: Show current poll
@bot.tree.command(name="poll", description="Show the current prediction poll")
async def poll(interaction: Interaction):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    try:
        poll_data = await poll_manager.get_poll_data()
        
        if not poll_data.get("active", False):
            await interaction.followup.send("There is no active poll!")
            return
        
        question = poll_data["question"]
        options = poll_data["options"]
        total_bets = poll_data["total_bets"]
        
        embed = discord.Embed(title="Prediction Poll", description=question, color=0x00ff00)
        for option, bets in options.items():
            bet_count = len(bets)
            bet_amount = sum(bets.values())
            embed.add_field(name=option, value=f"{bet_count} bets ({bet_amount} chips)", inline=True)
        
        embed.set_footer(text=f"Total bets: {total_bets} chips")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"Error in poll command: {e}")
        await interaction.followup.send("An error occurred while retrieving the poll.")

@bot.command()
async def togglesuwin(ctx):
    await ctx.message.delete()
    global superuser_always_win
    superuser_always_win = not superuser_always_win
    await ctx.author.send(f"Superuser always win is now {'enabled' if superuser_always_win else 'disabled'}")

# ! Command: Set chips for a user (Admin only)
@bot.command()
async def setchips(ctx, user: discord.User, chips: int):
    await ctx.message.delete()
    if ctx.author.id != int(superuser):
        await ctx.author.send("You are not allowed to use this command.")
        return
    
    await chip_manager.set_chips(user.id, chips)
    await ctx.author.send(f"Successfully set {user.name}'s chips to {chips}")

@bot.command()
async def resetbroke(ctx):
    if ctx.author.id != int(superuser):
        await ctx.author.send("You are not allowed to use this command.")
        return
    
    try:
        await ctx.message.delete()
    except (discord.Forbidden, AttributeError):
        pass

    count = await chip_manager.reset_broke_users()
    await ctx.author.send(f"Successfully reset {count} broke users.")

# ! Command: See all admin commands
@bot.command()
async def adminhelp(ctx):
    await ctx.message.delete()
    if ctx.author.id != int(superuser):
        await ctx.author.send("You are not allowed to use this command.")
        return

    embed = discord.Embed(title="Admin Commands", description="Here are the available admin commands:", color=0x00ff00)
    embed.add_field(name="!togglesuwin", value="Toggle superuser always win mode", inline=False)
    embed.add_field(name="!setchips", value="Set chips for a user", inline=False)
    embed.add_field(name="!resetbroke", value="Reset all users with 0 chips", inline=False)
    await ctx.author.send(embed=embed)

# Command error handler
@bot.event
async def on_command_error(ctx, error):
    print(f"Command error: {error}")
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Please wait {error.retry_after:.2f} seconds.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        await ctx.send(f"An error occurred: {error}")

# Application command error handler
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    print(f"App command error: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)
    else:
        await interaction.followup.send(f"An error occurred: {str(error)}")

bot.run(token)