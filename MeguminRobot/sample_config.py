# Buat config.py baru atau ubah namanya menjadi file config.py di dir yang sama dan impor, kemudian perluas kelas ini.
import json
import os


def get_user_list(config, key):
    with open("{}/MeguminRobot/{}".format(os.getcwd(), config), "r") as json_file:
        return json.load(json_file)[key]


# Buat config.py baru atau ubah namanya menjadi file config.py di dir yang sama dan impor, kemudian perluas kelas ini.
class Config(object):
    LOGGER = True
    # YG DIBUTUHKAN
    # Masuk ke https://my.telegram.org dan isi slot ini dengan detail yang diberikan olehnya

    API_ID = 123456  # nilai integer, jangan gunakan ""
    API_HASH = "vjviccycycucifgf76c6c"
    TOKEN = "BOT_TOKEN"  # Variabel ini dulunya adalah API_KEY tetapi sekarang TOKEN, sesuaikan.
    OWNER_ID = 1234567890  # Jika Anda tidak tahu, jalankan bot dan lakukan / id di obrolan pribadi Anda dengannya, juga bilangan bulat
    OWNER_USERNAME = "PeronaSama"
    SUPPORT_CHAT = "SoutingLegionSNK"  # Grup Anda sendiri untuk dukungan, jangan tambahkan @
    JOIN_LOGGER = (
        -12345678
    )  # Mencetak grup baru tempat bot ditambahkan, hanya mencetak nama dan ID.
    EVENT_LOGS = (
        -12345678
    )  # Mencetak informasi seperti gbans, sudo promotes, status nonaktifkan yang mendukung AI yang dapat membantu dalam debugging dan shit

    # DIANJURKAN
    SQLALCHEMY_DATABASE_URI = "something://somewhat:user@hosturl:port/databasename"  # diperlukan untuk modul database apa pun
    LOAD = []
    NO_LOAD = ["rss", "cleaner", "connection", "math"]
    WEBHOOK = False
    INFOPIC = True
    URL = None
    SPAMWATCH_API = ""  # buka support.spamwat.ch untuk mendapatkan kunci
    SPAMWATCH_SUPPORT_CHAT = "@SpamWatchSupport"

    # PILIHAN
    # Daftar id - (bukan nama pengguna) untuk pengguna yang memiliki akses sudo ke bot.
    DRAGONS = get_user_list("elevated_users.json", "sudos")
    # Daftar id - (bukan nama pengguna) untuk pengembang yang akan memiliki izin yang sama dengan pemiliknya
    DEV_USERS = get_user_list("elevated_users.json", "devs")
    # Daftar id (bukan usernames) untuk user yang boleh gban, tapi bisa juga di banned.
    DEMONS = get_user_list("elevated_users.json", "supports")
    # Daftar id (bukan nama pengguna) untuk pengguna yang TIDAK AKAN dilarang/ditendang oleh bot.
    TIGERS = get_user_list("elevated_users.json", "tigers")
    WOLVES = get_user_list("elevated_users.json", "whitelists")
    DONATION_LINK = None  # EG, paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = True  # Hapus perintah yang tidak dapat diakses pengguna, seperti hapus /ban jika non admin menggunakannya.
    STRICT_GBAN = True
    WORKERS = (
        8  # Jumlah subjudul yang akan digunakan.  Tetapkan sebagai jumlah utas yang digunakan prosesor Anda
    )
    BAN_STICKER = ""  # banhammer marie id stiker, bot akan mengirim stiker ini sebelum melarang atau menendang pengguna di obrolan.
    ALLOW_EXCL = True  # Izinkan!  perintah serta / (Biarkan ini benar sehingga daftar hitam dapat berfungsi)
    CASH_API_KEY = (
        "skksksksjnss"  # Dapatkan kunci API Anda dari https://www.alphavantage.co/support/#api-key
    )
    TIME_API_KEY = "hvksoehnal"  # Dapatkan kunci API Anda dari https://timezonedb.com/api
    WALL_API = (
        "iccijxussytsgxvjh"  # Untuk wallpaper, dapatkan dari https://wall.alphacoders.com/api.php
    )
    AI_API_KEY = "igigatejjvoov"  # Untuk chatbot, dapatkan satu dari https://coffeehouse.intellivoid.net/dashboard
    BL_CHATS = []  # Daftar grup yang ingin Anda daftar hitam.
    SPAMMERS = None


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
