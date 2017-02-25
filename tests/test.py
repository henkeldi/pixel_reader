# -*- coding: utf-8 -*-

from .context import pixel_reader
from OpenGL.GL import *

import unittest

class Tests(unittest.TestCase):

    def test_input(self):
        self.assertRaises(ValueError, pixel_reader.PixelReader, -1, 100, 100, GL_FLOAT, GL_RGB)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 1, 0, 100, GL_FLOAT, GL_RGB)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 1, 100, -2, GL_FLOAT, GL_RGB)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 2, 100, 100, -13414, GL_RGB)
        self.assertRaises(ValueError, pixel_reader.PixelReader, 2, 100, 100, GL_FLOAT, -2348923)

        try:
            pixel_reader.PixelReader(2, 100, 100, GL_FLOAT, GL_RGB)
        except Exception as e:
            self.fail("PixelReader raised Exception: {}".format(e))

    def test_pixel_read(self):
        reader = pixel_reader.PixelReader(2, 100, 100, GL_FLOAT, GL_RGB)

if __name__ == '__main__':
    unittest.main()