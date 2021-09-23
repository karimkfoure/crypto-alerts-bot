import os
import time
import schedule
import utils
from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Load environment (.env) settings.
load_dotenv()
TELEGRAM_BOT_API = os.getenv("TELEGRAM_BOT_API")
threshold = 5 # percent
interval = 15 # minutes

cg = CoinGeckoAPI()

lastValue = {'ethereum': {'usd': 0},
             'bitcoin': {'usd': 0}}

def getValue(coin, fiat):
    # 'get_price' returns BTC price without decimal points, use 'get_exchange_rates' instead
    if coin == 'bitcoin': 
        cgBtcExchangeRates = cg.get_exchange_rates()
        return cgBtcExchangeRates['rates'][fiat]['value']
    else:
        cgPrice = cg.get_price(ids=[coin], vs_currencies=fiat)
        return cgPrice[coin][fiat]

def compare(coin, fiat, update):
    previousValue = lastValue[coin][fiat]
    newValue = getValue(coin, fiat)
    change = utils.getPercentageChange(newValue, previousValue)
    print(f"change {change}, abs value {abs(change)}")
    if abs(change) >= threshold:
        if change > 0:
            update.message.reply_text(f"{coin}/{fiat} / ${newValue} / +{round(change,3)}% {interval} minutes")
        else:
            update.message.reply_text(f"{coin}/{fiat} / ${newValue} / {round(change,3)}% {interval} minutes")
    lastValue[coin][fiat] = newValue

# Telegram commands
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! después te explico mejor')

def alerts(update: Update, context: CallbackContext) -> None:
    if len(context.args) < 2:
        update.message.reply_text('missing arguments')
        return
    coinArg = context.args[0]
    fiatArg = context.args[1]
    if coinArg in lastValue:
        if fiatArg in lastValue[coinArg]:
            schedule.every(interval).minutes.do(compare, coinArg, fiatArg, update).tag(update.message.chat.id)
            print("ok")
        else:
            update.message.reply_text('fiat does not exist')
    else:
        update.message.reply_text('coin does not exist')

def unsubscribe(update: Update, context: CallbackContext) -> None:
    schedule.clear(update.message.chat.id)

def main() -> None:
    # configure Telegram
    updater = Updater(TELEGRAM_BOT_API)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("alerts", alerts))
    updater.start_polling()

    # run scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

    updater.idle()

if __name__ == '__main__':
    main()