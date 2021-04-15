import random

from config import username, password
from instagram import InstagramBot


hashtag_list = [
    'бортикикраснодар',
    'конвертнавыписку',
    'бортикивкроватку',
    'детскиекроватки',
    'детскиекроваткикраснодар',
    'детскиеколяски',
    'детскиеколяскикраснодар',
]


if __name__ == '__main__':
    my_bot = InstagramBot()
    my_bot.login(username, password)
    my_bot.like_photo_by_hashtag(random.choice(hashtag_list))
    #  my_bot.selection_of_posts(random.choice(hashtag_list), 15, 80)
