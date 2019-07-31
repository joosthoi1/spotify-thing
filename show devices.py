import tkinter as tk
import spotify_wrapper
import json
import requests
import time

class main:
    def __init__(self):
        self.root = tk.Tk()

        with open("config.json", 'r') as file:
            config = json.loads(file.read())
            username = config['username']
            client_id = config['client_id']
            client_secret = config['client_secret']

        scope = 'user-library-read user-modify-playback-state user-read-playback-state'

        s =spotify_wrapper.Spotify()
        self.token = s.get_token(
            username = username,
            client_id=client_id,
            client_secret=client_secret,
            scope = scope,
            redirect_uri='http://google.com/'
        )

        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }

        self.ids = []

        while True:
            response = requests.get(
                "https://api.spotify.com/v1/me/player/devices",
                headers=self.headers
            )
            if response.status_code == 429:
                time.sleep(1)
            else:
                devices = response.json()['devices']
                for i in devices:
                    if 'id' in i:
                        if i['id'] not in self.ids:
                            self.ids.append(i['id'])
                            tk.Button(
                                self.root,
                                text=f"{i['name']} - {i['type']}",
                                width=50
                            ).pack(side='top',anchor='nw')
            self.root.update()



if __name__ == "__main__":
    main()
