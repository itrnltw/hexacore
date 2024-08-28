import requests
import asyncio
import aiohttp
import jwt
import os
import platform
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
                    print(f"{response.status} | Gagal!, percobaan {attempt + 1}", flush=True)
        except aiohttp.ClientConnectionError:
            print(f"{response.status} | Koneksi gagal, mencoba lagi {attempt + 1}", flush=True)
        except Exception as e:
            print(f"{response.status} | Error: {str(e)}, mencoba lagi {attempt + 1}", flush=True)
    
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

async def Balance(session, token, id):
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
    return await fetch(session, 'POST', URL, headers=headers, json={"taps": 250})

def buyTapPass(token):
    headers['Authorization'] = token
    URL = "https://ago-api.hexacore.io/api/buy-tap-passes"
    return requests.post(URL, headers=headers, json={"name":"7_days"}).json()

async def process_token(session, token):
    decoded = decode_jwt(token)
    if decoded is None:
        return
    
    getDaily = await dailyCek(session, token)
    claimDaily = await dailyReward(session, token, decoded['user_id'], int(getDaily['next']))
    availableTaps = await AvailableTaps(session, token)
    balance = await Balance(session, token, decoded['user_id'])
    click = await Clicked(session, token)
    
    print(f"==== {Fore.GREEN+bright}{decoded['username']}{Style.RESET_ALL} ====")
    print(f"Claim Daily\t: {Fore.GREEN+bright}Day-{getDaily['last']}{' | '+Fore.RED+ claimDaily.get('success', claimDaily.get('error', 'Mboh Cok!')) if getDaily.get('is_available') else ''}")
    print(f"Balance\t\t: {Fore.GREEN+bright if balance['balance'] != 0 else Fore.RED}{balance['balance']}{Style.RESET_ALL}")
    print(f"Available Taps\t: {Fore.GREEN+bright if availableTaps['available_taps'] != 0 else Fore.RED}{availableTaps['available_taps']}{Style.RESET_ALL}")
    print(f"Clicked\t\t: {Fore.GREEN+bright if click.get('success') == True else Fore.RED}{click.get('success')}{Style.RESET_ALL}\n")
    
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
        for query in readQuery():
            print(f"Get Token...")
            tokens.append(appAuth(query).get('token', 'NO TOKEN'))

        buy = False #if input("Buy tap pass (7_days)? (y/n): ").lower() == 'y' else False
        if buy:
            for token in tokens:
                beli = buyTapPass(token)
                print(f"Tap Pass: {Fore.GREEN+bright if beli.get('success', False) else Fore.RED}{next(iter(beli.values()))}{Style.RESET_ALL}")
        
        while True:
            if not tokens:
                break
            
            async with aiohttp.ClientSession() as session:
                tasks = [process_token(session, token) for token in tokens if token not in available]
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
