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
async def start_message(c, m):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name)
        await c.send_message(LOG_CHANNEL, LOG_TEXT.format(m.from_user.id, m.from_user.mention))

    start_text = f"""<b>Hello {m.from_user.mention} 👋

I'm a smart Join Request Manager Bot built to help you manage join requests in your Telegram Groups and Channels effortlessly.

<b>What I Can Do:</b>
• Automatically approve new join requests.
• Instantly accept all old/pending requests.
• Let you set a custom welcome message.
• Work in both groups and channels.
• Ensure a smooth onboarding experience for new members.

Tap the <u>"How To Use Me"</u> button below to learn how to get started!

<b>Powered By:</b> @ck_linkz</b>
"""

    await m.reply(
        text=start_text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🍃 ᴊᴏɪɴ ᴜᴩᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 🍃", url="https://t.me/ck_linkz")],
                [InlineKeyboardButton("♻️ ʜᴏᴡ ᴛᴏ ᴜꜱᴇ ᴍᴇ ♻️", callback_data="help")]
            ]
        )
    )


@Client.on_callback_query(filters.regex("help"))
async def help_callback(client, callback_query):
    text = """<b>Available Commands:</b>

/accept - Accept all pending join requests (Login required)
/setmessage - Set a custom welcome message (in group or forward in PM)
/viewmessage - View the current welcome message
/resetmessage - Reset the welcome message to default (Group only)
/login - Login to use admin commands (if implemented)
/logout - Logout your session (if implemented)

<b>Note:</b>
- Use /setmessage and /viewmessage in groups or by forwarding a message from that group to the bot in PM.
- You must be an admin to change or reset welcome messages.
"""
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]
            ]
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
    user_id = message.from_user.id

    if message.chat.type != enums.ChatType.PRIVATE:
        chat_id = message.chat.id
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if not member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await message.reply("**You must be an admin to use this command.**")
        except Exception as e:
            return await message.reply(f"**Error checking permissions:** {str(e)}")

        if len(message.command) == 1:
            return await message.reply("**Please provide a message to set.\n\nUsage: /setmessage Your custom welcome message\n\nYou can use {mention} to tag the user and {chat} for the chat name.**")

        custom_message = message.text.split(None, 1)[1]
        await db.set_custom_approve_message(chat_id, custom_message)
        await message.reply("**✅ Custom approval message has been set successfully!**")
        preview = custom_message.replace("{mention}", message.from_user.mention).replace("{chat}", message.chat.title)
        await message.reply(f"**Preview of your custom message:**\n\n{preview}")
    
    else:
        msg = await message.reply("**Please forward a message from the group/channel where you want to set the custom welcome message. Make sure the bot is admin in that group.**")

        try:
            forwarded = await client.listen(message.chat.id)
            if forwarded.forward_from_chat and forwarded.forward_from_chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                chat_id = forwarded.forward_from_chat.id
                chat_title = forwarded.forward_from_chat.title

                try:
                    member = await client.get_chat_member(chat_id, user_id)
                    if not member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                        return await msg.edit("**You must be an admin in that group/channel to set the welcome message.**")
                except Exception as e:
                    return await msg.edit(f"**Error checking permissions: {str(e)}\nMake sure the bot is admin in the group/channel.**")

                await msg.edit(f"**Now, please send the custom welcome message for {chat_title}.\n\nYou can use:\n- {{mention}} to tag the user\n- {{chat}} for the chat name**")
                custom_msg_response = await client.listen(message.chat.id)
                custom_message = custom_msg_response.text
                await db.set_custom_approve_message(chat_id, custom_message)
                await message.reply(f"**✅ Custom approval message has been set for {chat_title}!**")
                preview = custom_message.replace("{mention}", message.from_user.mention).replace("{chat}", chat_title)
                await message.reply(f"**Preview of your custom message:**\n\n{preview}")
            else:
                await msg.edit("**That wasn't a forwarded message from a group or channel. Please try again with /setmessage.**")

        except asyncio.TimeoutError:
            await msg.edit("**No message received. Command canceled.**")

@Client.on_message(filters.command('viewmessage'))
async def view_message(client, message):
    user_id = message.from_user.id

    # If used in a group
    if message.chat.type != enums.ChatType.PRIVATE:
        chat_id = message.chat.id
        
        # Check if user is admin
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await message.reply("**Only group admins can view the custom welcome message.**")
        except Exception as e:
            return await message.reply(f"**Error checking admin status:** {str(e)}")

        custom_message = await db.get_custom_approve_message(chat_id)
        if custom_message:
            preview = custom_message.replace("{mention}", message.from_user.mention).replace("{chat}", message.chat.title)
            await message.reply(f"**Current custom message:**\n\n{preview}")
        else:
            await message.reply("**No custom message is set for this chat. Default message will be used.**")

    # If used in private
    else:
        msg = await message.reply("**Please forward a message from the group/channel where you want to view the custom welcome message.**")

        try:
            forwarded = await client.listen(message.chat.id)
            if forwarded.forward_from_chat and forwarded.forward_from_chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                chat_id = forwarded.forward_from_chat.id
                chat_title = forwarded.forward_from_chat.title

                # Check if user is admin in the forwarded group
                try:
                    member = await client.get_chat_member(chat_id, user_id)
                    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                        return await msg.edit("**Only group admins can view the welcome message.**")
                except Exception as e:
                    return await msg.edit(f"**Error checking admin status: {str(e)}**")

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

@Client.on_message(filters.command('resetmessage'))
async def reset_message(client, message):
    user_id = message.from_user.id

    if message.chat.type != enums.ChatType.PRIVATE:
        # Group chat
        chat_id = message.chat.id
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                return await message.reply("**You must be an admin to use this command.**")
        except Exception as e:
            return await message.reply(f"**Error checking permissions:** {str(e)}")

        await db.reset_custom_approve_message(chat_id)
        await message.reply("**✅ Custom message has been reset. Default message will be used.**")
    else:
        # PM: ask to forward a message from group
        msg = await message.reply("**Please forward a message from the group/channel where you want to reset the welcome message.**")

        try:
            forwarded = await client.listen(message.chat.id)
            if forwarded.forward_from_chat and forwarded.forward_from_chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                chat_id = forwarded.forward_from_chat.id

                try:
                    member = await client.get_chat_member(chat_id, user_id)
                    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                        return await msg.edit("**You must be an admin in that group/channel to reset the message.**")
                except Exception as e:
                    return await msg.edit(f"**Error checking admin status: {str(e)}**")

                await db.reset_custom_approve_message(chat_id)
                await msg.edit("**✅ Custom message has been reset for that group. Default message will be used.**")
            else:
                await msg.edit("**That wasn't a forwarded message from a group or channel. Please try again with /resetmessage.**")
        except asyncio.TimeoutError:
            await msg.edit("**No message received. Command canceled.**")

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
        
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        custom_message = await db.get_custom_approve_message(m.chat.id)
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🍃 ᴊᴏɪɴ ᴜᴩᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ 🍃", url="https://t.me/ck_linkz")]
            ]
        )
        try:
            if custom_message:
                welcome_text = custom_message.replace("{mention}", m.from_user.mention).replace("{chat}", m.chat.title)
                welcome_text = f"{welcome_text}"
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
