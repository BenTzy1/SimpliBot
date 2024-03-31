import telebot
import random
import string
import re
from requests.structures import CaseInsensitiveDict
import base64
import datetime
import requests
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from keep_alive import keep_alive

# Initialize the Telegram bot
bot = Bot(token=os.environ.get('token'))
dp = Dispatcher(bot)

# Dictionary to store authentication keys and activation status
auth_keys = {}

# Load authentication keys from file
with open('keys.txt', 'r') as keys_file:
    for line in keys_file:
        user_id, auth_key, activated = line.strip().split(':')
        auth_keys[int(user_id)] = {'auth_key': auth_key, 'activated': bool(int(activated))}

# Function to generate timestamp
def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Function to load accounts from a file
def load_accounts(filename):
    accounts = []
    with open(filename, 'r') as file:
        for line in file:
            account_info = line.strip().split(',')
            accounts.append(account_info)
    return accounts

# Function to send a message asynchronously
async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        print(f"Error sending message: {e}")

# Function to generate an authorization key based on Telegram username and ID
def get_authorization_key(telegram_username, telegram_id):  
    username_bytes = str(telegram_username).encode()
    id_bytes = str(telegram_id).encode()
    authorization_key_bytes = base64.b64encode(username_bytes) + b'|' + base64.b64encode(id_bytes)
    return authorization_key_bytes.decode()

# Function to generate a random password
def generate_random_password():
    letters_count = random.randint(5, 10)
    digits_count = 3
    random_letters = ''.join(random.choice(string.ascii_letters) for _ in range(letters_count))
    random_digits = ''.join(random.choice(string.digits) for _ in range(digits_count))
    password = random_letters + random_digits
    return password

# Function to clean response text
def clean_response_text(response_text):
    cleaned_text = re.sub(r'[^ -~]+', '', response_text)
    return cleaned_text

# Function to fetch the IP address using a proxy
def fetch_ip(proxy):
    try:
        response = requests.get('http://httpbin.org/ip', proxies=proxy)
        return response.json()['origin']
    except requests.RequestException as e:
        return f"Error fetching IP: {e}"

