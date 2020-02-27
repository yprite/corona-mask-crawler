# -*- coding: utf-8 -*-
import os
import wget
import time
import datetime
import logging

import telegram
from telegram.ext import Updater, CommandHandler
from telegram.error import NetworkError, Unauthorized

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


first_launch = True

def yopen(path):
    f = open(path, 'r', encoding='UTF8')
    data = f.read()
    f.close()
    return data

def get(url):
    import requests
    headers = {
        'Host': 'www.welkeepsmall.com',
        'Content-Type': 'text/html; charset=UTF-8',
        'Proxy-Connection': 'keep-alive',
        'Cache-Control' : 'max-age=0',
        'Upgrade-Insecure-Requests' : '1',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36 SECSSOBrowserChrome',
        'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer' : 'http://www.welkeepsmall.com/shop/shopbrand.html?type=M&xcode=023&mcode=001',
        'Accept-Encoding' : 'gzip, deflate',
        'Accept-Language' : 'ko-KR,ko;q=0.9,es-ES;q=0.8,es;q=0.7,en-US;q=0.6,en;q=0.5'
    }
    try:
        req = requests.get(url=url, headers=headers, timeout=30)
        print (req.status_code)
        req.encoding = None
        if req.ok == False:
            return ''
    except Exception as E:
        return ''
    return req.text

def send_message_telegram(msg):
    bot = telegram.Bot('879043364:AAGDXv6TvnBGFt5qatSnw92FqZKW6STWsT0')
    bot.sendMessage(chat_id = '@terranscv', text=msg)

def parser(data, now):
    if data == '':
        delta = datetime.datetime.now() - now
        if delta.second > 30:
            send_message_telegram('Timeout 발생 : 서버 과부하')
        return
    soup = BeautifulSoup(data, 'html.parser')
    all_div = soup.find_all('div', {'class':'tb-center'})
    for div in all_div:
        #print (div.find('a').get('href'))
        if div.find('li', {'class':'dsc'}).text == '웰킵스 뉴 스마트 황사마스크 대형  [KF94] [50개입]':
            #send_message_telegram(div.find('ul', {'class':'info'}).text)
            try:
                #print (div.find('li', {'class':'dsc'}).text)
                s = div.find('li', {'class':'soldout'}).text
                #print (div.find('a').get('href'))
                #print ("")
            except Exception as E:
                send_message_telegram("" + div.find('li', {'class':'dsc'}).text + "\n" + "http://www.welkeepsmall.com" +div.find('a').get('href') )

            #정각에 텔레그램으로 쏘기
            if now.minute % 30 == 0 and now.second == 0:
                send_message_telegram(div.find('ul', {'class':'info'}).text)

            global first_launch
            if first_launch == True:
                send_message_telegram(div.find('ul', {'class':'info'}).text)
                first_launch = False
    return

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    update.message.reply_text('Hi! Use /set <seconds> to set a timer')

def alarm(context):
    """Send the alarm message."""
    job = context.job
    context.bot.send_message(job.context, text='Beep!')


def set_timer(update, context):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return

        # Add job to queue and stop current one if there is a timer already
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_once(alarm, due, context=chat_id)
        context.chat_data['job'] = new_job

        update.message.reply_text('Timer successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']

    update.message.reply_text('Timer successfully unset!')


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main2():
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("940183112:AAHVKHOgsh0XRp5KUbSe-HMX8Rv3SmbvvTc", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()

update_id = None


def main():
    """Run the bot."""
    global update_id
    # Telegram Bot Authorization Token
    bot = telegram.Bot('879043364:AAGDXv6TvnBGFt5qatSnw92FqZKW6STWsT0')

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            bot.sendMessage(chat_id = '@terranscv', text="저는 봇입니다.")
            echo(bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            # The user has removed or blocked the bot.
            update_id += 1


def echo(bot):
    """Echo the message the user sent."""
    global update_id
    # Request updates after the last update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1

        if update.message:  # your bot can receive updates without messages
            # Reply to the message
            update.message.reply_text(update.message.text)



if __name__ == "__main__":
    #import threading
    #threading.Thread(target=main).start()



    while(1):
        now = datetime.datetime.now()
        parser(get('http://www.welkeepsmall.com/shop/shopbrandCA.html?xcode=023&type=M&mcode=002'), now)
        time.sleep(10)
    
    #with open("shopbrand.html", encoding='UTF-8') as fp:
    #    soup = BeautifulSoup(fp, 'html.parser')
    #    all_div = soup.find_all('div', {'class':'tb-center'})
    #    for div in all_div:
    #        if div.find('a').get('href') == '/shop/shopdetail.html?branduid=1000798&xcode=023&mcode=002&scode=&type=X&sort=manual&cur_code=023002&GfDT=bm56W11G':
    #            print (div.find('li', {'class':'dsc'}).text)
    #            print (div.find('li', {'class':'soldout'}))
    #            print (div.find('a').get('href'))
    #            print ("")
