# From vitiko98/qobuz-dl
import time
import hashlib
import requests

from config import Config

from bot.helpers.qobuz.bundle import Bundle

from bot.logger import LOGGER
from bot.helpers.database.postgres_impl import set_db

class Client:
    def __init__(self):
        quality, _ = set_db.get_variable("QOBUZ_QUALITY")
        if not quality:
            set_db.set_variable("QOBUZ_QUALITY", 6, False, None)
            quality = 6
        self.id = None
        self.secrets = None
        self.session = requests.Session()
        self.base = "https://www.qobuz.com/api.json/0.2/"
        self.sec = None
        self.quality = int(quality)
        

    def api_call(self, epoint, **kwargs):
        if epoint == "user/login":
            if kwargs.get('email'):
                params = {
                    "email": kwargs["email"],
                    "password": kwargs["pwd"],
                    "app_id": self.id,
                }
            else:
                params = {
                    "user_id": kwargs["userid"],
                    "user_auth_token": kwargs["usertoken"],
                    "app_id": self.id,
                }
        elif epoint == "track/get":
            params = {"track_id": kwargs["id"]}
        elif epoint == "album/get":
            params = {"album_id": kwargs["id"]}
        elif epoint == "playlist/get":
            params = {
                "extra": "tracks",
                "playlist_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
            }
        elif epoint == "artist/get":
            params = {
                "app_id": self.id,
                "artist_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
                "extra": "albums",
            }
        elif epoint == "label/get":
            params = {
                "label_id": kwargs["id"],
                "limit": 500,
                "offset": kwargs["offset"],
                "extra": "albums",
            }
        elif epoint == "favorite/getUserFavorites":
            unix = time.time()
            # r_sig = "userLibrarygetAlbumsList" + str(unix) + kwargs["sec"]
            r_sig = "favoritegetUserFavorites" + str(unix) + kwargs["sec"]
            r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
            params = {
                "app_id": self.id,
                "user_auth_token": self.uat,
                "type": "albums",
                "request_ts": unix,
                "request_sig": r_sig_hashed,
            }
        elif epoint == "track/getFileUrl":
            unix = time.time()
            track_id = kwargs["id"]
            fmt_id = kwargs["fmt_id"]
            if int(fmt_id) not in (5, 6, 7, 27):
                raise Exception("QOBUZ : Invalid quality id: choose between 5, 6, 7 or 27")
            r_sig = "trackgetFileUrlformat_id{}intentstreamtrack_id{}{}{}".format(
                fmt_id, track_id, unix, kwargs.get("sec", self.sec)
            )
            r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
            params = {
                "request_ts": unix,
                "request_sig": r_sig_hashed,
                "track_id": track_id,
                "format_id": fmt_id,
                "intent": "stream",
            }
        else:
            params = kwargs
        r = self.session.get(self.base + epoint, params=params)
        if epoint == "user/login":
            if r.status_code == 401:
                raise Exception('QOBUZ : Invalid credentials given..... Disabling QOBUZ')
            elif r.status_code == 400:
                raise Exception("QOBUZ : Invalid App ID. Please Recheck your credentials.... Disabling QOBUZ")
            else:
                pass
        elif (
            epoint in ["track/getFileUrl", "favorite/getUserFavorites"]
            and r.status_code == 400
        ):
            raise Exception("QOBUZ : Invalid App Secret. Please recheck your credentials.... Disabling QOBUZ")

        #r.raise_for_status()
        return r.json()

    def auth(self, auth):
        if auth=='email':
            usr_info = self.api_call(
                "user/login", 
                email=Config.QOBUZ_EMAIL, 
                pwd=Config.QOBUZ_PASSWORD)
        else:
            usr_info = self.api_call(
                "user/login", 
                userid=Config.QOBUZ_USER,
                usertoken=Config.QOBUZ_TOKEN)
        if not usr_info:
            return
        if not usr_info["user"]["credential"]["parameters"]:
            raise Exception("QOBUZ : Free accounts are not eligible to download tracks from QOBUZ. Disabling QOBUZ for now")
        self.uat = usr_info["user_auth_token"]
        self.session.headers.update({"X-User-Auth-Token": self.uat})
        self.label = usr_info["user"]["credential"]["parameters"]["short_label"]
        LOGGER.debug(f"Loaded QOBUZ - Membership Status: {self.label}")

    def multi_meta(self, epoint, key, id, type):
        total = 1
        offset = 0
        while total > 0:
            if type in ["tracks", "albums"]:
                j = self.api_call(epoint, id=id, offset=offset, type=type)[type]
            else:
                j = self.api_call(epoint, id=id, offset=offset, type=type)
            if offset == 0:
                yield j
                total = j[key] - 500
            else:
                yield j
                total -= 500
            offset += 500

    def get_album_meta(self, id):
        return self.api_call("album/get", id=id)

    def get_track_meta(self, id):
        return self.api_call("track/get", id=id)

    def get_track_url(self, id):
        fmt_id = self.quality
        return self.api_call("track/getFileUrl", id=id, fmt_id=fmt_id)

    def get_artist_meta(self, id):
        return self.multi_meta("artist/get", "albums_count", id, None)

    def get_plist_meta(self, id):
        return self.multi_meta("playlist/get", "tracks_count", id, None)

    def get_label_meta(self, id):
        return self.multi_meta("label/get", "albums_count", id, None)

    def search_albums(self, query, limit):
        return self.api_call("album/search", query=query, limit=limit)

    def search_artists(self, query, limit):
        return self.api_call("artist/search", query=query, limit=limit)

    def search_playlists(self, query, limit):
        return self.api_call("playlist/search", query=query, limit=limit)

    def search_tracks(self, query, limit):
        return self.api_call("track/search", query=query, limit=limit)

    def get_favorite_albums(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="albums", offset=offset, limit=limit
        )

    def get_favorite_tracks(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="tracks", offset=offset, limit=limit
        )

    def get_favorite_artists(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="artists", offset=offset, limit=limit
        )

    def get_user_playlists(self, limit):
        return self.api_call("playlist/getUserPlaylists", limit=limit)

    def test_secret(self, sec):
        try:
            self.api_call("track/getFileUrl", id=5966783, fmt_id=5, sec=sec)
            return True
        except:
            return False

    def get_tokens(self):
        bundle = Bundle()
        self.id = str(bundle.get_app_id())
        self.secrets = [
            secret for secret in bundle.get_secrets().values() if secret
        ]  # avoid empty fields

    def login(self, auth):
        self.get_tokens()

        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
                "X-App-Id": self.id,
            }
        )
        self.auth(auth)
        self.cfg_setup()

    def cfg_setup(self):
        for secret in self.secrets:
            # Falsy secrets
            if not secret:
                continue
            if self.test_secret(secret):
                self.sec = secret
                break
        if self.sec is None:
            raise LOGGER.debug("QOBUZ : Can't find any valid app secret")
        

qobuz_api = Client()