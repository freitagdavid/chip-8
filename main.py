import pygame
import struct
import sys
import pprint
import random
pp = pprint.PrettyPrinter(indent=0).pprint
SYS = 0x0000
CLR = 0x00E0
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
JUMPI = 0xB000
RAND = 0xC000
DRAW = 0xD000
SKPR = 0xE09E
SKUP = 0xE0A1
MOVED = 0xF007
KEYD = 0xF00A
LOADD = 0xF015
LOADS = 0xF018
ADDI = 0XF01E
LDSPR = 0xF029
BCD = 0xF033
STOR = 0xF055
READ = 0xF065

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


def not_implemented(ins):
    print(f"{ins}: Not Implemented")


class Screen():
    def __init__(self):
        self.DARK = (0, 0, 0, 255)
        self.LIGHT = (255, 255, 255, 255)
        self.display_w = 1280
        self.display_h = 640
        self.w = 64
        self.h = 32
        self.draw_screen = pygame.Surface((self.w, self.h))
        self.display_screen = pygame.display.set_mode(
            (self.display_w, self.display_h))
        self.success, self.failure = pygame.init()
        self.did_update = False

    def clear_screen(self):
        self.display_screen.draw.rect(
            (0, 0, self.display_width, self.display_height))

    def xor(self, x, y):
        if x != y:
            return True
        return False

    def draw_sprite(self, x, y, sprite):
        bitmap = []
        self.did_update = False
        # print(f"x: {x}, y: {y}")
        for line in sprite:
            working = []
            for i in range(8):
                working.append(line >> 7 - i & 0b1)
            bitmap.append(working)

        for loop_y, row in enumerate(bitmap):
            for loop_x, data in enumerate(bitmap[loop_y]):
                if bitmap[loop_y][loop_x] == 0:
                    color = self.DARK
                else:
                    color = self.LIGHT
                if self.xor(self.draw_screen.get_at((x + loop_x, y + loop_y)), color):
                    self.did_update = True
                    self.draw_screen.set_at((x + loop_x, y + loop_y), color)
                # print(f"drew_x: {x + loop_x}, drew_y: {y + loop_y}")

    def update_display(self):
        main_surface = pygame.display.get_surface()
        main_surface.blit(pygame.transform.scale(
            self.draw_screen, (self.display_w, self.display_h)), (0, 0))
        pygame.display.update()


