"""
Main loop.
"""
import os

import pygame
import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *

from tools.geometry import dist, square_dist, rotate_array, rot, unit_vector

from entities.person import Person
from entities.scenery import Scenery
from entities.map import Map

def draw_cross():
    CPOINTS = np.array((
        (0, 0, 1),
        (1000, 0, 1),
        (0, 0, 1),
        (0, 1000, 1)
    ), dtype="int32")
    glLineWidth(5.0)
    glColor3f(0.9, 0.0, 0.0)
    glBegin(GL_LINES)
    glVertex3fv(CPOINTS[0])
    glVertex3fv(CPOINTS[1])
    glEnd()
    glColor3f(0.0, 0.9, 0.0)
    glBegin(GL_LINES)
    glVertex3fv(CPOINTS[2])
    glVertex3fv(CPOINTS[3])
    glEnd()


MAP_NAME = "maps.map1"
FULLSCREEN = False
TEST_MODE = False
ZOOM_INCREMENT = 25
VIEW_AS_BIRD = False
VIEW_AS_FIRST = True
fog_switch = False


os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)


pygame.init()
clock = pygame.time.Clock()
res = pygame.display.list_modes()[0]


if FULLSCREEN:
    GAME_SCREEN_WIDTH = res[0]
    GAME_SCREEN_HEIGHT = res[1]
    screen = pygame.display.set_mode((GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT), pygame.FULLSCREEN|pygame.DOUBLEBUF|pygame.OPENGL)
else:
    GAME_SCREEN_WIDTH = 1100
    GAME_SCREEN_HEIGHT = 700
    screen = pygame.display.set_mode((GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT), pygame.DOUBLEBUF|pygame.OPENGL)


common = {}
common["zoom"] = 500
common["screen"] = screen
res = pygame.display.get_surface().get_size()
done = False
pygame.mouse.set_visible(False)

if not TEST_MODE:
    CROSS_POS = (int(res[0] * 0.5), int(res[1] * 0.75))
else:
    CROSS_POS = (int(res[0] * 0.25), int(res[1] * 0.75))

pygame.mouse.set_pos(CROSS_POS[0], 100)
basicfont = pygame.font.SysFont(None, 20)




# scenery and level init stuff

cx = 0
cy = 0
a = 0
b = 0
zT = 180

scenery = Scenery(Map(MAP_NAME), cx, cy)
scenery.start()

player = Person(scenery, "player", cx, cy)
creatures = [player,]

# npc = Person(scenery, "npc1", -100, -100)
# creatures.append(npc)

for k in range(10):
    creatures.append(Person(scenery, "npc1", 100, -200-k*100))

scenery.creatures = creatures

scenery.update(cx, cy)

while not scenery.ready:
    # wait till boards are ready
    pass





gluPerspective(70, (res[0] / res[1]), 1., 10000.0)

if VIEW_AS_BIRD:
    glViewport (0, -int(res[1]*0.75), res[0], int(res[1]*1.75) )
    common["zoom"] = 250
elif VIEW_AS_FIRST:
    common["zoom"] = 0

glEnable(GL_DEPTH_TEST)
glDepthFunc(GL_LESS)
glEnable(GL_BLEND)

# glEnable(GL_CULL_FACE)
# glDisable(GL_CULL_FACE);


glClearColor (0.529,  0.808, 0.922, 0.5)




glTranslatef(cx, cy, -common["zoom"])



if VIEW_AS_BIRD:
    glRotatef(0, 1, 0, 0)
elif VIEW_AS_FIRST:
    glRotatef(-90, 1, 0, 0)
    glTranslatef(cx, cy, -zT)
else:
    glRotatef(-70, 1, 0, 0)

sc = [0, 0]
while not done:
    x = 0
    y = 0
    z = 0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 and common["zoom"] > 200:
                z = -ZOOM_INCREMENT
                common["zoom"] += z
            if event.button == 5 and common["zoom"] < 1500:
                z = ZOOM_INCREMENT
                common["zoom"] += z

    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_ESCAPE]:
        done = True
        scenery.stop()
    if pressed[pygame.K_KP_PLUS] and common["zoom"] > 200:
        z = -ZOOM_INCREMENT
        common["zoom"] += z
    if pressed[pygame.K_KP_MINUS] and common["zoom"] < 1500:
        z = ZOOM_INCREMENT
        common["zoom"] += z
    if pressed[pygame.K_f]:
        if not fog_switch:
            fog_switch = True
            glEnable(GL_FOG)
            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogfv(GL_FOG_COLOR, [0.1, 0.1, 0.1])
            glFogf(GL_FOG_START, 0.0)
            glFogf(GL_FOG_END, 2.)
            glHint(GL_FOG_HINT, GL_NICEST)
        else:
            fog_switch = False
            glDisable(GL_FOG)


    # mouse stuff
    mx, my = pygame.mouse.get_pos()
    mx, my = CROSS_POS[0] - mx, CROSS_POS[1] - my
    a_delta = -mx * 0.05
    b_delta = -my * 0.05
    a += a_delta * np.pi / 180.
    b += b_delta * np.pi / 180.
    pygame.mouse.set_pos(CROSS_POS[0], CROSS_POS[1])


    if pressed[pygame.K_UP] or pressed[pygame.K_w]:
        player.intention = "walk-front"
    elif pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
        player.intention = "walk-back"
    elif pressed[pygame.K_LEFT] or pressed[pygame.K_a]:
        player.intention = "walk-left"
    elif pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
        player.intention = "walk-right"
    else:
        player.intention = "idle"


    x, y, delta_z = player.controlled(a)
    cx, cy, cz = player.get_position()


    # movement
    glTranslatef(-x, -y, -z - delta_z)

    # rotation
    glTranslatef(cx, cy, cz+zT)
    glTranslatef(sc[0], sc[1], 0)
    glRotatef(a_delta, 0, 0, 1)
    sc = rot(0, -100, -a)
    glTranslatef(-sc[0], -sc[1], 0)
    glRotatef(b_delta, np.cos(a), -np.sin(a), 0)
    glTranslatef(-cx, -cy, -cz-zT)



    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)




    pygame.display.flip()
    clock.tick(40)



