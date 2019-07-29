import pygame
import struct
import sys
import pprint
import random
pp = pprint.PrettyPrinter(indent=0).pprint
RTS = 0x00EE
JUMP = 0x1000
CALL = 0x2000
SKE = 0x3000
SKNE = 0x4000
SKRE = 0x5000
LOAD = 0x6000
ADD = 0x7000
MOVE = 0x8000
OR = 0x8001
AND = 0x8002
XOR = 0x8003
ADDR = 0x8004
SUB = 0x8005
SHR = 0x8006
SHL = 0x800E
SKRNE = 0x9000
LOADI = 0xA000
DRAW = 0xD000
BCD = 0xF033
LOADD = 0xF015
STOR = 0xF055
READ = 0xF065
LDSPR = 0xF029
MOVED = 0xF007
RAND = 0xC000
SKUP = 0xE0A1

ZERO_INSTRUCTIONS = 0x0000
EIGHT_INSTRUCTIONS = 0x8000
F_INSTRUCTIONS = 0xF000

chip8_fontset = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,
    0x20, 0x60, 0x20, 0x20, 0x70,
    0xF0, 0x10, 0xF0, 0x80, 0xF0,
    0xF0, 0x10, 0xF0, 0x10, 0xF0,
    0x90, 0x90, 0xF0, 0x10, 0x10,
    0xF0, 0x80, 0xF0, 0x10, 0xF0,
    0xF0, 0x80, 0xF0, 0x90, 0xF0,
    0xF0, 0x10, 0x20, 0x40, 0x40,
    0xF0, 0x90, 0xF0, 0x90, 0xF0,
    0xF0, 0x90, 0xF0, 0x10, 0xF0,
    0xF0, 0x90, 0xF0, 0x90, 0x90,
    0xE0, 0x90, 0xE0, 0x90, 0xE0,
    0xF0, 0x80, 0x80, 0x80, 0xF0,
    0xE0, 0x90, 0x90, 0x90, 0xE0,
    0xF0, 0x80, 0xF0, 0x80, 0xF0,
    0xF0, 0x80, 0xF0, 0x80, 0x80
]



def get_index(x, y, height):
    return x * height + y


class Screen():
    def __init__(self):
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.pixels_width = 1280
        self.pixels_height = 640
        self.success, self.falures = pygame.init()
        self.screen = pygame.display.set_mode(
            (self.pixels_width, self.pixels_height))
        self.num_width = 64
        self.num_height = 32
        self.pixel_height = self.pixels_height / self.num_height
        self.pixel_width = self.pixels_width / self.num_width
        self.pixels = [[0] * self.num_width] * self.num_height
        self.did_update = False

    def clear_screen(self):
        for x in self.num_width:
            for y in self.num_height:
                self.pixels[y][x] = 0

    def draw_sprite(self, x, y, sprite):
        bitmap = []
        did_change = 0
        for line in sprite:
            sprite_line = []
            for i in range(8):
                sprite_line.append(line >> 7 - i & 0b1)
            bitmap.append(sprite_line)
        for row in range(len(bitmap)):
            for column in range(8):
                self.pixels[x + row][y + column] = bitmap[row][column] ^ self.pixels[x + row][y + column]
        self.draw_screen(bitmap, x, y)
        return did_change

    def update(self, diff):
        self.diff(diff)

    def draw_screen(self, sprite, x, y):
        for row, row_data in enumerate(sprite):
            for column, data in enumerate(row_data):
                current_pixel = self.pixels[row + x][column + y]
                self.did_update = False
                if current_pixel ^ data != current_pixel:
                    self.did_update = True
                    self.pixels[row + x][column + y] = data
                    if data == 1:
                        self.draw_pixel(row + x, column + y, self.WHITE)
                    elif data == 0:
                        self.draw_pixel(row + x, column + y, self.BLACK)
        pygame.display.update()

    def draw_pixel(self, x, y, color):
        pygame.draw.rect(self.screen, color, (x * self.pixel_width,
                                              y * self.pixel_height, self.pixel_width, self.pixel_height))


