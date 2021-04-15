import requests

from config import token, chat_id


class TelegramBot:
    url = 'https://api.telegram.org/bot' + token
    chat_id = chat_id
    timeout = 5

    @classmethod
    def send_notification(cls, instagram_data, only_posts=False):
        method = cls.url + '/sendMessage'
        text = cls.create_text_posts(instagram_data) if only_posts else cls.create_text(instagram_data)

        data = {
            "chat_id": cls.chat_id,
            "text": text,
            "parse_mode": 'HTML'
        }

        try:
            r = requests.post(url=method, json=data, timeout=cls.timeout)
        except (ConnectionError, requests.exceptions.Timeout):
            print('Не удается отправить уведомление!')
        else:
            if r.status_code != 200:
                print('Ошибка отправки в телеграм!')
                return

            print('Данные успешно отправлены!')

    @staticmethod
    def create_text(instagram_data):
        users_count = len(instagram_data['users'])
        likes_count = len(instagram_data['like_posts'])
        sub_count = len(instagram_data['subscribers'])
        posts_count = len(instagram_data["select_posts"])
        select_posts = '\n'.join(f'<a href="{i}">{i}</a>' for i in instagram_data["select_posts"])
        text = f'Хештег: <b>{instagram_data["hashtag"]}</b>\nНайдено подходящих постов: ' \
               f'<b>{posts_count}</b>\n{select_posts}\nНайдено пользователей: ' \
               f'<b>{users_count}</b>\n\nВсего лайкнуто постов: <b>{likes_count}</b>'

        if sub_count > 0:
            text += f'\n\nПодписался на <b>{sub_count}</b>'

        return text

    @staticmethod
    def create_text_posts(instagram_data):
        select_posts = '\n'.join(f'<a href="{i}">{i}</a>' for i in instagram_data)
        return f'Подходящие посты:\n{select_posts}\n'
