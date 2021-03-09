import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from MeguminRobot import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    DRAGONS,
    DEMONS,
    TIGERS,
    WOLVES,
    dispatcher,
)
from MeguminRobot.modules.disable import DisableAbleCommandHandler
from MeguminRobot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
    user_can_ban,
    can_delete,
)
from MeguminRobot.modules.helper_funcs.extraction import extract_user_and_text
from MeguminRobot.modules.helper_funcs.string_handling import extract_time
from MeguminRobot.modules.log_channel import gloggable, loggable


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Saya ragu itu adalah pengguna.")
        return log_message
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Pengguna tidak ditemukan ":
            raise
        message.reply_text("Sepertinya tidak dapat menemukan orang ini.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Oh ya, larang diriku sendiri, baka!")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("Mencoba menempatkanku pada bencana tingkat Dewa ya?")
        elif user_id in DEV_USERS:
            message.reply_text("Aku tidak bisa melawan kita sendiri.")
        elif user_id in DRAGONS:
            message.reply_text(
                "Melawan Naga ini di sini akan membahayakan nyawa warga sipil."
            )
        elif user_id in DEMONS:
            message.reply_text(
                "Bawalah perintah dari asosiasi Pahlawan untuk melawan bencana Iblis."
            )
        elif user_id in TIGERS:
            message.reply_text(
                "Bawa perintah dari asosiasi Pahlawan untuk melawan bencana Harimau."
            )
        elif user_id in WOLVES:
            message.reply_text("Kemampuan serigala membuat mereka kebal!")
        else:
            message.reply_text("Pengguna ini memiliki kekebalan dan tidak dapat diblokir.")
        return log_message
    if message.text.startswith("/s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False
    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{'S' if silent else ''}BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)

        if silent:
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.delete()
            return log

        reply = (
            f"<code>❕</code><b>Ban Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            reply += f"\n<code> </code><b>•  Reason:</b> \n{html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML, quote=False)
        return log

    except BadRequest as excp:
        if excp.message == "Pesan balasan tidak ditemukan":
            # Jangan dibalas
            if silent:
                return log
            message.reply_text("Banned!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Uhm ... itu tidak berhasil ...")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Saya ragu itu adalah pengguna.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Pengguna tidak ditemukan":
            raise
        message.reply_text("Saya tidak dapat menemukan pengguna ini.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Aku tidak akan melarang diriku sendiri, apakah kamu gila?")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Saya tidak merasa seperti itu.")
        return log_message

    if not reason:
        message.reply_text("Anda belum menentukan waktu untuk mencekal pengguna ini!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)

        bot.sendMessage(
            chat.id,
            f"Banned! Pengguna {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"akan dilarang selama {time_val}.",
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Pesan balasan tidak ditemukan":
            # Jangan dibalas
            message.reply_text(
                f"Banned! Pengguna akan diblokir {time_val}.", quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Sial, saya tidak bisa melarang pengguna itu.")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def punch(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Saya ragu itu adalah pengguna.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Pengguna tidak ditemukan":
            raise

        message.reply_text("Saya tidak dapat menemukan pengguna ini.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Yeahhh aku tidak akan melakukan itu.")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Saya benar-benar berharap bisa membunuh pengguna ini....")
        return log_message

    res = chat.unban_member(user_id)  
    if res:

        bot.sendMessage(
            chat.id,
            f"Satu tebasan! {mention_html(member.user.id, html.escape(member.user.first_name))}.",
            parse_mode=ParseMode.HTML,
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        message.reply_text("Sial, aku tidak bisa membunuh pengguna itu.")

    return log_message


@run_async
@bot_admin
@can_restrict
def punchme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Saya berharap saya bisa ... tetapi Anda adalah seorang admin.")
        return

    res = update.effective_chat.unban_member(user_id)  
    if res:
        update.effective_message.reply_text("*menendang Anda keluar dari grup*")
    else:
        update.effective_message.reply_text("Huh? aku bisa :/")


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Saya ragu itu adalah pengguna.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Pengguna tidak detemukan":
            raise
        message.reply_text("Saya tidak dapat menemukan pengguna ini.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Bagaimana saya membatalkan pelarangan diri saya sendiri jika saya tidak ada di sini ...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("Bukankah orang ini sudah ada di sini??")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("Ya, pengguna ini dapat bergabung!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    return log


@run_async
@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(context: CallbackContext, update: Update) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in DRAGONS or user.id not in TIGERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("Berikan ID obrolan yang valid.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "Pengguna tidak ditemukan":
            message.reply_text("Saya tidak dapat menemukan pengguna ini.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("Bukankah kamu sudah mengobrol??")
        return

    chat.unban_member(user.id)
    message.reply_text("Ya, saya telah membatalkan pencekalan Anda.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


__help__ = """
 • `/punchme`*:* meninju pengguna yang mengeluarkan perintah

*Admins only:*
 • `/ban <userhandle>`*:* melarang pengguna.  (melalui pegangan, atau balasan)
 • `/sban <userhandle>`*:* Cekal pengguna secara diam-diam.  Menghapus perintah, membalas pesan dan tidak membalas.  (melalui pegangan, atau balasan)
 • `/tban <userhandle> x(m/h/d)`*:* melarang pengguna untuk waktu `x`.  (melalui pegangan, atau balasan).  `m` =` menit`, `h` =` jam`, `d` =` hari`.
 • `/unban <userhandle>`*:* batalkan larangan pengguna.  (melalui pegangan, atau balasan)
 • `/punch <userhandle>`*:* Meninju pengguna keluar dari grup, (melalui pegangan, atau balasan)
"""

BAN_HANDLER = CommandHandler(["ban", "sban"], ban)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban)
PUNCH_HANDLER = CommandHandler("punch", punch)
UNBAN_HANDLER = CommandHandler("unban", unban)
ROAR_HANDLER = CommandHandler("roar", selfunban)
PUNCHME_HANDLER = DisableAbleCommandHandler("punchme", punchme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(PUNCH_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(PUNCHME_HANDLER)

__mod_name__ = "Bans"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    PUNCH_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    PUNCHME_HANDLER,
]
