"""
SIMPLE SCRIPT FOR SCRAPING, FORMATTING, AND CREATING INVERTED INDICES FOR GIFS
"""

from PIL import Image, ImageSequence
import requests as req
import json
from tqdm import tqdm
from os import remove
from time import sleep

from gifindexer import GIFIndexer


POLITENESS = 2 # time to sleep between API queries

# user parameters
GIFS_TO_PROCESS = 1000              # max number of GIFS to scrape before purposefully exiting
GIF_TARGET_SIZE = (32, 32)          # (width, height) of saved GIFS, if this parameter is changed ALL previous data must be deleted
QUERY = "yes"                       # query to use when scraping GIFs, best to run multiple times with different QUERY values
TEMP_DIR = "temp/"                  # dir where work is done, can't be same as GIFS_DIR
GIFS_DIR = "gifs/"                  # final output location
INDEX_FILE = GIFS_DIR + "index"     # index data, generally doesn't need to be changed
MAX_COLORS = 512                    # don't modify unless you know what you're doing

# API query parameters
API_KEY = "" # <--- tenor.com GIF private key
LOCALE = "en_US"
CONTENT_FILTER = "high"
MEDIA_FILTER = "minimal"
AR_RANGE = "standard"
LIMIT = 50 # max value

API_URL = "https://api.tenor.com/v1/random?key={}&q={}&locale={}&contentfilter={}&media_filter={}&ar_range={}&limit={}" \
    .format(API_KEY, QUERY, LOCALE, CONTENT_FILTER, MEDIA_FILTER, AR_RANGE, LIMIT)


if __name__ == "__main__":
    indexer = GIFIndexer(MAX_COLORS, loadFile=INDEX_FILE)
    
    gifs_processed = 0
    nextPos = "0" # string for tenor API to continue search

    while gifs_processed < GIFS_TO_PROCESS:
        res = req.get(API_URL + "&pos={}".format(nextPos))

        if res.status_code != 200:
            print("Got response code {} exiting...".format(res.stats_code))
            exit(1)
        
        gifs = json.loads(res.content)

        if 'next' not in gifs:
            print("ran out of results... exiting")
            break
        else:
            nextPos = gifs['next']

        print("Processing next {} gifs".format(LIMIT))

        for result in tqdm(gifs['results']):
            gif_media = result['media'][0]['gif']

            if gif_media['dims'][0] != gif_media['dims'][1]:
                continue # only want sqauare gifs (aspect ratio 1:1)

            download = req.get(gif_media['url'], allow_redirects=True)

            if download.status_code != 200:
                continue # skip this one

            gif_fname = "{}{}.gif".format(TEMP_DIR, result['id'])
            open(gif_fname, "wb").write(download.content) # save to temp directory
            
            # resize image with resampling to final directory
            with Image.open(gif_fname) as im:
                output = []

                for frame in ImageSequence.Iterator(im):
                    output.append(frame.resize(GIF_TARGET_SIZE).convert(mode="RGB"))

                final_name = "{}{}".format(GIFS_DIR, gif_fname[gif_fname.find('/')+1:])
                
                indexer.addToIndex(output, final_name)
                output[0].save(final_name, save_all=True, append_images=output[1:])

            remove(gif_fname) # delete temp file
            gifs_processed += 1

        print("{} / {} gifs acquired!".format(gifs_processed, GIFS_TO_PROCESS))
        sleep(POLITENESS)

    indexer.finalize()
    indexer.saveIndex(INDEX_FILE)

