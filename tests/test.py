# -*- coding: utf-8 -*-
import unittest
import numpy as np

from gl_utils import OffscreenContext

from OpenGL.GL import *
from .context import pixel_reader

class Tests(unittest.TestCase):

    def setUp(self):
        self.context = OffscreenContext()

    def tearDown(self):
        self.context.close()

    def test_input(self):
        self.assertRaises(ValueError, pixel_reader.PixelReader, 100, 100, GL_RGB, GL_FLOAT, -1)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 0, 100, GL_RGB, GL_FLOAT, 1)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 100, -2, GL_RGB, GL_FLOAT, 1)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 100, 100, GL_RGB, -13414, 2)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 100, 100, -2348923, GL_FLOAT, 2)
        try:
            pixel_reader.PixelReader(100, 100, GL_RGB, GL_FLOAT, 2)
        except Exception as e:
            self.fail("PixelReader raised Exception: {}".format(e))


    def test_pixel_read(self):
        '''Test which makes sure that the PixelReader produces the same output as pure glReadPixels and that its actually faster
        '''
        H, W = 743, 458
        N = 142

        tex = np.empty(2, dtype=np.uint32)
        glCreateTextures(GL_TEXTURE_2D, len(tex), tex)

        glTextureStorage2D(tex[0], 1, GL_RGB32F, W, H)
        glTextureParameteri(tex[0], GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTextureParameteri(tex[0], GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glTextureStorage2D(tex[1], 1, GL_DEPTH_COMPONENT32F, W, H)
        glTextureParameteri(tex[1], GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTextureParameteri(tex[1], GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        fbo = np.empty(1, dtype=np.uint32)
        glCreateFramebuffers(1, fbo)
        glNamedFramebufferTexture(fbo, GL_COLOR_ATTACHMENT0, tex[0], 0)
        glNamedFramebufferTexture(fbo, GL_DEPTH_ATTACHMENT, tex[1], 0)

        assert glCheckNamedFramebufferStatus(fbo, GL_FRAMEBUFFER)\
                        == GL_FRAMEBUFFER_COMPLETE, 'Framebuffer not complete'

        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glClearColor(0.2, 0.4, 0.8, 1.0)
        glClear(GL_COLOR_BUFFER_BIT| GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, W, H)

        random_colors = np.random.random((N, 4)).astype(np.float32, copy=True)

        datatype = GL_FLOAT
        pixel_format = GL_RGB

        reader = pixel_reader.PixelReader(W, H, pixel_format, datatype)
        
        gl_read_pixels_out = []

        import time

        t1 = time.time()
        for i in xrange(N):
            glClearBufferfv(GL_COLOR, 0, random_colors[i])
            screenshot = glReadPixels(0, 0, W, H, pixel_format, datatype)
            gl_read_pixels_out.append( screenshot )
        t2 = time.time()

        glClearColor(0.2, 0.4, 0.8, 1.0)
        glClear(GL_COLOR_BUFFER_BIT| GL_DEPTH_BUFFER_BIT)

        t3 = time.time()
        for i in xrange(N):
            glClearBufferfv(GL_COLOR, 0, random_colors[i])
            reader.readPixels()

        reader.flush()
        pixel_reader_out = list(reader)
        t4 = time.time()

        self.assertTrue( len(gl_read_pixels_out)==len(pixel_reader_out) )

        for gl_pixel, pixel in zip(gl_read_pixels_out, pixel_reader_out):
            self.assertTrue( np.all( np.equal(gl_pixel, pixel) ) )

        time_gl = t2 - t1
        time_pixel_reader = t4 - t3
        self.assertTrue( time_pixel_reader < time_gl )

if __name__ == '__main__':
    unittest.main()