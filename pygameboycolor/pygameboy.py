from OpenGL.GL import *
from pathlib import Path

import glfw
import numpy
import pygameboycore
import sys
import time

GB_WIDTH = 160
GB_HEIGHT = 144
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480

class PyGameboyColor(object):
    def __init__(self, width, height):
        if not glfw.init():
            raise Exception('cannot initialize glfw')

        window = glfw.create_window(width, height, "PyGameboyColor", None, None)

        if not window:
            glfw.terminate()
            raise Exception('cannot create glfw window')

        glfw.make_context_current(window)

        self.window = window

        self.color_frame_buffer = numpy.empty(
            GB_WIDTH * GB_HEIGHT * 3,
            numpy.uint8
        )

        glEnable(GL_TEXTURE_2D)
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            GB_WIDTH,
            GB_HEIGHT,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            self.color_frame_buffer,
        )

        self.core = pygameboycore.GameboyCore()

        glfw.set_key_callback(self.window, self.process_input)

        self.action_map = {
            glfw.PRESS: pygameboycore.KeyAction.ACTION_PRESS,
            glfw.RELEASE: pygameboycore.KeyAction.ACTION_RELEASE,
        }

        self.key_map = {
            glfw.KEY_W: pygameboycore.JoypadKey.KEY_UP,
            glfw.KEY_A: pygameboycore.JoypadKey.KEY_LEFT,
            glfw.KEY_D: pygameboycore.JoypadKey.KEY_RIGHT,
            glfw.KEY_S: pygameboycore.JoypadKey.KEY_DOWN,
            glfw.KEY_J: pygameboycore.JoypadKey.KEY_A,
            glfw.KEY_K: pygameboycore.JoypadKey.KEY_B,
            glfw.KEY_ENTER: pygameboycore.JoypadKey.KEY_START,
            glfw.KEY_LEFT_SHIFT: pygameboycore.JoypadKey.KEY_SELECT,
        }

    def load_state(self, filename):
        save_filename = f'{filename}.sav'
        if Path(save_filename).is_file():
            with open(save_filename, 'r') as save_file:
                save_state = list(map(int, save_file.read().split('\n')))
                self.core.set_save_data(save_state)

    def save_state(self, filename):
        save_filename = f'{filename}.sav'
        with open(save_filename, 'w') as save_file:
            save_file.write('\n'.join(map(str, self.core.get_save_data())))

    def vblank_callback(self, framebuffer):
        self.color_frame_buffer[:] = framebuffer

    def process_input(self, window, key, scancode, action, mods):
        if key not in self.key_map:
            return

        if action not in self.action_map:
            return

        gbaction = self.action_map[action]
        gbkey = self.key_map[key]

        self.core.input(gbkey, gbaction)

    def run(self, filename):
        self.core.open(filename)

        self.load_state(filename)

        self.core.register_vblank_callback(self.vblank_callback)

        try:
            while not glfw.window_should_close(self.window):
                glfw.poll_events()

                self.core.update()

                self.render()
        except KeyboardInterrupt:
            pass

        self.save_state(filename)

        glfw.terminate()

    def render(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0, 
            0,
            0,
            GB_WIDTH,
            GB_HEIGHT,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            self.color_frame_buffer,
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, GB_WIDTH, 0.0, GB_HEIGHT, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)

        glBegin(GL_QUADS)
        glTexCoord2d(0.0, 1.0)
        glVertex2d(0.0, 0.0)
        glTexCoord2d(1.0, 1.0)
        glVertex2d(GB_WIDTH, 0.0)
        glTexCoord2d(1.0, 0.0)
        glVertex2d(GB_WIDTH, GB_HEIGHT)
        glTexCoord2d(0.0, 0.0)
        glVertex2d(0.0, GB_HEIGHT)
        glEnd()

        glfw.swap_buffers(self.window)

def main():
    gb = PyGameboyColor(WINDOW_WIDTH, WINDOW_HEIGHT)
    gb.run(sys.argv[1])

if __name__ == '__main__':
    main()
