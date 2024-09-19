import aiohttp
import asyncio
import json
import time
import random
from colorama import Fore, init
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

# Inisialisasi colorama agar berfungsi di semua platform
init(autoreset=True)

# Inisialisasi Random User Agent
software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value, SoftwareName.EDGE.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value, OperatingSystem.MAC.value]
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

# URL untuk mengirim task dan mengambil balance
url_task = "https://api.agent301.org/completeTask"
url_balance = "https://api.agent301.org/getMe"

payload_task = json.dumps({
    "type": "video"
})

payload_balance = json.dumps({
    "referrer_id": 0
})

# Template header
headers_template = {
    'authority': 'api.agent301.org',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://telegram.agent301.org',
    'referer': 'https://telegram.agent301.org/',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
}

# Variabel untuk menyimpan total balance
total_balance = 0

# Fungsi untuk mengirim request balance
async def check_balance(session, authorization, query_num):
    global total_balance
    headers = headers_template.copy()
    headers['authorization'] = authorization  # Masukkan authorization yang sesuai
    headers['user-agent'] = user_agent_rotator.get_random_user_agent()  # Ambil user-agent secara acak

    try:
        async with session.post(url_balance, headers=headers, data=payload_balance) as response:
            res_text = await response.text()

            if response.status == 200:
                response_json = json.loads(res_text)
                balance = response_json["result"]["balance"]

                # Tampilkan balance dengan warna biru
                print(Fore.BLUE + f"Query {query_num}: Balance: {balance}")

                # Tambahkan balance ke total_balance
                total_balance += balance

            else:
                print(f"Query {query_num}: Failed to fetch balance, status code: {response.status}")

    except Exception as e:
        print(f"Error fetching balance for Query {query_num}: {e}")

# Fungsi untuk mengirim request task
async def send_task_request(session, authorization, query_num):
    headers = headers_template.copy()
    headers['authorization'] = authorization
    headers['user-agent'] = user_agent_rotator.get_random_user_agent()  # Ambil user-agent secara acak

    while True:
        try:
            async with session.post(url_task, headers=headers, data=payload_task) as response:
                res_text = await response.text()

                # Jika mendapatkan log 403 Forbidden, tampilkan "Sudah Limit" dengan warna merah
                if "403" in res_text and "Forbidden" in res_text:
                    print(Fore.RED + f"Query {query_num}: Sudah Limit")
                    break  # Hentikan loop dan lanjut ke query berikutnya

                # Jika internal server error, tetap lanjutkan memproses query yang sama
                elif '"statusCode":500' in res_text:
                    print(f"Query {query_num}: Unexpected response {res_text}")
                    await asyncio.sleep(5)  # Jeda sebelum mencoba lagi

                # Jika respons sukses dan mengandung is_completed true, tampilkan reward dan balance
                elif '"is_completed":true' in res_text:
                    response_json = json.loads(res_text)
                    reward = response_json["result"]["reward"]
                    balance = response_json["result"]["balance"]

                    # Tampilkan log Reward dan Balance dengan warna hijau
                    print(Fore.GREEN + f"Query {query_num}: Reward: {reward}, Balance: {balance}")

                    await asyncio.sleep(5)  # Jeda dan proses query yang sama lagi

                # Jika respons tidak sesuai dengan kondisi di atas, lanjutkan ke query berikutnya
                else:
                    print(f"Query {query_num}: Unexpected response {res_text}")
                    break
        except Exception as e:
            print(f"Error with Query {query_num}: {e}")
            break

# Fungsi utama untuk memproses satu per satu authorization
async def process_authorizations():
    async with aiohttp.ClientSession() as session:
        while True:
            with open('query.txt', 'r') as file:
                authorizations = [line.strip() for line in file if line.strip()]
            
            for i, auth in enumerate(authorizations, start=1):
                await send_task_request(session, auth, i)  # Kirim query task terlebih dahulu
                await check_balance(session, auth, i)  # Cek balance setelah task
                await asyncio.sleep(5)  # Jeda 5 detik sebelum melanjutkan ke query berikutnya

            # Setelah semua query selesai, tampilkan total balance
            print(Fore.CYAN + f"Total Balance Keseluruhan: {total_balance}")
            break  # Keluar dari loop setelah semua query selesai

async def main():
    duration = 10 * 60 * 60  # 10 jam dalam detik

    while True:
        # Proses semua query dari file 'query.txt'
        await process_authorizations()

        # Mulai hitungan mundur untuk jeda selama 10 jam sebelum memproses ulang query
        cycle_start_time = time.time()
        cycle_end_time = cycle_start_time + duration

        while (time.time() < cycle_end_time):
            remaining_time = cycle_end_time - time.time()
            hours, rem = divmod(remaining_time, 3600)
            minutes, seconds = divmod(rem, 60)

            # Tampilkan hitung mundur waktu tersisa
            print(Fore.CYAN + f"Menjalankan lagi dalam... Waktu tersisa: {int(hours)} jam, {int(minutes)} menit, {int(seconds)} detik", end="\r")

            await asyncio.sleep(1)  # Update hitung mundur setiap detik

        print(Fore.YELLOW + "\nWaktu jeda 10 jam selesai, memulai kembali dari query pertama...")


if __name__ == "__main__":
    asyncio.run(main())