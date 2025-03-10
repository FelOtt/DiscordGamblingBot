import unittest
import asyncio
import os
import json
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from poll_manager import PollManager

class TestPollManager(unittest.TestCase):
    def setUp(self):
        # Create a test file
        self.test_file = 'test_poll.json'
        
        # Reset the singleton instance for clean tests
        PollManager._instance = None
        
        # Create a new instance with a mocked _initialize
        with patch.object(PollManager, '_initialize') as mock_init:
            self.poll_manager = PollManager()
            # Manually set attributes that would be set in _initialize
            self.poll_manager.poll_file = self.test_file
            self.poll_manager.poll_data = {}
        
        # Clear any existing poll data
        self.poll_manager.poll_data = {}
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def tearDown(self):
        # Remove test file
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_create_poll(self):
        # Mock the _save_poll method to avoid actual file operations
        with patch.object(self.poll_manager, '_save_poll', return_value=True):
            # Test creating a poll
            success, error = asyncio.run(self.poll_manager.create_poll("Test Question", "Option A", "Option B"))
            self.assertTrue(success)
            self.assertIsNone(error)
            
            # Verify poll data
            poll_data = self.poll_manager.poll_data
            self.assertTrue(poll_data["active"])
            self.assertFalse(poll_data["closed"])
            self.assertEqual(poll_data["question"], "Test Question")
            self.assertIn("Option A", poll_data["options"])
            self.assertIn("Option B", poll_data["options"])
            
            # Test creating a poll when one already exists
            success, error = asyncio.run(self.poll_manager.create_poll("Another Question", "C", "D"))
            self.assertFalse(success)
            self.assertEqual(error, "There is already an active poll!")
    
    def test_close_poll(self):
        # Create a poll first
        with patch.object(self.poll_manager, '_save_poll', return_value=True):
            asyncio.run(self.poll_manager.create_poll("Test Question", "Option A", "Option B"))
            
            # Close the poll
            success, error = asyncio.run(self.poll_manager.close_poll())
            self.assertTrue(success)
            self.assertIsNone(error)
            self.assertTrue(self.poll_manager.poll_data["closed"])
            
            # Try to close again
            success, error = asyncio.run(self.poll_manager.close_poll())
            self.assertFalse(success)
            self.assertEqual(error, "The poll is already closed!")
    
    def test_place_bet(self):
        # Create a poll first
        with patch.object(self.poll_manager, '_save_poll', return_value=True):
            asyncio.run(self.poll_manager.create_poll("Test Question", "Option A", "Option B"))
            
            # Place a bet
            success, error = asyncio.run(self.poll_manager.place_bet("123456", "Option A", 100))
            self.assertTrue(success)
            self.assertIsNone(error)
            
            # Verify the bet was placed
            self.assertEqual(self.poll_manager.poll_data["options"]["Option A"]["123456"], 100)
            self.assertEqual(self.poll_manager.poll_data["total_bets"], 100)
            
            # Place another bet on same option
            success, error = asyncio.run(self.poll_manager.place_bet("123456", "Option A", 50))
            self.assertTrue(success)
            self.assertEqual(self.poll_manager.poll_data["options"]["Option A"]["123456"], 150)
            self.assertEqual(self.poll_manager.poll_data["total_bets"], 150)
            
            # Try to bet on a different option (should fail)
            success, error = asyncio.run(self.poll_manager.place_bet("123456", "Option B", 100))
            self.assertFalse(success)
            self.assertIn("you cannot switch options", error.lower())
            
            # Place a bet from different user
            success, error = asyncio.run(self.poll_manager.place_bet("789012", "Option B", 200))
            self.assertTrue(success)
            self.assertEqual(self.poll_manager.poll_data["options"]["Option B"]["789012"], 200)
            self.assertEqual(self.poll_manager.poll_data["total_bets"], 350)
    
    def test_end_poll(self):
        # Create a poll with bets
        with patch.object(self.poll_manager, '_save_poll', return_value=True):
            asyncio.run(self.poll_manager.create_poll("Test Question", "Option A", "Option B"))
            asyncio.run(self.poll_manager.place_bet("123456", "Option A", 100))
            asyncio.run(self.poll_manager.place_bet("789012", "Option B", 200))
            asyncio.run(self.poll_manager.close_poll())
            
            # End the poll
            success, winning_option, payouts = asyncio.run(self.poll_manager.end_poll("Option A"))
            
            self.assertTrue(success)
            self.assertEqual(winning_option, "Option A")
            self.assertEqual(len(payouts), 1)
            self.assertEqual(payouts["123456"], 300)  # All 300 chips go to user
            self.assertFalse(self.poll_manager.poll_data["active"])
    
    def test_has_active_poll(self):
        # Initially no active poll
        has_poll = asyncio.run(self.poll_manager.has_active_poll())
        self.assertFalse(has_poll)
        
        # Create a poll
        with patch.object(self.poll_manager, '_save_poll', return_value=True):
            asyncio.run(self.poll_manager.create_poll("Test Question", "Option A", "Option B"))
            
            # Should now have an active poll
            has_poll = asyncio.run(self.poll_manager.has_active_poll())
            self.assertTrue(has_poll)
    
    def test_is_poll_closed(self):
        # Create a poll
        with patch.object(self.poll_manager, '_save_poll', return_value=True):
            asyncio.run(self.poll_manager.create_poll("Test Question", "Option A", "Option B"))
            
            # Poll should be open initially
            is_closed = asyncio.run(self.poll_manager.is_poll_closed())
            self.assertFalse(is_closed)
            
            # Close the poll
            asyncio.run(self.poll_manager.close_poll())
            
            # Poll should now be closed
            is_closed = asyncio.run(self.poll_manager.is_poll_closed())
            self.assertTrue(is_closed)
    
    def test_get_poll_data(self):
        # Create a poll
        with patch.object(self.poll_manager, '_save_poll', return_value=True):
            asyncio.run(self.poll_manager.create_poll("Test Question", "Option A", "Option B"))
            
            # Get poll data
            poll_data = asyncio.run(self.poll_manager.get_poll_data())
            
            # Verify data
            self.assertEqual(poll_data["question"], "Test Question")
            self.assertIn("Option A", poll_data["options"])
            self.assertIn("Option B", poll_data["options"])
            self.assertTrue(poll_data["active"])
            self.assertFalse(poll_data["closed"])

if __name__ == '__main__':
    unittest.main()