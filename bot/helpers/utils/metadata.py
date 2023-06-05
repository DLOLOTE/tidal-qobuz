import os
import aigpy
import music_tag

from bot.logger import LOGGER

from mutagen import File
from config import Config
from mutagen.mp4 import MP4
from mutagen import flac, mp4
from mutagen.mp3 import EasyMP3
from mutagen.flac import FLAC
from mutagen.id3 import TALB, TCOP, TDRC, TIT2, TPE1, TRCK, APIC, \
    TCON, TOPE, TSRC, USLT, TPOS, TXXX


base_metadata = {
    'item_id': '',
    'title': '',
    'album': '',
    'artist': '',
    'albumartist': '',
    'tracknumber': '',
    'date': '',
    'lyrics': '',
    'upc': '',
    'isrc': '',
    'totaltracks': '',
    'volume': '',
    'totalvolume': '',
    'albumart': '',
    'thumbnail': '',
    'extension': '',
    'duration': '',  # in seconds
    'copyright': '',
    'genre': '',
    'provider': '',
    'quality': '',
    'explicit': ''
}

async def set_metadata(audio_path, data):
    ext = data['extension']
    handle = File(audio_path)
    if data['duration'] == '':
        await get_duration(audio_path, data, ext)
    if ext == 'flac':
        await set_flac(data, handle)
    elif ext == 'm4a' or ext == 'mp4':
        await set_m4a(data, handle)
    elif ext == 'mp3':
        await set_mp3(data, handle)
    elif ext == 'ogg':
        handle = music_tag.load_file(audio_path)
        await set_ogg(data, handle)

async def set_flac(data, handle):
    if handle.tags is None:
            handle.add_tags()
    handle.tags['title'] = data['title']
    handle.tags['album'] = data['album']
    handle.tags['albumartist'] = data['albumartist']
    handle.tags['artist'] = data['artist']
    handle.tags['copyright'] = data['copyright']
    handle.tags['tracknumber'] = str(data['tracknumber'])
    handle.tags['tracktotal'] = str(data['totaltracks'])
    #handle.tags['discnumber'] = 
    #handle.tags['disctotal'] = 
    handle.tags['genre'] = data['genre']
    handle.tags['date'] = data['date']
    #handle.tags['composer'] = 
    handle.tags['isrc'] = data['isrc']
    handle.tags['lyrics'] = data['lyrics']
    await savePic(handle, data)
    handle.save()
    return True

async def set_m4a(data, handle):
    handle.tags['\xa9nam'] = data['title']
    handle.tags['\xa9alb'] = data['album']
    handle.tags['aART'] = data['albumartist']
    handle.tags['\xa9ART'] = data['artist']
    handle.tags['cprt'] = data['copyright']
    handle.tags['trkn'] = [[int(data['tracknumber']), int(data['totaltracks'])]]
    #handle.tags['disk'] = [[__tryInt__(self.discnumber), __tryInt__(self.totaldisc)]]
    handle.tags['\xa9gen'] = data['genre']
    handle.tags['\xa9day'] = data['date']
    #handle.tags['\xa9wrt'] = __tryList__(self.composer)
    handle.tags['\xa9lyr'] = data['lyrics']
    await savePic(handle, data)
    handle.save()
    return True

async def set_ogg(data, handle):
    try:
        # Using music_tag cuz its less complex dealing ogg
        handle['title'] = data['title']
        handle['album'] = data['album']
        handle['albumartist'] = data['albumartist']
        handle['artist'] = data['artist']
        #handle['copyright'] = data['copyright']
        handle['tracknumber'] = str(data['tracknumber'])
        handle['totaltracks'] = str(data['totaltracks'])
        handle['discnumber'] = str(data['totaltracks'])
        #handle.tags['disctotal'] = 
        handle['genre'] = data['genre']
        handle['year'] = data['date']
        #handle.tags['composer'] = 
        handle['isrc'] = data['isrc']
        handle['lyrics'] = data['lyrics']
        await savePic(handle, data)
        handle.save()
    except:
        pass