class Chip8():
    def __init__(self):
        self.opCode = 0
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.gfx = [0] * 64 * 32
        self.delay_timer = 0
        self.sound_timer = 0
        self.stack = []
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

    def next_instruction(self):
        self.pc += 2

    def stack_put(self, in_data):
        self.stack.append(in_data)

    def stack_get(self):
        return self.stack.pop()

    def fetchOpcode(self):
        self.opCode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
    
    def get_register(self, x):
        return self.V[x]

    def get_sec_byte(self, x):
        return x & 0x00FF

    def handle_sys(self):
        not_implemented("SYS()")
        # TODO Implement SYS call

    def handle_clr(self):
        # This should work hopefully
        print("CLR()")
        self.screen.clear_screen()

    def handle_rts(self):
        # TODO Maybe working?
        self.pc = self.stack_get()
        self.next_instruction()
    
    def handle_jump(self):
        # TODO Maybe working?
        x = self.opCode & 0x0FFF
        print(f"JUMP({x})")
        self.pc = x - 2

    def handle_call(self):
        # TODO Maybe working?
        x = self.opCode & 0x0FFF
        print(f"CALL({x})")
        self.stack_put(self.pc)
        self.pc = x - 2

    def handle_ske(self):
        x = self.opCode >> 8 & 0x0F
        y = self.get_sec_byte(self.opCode)
        print(f"SKE({x}, {y})")
        if self.get_register(x) == y:
            self.next_instruction()

    def handle_skne(self):
        x = self.opCode >> 8 & 0x0F
        y = self.get_sec_byte(self.opCode)
        print(f"SKNE({x}, {y})")
        if self.get_register(x) != y:
            self.pc += 2

    def handle_skre(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode >> 4 & 0x00F
        print(f"SKRE({x}, {y})")
        if self.V[x] == self.V[y]:
            self.pc += 2

    def handle_load(self):
        x = self.opCode >> 8 & 0x0F
        y = self.get_sec_byte(self.opCode)
        print(f"LOAD({x}, {y})")
        self.V[x] == y

    def handle_draw(self):
        x = self.V[self.opCode >> 8 & 0x0F]
        y = self.V[self.opCode >> 4 & 0x00F]
        n = self.opCode & 0x000F
        print(f"DRAW({x}, {y}, {n})")
        sprite = []
        for i in range(n):
            sprite.append(self.memory[self.I + i])
        self.screen.draw_sprite(x, y, sprite)
        if self.screen.did_update:
            self.V[15] = 1
        else:
            self.V[15] = 0

    def handle_loadi(self):
        x = self.opCode & 0x0FFF
        print(f"LOADI({x})")
        self.I = x




    def handle_add(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode & 0x00FF
        print(f"ADD({x}, {y})")
        self.V[x] += y

    def handle_skrne(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode >> 4 & 0x00F
        print(f"SKRNE({x}, {y})")
        if self.V[x] != self.V[y]:
            self.pc += 2

    def handle_move(self, x, y):
        print(f"MOVE({x}, {y})")
        self.V[y] = self.V[x]

    def handle_or(self, x, y):
        print(f"OR({x}, {y})")
        self.V[y] |= self.V[x]

    def handle_and(self, x, y):
        print(f"ADD({x}, {y})")
        self.V[y] &= self.V[x]

    def handle_xor(self, x, y):
        print(f"XOR({x}, {y})")
        self.V[y] ^= self.V[x]

    def handle_addr(self, x, y):
        print(f"ADDR({x}, {y})")
        working = self.V[x] + self.V[y]
        if working > 255:
            self.V[15] = 1
            working -= 255
        else:
            self.V[15] = 0
        self.V[x] = working

    def handle_sub(self, x, y):
        print(f"SUB({x}, {y})")
        temp = self.V[y] - self.V[x]
        if (temp >= -1):
            self.V[15] = 0
        else:
            self.V[15] = 1
        self.V[x] = temp

    def handle_shl(self, x, y):
        print(f"SHL({x}, {y})")
        self.V[15] = self.V[x] & 0b10000000
        self.V[x] = self.V[x] << 1

    def handle_shr(self, x, y):
        print(f"SHR({x}, {y})")
        self.V[15] = self.V[x] & 0b10000000
        self.V[x] = self.V[x] >> 1

    def handle_bcd(self, x):
        print(f"BCD({x})")
        # TODO Might be broken
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
        print(f"LOADD({x})")
        self.delay_timer = self.V[x]

    def handle_stor(self, x):
        print(f"STOR({x})")
        for i in range(x + 1):
            self.memory[self.I + i] = self.V[i]

    def handle_read(self, x):
        print(f"READ({x})")
        for i in range(x + 1):
            self.V[i] = self.V[i] = self.memory[self.I + i]

    def handle_ldspr(self, x):
        print(f"LDSPR({x})")
        working = 5 * x
        self.I = 0x50 + working

    def handle_moved(self, x):
        print(f"MOVED({x})")
        self.V[x] = self.delay_timer

    def handle_rand(self):
        x = self.opCode >> 8 & 0x0F
        y = self.opCode & 0x00FF
        print(f"RAND({x}, {y})")
        self.V[x] = random.randint(0, y)

    def handle_zero(self):
        if self.opCode == CLR:
            self.handle_clr()
        elif self.opCode == RTS:
            self.handle_rts()
        else:
            self.handle_sys()

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
        op_map[operation](x, y)

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
        op_map[operation](x)

    def decodeOpcode(self):
        operation = self.opCode & 0xF000
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


def handle_input(event):
    key_map = {
        pygame.K_1: 0,
        pygame.K_2: 1,
        pygame.K_3: 2,
        pygame.K_4: 3,
        pygame.K_q: 4,
        pygame.K_w: 5,
        pygame.K_e: 6,
        pygame.K_r: 7,
        pygame.K_a: 8,
        pygame.K_s: 9,
        pygame.K_d: 10,
        pygame.K_f: 11,
        pygame.K_z: 12,
        pygame.K_x: 13,
        pygame.K_c: 14,
        pygame.K_v: 15
    }
    try:
        print(key_map[event.key])
    except:
        print("Not a registered key")


def drawGraphics():
    pygame.display.update()


if __name__ == "__main__":
    clock = pygame.time.Clock()
    FPS = 10
    chip8 = Chip8()
    chip8.loadGame("./testGames/PONG")
    while True:
        clock.tick(FPS)
        chip8.emulateCycle()
        if chip8.V[15]:
            chip8.screen.update_display()
        chip8.setKeys()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            elif event.type == pygame.KEYDOWN:
                handle_input(event)
                # print(event.key)
