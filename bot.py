import requests
import random
import sys
import yaml
import time
import pickle
from datetime import datetime, timedelta

class Discord:
    def __init__(self, t):
        self.base = "https://discord.com/api/v10"
        self.auth = {'authorization': t}

    def getMe(self):
        u = requests.get(self.base + "/users/@me", headers=self.auth).json()
        return u

    def getMessage(self, cid, l):
        u = requests.get(self.base + f"/channels/{cid}/messages?limit={l}", headers=self.auth).json()
        return u

    def sendMessage(self, cid, txt):
        u = requests.post(self.base + f"/channels/{cid}/messages", headers=self.auth, json={'content': txt}).json()
        return u

    def replyMessage(self, cid, mid, txt):
        u = requests.post(self.base + f"/channels/{cid}/messages", headers=self.auth,
                          json={'content': txt, 'message_reference': {'message_id': mid}}).json()
        return u

    def deleteMessage(self, cid, mid):
        u = requests.delete(self.base + f"/channels/{cid}/messages/{mid}", headers=self.auth)
        return u

def load_custom_responses():
    with open("custom.txt") as custom_file:
        custom_responses = custom_file.readlines()

    responses_dict = {}
    for line in custom_responses:
        key, values = line.strip().split('=')
        keywords = key.split(',')
        responses_dict.update({keyword.lower(): values.strip().split('|') for keyword in keywords})

    return responses_dict

def load_last_response_times():
    try:
        with open("last_response_times.pkl", "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return {}

def save_last_response_times(last_response_times):
    with open("last_response_times.pkl", "wb") as file:
        pickle.dump(last_response_times, file)

def main():
    with open('config.yaml') as cfg:
        conf = yaml.load(cfg, Loader=yaml.FullLoader)

    if not conf['BOT_TOKEN']:
        print("[!] Harap berikan token discord di config.yaml!")
        sys.exit()

    if not conf['CHANNEL_ID']:
        print("[!] Harap berikan ID channel di config.yaml!")
        sys.exit()

    custom_responses = load_custom_responses()
    last_response_times = load_last_response_times()

    while True:
        for token in conf['BOT_TOKEN']:
            try:
                for chan in conf['CHANNEL_ID']:
                    Bot = Discord(token)
                    me = ''  # Menghapus nama pengguna
                    messages = Bot.getMessage(chan, 1)
                    if messages:
                        last_message = messages[0]
                        received_message = last_message['content'].lower()
                        sender_id = last_message['author']['id']

                        # Periksa apakah pengirim pesan bukan bot itu sendiri
                        if sender_id != Bot.getMe()['id']:
                            keyword_found = False  # Tandai apakah kata kunci ditemukan dalam pesan

                            for keyword, responses in custom_responses.items():
                                # Pisahkan kata kunci menggunakan tanda koma
                                keywords = keyword.split(',')

                                # Periksa apakah setidaknya satu kata kunci ada di awal pesan
                                if any(received_message.startswith(kw.strip()) for kw in keywords):
                                    keyword_found = True

                                    # Periksa waktu terakhir respons berdasarkan pengguna dan kata kunci
                                    user_key = sender_id
                                    last_response_time = last_response_times.get(user_key, {})
                                    keyword_last_response_time = last_response_time.get(keyword, datetime.min)
                                    elapsed_time = datetime.now() - keyword_last_response_time

                                    if elapsed_time > timedelta(hours=3) or not keyword_last_response_time:
                                        # Hanya merespons setiap 3 jam atau jika belum pernah merespons sebelumnya
                                        reply = random.choice(responses)
                                        reply_with_name = f"{reply}"  # Tanpa nama pengguna

                                        Bot.replyMessage(chan, last_message['id'], reply_with_name)
                                        print("[{}][{}][REPLY] {}".format(me, chan, reply_with_name))

                                        # Update waktu terakhir respons untuk pengguna dan kata kunci tertentu
                                        last_response_time[keyword] = datetime.now()
                                        last_response_times[user_key] = last_response_time
                                        save_last_response_times(last_response_times)

                            # Tidak perlu respons default jika ada kata kunci yang cocok
                            if not keyword_found:
                                print("[{}][{}][NO REPLY]".format(me, chan))

            except:
                print(f"[Error] {token} : TOKEN TIDAK VALID / DIKELUARKAN DARI GUILD!")

        print("-------[ Jeda selama 15 detik ]-------")
        time.sleep(30)

if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f"{type(err).__name__} : {err}")
