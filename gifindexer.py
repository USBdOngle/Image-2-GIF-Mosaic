from PIL import Image
from sklearn.cluster import KMeans
import pickle
import random
import math
from tqdm import tqdm


ADD_TUPLES = lambda l1, l2: [ a + b for a, b in zip(l1, l2) ]


class GIFIndexer:
    def __init__(self, maxColors, loadFile=""):
        if loadFile != "" and isinstance(loadFile, str):
            self.loadIndex(loadFile)
        else:
            self.__index = dict()
            self.__kmeans = KMeans(n_clusters=maxColors)
            self.__clusters = [ [] for _ in range(maxColors) ]


    def __frameAvgPx(self, frame):
        avgRGB = [0, 0, 0]

        for row in range(frame.height):
            for col in range(frame.width):
                avgRGB = ADD_TUPLES(avgRGB, frame.getpixel((row, col)))

        return ( avg / (frame.height * frame.width) for avg in avgRGB )

    
    def __gifAvgPx(self, gif=[]):
        gifAvg = [0, 0, 0]
        
        for frame in gif:
            gifAvg = ADD_TUPLES(gifAvg, self.__frameAvgPx(frame))

        return [ int(avg / len(gif)) for avg in gifAvg ]

    
    # return tuple in T with minimal Euclidean distance to t1
    def __minRGBDistance(self, t1=(0,0,0), T=[]):
        dist = lambda a, b: math.sqrt(sum([ (i-j)**2 for i, j in zip(a, b)]))

        best = T[0]
        minDist = dist(t1, T[0])

        for tup in T:
            d = dist(t1, tup)

            if d < minDist:
                best = tup
                minDist = d

        return best


    def addToIndex(self, gif=[], name=""):
        res = tuple(self.__gifAvgPx(gif))
    
        if res in self.__index:
            self.__index[res].append(name)
        else:
            self.__index[res] = [ name ]

    
    # needs to be called when done adding new indexes to build rgb lookup
    def finalize(self):
        if len(self.__index) < 1:
            raise ValueError
        
        pixels = [ [ ch for ch in rgb ] for rgb in self.__index.keys() ]
        clusters = self.__kmeans.fit_predict([ [ ch for ch in rgb ] for rgb in self.__index.keys() ])

        for px, clust in zip(pixels, clusters):
            self.__clusters[clust].append(px)


    def getBestGIF(self, rgb=(0, 0, 0)):
        cluster = self.__kmeans.predict([rgb])
        pixel = self.__minRGBDistance(t1=rgb, T=self.__clusters[cluster[0]])
        return random.choice(self.__index[tuple(pixel)])


    # write index data to file
    def saveIndex(self, file=""):
        saveData = { 'kmeans': self.__kmeans, 'clusters': self.__clusters, 'index': self.__index }
        pickle.dump(saveData, open(file, "wb"))


    # load index data from file
    def loadIndex(self, file=""):
        loadData = pickle.load(open(file, "rb"))
        self.__kmeans = loadData['kmeans']
        self.__clusters = loadData['clusters']
        self.__index = loadData['index']


if __name__ == "__main__":
    testIndexer = GIFIndexer(512, "gifs/index")
    testIndexer.finalize()
    testIndexer.saveIndex("gifs/index")
    res = testIndexer.getBestGIF((178,100,255))
    print(res)