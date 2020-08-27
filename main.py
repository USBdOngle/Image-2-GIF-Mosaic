from gifindexer import GIFIndexer, ADD_TUPLES
from gifscraper import GIFS_DIR, INDEX_FILE, GIF_TARGET_SIZE, MAX_COLORS

from PIL import Image
from tqdm import tqdm

# input parameters
INPUT_IMAGE = "inputs/lenna.png"
FACTOR = 4                # amount of downsampling to apply to input (increase aggressively for large inputs)
FRAME_COUNT = 12
FRAME_DURATION = 100      # ms

INPUT_DIR = "inputs/"
OUTPUT_DIR = "outputs/"
OUTPUT_IMAGE = OUTPUT_DIR + INPUT_IMAGE.replace(INPUT_IMAGE[INPUT_IMAGE.rfind('.'):], ".gif")


class GIFWrapper():
    def __init__(self, path):
        self.__nextFrameIdx = 1
        self.__im = Image.open(path)


    def __del__(self):
        self.__im.close()


    def getIm(self):
        return self.__im.convert(mode="RGB")


    def seekNext(self):
        try:
            self.__im.seek(self.__nextFrameIdx)
            self.__nextFrameIdx += 1
        except:
            self.__im.seek(0)
            self.__nextFrameIdx = 1


def img_2_bitmap(img="", factor=FACTOR):
    with Image.open(img) as im:
        fit_factor = lambda x: x - (x % factor)
        bitmap = []
        im = im.convert(mode="RGB")
        
        for row in range(0, fit_factor(im.height), factor):
            map_row = []

            for col in range(0, fit_factor(im.width), factor):
                avg = (0, 0, 0) # get avg RGB value for block with side dimensions of factor

                for y in range(row, row + factor):
                    for x in range(col, col + factor):
                        avg = ADD_TUPLES(avg, im.getpixel((x, y)))

                map_row.append([ int(a / (factor ** 2)) for a in avg ])

            bitmap.append(map_row)

    return bitmap


def rgb_2_gifpath(bitmap, index):
    return [ [ index.getBestGIF(px) for px in row ] for row in bitmap ]


def fill_frame(frame, path_map, cache):
    for row in tqdm(range(len(path_map))):
        for col in range(len(path_map[0])):
            path = path_map[row][col]

            if path not in cache:
                cache[path] = GIFWrapper(path)

            gifIm = cache[path].getIm()

            base_y = row * GIF_TARGET_SIZE[1]
            base_x = col * GIF_TARGET_SIZE[0]
            
            for y in range(GIF_TARGET_SIZE[1]):
                for x in range(GIF_TARGET_SIZE[0]):
                    frame.putpixel((base_x + x, base_y + y), gifIm.getpixel((x, y)))

    # advance each gif by 1 frame
    for gif in cache.values():
        gif.seekNext()


if __name__ == "__main__":
    index = GIFIndexer(MAX_COLORS, INDEX_FILE)
    gif_paths_map = rgb_2_gifpath(img_2_bitmap(INPUT_IMAGE), index)

    output_frames = []
    cache = {} # will be shared between succesive calls of fill_frame to save io
    frame_size = (len(gif_paths_map[0]) * GIF_TARGET_SIZE[1], len(gif_paths_map) * GIF_TARGET_SIZE[0])

    for i in range(FRAME_COUNT):
        frame = Image.new("RGB", frame_size)
        fill_frame(frame, gif_paths_map, cache)
        output_frames.append(frame)

        print("Done frame {} / {}!".format(i+1, FRAME_COUNT))

    print("Saving output to {}".format(OUTPUT_IMAGE))
    output_frames[0].save(OUTPUT_IMAGE, save_all=True, optimize=False, append_images=output_frames[1:], loop=0, duration=FRAME_DURATION)