# -*- coding: utf-8 -*-
import numpy as np
from Queue import Queue

from OpenGL.GL import *

class PixelReader(object):

    bytes_per_datatype= {
        GL_UNSIGNED_BYTE:1,
        GL_BYTE:1,
        GL_UNSIGNED_SHORT:2,
        GL_SHORT:2,
        GL_UNSIGNED_INT:4,
        GL_INT:4,
        GL_FLOAT:4,
    }

    known_formattypes = [
        GL_DEPTH_COMPONENT,
        GL_RED,
        GL_GREEN,
        GL_BLUE,
        GL_ALPHA,
        GL_RGB,
        GL_BGR,
        GL_RGBA,
        GL_BGRA,
        GL_LUMINANCE,
        GL_LUMINANCE_ALPHA
    ]

    formattypes_numchannels = {
        GL_COLOR_INDEX:1,
        GL_STENCIL_INDEX:1,
        GL_DEPTH_COMPONENT:1,
        GL_RED:1,
        GL_GREEN:1,
        GL_BLUE:1,
        GL_ALPHA:1,
        GL_RGB:3,
        GL_BGR:3,
        GL_RGBA:4,
        GL_BGRA:4,
        GL_LUMINANCE:1,
        GL_LUMINANCE_ALPHA:1
    }

    formattype_to_ctypes = {
        GL_UNSIGNED_BYTE: ctypes.c_ubyte,
        GL_BYTE: ctypes.c_byte,
        GL_UNSIGNED_SHORT: ctypes.c_ushort,
        GL_SHORT: ctypes.c_short,
        GL_UNSIGNED_INT: ctypes.c_uint,
        GL_INT: ctypes.c_int,
        GL_FLOAT: ctypes.c_float
    } 

    def __init__(self, x0, y0, W, H, pixel_format, datatype, ringbuffer_size=2, max_sync_wait_time=1000000000):
        self.__check_input_args(x0, y0, W, H, pixel_format, datatype, ringbuffer_size)

        self.__buf_idx = 0
        self.__memory_pointer = []
        self.__fences = []
        self.__datatype_byte_count = PixelReader.bytes_per_datatype[datatype]
        self.__c_type_format = PixelReader.formattype_to_ctypes[datatype]
        self.__C = PixelReader.formattypes_numchannels[pixel_format]

        self.__pbo = np.empty(ringbuffer_size, dtype=np.uint32)
        glCreateBuffers(len(self.__pbo), self.__pbo)
        for i in xrange(ringbuffer_size):
            num_bytes = self.__datatype_byte_count*self.__C*W*H
            glNamedBufferStorage(self.__pbo[i], num_bytes, None, GL_MAP_READ_BIT|GL_MAP_PERSISTENT_BIT)
            ptr = glMapNamedBufferRange(self.__pbo[i], 0, num_bytes, GL_MAP_READ_BIT|GL_MAP_PERSISTENT_BIT)
            self.__memory_pointer.append(ptr)
            self.__fences.append(None)

        self.__ringbuffer_size = ringbuffer_size
        self.__x0 = x0
        self.__y0 = y0
        self.__W = W
        self.__H = H
        self.__datatype = datatype
        self.__pixel_format = pixel_format
        self.__sync_wait_time = max_sync_wait_time

        self.__queue = Queue()

    def __check_input_args(self, x0, y0, W, H, pixel_format, datatype, ring_buffer_size):
        if x0 < 0:
            raise ValueError('x0 must be bigger or equal 0. Is {0}'.format(x0))
        if y0 < 0:
            raise ValueError('y0 must be bigger or equal 0. Is {0}'.format(y0))
        if W <= 0:
            raise ValueError('Width must be bigger 0. Is {0}'.format(W))
        if H <= 0:
            raise ValueError('Height must be bigger 0. Is {0}'.format(H))
        if not datatype in PixelReader.bytes_per_datatype.keys():
            raise ValueError('Unknown Datatype: {0}'.format(datatype))
        if not pixel_format in PixelReader.known_formattypes:
            raise ValueError('Unknown pixel format: {0}'.format(pixel_format))
        if ring_buffer_size <= 0:
            raise ValueError('Ringbuffersize must be bigger 0. Is {0}'.format(ring_buffer_size))

    def readPixels(self):
        write_buf_idx = self.__buf_idx
        read_buf_idx = (self.__buf_idx-self.__ringbuffer_size/2) % self.__ringbuffer_size

        glBindBuffer(GL_PIXEL_PACK_BUFFER, self.__pbo[write_buf_idx])
        glReadPixels(0, 0, self.__W, self.__H, self.__pixel_format, self.__datatype, 0)
        self.__fences[write_buf_idx] = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)

        self.__read_pixels(read_buf_idx)

        self.__buf_idx = (self.__buf_idx+1) % self.__ringbuffer_size

    def __read_pixels(self, read_buf_idx):
        if self.__fences[read_buf_idx] != None:
            glClientWaitSync(self.__fences[read_buf_idx], GL_SYNC_FLUSH_COMMANDS_BIT, self.__sync_wait_time)
            if self.__C == 1:
                pixels = np.ctypeslib.as_array((self.__c_type_format * self.__H*self.__W).from_address(self.__memory_pointer[read_buf_idx])).copy()
            else:
                pixels = np.ctypeslib.as_array((self.__c_type_format * self.__C*self.__H*self.__W).from_address(self.__memory_pointer[read_buf_idx])).copy()
            self.__queue.put(pixels)
            glDeleteSync(self.__fences[read_buf_idx])
            self.__fences[read_buf_idx] = None

    def __iter__(self):
        return self

    def next(self):
        if self.__queue.qsize() > 0:
            return self.__queue.get()
        else:
            raise StopIteration()

    def flush(self):
        for _ in  xrange(self.__ringbuffer_size):
            read_buf_idx = (self.__buf_idx-self.__ringbuffer_size/2) % self.__ringbuffer_size
            self.__read_pixels(read_buf_idx)
            self.__buf_idx = (self.__buf_idx+1) % self.__ringbuffer_size
        self.__buf_idx = 0