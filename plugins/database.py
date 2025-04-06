# database.py

import motor.motor_asyncio
from config import DB_NAME, DB_URI

class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.user
        self.chat = self.db.chat
        
    def new_user(self, id):
        return dict(_id=int(id))
            
    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)            
            await self.send_user_log(b, u)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        await self.col.delete_many({'_id': int(user_id)})
    
    async def add_chat(self, b, m):
        # Corrected to use is_chat_exist instead of is_user_exist
        if not await self.is_chat_exist(m.chat.id):
            user = self.new_user(m.chat.id)
            try:
                await self.chat.insert_one(user)            
                await self.send_chat_log(b, m)
            except motor.motor_asyncio.AsyncIOMotorDuplicateKeyError:
                # Handle case where chat was added between check and insert
                pass

    async def is_chat_exist(self, id):
        user = await self.chat.find_one({'_id': int(id)})
        return bool(user)

    async def total_chats_count(self):
        count = await self.chat.count_documents({})
        return count

    async def get_all_chats(self):
        all_users = self.chat.find({})
        return all_users

    async def delete_chat(self, user_id):
        await self.chat.delete_many({'_id': int(user_id)})

db = Database(DB_URI, DB_NAME)
