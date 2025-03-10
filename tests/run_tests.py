import unittest
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests.test_chip_manager import TestChipManager
from tests.test_poll_manager import TestPollManager
from tests.test_game_mechanics import TestGameMechanics

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add tests (updated to use the recommended approach)
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestChipManager))
    test_suite.addTest(loader.loadTestsFromTestCase(TestPollManager))
    test_suite.addTest(loader.loadTestsFromTestCase(TestGameMechanics))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())