import os
import json
import platform
import urllib.parse
import aiohttp
import asyncio
import requests
import time
import random
from datetime import datetime, timedelta
from colorama import Fore, Style, init

bright = Style.BRIGHT

QUERY_FILE = 'query.txt'
TOKEN_FILE = 'acc.json'

def clear_console():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def readQuery():
    if os.path.exists(QUERY_FILE):
        with open(QUERY_FILE, 'r') as file:
            return file.read().splitlines()
    else:
        print(f"File {QUERY_FILE} tidak ditemukan.")
        return []

def hitung_mundur(timestamp):
    if isinstance(timestamp, int):
        sekarang = time.time()
        selisih = timestamp - sekarang
        return str(timedelta(seconds=int(selisih)))
    else:
        return None

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            tokens = json.load(f)
            for username, token_data in tokens.items():
                if isinstance(token_data, str):
                    tokens[username] = {
                        'token': token_data,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            f.close()
            return tokens
    return {}

def update_token(username, new_token):
    tokens = load_tokens()
    tokens[username] = {
        'token': new_token,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)
        f.close()
    
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

def generate_headers(token=None):
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json',
        'Origin': 'https://ago-wallet.hexacore.io',
        'Referer': 'https://ago-wallet.hexacore.io/',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0'
    }
    if token is None:
        headers.pop('Authorization', None)
    return headers

def get_token(query):
    return requests.post(url='https://ago-api.hexacore.io/api/app-auth', headers=generate_headers(), json={"data": query}).json()

def dailyCek(token):
    return requests.get(url='https://ago-api.hexacore.io/api/daily-checkin', headers=generate_headers(token)).json()

def dailyReward(token, hari):
    return requests.post(url='https://ago-api.hexacore.io/api/daily-checkin', headers=generate_headers(token), json={"day": hari}).json()

async def getBalance(session, token, user_id):
    return await fetch(session, 'GET', f'https://ago-api.hexacore.io/api/balance/{user_id}', generate_headers(token))

async def availableTaps(session, token):
    return await fetch(session, 'GET', 'https://ago-api.hexacore.io/api/available-taps', generate_headers(token))

async def clicked(session, token):
    acak = random.choice(range(20, 251, 20)) #awal, akhir, lompat
    return await fetch(session, 'POST', 'https://ago-api.hexacore.io/api/mining-complete', generate_headers(token), {"taps": acak}), acak

def buyTapPass(token):
    return requests.post(url='https://ago-api.hexacore.io/api/buy-tap-passes', headers=generate_headers(token), json={"name":"7_days"}).json()

async def proses_semua_akun(session, username, token, user_id):
    poin = await getBalance(session, token, user_id)
    tersedia = await availableTaps(session, token)
    click, jumlah_taps = await clicked(session, token)

    # print(cek)
    # print(beliTap)
    # print(harian)
    # print(tersedia)
    # print(poin)
    # print(click)
    # print(jumlah_taps)

    print(f"===={Fore.GREEN+bright} {username} {Style.RESET_ALL}====")
    
    print(f"Balance\t\t: {Fore.GREEN+bright}{'{:,}'.format(poin.get('balance','err')).replace(',', '.')}{Style.RESET_ALL}")
    print(f"Available Taps\t: {Fore.GREEN+bright if tersedia.get('available_taps', 'err') != 0 else Fore.RED}{'{:,}'.format(tersedia.get('available_taps', 'err')).replace(',', '.')}{Style.RESET_ALL}")
    print(f"Tapped\t\t: {Fore.GREEN+bright if click['success'] == True else Fore.RED}{click['success']} | {jumlah_taps} Taps{Style.RESET_ALL}\n")
    
    global proses_data
    if tersedia['available_taps'] == 0:
        if username in proses_data:  # Cek apakah username ada di proses_data
            del proses_data[username]  # Hapus dari proses_data
        return False  # Jangan eksekusi lagi
    return True  # Lanjutkan eksekusi

# Fungsi untuk menambahkan akun yang tersedia Tapsnya saja
def simpan_datanya(username, token, user_id):
    proses_data[username] = {  # Buat dictionary untuk setiap username
        'token': token,
        'user_id': user_id
    }

async def main():
    try:
        for query in readQuery():
            #initial
            sub = json.loads(urllib.parse.unquote(urllib.parse.parse_qs(query)['user'][0]))
            namaDepan = sub['first_name'] 
            username = sub['username']
            user_id = sub['id']

            tokens = load_tokens()
            ambil_Token = tokens.get(username)
            # print(f"{username} Login")
            if ambil_Token:
                token = ambil_Token.get('token')
                cek = dailyCek(token)
                if 'error' in cek == 'Unauthorized':  #VALIDASI TOKEN jika exired
                    token = get_token(query)['token']
                    if token: #Jika Token Berhasil di Generate
                        print(f"{username} {Fore.GREEN+bright}Berhasil generate token baru{Style.RESET_ALL}", flush=True)
                        update_token(username, token)
                    else:
                        print(f"{username} {Fore.RED}Gagal generate token baru{Style.RESET_ALL}", flush=True)
                        continue
                else:
                    print(f"{username} {Fore.GREEN+bright}Memakai Token yang sudah ada & valid{Style.RESET_ALL}", flush=True)
            else:
                print(f"{username} {Fore.RED}Tidak ada Token. Generate!{Style.RESET_ALL}", flush=True)
                token = get_token(query)['token']
                if token: #Jika Token Berhasil di Generate
                    print(f"{username} {Fore.GREEN+bright}Berhasil generate token baru{Style.RESET_ALL}", flush=True)
                    update_token(username, token)
                else:
                    print(f"{username} {Fore.RED}Gagal generate token baru. Skip...{Style.RESET_ALL}", flush=True)
                    continue
            if token: #VALIDASI jika Token VALID
                beliTap = buyTapPass(token)
                print(f"Buy Tap (7_days): {Fore.GREEN+bright if beliTap.get('success', '') else Fore.RED}{beliTap.get('success', next(iter(beliTap.values())))}{Style.RESET_ALL}")
                cek = dailyCek(token)
                harian = dailyReward(token, int(cek.get('next', 'err')))
                print(f"Claim Daily\t: {Fore.GREEN+bright}Day-{cek['last']} | {Fore.GREEN+bright + harian.get('success', harian.get('error', 0)) if cek.get('is_available', False) else Fore.RED + 'Wait -'+ hitung_mundur(cek.get('available_at', 0))}{Style.RESET_ALL}\n")
                simpan_datanya(username, token, user_id)
        

        global proses_data
        while True:
            # if not username in proses_data.items():
            #     break

            # for username, akun_data in proses_data.items():
            #     token = akun_data['token']
            #     user_id = akun_data['user_id']
            #     print(username)
            #     print(token)
            #     print(user_id)

            # print(proses_data.items())
            # if username in proses_data.items():
            #     print(username)
            

            async with aiohttp.ClientSession() as session:
                tasks = [proses_semua_akun(session, username, akun_data['token'], akun_data['user_id']) for username, akun_data in proses_data.items() if username in proses_data]
                results = await asyncio.gather(*tasks)
    
            if all(result is False for result in results):
                print('\nTidak ada "Available Taps" yang Tersisa')
                break
            # Menunggu 3 detik dan membersihkan konsol setelah semua token diproses
            await asyncio.sleep(2)
            clear_console()

        print("[EXIT]")
    except Exception as e:
        print(f"ERROR due to : {e}")

if __name__ == "__main__":
    try:
        proses_data = {}
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Stop]")