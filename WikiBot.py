"""По запросу пользователя отправляет ему статью с коротким описанием
    и ссылкой на неё

    :param bot: Бот
    :type bot: any
    :param helpt: Файл с полезной информацией о боте
    :type helpt: file
    :param timer_seconds: Промежуток времени для отправки избраных статей
    :type timer_seconds: int
    :param top_n: Кол-во выводимых популярных запросов
    :type top_n: int
    :param connection: Соединение с бд
    :type connection: any"""

from telebot import TeleBot, types
import wikipedia
import time
from config import tg_token,host,user,password,dbname
import pymysql
import threading
def keep_connection_alive(conn,interval=60):
    while True:
        time.sleep(interval)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")

try:
    connection=pymysql.connect(host=host,port=3306,user=user,password=password,database=dbname,cursorclass=pymysql.cursors.DictCursor)
    print("connection succeed")
    print("#"*20)

except Exception as e:
    print("connection refused")
    print(e)




def time_convert(text):
    """Меняет фомат времени из (h1,d1,w1,m1,y1) в секундный

        :param text: format1
        :type text: str
        :returns: converted text[0]*int(text[1:])
        :rtype:int"""
    times = {'h': 3600, 'd': 86400, 'w': 604800, 'm': 2419200, 'y': 31536000, 's': 1}
    return times[text[0]] * int(text[1:])


wikipedia.set_lang('ru')
timer_seconds = 3600 * 24 * 7
top_n=5


def wikisearch(quary):
    """Ищет 15 самых популярных запросов по клячевому слову из Википедии

    :param quary: Поисковый запрос к Википедии
    :type quary: str
    :param res: results of searching
    :type res: array
    :returns: res
    :rtype: array"""
    res = wikipedia.search(quary, results=15)
    return res


def wikipage(pagename):
    """Ищет на Википедии статью по запросу с самым близким к нему значением

    :param pagename: Поисковый запрос к Википедии
    :type pagename: str
    :param page: result of search
    :type page: WikipediaPage
    :returns: page.title, page.summary, page.url
    :param page.title: name of page
    :type page.title: str
    :param page.summary: short version of article
    :type page.summary: str
    :param page.url: link on page
    :type page.url: any"""
    page = wikipedia.page(pagename)
    return page.title, page.summary, page.url


bot = TeleBot(tg_token)
helpt = open('Help.txt', encoding='utf-8').read()

thread = threading.Thread(target=keep_connection_alive, args=(connection,))
thread.daemon = True
thread.start()

@bot.message_handler(commands=['start'])
def main(message):
    """Посылает приветственное сообщение пользователю

    :param message: Сообщение от пользователя
    :type message: any
    :returns: None"""
    bot.send_message(message.chat.id, 'Привет, я Wiki-бот с плохой реализацией. Если тебе нужна помощь с командами, '
                                      'то введи /help')


@bot.message_handler(commands=['help'])
def help(message):
    """Посылает сообщение с полезной информацией о боте

    :param message: Сообщение от пользователя
    :type message: any"""
    bot.send_message(message.chat.id, helpt)


@bot.message_handler(commands=['settime'])
def set_time(message):
    """Устанавливает период времени на отправку ссылки
        на избранные статьи с Википедии

    :param message: Сообщение от пользователя
    :type message: any
    :returns:None
    :exception: TypeError"""
    try:
        global timer_seconds
        timer_seconds = time_convert(' '.join(message.text.split(' ')[1:]))
    except Exception:
        bot.send_message(message.chat.id, "Введите время формата:(h1,d1,w1,m1 (28 дней),y1 (365дней))")


@bot.message_handler(commands=["daily"])
def daily_state(message):
    """Отправляет ссылку на избранные статьи с Википедии через промежуток времени

    :param message: Сообщение от пользователя
    :type message: any
    :returns:None"""
    bot.send_message(message.chat.id, "Вот последняя версия страницы с избраными статьями")
    bot.send_message(message.chat.id,
                     "https://ru.wikipedia.org/wiki/%D0%92%D0%B8%D0%BA%D0%B8%D0%BF%D0%B5%D0%B4%D0%B8%D1%8F:%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B8%D0%B7%D0%B1%D1%80%D0%B0%D0%BD%D0%BD%D1%8B%D1%85_%D1%81%D1%82%D0%B0%D1%82%D0%B5%D0%B9")
    time.sleep(timer_seconds)
    daily_state(message)


