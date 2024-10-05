import requests
import asyncio
import aiohttp
import jwt
import os
import platform
import random
import time
from datetime import datetime, timedelta
from colorama import Fore, Style, init

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
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
}

def readQuery():
    if os.path.exists('query.txt'):
        with open('query.txt', 'r') as file:
            return file.read().splitlines()
    else:
        print("File 'query.txt' tidak ditemukan.")
        return []

def hitung_mundur(timestamp):
    if isinstance(timestamp, int):
        sekarang = time.time()
        selisih = timestamp - sekarang
        return str(timedelta(seconds=int(selisih)))
    else:
        return None

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
                if response.status in [200, 403, 400, 500]:
                    return await response.json()
                else:
                    print(f"Gagal!, percobaan {attempt + 1}", flush=True)
        except aiohttp.ClientConnectionError:
            print(f"Koneksi gagal, mencoba lagi {attempt + 1}", flush=True)
        except Exception as e:
            print(f"Error: {str(e)}, mencoba lagi {attempt + 1}", flush=True)
    
    print(f"Gagal setelah 3 percobaan.", flush=True)
    return None

def appAuth(query):
    URL = "https://ago-api.hexacore.io/api/app-auth"
    return requests.post(URL, headers=headers, json={'data': query}).json()

async def dailyCek(session, token):
    headers['Authorization'] = token
    URL = "https://ago-api.hexacore.io/api/daily-checkin"
    return await fetch(session, 'GET', URL, headers=headers)

async def dailyReward(session, token, id, hari):
    headers['Authorization'] = token
    URL = "https://ago-api.hexacore.io/api/daily-checkin"
    data = {"day": hari}
    return await fetch(session, 'POST', URL, headers=headers, json=data)

async def booster(session, token):
    headers['Authorization'] = token
    URL = "https://ago-api.hexacore.io/api/activate-boosters"
    return await fetch(session, 'POST', URL, headers=headers)

async def getBalance(session, token, id):
    headers['Authorization'] = token
    URL = f"https://ago-api.hexacore.io/api/balance/{id}"
    return await fetch(session, 'GET', URL, headers=headers)

async def AvailableTaps(session, token):
    headers['Authorization'] = token
    URL = "https://ago-api.hexacore.io/api/available-taps"
    return await fetch(session, 'GET', URL, headers=headers)

async def Clicked(session, token):
    headers['Authorization'] = token
    URL = "https://ago-api.hexacore.io/api/mining-complete"
    acak = random.choice(range(20, 251, 20)) #awal, akhir, lompat
    return await fetch(session, 'POST', URL, headers=headers, json={"taps": acak}), acak

def buyTapPass(token):
    headers['Authorization'] = token
    URL = "https://ago-api.hexacore.io/api/buy-tap-passes"
    return requests.post(URL, headers=headers, json={"name":"7_days"}).json()

async def process_token(session, index, token):
    decoded = decode_jwt(token)
    if decoded is None:
        return
    
    getDaily = await dailyCek(session, token)
    claimDaily = await dailyReward(session, token, decoded['user_id'], int(getDaily.get('next', 'err')))
    availableTaps = await AvailableTaps(session, token)
    sisaBooster = (availableTaps.get('available_boosters', 0) - availableTaps.get('used_boosters', 0))
    balance = await getBalance(session, token, decoded['user_id'])
    click, jumlah_taps = await Clicked(session, token)
    balanceAwal = balance.get('balance',0)
    print(f"==== {Fore.GREEN+bright}{index+1}. {decoded['username']}{Style.RESET_ALL} ====")
    print(f"Claim Daily\t: {Fore.GREEN+bright}Day-{getDaily.get('last', 0)}{' | '+Fore.RED+ claimDaily.get('success', claimDaily.get('error', 0)) if getDaily.get('is_available', 0) else ''}{Fore.RED+' | -'+hitung_mundur(getDaily.get('available_at', 0))}")
    print(f"Balance\t\t: {Fore.GREEN+bright if balance.get('balance', 0) != 0 else Fore.RED}{'{:,}'.format(balance.get('balance','err')).replace(',', '.')}{Style.RESET_ALL}")
    print(f"Available Taps\t: {Fore.GREEN+bright if availableTaps.get('available_taps', 0) != 0 else Fore.RED}{'{:,}'.format(availableTaps.get('available_taps', 'err')).replace(',', '.')}{Style.RESET_ALL}")
    #sisaBooster = 0     #PAKSA SKIP BOOSTER
    print(f"Booster\t\t: {Fore.GREEN+bright if sisaBooster != 0 else Fore.RED}{sisaBooster}{Style.RESET_ALL}")
    noBooster = True
    if sisaBooster > 0 and availableTaps.get('available_taps', 0) > 0 and noBooster == False:
        total_jumlah_taps = 0
        boosternya = await booster(session, token)
        print(f"{next(iter(boosternya.values()))} Boostering, Wait 20 seconds...\n", end='\r', flush=True)
        indexnya = 0
        while availableTaps.get('available_taps', 0) >0:
            taps, jumlah_taps = await Clicked(session, token)
            total_jumlah_taps += jumlah_taps
            print(f"Boost Tapped\t: {Fore.GREEN+bright if taps.get('success','err') else Fore.RED}{taps.get('success','err')} | Total: {total_jumlah_taps} Taps{Style.RESET_ALL} {indexnya+1}s", end='\r', flush=True)
            indexnya += 1
            if click.get('success','err') == False or indexnya >=20:
                break
        balanceBoost :int = await getBalance(session, token, decoded['user_id'])
        print(f"\nTotal Booster\t: {balanceBoost.get('balance',0)}-{balanceAwal} = {Fore.GREEN+bright}{balanceBoost.get('balance',0)-balanceAwal} hex{Style.RESET_ALL}")
    print(f"Combo\t\t: Coming Soon")
    print(f"Tapped\t\t: {Fore.GREEN+bright if click.get('success','err') else Fore.RED}{click.get('success','err')} {jumlah_taps} Taps{Style.RESET_ALL}\n")
    
    global available
    if availableTaps['available_taps'] == 0:
        if token not in available:
            available.append(token)
        return False  # Don't execute again
    return True  # Continue execution

async def main():
    init(autoreset=True)
    try:
        tokens: list = []
        for index, query in enumerate(readQuery()):
            print(f"{index+1}. Get Token...", end='\r', flush=True)
            tokens.append(appAuth(query).get('token', 'NO TOKEN'))

        buy = True #if input("Buy tap pass (7_days)? (y/n): ").lower() == 'y' else False
        if buy:
            for index, token in enumerate(tokens):
                beli = buyTapPass(token)
                print(f"{index+1}. Tap Pass: {Fore.GREEN+bright if beli.get('success', False) else Fore.RED}{next(iter(beli.values()))}{Style.RESET_ALL}\n", end='\r', flush=True)
        
        while True:
            if not tokens:
                break
            
            async with aiohttp.ClientSession() as session:
                tasks = [process_token(session, index, token) for index, token in enumerate(tokens) if token not in available]
                results = await asyncio.gather(*tasks)

            if all(result is False for result in results):
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
