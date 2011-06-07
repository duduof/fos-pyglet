""" Meaningful composition of shader programs exposed as a library """
__author__ = 'Stephan Gerhard'

from .shaders import Shader
from .lib import get_shader_code
# import fos.lib.pyglet.gl as gl

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# load the vary-line-width-shader
def get_vary_line_width_shader():
    return Shader( [get_shader_code('propagatevertex130.vert')],
                   [get_shader_code('allRed.frag')],
                   [get_shader_code('lineextrusion130.geom'), GL_LINES, GL_TRIANGLE_STRIP, 6]
                  )

# load the vary-line-width-shader
def get_simple_shader():
    return Shader( [get_shader_code('propagatevertex130b.vert')],
                   [get_shader_code('allRed.frag')]
                  )

# load the vary-line-width-shader
def get_propagate_shader():
    return Shader( [get_shader_code('propagatevertex150.vert')],
                   [get_shader_code('propagatecolor150.frag')],
                   [get_shader_code('lineextrusion130b.geom'), GL_LINES, GL_TRIANGLE_STRIP, 6]
                  )
