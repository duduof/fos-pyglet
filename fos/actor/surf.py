import numpy as np
import fos.lib.pyglet as pyglet
from fos.lib.pyglet.gl import *
from fos.lib.pyglet.gl import GLfloat

from fos.core.actor import Actor
from fos.core.utils import vec

class Surface(Actor):
    
    def __init__(self,vertices,faces,colors,
                 affine = None,
                 force_centering = False,
                 add_lights = False,
                 normals = None):
        
        super(Surface, self).__init__()
        
        # store a reference to vertices for bounding box computation
        self.vertices = vertices
        if force_centering:
            self.vertices = self.vertices - np.mean(self.vertices, axis = 0)
            
        self.vert_ptr=self.vertices.ctypes.data
        self.face_ptr=faces.ctypes.data
        self.color_ptr=colors.ctypes.data
        self.el_count=len(faces)*3

        if affine == None:
            # create a default affine
            self.affine = np.eye(4, dtype = np.float32)
        else:
            self.affine = affine
            
        self._update_glaffine()
        
        if add_lights:
            self.norm_ptr=normals.ctypes.data
            self.draw = self.draw_withlight
        else:
            self.draw = self.draw_sanslight
        
        self.show_aabb = True
        self.make_aabb(margin = 0)
    
    
    def draw_withlight(self):
        self.set_state()
        glPushMatrix()
        glMultMatrixf(self.glaffine)    
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)        
        glVertexPointer(3, GL_FLOAT, 0, self.vert_ptr)                          
        glNormalPointer(GL_FLOAT, 0, self.norm_ptr)        
        glColorPointer(4, GL_FLOAT, 0, self.color_ptr)
        glDrawElements(GL_TRIANGLES, self.el_count, GL_UNSIGNED_INT, self.face_ptr)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
                 
        self.unset_state()
        glEnable(GL_DEPTH_TEST)
        self.draw_aabb() 
        
        glPopMatrix()

        
    def draw_sanslight(self):
        glPushMatrix()
        glMultMatrixf(self.glaffine)
        #glEnable (GL_BLEND) 
        #glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)        
        glVertexPointer(3, GL_FLOAT, 0, self.vert_ptr)                             
        glColorPointer(4, GL_FLOAT, 0, self.color_ptr)
        glDrawElements(GL_TRIANGLES, self.el_count, GL_UNSIGNED_INT, self.face_ptr)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)             
        #self.draw_aabb()
        glPopMatrix()
        
    def set_state(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)        
        #glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        
        glLineWidth(3.)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        #Define a simple function to create ctypes arrays of floats:
        
        glLightfv(GL_LIGHT0, GL_POSITION, vec(.0, .0, 1, 1))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, 1, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1, 1, 1, 1))
        
        glLightfv(GL_LIGHT1, GL_POSITION, vec(1, 0, .5, 0))
        glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(.5, .0, 0, 1))
        glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1, 0, 0, 1))

        glMaterialfv(GL_FRONT_AND_BACK,GL_AMBIENT_AND_DIFFUSE,vec(0.9, 0, 0.3, 1.))
        glMaterialfv(GL_FRONT_AND_BACK,GL_SPECULAR, vec(1, 1, 1, 1.))
        glMaterialf(GL_FRONT_AND_BACK,GL_SHININESS, 50)
        
    def unset_state(self):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glLineWidth(1.)
        glDisable(GL_LIGHTING)
    
        
    '''
    def update(self, dt):
        print 'dt',dt
        pass
    '''
