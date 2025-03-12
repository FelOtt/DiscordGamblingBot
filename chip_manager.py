import json
import os
import asyncio

from dotenv import load_dotenv

class ChipManager:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChipManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.users = {}
        self.default_chips = os.getenv('DEFAULT_CHIPS', 1000)
        self.chip_file = 'chips.json'
        self._load_chips()
        
    def _load_chips(self):
        """Load chips data from file"""
        try:
            if os.path.exists(self.chip_file):
                with open(self.chip_file, 'r') as f:
                    self.users = json.load(f)
        except Exception as e:
            print(f"Error loading chips: {e}")
            self.users = {}
    
    async def _save_chips(self):
        """Save chips data to file without re-acquiring the lock"""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._save_chips_sync)
            return True
        except Exception as e:
            print(f"Error saving chips: {e}")
            return False
    
    def _save_chips_sync(self):
        """Synchronous helper for _save_chips"""
        with open(self.chip_file, 'w') as f:
            json.dump(self.users, f)
    
    async def get_chips(self, user_id):
        """Get a user's chips, initializing if needed - with locking"""
        async with self._lock:
            user_id = str(user_id)
            if user_id not in self.users:
                self.users[user_id] = self.default_chips
                await self._save_chips()
            return self.users[user_id]
    
    async def set_chips(self, user_id, amount):
        """Set a user's chips to a specific amount"""
        async with self._lock:
            user_id = str(user_id)
            self.users[user_id] = amount
            return await self._save_chips()
    
    async def add_chips(self, user_id, amount):
        """Add chips to a user's balance"""
        async with self._lock:
            user_id = str(user_id)
            if user_id not in self.users:
                self.users[user_id] = self.default_chips
            self.users[user_id] += amount
            return await self._save_chips()
    
    async def remove_chips(self, user_id, amount):
        """Remove chips from a user's balance if they have enough"""
        async with self._lock:
            user_id = str(user_id)
            if user_id not in self.users:
                self.users[user_id] = self.default_chips
            current = self.users[user_id]
            if current < amount:
                return False
            self.users[user_id] -= amount
            await self._save_chips()
            return True
    
    async def transfer_chips(self, from_user, to_user, amount):
        """Transfer chips between users without nested locking"""
        async with self._lock:
            from_user = str(from_user)
            to_user = str(to_user)
            if from_user not in self.users:
                self.users[from_user] = self.default_chips
            if to_user not in self.users:
                self.users[to_user] = self.default_chips
                
            if self.users[from_user] < amount:
                return False
                
            self.users[from_user] -= amount
            self.users[to_user] += amount
            await self._save_chips()
            return True
    
    async def get_top_users(self, count=10, exclude_ids=None):
        """Get top users by chip count, optionally excluding certain users"""
        async with self._lock:
            exclude_ids = exclude_ids or []
            filtered_users = {uid: chips for uid, chips in self.users.items() if uid not in exclude_ids}
            sorted_users = sorted(filtered_users.items(), key=lambda x: x[1], reverse=True)
            return sorted_users[:count]
    
    async def get_user_rank(self, user_id):
        """Get a user's rank in the leaderboard"""
        async with self._lock:
            user_id = str(user_id)
            sorted_users = sorted(self.users.items(), key=lambda x: x[1], reverse=True)
            for i, (uid, _) in enumerate(sorted_users):
                if uid == user_id:
                    return i + 1
            return None
    
    async def get_broke_users(self):
        """Get all users with 0 chips"""
        async with self._lock:
            return [user for user, chips in self.users.items() if chips == 0]
    
    async def reset_broke_users(self):
        """Reset all broke users to default chip count without nested locking"""
        async with self._lock:
            broke_users = [user for user, chips in self.users.items() if chips == 0]
            for user in broke_users:
                self.users[user] = self.default_chips
            await self._save_chips()
            return len(broke_users)