# Function to perform auto registration
def auto_register(inv_code, proxy):
    url = "https://api.711bet2.com/gw/login/register"
    headers = CaseInsensitiveDict({
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Referer": "https://711bet2.com/",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "U-Devicetype": "pc",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    })

    phone_number = f"+63|9{random.randint(111111111, 999999999)}"
    random_password = generate_random_password()

    payload = {
        "invite_code": inv_code,
        "agreeOnPromos": True,
        "account_value": phone_number,
        "account_type": 1,
        "password": random_password,
        "agreeOnState": True,
        "extra": {"from": "act_raffle"},
        "flow_id": ""
    }

    current_ip = fetch_ip(proxy)

    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxy)
        response.raise_for_status()
        cleaned_text = clean_response_text(response.text)

        if '{"code":6,"msg":"already exists"}' in cleaned_text:
            print("Invitation code already exists. Skipping registration.")
            return None

        data = response.json().get('data', {})
        user_id = data.get('user_id', 'N/A')
        token = data.get('token', 'N/A')

        if user_id == 'N/A' or token == 'N/A':
            raise ValueError("Failed to extract user_id or token from the registration response.")

        return (current_ip, random_password, phone_number, user_id, token)
    except Exception as e:
        print(f"Error during auto registration: {e}")
        return None

# Function to perform auto recharge
def auto_recharge(user_id, token, amount, currency, typ, pay_method, proxy):
    recharge_url = "https://api.711bet2.com/user/recharge"
    headers = CaseInsensitiveDict({
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"{token};{user_id}",
        "Content-Type": "application/json",
        "Referer": "https://711bet2.com/",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "U-Devicetype": "pc",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    })

    recharge_payload = {
        "amount": "100",
        "currency": "PHP",
        "data": {"typ": "GCASHORIGIN", "pay_method": "electronic_wallet"},
        "pay_method": "electronic_wallet",
        "typ": "GCASHORIGIN",
        "device": "pc",
        "task_id": "-1",
        "token": token,
        "user_id": user_id
    }

    try:
        response = requests.post(recharge_url, json=recharge_payload, proxies=proxy)
        response.raise_for_status()

        if '{"code":200,"message' in response.text:
            responseData = response.json()
            paymentLink = responseData['data']['pay_method']['cashier']
            return True, paymentLink
        else:
            return False, response.text
    except Exception as e:
        print(f"Error during auto recharge: {e}")
        return False, f"Error during auto recharge: {e}"

# Function to handle the /start command
@bot.message_handler(commands=['start'])
async def handle_start(message):
    welcome_message = ("Welcome to Simpli Noob Bot!\n\n"
                       "The only function available for now is Boosting.\n"
                       "For other concerns please input\n"
                       "/help\n")
    await message.reply(welcome_message)

# Function to handle the /help command
@bot.message_handler(commands=['help'])
async def handle_help(message):
    help_message = ("/help - shows all of the available commands\n\n"
                    "/auth - shows authentication key to activate your account\n"
                    "        If your account is not activated, please DM @simpli100 for activation\n\n"
                    "/boost - boost your account. Format: /boost INVITATION_CODE number_of_boosts\n"
                    "         Example: /boost 65f394375c041c198ad8b0c3 2\n"
                    "               REMINDER MAX BOOST IS 5 FOR NOT LAGGY SERVER")
    await message.reply(help_message)

# Function to handle the /activate command
@bot.message_handler(commands=['activate'])
async def handle_activate(message):
    if message.from_user.id == 6589378584:  # Assuming 6589378584 is the admin user ID
        command_parts = message.text.split()
        if len(command_parts) == 2:
            auth_key = command_parts[1]
            if auth_key in (data['auth_key'] for data in auth_keys.values()):
                user_id = next((uid for uid, data in auth_keys.items() if data['auth_key'] == auth_key), None)
                if user_id:
                    auth_keys[user_id]['activated'] = True
                    with open('bot/keys.txt', 'r') as keys_file:
                        lines = keys_file.readlines()
                    with open('bot/keys.txt', 'w') as keys_file:
                        for line in lines:
                            if line.startswith(f"{user_id}:{auth_key}:"):
                                keys_file.write(f"{user_id}:{auth_key}:1\n")  # 1 indicates activated
                            else:
                                keys_file.write(line)
                    await message.reply("Authentication key activated successfully!")
                else:
                    await message.reply("User ID not found for the provided authentication key.")
            else:
                await message.reply("Authentication key not found.")
        else:
            await message.reply("Invalid command format. Please use /activate <authentication_key>")
    else:
        await message.reply("You are not authorized to use this command.")

# Function to handle the /deactivate command
@bot.message_handler(commands=['deactivate'])
async def handle_deactivate(message):
    if message.from_user.id == 6589378584:  # Assuming 6589378584 is the admin user ID
        command_parts = message.text.split()
        if len(command_parts) == 2:
            auth_key = command_parts[1]
            user_id = next((uid for uid, data in auth_keys.items() if data['auth_key'] == auth_key), None)
            if user_id:
                auth_keys[user_id]['activated'] = False
                with open('bot/keys.txt', 'r') as keys_file:
                    lines = keys_file.readlines()
                with open('bot/keys.txt', 'w') as keys_file:
                    for line in lines:
                        if line.startswith(f"{user_id}:{auth_key}:"):
                            keys_file.write(f"{user_id}:{auth_key}:0\n")  # 0 indicates not activated
                        else:
                            keys_file.write(line)
                await message.reply("Authentication key deactivated successfully!")
            else:
                await message.reply("Authentication key not found.")
        else:
            await message.reply("Invalid command format. Please use /deactivate <authentication_key>")
    else:
        await message.reply("You are not authorized to use this command.")

# Function to handle the /boost command
@bot.message_handler(commands=['boost'])
async def handle_boost(message):
    user_id = message.from_user.id
    if user_id in auth_keys and auth_keys[user_id]['activated']:
        command_parts = message.text.split()
        if len(command_parts) < 3:
            await message.reply("Error: Command Error Format: /boost Inv_Code_here number_of_boosts")
            return

        inv_code = command_parts[1]
        num_boosts = int(command_parts[2])

        proxy_host = "rp.proxyscrape.com"
        proxy_port = 6060
        proxy_username = "6m6o59u1ws8tv2k"
        proxy_password = "3w3tzaf5recglxg"
        proxy = {
            'http': f'http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}',
            'https': f'http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}',
        }

        initial_response = await message.reply("PLEASE WAIT 1-3 MINS\nBOOSTING IS ON PROCESS")
        boosting_messages[message.chat.id] = initial_response.message_id

        successful_accounts = []
        failed_accounts = 0
        for _ in range(num_boosts):
            result = auto_register(inv_code, proxy)
            if result:
                ip_address = result[0]
                password = result[1]
                phone_number = result[2].split('|')[-1]
                
                success, payment_link = auto_recharge(result[3], result[4], "100", "PHP", "GCASHORIGIN", "electronic_wallet", proxy)
                if success:
                    account_info = f"IP Address: {ip_address}\nPassword: {password}\nPhone: {phone_number}\nPayment Link: {payment_link}"
                    successful_accounts.append(account_info)
                    print("Boosted successfully:")
                    print(account_info)
                else:
                    print("Failed to recharge. Skipping this account.")
                    failed_accounts += 1
            else:
                print("Failed to auto-register.")
                failed_accounts += 1
        
        if len(successful_accounts) == num_boosts:
            accounts_message = "\n\n".join(successful_accounts)
            await message.reply(f"Boosted successfully:\n\n{accounts_message}")
        else:
            success_count = len(successful_accounts)
            await message.reply(f"Boosted successfully: {success_count}\nFailed to boost: {failed_accounts}")

        chat_id = message.chat.id
        if chat_id in boosting_messages:
            await bot.delete_message(chat_id, boosting_messages[chat_id])
            del boosting_messages[chat_id]
    else:
        await message.reply("You are not authorized to use this command. Please activate your authentication key using /auth.")

# Function to handle the /auth command
@bot.message_handler(commands=['auth'])
async def handle_auth(message):
    user_id = message.from_user.id
    username = message.from_user.username
    try:
        # Generate authentication key
        auth_key = get_authorization_key(username, user_id)
        
        # Write authentication key to keys.txt file
        with open('bot/keys.txt', 'a') as keys_file:
            keys_file.write(f"{user_id}:{auth_key}:0\n")  # 0 indicates not activated

        # Store authentication key and activation status in auth_keys dictionary
        auth_keys[user_id] = {'auth_key': auth_key, 'activated': False}

        # Reply to the user with the generated authentication key
        await message.reply(f"Your authentication key: {auth_key}")
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        await message.reply("An error occurred during authentication. Please try again later.")

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp)
