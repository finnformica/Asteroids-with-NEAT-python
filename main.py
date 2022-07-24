import pygame
from pygame import Vector2
import os
import random
import neat
import pickle
import math

# initialise all pygame modules
pygame.init()

# defining game constants
WIDTH = 800
HEIGHT = 800
FPS = 60
FONT = pygame.font.SysFont('Helvetica', 32)
BIG_FONT = pygame.font.SysFont('Helvetica', 85)

GEN = 0

# defining colour constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MAGENTA = (220, 0, 220)
DARK_GREY = (30, 30, 30)

# defining size constants
SHIP_WIDTH = 15
SHIP_HEIGHT = 20

PROJ_WIDTH = 40
PROJ_HEIGHT = 40

# create and label the pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Retro Arcade: Asteroid')

# init a clock
clock = pygame.time.Clock()

SHIP_IMG = pygame.transform.scale(pygame.image.load(os.path.join('imgs', 'spaceship.png')), (SHIP_WIDTH, SHIP_HEIGHT))
ASTEROID_IMGS = [pygame.transform.scale(pygame.image.load(os.path.join('imgs', 'asteroid.png')), (85, 85)),
                 pygame.transform.scale(pygame.image.load(os.path.join('imgs', 'asteroid.png')), (65, 65)),
                 pygame.transform.scale(pygame.image.load(os.path.join('imgs', 'asteroid.png')), (35, 35))]
PROJ_IMG = pygame.transform.scale(pygame.image.load(os.path.join('imgs', 'projectile.png')), (PROJ_WIDTH, PROJ_HEIGHT))
ARROW_IMG = pygame.transform.scale(pygame.image.load(os.path.join('imgs', 'arrow.png')), (150, 150))
ROTARROW_IMG = pygame.transform.scale(pygame.image.load(os.path.join('imgs', 'rotate_arrow.png')), (300, 300))

sign = lambda: 1 if random.random() < 0.5 else -1  # randomly generates 1 or -1

