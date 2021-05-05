import math
import sys
import os
import array

import numpy as np
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from libs.sensors import Sensors
from libs.const import COLORS, CUBE_SURFACES, CUBE_VERTICIES, CUBE_EDGES
from libs.const import POI_VERTICIES, POI_SURFACES

#https://coolors.co/88a2aa-ada296-e2856e-f42c04-0f1a20

class Poi():

    def __init__(self, loc):
        self.loc = (*loc, 1)

        self.verticies = POI_VERTICIES + np.array(self.loc)

        self.colors = np.array([COLORS["green"] for _ in range(5)])
        self.colors += np.random.random(self.colors.shape) / 15

    def draw(self):
        # glColor3f(*COLORS["red"])
        glBegin(GL_QUADS)
        for surface, color in zip(POI_SURFACES, self.colors):
            glColor3f(*color)
            for vertex in surface:
                glVertex3fv(self.verticies[vertex])
        glEnd()


class Canal():

    def __init__(self):
        self.dist = 0
        self.offset = 0
        self.CANAL_WIDTH = 40
        self.VISIBILITY = (200, -30)

        self.pois = [Poi(self.random_loc()) for _ in range(10)]

    def random_loc(self, ahead=0):
        return(
            np.random.randint(3, self.CANAL_WIDTH - 3) - self.CANAL_WIDTH / 2,
            np.random.randint(self.dist + ahead, self.dist + self.VISIBILITY[0] + ahead)
        )


    def move(self, speed, turn, angle):
        self.angle = angle
        new_offset = self.offset + turn
        new_offset = min(self.CANAL_WIDTH / 2, new_offset)
        new_offset = max(-self.CANAL_WIDTH / 2, new_offset)
        turn = new_offset - self.offset
        self.offset = new_offset

        self.dist += speed
        self.speed = speed
        self.turn = turn

        self.pois = [p for p in self.pois if p.loc[1] > self.dist + self.VISIBILITY[1]] # remove old
        self.pois += [Poi(self.random_loc(ahead=self.VISIBILITY[0])) for _ in range(10 - len(self.pois))] # add some new

        return speed, turn


    def draw_canal_sides(self):
        high = 2
        safety = 100
        slope = 5
        side = self.CANAL_WIDTH // 2
        for direction in (1, -1):
            glBegin(GL_QUADS)
            glColor3f(*COLORS["lighter_brown"])
            verticies = (
                (direction * (side + slope), self.dist + self.VISIBILITY[0], high),
                (direction * side, self.dist + self.VISIBILITY[0], 0),
                (direction * side, self.dist + self.VISIBILITY[1], 0),
                (direction * (side + slope), self.dist + self.VISIBILITY[1], high)
            )
            for vert in verticies:
                glVertex3fv(vert)
            glEnd()

        for direction in (1, -1):
            glBegin(GL_QUADS)
            glColor3f(*COLORS["light_brown"])
            verticies = (
                (direction * (side + slope), self.dist + self.VISIBILITY[0], high),
                (direction * side * safety, self.dist + self.VISIBILITY[0], high),
                (direction * side * safety, self.dist + self.VISIBILITY[1], high),
                (direction * (side + slope), self.dist + self.VISIBILITY[1], high)
            )
            for vert in verticies:
                glVertex3fv(vert)
            glEnd()


    def draw_water(self):
        side = self.CANAL_WIDTH // 2
        glBegin(GL_QUADS)
        glColor3f(*COLORS["light_blue"])
        verticies = (
            (side, self.dist + self.VISIBILITY[0], 0),
            (side, self.dist + self.VISIBILITY[1], 0),
            (-side, self.dist + self.VISIBILITY[1], 0),
            (-side, self.dist + self.VISIBILITY[0], 0),
        )
        for vert in verticies:
            glVertex3fv(vert)
        glEnd()


    def draw_board(self):
        span = 1
        reach = 3
        rot = self.angle * 1.2
        float = 0.3

        verticies = np.array((
            (-span + self.offset, self.dist, rot + float),
            (self.offset - rot, self.dist + reach + abs(rot), 0 + float),
            (span + self.offset, self.dist, -rot + float)
        ))
        glColor3f(*COLORS["red"])
        glBegin(GL_TRIANGLES)
        for vertex in verticies:
            glVertex3fv(vertex)
        glEnd()



    def draw(self):
        self.draw_water()
        self.draw_board()
        self.draw_canal_sides()


        for poi in self.pois:
            if abs(self.dist - poi.loc[1]) < self.VISIBILITY[0]: # TODO check visibility in both direction instead of abs
                poi.draw()


FPS = 30
FULLCSREEN = True

pygame.init()
clock = pygame.time.Clock()

if FULLCSREEN:
    res = pygame.display.list_modes()[0]
    GAME_SCREEN_WIDTH = res[0]
    GAME_SCREEN_HEIGHT = res[1]
    screen = pygame.display.set_mode((GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT), pygame.FULLSCREEN|pygame.DOUBLEBUF|pygame.OPENGL)
else:
    GAME_SCREEN_WIDTH = 1400
    GAME_SCREEN_HEIGHT = 900
    screen = pygame.display.set_mode((GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT), pygame.DOUBLEBUF | pygame.OPENGL)


gluPerspective(45, (GAME_SCREEN_WIDTH/GAME_SCREEN_HEIGHT), 0.1, 200.0)
glEnable(GL_DEPTH_TEST)

canal = Canal()
sensors = Sensors()

glTranslatef(0.0, -5, -15)
glRotatef(-70, 1, 0, 0)
glClearColor(*COLORS["black"], 1)

print(sensors.get_address())


pygame.mixer.init()
pygame.mixer.set_num_channels(8)
voice = pygame.mixer.Channel(5)
sound = pygame.mixer.Sound("sound1.wav")
voice.play(sound, loops=-1)
voice.set_volume(0)

done = False
while not done:


    # default
    speed = 0.3
    turn = 0

    # acc input
    sensor_data = sensors.get_values()
    acc = sensor_data["acc1"]["data"]
    angle = math.atan2(-acc[0], acc[2])
    TURN_FACTOR = 1
    turn = angle * TURN_FACTOR

    # keyboard input
    pygame.event.pump()
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_UP] or pressed[pygame.K_w]:
        speed = 0.1
    elif pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
        speed = -0.1
    elif pressed[pygame.K_LEFT] or pressed[pygame.K_a]:
        turn = -0.1
        angle = -0.2
    elif pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
        turn = 0.1
        angle = 0.2
    if pressed[pygame.K_q] or pressed[pygame.K_ESCAPE]:
        done = True
        sensors.stop()
        pygame.quit()
        quit()
        sys.exit()

    # if abs(turn) > 0.09:
    #     voice.set_volume(turn * 2)
    #     if not voice.get_busy():
    #         voice.play(sound, loops=-1)
    # elif voice.get_busy():
    #     voice.stop()

    voice.set_volume(max(abs(turn) * 4, 0.05))




    speed, turn = canal.move(speed, turn, angle)

    glTranslatef(-turn, -speed, 0)

    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    canal.draw()

    pygame.display.flip()
    clock.tick(FPS)
