import asyncio
from datetime import datetime
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async, run_js
import webbrowser


url = "http://192.168.31.38:8081/"
webbrowser.open(url)

chat_msgs = []
online_users = {}
MAX_MESSAGES_COUNT = 100

def nickname_color(avatar):
    return {
        "🔴": "red",
        "🟢": "green",
        "⚪️": "black",
        "🟣": "purple",
        "🟠": "orange"
    }.get(str(avatar), "black")

async def main():
    global chat_msgs, online_users

    put_markdown("## 🧊 Онлайн чат!")

    msg_box = output()
    put_scrollable(msg_box, height=300, keep_bottom=True)

    avatar_options = ["🔴", "🟢", "⚪️", "🟣", "🟠"]

    input_data = await input_group("Войти в чат", [
        input("Твое имя", name="nickname", required=True, validate=lambda n: "Такой ник уже используется!" if n in online_users else None),
        radio("Выбери аватар", options=avatar_options, required=True, name="avatar"),
    ])

    nickname = input_data["nickname"]
    avatar = input_data["avatar"]

    online_users[nickname] = avatar

    nickname_color_str = nickname_color(avatar)

    current_time = datetime.now().strftime('%H:%M')
    chat_msgs.append({'type': 'system', 'nickname': nickname, 'avatar': avatar, 'message': f'📢 {avatar} {nickname} присоединился к чату!', 'time': current_time})
    msg_box.append(put_markdown(f'<span style="color:{nickname_color_str}">{avatar}</span> {nickname} присоединился к чату в {current_time}'))

    refresh_task = run_async(refresh_msg(nickname, avatar, msg_box, nickname_color))
    while True:
        data = await input_group("💭 Новое сообщение", [
            input(placeholder="Текст сообщения...", name="msg"),
            actions(name="cmd", buttons=["Отправить", {'label': "Сменить аватар", 'value': 'change_avatar'}, {'label': "Выйти из чата", 'type': 'cancel'}])
        ], validate=lambda m: ('msg', "Введите текст сообщения!") if m["cmd"] == "Отправить" and not m['msg'] else None)

        if data is None:
            break

        if data["cmd"] == "change_avatar":
            new_avatar = await radio("Выберите аватар", options=avatar_options, required=True)
            online_users[nickname] = new_avatar
            avatar = new_avatar
            new_nickname_color = nickname_color(new_avatar)
            current_time = datetime.now().strftime('%H:%M')
            chat_msgs.append({'type': 'system', 'nickname': nickname, 'avatar': new_avatar, 'message': f'Пользователь <span style="color:{new_nickname_color}">{nickname}</span> сменил аватар на {new_avatar}', 'time': current_time})
            nickname_color_str = new_nickname_color
            continue

        current_time = datetime.now().strftime('%H:%M')
        chat_msgs.append({'type': 'message', 'nickname': nickname, 'avatar': avatar, 'message': data['msg'], 'time': current_time})
        msg_box.append(put_markdown(f"<small>{current_time}</small> {avatar} <span style='color:{nickname_color_str}'> Ты:</span> {data['msg']}"))

    refresh_task.close()

    if nickname in online_users:
        del online_users[nickname]
        toast("Ты вышел из чата!")
        current_time = datetime.now().strftime('%H:%M')
        chat_msgs.append({'type': 'system', 'nickname': nickname, 'avatar': online_users.get(nickname, ""), 'message': f'Пользователь <span style="color:{nickname_color_str}">{nickname}</span> покинул чат!', 'time': current_time})
        msg_box.append(put_markdown(f'📢 Пользователь <span style="color:{nickname_color_str}">{nickname}</span> покинул чат в {current_time}'))

    put_buttons(['Перезайти'], onclick=lambda btn: run_js('window.location.reload()'))


async def refresh_msg(nickname, avatar, msg_box, nickname_color):
    global chat_msgs, online_users
    last_idx = len(chat_msgs)

    while True:
        await asyncio.sleep(1)
        
        for m in chat_msgs[last_idx:]:
            if m['type'] == 'message' and m['nickname'] != nickname:
                avatar_str = str(m['avatar']) if isinstance(m['avatar'], str) else ''
                msg_box.append(put_markdown(f"<small>{m['time']}</small> {avatar_str} <span style='color:{nickname_color(avatar_str)}'> {m['nickname']}</span>: {m['message']}"))
            elif m['type'] == 'system':
                msg_box.append(put_markdown(f"{m['message']} ({m['time']})"))
                
        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]
        
        last_idx = len(chat_msgs)

if __name__ == "__main__":
    start_server(main, debug=True, port=8081, cdn=False)