class Spaceship(pygame.sprite.Sprite):

    SHIP_ACC = 0.6
    SHIP_DEC = -0.01

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.image = SHIP_IMG
        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH / 2, HEIGHT / 2)
        self.pos = Vector2(WIDTH / 2, HEIGHT / 2)
        self.vel = Vector2(0, 0)
        self.acc = Vector2(0, 0)
        self.max_speed = Vector2(4, 4)
        self.angle = 0
        self.angular_vel = 4
        self.mask = pygame.mask.from_surface(self.image)

    def forward(self):
        # move in direction its facing
        self.acc = Vector2(math.sin(math.radians(self.angle)), math.cos(math.radians(self.angle))) * -self.SHIP_ACC

    def rotate_left(self):
        self.angle += self.angular_vel  # rotate anti-clockwise

    def rotate_right(self):
        self.angle -= self.angular_vel  # rotate clockwise

    def shoot(self, all_sprites, lasers):
        projectile = Projectile(round(self.rect.x - SHIP_WIDTH // 2), round(self.rect.y - SHIP_HEIGHT // 3), self.angle)
        all_sprites.add(projectile)
        lasers.add(projectile)

    def update(self):

        # equations of motion
        self.acc += self.vel * self.SHIP_DEC
        self.vel += self.acc
        self.pos += 0.5 * self.vel + 0.5 * self.acc

        # limit the top speed
        if self.vel.x > self.max_speed.x:
            self.vel.x = self.max_speed.x
        if self.vel.y > self.max_speed.y:
            self.vel.y = self.max_speed.y

        # teleport ship to opposite side if it leaves the screen
        if self.pos.x > WIDTH + self.image.get_width() / 2:
            self.pos.x = -self.image.get_width() / 2
        if self.pos.x < -self.image.get_width() / 2:
            self.pos.x = WIDTH + self.image.get_width() / 2
        if self.pos.y > HEIGHT + self.image.get_height() / 2:
            self.pos.y = -self.image.get_height() / 2
        if self.pos.y < -self.image.get_height() / 2:
            self.pos.y = HEIGHT + self.image.get_height() / 2

        self.rect.center = self.pos  # update the sprite with calculated position

        # 0 < angle < 360
        if self.angle == 360:
            self.angle = 0
        if self.angle == -4:
            self.angle = 356

        self.image = pygame.transform.rotate(self.original_image, self.angle)


class Asteroid(pygame.sprite.Sprite):

    def __init__(self, size):
        pygame.sprite.Sprite.__init__(self)

        self.image = ASTEROID_IMGS[size]
        self.rect = self.image.get_rect()
        self.size = size

        if self.size == 2:
            self.max_speed = 1.5
        elif self.size == 1:
            self.max_speed = 1
        else:
            self.max_speed = 0.5

        self.pos = Vector2(random.randrange(-self.image.get_width(), WIDTH + self.image.get_width(), WIDTH + self.image.get_width() * 2), random.randrange(HEIGHT))
        self.vel = Vector2(math.tanh(random.randrange(1, 100) * sign()) * self.max_speed, math.tanh(random.randrange(1, 100) * sign()) * self.max_speed)
        self.rect.center = self.pos
        self.angle = math.atan2(self.vel.y, self.vel.x)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.pos.x += self.vel.x
        self.pos.y += self.vel.y

        # teleport asteroid to opposite side if it leaves the screen
        if self.pos.x > WIDTH + self.image.get_width() / 2:
            self.pos.x = -self.image.get_width() / 2
        if self.pos.x < -self.image.get_width() / 2:
            self.pos.x = WIDTH + self.image.get_width() / 2
        if self.pos.y > HEIGHT + self.image.get_height() / 2:
            self.pos.y = -self.image.get_height() / 2
        if self.pos.y < -self.image.get_height() / 2:
            self.pos.y = HEIGHT + self.image.get_height() / 2

        self.rect.center = self.pos

    def split(self, asteroids, all_sprites):
        self.size += 1
        rand = random.randrange(1, 45)

        ob1 = Asteroid(self.size)
        ob2 = Asteroid(self.size)

        ob1.pos = Vector2(self.pos.x, self.pos.y)
        ob1.vel = Vector2(ob1.max_speed * math.sin(math.radians(self.angle + rand)), self.vel.y)

        ob2.pos = Vector2(self.pos.x, self.pos.y)
        ob2.vel = Vector2(ob2.max_speed * math.sin(math.radians(self.angle - rand)), self.vel.y)

        all_sprites.add(ob1, ob2)
        asteroids.add(ob1, ob2)

    def find_cartesian(self, ship):
        x, y = ship.pos.x - self.pos.x, ship.pos.y - self.pos.y
        return (x, y), math.sqrt(x ** 2 + y ** 2)

    def find_polar(self, ship):
        x, y = ship.pos.x - self.pos.x, ship.pos.y - self.pos.y
        radius = math.sqrt(x ** 2 + y ** 2)
        angle = math.degrees(math.atan2(y, x))
        return radius, angle


class Projectile(pygame.sprite.Sprite):

    def __init__(self, x, y, angle):
        pygame.sprite.Sprite.__init__(self)
        self.image = PROJ_IMG
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.angle = math.radians(angle)
        self.vel = Vector2(-8 * math.sin(self.angle), -8 * math.cos(self.angle))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y

        if self.rect.x < 1 or self.rect.x > WIDTH:
            self.kill()
        if self.rect.y < 1 or self.rect.y > HEIGHT:
            self.kill()


def redraw_game_window(screen, all_sprites, score, GEN, number):
    # background
    screen.fill(BLACK)

    # generation, score, ship no.
    display_message('score: ' + str(score), True, WHITE, True, 10, FONT)
    display_message('gen: ' + str(GEN), True, WHITE, 10, 10, FONT)
    display_message('no.: ' + str(number), True, WHITE, False, 10, FONT)

    # sprites
    all_sprites.draw(screen)

    # after drawing everything
    pygame.display.flip()


def check_score(score):
    r = open('best_score.txt', 'r')
    file = r.readlines()
    best_score = int(file[0])

    if best_score < int(score):
        r.close()
        file = open('best_score.txt', 'w')
        file.write(str(score))
        file.close()

        return score

    return best_score


def display_message(string, aliased, colour, xpos, ypos, font):
    message = font.render(string, aliased, colour)
    if xpos == True:
        xpos = WIDTH / 2 - message.get_width() / 2
    if xpos == False:
        xpos = WIDTH - message.get_width() - 20
    screen.blit(message, (xpos, ypos))


def main(genomes, config):  # use a for loop to run the game for each ship
    global GEN
    ships = []
    nets = []
    ge = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)

        ships.append(Spaceship())

        g.fitness = 0
        ge.append(g)

    for x, ship in enumerate(ships):
        number = x + 1

        all_sprites = pygame.sprite.RenderUpdates()
        asteroids = pygame.sprite.Group()
        lasers = pygame.sprite.Group()

        for i in range(6):
            a = Asteroid(random.randrange(2))
            all_sprites.add(a)
            asteroids.add(a)

        a = Asteroid(random.randrange(2))
        a.pos = Vector2(WIDTH / 2, 0)
        a.vel = Vector2(0, -0.5)
        all_sprites.add(a)
        asteroids.add(a)

        all_sprites.add(ship)

        total_asteroids = 6

        score = 0
        end = False
        tick = 0

        # MAIN PYGAME LOOP
        crashed = False
        while not crashed:

            clock.tick(FPS)
            tick += 1

            # process pygame event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    crashed = True
                    pygame.quit()
                    quit()

            ge[x].fitness += 0.001
            # # ###############################
            # d = {}
            # for asteroid in asteroids:
            #     k, v = asteroid.find_distance(ship)
            #     d[k] = v
            #
            # coord = sorted(d, key=lambda i: int(d[i]))
            # input = [num for tup in coord[:6] for num in tup]
            #
            # while len(input) != 12:
            #     input.append(600)
            # input.append(ship.angle)
            # input.extend([ship.pos.x, ship.pos.y])
            #
            # # provide ship angle relative to vertical, ship pos and the relative distances to the 6 closest asteroids
            # output = nets[x].activate(input)
            # # ###############################

            # ###############################
            i = [800, 0]
            for asteroid in asteroids:
                radius, angle = asteroid.find_polar(ship)
                if i[0] > radius:
                    i[0] = radius
                    i[1] = angle

            # provide ship angle relative to vertical, ship pos and the relative distances to the 6 closest asteroids
            output = nets[x].activate(i)
            # ###############################

            if output[0] > 0.5:
                ship.forward()
            if output[1] > 0.5:
                if len(lasers) < 4:
                    ship.shoot(all_sprites, lasers)
            if output[2] > 0.5:
                ship.rotate_left()
            if output[3] > 0.5:
                ship.rotate_right()

            if len(asteroids) < total_asteroids:  # caps no. asteroids
                a = Asteroid(random.randrange(2))
                all_sprites.add(a)
                asteroids.add(a)

            # increment total asteroids
            if total_asteroids < int((score / 10)):
                total_asteroids = int((score / 10))

            # update
            all_sprites.update()

            # check for projectile / asteroid collision
            hits = pygame.sprite.groupcollide(asteroids, lasers, False, True, pygame.sprite.collide_circle_ratio(0.65))
            if hits:
                score += 1
                tick = 0
                ge[x].fitness += 15  # incentivise scoring (shooting asteroids)
                for sprite in hits:
                    if sprite.size < 2:
                        sprite.split(asteroids, all_sprites)
                    sprite.kill()

            if tick >= FPS * 8:
                ge[x].fitness -= 5  # incentivise not idling (8 secs)
                end = True

            # check for player / asteroid collision
            crashes = pygame.sprite.spritecollide(ship, asteroids, False, pygame.sprite.collide_mask)
            if crashes or end:
                check_score(score)
                ge[x].fitness -= 5  # incentivise not hitting asteroids
                ships.pop(x)
                nets.pop(x)
                ge.pop(x)
                crashed = True

            # draw
            redraw_game_window(screen, all_sprites, score, GEN, number)

            if score > 700:  # break program and save neural network if it becomes good enough
                pickle.dump(nets[x], open("best.pickle", "wb"))
                break

    print('Best score of generation: ' + str(open('best_score.txt', 'r').readlines()[0]))
    GEN += 1
    file = open('best_score.txt', 'w')
    file.write(str(0))
    file.close()


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                config_path)

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(main, 50)

    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == '__main__':  # only run if module called directly
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
