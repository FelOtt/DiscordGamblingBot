import json
import os
import asyncio

class PollManager:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PollManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.poll_file = 'poll.json'
        self.poll_data = {}
        self._load_poll()
        
    def _load_poll(self):
        """Load poll data from file"""
        try:
            if os.path.exists(self.poll_file):
                with open(self.poll_file, 'r') as f:
                    self.poll_data = json.load(f)
        except Exception as e:
            print(f"Error loading poll: {e}")
            self.poll_data = {}
    
    async def _save_poll(self):
        """Save poll data to file"""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._save_poll_sync)
            return True
        except Exception as e:
            print(f"Error saving poll: {e}")
            return False
    
    def _save_poll_sync(self):
        """Synchronous helper for _save_poll"""
        with open(self.poll_file, 'w') as f:
            json.dump(self.poll_data, f)
    
    async def has_active_poll(self):
        """Check if there is an active poll"""
        async with self._lock:
            return self.poll_data.get("active", False)
    
    async def is_poll_closed(self):
        """Check if the active poll is closed"""
        async with self._lock:
            return self.poll_data.get("closed", True)
    
    async def create_poll(self, question, option1, option2):
        """Create a new poll"""
        async with self._lock:
            if self.poll_data.get("active", False):
                return False, "There is already an active poll!"
            
            self.poll_data = {
                "active": True,
                "closed": False,
                "question": question,
                "options": {option1: {}, option2: {}},
                "total_bets": 0
            }
            
            await self._save_poll()
            return True, None
    
    async def close_poll(self):
        """Close an active poll for betting"""
        async with self._lock:
            if not self.poll_data.get("active", False):
                return False, "There is no active poll to close!"
            
            if self.poll_data.get("closed", True):
                return False, "The poll is already closed!"
            
            self.poll_data["closed"] = True
            await self._save_poll()
            return True, None
    
    async def end_poll(self, winning_option):
        """End a poll and return user payouts"""
        async with self._lock:
            if not self.poll_data.get("active", False):
                return False, "There is no active poll to end!", {}
            
            if winning_option not in self.poll_data["options"]:
                return False, "Invalid winning option!", {}
            
            total_winning_bets = sum(self.poll_data["options"][winning_option].values())
            total_pot = self.poll_data["total_bets"]
            
            payouts = {}
            if total_winning_bets > 0:
                # Calculate payouts for winners
                for user_id, bet in self.poll_data["options"][winning_option].items():
                    win_share = (bet / total_winning_bets) * total_pot
                    payouts[user_id] = int(win_share)
            
            self.poll_data["active"] = False
            await self._save_poll()
            
            return True, winning_option, payouts
    
    async def place_bet(self, user_id, option, amount):
        """Place a bet on a poll option"""
        async with self._lock:
            user_id = str(user_id)
            
            if not self.poll_data.get("active", False):
                return False, "There is no active poll!"
            
            if self.poll_data.get("closed", True):
                return False, "The poll is closed!"
            
            if option not in self.poll_data["options"]:
                return False, "Invalid option!"
            
            # Check if the user already bet on a different option
            already_bet_on = None
            for opt, bets in self.poll_data["options"].items():
                if user_id in bets:
                    already_bet_on = opt
                    break
            
            if already_bet_on and already_bet_on != option:
                return False, f"You have already bet on '{already_bet_on}', you cannot switch options!"
            
            # Add bet to poll data
            self.poll_data["options"][option][user_id] = self.poll_data["options"][option].get(user_id, 0) + amount
            self.poll_data["total_bets"] += amount
            
            await self._save_poll()
            return True, None
    
    async def get_poll_data(self):
        """Get current poll data"""
        async with self._lock:
            return self.poll_data.copy()