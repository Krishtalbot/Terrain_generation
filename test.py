import noise
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

movement_speed = 0.3
rotation_angle = 0.3


class Vector(object):
    def __init__(self, x, y, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def normalize(self):
        length = np.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
        if length != 0:
            self.x /= length
            self.y /= length
            self.z /= length


scale = 15.0
target_scale = scale
height_scale = 10

octaves = 8
octaveOffsets = []

persistence = 0.5
lacunarity = 2

flattening_threshold = 0.0125

for i in range(octaves):
    octaveOffsets.append(
        Vector(np.random.randint(-10000, 10000), np.random.randint(-10000, 10000)))

terrain_size = 200
terrain = []
offset = Vector(0, 0, 50)
target_offset = Vector(0, 0, 50)
normals = np.zeros((terrain_size, terrain_size, 3), dtype=np.float32)

# Smooth interpolation factor
lerp_factor = 0.1


def animate(_):
    global offset, target_offset, scale, target_scale

    # Smoothly interpolate offsets and scale
    offset.x = np.interp(lerp_factor, [0, 1], [offset.x, target_offset.x])
    offset.y = np.interp(lerp_factor, [0, 1], [offset.y, target_offset.y])
    offset.z = np.interp(lerp_factor, [0, 1], [offset.z, target_offset.z])
    scale = np.interp(lerp_factor, [0, 1], [scale, target_scale])

    # Update terrain and display
    calculate_terrain()
    glutPostRedisplay()

    # Set up the next animation frame
    glutTimerFunc(16, animate, 0)


def calculate_terrain():
    global terrain
    terrain = []
    for y in range(terrain_size):
        terrain.append([])
        for x in range(terrain_size):
            terrain[-1].append(0)

    for y in range(terrain_size):
        for x in range(terrain_size):
            amplitude = 1
            frequency = 1
            noiseHeight = 0
            for i in range(octaves):
                sampleX = frequency * \
                    (x + octaveOffsets[i].x + offset.x) / scale
                sampleY = frequency * \
                    (y + octaveOffsets[i].y + offset.y) / scale
                noiseHeight += amplitude * noise.pnoise2(sampleX, sampleY)
                amplitude *= persistence
                frequency *= lacunarity
            terrain[x][y] = noiseHeight

    min_val = np.min(terrain)
    max_val = np.max(terrain)

    terrain = np.array(terrain)
    np.clip(terrain, -0.71, max_val)

    calculate_normals()


color_heights = [-0.7078, -0.6518, -0.5057, -
                 0.27, -0.07, 0.1765, 0.3725, 0.5686, 0.9608]


def calculate_normals():
    global normals
    normals = np.zeros((terrain_size, terrain_size, 3), dtype=np.float32)

    for y in range(terrain_size):
        for x in range(terrain_size):
            dx = terrain[(x + 1) % terrain_size][y] - terrain[x][y]
            dy = terrain[x][(y + 1) % terrain_size] - terrain[x][y]

            normal = Vector(dy, -dx, 2.0)
            normal.normalize()

            normals[x][y] = [normal.x, normal.y, normal.z]


def keyboard(bkey, x, y):
    global target_offset, target_scale

    key = bkey.decode("utf-8")
    if key == 'w':
        target_offset.y += offset.z
    elif key == 'a':
        target_offset.x -= offset.z
    elif key == 's':
        target_offset.y -= offset.z
    elif key == 'd':
        target_offset.x += offset.z
    elif key == 'up':
        target_scale *= 1.1  # Increase scale for zooming in
    elif key == 'down':
        target_scale /= 1.1


def keyboard_special(key, x, y):
    global scale
    if key == GLUT_KEY_UP:
        scale *= 1.1  # Increase scale for zooming in
    elif key == GLUT_KEY_DOWN:
        scale /= 1.1  # Decrease scale for zooming out
    calculate_terrain()


def initGL():
    calculate_terrain()
    glClear(GL_COLOR_BUFFER_BIT)
    glClearDepth(1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glShadeModel(GL_SMOOTH)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_DIFFUSE)


def getColor(value):
    global color_heights
    if value < color_heights[0]:
        return 42 / 255.0, 93 / 255.0, 186 / 255.0
    elif color_heights[0] <= value < color_heights[1]:
        return 51 / 255.0, 102 / 255.0, 195 / 255.0
    elif color_heights[1] <= value < color_heights[2]:
        return 207 / 255.0, 215 / 255.0, 127 / 255.0
    elif color_heights[2] <= value < color_heights[3]:
        return 91 / 255.0, 169 / 255.0, 24 / 255.0
    elif color_heights[3] <= value < color_heights[4]:
        return 63 / 255.0, 119 / 255.0, 17 / 255.0
    elif color_heights[4] <= value < color_heights[5]:
        return 89 / 255.0, 68 / 255.0, 61 / 255.0
    elif color_heights[5] <= value < color_heights[6]:
        return 74 / 255.0, 59 / 255.0, 55 / 255.0
    elif color_heights[6] <= value < color_heights[7]:
        return 250 / 255.0, 250 / 255.0, 250 / 255.0
    elif value >= color_heights[7]:
        return 1, 1, 1


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glTranslatef(-terrain_size / 2.0, -25, -6)
    glRotate(60, -1, 0, 0)
    glEnableClientState(GL_NORMAL_ARRAY)
    glNormalPointer(GL_FLOAT, 0, normals)
    offset.x += movement_speed
    glBegin(GL_TRIANGLES)
    for y in range(1, terrain_size - 1):
        for x in range(1, terrain_size - 1):
            if terrain[x][y + 1] < flattening_threshold:
                glNormal3fv(normals[x][y + 1])
                color = getColor(terrain[x][y + 1])
                glColor3f(color[0], color[1], color[2])
                glVertex(x, (y + 1), 0)
            else:
                glNormal3fv(normals[x][y])
                color = getColor(terrain[x][y + 1])
                glColor3f(color[0], color[1], color[2])
                glVertex3f(x, (y + 1), (terrain[x][y + 1] * height_scale))

            if terrain[x][y] < flattening_threshold:
                color = getColor(terrain[x][y])
                glColor3f(color[0], color[1], color[2])
                glVertex3f(x, y, 0)
            else:
                color = getColor(terrain[x][y])
                glColor3f(color[0], color[1], color[2])
                glVertex3f(x, y, (terrain[x][y] * height_scale))

            if terrain[x + 1][y + 1] < flattening_threshold:
                glNormal3fv(normals[x + 1][y + 1])
                color = getColor(terrain[x + 1][y + 1])
                glColor3f(color[0], color[1], color[2])
                glVertex3f((x + 1), (y + 1), 0)
            else:
                color = getColor(terrain[x + 1][y + 1])
                glColor3f(color[0], color[1], color[2])
                glVertex3f((x + 1), (y + 1),
                           (terrain[x + 1][y + 1] * height_scale))
    glEnd()

    glBegin(GL_TRIANGLES)
    for y in range(1, terrain_size - 1):
        for x in range(1, terrain_size - 1):
            if terrain[x + 1][y + 1] < flattening_threshold:
                color = getColor(terrain[x + 1][y + 1])
                glColor3f(color[0], color[1], color[2])
                glVertex3f((x + 1), (y + 1), 0)
            else:
                color = getColor(terrain[x + 1][y + 1])
                glColor3f(color[0], color[1], color[2])
                glVertex3f((x + 1), (y + 1),
                           (terrain[x + 1][y + 1] * height_scale))

            if terrain[x + 1][y] < flattening_threshold:
                color = getColor(terrain[x + 1][y])
                glColor3f(color[0], color[1], color[2])
                glVertex3f((x + 1), y, 0)
            else:
                color = getColor(terrain[x + 1][y])
                glColor3f(color[0], color[1], color[2])
                glVertex3f((x + 1), y, (terrain[x + 1][y] * height_scale))

            if terrain[x][y] < flattening_threshold:
                color = getColor(terrain[x][y])
                glColor3f(color[0], color[1], color[2])
                glVertex3f(x, y, 0)
            else:
                color = getColor(terrain[x][y])
                glColor3f(color[0], color[1], color[2])
                glVertex3f(x, y, (terrain[x][y] * height_scale))
    glEnd()
    glutSwapBuffers()


def reshape(width, height):
    if height == 0:
        height = 1
    aspect = width / height

    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    gluPerspective(45.0, aspect, 0.1, 100.0)


if __name__ == '__main__':
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutInitWindowPosition(50, 50)
    glutCreateWindow("3D Terrain")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(keyboard_special)  # Register the special keyboard function
    initGL()
    glutTimerFunc(0, animate, 0)

    glutMainLoop()