@bot.message_handler(commands=['settop'])
def settopn(message):
    """Устанавливает желаемое колличество выводимых популярных значений

        :param message: Сообщение от пользователя
        :type message: any
        :returns: None
    """
    global top_n
    try:
        top_n = int(message.text.split('')[1])
    except Exception:
        bot.send_message(message.chat.id, "Введите число")

@bot.message_handler(commands=['mostpopular'])
def mp(message):
    """Выводит самые популярные запросы и ссылки на них

        :param message: Сообщение от пользователя
        :type message: any
    """
    global top_n
    try:
        n = top_n -1
        select_mostpopular_name = "SELECT name, count(*) from query group by name order by 2 desc limit %s"
        select_mostpopular_url = "SELECT url, count(*) from query group by name order by 2 desc limit %s"
        with connection.cursor() as cursor:
            cursor.execute(select_mostpopular_name,top_n)
            names = cursor.fetchall()
            cursor.execute(select_mostpopular_url,top_n)
            urls = cursor.fetchall()
            for popular in range(len(names)):
                name=dict(names[popular]).values()
                surl=dict(urls[popular]).values()
                bot.send_message(message.chat.id, name)
                bot.send_message(message.chat.id,surl)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Прости, я не смог посчитать популярные запросы")


@bot.message_handler()
def wiki(message):
    """Отправляет сообщение с результатами поиска

    :param message: Сообщение от пользователя
    :type message: any
    :param text: стандартизированый запрос от пользователя
    :type text: str
    :param results: Результаты поиска
    :type results: array
    :param markup: клавиатура вариантов под сообщением от бота
    :type markup: InlineKeyboardMarkup
    :param bat: кнопка для markup
    :type bat:InlineKeyboardButton
    :param title: Название статьи
    :type title: str
    :param summary: Краткое содержание статьи
    :type summary: str
    :param url: Ссылка на статью
    :type url: any
    :returns: None"""
    try:
        text = ' '.join(message.text.split(' ')).lower()
        results = wikisearch(text)
        markup = types.InlineKeyboardMarkup()
        for res in results:
            bat = types.InlineKeyboardButton(res, callback_data=res)
            markup.add(bat)
        bot.send_message(message.chat.id, text='Вот что я нашёл на Wikipedia', reply_markup=markup)
    except Exception:
        try:
            title, summary, url = wikipage(text)
            bot.send_message(message.chat.id, title)
            bot.send_message(message.chat.id, summary)
            bot.send_message(message.chat.id, url)
            db_url=str(url)
            try:
                insert_url = "INSERT INTO query(`name`,`url`) VALUES (%s,%s)"
                insert_val = (title,db_url)
                with connection.cursor() as cursor:
                    cursor.execute(insert_url, insert_val)
                    connection.commit()
            except Exception as e:
                print(e)
        except Exception:
            bot.send_message(message.chat.id, f"К сожалению я не могу ничего найти по запросу {text}")


@bot.callback_query_handler(func=lambda call: call.data)
def answer(call):
    '''Отправляет информацию поиска по запросу с клавиатуры markup

    :param call: Запрос от bat
    :type call: any
    :param title: Название статьи
    :type title: str
    :param summary: Краткое содержание статьи
    :type summary: str
    :param url: Ссылка на статью
    :type url: any
    :returns: None'''
    try:
        title, summary, url = wikipage(call.data)
        bot.send_message(call.message.chat.id, text=title)
        bot.send_message(call.message.chat.id, text=summary)
        bot.send_message(call.message.chat.id, text=url)
        db_url = str(url)
        try:
            insert_url = "INSERT INTO query(`name`,`url`) VALUES (%s,%s)"
            insert_val = (title, db_url)
            with connection.cursor() as cursor:
                cursor.execute(insert_url, insert_val)
                connection.commit()
        except Exception as e:
            print(e)
    except Exception:
        bot.send_message(call.message.chat.id, f"К сожалению я не могу ничего найти по запросу {call.data} ")


bot.polling(non_stop=True)