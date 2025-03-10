import unittest
import asyncio
import os
import sys
import random
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from views import SlotsView
from chip_manager import ChipManager

class TestGameMechanics(unittest.TestCase):
    def setUp(self):
        # Mock ChipManager
        self.chip_manager = MagicMock(spec=ChipManager)
        
        # Sample test data
        self.user_id = 123456
        self.bet = 100
        self.superuser = "999999"
    
    @patch('random.choice')
    async def _test_slots_win_logic(self, mock_choice):
        # Set up mocks for all symbols
        mock_choice.side_effect = ["🍒", "🍒", "🍒"]  # All matching
        
        # Create slots view and process spin
        slots_view = SlotsView(self.user_id, self.bet, self.chip_manager)
        result, is_win, winnings, _ = await slots_view._process_spin(self.user_id)
        
        # Check results
        self.assertEqual(result, ["🍒", "🍒", "🍒"])
        self.assertTrue(is_win)
        self.assertEqual(winnings, self.bet * 14)
        
        # Verify chips were added
        self.chip_manager.add_chips.assert_called_once_with(self.user_id, self.bet * 15)
    
    @patch('random.choice')
    async def _test_slots_partial_win_logic(self, mock_choice):
        # Set up mocks for partial match
        mock_choice.side_effect = ["🍊", "🍊", "🍌"]  # Two matching
        
        # Create slots view and process spin
        slots_view = SlotsView(self.user_id, self.bet, self.chip_manager)
        result, is_win, winnings, _ = await slots_view._process_spin(self.user_id)
        
        # Check results
        self.assertEqual(result, ["🍊", "🍊", "🍌"])
        self.assertTrue(is_win)
        self.assertEqual(winnings, self.bet * 2)
        
        # Verify chips were added
        self.chip_manager.add_chips.assert_called_once_with(self.user_id, self.bet * 3)
    
    @patch('random.choice')
    async def _test_slots_loss_logic(self, mock_choice):
        # Set up mocks for no match
        mock_choice.side_effect = ["🍎", "🍊", "🍌"]  # No matches
        
        # Create slots view and process spin
        slots_view = SlotsView(self.user_id, self.bet, self.chip_manager)
        result, is_win, winnings, _ = await slots_view._process_spin(self.user_id)
        
        # Check results
        self.assertEqual(result, ["🍎", "🍊", "🍌"])
        self.assertFalse(is_win)
        self.assertEqual(winnings, 0)
        
        # Verify no chips were added
        self.chip_manager.add_chips.assert_not_called()
    
    async def _test_superuser_always_win(self):
        # Create slots view with superuser settings
        slots_view = SlotsView(
            int(self.superuser), 
            self.bet, 
            self.chip_manager,
            superuser=self.superuser,
            superuser_always_win=True
        )
        
        # Process spin
        result, is_win, winnings, _ = await slots_view._process_spin(int(self.superuser))
        
        # Check results - superuser should get 3 matching symbols
        self.assertEqual(result, ["🍉", "🍉", "🍉"])
        self.assertTrue(is_win)
        self.assertEqual(winnings, self.bet * 14)
    
    def test_slots_win_logic(self):
        asyncio.run(self._test_slots_win_logic())
    
    def test_slots_partial_win_logic(self):
        asyncio.run(self._test_slots_partial_win_logic())
    
    def test_slots_loss_logic(self):
        asyncio.run(self._test_slots_loss_logic())
    
    def test_superuser_always_win(self):
        asyncio.run(self._test_superuser_always_win())

if __name__ == '__main__':
    unittest.main()