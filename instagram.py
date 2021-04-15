import time
import random
import re
import pickle
import os

from seleniumwire import webdriver
#  from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from config import chrome_options, chromedriver, cookies, proxy_options
from telegram import TelegramBot


class InstagramBot:
    main_url = 'https://www.instagram.com'
    hashtag_url = 'https://www.instagram.com/explore/tags/'
    scroll_script = "window.scrollTo(0, document.body.scrollHeight);"
    like_button_xpath = '/html/body/div[1]/section/main/div/div[1]/article/div[3]/section[1]/span[1]/button'
    wrong_userpage = '/html/body/div[1]/section/main/div/h2'
    post_count_xpath = '/html/body/div[1]/section/main/div/header/section/ul/li[1]/span/span'
    closed_account_xpath = '/html/body/div[1]/section/main/div/div/article/div[1]/div/h2'
    subscribe_button = '/html/body/div[1]/section/main/div/header/section/div[1]/div[1]/div/div/button'
    subscribe_button2 = '/html/body/div[1]/section/main/div/header/section/div[2]/div/div/div/button'
    comments_xpath = '/html/body/div[1]/section/main/div/div[1]/article/div[3]/div[1]/ul'
    comment_author_xpath = '/html/body/div[1]/section/main/div/div[1]/article/header/div[2]/div[1]/div[1]/span/a'
    comment_author_xpath_2 = '/html/body/div[1]/section/main/div/div[1]/article/header/div[2]/div[1]/div[1]/a'
    comment_pattern = 'цена|стоимость|стоит|сколько|цены|цену|цене'
    author = 'sovenok__krd'

    def __init__(self):
        self.browser = webdriver.Chrome(chromedriver, options=chrome_options, seleniumwire_options=proxy_options)
        self.telegram = TelegramBot()
        self.max_likes = 20
        self.likes_count = 0

    def close_browser(self):
        self.browser.close()
        self.browser.quit()

    def login(self, username, password):
        browser = self.browser

        browser.get(self.main_url)
        time.sleep(random.randrange(3, 5))
        print(browser.title)

        if os.path.exists(f"{cookies}"):
            print("Куки найдены!")

            for cookie in pickle.load(open(f"{username}_cookies", "rb")):
                browser.add_cookie(cookie)

            time.sleep(5)
            browser.refresh()
            time.sleep(10)
        else:
            username_input = browser.find_element_by_name('username')
            username_input.clear()
            username_input.send_keys(username)

            time.sleep(2)

            password_input = browser.find_element_by_name('password')
            password_input.clear()
            password_input.send_keys(password)

            password_input.send_keys(Keys.ENTER)
            time.sleep(5)

            # cookies
            pickle.dump(browser.get_cookies(), open(f"{username}_cookies", "wb"))
            print("Куки созданы!")

    # получаем список url страниц авторов комментариев к посту
    def get_comment_autor_urls(self):
        try:
            if self.xpath_exists(self.comment_author_xpath):
                author = self.browser.find_element_by_xpath(self.comment_author_xpath).text
            else:
                author = self.browser.find_element_by_xpath(self.comment_author_xpath_2).text

            if author == self.author:
                return []

            comments = self.browser.find_element_by_xpath(self.comments_xpath)

            spans = comments.find_elements_by_tag_name('span')
            # собираем не пустые span в которых спрашивают про стоимость
            spans = [item for item in spans if item.text != '' and re.search(self.comment_pattern, item.text.lower())]

            # Составляем список тегов 'a' которые относятся к родительскому элементу тега span,
            # кроме ссылки на автора поста
            hrefs = []
            for span in spans:
                parent_element = span.find_element_by_xpath('..')
                all_tags_a = parent_element.find_elements_by_tag_name('a')
                for a in all_tags_a:
                    if a.text != author:
                        hrefs.append(a)

            # hrefs = comments.find_elements_by_tag_name('a')
            hrefs = [
                item.get_attribute('href')
                for item in hrefs
                if "/p/" not in item.get_attribute('href') and "/tags/" not in item.get_attribute('href')
            ]

        except Exception as ex:
            print(ex)
            return None
        else:
            return list(set(hrefs))

    # будем заходить на рандомный пост из найденных, получать все комментарии и лайкать посты их авторов
    def like_photo_by_hashtag(self, hashtag):
        browser = self.browser
        hashtag_page_loops_count = 20  # сколько скролов делать на странице с хештегами
        user_page_loops_count = 5  # сколько скролов делать на странице пользователя
        user_posts_count = 2  # сколько постов каждого пользователя лакать
        hashtag_posts_count = 150  # сколько постов на странице с хештегами выбирать
        
        # для отправки в телегу
        telegram_data = {
            'hashtag': hashtag,
            'select_posts': [],
            'users': [],
            'like_posts': [],
            'subscribers': [],
        }

        browser.get(f'{self.hashtag_url}{hashtag}/')
        time.sleep(5)

        post_urls = self.get_post_urls(loops_count=hashtag_page_loops_count)

        try:
            posts = random.sample(post_urls, hashtag_posts_count)
        except ValueError:
            print('Похоже, мы не авторизированы.')
            self.close_browser()
            return

        # ходим пока не наберем нужное колличество лайков
        post_number = 0
        while self.likes_count < self.max_likes:
            post_number += 1
            print(f'Пост {post_number}  лайков поставлено {self.likes_count}')

            try:
                post = posts.pop()
            except IndexError:
                print('Закончились посты, выхожу.')
                break

            print(f'Выбран пост: {post}')

            browser.get(post)
            time.sleep(random.randrange(10, 20))

            hrefs = self.get_comment_autor_urls()  # Получаем список пользователей которых надо лайкнуть
            if hrefs is None:
                break

            if hrefs:
                print(f'Список пользователей для лайков: {hrefs}')
                telegram_data['select_posts'].append(post)

            # Поочередно лайкаем посты пользователя
            for href in hrefs:
                # если уже наброно нужное колличество лайков, выходим
                if self.likes_count >= self.max_likes:
                    print('Мы набрали нужное колличество лайков.Выходим.')
                    break

                account = href.split("/")[-2]

                # Если мы уже лайкали этого пользователя
                if account in telegram_data['users']:
                    print(f'Мы уже лайкали пользователя {account}')
                    continue

                telegram_data['users'].append(account)

                browser.get(href)
                time.sleep(5)

                if self.xpath_exists(self.wrong_userpage):
                    print('Такого пользователя не существует')
                    continue
                elif self.xpath_exists(self.closed_account_xpath):
                    print(f'Это закрытый аккаунт! Подписываемся на {account}')
                    self.subscribe_to_account()
                    telegram_data['subscribers'].append(account)

                    time.sleep(3)
                    continue
                else:
                    print(f'Пользователь {account} успешно найден, ставим лайки!')
                    time.sleep(3)

                    post_urls = self.get_post_urls(loops_count=user_page_loops_count)
                    try:
                        post_urls = random.sample(post_urls, user_posts_count)
                    except ValueError:
                        print('На странице недостаточно постов')
                    else:
                        print(f'Выбраны случайные посты: {post_urls}')
                        self.like_posts(post_urls)
                        telegram_data['like_posts'].extend(post_urls)
                        time.sleep(3)

        self.close_browser()

        self.telegram.send_notification(telegram_data)

    def xpath_exists(self, url):
        # проверяем по xpath существует ли элемент на странице
        browser = self.browser
        try:
            browser.find_element_by_xpath(url)
            exist = True
        except NoSuchElementException:
            exist = False

        return exist

    #  ставим лайк на пост по прямой ссылке
    def put_exactly_like(self, userpost):
        browser = self.browser
        browser.get(userpost)
        time.sleep(4)

        if self.xpath_exists(self.wrong_userpage):
            print('Такого поста не существует')
            self.close_browser()
        else:
            print('Пост успешно найден, ставим лайк!')
            time.sleep(2)

        browser.find_element_by_xpath(self.like_button_xpath).click()
        time.sleep(2)

        print(f'Лайк на пост: {userpost} поставлен!')
        self.close_browser()

    #  получаем колличество постов на странице юзера
    def get_posts_count(self):
        post_count = self.browser.find_element_by_xpath(self.post_count_xpath).text
        post_count = post_count.replace(' ', '')

        return int(post_count) // 12

    # Получаем список с url постов пользователя
    def get_post_urls(self, loops_count=1):
        browser = self.browser

        post_urls = []
        for i in range(0, loops_count):
            hrefs = browser.find_elements_by_tag_name('a')
            hrefs = [item.get_attribute('href') for item in hrefs if "/p/" in item.get_attribute('href')]

            for href in hrefs:
                post_urls.append(href)

            browser.execute_script(self.scroll_script)
            time.sleep(random.randrange(2, 4))

        return list(set(post_urls))

    # лайкаем каждый пост из списка
    def like_posts(self, post_urls):
        browser = self.browser

        for post_url in post_urls:
            try:
                browser.get(post_url)
                time.sleep(5)

                browser.find_element_by_xpath(self.like_button_xpath).send_keys(Keys.ENTER)
                time.sleep(random.randrange(80, 100))

                self.likes_count += 1
                print(f'Лайк на пост: {post_url} поставлен!')
            except Exception as ex:
                print(ex)
                self.close_browser()

    # ставим слайки по ссылке на аккаунт пользователя
    def put_many_likes(self, user_page):
        browser = self.browser
        browser.get(user_page)
        time.sleep(4)

        if self.xpath_exists(self.wrong_userpage):
            print('Такого пользователя не существует')
            self.close_browser()
            return
        elif self.xpath_exists(self.closed_account_xpath):
            print('Это закрытый аккаунт')
            self.subscribe_to_account()
            self.close_browser()
            return
        else:
            print('Пользователь успешно найден, ставим лайки!')
            time.sleep(2)

        loops_count = self.get_posts_count()
        post_urls = self.get_post_urls(loops_count=loops_count)

        self.like_posts(post_urls)
        self.close_browser()

    def subscribe_to_account(self):
        browser = self.browser
        time.sleep(3)
        try:
            if self.xpath_exists(self.subscribe_button):
                browser.find_element_by_xpath(self.subscribe_button).send_keys(Keys.ENTER)
            else:
                browser.find_element_by_xpath(self.subscribe_button2).send_keys(Keys.ENTER)
            time.sleep(3)
        except Exception as ex:
            print(ex)
            self.close_browser()

    def selection_of_posts(self, hashtag: str, loops_count: int, post_sample: int):
        """ Заходим по рандомному хештегу, выбирает рандомное колличество постов,
            проверяем их на наличее нужных нам комментариев и составляем список.

            :loops_count: колличество скролов страницы хештегов
            :post_sample: сколько рандомных постов выбираем для проверки
        """
        browser = self.browser
        posts_count = 0
        max_posts = 20

        # список постов для отправки в телегу
        select_posts = []

        print(f'Хештег {hashtag}')
        browser.get(f'{self.hashtag_url}{hashtag}/')
        time.sleep(random.randrange(8, 16))
        print(browser.title)

        post_urls = self.get_post_urls(loops_count=loops_count)
        print(f'Постов отобрано: {post_urls}')

        try:
            posts = random.sample(post_urls, post_sample)
        except ValueError:
            print('Не открывается страница с хештегами.')
            self.close_browser()
            return

        # ходим пока не наберем нужное колличество подхлдящих постов
        while posts_count < max_posts:
            print(f'собрано постов {posts_count}')
            try:
                post = posts.pop()
            except IndexError:
                print('Закончились посты, выхожу.')
                break

            print(f'Выбран пост: {post}')
            browser.get(post)
            time.sleep(random.randrange(8, 16))

            hrefs = self.get_comment_autor_urls()
            if hrefs:
                print(f'Подходящий пост. {post}')
                select_posts.append(post)
                posts_count += 1

            # если уже наброно нужное колличество постов, выходим
            if posts_count >= max_posts:
                print('Мы набрали нужное колличество постов.Выходим.')
                break

        self.close_browser()
        self.telegram.send_notification(select_posts, only_posts=True)
