import requests
import json
import urllib.parse
import webbrowser
import base64
import os
import datetime
import time

class Spotify:
    def get_token(
        self,
        username,
        client_id,
        client_secret,
        redirect_uri,
        scope,
        overwrite=False
    ):
        is_file = os.path.isfile("token.json")
        if is_file:
            with open("token.json", 'r') as file:
                contents = json.loads(file.read())
            if not set(scope.split(' ')) == set(contents['scope'].split(' ')):
                differend = True
            else:
                differend = False
            if time.time() > contents['expires_at']:
                expired = True
            else:
                expired = False
        else:
            differend = False
            expired = False

        if (overwrite or not is_file or differend) and not expired:
            token = self.normal_auth(
                username,
                client_id,
                client_secret,
                redirect_uri,
                scope
            )
        elif expired:
            token = self.refresh_auth(
                client_id,
                client_secret
            )
        else:
            with open("token.json", 'r') as file:
                contents = json.loads(file.read())
            token = contents['access_token']
        return token

    def refresh_auth(self, client_id, client_secret):
        with open("token.json", 'r') as file:
            contents = json.loads(file.read())

        b64 = base64.b64encode(
        bytearray(f"{client_id}:{client_secret}", 'utf-8')
        ).decode()
        headers = {
        "Authorization": f"Basic {b64}"
        }

        data = {
            "grant_type": 'refresh_token',
            "refresh_token": contents['refresh_token']
        }
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            data = data,
            headers = headers
        )
        contents = r.json()
        contents['expires_at'] = int(time.time()) + contents['expires_in']
        with open("token.json", 'w+') as file:
            file.write(json.dumps(contents,indent=4))

        return contents['access_token']



    def normal_auth(
        self,
        username,
        client_id,
        client_secret,
        redirect_uri,
        scope,
    ):
        params = urllib.parse.quote(
            f"?client_id={client_id}&"
            "response_type=code&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&",
            "show_dialog=true",
            safe='&?='
        )
        webbrowser.open("https://accounts.spotify.com/authorize" + params)
        print(
            """
            Please print the url you have been redirected to
            """
        )
        url = input()
        print('\n\n')
        code = url.split("code=")[1]
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        b64 = base64.b64encode(
            bytearray(f"{client_id}:{client_secret}", 'utf-8')
        ).decode()
        headers = {
            "Authorization": f"Basic {b64}"
        }
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            data=params,
            headers=headers
        )
        contents = r.json()
        contents['expires_at'] = int(time.time())+contents['expires_in']
        with open('token.json', 'w+') as file:
            file.write(json.dumps(contents, indent=4))

        return contents['access_token']



if __name__ == "__main__":
    with open("config.json", 'r') as file:
        config = json.loads(file.read())
        username = config['username']
        client_id = config['client_id']
        client_secret = config['client_secret']

    s = Spotify()
    token = s.get_token(
        username,
        client_id,
        client_secret,
        "http://google.com/",
        'user-library-read user-modify-playback-state user-read-playback-state',
    )
    print(token)
