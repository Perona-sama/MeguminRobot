import json, time, os
from io import BytesIO

from telegram import ParseMode, Message
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async

import MeguminRobot.modules.sql.notes_sql as sql
from MeguminRobot import dispatcher, LOGGER, OWNER_ID, JOIN_LOGGER, SUPPORT_CHAT
from MeguminRobot.__main__ import DATA_IMPORT
from MeguminRobot.modules.helper_funcs.chat_status import user_admin
from MeguminRobot.modules.helper_funcs.alternate import typing_action

import MeguminRobot.modules.sql.rules_sql as rulessql

import MeguminRobot.modules.sql.blacklist_sql as blacklistsql
from MeguminRobot.modules.sql import disable_sql as disabledsql

import MeguminRobot.modules.sql.locks_sql as locksql
from MeguminRobot.modules.connection import connected


@run_async
@user_admin
@typing_action
def import_data(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    # TODO: izinkan mengunggah dokumen dengan perintah, bukan hanya sebagai balasan
    # hanya bekerja dengan seorang dokter

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text("Ini adalah perintah khusus grup!")
            return ""

        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = context.bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            msg.reply_text(
                "Coba unduh dan unggah file sendiri lagi, Yang ini sepertinya rusak bagi saya!"
            )
            return

        with BytesIO() as file:
            file_info.download(out=file)
            file.seek(0)
            data = json.load(file)

        # hanya mengimpor satu grup
        if len(data) > 1 and str(chat.id) not in data:
            msg.reply_text(
                "Ada lebih dari satu grup di file ini dan chat.id tidak sama!  Bagaimana saya bisa mengimpornya?"
            )
            return

        # Periksa apakah cadangan obrolan ini
        try:
            if data.get(str(chat.id)) is None:
                if conn:
                    text = "Cadangan berasal dari obrolan lain, saya tidak dapat mengembalikan obrolan lain ke obrolan *{}*".format(
                        chat_name
                    )
                else:
                    text = "Cadangan berasal dari obrolan lain, saya tidak dapat mengembalikan obrolan lain ke obrolan ini"
                return msg.reply_text(text, parse_mode="markdown")
        except Exception:
            return msg.reply_text("Ada masalah saat mengimpor data!")
        # Periksa apakah cadangan dari diri sendiri
        try:
            if str(context.bot.id) != str(data[str(chat.id)]["bot"]):
                return msg.reply_text(
                    "Cadangan dari bot lain yang tidak disarankan dapat menyebabkan masalah, dokumen, foto, video, audio, catatan mungkin tidak berfungsi sebagaimana mestinya."
                )
        except Exception:
            pass
        # Pilih sumber data
        if str(chat.id) in data:
            data = data[str(chat.id)]["hashes"]
        else:
            data = data[list(data.keys())[0]]["hashes"]

        try:
            for mod in DATA_IMPORT:
                mod.__import_data__(str(chat.id), data)
        except Exception:
            msg.reply_text(
                f"Terjadi kesalahan saat memulihkan data Anda.  Prosesnya gagal.  Jika Anda mengalami masalah dengan ini, harap bawa ke @{SUPPORT_CHAT}"
            )

            LOGGER.exception(
                "Impor untuk obrolan %s dengan nama %s gagal.",
                str(chat.id),
                str(chat.title),
            )
            return

        # TODO: beberapa logika tautan itu
        # CATATAN: pertimbangkan hal-hal perizinan default?
        if conn:

            text = "Cadangan sepenuhnya dipulihkan pada *{}*.".format(chat_name)
        else:
            text = "Cadangan sepenuhnya dipulihkan"
        msg.reply_text(text, parse_mode="markdown")


@run_async
@user_admin
def export_data(update, context):
    chat_data = context.chat_data
    msg = update.effective_message  
    user = update.effective_user  
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    current_chat_id = update.effective_chat.id
    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn

    else:
        if update.effective_message.chat.type == "private":
            update.effective_message.reply_text("Ini adalah perintah khusus grup!")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id

    jam = time.time()
    new_jam = jam + 10800
    checkchat = get_chat(chat_id, chat_data)
    if checkchat.get("status"):
        if jam <= int(checkchat.get("value")):
            timeformatt = time.strftime(
                "%H:%M:%S %d/%m/%Y", time.localtime(checkchat.get("value"))
            )
            update.effective_message.reply_text(
                "Anda hanya dapat melakukan backup sekali sehari!\nAnda dapat mencadangkan lagi di sekitar `{}`".format(
                    timeformatt
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        else:
            if user.id != OWNER_ID:
                put_chat(chat_id, new_jam, chat_data)
    else:
        if user.id != OWNER_ID:
            put_chat(chat_id, new_jam, chat_data)

    note_list = sql.get_all_chat_notes(chat_id)
    backup = {}
    buttonlist = []
    namacat = ""
    isicat = ""
    rules = ""
    count = 0
    countbtn = 0

    for note in note_list:
        count += 1

        namacat += "{}<###splitter###>".format(note.name)
        if note.msgtype == 1:
            tombol = sql.get_buttons(chat_id, note.name)

            for btn in tombol:
                countbtn += 1
                if btn.same_line:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), True)
                    )
                else:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), False)
                    )
            isicat += "###button###: {}<###button###>{}<###splitter###>".format(
                note.value, str(buttonlist)
            )
            buttonlist.clear()
        elif note.msgtype == 2:
            isicat += "###sticker###:{}<###splitter###>".format(note.file)
        elif note.msgtype == 3:
            isicat += "###file###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 4:
            isicat += "###photo###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 5:
            isicat += "###audio###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 6:
            isicat += "###voice###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 7:
            isicat += "###video###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        elif note.msgtype == 8:
            isicat += "###video_note###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                note.file, note.value
            )
        else:
            isicat += "{}<###splitter###>".format(note.value)
    notes = {
        "#{}".format(namacat.split("<###splitter###>")[x]): "{}".format(
            isicat.split("<###splitter###>")[x]
        )
        for x in range(count)
    }
    # Rules
    rules = rulessql.get_rules(chat_id)
    # Blacklist
    bl = list(blacklistsql.get_chat_blacklist(chat_id))
    # Disabled command
    disabledcmd = list(disabledsql.get_all_disabled(chat_id))
    # Filters (TODO)
    """
	all_filters = list(filtersql.get_chat_triggers(chat_id))
	export_filters = {}
	for filters in all_filters:
		filt = filtersql.get_filter(chat_id, filters)
		# print(vars(filt))
		if filt.is_sticker:
			tipefilt = "sticker"
		elif filt.is_document:
			tipefilt = "doc"
		elif filt.is_image:
			tipefilt = "img"
		elif filt.is_audio:
			tipefilt = "audio"
		elif filt.is_voice:
			tipefilt = "voice"
		elif filt.is_video:
			tipefilt = "video"
		elif filt.has_buttons:
			tipefilt = "button"
			buttons = filtersql.get_buttons(chat.id, filt.keyword)
			print(vars(buttons))
		elif filt.has_markdown:
			tipefilt = "text"
		if tipefilt == "button":
			content = "{}#=#{}|btn|{}".format(tipefilt, filt.reply, buttons)
		else:
			content = "{}#=#{}".format(tipefilt, filt.reply)
		print(content)
		export_filters[filters] = content
	print(export_filters)
	"""

    # Locked
    curr_locks = locksql.get_locks(chat_id)
    curr_restr = locksql.get_restr(chat_id)

    if curr_locks:
        locked_lock = {
            "sticker": curr_locks.sticker,
            "audio": curr_locks.audio,
            "voice": curr_locks.voice,
            "document": curr_locks.document,
            "video": curr_locks.video,
            "contact": curr_locks.contact,
            "photo": curr_locks.photo,
            "gif": curr_locks.gif,
            "url": curr_locks.url,
            "bots": curr_locks.bots,
            "forward": curr_locks.forward,
            "game": curr_locks.game,
            "location": curr_locks.location,
            "rtl": curr_locks.rtl,
        }
    else:
        locked_lock = {}

    if curr_restr:
        locked_restr = {
            "messages": curr_restr.messages,
            "media": curr_restr.media,
            "other": curr_restr.other,
            "previews": curr_restr.preview,
            "all": all(
                [
                    curr_restr.messages,
                    curr_restr.media,
                    curr_restr.other,
                    curr_restr.preview,
                ]
            ),
        }
    else:
        locked_restr = {}

    locks = {"locks": locked_lock, "restrict": locked_restr}

    # Backing up
    backup[chat_id] = {
        "bot": context.bot.id,
        "hashes": {
            "info": {"rules": rules},
            "extra": notes,
            "blacklist": bl,
            "disabled": disabledcmd,
            "locks": locks,
        },
    }
    baccinfo = json.dumps(backup, indent=4)
    with open("MeguminRobot{}.backup".format(chat_id), "w") as f:
        f.write(str(baccinfo))
    context.bot.sendChatAction(current_chat_id, "upload_document")
    tgl = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime(time.time()))
    try:
        context.bot.sendMessage(
            JOIN_LOGGER,
            "*Cadangan berhasil diimpor:*\nChat: `{}`\nChat ID: `{}`\nOn: `{}`".format(
                chat.title, chat_id, tgl
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except BadRequest:
        pass
    context.bot.sendDocument(
        current_chat_id,
        document=open("MeguminRobot{}.backup".format(chat_id), "rb"),
        caption="*Cadangan berhasil diekspor:*\nChat: `{}`\nChat ID: `{}`\nOn: `{}`\n\nCatatan: `MeguminRobot-Backup` ini dibuat khusus untuk catatan.".format(
            chat.title, chat_id, tgl
        ),
        timeout=360,
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.MARKDOWN,
    )
    os.remove("MeguminRobot{}.backup".format(chat_id))  # Membersihkan file


# Data sementara
def put_chat(chat_id, value, chat_data):
)
    status = value is not False
    chat_data[chat_id] = {"backups": {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
)
    try:
        return chat_data[chat_id]["backups"]
    except KeyError:
        return {"status": False, "value": False}


__mod_name__ = "Backups"

__help__ = """
*Hanya untuk pemilik grup:*

 • /import: Membalas file cadangan agar butler / grup emilia dapat mengimpor sebanyak mungkin, membuat transfer menjadi sangat mudah! \
 Perhatikan bahwa file / foto tidak dapat diimpor karena batasan telegram.

 • /export: Data grup ekspor yang akan diekspor adalah: aturan, catatan (dokumen, gambar, musik, video, audio, suara, teks, tombol teks) \

"""

IMPORT_HANDLER = CommandHandler("import", import_data)
EXPORT_HANDLER = CommandHandler("export", export_data, pass_chat_data=True)

dispatcher.add_handler(IMPORT_HANDLER)
dispatcher.add_handler(EXPORT_HANDLER)
