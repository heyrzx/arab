import asyncio 
from pyrogram import Client, filters, enums
from config import LOG_CHANNEL, API_ID, API_HASH, NEW_REQ_MODE
from plugins.database import db
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LOG_TEXT = """<b>#NewUser
    
ID - <code>{}</code>

Name - {}</b>
"""

@Client.on_message(filters.command('start'))
async def start_message(c,m):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name)
        await c.send_message(LOG_CHANNEL, LOG_TEXT.format(m.from_user.id, m.from_user.mention))
    await m.reply(
        text=f"<b>Hello {m.from_user.mention} 👋\n\nI Am Join Request Acceptor Bot. I Can Accept All Old Pending & New Join Request In Your Groups/Channels.\n\nFor All Pending Join Request Use - /accept\n\nFor New Join Request Add Me To Your Chat And Promote Me To Admin With Add Members Permission\n\nTo Set Custom Approval Message Use - /setmessage</b>",
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton('🍃 ᴊᴏɪɴ ᴜᴩᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 🍃', url='https://t.me/ck_linkz')
            ]]
        )
    )

@Client.on_message(filters.command('accept') & filters.private)
async def accept(client, message):
    show = await message.reply("**Please Wait.....**")
    user_data = await db.get_session(message.from_user.id)
    if user_data is None:
        await show.edit("**For Accepte Pending Request You Have To /login First.**")
        return
    try:
        acc = Client("joinrequest", session_string=user_data, api_hash=API_HASH, api_id=API_ID)
        await acc.connect()
    except:
        return await show.edit("**Your Login Session Expired. So /logout First Then Login Again By - /login**")
    show = await show.edit("**Now Forward A Message From Your Channel Or Group With Forward Tag\n\nMake Sure Your Logged In Account Is Admin In That Channel Or Group With Full Rights.**")
    vj = await client.listen(message.chat.id)
    if vj.forward_from_chat and not vj.forward_from_chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
        chat_id = vj.forward_from_chat.id
        try:
            info = await acc.get_chat(chat_id)
        except:
            await show.edit("**Error - Make Sure Your Logged In Account Is Admin In This Channel Or Group With Rights.**")
    else:
        return await message.reply("**Message Not Forwarded From Channel Or Group.**")
    await vj.delete()
    msg = await show.edit("**Accepting all join requests... Please wait until it's completed.**")
    try:
        while True:
            await acc.approve_all_chat_join_requests(chat_id)
            await asyncio.sleep(2)
            join_requests = [request async for request in acc.get_chat_join_requests(chat_id)]
            if not join_requests:
                break
        await msg.edit("**Successfully accepted all join requests.**")
    except Exception as e:
        await msg.edit(f"**An error occurred:** {str(e)}")

@Client.on_message(filters.command('setmessage'))
async def set_message(client, message):
    """Set custom approval message for a group"""
    user_id = message.from_user.id
    
    # Handle command in group chat
    if message.chat.type != enums.ChatType.PRIVATE:
        chat_id = message.chat.id
        
        # Check if user is admin in this group
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if not member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await message.reply("**You must be an admin to use this command.**")
        except Exception as e:
            return await message.reply(f"**Error checking permissions:** {str(e)}")
        
        # Get custom message text
        if len(message.command) == 1:
            return await message.reply("**Please provide a message to set.\n\nUsage: /setmessage Your custom welcome message\n\nYou can use {mention} to tag the user and {chat} for the chat name.**")
        
        custom_message = message.text.split(None, 1)[1]
        
        # Save to database
        await db.set_custom_approve_message(chat_id, custom_message)
        await message.reply("**✅ Custom approval message has been set successfully!**")
        
        # Show preview
        preview = custom_message.replace("{mention}", message.from_user.mention).replace("{chat}", message.chat.title)
        await message.reply(f"**Preview of your custom message:**\n\n{preview}")
    
    # Handle command in private chat
    else:
        # Ask user to forward a message from the group
        msg = await message.reply("**Please forward a message from the group/channel where you want to set the custom welcome message. Make sure the bot is admin in that group.**")
        
        # Wait for user to forward a message
        try:
            forwarded = await client.listen(message.chat.id, timeout=60)
            
            # Check if it's a forwarded message from a group/channel
            if forwarded.forward_from_chat and forwarded.forward_from_chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                chat_id = forwarded.forward_from_chat.id
                chat_title = forwarded.forward_from_chat.title
                
                # Check if user is admin in that group
                try:
                    member = await client.get_chat_member(chat_id, user_id)
                    if not member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                        return await msg.edit("**You must be an admin in that group/channel to set the welcome message.**")
                except Exception as e:
                    return await msg.edit(f"**Error checking permissions: {str(e)}\nMake sure the bot is admin in the group/channel.**")
                
                # Ask for the custom message
                await msg.edit(f"**Now, please send the custom welcome message for {chat_title}.\n\nYou can use:\n- {{mention}} to tag the user\n- {{chat}} for the chat name**")
                
                # Wait for the custom message
                try:
                    custom_msg_response = await client.listen(message.chat.id, timeout=120)
                    custom_message = custom_msg_response.text
                    
                    # Save to database
                    await db.set_custom_approve_message(chat_id, custom_message)
                    await message.reply(f"**✅ Custom approval message has been set for {chat_title}!**")
                    
                    # Show preview
                    preview = custom_message.replace("{mention}", message.from_user.mention).replace("{chat}", chat_title)
                    await message.reply(f"**Preview of your custom message:**\n\n{preview}")
                    
                except asyncio.TimeoutError:
                    await msg.edit("**No message received. Command canceled.**")
            else:
                await msg.edit("**That wasn't a forwarded message from a group or channel. Please try again with /setmessage.**")
        
        except asyncio.TimeoutError:
            await msg.edit("**No message received. Command canceled.**")

