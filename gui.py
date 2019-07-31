import tkinter as tk
from tkinter import ttk
from functools import partial
import spotipy
import spotipy.util as util
import requests
import time
import threading
import json
import datetime
import sys


class main:
    def __init__(self, device_id=None):
        self.root = tk.Tk()
        self.root.title("Spotify")

        self.playing = {}

        self.kill_thread = False
        self.index = 0
        self.uri_entries = []
        self.start_entries = []
        self.end_entries = []
        self.time2 = 0
        self.old_volume = 0
        previous_ms = 0
        with open("config.json", 'r') as file:
            config = json.loads(file.read())
            username = config['username']
            client_id = config['client_id']
            client_secret = config['client_secret']

        scope = 'user-library-read user-modify-playback-state user-read-playback-state'


        self.token = util.prompt_for_user_token(
            username,
            scope,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri='http://google.com/'
        )

        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }

        play_thread = threading.Thread(target=self.listener)
        play_thread.isDeamon = True
        play_thread.start()

        self.add_scrollbar()
        for i in range(8):
            self.add_uri()
        self.add_lower_frame()
        self.add_volume()
        self.buttons()

        while self.playing == {}:
            self.root.update()

        print(json.dumps(self.playing, indent=4))
        while True:
            try:
                if 'item' in self.playing:
                    item = self.playing['item']
                    if 'duration_ms' in item:
                        ms = self.playing['item']['duration_ms']
                        self.scale['to'] = ms
                        if not previous_ms == ms:
                            previous_ms = ms
                            seconds = int((ms/1000)%60)
                            minutes = int((ms/(1000*60)))
                            format = '{}:{}'.format(
                                str(minutes).rjust(2, '0'),
                                str(seconds).rjust(2, '0')
                            )
                            self.label4['text'] = format

                    if 'device' in self.playing:
                        device = self.playing['device']
                        if 'volume_percent' in device:
                            volume = device['volume_percent']
                            if volume != self.old_volume:
                                self.old_volume = volume
                                self.volume_scale.set(volume)
                                self.root.update()

                    if 'name' in item:
                        self.label1['text'] = item['name']

                    if 'artists' in item:
                        artists = ", ".join(i['name'] for i in item['artists'])
                        self.label2['text'] = artists

                if 'progress_ms' in self.playing:
                    ms = self.playing['progress_ms']
                    self.scale.set(ms)
                    seconds = int((ms/1000)%60)
                    minutes = int((ms/(1000*60)))
                    format = '{}:{}'.format(
                        str(minutes).rjust(2, '0'),
                        str(seconds).rjust(2, '0')
                    )
                    self.label3['text'] = format
                if 'shuffle_state' in self.playing:
                    self.shuffle_var.set(self.playing['shuffle_state'])
                if 'repeat_state' in self.playing:
                    if self.playing['repeat_state'] == 'track':
                        self.repeat_var.set(True)
                    else:
                        self.repeat_var.set(False)
                if 'is_playing' in self.playing:
                    self.play_var.set(self.playing['is_playing'])
                    if self.play_var.get():
                        self.play_button['text'] = '⏸'
                    else:
                        self.play_button['text'] = '▶'



                self.root.update()
            except tk.TclError:
                break
        self.kill_thread = True
        play_thread.join()

    def scale_command(self, value):
        if 'progress_ms' in self.playing:
            if int(value) != self.playing['progress_ms']:
                requests.put(
                    "https://api.spotify.com/v1/me/player/seek",
                    headers=self.headers,
                    params={"position_ms":int(value)}
                )

    def volume_command(self, value):
        if int(value) != self.old_volume:
            params = {
                'volume_percent': value
            }
            requests.put(
                'https://api.spotify.com/v1/me/player/volume',
                headers = self.headers,
                params = params
            )

    def add_lower_frame(self):
        self.lower_frame = tk.Frame(self.canvas)
        self.lower_frame.grid_propagate = False
        self.lower_frame.pack_propagate = False
        self.lower_frame.pack(side='bottom', anchor='w')
        self.label1 = tk.Label(
            self.lower_frame,
            text = '',
            anchor = 'w',
            justify='left',
            wraplength = 200,
            width=28
        )
        self.label2 = tk.Label(
            self.lower_frame,
            text = '',
            anchor = 'sw',
            wraplength = 200,
            width=28
        )
        self.label3 = tk.Label(self.lower_frame, text = '', anchor = 'sw',width=4)
        self.label4 = tk.Label(self.lower_frame, text = '', anchor = 'sw')
        self.label1.grid(row=0,column=0,sticky='sw')
        self.label2.grid(row=1,column=0,sticky='sw')
        self.label3.grid(row=1,column=1,sticky='sw')
        self.label4.grid(row=1,column=3,sticky='sw')
        self.scale = tk.Scale(
            self.lower_frame,
            orient='horizontal',
            length=260,
            command=self.scale_command,
            showvalue=False
        )
        self.scale.grid(row=1,column=2,sticky='s')

        self.buttons_frame = tk.Frame(self.lower_frame)

    def add_volume(self):
        tk.Label(self.lower_frame,text='Volume:').grid(row=1, column=4)
        self.volume_scale = tk.Scale(
            self.lower_frame,
            command = self.volume_command,
            orient= 'horizontal',
            showvalue=False,
        )
        self.volume_scale.grid(row=1,column=5)

    def buttons(self):
        self.button_frame = tk.Frame(self.lower_frame)
        self.button_frame.grid(row=0, column=2)
        self.shuffle_var = tk.BooleanVar()
        self.play_var = tk.BooleanVar()
        self.repeat_var = tk.BooleanVar()
        tk.Checkbutton(
            self.button_frame,
            text='Shuffle',
            indicatoron=False,
            variable = self.shuffle_var,
            command=self.shuffle
        ).pack(side='left')
        tk.Button(
            self.button_frame,
            text='⏮️',
            command = self.previous
        ).pack(side='left')
        self.play_button = tk.Checkbutton(
            self.button_frame,
            text='⏸',
            variable = self.play_var,
            indicatoron=False,
            command=self.play
        )
        self.play_button.pack(side='left')
        tk.Button(
            self.button_frame,
            text='⏭',
            command=self.next
        ).pack(side='left')
        tk.Checkbutton(
            self.button_frame,
            text='Repeat',
            variable = self.repeat_var,
            command=self.repeat,
            indicatoron=False
        ).pack(side='left')

    def shuffle(self):
        shuffle = self.shuffle_var.get()
        params = {
            "state":shuffle
        }
        r = requests.put(
            "https://api.spotify.com/v1/me/player/shuffle",
            headers = self.headers,
            params=params
        )
        print(r)

    def play(self):
        play = self.play_var.get()
        if play:

            r = requests.put(
                "https://api.spotify.com/v1/me/player/play",
                headers=self.headers
            )
        else:
            r = requests.put(
                "https://api.spotify.com/v1/me/player/pause",
                headers=self.headers
            )
        print(r.text)

    def repeat(self):
        play = self.repeat_var.get()
        if play:
            params = {
            "state": "track"
            }
        else:
            params = {
            "state": "off"
            }

        r = requests.put(
            "https://api.spotify.com/v1/me/player/repeat",
            headers = self.headers,
            params= params
        )
        print(r)
    def next(self):
        r = requests.post(
            "https://api.spotify.com/v1/me/player/next",
            headers = self.headers
        )
        print(r)

    def previous(self):
        r = requests.post(
            "https://api.spotify.com/v1/me/player/previous",
            headers = self.headers
        )
        print(r)
        print(r.text)

    def add_uri(self):
        f1 = tk.Frame(self.frame, relief='raised',bd=2)
        f1.pack()
        f2 = tk.Frame(f1)
        f2.pack()
        f3 = tk.Frame(f1)
        f3.pack(anchor='w')

        tk.Label(f2, text = 'uri: ').grid(row=0,column=0)
        self.uri_entries.append(
            tk.Entry(f2, width=37)
        )
        self.uri_entries[-1].grid(row=0,column=1)
        tk.Button(
            f2, text = "Start", command = partial(self.start, self.index)
        ).grid(row=0,column=2)

        tk.Label(f3, text = 'start (ms): ').grid(row=0, column=0, sticky = 'w')

        self.start_entries.append(
            tk.Entry(f3, width=8)
        )
        self.start_entries[-1].grid(row=0,column=1, sticky = 'w')
        tk.Frame(f3, width = 27).grid(row=0, column=2, sticky = 'w')
        tk.Label(f3, text = 'end (ms): ').grid(row=0, column=3, sticky = 'w')

        self.end_entries.append(
            tk.Entry(f3, width=8)
        )
        self.end_entries[-1].grid(row=0,column=4, sticky = 'e')
        self.index += 1

    def start(self, index):
        self.time_true = False
        time.sleep(self.time2)
        print('test')
        uri = self.uri_entries[index].get()
        start = self.start_entries[index].get()
        end = self.end_entries[index].get()
        if not start:
            start = 0
        data = '{' + f'"uris":["{uri}"],"position_ms":{start}' + '}'
        f = requests.put('https://api.spotify.com/v1/me/player/play', headers=self.headers, data=data)
        time1 = (int(end)-int(start))/1000
        print((int(end)-int(start))/1000)
        t = threading.Thread(target=self.time_thread, args=(time1,))
        t.start()


    def time_thread(self, time1):
        self.time_true = True
        self.time2 = self.time1/100
        for i in range(100):
            time.sleep(self.time2)
            if not self.time_true:
                requests.put('https://api.spotify.com/v1/me/player/pause', headers=self.headers)
                return
        requests.put('https://api.spotify.com/v1/me/player/pause', headers=self.headers)

    def listener(self):
        while True:
            response = requests.get("https://api.spotify.com/v1/me/player/", headers = self.headers)
            if response.status_code == 429:
                time.sleep(1)
            if response.status_code != 204 and response.status_code != 429:
                self.playing = json.loads(response.text)
            if self.kill_thread:
                return
            time.sleep(0.05)

    def add_scrollbar(self):
        self.canvas = tk.Canvas(self.root, borderwidth=0, height=650,width=680)
        self.canvas.pack_propagate(False)
        self.frame = tk.Frame(self.canvas)

        self.vsb = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window(
            (4,4),
            window=self.frame,
            anchor="nw",
            tags="self.frame"
        )
        self.frame.pack(side='top',anchor='w')

        self.frame.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

if __name__ == "__main__":
    main()
