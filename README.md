# Zulip Telegram Forwarder

TeleZulip is a Python bot that forwards specific messages from Zulip to Telegram. Monitor your Zulip streams for important keywords and get instant notifications in your Telegram chat.

## Features

- Forward only messages containing specific text patterns (e.g., "wallet", "Wallet Extensions")
- Customize message format for each pattern
- Handle long messages by automatically splitting them into readable chunks
- Preserve message formatting
- Include sender name, stream, and topic information
- Handle connection errors gracefully

## Setup

1. **Create a Zulip Bot**:
   - Go to your Zulip settings
   - Navigate to "Your bots"
   - Click "Add a new bot"
   - Choose "Generic bot"
   - Note down the bot's email and API key

2. **Create a Telegram Bot**:
   - Open Telegram and search for "@BotFather"
   - Send `/newbot` command
   - Follow the instructions to create a bot
   - Note down the bot token you receive

3. **Get Your Telegram Chat ID**:
   - Add your bot to the target chat/group
   - Send a message to the chat
   - Visit `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
   - Look for the `chat.id` in the response

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure the Bot**:
   Copy `config.example.json` to `config.json` and edit with your credentials:
   ```json
   {
       "zulip": {
           "email": "your-bot-email@zulipchat.com",
           "api_key": "your-zulip-api-key",
           "site": "https://your-org.zulipchat.com"
       },
       "telegram": {
           "bot_token": "your-telegram-bot-token",
           "chat_id": "your-telegram-chat-id"
       },
       "message_filter": {
           "enabled": true,
           "patterns": [
               {
                   "text": "wallet",
                   "format": "💼 Wallet Update\nFrom: {sender}\nIn: {stream}/{topic}\nMessage: {content}"
               },
               {
                   "text": "Wallet Extensions",
                   "format": "🔌 Wallet Extensions Update\nFrom: {sender}\nIn: {stream}/{topic}\nMessage: {content}"
               }
           ]
       }
   }
   ```

   The message filter configuration allows you to:
   - Enable/disable message filtering with `enabled`
   - Define multiple patterns to match in messages
   - Customize the format of forwarded messages using these placeholders:
     - `{sender}`: The name of the message sender
     - `{stream}`: The Zulip stream name
     - `{topic}`: The topic name
     - `{content}`: The message content

6. **Run the Bot**:
   ```bash
   python zulip_to_telegram.py
   ```

## Note

Make sure your Zulip bot has access to the streams you want to monitor. You may need to subscribe the bot to specific streams in your Zulip organization.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
