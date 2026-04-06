import vk_api
import json
import random
import time
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv
import os

load_dotenv 
TOKEN = "os.getenv('TOKEN'))"
BOT_NAME = "🐟 Рыбкинс"

vk = vk_api.VkApi(token=TOKEN)
api = vk.get_api()
longpoll = VkLongPoll(vk)

# ===== БД =====
try:
    with open("db.json", "r", encoding="utf-8") as f:
        db = json.load(f)
except:
    db = {
        "users": {},
        "punishments": {},
        "relationships": {},
        "logs": []
    }

def save():
    with open("db.json", "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def now():
    return int(time.time())

# ===== РОЛИ =====
ROLES = {
    "owner": [123456789],
    "admin": [],
    "mod": [],
    "helper": []
}

def has_role(user_id, role):
    return user_id in ROLES.get(role, []) or user_id in ROLES["owner"]

# ===== НАКАЗАНИЯ =====
def set_punishment(uid, ptype, seconds):
    if str(uid) not in db["punishments"]:
        db["punishments"][str(uid)] = {}
    db["punishments"][str(uid)][ptype] = now() + seconds

def is_muted(uid):
    return db["punishments"].get(str(uid), {}).get("mute", 0) > now()

def is_banned(uid):
    return db["punishments"].get(str(uid), {}).get("ban", 0) > now()

def log(text):
    db["logs"].append(f"[{time.ctime()}] {text}")
    if len(db["logs"]) > 100:
        db["logs"].pop(0)

# ===== RP =====
rp_commands = {
    "обнять": ("🤗", "hug"),
    "поцеловать": ("💋", "kiss"),
    "ударить": ("👊", "slap"),
    "укусить": ("🧛", "bite"),
    "погладить": ("🫳", "hug"),
    "пнуть": ("🦵", "slap")
}

extra = [
    "обнять крепко","чмокнуть","подмигнуть","толкнуть",
    "напугать","разозлить","обрадовать","поддержать",
    "утешить","развеселить","подарить","украсть",
    "влюбиться","ревновать","играть","защитить"
]

for cmd in extra:
    rp_commands[cmd] = ("✨", "hug")

rp_gifs = {
    "hug": ["https://media.giphy.com/media/l2QDM9Jnim1YVILXa/giphy.gif"],
    "kiss": ["https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif"],
    "slap": ["https://media.giphy.com/media/jLeyZWgtwgr2U/giphy.gif"],
    "bite": ["https://media.giphy.com/media/11k3oaUjSlFR4I/giphy.gif"]
}

def get_gif(t):
    return random.choice(rp_gifs.get(t, [""]))

# ===== ОТПРАВКА =====
def send(peer_id, text, attachment=None):
    api.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=random.randint(1, 999999),
        attachment=attachment
    )

# ===== БОТ =====
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        text = event.text.lower()
        user_id = event.user_id
        peer_id = event.peer_id

        if is_banned(user_id):
            continue
        if is_muted(user_id):
            continue

        if str(user_id) not in db["users"]:
            db["users"][str(user_id)] = {
                "race": "человек",
                "level": 1,
                "xp": 0
            }

        # ===== RP =====
        if text.startswith("!"):
            cmd = text[1:]

            if cmd in rp_commands:
                if not event.reply_to:
                    send(peer_id, f"{BOT_NAME}: Ответь на человека")
                    continue

                emoji, rtype = rp_commands[cmd]
                gif = get_gif(rtype)

                send(peer_id,
                     f"{BOT_NAME}: {emoji} [id{user_id}|ты] {cmd} человека",
                     gif)

        # ===== МУТ =====
        if text.startswith("!мут"):
            if not has_role(user_id, "helper"):
                send(peer_id, f"{BOT_NAME}: ❗ Нет прав")
                continue

            try:
                time_sec = int(text.split()[1])
                target = event.reply_to

                set_punishment(target, "mute", time_sec)
                log(f"{user_id} мут {target}")

                send(peer_id, f"{BOT_NAME}: 🔇 Мут на {time_sec} сек")
            except:
                send(peer_id, f"{BOT_NAME}: Ошибка")

        # ===== БАН =====
        if text.startswith("!бан"):
            if not has_role(user_id, "admin"):
                send(peer_id, f"{BOT_NAME}: ❗ Нет прав")
                continue

            try:
                time_sec = int(text.split()[1])
                target = event.reply_to

                set_punishment(target, "ban", time_sec)
                log(f"{user_id} бан {target}")

                send(peer_id, f"{BOT_NAME}: ⛔ Бан на {time_sec} сек")
            except:
                send(peer_id, f"{BOT_NAME}: Ошибка")

        # ===== ЛОГИ =====
        if text == "!логи":
            if not has_role(user_id, "admin"):
                send(peer_id, f"{BOT_NAME}: ❗ Нет прав")
                continue

            logs = "\n".join(db["logs"][-10:])
            send(peer_id, f"{BOT_NAME}:\n{logs or 'Нет логов'}")

        # ===== ИНФО =====
        if text == "!инфо":
            user = db["users"][str(user_id)]
            rel = db["relationships"].get(str(user_id), {})

            status = "❌ Нет отношений"
            if rel.get("partner"):
                status = f"❤️ {rel['partner']}"
            if rel.get("married"):
                status = f"💍 {rel['partner']}"

            send(peer_id,
                 f"""{BOT_NAME}

Раса: {user['race']}
Уровень: {user['level']}
XP: {user['xp']}

{status}""")

        # ===== БРАК =====
        if text == "!брак":
            if not event.reply_to:
                send(peer_id, f"{BOT_NAME}: Ответь на человека")
                continue

            target = event.reply_to

            db["relationships"][str(user_id)] = {
                "partner": target,
                "married": True
            }
            db["relationships"][str(target)] = {
                "partner": user_id,
                "married": True
            }

            send(peer_id, f"{BOT_NAME}: 💍 Вы в браке")

        save()