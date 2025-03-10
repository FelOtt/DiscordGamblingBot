import discord
import random
from discord import Interaction

class SlotsView(discord.ui.View):
    def __init__(self, user_id: int, bet: int, chip_manager, superuser=None, superuser_always_win=False):
        super().__init__(timeout=600)  # Views timeout after 10 minutes
        self.user_id = user_id
        self.bet = bet
        self.chip_manager = chip_manager
        self.superuser = superuser
        self.superuser_always_win = superuser_always_win
        # Set custom ID for persistence
        self.spin_button.custom_id = f"slots_spin_{user_id}_{bet}"
    
    async def handle_initial_spin(self, interaction: Interaction):
        """Process the initial spin when /slots is called"""
        # Check if user has enough chips
        if not await self.chip_manager.remove_chips(interaction.user.id, self.bet):
            await interaction.response.send_message("You don't have enough chips! Use `/chips` to check your chips.", ephemeral=True)
            return
        
        # Process slot spin using shared logic
        result, is_win, winnings, embed = await self._process_spin(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
    
    async def _process_spin(self, user_id):
        """Shared logic for processing a slots spin"""
        # Generate slots result
        result = [random.choice(["🍒", "🍋", "🍊", "🍇", "🍉", "🍌", "🍓"]) for _ in range(3)]
        
        # Superuser always win logic
        if str(user_id) == self.superuser and self.superuser_always_win:
            result = ["🍉", "🍉", "🍉"]

        # Calculate winnings
        is_win = False
        winnings = 0
        
        if result[0] == result[1] == result[2]:
            await self.chip_manager.add_chips(user_id, self.bet * 15)
            embed = discord.Embed(title="Slots", 
                                 description=f"Result: {' '.join(result)}!\nYou won {self.bet * 14} chips!", 
                                 color=0x00ff00)
            is_win = True
            winnings = self.bet * 14
        elif result[0] == result[1] or result[1] == result[2]:
            await self.chip_manager.add_chips(user_id, self.bet * 3)
            embed = discord.Embed(title="Slots", 
                                 description=f"Result: {' '.join(result)}!\nYou won {self.bet * 2} chips!", 
                                 color=0x00ff00)
            is_win = True
            winnings = self.bet * 2
        else:
            embed = discord.Embed(title="Slots", 
                                 description=f"Result: {' '.join(result)}!\nYou lost {self.bet} chips!", 
                                 color=0xff0000)
            is_win = False
            winnings = 0
        
        return result, is_win, winnings, embed
        
    @discord.ui.button(label="Spin Again", style=discord.ButtonStyle.green, custom_id="spin_again")
    async def spin_button(self, interaction: Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("You cannot use this button!", ephemeral=True)
                return
            
            # Check if user has enough chips
            if not await self.chip_manager.remove_chips(interaction.user.id, self.bet):
                await interaction.response.send_message("You don't have enough chips! Use `/chips` to check your chips.", ephemeral=True)
                return
            
            # Process spin using shared logic
            result, is_win, winnings, embed = await self._process_spin(interaction.user.id)
            
            # Create a new view for the next spin
            new_view = SlotsView(interaction.user.id, self.bet, self.chip_manager, self.superuser, self.superuser_always_win)
            await interaction.response.send_message(embed=embed, view=new_view, ephemeral=True)
            
        except Exception as e:
            print(f"Error in spin_button: {e}")
            await interaction.response.send_message("An error occurred while processing your spin.", ephemeral=True)