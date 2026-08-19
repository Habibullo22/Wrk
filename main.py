import subprocess
import telebot
from telebot import types

BOT_TOKEN = "8684787295:AAG-QBloVCtrVIuL0GXZl0J7lep0070vooE"

bot = telebot.TeleBot(BOT_TOKEN)

# Test ishlayotgan processlar
processes = {}


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🚀 Test boshlash", callback_data="start_test"),
        types.InlineKeyboardButton("🛑 Testni to‘xtatish", callback_data="stop_test")
    )

    bot.send_message(
        message.chat.id,
        "🛠 WRK Test Bot\n\n"
        "Faqat o‘zingizga tegishli yoki test qilishga ruxsatingiz bor serverlardan foydalaning.",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "start_test")
def ask_url(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "🌐 Test qilinadigan URLni yuboring:"
    )
    bot.register_next_step_handler(msg, ask_threads)


def ask_threads(message):
    url = message.text.strip()

    if not url.startswith(("http://", "https://")):
        bot.send_message(message.chat.id, "❌ URL noto‘g‘ri.")
        return

    msg = bot.send_message(message.chat.id, "🧵 Thread sonini kiriting (masalan: 4):")
    bot.register_next_step_handler(msg, ask_connections, url)


def ask_connections(message, url):
    try:
        threads = int(message.text)
        if threads < 1 or threads > 32:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ 1–32 oralig‘ida son kiriting.")
        return

    msg = bot.send_message(message.chat.id, "🔗 Connection sonini kiriting (masalan: 50):")
    bot.register_next_step_handler(msg, ask_duration, url, threads)


def ask_duration(message, url, threads):
    try:
        connections = int(message.text)
        if connections < 1 or connections > 500:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ 1–500 oralig‘ida son kiriting.")
        return

    msg = bot.send_message(message.chat.id, "⏱ Test davomiyligi (masalan: 10s):")
    bot.register_next_step_handler(
        msg,
        run_test,
        url,
        threads,
        connections
    )


def run_test(message, url, threads, connections):
    duration = message.text.strip()

    # Oddiy format tekshiruvi
    if not duration.endswith(("s", "m")):
        bot.send_message(message.chat.id, "❌ Masalan: 10s yoki 1m")
        return

    command = [
        "wrk",
        f"-t{threads}",
        f"-c{connections}",
        f"-d{duration}",
        url
    ]

    bot.send_message(
        message.chat.id,
        "🚀 Test boshlandi...\n\n"
        f"🧵 Threads: {threads}\n"
        f"🔗 Connections: {connections}\n"
        f"⏱ Duration: {duration}"
    )

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        processes[message.chat.id] = process

        output, _ = process.communicate()

        processes.pop(message.chat.id, None)

        # Telegram xabar hajmini oshirib yubormaslik
        output = output[-3500:]

        bot.send_message(
            message.chat.id,
            "✅ Test tugadi:\n\n"
            f"<pre>{output}</pre>",
            parse_mode="HTML"
        )

    except FileNotFoundError:
        bot.send_message(
            message.chat.id,
            "❌ wrk o‘rnatilmagan."
        )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Xato: {e}"
        )


@bot.callback_query_handler(func=lambda call: call.data == "stop_test")
def stop_test(call):
    bot.answer_callback_query(call.id)

    process = processes.get(call.message.chat.id)

    if not process:
        bot.send_message(call.message.chat.id, "ℹ️ Hozir test ishlamayapti.")
        return

    process.terminate()
    processes.pop(call.message.chat.id, None)

    bot.send_message(
        call.message.chat.id,
        "🛑 Test to‘xtatildi."
    )


print("🤖 WRK BOT ISHGA TUSHDI")
bot.infinity_polling()
