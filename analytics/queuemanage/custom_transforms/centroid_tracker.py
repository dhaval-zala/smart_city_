from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np
import datetime


class CentroidTracker():
    def __init__(self,maxDisappeared=20):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.originRects = OrderedDict()
        self.disappeared = OrderedDict()
        self.start_time=OrderedDict()
        self.end_time=OrderedDict()
        self.wait_time=OrderedDict()
        self.index=OrderedDict()
        self.maxDisappeared = maxDisappeared

    def register(self, centroid, rect,i):
        self.originRects[self.nextObjectID] = rect
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.start_time[self.nextObjectID]=0
        self.end_time[self.nextObjectID]=0
        self.wait_time[self.nextObjectID]=0
        self.index[self.nextObjectID]=i
        self.nextObjectID += 1

    def deregister(self, objectID):
        del self.originRects[objectID]
        del self.objects[objectID]
        del self.disappeared[objectID]
        del self.index[objectID]
        if objectID in list(self.start_time.keys()):
            del self.start_time[objectID]
        if objectID in list(self.end_time.keys()):
            del self.end_time[objectID]

    def get_id(self, rect):
        (x, y, eX, eY) = rect
        cX = ((x + eX) / 2.0)
        cY = ((y + eY) / 2.0)

        objectIDs = list(self.objects.keys())
        objectCentroids = list(self.objects.values())
        
        D = dist.cdist(np.array(objectCentroids), [(cX, cY)])

        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]
        objectID = None

        for (row, col) in zip(rows, cols):
            objectID = objectIDs[row]
            break
        return objectID

    def update(self,rects):

        if(len(rects) == 0):
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                
                if(self.disappeared[objectID] > self.maxDisappeared):
                    self.deregister(objectID)
            return self.objects, self.originRects
        
        inputCentroids = np.zeros((len(rects), 2), dtype="int")
    
        for(i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        if(len(self.objects) == 0):
            for i in range(0, len(inputCentroids)):
                centroid = inputCentroids[i]
                rect = rects[i]
                self.register(centroid, rect,i)
        
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = dist.cdist(np.array(objectCentroids), inputCentroids)
            print("distance of objects:{}".format(D),flush=True)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                
                if row in usedRows or col in usedCols:
                    continue
                
                if D[row][col]<50:

                    objectID = objectIDs[row]
                    self.objects[objectID] = inputCentroids[col]
                    self.originRects[objectID] = rects[col]
                    self.disappeared[objectID] = 0
                    self.index[objectID]=col

                    usedRows.add(row)
                    usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:

                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1

                    if self.disappeared[objectID] > self.maxDisappeared:
                        self.deregister(objectID)

            else:

                for col in unusedCols:
                    centroid = inputCentroids[col]
                    rect = rects[col]
                    self.register(centroid,rect,col)

        return self.objects, self.originRects