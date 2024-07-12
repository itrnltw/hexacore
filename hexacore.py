import requests
import asyncio
import aiohttp
import jwt
import os
import platform
from colorama import Fore, Back, Style, init

bright = Style.BRIGHT

def clear_console():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

headers = {
    'Content-Type': 'application/json',
    'Origin': 'https://ago-wallet.hexacore.io',
    'Referer': 'https://ago-wallet.hexacore.io/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
}

def read_tokens():
    if os.path.exists('token.txt'):
        with open('token.txt', 'r') as file:
            return file.read().splitlines()
    else:
        print("File 'token.txt' tidak ditemukan.")
        return []

# Fungsi untuk decode token JWT
def decode_jwt(token):
    try:
        # Decoding the JWT token without verification
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

async def fetch(session, method, url, headers=None, json=None):
    for attempt in range(3):
        try:
            async with session.request(method, url, headers=headers, json=json) as response:
                if response.status == 200 or response.status == 403 or response.status == 400:
                    return await response.json()
                else:
                    print(f"{response.status} | Gagal!, percobaan {attempt + 1}", flush=True)
        except aiohttp.ClientConnectionError:
            print(f"{response.status} | Koneksi gagal, mencoba lagi {attempt + 1}", flush=True)
        except Exception as e:
            print(f"{response.status} | Error: {str(e)}, mencoba lagi {attempt + 1}", flush=True)
    
    print(f"Gagal setelah 3 percobaan.", flush=True)
    return None

async def dailyReward(session, token, id):
    headers['Authorization'] = token
    URL = "https://ago-api.onrender.com/api/daily-reward"
    return await fetch(session, 'POST', URL, headers=headers, json={"user_id": id})

async def Balance(session, token, id):
    headers['Authorization'] = token
    URL = f"https://ago-api.onrender.com/api/balance/{id}"
    return await fetch(session, 'GET', URL, headers=headers)

async def AvailableTaps(session, token):
    headers['Authorization'] = token
    URL = "https://ago-api.onrender.com/api/available-taps"
    return await fetch(session, 'GET', URL, headers=headers)

async def Clicked(session, token):
    headers['Authorization'] = token
    URL = "https://ago-api.onrender.com/api/mining-complete"
    return await fetch(session, 'POST', URL, headers=headers, json={"taps": 25})

def buyTapPass(token):
    headers['Authorization'] = token
    URL = "https://ago-api.onrender.com/api/buy-tap-passes"
    return requests.post(URL, headers=headers, json={"name":"7_days"}).json()

async def process_token(session, token):
    decoded = decode_jwt(token)
    if decoded is None:
        return

    daily = await dailyReward(session, token, decoded['user_id'])
    availableTaps = await AvailableTaps(session, token)
    balance = await Balance(session, token, decoded['user_id'])
    click = "Success" if (await Clicked(session, token))['success'] else "Gagal"
    
    print(f"==== {Fore.GREEN+bright}{decoded['username']}{Style.RESET_ALL} ====")
    print(f"Balance\t\t: {Fore.GREEN+bright if balance['balance'] != 0 else Fore.RED}{balance['balance']}{Style.RESET_ALL}")
    print(f"Available Taps\t: {Fore.GREEN+bright if availableTaps['available_taps'] != 0 else Fore.RED}{availableTaps['available_taps']}{Style.RESET_ALL}")
    print(f"Clicked\t\t: {Fore.GREEN+bright if click=='Success' else Fore.RED}{click}{Style.RESET_ALL}\n")
    
    global available, tokens
    if availableTaps['available_taps'] == 0:
        available.append(decoded['username'])

def banner():
    
    print(fr'''{Fore.GREEN+bright}
 __        ___       _             __      _ _ 
 \ \      / (_)_ __ | |_ ___ _ __ / _| ___| | |
  \ \ /\ / /| | '_ \| __/ _ \ '__| |_ / _ \ | |
   \ V  V / | | | | | ||  __/ |  |  _|  __/ | |
    \_/\_/  |_|_| |_|\__\___|_|  |_|  \___|_|_|
                    HEXACORE BOT
          {Style.RESET_ALL}''')

async def main():
    init(autoreset=True)
    banner()
    try:
        tokens = read_tokens()
        buy = True if input("Buy tap pass (7_days)? (y/n): ").lower() == 'y' else False
        if buy:
            for token in tokens:
                beli = buyTapPass(token)
                print(f"Tap Pass: {Fore.GREEN+bright if beli.get('success', False) else Fore.RED}{next(iter(beli.values()))}{Style.RESET_ALL}")
        while True:
            if not tokens:
                break
            
            async with aiohttp.ClientSession() as session:
                tasks = [process_token(session, token) for token in tokens]
                await asyncio.gather(*tasks)
            
            if len(available) == len(tokens):
                print('\nTidak ada "Available Taps" yang Tersisa\nKELUAR')
                break

            # Menunggu 3 detik dan membersihkan konsol setelah semua token diproses
            await asyncio.sleep(2)
            clear_console()

    except KeyboardInterrupt:
        print("Eksekusi dihentikan oleh pengguna.")

if __name__ == "__main__":
    available = []
    asyncio.run(main())