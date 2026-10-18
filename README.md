# Temporary Mail Telegram Bot

A Telegram bot for creating temporary email addresses and checking incoming messages using **Guerrilla Mail** and **Mail.tm**.

**Author:** Parsa-Azima  
**License:** GNU General Public License v2.0 or later (GPL-2.0-or-later)

## Features

- 📧 Create temporary email addresses.
- 🔄 Refresh your inbox to check for new messages.
- ✉️ Read received emails, including their subjects and senders.
- 🔀 Switch between Guerrilla Mail and Mail.tm.
- 📱 Interactive Telegram inline keyboards.
- 🛡️ HTML escaping for dynamically displayed content.
- ⚙️ Configure the Telegram bot token using an environment variable.
- 🔁 Automatic retry after polling errors.
- 💾 Lightweight in-memory user sessions.

## Supported Email Providers

| Provider | Features |
|---|---|
| Guerrilla Mail | Create temporary addresses, check inboxes, and read messages |
| Mail.tm | Create email accounts, authenticate, check inboxes, and read messages |

**Note:** Email availability, message delivery, and address expiration depend on the selected provider.

## Requirements

- Python 3.10 or newer recommended
- A Telegram bot token
- An internet connection
- Access to the Guerrilla Mail and Mail.tm APIs

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ParsaAzima/TempMailBot.git
cd TempMailBot
```

### 2. Create a virtual environment (recommended)

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install pyTelegramBotAPI requests
```

Alternatively, create a `requirements.txt` file containing:

```text
pyTelegramBotAPI
requests
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configure the bot token

Create a Telegram bot using [@BotFather](https://t.me/BotFather) and copy its token.

Set the `BOT_TOKEN` environment variable before running the bot.

**Windows PowerShell:**

```powershell
$env:BOT_TOKEN="YOUR_NEW_BOT_TOKEN"
```

**Windows Command Prompt:**

```cmd
set BOT_TOKEN=YOUR_NEW_BOT_TOKEN
```

**Linux / macOS:**

```bash
export BOT_TOKEN="YOUR_NEW_BOT_TOKEN"
```

Never publish your real bot token in a public repository.

### 5. Run the bot

If your Python file is named `bot.py`, execute:

```bash
python bot.py
```

You should see:

```text
Temporary Mail bot is running.
```

Open your bot in Telegram and send `/start`.

## Usage

1. Start the bot using `/start`.
2. Select **Create temporary email** to generate an address.
3. Select **Choose email service** to switch providers.
4. Use **Refresh inbox** to check for incoming emails.
5. Select a message to view its subject, sender, and text content.
6. Use the navigation buttons to return to your email or the main menu.

### Available Commands

| Command | Description |
|---|---|
| `/start` | Open the main menu |
| `/help` | Display the bot's main menu and help entry |
| `/cancel` | Return to the main menu |

## Project Structure

```text
temporary-mail-telegram-bot/
├── bot.py
├── requirements.txt
├── README.md
└── LICENSE
```

- `bot.py` — Main application, Telegram handlers, provider integrations, and user sessions.
- `requirements.txt` — Python dependencies.
- `README.md` — Project documentation.
- `LICENSE` — Full GPL-2.0-or-later license text.

## Configuration

The bot uses the following configuration values:

| Setting | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token, supplied through an environment variable |
| `GUERRILLA_API` | Guerrilla Mail API endpoint |
| `MAILTM_API` | Mail.tm API base URL |
| `HTTP_TIMEOUT` | HTTP request timeout in seconds |

The default HTTP timeout is 20 seconds.

## Important Limitations

- User sessions are stored in memory and are lost when the bot restarts.
- Temporary email addresses may expire or stop receiving messages.
- Guerrilla Mail and Mail.tm may impose their own restrictions or rate limits.
- The bot does not provide permanent email storage.
- Email contents are displayed as text; HTML email formatting is not fully rendered.
- The application relies on third-party APIs and requires internet access.

## Security and Privacy

- Never use temporary email addresses for sensitive accounts, financial services, or password recovery.
- Do not assume that a temporary inbox is private or permanently accessible.
- Keep your Telegram bot token and email account credentials secret.
- Avoid logging access tokens, passwords, or private email contents.
- Use environment variables or a secrets manager for sensitive configuration.
- Consider adding request rate limits and stronger session isolation before deploying the bot publicly.

## Troubleshooting

**The bot does not start**

Verify that Python and the required packages are installed and that `BOT_TOKEN` contains a valid token.

**Email creation fails**

Check your internet connection and verify that the selected provider's API is available.

**The inbox is empty**

Wait for the message to arrive, then press **Refresh inbox**. Some websites do not support temporary email domains.

**The bot stops responding**

Check the terminal for errors. The application retries Telegram polling after unexpected errors, but persistent API failures may require further investigation.

## License

This project is licensed under the **GNU General Public License v2.0 or later (GPL-2.0-or-later)**.

You may redistribute and modify the software under the terms of the license.

See the [GNU GPL v2 license](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) for details.

## Author

**Parsa-Azima**

Contributions, bug reports, and suggestions are welcome.
