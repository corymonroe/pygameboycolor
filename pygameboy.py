from OpenGL.GL import *

import glfw
import numpy
import pygameboycore
import sys
import time

GB_SIZE = (160, 144)
WINDOW_SIZE = (640, 480)

class PyGameboyColor(object):
    def __init__(self, dim):
        self.vblank = False

        if not glfw.init():
            return
        window = glfw.create_window(dim[0], dim[1], "PyGameboy Color", None, None)

        if not window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(window)

        self.window = window

        # 160x144 is the Gameboy window size
        self.color_frame_buffer = numpy.zeros(
            GB_SIZE[0] * GB_SIZE[1] * 4,
            numpy.uint8
        )

        glEnable(GL_TEXTURE_2D)
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            GB_SIZE[0],
            GB_SIZE[1],
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            self.color_frame_buffer,
        )

        self.core = pygameboycore.GameboyCore()

        glfw.set_key_callback(self.window, self.process_input)

        self.action_map = {
            glfw.PRESS:pygameboycore.KeyAction.ACTION_PRESS,
            glfw.RELEASE:pygameboycore.KeyAction.ACTION_RELEASE,
        }

        self.key_map = {
            glfw.KEY_W:pygameboycore.JoypadKey.KEY_UP,
            glfw.KEY_A:pygameboycore.JoypadKey.KEY_LEFT,
            glfw.KEY_D:pygameboycore.JoypadKey.KEY_RIGHT,
            glfw.KEY_S:pygameboycore.JoypadKey.KEY_DOWN,
            glfw.KEY_J:pygameboycore.JoypadKey.KEY_A,
            glfw.KEY_K:pygameboycore.JoypadKey.KEY_B,
            glfw.KEY_ENTER:pygameboycore.JoypadKey.KEY_START,
            glfw.KEY_LEFT_SHIFT:pygameboycore.JoypadKey.KEY_SELECT,
        }

    def run(self, filename):
        self.core.open(filename)
        self.core.register_scanline_callback(self.scanline_callback)
        self.core.register_vblank_callback(self.vblank_callback)

        # Loop until the user closes the window
        fps = 0
        global_start = time.time()
        while not glfw.window_should_close(self.window):
            glfw.poll_events()

            self.vblank = False
            while not self.vblank:
                self.core.update(512)

            self.render()

            fps += 1
            global_curr = time.time()

            if global_curr - global_start > 1.0:
                print(f'FPS: {fps}')
                fps = 0
                global_start = global_curr

        glfw.terminate()

    def process_input(self, window, key, scancode, action, mods):
        if key not in self.key_map:
            return

        if action not in self.action_map:
            return

        gbaction = self.action_map[action]
        gbkey = self.key_map[key]

        self.core.input(gbkey, gbaction)

    def scanline_callback(self, scanline, line):
        w = GB_SIZE[0]
        for i in range(len(scanline)):
            pixel = scanline[i]
            index = (i + (w * line)) * 4
            self.color_frame_buffer[index] = pixel.r
            self.color_frame_buffer[index+1] = pixel.g
            self.color_frame_buffer[index+2] = pixel.b

    def vblank_callback(self):
        self.vblank = True

    def render(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0, 
            0,
            0,
            GB_SIZE[0],
            GB_SIZE[1],
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            self.color_frame_buffer,
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, GB_SIZE[0], 0.0, GB_SIZE[1], -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)

        glBegin(GL_QUADS)
        glTexCoord2d(0.0, 1.0)
        glVertex2d(0.0, 0.0)
        glTexCoord2d(1.0, 1.0)
        glVertex2d(GB_SIZE[0], 0.0)
        glTexCoord2d(1.0, 0.0)
        glVertex2d(GB_SIZE[0], GB_SIZE[1])
        glTexCoord2d(0.0, 0.0)
        glVertex2d(0.0, GB_SIZE[1])
        glEnd()

        glfw.swap_buffers(self.window)

def main():
    gb = PyGameboyColor(WINDOW_SIZE)
    gb.run(sys.argv[1])

if __name__ == '__main__':
    main()