@Client.on_message(filters.command('viewmessage'))
async def view_message(client, message):
    """View current custom approval message"""
    # Handle command in group chat
    if message.chat.type != enums.ChatType.PRIVATE:
        chat_id = message.chat.id
        custom_message = await db.get_custom_approve_message(chat_id)
        
        if custom_message:
            preview = custom_message.replace("{mention}", message.from_user.mention).replace("{chat}", message.chat.title)
            await message.reply(f"**Current custom message:**\n\n{preview}")
        else:
            await message.reply("**No custom message is set for this chat. Default message will be used.**")
    
    # Handle command in private chat
    else:
        # Ask user to forward a message from the group
        msg = await message.reply("**Please forward a message from the group/channel where you want to view the custom welcome message.**")
        
        # Wait for user to forward a message
        try:
            forwarded = await client.listen(message.chat.id, timeout=60)
            
            # Check if it's a forwarded message from a group/channel
            if forwarded.forward_from_chat and forwarded.forward_from_chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                chat_id = forwarded.forward_from_chat.id
                chat_title = forwarded.forward_from_chat.title
                
                # Get custom message
                custom_message = await db.get_custom_approve_message(chat_id)
                
                if custom_message:
                    preview = custom_message.replace("{mention}", message.from_user.mention).replace("{chat}", chat_title)
                    await msg.edit(f"**Current custom message for {chat_title}:**\n\n{preview}")
                else:
                    await msg.edit(f"**No custom message is set for {chat_title}. Default message will be used.**")
            else:
                await msg.edit("**That wasn't a forwarded message from a group or channel. Please try again with /viewmessage.**")
        
        except asyncio.TimeoutError:
            await msg.edit("**No message received. Command canceled.**")

@Client.on_message(filters.command('resetmessage') & filters.group)
async def reset_message(client, message):
    """Reset custom approval message to default"""
    # Check if user is admin
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if not member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return await message.reply("**You must be an admin to use this command.**")
    except Exception as e:
        return await message.reply(f"**Error checking permissions:** {str(e)}")
    
    await db.reset_custom_approve_message(chat_id)
    await message.reply("**✅ Custom message has been reset. Default message will be used.**")

@Client.on_chat_join_request(filters.group | filters.channel)
async def approve_new(client, m):
    if not NEW_REQ_MODE:
        return 
    try:
        if not await db.is_user_exist(m.from_user.id):
            await db.add_user(m.from_user.id, m.from_user.first_name)
            await client.send_message(
                LOG_CHANNEL, 
                LOG_TEXT.format(m.from_user.id, m.from_user.mention)
            )
        
        # Approve the join request
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        
        # Get custom approval message if available
        custom_message = await db.get_custom_approve_message(m.chat.id)
        
        # Welcome message with a button
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🍃 ᴊᴏɪɴ ᴜᴩᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 🍃", url="https://t.me/ck_linkz")]
            ]
        )
        
        try:
            # Use custom message if available, otherwise use default
            if custom_message:
                welcome_text = custom_message.replace("{mention}", m.from_user.mention).replace("{chat}", m.chat.title)
                welcome_text = f"{welcome_text}\n\n__Powered By : @ck_linkz__"
            else:
                welcome_text = "**Hello {}!\nWelcome To {}\n\n__Powered By : @ck_linkz__**".format(
                    m.from_user.mention, m.chat.title)
                
            await client.send_message(
                m.from_user.id,
                welcome_text,
                reply_markup=keyboard
            )
        except:
            pass
    except Exception as e:
        print(str(e))
        pass
