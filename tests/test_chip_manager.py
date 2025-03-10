import unittest
import asyncio
import os
import json
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chip_manager import ChipManager

class TestChipManager(unittest.TestCase):
    def setUp(self):
        # Create a test file
        self.test_file = 'test_chips.json'
        
        # Reset the singleton instance for clean tests
        ChipManager._instance = None
        
        # Create a new instance with a mocked _initialize
        with patch.object(ChipManager, '_initialize') as mock_init:
            self.chip_manager = ChipManager()
            # Manually set attributes that would be set in _initialize
            self.chip_manager.users = {}
            self.chip_manager.default_chips = 1000
            self.chip_manager.chip_file = self.test_file
        
        # Sample test data
        self.test_data = {
            '123456': 1000,
            '789012': 500,
            '345678': 0
        }
        
        # Write test data to file
        with open(self.test_file, 'w') as f:
            json.dump(self.test_data, f)
        
        # Load the test data
        self.chip_manager._load_chips()
    
    def tearDown(self):
        # Remove test file
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_get_chips(self):
        result = asyncio.run(self.chip_manager.get_chips('123456'))
        self.assertEqual(result, 1000)
        
        # Test with non-existent user (should create with default)
        result = asyncio.run(self.chip_manager.get_chips('999999'))
        self.assertEqual(result, 1000)  # Default value
    
    def test_set_chips(self):
        # Set chips for existing user
        asyncio.run(self.chip_manager.set_chips('123456', 2000))
        self.assertEqual(self.chip_manager.users['123456'], 2000)
        
        # Set chips for new user
        asyncio.run(self.chip_manager.set_chips('999999', 500))
        self.assertEqual(self.chip_manager.users['999999'], 500)
    
    def test_add_chips(self):
        # Add to existing user
        asyncio.run(self.chip_manager.add_chips('123456', 500))
        self.assertEqual(self.chip_manager.users['123456'], 1500)
        
        # Add to new user
        asyncio.run(self.chip_manager.add_chips('999999', 500))
        self.assertEqual(self.chip_manager.users['999999'], 1500)  # Default + amount
    
    def test_remove_chips(self):
        # Test successful removal
        result = asyncio.run(self.chip_manager.remove_chips('123456', 300))
        self.assertTrue(result)
        self.assertEqual(self.chip_manager.users['123456'], 700)
        
        # Test removal with insufficient funds
        result = asyncio.run(self.chip_manager.remove_chips('789012', 600))
        self.assertFalse(result)
        self.assertEqual(self.chip_manager.users['789012'], 500)  # Unchanged
    
    def test_transfer_chips(self):
        # Test successful transfer
        result = asyncio.run(self.chip_manager.transfer_chips('123456', '789012', 300))
        self.assertTrue(result)
        self.assertEqual(self.chip_manager.users['123456'], 700)
        self.assertEqual(self.chip_manager.users['789012'], 800)
        
        # Test transfer with insufficient funds
        result = asyncio.run(self.chip_manager.transfer_chips('789012', '123456', 1000))
        self.assertFalse(result)
        self.assertEqual(self.chip_manager.users['789012'], 800)  # Unchanged
        self.assertEqual(self.chip_manager.users['123456'], 700)  # Unchanged
    
    def test_get_top_users(self):
        # Add more users for testing
        self.chip_manager.users['111111'] = 1500
        self.chip_manager.users['222222'] = 1200
        
        # Get top 2 users
        result = asyncio.run(self.chip_manager.get_top_users(2))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], '111111')
        self.assertEqual(result[0][1], 1500)
        self.assertEqual(result[1][0], '222222')
        self.assertEqual(result[1][1], 1200)
        
        # Test exclusion
        result = asyncio.run(self.chip_manager.get_top_users(2, ['111111']))
        self.assertEqual(result[0][0], '222222')
        self.assertEqual(result[0][1], 1200)
    
    def test_get_user_rank(self):
        # Add more users for testing
        self.chip_manager.users['111111'] = 1500
        self.chip_manager.users['222222'] = 1200
        
        # Test ranks
        rank = asyncio.run(self.chip_manager.get_user_rank('111111'))
        self.assertEqual(rank, 1)
        
        rank = asyncio.run(self.chip_manager.get_user_rank('123456'))
        self.assertEqual(rank, 3)
        
        # Test non-existent user
        rank = asyncio.run(self.chip_manager.get_user_rank('999999'))
        self.assertIsNone(rank)
    
    def test_get_broke_users(self):
        result = asyncio.run(self.chip_manager.get_broke_users())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], '345678')
    
    def test_reset_broke_users(self):
        # Add another broke user
        self.chip_manager.users['555555'] = 0
        
        # Mock the _save_chips method to avoid actual file operations
        with patch.object(self.chip_manager, '_save_chips', return_value=True):
            count = asyncio.run(self.chip_manager.reset_broke_users())
            self.assertEqual(count, 2)
            self.assertEqual(self.chip_manager.users['345678'], 1000)
            self.assertEqual(self.chip_manager.users['555555'], 1000)

if __name__ == '__main__':
    unittest.main()