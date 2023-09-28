import pygame
import neat
import time
import os
import random
pygame.font.init()
#constantes para as imagens e tamanho da janela
WIN_WIDTH = 500
WIN_HEIGTH = 800

GEN = 0

                            #se nao funcionar colocar na mesma linha Bird img
BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("bird1.png"))), 
               pygame.transform.scale2x(pygame.image.load(os.path.join("bird2.png"))), 
               pygame.transform.scale2x(pygame.image.load(os.path.join("bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("bg.png")))
#const pra fonte
STAT_FONT = pygame.font.SysFont("comicsans", 50)

#classe pato
class Bird:
    IMGS = BIRD_IMAGES
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0    
        self.height = self.y

    def move(self):
        self.tick_count += 1
        #calculo para saber o quanto o passaro vai se mover //fisica do pato
        d =  self.vel * self.tick_count + 1.5*self.tick_count**2

        if d >= 16:
            d = 16

        if d< 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION

        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):#funçao pra mudar o desenho do pato //asa aberta/fechada 
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]       
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1] 
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0] 
            self.img_count = 0      

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2
        #rotaciona a imagem no centro, assim quando o pato sobe ele inclina pra cima
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center) 
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

#criando os canos 
class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        

        self.top = 0
        self.botton = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)#inverte a img do cano
        self.PIPE_BOTTON = PIPE_IMG

        self.passed = False
        self.set_height()
    #altura do cano tanto de baixo quanto de cima
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.botton = self.height + self.GAP
    #fazendo o cano se mover em direçao ao pato
    def move(self):
        self.x -= self.VEL
    #desenhando o cano
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTON, (self.x, self.botton)) 
    #fazendo os canos colidirem so com o os pixels do pato e não com o qdrd do pato 
    def collide(self, bird):
        bird_mask = bird.get_mask() 
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)    
        botton_mask = pygame.mask.from_surface(self.PIPE_BOTTON)

        top_offset = (self.x - bird.x, self.top - round(bird.y)) 
        botton_offset = (self.x - bird.x, self.botton - round(bird.y))

        b_point = bird_mask.overlap(botton_mask, top_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point :
            return True
        
        return False

#classe que vai ficar mudando a imagem da base constantemente 
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        #duas imagens iguais, qunado chegar ao final de uma imagem a outra entra  
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH  

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH 

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))



def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255,255,255))
    win.blit(text, (10, 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    pygame.display.update()  

def main(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []
    #definindo a evolução do pato
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230,350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGTH))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:#muda o cano que os patos vão focar para o 2º cano na tela
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():       
                pipe_ind = 1
        else:#se acabar os pato o jogo fecha
            run = False
            break    


        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].botton)))

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):#define que patos que chegam longe 
                                            #mas dão uma de louco sejam punidos perdendo desenvolvimento
                if pipe.collide(bird):      
                    ge[x].fitness -= 1
                    birds.pop(x) 
                    nets.pop(x)
                    ge.pop(x)

                #checa se o pato passou do cano
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True 

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)           

            pipe.move()
        #spawna um novo cano
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600)) 

        for r in rem: 
            pipes.remove(r) 

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
               birds.pop(x)
               nets.pop(x)
               ge.pop(x)       

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)        

    

                    

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    
    p = neat.Population(config) 

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main,50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-file.txt") 
    run(config_path)  