class Chip8():
    def __init__(self):
        self.drawFlag = True
        self.opCode = 0
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.gfx = [0] * 64 * 32
        self.delay_timer = 0
        self.sound_timer = 0
        self.stack = [0] * 16
        self.sp = 0
        self.key = [0] * 16
        self.init_font()
        self.screen = Screen()

    def init_font(self):
        mem_loc = 0x50
        for byte in chip8_fontset:
            self.memory[mem_loc] = byte
            mem_loc += 1

    def loadGame(self, path):
        with open(path, 'rb') as f:
            fileContent = f.read()
            for index, value in enumerate(fileContent):
                self.memory[index + self.pc] = value

    def emulateCycle(self):
        self.fetchOpcode()
        self.decodeOpcode()
        self.updateTimers()

    def setKeys(self):
        pass

    def stack_put(self, in_data):
        self.stack[self.sp] = in_data
        self.sp += 1

    def stack_get(self):
        self.sp -= 1
        return self.stack[self.sp]

    def fetchOpcode(self):
        self.opCode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]

    def handle_CLR(self):
        self.screen.clear_screen()

    def handle_load(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode & 0x00FF
        self.V[x] == y

    def handle_draw(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode >> 4 & 0x00F
        n = self.opCode & 0x000F
        sprite = []
        for i in range(n):
            sprite.append(self.memory[self.I + i])
        self.screen.draw_sprite(x, y, sprite)
        self.drawFlag = self.screen.did_update


    def handle_loadi(self):
        self.I = self.opCode & 0x0FFF

    def handle_call(self):
        x = self.opCode & 0x0FFF
        self.stack_put(self.pc)
        self.pc = x

    def handle_jump(self):
        self.stack_put(self.pc)
        self.pc = self.opCode & 0x0FFF

    def handle_ske(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode & 0x00FF
        if self.V[x] == y:
            self.pc += 2

    def handle_skne(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode & 0x00FF
        if self.V[x] != y:
            self.pc += 2

    def handle_skre(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode >> 4 & 0x00F
        if self.V[x] == self.V[y]:
            self.pc += 2

    def handle_add(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode & 0x00FF
        self.V[x] += y

    def handle_skrne(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode >> 4 & 0x00F
        if self.V[x] != self.V[y]:
            self.pc += 2

    def handle_move(self, x, y):
        self.V[y] = self.V[x]

    def handle_or(self, x, y):
        self.V[y] |= self.V[x]

    def handle_and(self, x, y):
        self.V[y] &= self.V[x]

    def handle_xor(self, x, y):
        self.V[y] ^= self.V[x]

    def handle_addr(self, x, y):
        working = self.V[x] + self.V[y]
        if working > 255:
            self.V[15] = 1
            working -= 255
        else:
            self.V[15] = 0
        self.V[x] = working

    def handle_sub(self, x, y):
        temp = self.V[y] - self.V[x]
        if (temp >= -1):
            self.V[15] = 0
        else:
            self.V[15] = 1    
        self.V[x] = temp

    def handle_shl(self, x, y):
        self.V[15] = self.V[x] & 0b10000000
        self.V[x] = self.V[x] << 1

    def handle_shr(self, x, y):
        self.V[15] = self.V[x] & 0b10000000
        self.V[x] = self.V[x] >> 1
    
    def handle_bcd(self, x):
        # TODO Might be broken
        print("bcd")
        num = self.V[x]
        nums = []
        while num != 0:
            if num % 10 > 0:
                nums.append(num % 10)
            else:
                num //= 10
                nums.append(num)
        if len(nums) < 1:
            nums.append(0)
        for index, item in enumerate(nums):
            self.memory[self.I + index] = item

    def handle_loadd(self, x):
        self.delay_timer = self.V[x]

    def handle_stor(self, x):
        for i in range(x + 1):
            self.memory[self.I + i] = self.V[i]

    def handle_read(self, x):
        for i in range(x + 1):
            self.V[i] = self.V[i] = self.memory[self.I + i]
    
    def handle_ldspr(self, x):
        working = 5 * x
        self.I = 0x50 + working

    def handle_moved(self, x):
        self.V[x] = self.delay_timer

    def handle_rand(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode & 0x00FF
        self.V[x] = random.randint(0, y)

    def handle_zero(self):
        if self.opCode == RTS:
            self.pc = self.stack_get()

    def handle_eight(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode >> 4 & 0x00F
        operation = self.opCode & 0xF00F
        op_map = {
            MOVE: self.handle_move,
            OR: self.handle_or,
            AND: self.handle_and,
            XOR: self.handle_xor,
            ADDR: self.handle_addr,
            SUB: self.handle_sub,
            SHL: self.handle_shl,
            SHR: self.handle_shr
        }

        try:
            op_map[operation](x, y)
        except:
            print(f"{hex(self.opCode)} not implemented.")

    def handle_f(self):
        operation = self.opCode & 0xF0FF
        x = self.opCode >> 8 & 0x0F
        op_map = {
            BCD: self.handle_bcd,
            LOADD: self.handle_loadd,
            STOR: self.handle_stor,
            READ: self.handle_read,
            LDSPR: self.handle_ldspr,
            MOVED: self.handle_moved
        }
        try:
            op_map[operation](x)
        except:
            print(f"{hex(self.opCode)} not implemented.")
            

    def decodeOpcode(self):
        operation = self.opCode & 0xF000
        # print(f"Op: {hex(self.opCode)}")
        # print(f"{hex(self.opCode >> 12)}, {hex(self.opCode >> 8 & 0x0F)}, {hex(self.opCode >> 4 & 0x00F)}, {hex(self.opCode & 0x000F)}")
        op_map = {
            ZERO_INSTRUCTIONS: self.handle_zero,
            EIGHT_INSTRUCTIONS: self.handle_eight,
            F_INSTRUCTIONS: self.handle_f,
            LOAD: self.handle_load,
            DRAW: self.handle_draw,
            LOADI: self.handle_loadi,
            CALL: self.handle_call,
            JUMP: self.handle_jump,
            SKE: self.handle_ske,
            SKNE: self.handle_skne,
            SKRE: self.handle_skre,
            ADD: self.handle_add,
            SKRNE: self.handle_skrne,
            RAND: self.handle_rand
        }

        try:
            op_map[operation]()
        except:
            print(f"{hex(self.opCode)} not implemented.")
        self.pc += 2

    def updateTimers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1


def setupInput():
    pass


def drawGraphics():
    pygame.display.update()


if __name__ == "__main__":
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    clock = pygame.time.Clock()
    FPS = 60
    chip8 = Chip8()
    chip8.loadGame("./testGames/PONG")
    while True:
        clock.tick(FPS)
        chip8.emulateCycle()
        if chip8.drawFlag:
            drawGraphics()
        chip8.setKeys()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            elif event.type == pygame.KEYDOWN:
                print("test")
    # while True:
    #     chip8.emulateCycle()
    #     if chip8.drawFlag:
    #         drawGraphics()
    #     chip8.setKeys()
