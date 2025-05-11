# database.py

import motor.motor_asyncio
from config import DB_NAME, DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.chat_col = self.db.chats

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            session = None,
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    # Chat-related methods
    async def add_chat(self, chat_id):
        exists = await self.chat_col.find_one({'id': int(chat_id)})
        if not exists:
            await self.chat_col.insert_one({
                'id': int(chat_id),
                'custom_approve_message': None
            })

    async def total_chats_count(self):
        count = await self.chat_col.count_documents({})
        return count

    async def get_all_chats(self):
        return self.chat_col.find({})
    
    # Custom approval message methods
    async def set_custom_approve_message(self, chat_id, message):
        exists = await self.chat_col.find_one({'id': int(chat_id)})
        if exists:
            await self.chat_col.update_one(
                {'id': int(chat_id)}, 
                {'$set': {'custom_approve_message': message}}
            )
        else:
            await self.chat_col.insert_one({
                'id': int(chat_id),
                'custom_approve_message': message
            })
    
    async def get_custom_approve_message(self, chat_id):
        chat = await self.chat_col.find_one({'id': int(chat_id)})
        if chat and 'custom_approve_message' in chat:
            return chat['custom_approve_message']
        return None
    
    async def reset_custom_approve_message(self, chat_id):
        await self.chat_col.update_one(
            {'id': int(chat_id)}, 
            {'$unset': {'custom_approve_message': ""}}
        )

db = Database(DB_URI, DB_NAME)