async def set_mp3(data, handle):
    # ID3
    if handle.tags is None:
            handle.add_tags()
    handle.tags.add(TIT2(encoding=3, text=data['title']))
    handle.tags.add(TALB(encoding=3, text=data['album']))
    handle.tags.add(TOPE(encoding=3, text=data['albumartist']))
    handle.tags.add(TPE1(encoding=3, text=data['artist']))
    handle.tags.add(TCOP(encoding=3, text=data['copyright']))
    handle.tags.add(TRCK(encoding=3, text=str(data['tracknumber'])))
    handle.tags.add(TPOS(encoding=3, text=str(data['volume'])))
    handle.tags.add(TXXX(encoding=3, text=str(data['totaltracks'])))
    handle.tags.add(TCON(encoding=3, text=data['genre']))
    handle.tags.add(TDRC(encoding=3, text=data['date']))
    #handle.tags.add(TCOM(encoding=3, text=self.composer))
    handle.tags.add(TSRC(encoding=3, text=data['isrc']))
    handle.tags.add(USLT(encoding=3, lang=u'eng', desc=u'desc', text=data['lyrics']))
    await savePic(handle, data)
    handle.save()
    return True

async def savePic(handle, metadata):
    album_art = metadata['albumart']
    ext = metadata['extension']

    if not os.path.exists(album_art):
        coverPath = Config.DOWNLOAD_BASE_DIR + f"/{metadata['provider']}/albumart/{metadata['album']}.jpg"
        aigpy.net.downloadFile(album_art, coverPath)
        album_art = coverPath

    try:
        with open(album_art, "rb") as f:
            data = f.read()
    except Exception as e:
        await LOGGER.error(e)
        return

    if ext == 'flac':
        pic = flac.Picture()
        pic.data = data
        pic.mime = u"image/jpeg"
        handle.clear_pictures()
        handle.add_picture(pic)

    if ext == 'mp3':
        handle.tags.add(APIC(encoding=3, data=data))

    if ext == 'mp4' or ext == 'm4a':
        pic = mp4.MP4Cover(data)
        handle.tags['covr'] = [pic]

    if ext =='ogg':
        handle['artwork'] = data
    
    os.remove(album_art)

async def get_duration(path, data, ext):
    if ext == 'mp3':
        audio = EasyMP3(path)
    elif ext == 'm4a':
        audio = MP4(path)
    elif ext == 'flac':
        audio = FLAC(path)
    data['duration'] = audio.info.length
    
async def format_string(text, data, user=None):
    text = text.replace(R'{title}', data['title'])
    text = text.replace(R'{album}', data['album'])
    text = text.replace(R'{artist}', data['artist'])
    text = text.replace(R'{albumartist}', data['albumartist'])
    text = text.replace(R'{tracknumber}', str(data['tracknumber']))
    text = text.replace(R'{date}', str(data['date']))
    text = text.replace(R'{upc}', str(data['upc']))
    text = text.replace(R'{isrc}', str(data['isrc']))
    text = text.replace(R'{totaltracks}', str(data['totaltracks']))
    text = text.replace(R'{volume}', str(data['volume']))
    text = text.replace(R'{totalvolume}', str(data['totalvolume']))
    text = text.replace(R'{extension}', data['extension'])
    text = text.replace(R'{duration}', str(data['duration']))
    text = text.replace(R'{copyright}', data['copyright'])
    text = text.replace(R'{genre}', data['genre'])
    text = text.replace(R'{provider}', data['provider'].title())
    text = text.replace(R'{quality}', data['quality'])
    text = text.replace(R'{explicit}', str(data['explicit']))
    if user:
        text = text.replace(R'{user}', user['name'])
        text = text.replace(R'{username}', user['user_name'])
    return text