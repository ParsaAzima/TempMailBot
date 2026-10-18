# -*- coding: utf-8 -*-
#
# Temporary Mail Telegram Bot
# Copyright (C) 2026 Parsa-Azima
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# License: GPL-2.0-or-later
# https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import os
import re
import html
import time
import secrets
import string
import threading
import requests
import telebot

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================================
# CONFIGURATION
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
    raise SystemExit(
        "Please set BOT_TOKEN in the code or as an environment variable."
    )

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

GUERRILLA_API = "https://api.guerrillamail.com/ajax.php"
MAILTM_API = "https://api.mail.tm"

HTTP_TIMEOUT = 20

http = requests.Session()
http.headers.update({
    "User-Agent": "TemporaryMailTelegramBot/1.0"
})

# In-memory user sessions. Sessions reset if the bot restarts.
users = {}
users_lock = threading.Lock()


# =========================================================
# SMALL CAPS TEXT
# =========================================================

SMALL_CAPS = str.maketrans({
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ",
    "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ",
    "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ",
    "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ",
    "q": "ǫ", "r": "ʀ", "s": "ꜱ", "t": "ᴛ",
    "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x",
    "y": "ʏ", "z": "ᴢ",
})


def caps(text):
    """Convert ordinary text to Unicode small caps."""
    return str(text).translate(SMALL_CAPS)


def format_html(text):
    """
    Convert visible text to small caps while preserving HTML tags
    and HTML entities. Text inside code/pre remains unchanged.
    """
    text = str(text)

    parts = re.split(
        r"(<[^>]*>|&(?:amp|lt|gt|quot|#39|#\d+|#x[0-9a-fA-F]+);)",
        text
    )

    result = []
    code_depth = 0

    for part in parts:
        if not part:
            continue

        # Keep HTML tags unchanged.
        if part.startswith("<") and part.endswith(">"):
            result.append(part)

            if re.match(r"<(?:code|pre)(?:\s|>)", part, re.I):
                code_depth += 1
            elif re.match(r"</(?:code|pre)\s*>", part, re.I):
                code_depth = max(0, code_depth - 1)

        # Keep HTML entities unchanged.
        elif part.startswith("&") and part.endswith(";"):
            result.append(part)

        # Do not modify code blocks.
        elif code_depth:
            result.append(part)

        else:
            result.append(caps(part))

    return "".join(result)


def esc(value):
    """Safely escape dynamic text before inserting it into HTML."""
    return html.escape(str(value or ""), quote=True)


# =========================================================
# TELEGRAM UI HELPERS
# =========================================================

def button(label, callback):
    return InlineKeyboardButton(
        caps(label),
        callback_data=callback
    )


def send(chat_id, text, **kwargs):
    """Send a message without corrupting HTML formatting."""
    return bot.send_message(
        chat_id,
        format_html(text),
        parse_mode="HTML",
        **kwargs
    )


