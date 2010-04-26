import numpy as np
import OpenGL.GL as gl
import fos.core.primitives as prim
import fos.core.text as text
import fos.core.cortex as cortex

MS=1500


def center(x,y):

    return ((int(1024-x)/2),int((768-y)/2))


class Plot():


    def __init__(self):

        self.slots = None

        self.time = 0

        self.near_pick = None

        self.far_pick = None

        

    def init(self):

        global csurf

        #csurf_fname ='/home/eg01/Data_Backup/Data/Adam/multiple_transp_volumes/freesurfer_trich/rh.pial.vtk'

        csurf_fname ='/home/eg309/Desktop/rh.pial.vtk'
        

        csurf = cortex.CorticalSurface(csurf_fname)

        csurf.init()            
       
        self.slots={0:{'actor':csurf,'slot':( 0,   800*MS )}}                 

        
          
    def display(self):

        now = self.time

        for s in self.slots:

            if now >= self.slots[s]['slot'][0] and now <=self.slots[s]['slot'][1]:

                self.slots[s]['actor'].near_pick = self.near_pick

                self.slots[s]['actor'].far_pick = self.far_pick               
                
                self.slots[s]['actor'].display()



    def update_time(self,time):

        self.time=time


    def update_pick_ray(self,near_pick, far_pick):

        self.near_pick = near_pick

        self.far_pick = far_pick





        
                 



        



        