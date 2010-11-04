# ----------------------------------------------------------------------------
# fos.lib.pyglet
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of fos.lib.pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
'''

# TODO Windows Vista: need to call SetProcessDPIAware?  May affect GDI+ calls
# as well as font.

from ctypes import *
import ctypes
import math

from sys import byteorder
import fos.lib.pyglet
from fos.lib.pyglet.font import base
import fos.lib.pyglet.image
from fos.lib.pyglet.libs.win32.constants import *
from fos.lib.pyglet.libs.win32.types import *
from fos.lib.pyglet.libs.win32 import _gdi32 as gdi32, _user32 as user32
from fos.lib.pyglet.libs.win32 import _kernel32 as kernel32

_debug_font = fos.lib.pyglet.options['debug_font']

HFONT = HANDLE
HBITMAP = HANDLE
HDC = HANDLE
HGDIOBJ = HANDLE
gdi32.CreateFontIndirectA.restype = HFONT
gdi32.CreateCompatibleBitmap.restype = HBITMAP
gdi32.CreateCompatibleDC.restype = HDC
user32.GetDC.restype = HDC
gdi32.GetStockObject.restype = HGDIOBJ
gdi32.CreateDIBSection.restype = HBITMAP

class LOGFONT(Structure):
    _fields_ = [
        ('lfHeight', c_long),
        ('lfWidth', c_long),
        ('lfEscapement', c_long),
        ('lfOrientation', c_long),
        ('lfWeight', c_long),
        ('lfItalic', c_byte),
        ('lfUnderline', c_byte),
        ('lfStrikeOut', c_byte),
        ('lfCharSet', c_byte),
        ('lfOutPrecision', c_byte),
        ('lfClipPrecision', c_byte),
        ('lfQuality', c_byte),
        ('lfPitchAndFamily', c_byte),
        ('lfFaceName', (c_char * LF_FACESIZE))  # Use ASCII
    ]
    __slots__ = [f[0] for f in _fields_]

class TEXTMETRIC(Structure):
    _fields_ = [
        ('tmHeight', c_long),
        ('tmAscent', c_long),
        ('tmDescent', c_long),
        ('tmInternalLeading', c_long),
        ('tmExternalLeading', c_long),
        ('tmAveCharWidth', c_long),
        ('tmMaxCharWidth', c_long),
        ('tmWeight', c_long),
        ('tmOverhang', c_long),
        ('tmDigitizedAspectX', c_long),
        ('tmDigitizedAspectY', c_long),
        ('tmFirstChar', c_char),  # Use ASCII 
        ('tmLastChar', c_char),
        ('tmDefaultChar', c_char),
        ('tmBreakChar', c_char),
        ('tmItalic', c_byte),
        ('tmUnderlined', c_byte),
        ('tmStruckOut', c_byte),
        ('tmPitchAndFamily', c_byte),
        ('tmCharSet', c_byte)
    ]
    __slots__ = [f[0] for f in _fields_]

class ABC(Structure):
    _fields_ = [
        ('abcA', c_int),
        ('abcB', c_uint),
        ('abcC', c_int)
    ]
    __slots__ = [f[0] for f in _fields_]

class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ('biSize', c_uint32),
        ('biWidth', c_int),
        ('biHeight', c_int),
        ('biPlanes', c_short),
        ('biBitCount', c_short),
        ('biCompression', c_uint32),
        ('biSizeImage', c_uint32),
        ('biXPelsPerMeter', c_long),
        ('biYPelsPerMeter', c_long),
        ('biClrUsed', c_uint32),
        ('biClrImportant', c_uint32)
    ]
    __slots__ = [f[0] for f in _fields_]

class RGBQUAD(Structure):
    _fields_ = [
        ('rgbBlue', c_byte),
        ('rgbGreen', c_byte),
        ('rgbRed', c_byte),
        ('rgbReserved', c_byte)
    ]

    def __init__(self, r, g, b):
        self.rgbRed = r
        self.rgbGreen = g
        self.rgbBlue = b


class BITMAPINFO(Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', c_ulong * 3)
    ]

def str_ucs2(text):
    if byteorder == 'big':
        text = text.encode('utf_16_be')
    else:
        text = text.encode('utf_16_le')   # explicit endian avoids BOM
    return create_string_buffer(text + '\0')

_debug_dir = 'debug_font'
def _debug_filename(base, extension):
    import os
    if not os.path.exists(_debug_dir):
        os.makedirs(_debug_dir)
    name = '%s-%%d.%%s' % os.path.join(_debug_dir, base)
    num = 1
    while os.path.exists(name % (num, extension)):
        num += 1
    return name % (num, extension)

def _debug_image(image, name):
    filename = _debug_filename(name, 'png')
    image.save(filename)
    _debug('Saved image %r to %s' % (image, filename))

_debug_logfile = None
def _debug(msg):
    global _debug_logfile
    if not _debug_logfile:
        _debug_logfile = open(_debug_filename('log', 'txt'), 'wt')
    _debug_logfile.write(msg + '\n')

class Win32GlyphRenderer(base.GlyphRenderer):
    _bitmap = None
    _dc = None
    _bitmap_rect = None

    def __init__(self, font):
        super(Win32GlyphRenderer, self).__init__(font)
        self.font = font

        # Pessimistically round up width and height to 4 byte alignment
        width = font.max_glyph_width
        height = font.ascent - font.descent
        width = (width | 0x3) + 1
        height = (height | 0x3) + 1
        self._create_bitmap(width, height)

        gdi32.SelectObject(self._dc, self.font.hfont)

    def _create_bitmap(self, width, height):
        pass

    def render(self, text):
        raise NotImplementedError('abstract')

class GDIGlyphRenderer(Win32GlyphRenderer):
    def __del__(self):
        try:
            if self._dc:
                gdi32.DeleteDC(self._dc)
            if self._bitmap:
                gdi32.DeleteObject(self._bitmap)
        except:
            pass

    def render(self, text):
        # Attempt to get ABC widths (only for TrueType)
        abc = ABC()
        if gdi32.GetCharABCWidthsW(self._dc, 
            ord(text), ord(text), byref(abc)):
            width = abc.abcB 
            lsb = abc.abcA
            advance = abc.abcA + abc.abcB + abc.abcC
        else:
            width_buf = c_int()
            gdi32.GetCharWidth32W(self._dc, 
                ord(text), ord(text), byref(width_buf))
            width = width_buf.value
            lsb = 0
            advance = width

        # Can't get glyph-specific dimensions, use whole line-height.
        height = self._bitmap_height
        image = self._get_image(text, width, height, lsb)
        
        glyph = self.font.create_glyph(image)
        glyph.set_bearings(-self.font.descent, lsb, advance)

        if _debug_font:
            _debug('%r.render(%s)' % (self, text))
            _debug('abc.abcA = %r' % abc.abcA)
            _debug('abc.abcB = %r' % abc.abcB)
            _debug('abc.abcC = %r' % abc.abcC)
            _debug('width = %r' % width)
            _debug('height = %r' % height)
            _debug('lsb = %r' % lsb)
            _debug('advance = %r' % advance)
            _debug_image(image, 'glyph_%s' % text)
            _debug_image(self.font.textures[0], 'tex_%s' % text)

        return glyph

    def _get_image(self, text, width, height, lsb):
        # There's no such thing as a greyscale bitmap format in GDI.  We can
        # create an 8-bit palette bitmap with 256 shades of grey, but
        # unfortunately antialiasing will not work on such a bitmap.  So, we
        # use a 32-bit bitmap and use the red channel as OpenGL's alpha.
    
        gdi32.SelectObject(self._dc, self._bitmap)
        gdi32.SelectObject(self._dc, self.font.hfont)
        gdi32.SetBkColor(self._dc, 0x0)
        gdi32.SetTextColor(self._dc, 0x00ffffff)
        gdi32.SetBkMode(self._dc, OPAQUE)

        # Draw to DC
        user32.FillRect(self._dc, byref(self._bitmap_rect), self._black)
        gdi32.ExtTextOutA(self._dc, -lsb, 0, 0, c_void_p(), text,
            len(text), c_void_p())
        gdi32.GdiFlush()

        # Create glyph object and copy bitmap data to texture
        image = fos.lib.pyglet.image.ImageData(width, height, 
            'AXXX', self._bitmap_data, self._bitmap_rect.right * 4)
        return image
        
    def _create_bitmap(self, width, height):
        self._black = gdi32.GetStockObject(BLACK_BRUSH)
        self._white = gdi32.GetStockObject(WHITE_BRUSH)

        if self._dc:
            gdi32.ReleaseDC(self._dc)
        if self._bitmap:
            gdi32.DeleteObject(self._bitmap)

        pitch = width * 4
        data = POINTER(c_byte * (height * pitch))()
        info = BITMAPINFO()
        info.bmiHeader.biSize = sizeof(info.bmiHeader)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32 
        info.bmiHeader.biCompression = BI_RGB

        self._dc = gdi32.CreateCompatibleDC(c_void_p())
        self._bitmap = gdi32.CreateDIBSection(c_void_p(),
            byref(info), DIB_RGB_COLORS, byref(data), c_void_p(),
            0)
        # Spookiness: the above line causes a "not enough storage" error,
        # even though that error cannot be generated according to docs,
        # and everything works fine anyway.  Call SetLastError to clear it.
        kernel32.SetLastError(0)

        self._bitmap_data = data.contents
        self._bitmap_rect = RECT()
        self._bitmap_rect.left = 0
        self._bitmap_rect.right = width
        self._bitmap_rect.top = 0
        self._bitmap_rect.bottom = height
        self._bitmap_height = height

        if _debug_font:
            _debug('%r._create_dc(%d, %d)' % (self, width, height))
            _debug('_dc = %r' % self._dc)
            _debug('_bitmap = %r' % self._bitmap)
            _debug('pitch = %r' % pitch)
            _debug('info.bmiHeader.biSize = %r' % info.bmiHeader.biSize)

class Win32Font(base.Font):
    glyph_renderer_class = GDIGlyphRenderer

    def __init__(self, name, size, bold=False, italic=False, dpi=None):
        super(Win32Font, self).__init__()

        self.logfont = self.get_logfont(name, size, bold, italic, dpi)
        self.hfont = gdi32.CreateFontIndirectA(byref(self.logfont))

        # Create a dummy DC for coordinate mapping
        dc = user32.GetDC(0)
        metrics = TEXTMETRIC()
        gdi32.SelectObject(dc, self.hfont)
        gdi32.GetTextMetricsA(dc, byref(metrics))
        self.ascent = metrics.tmAscent
        self.descent = -metrics.tmDescent
        self.max_glyph_width = metrics.tmMaxCharWidth

    @staticmethod
    def get_logfont(name, size, bold, italic, dpi):
        # Create a dummy DC for coordinate mapping
        dc = user32.GetDC(0)
        if dpi is None:
            dpi = 96
        logpixelsy = dpi

        logfont = LOGFONT()
        # Conversion of point size to device pixels
        logfont.lfHeight = int(-size * logpixelsy // 72)
        if bold:
            logfont.lfWeight = FW_BOLD
        else:
            logfont.lfWeight = FW_NORMAL
        logfont.lfItalic = italic
        logfont.lfFaceName = name
        logfont.lfQuality = ANTIALIASED_QUALITY
        return logfont

    @classmethod
    def have_font(cls, name):
        # CreateFontIndirect always returns a font... have to work out
        # something with EnumFontFamily... TODO
        return True

    @classmethod
    def add_font_data(cls, data):
        numfonts = c_uint32()
        gdi32.AddFontMemResourceEx(data, len(data), 0, byref(numfonts))

# --- GDI+ font rendering ---

from fos.lib.pyglet.image.codecs.gdiplus import PixelFormat32bppARGB, gdiplus, Rect
from fos.lib.pyglet.image.codecs.gdiplus import ImageLockModeRead, BitmapData

DriverStringOptionsCmapLookup = 1
DriverStringOptionsRealizedAdvance = 4
TextRenderingHintAntiAlias = 4
TextRenderingHintAntiAliasGridFit = 3

StringFormatFlagsDirectionRightToLeft = 0x00000001
StringFormatFlagsDirectionVertical = 0x00000002
StringFormatFlagsNoFitBlackBox = 0x00000004
StringFormatFlagsDisplayFormatControl = 0x00000020
StringFormatFlagsNoFontFallback = 0x00000400
StringFormatFlagsMeasureTrailingSpaces = 0x00000800
StringFormatFlagsNoWrap = 0x00001000
StringFormatFlagsLineLimit = 0x00002000
StringFormatFlagsNoClip = 0x00004000

class Rectf(ctypes.Structure):
    _fields_ = [
        ('x', ctypes.c_float),
        ('y', ctypes.c_float),
        ('width', ctypes.c_float),
        ('height', ctypes.c_float),
    ]

class GDIPlusGlyphRenderer(Win32GlyphRenderer):
    def _create_bitmap(self, width, height):
        self._data = (ctypes.c_byte * (4 * width * height))()
        self._bitmap = ctypes.c_void_p()
        self._format = PixelFormat32bppARGB 
        gdiplus.GdipCreateBitmapFromScan0(width, height, width * 4,
            self._format, self._data, ctypes.byref(self._bitmap))

        self._graphics = ctypes.c_void_p()
        gdiplus.GdipGetImageGraphicsContext(self._bitmap,
            ctypes.byref(self._graphics))
        gdiplus.GdipSetPageUnit(self._graphics, UnitPixel)

        self._dc = user32.GetDC(0)
        gdi32.SelectObject(self._dc, self.font.hfont)

        gdiplus.GdipSetTextRenderingHint(self._graphics,
            TextRenderingHintAntiAliasGridFit)


        self._brush = ctypes.c_void_p()
        gdiplus.GdipCreateSolidFill(0xffffffff, ctypes.byref(self._brush))

        
        self._matrix = ctypes.c_void_p()
        gdiplus.GdipCreateMatrix(ctypes.byref(self._matrix))

        self._flags = (DriverStringOptionsCmapLookup |
                       DriverStringOptionsRealizedAdvance)

        self._rect = Rect(0, 0, width, height)

        self._bitmap_height = height

    def render(self, text):
        
        ch = ctypes.create_unicode_buffer(text)
        len_ch = len(text)

        # Layout rectangle; not clipped against so not terribly important.
        width = 10000
        height = self._bitmap_height
        rect = Rectf(0, self._bitmap_height 
                        - self.font.ascent + self.font.descent, 
                     width, height)

        # Set up GenericTypographic with 1 character measure range
        generic = ctypes.c_void_p()
        gdiplus.GdipStringFormatGetGenericTypographic(ctypes.byref(generic))
        format = ctypes.c_void_p()
        gdiplus.GdipCloneStringFormat(generic, ctypes.byref(format))

        # Measure advance
        bbox = Rectf()
        flags = (StringFormatFlagsMeasureTrailingSpaces | 
                 StringFormatFlagsNoClip | 
                 StringFormatFlagsNoFitBlackBox)
        gdiplus.GdipSetStringFormatFlags(format, flags)
        gdiplus.GdipMeasureString(self._graphics, ch, len_ch,
            self.font._gdipfont, ctypes.byref(rect), format,
            ctypes.byref(bbox), 0, 0)

        lsb = 0
        advance = int(math.ceil(bbox.width))

        # XXX HACK HACK HACK
        # Windows GDI+ is a filthy broken toy.  No way to measure the bounding
        # box of a string, or to obtain LSB.  What a joke.
        # 
        # For historical note, GDI cannot be used because it cannot composite
        # into a bitmap with alpha.
        #
        # It looks like MS have abandoned GDI and GDI+ and are finally
        # supporting accurate text measurement with alpha composition in .NET
        # 2.0 (WinForms) via the TextRenderer class; this has no C interface
        # though, so we're entirely screwed.
        # 
        # So anyway, this hack bumps up the width if the font is italic;
        # this compensates for some common fonts.  It's also a stupid waste of
        # texture memory.
    
        width = advance
        if self.font.italic:
            width += width // 2
        
        # XXX END HACK HACK HACK

        # Draw character to bitmap
        
        gdiplus.GdipGraphicsClear(self._graphics, 0x00000000)
        gdiplus.GdipDrawString(self._graphics, ch, len_ch,
            self.font._gdipfont, ctypes.byref(rect), format,
            self._brush)
        gdiplus.GdipFlush(self._graphics, 1)

        bitmap_data = BitmapData()
        gdiplus.GdipBitmapLockBits(self._bitmap, 
            byref(self._rect), ImageLockModeRead, self._format, 
            byref(bitmap_data))
        
        # Create buffer for RawImage
        buffer = create_string_buffer(
            bitmap_data.Stride * bitmap_data.Height)
        memmove(buffer, bitmap_data.Scan0, len(buffer))
        
        # Unlock data
        gdiplus.GdipBitmapUnlockBits(self._bitmap, byref(bitmap_data))
        
        image = fos.lib.pyglet.image.ImageData(width, height, 
            'BGRA', buffer, -bitmap_data.Stride)

        glyph = self.font.create_glyph(image)
        glyph.set_bearings(-self.font.descent, lsb, advance)

        return glyph

FontStyleBold = 1
FontStyleItalic = 2
UnitPixel = 2
UnitPoint = 3
        
class GDIPlusFont(Win32Font):
    glyph_renderer_class = GDIPlusGlyphRenderer

    _private_fonts = None

    _default_name = 'Arial'

    def __init__(self, name, size, bold=False, italic=False, dpi=None):
        if not name:
            name = self._default_name
        super(GDIPlusFont, self).__init__(name, size, bold, italic, dpi)

        family = ctypes.c_void_p()
        name = ctypes.c_wchar_p(name)

        # Look in private collection first:
        if self._private_fonts:
            gdiplus.GdipCreateFontFamilyFromName(name,
                self._private_fonts, ctypes.byref(family)) 

        # Then in system collection:
        if not family:
            gdiplus.GdipCreateFontFamilyFromName(name,
                None, ctypes.byref(family)) 

        # Nothing found, use default font.
        if not family:
            name = self._default_name
            gdiplus.GdipCreateFontFamilyFromName(ctypes.c_wchar_p(name),
                None, ctypes.byref(family)) 

        if dpi is None:
            unit = UnitPoint
            self.dpi = 96
        else:
            unit = UnitPixel
            size = (size * dpi) // 72
            self.dpi = dpi

        style = 0
        if bold:
            style |= FontStyleBold
        if italic:
            style |= FontStyleItalic
        self.italic = italic # XXX needed for HACK HACK HACK
        self._gdipfont = ctypes.c_void_p()
        gdiplus.GdipCreateFont(family, ctypes.c_float(size),
            style, unit, ctypes.byref(self._gdipfont))

    @classmethod
    def add_font_data(cls, data):
        super(GDIPlusFont, cls).add_font_data(data)

        if not cls._private_fonts:
            cls._private_fonts = ctypes.c_void_p()
            gdiplus.GdipNewPrivateFontCollection(
                ctypes.byref(cls._private_fonts))
        gdiplus.GdipPrivateAddMemoryFont(cls._private_fonts, data, len(data))