def edit(call, text, markup=None):
    try:
        bot.edit_message_text(
            format_html(text),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as exc:
        if "message is not modified" not in str(exc).lower():
            send(
                call.message.chat.id,
                text,
                reply_markup=markup
            )


def main_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(button("Create temporary email", "create"))
    kb.add(button("Choose email service", "providers"))
    kb.add(button("My current email", "current"))
    kb.add(button("Help", "help"))
    return kb


def back_keyboard(destination="home"):
    kb = InlineKeyboardMarkup()
    kb.add(button("Back", destination))
    return kb


def provider_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(button("Guerrilla Mail", "provider:guerrilla"))
    kb.add(button("Mail.tm", "provider:mailtm"))
    kb.add(button("Back", "home"))
    return kb


def email_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(button("Refresh inbox", "inbox"))
    kb.add(button("Create another email", "create"))
    kb.add(button("Choose email service", "providers"))
    kb.add(button("Back to main menu", "home"))
    return kb


def inbox_keyboard(messages):
    kb = InlineKeyboardMarkup(row_width=1)

    for message in messages[:10]:
        message_id = str(message.get("id", ""))
        subject = message.get("subject") or "No subject"
        subject = str(subject).strip()[:45]

        if message_id:
            kb.add(
                button(subject, "read:" + message_id)
            )

    kb.add(button("Refresh inbox", "inbox"))
    kb.add(button("Back", "email"))
    kb.add(button("Main menu", "home"))
    return kb


# =========================================================
# USER SESSION HELPERS
# =========================================================

def get_user(user_id):
    with users_lock:
        return users.setdefault(user_id, {
            "provider": "guerrilla",
            "email": None,
            "password": None,
            "token": None,
            "sid": None,
            "messages": []
        })


def set_user(user_id, **values):
    with users_lock:
        users.setdefault(user_id, {}).update(values)


def reset_email(user_id):
    set_user(
        user_id,
        email=None,
        password=None,
        token=None,
        sid=None,
        messages=[]
    )


def current_user(call):
    return get_user(call.from_user.id)


# =========================================================
# HTTP HELPERS
# =========================================================

def get_json(url, params=None, headers=None):
    response = http.get(
        url,
        params=params,
        headers=headers,
        timeout=HTTP_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def post_json(url, payload=None, headers=None):
    response = http.post(
        url,
        json=payload or {},
        headers=headers,
        timeout=HTTP_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


# =========================================================
# GUERRILLA MAIL
# =========================================================

def create_guerrilla_email(user_id):
    data = get_json(
        GUERRILLA_API,
        params={
            "f": "get_email_address",
            "lang": "en",
            "ip": "127.0.0.1",
            "agent": "TelegramTempMailBot"
        }
    )

    email_address = data.get("email_addr")
    sid = data.get("sid_token")

    if not email_address or not sid:
        raise RuntimeError(
            "Guerrilla Mail did not return an email address."
        )

    set_user(
        user_id,
        provider="guerrilla",
        email=email_address,
        sid=sid,
        token=None,
        password=None,
        messages=[]
    )

    return email_address


def guerrilla_inbox(user):
    if not user.get("sid"):
        raise RuntimeError("Create an email address first.")

    data = get_json(
        GUERRILLA_API,
        params={
            "f": "get_email_list",
            "sid_token": user["sid"],
            "offset": 0
        }
    )

    messages = data.get("list", [])
    user["messages"] = messages
    return messages


def guerrilla_read(user, message_id):
    data = get_json(
        GUERRILLA_API,
        params={
            "f": "fetch_email",
            "sid_token": user["sid"],
            "email_id": message_id
        }
    )

    return {
        "subject": data.get("mail_subject", "No subject"),
        "from": data.get("mail_from", "Unknown sender"),
        "text": data.get("mail_body", ""),
        "html": ""
    }


# =========================================================
# MAIL.TM
# =========================================================

def mailtm_headers(user):
    headers = {}

    if user.get("token"):
        headers["Authorization"] = "Bearer " + user["token"]

    return headers


def create_mailtm_email(user_id):
    domains_data = get_json(MAILTM_API + "/domains")
    domains = domains_data.get("hydra:member", [])

    if not domains:
        raise RuntimeError("Mail.tm has no available domains.")

    domain = domains[0].get("domain")

    if not domain:
        raise RuntimeError("Mail.tm returned an invalid domain.")

    username = (
        "user"
        + str(int(time.time()))
        + secrets.token_hex(3)
    )

    email_address = username + "@" + domain
    password = secrets.token_urlsafe(16)

    account_data = post_json(
        MAILTM_API + "/accounts",
        {
            "address": email_address,
            "password": password
        }
    )

    if not account_data.get("id"):
        raise RuntimeError("Mail.tm account creation failed.")

    token_data = post_json(
        MAILTM_API + "/token",
        {
            "address": email_address,
            "password": password
        }
    )

    token = token_data.get("token")

    if not token:
        raise RuntimeError("Mail.tm did not return an access token.")

    set_user(
        user_id,
        provider="mailtm",
        email=email_address,
        password=password,
        token=token,
        sid=None,
        messages=[]
    )

    return email_address


def mailtm_inbox(user):
    if not user.get("token"):
        raise RuntimeError("Create an email address first.")

    data = get_json(
        MAILTM_API + "/messages",
        headers=mailtm_headers(user)
    )

    messages = data.get("hydra:member", [])
    user["messages"] = messages
    return messages


def mailtm_read(user, message_id):
    data = get_json(
        MAILTM_API + "/messages/" + message_id,
        headers=mailtm_headers(user)
    )

    body = data.get("text") or ""

    if isinstance(body, list):
        body = "\n".join(str(line) for line in body)

    body_html = data.get("html") or ""

    if isinstance(body_html, list):
        body_html = "\n".join(str(line) for line in body_html)

    if not body and body_html:
        body = re.sub(r"<[^>]+>", " ", body_html)
        body = html.unescape(body)
        body = re.sub(r"\s+", " ", body).strip()

    return {
        "subject": data.get("subject", "No subject"),
        "from": ", ".join(
            sender.get("address", "Unknown")
            for sender in data.get("from", [])
        ) or "Unknown sender",
        "text": body,
        "html": body_html
    }


# =========================================================
# PROVIDER DISPATCH
# =========================================================

def create_email(user_id):
    user = get_user(user_id)

    if user["provider"] == "mailtm":
        return create_mailtm_email(user_id)

    return create_guerrilla_email(user_id)


def get_inbox(user):
    if not user.get("email"):
        raise RuntimeError("Create an email address first.")

    if user["provider"] == "mailtm":
        return mailtm_inbox(user)

    return guerrilla_inbox(user)


def read_message(user, message_id):
    if user["provider"] == "mailtm":
        return mailtm_read(user, message_id)

    return guerrilla_read(user, message_id)


# =========================================================
# MESSAGE TEMPLATES
# =========================================================

def home_text():
    return (
        "<b>Temporary Mail</b>\n\n"
        "Create a temporary email address and check its inbox.\n\n"
        "Choose an option below to get started.\n"
        "Author: Parsa-Azima"
    )


def provider_name(user):
    return (
        "Mail.tm"
        if user.get("provider") == "mailtm"
        else "Guerrilla Mail"
    )


def email_text(user):
    return (
        "<b>Your temporary email</b>\n\n"
        "<code>" + esc(user.get("email", "")) + "</code>\n\n"
        "<b>Service:</b> " + esc(provider_name(user)) + "\n\n"
        "Use the buttons below to check incoming messages."
    )


def error_text(exc):
    # Do not expose long server traces or credentials to users.
    message = str(exc).strip()
    if len(message) > 220:
        message = message[:220] + "..."
    return (
        "<b>Something went wrong</b>\n\n"
        + esc(message)
        + "\n\nPlease try again later or choose another service."
    )


# =========================================================
# COMMAND HANDLERS
# =========================================================

@bot.message_handler(commands=["start", "help"])
def start_handler(message):
    get_user(message.from_user.id)
    send(
        message.chat.id,
        home_text(),
        reply_markup=main_keyboard()
    )


@bot.message_handler(commands=["cancel"])
def cancel_handler(message):
    send(
        message.chat.id,
        home_text(),
        reply_markup=main_keyboard()
    )


# =========================================================
# CALLBACK HANDLERS
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data or ""
    user = get_user(user_id)

    try:
        bot.answer_callback_query(call.id)

        # Main menu
        if data == "home":
            edit(call, home_text(), main_keyboard())
            return

        # Help
        if data == "help":
            text = (
                "<b>Help</b>\n\n"
                "1. Choose an email service.\n"
                "2. Create a temporary email address.\n"
                "3. Copy the address and use it where needed.\n"
                "4. Open the inbox to check incoming messages.\n\n"
                "Temporary addresses may expire or be accessible "
                "to other users, depending on the provider. "
                "Do not use them for sensitive accounts."
            )
            edit(call, text, back_keyboard("home"))
            return

        # Choose provider
        if data == "providers":
            edit(
                call,
                "<b>Choose an email service</b>\n\n"
                "Select the provider you want to use.",
                provider_keyboard()
            )
            return

        # Set provider
        if data.startswith("provider:"):
            provider = data.split(":", 1)[1]

            if provider not in ("guerrilla", "mailtm"):
                edit(call, "Unknown email service.", back_keyboard())
                return

            set_user(user_id, provider=provider)
            reset_email(user_id)
            set_user(user_id, provider=provider)

            text = (
                "<b>Service selected</b>\n\n"
                "Provider: "
                + esc(provider_name(get_user(user_id)))
                + "\n\nPress the button below to create an address."
            )

            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(button("Create temporary email", "create"))
            kb.add(button("Choose another service", "providers"))
            kb.add(button("Back", "home"))

            edit(call, text, kb)
            return

        # Create email
        if data == "create":
            edit(
                call,
                "<b>Creating your email address...</b>\n\n"
                "Please wait.",
                None
            )

            try:
                email_address = create_email(user_id)
                user = get_user(user_id)

                edit(
                    call,
                    email_text(user),
                    email_keyboard()
                )

            except Exception as exc:
                edit(
                    call,
                    error_text(exc),
                    back_keyboard("providers")
                )
            return

        # Show current email
        if data in ("current", "email"):
            user = get_user(user_id)

            if not user.get("email"):
                edit(
                    call,
                    "You do not have an email address yet.\n\n"
                    "Create one to continue.",
                    main_keyboard()
                )
            else:
                edit(call, email_text(user), email_keyboard())
            return

        # Inbox
        if data == "inbox":
            user = get_user(user_id)

            if not user.get("email"):
                edit(
                    call,
                    "Create an email address first.",
                    back_keyboard("home")
                )
                return

            edit(
                call,
                "<b>Checking inbox...</b>\n\nPlease wait.",
                None
            )

            try:
                messages = get_inbox(user)

                if not messages:
                    edit(
                        call,
                        "<b>Inbox</b>\n\n"
                        "No messages have arrived yet.",
                        email_keyboard()
                    )
                    return

                lines = ["<b>Inbox</b>\n"]

                for index, msg in enumerate(messages[:10], start=1):
                    subject = (
                        msg.get("subject")
                        or msg.get("mail_subject")
                        or "No subject"
                    )
                    sender = msg.get("from")

                    if isinstance(sender, dict):
                        sender = sender.get("address", "Unknown sender")
                    elif isinstance(sender, list):
                        sender = ", ".join(
                            item.get("address", "Unknown sender")
                            for item in sender
                        )

                    if not sender:
                        sender = (
                            msg.get("mail_from")
                            or "Unknown sender"
                        )

                    lines.append(
                        str(index) + ". <b>" + esc(subject) + "</b>\n"
                        "<i>" + esc(sender) + "</i>"
                    )

                edit(
                    call,
                    "\n\n".join(lines),
                    inbox_keyboard(messages)
                )

            except Exception as exc:
                edit(
                    call,
                    error_text(exc),
                    email_keyboard()
                )
            return

        # Read message
        if data.startswith("read:"):
            message_id = data.split(":", 1)[1]
            user = get_user(user_id)

            if not user.get("email"):
                edit(
                    call,
                    "Create an email address first.",
                    back_keyboard("home")
                )
                return

            try:
                message = read_message(user, message_id)

                body = message.get("text") or "(No text content)"
                body = str(body).strip()

                # Keep message output within Telegram's message limit.
                if len(body) > 2500:
                    body = body[:2500] + "\n\n[Message shortened]"

                text = (
                    "<b>Email details</b>\n\n"
                    "<b>Subject:</b> " + esc(message.get("subject")) + "\n"
                    "<b>From:</b> " + esc(message.get("from")) + "\n\n"
                    "<b>Message:</b>\n"
                    "<pre>" + esc(body) + "</pre>"
                )

                kb = InlineKeyboardMarkup(row_width=1)
                kb.add(button("Back to inbox", "inbox"))
                kb.add(button("Back to email", "email"))
                kb.add(button("Main menu", "home"))

                edit(call, text, kb)

            except Exception as exc:
                edit(
                    call,
                    error_text(exc),
                    back_keyboard("inbox")
                )
            return

        # Unknown callback
        edit(
            call,
            "Unknown option. Please return to the main menu.",
            back_keyboard("home")
        )

    except Exception as exc:
        try:
            send(
                chat_id,
                error_text(exc),
                reply_markup=main_keyboard()
            )
        except Exception:
            pass


# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":
    print("Temporary Mail bot is running.")

    while True:
        try:
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=25,
                skip_pending=True
            )
        except KeyboardInterrupt:
            print("Bot stopped.")
            break
        except Exception as exc:
            print("Polling error:", repr(exc))
            time.sleep(5)
