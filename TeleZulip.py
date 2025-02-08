import zulip
import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

class TeleZulip:
    def __init__(self, zulip_config: Dict[str, str], telegram_token: str, telegram_chat_id: str, message_filter: Dict[str, Any]):
        # Initialize Zulip client
        self.client = zulip.Client(**zulip_config)
        
        # Telegram configuration
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_api_url = f"https://api.telegram.org/bot{telegram_token}"

        # Message filter configuration
        self.message_filter = message_filter

    def send_to_telegram(self, message: str) -> None:
        """Send a message to Telegram."""
        # Telegram message limit is 4096 characters
        MAX_LENGTH = 4000  # Leave some room for formatting

        def chunk_message(text: str, chunk_size: int) -> List[str]:
            """Split message into chunks of specified size."""
            return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

        try:
            if len(message) > MAX_LENGTH:
                chunks = chunk_message(message, MAX_LENGTH)
                for i, chunk in enumerate(chunks, 1):
                    if len(chunks) > 1:
                        chunk = f"Part {i}/{len(chunks)}\n\n{chunk}"
                    
                    url = f"{self.telegram_api_url}/sendMessage"
                    data = {
                        "chat_id": self.telegram_chat_id,
                        "text": chunk,
                        "parse_mode": "HTML"
                    }
                    response = requests.post(url, json=data)
                    response.raise_for_status()
                    print(f"Successfully sent message part {i}/{len(chunks)} to Telegram")
            else:
                url = f"{self.telegram_api_url}/sendMessage"
                data = {
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, json=data)
                response.raise_for_status()
                print(f"Successfully sent message to Telegram")
        except requests.exceptions.RequestException as e:
            print(f"Error sending to Telegram: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Telegram API Response: {e.response.json()}")
            raise

    def format_message(self, msg: Dict[str, Any], pattern: Dict[str, str]) -> str:
        """Format Zulip message for Telegram using the specified pattern format."""
        try:
            format_str = pattern.get("format", "{sender} posted in {stream}/{topic}: {content}")
            return format_str.format(
                sender=msg["sender_full_name"],
                stream=msg["display_recipient"],
                topic=msg["subject"],
                content=msg["content"]
            )
        except KeyError as e:
            print(f"Error formatting message - missing key: {e}")
            print(f"Message structure: {json.dumps(msg, indent=2)}")
            raise

    def should_forward_message(self, content: str) -> Dict[str, str]:
        """Check if message should be forwarded based on filter patterns."""
        if not self.message_filter.get("enabled", False):
            return None

        patterns = self.message_filter.get("patterns", [])
        for pattern in patterns:
            if pattern["text"].lower() in content.lower():
                return pattern
        return None

    def handle_message(self, msg: Dict[str, Any]) -> None:
        """Handle incoming Zulip message."""
        try:
            # Skip messages sent by the bot itself
            if msg["sender_email"] == self.client.email:
                return

            print(f"\nReceived message from {msg['sender_full_name']} in {msg['display_recipient']}/{msg['subject']}")
            
            # Check if message matches any patterns
            pattern = self.should_forward_message(msg["content"])
            if pattern:
                print(f"Message matches pattern: {pattern['text']}")
                formatted_message = self.format_message(msg, pattern)
                self.send_to_telegram(formatted_message)
            else:
                print("Message doesn't match any patterns, skipping")
                
        except Exception as e:
            print(f"Error handling message: {e}")
            print(f"Message content: {json.dumps(msg, indent=2)}")

    def start(self) -> None:
        """Start listening for Zulip messages."""
        print("Starting Zulip to Telegram forwarder...")
        print(f"Message filtering is {'enabled' if self.message_filter.get('enabled', False) else 'disabled'}")
        if self.message_filter.get("enabled", False):
            patterns = self.message_filter.get("patterns", [])
            print(f"Watching for {len(patterns)} message pattern(s)")
            for pattern in patterns:
                print(f"- Pattern: '{pattern['text']}'")
        
        while True:
            try:
                print("\nRegistering new queue with Zulip...")
                queue_id = self.client.register(event_types=["message"])["queue_id"]
                print(f"Queue registered successfully: {queue_id}")
                
                last_event_id = -1
                while True:
                    print(f"\nGetting events since ID: {last_event_id}")
                    response = self.client.get_events(queue_id=queue_id, last_event_id=last_event_id)
                    
                    if "events" not in response:
                        print(f"Unexpected response from Zulip: {json.dumps(response, indent=2)}")
                        raise KeyError("No 'events' in response")
                    
                    for event in response["events"]:
                        if event["type"] == "message":
                            self.handle_message(event["message"])
                        last_event_id = max(last_event_id, event["id"])
                    
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Waiting 5 seconds before reconnecting...")
                time.sleep(5)

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError:
        print(f"Invalid JSON in config file: {config_path}")
        raise

def main():
    # Load configuration from config file
    config = load_config()
    
    # Extract configurations
    zulip_config = config["zulip"]
    telegram_config = config["telegram"]
    message_filter = config.get("message_filter", {"enabled": False, "patterns": []})
    
    # Validate configuration
    required_zulip = ["email", "api_key", "site"]
    required_telegram = ["bot_token", "chat_id"]
    
    missing_zulip = [key for key in required_zulip if key not in zulip_config]
    missing_telegram = [key for key in required_telegram if key not in telegram_config]
    
    if missing_zulip or missing_telegram:
        if missing_zulip:
            print(f"Missing required Zulip config: {', '.join(missing_zulip)}")
        if missing_telegram:
            print(f"Missing required Telegram config: {', '.join(missing_telegram)}")
        return
    
    # Start the bot
    bot = TeleZulip(
        zulip_config=zulip_config,
        telegram_token=telegram_config["bot_token"],
        telegram_chat_id=telegram_config["chat_id"],
        message_filter=message_filter
    )
    bot.start()

if __name__ == "__main__":
    main()
