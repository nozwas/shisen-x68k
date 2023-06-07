# -*- coding: shift_jis -*-
# shisen: xbasip sample program
# nozwas <https://github.com/nozwas>

r"""shisen.py
    puzzle game SHISEN-SHO
"""
from xbasip import *
from random import randrange, seed
from uctypes import addressof, bytearray_at
from binascii import unhexlify
from time import time
from usys import argv

TILE_W, TILE_H = 24, 48
TILE_SZ = TILE_W * TILE_H * 2
SCREEN_W, SCREEN_H = 512, 512
MARGIN = 2
GAME_CLEAR, GAME_QUIT = 1, 2
STAGE_DATA = ((18, 9, 68040), (27, 12, 8801), (34, 17, 7205), [34, 17, None])
EDGE = -1
C_BG = rgb(0, 16, 16)
K_RUP, K_RDN, K_INS, K_DEL = ord(" "), ord("u"), ord(" "), ord("u")
K_UP, K_LEFT, K_RIGHT, K_DOWN = ord("8"), ord("4"), ord("6"), ord("2")
K_CLR, K_HELP, K_HOME, K_UNDO = ord("u"), ord("u"), ord(" "), ord("u")
K_ESCAPE, K_RETURN, K_SPACE, K_BACKSPACE  = 0x1b, 0x0d, 0x20, 0x08
K_s, K_q, K_u, K_S, K_Q, K_U = map(lambda i: ord(i), "squSQU")

def draw_tile(x, y, n):
    x, y = x * TILE_W + ofs_x, y * TILE_H + ofs_y
    put(x, y, x + TILE_W - 1, y + TILE_H - 1,
        bytearray_at(addressof(tile) + TILE_SZ * n, TILE_SZ))

def erase_tile(x, y):
    x, y = x * TILE_W + ofs_x, y * TILE_H + ofs_y
    fill(x, y, x + TILE_W - 1, y + TILE_H - 1, C_BG)

def marker_on(x, y):
    x, y = x * TILE_W + ofs_x + 16, y * TILE_H + ofs_y + 16
    sp_set(4, x - 1, y - 2, sp_code(2, 0, 0, 2), 3)
    sp_set(5, x + 8, y - 2, sp_code(2, 1, 0, 2), 3)
    sp_set(6, x - 1, y + 32, sp_code(2, 0, 1, 2), 3)
    sp_set(7, x + 8, y + 32, sp_code(2, 1, 1, 2), 3)

def marker_off():
    for i in range(4):
        sp_set(i + 4, 0, 0, 2, 3)

def pointer_on(x, y):
    x, y = x * TILE_W + ofs_x + 16, y * TILE_H + ofs_y + 16
    sp_set(0, x + 4, y - 6, sp_code(0, 0, 0, 2), 3)
    sp_set(1, x + 4, y + 32 + 4 , sp_code(0, 0, 1, 2), 3)
    sp_set(2, x - 4, y + 15, sp_code(1, 0, 0, 2), 3)
    sp_set(3, x + 11, y + 15, sp_code(1, 1, 0, 2), 3)
    
def pointer_off():
    for i in range(4):
        sp_set(i, 0, 0, 0, 3)

def connected_h(x1, y1, x2, y2):
    small1 = large1 = x1
    while field[y1][small1 - 1] is None:
        small1 -= 1
    while field[y1][large1 + 1] is None:
        large1 += 1
    small2 = large2 = x2
    while field[y2][small2 - 1] is None:
        small2 -= 1
    while field[y2][large2 + 1] is None:
        large2 += 1
    connected = False
    for x in range(max(small1, small2), min(large1, large2) + 1):
        connected = True
        for y in range(min(y1, y2) + 1, max(y1, y2)):
            connected &= field[y][x] is None
        if connected:
            break
    return connected

def connected_v(x1, y1, x2, y2):
    small1 = large1 = y1
    while field[small1 - 1][x1] is None:
        small1 -= 1
    while field[large1 + 1][x1] is None:
        large1 += 1
    small2 = large2 = y2
    while field[small2 - 1][x2] is None:
        small2 -= 1
    while field[large2 + 1][x2] is None:
        large2 += 1
    connected = False
    for y in range(max(small1, small2), min(large1, large2) + 1):
        connected = True
        for x in range(min(x1, x2) + 1, max(x1, x2)):
            connected &= field[y][x] is None
        if connected:
            break
    return connected

def connected(x, y, sel_x, sel_y):
    return connected_h(x, y, sel_x, sel_y) or connected_v(x, y, sel_x, sel_y)

def repeat_BGM():
    if m_stat() == 0:
        m_play()

def game_play(stage):
    new_stage(stage)
    picked = 0
    sel_tile = None
    xx = yy = cx = cy = MARGIN
    undo = []
    mouse(4)
    mouse(1)
    setmspos(50, 50)
    keyflush()
    k, s, b, m = 0, stick(1), strig(1), msstat()
    s_delay = 0

    while True:
        pointer_on(cx, cy)
        pre_k, k = k, inkey0()
        pre_s, s = s, stick(1) # x, y = 10key
        pre_b, b = b, strig(1) # a, b = 1, 2
        pre_m, m = m, msstat() # l, r = m[2], m[3]
        p = mspos()            # x, y = p[0], p[1]
        if k != 0:
            keyflush()
        if s_delay == 0:
            if s != 0 and pre_s == 0:
                s_delay = 10
        elif s == 0:
            s_delay = 0
        else:
            s_delay -= 1
            if s_delay == 0:
                s_delay = 2
                pre_s = 0
        if k in (K_q, K_Q, K_ESCAPE):
            return GAME_QUIT
        elif k == K_LEFT or s in (1, 4, 7) and pre_s == 0:
            cx = (cx - 1 - MARGIN) % columns + MARGIN
        elif k == K_RIGHT or s in (3, 6, 9) and pre_s == 0:
            cx = (cx + 1 - MARGIN) % columns + MARGIN
        elif k == K_UP or s in (7, 8, 9) and pre_s == 0:
            cy = (cy - 1 - MARGIN) % rows + MARGIN
        elif k == K_DOWN or s in (1, 2, 3) and pre_s == 0:
            cy = (cy + 1 - MARGIN) % rows + MARGIN
        elif k in (K_SPACE, K_RETURN) or b == 1 and pre_b == 0:
            xx, yy = cx, cy
        elif m[2] and not pre_m[2]:
            xx = max(1, min(columns + MARGIN, (p[0] - ofs_x) // TILE_W))
            yy = max(1, min(rows + MARGIN, (p[1] - ofs_y) // TILE_H))
        if not m[2] and pre_m[2] or k in (K_SPACE, K_RETURN) \
           or b == 1 and pre_b == 0:
            if sel_tile is None:
                if field[yy][xx] is not None:
                    sel_tile = field[yy][xx]
                    sel_x, sel_y = cx, cy = xx, yy                    
                    marker_on(xx, yy)
            elif field[yy][xx] == sel_tile:
                if xx == sel_x and yy == sel_y:
                    marker_off()
                    sel_tile = None
                elif connected(xx, yy, sel_x, sel_y):
                    marker_off()
                    erase_tile(xx, yy)
                    erase_tile(sel_x, sel_y)
                    field[yy][xx] = field[sel_y][sel_x] = None
                    undo.append((sel_tile, xx, yy, sel_x, sel_y))
                    sel_tile = None
                    cx, cy = xx, yy
                    picked += 2
                    if picked == tiletypes * 4:
                        return GAME_CLEAR
        elif not m[3] and pre_m[3] or k in (K_BACKSPACE, K_u, K_U) \
             or b == 0 and pre_b == 2:
            if sel_tile is not None:
                marker_off()
                sel_tile = None
            elif len(undo) > 0:
                tile, x1, y1, x2, y2 = undo.pop()
                picked -= 2
                draw_tile(x1, y1, tile)
                draw_tile(x2, y2, tile)
                field[y1][x1] = field[y2][x2] = tile
        repeat_BGM()
        x68k.vsync()

def new_stage(stage):
    global field, tiletypes, columns, rows, ofs_x, ofs_y
    cls()
    fill(0, 0, SCREEN_W - 1, SCREEN_H - 1, C_BG)
    tiletypes = STAGE_DATA[stage][0]
    columns = STAGE_DATA[stage][1]
    rows = tiletypes * 4 // columns
    ofs_x = (SCREEN_W - TILE_W * (columns + MARGIN * 2)) // 2
    ofs_y = (SCREEN_H - TILE_H * (rows + MARGIN * 2)) // 2
    seed(random_seed if stage == 3 else STAGE_DATA[stage][2])
    field = [[None] * (columns + MARGIN * 2) for y in range(rows + MARGIN * 2)]
    field[0] = field[rows + MARGIN * 2 - 1] = [EDGE] * (columns + MARGIN * 2)
    t = [4] * tiletypes
    x_list = list(range(MARGIN, columns + MARGIN))
    for i in range(len(x_list)):
        j = randrange(len(x_list))
        x_list[i], x_list[j] = x_list[j], x_list[i]
    y_list = list(range(MARGIN, rows + MARGIN))
    for i in range(len(y_list)):
        j = randrange(len(y_list))
        y_list[i], y_list[j] = y_list[j], y_list[i]
    for y in y_list:
        field[y][0] = field[y][columns + MARGIN * 2 - 1] = EDGE
        for x in x_list:
            i = randrange(tiletypes)
            while t[i] == 0:
                i = (i + 1) % tiletypes
            t[i] -= 1
            field[y][x] = i
            draw_tile(x, y, i)
    color(2 + 4)
    locate(11, 1)
    print("*** Shisen-sho for MicroPython X68000 ***")
    color(3)
    locate(5, 30)
    print("選択:[↑↓←→] 決定:[RET/SPC] 取消:[BS/U] 終了:[ESC/Q]")
    if stage == 3:
        locate(55, 0)
        print(f"seed:{random_seed:04}")
    
def draw_GRP(g, line_color = 0):
    i, x1, y1  = 0, 0, 0
    while i < len(GRP[g]):
        p = GRP[g][i]
        if type(p) is str:
            if p == 'mv':
                x1, y1 = GRP[g][i + 1], GRP[g][i + 2]
                i += 2
            elif p == 'pa':
                paint(GRP[g][i + 1], GRP[g][i + 2], GRP[g][i + 3])
                i += 3
        else:
            if x1 is not None:
                line(x1, y1, GRP[g][i], GRP[g][i + 1], line_color)
                x1 = None
            else:
                line_to(GRP[g][i], GRP[g][i + 1], line_color)
            i += 1
        i += 1
      
def opening():
    global ofs_x, ofs_y
    marker_off()
    pointer_off()
    cls()
    fill(0, 0, SCREEN_W - 1, SCREEN_H - 1, C_BG)
    draw_GRP(0)
    ofs_x = (SCREEN_W - TILE_W * (17 + MARGIN * 2)) // 2
    ofs_y = (SCREEN_H - TILE_H * (8 + MARGIN * 2)) // 2
    for i in range(13):
        draw_tile(i + 4, 9, (0,8,9,17,18,26,27,28,29,30,31,32,33)[i])
    color(2 + 4)
    locate(11, 3)
    print("*** Shisen-sho for MicroPython X68000 ***")
    color(3)
    locate (25, 19)
    print("レベル１( 9×8)")
    locate (25, 20)
    print("レベル２(12×9)")
    locate (25, 21)
    print("レベル３(17×8)")
    locate (25, 22)
    print("ランダム(17×8)")
    locate (25, 23)
    print("ゲーム終了")
    color(3 + 4)
    locate(25, 29)
    print("(C)2023 nozwas")
    color(1)
    locate(22, 30)
    print("BGM:composed by Awed")
    mouse(4)
    mouse(1)
    setmspos(50, 50)
    keyflush()
    k, s, b, m = 0, stick(1), strig(1), msstat()
    sel = 0

    while True:
        sp_set(1, 204, 320 + sel * 16, sp_code(1, 0, 0, 2), 3)
        pre_k, k = k, inkey0()
        pre_s, s = s, stick(1) # x, y = 10key
        pre_b, b = b, strig(1) # a, b = 1, 2
        pre_m, m = m, msstat() # l, r = m[2], m[3]
        p = mspos()            # x, y = p[0], p[1]
        if k != 0:
            keyflush()
        if k in (K_q, K_Q, K_ESCAPE):
            sel = 4
            break
        elif k == K_UP or s == 8 and pre_s == 0:
            sel = (sel - 1) % 5
        elif k == K_DOWN or s == 2 and pre_s == 0:
            sel = (sel + 1) % 5
        elif m[2] and not pre_m[2]:
            if p[0] in range(200, 335) and p[1] in range(304, 383):
                sel = (p[1] - 304) // 16
        if not m[2] and pre_m[2] or k in (K_SPACE, K_RETURN) \
            or b == 1 and pre_b == 0:
            break
        repeat_BGM()
    sp_set(1, 0, 0, 0, 3)
    return sel

def game_clear():
    pointer_off()
    marker_off()
    draw_GRP(1)
    draw_GRP(2)
    keyflush()
    color(3)
    locate(5, 30)
    print(" " * 55)
    locate(20, 30)
    print("何かキーを押してください")
    inkey()
    
def main():
    global tile, random_seed
    screen(1, 3, 1, 1)
    key_off()
    cursor_off()
    tpalet(12, rgb(31, 0, 31)) # mouse color
    tpalet(4, 0x0001)
    sp_init()
    sp_clr()
    for i in range(len(PAT)):
        sp_def(i, unhexlify(PAT[i]), 1)
    sp_color(1, rgb(0, 31, 31), 2)
    sp_color(2, rgb(31, 16, 8), 2)
    sp_color(3, 0x0001, 2)
    sp_disp(1)
    sp_on(0, 7)
    priority(1, 0, 2)
    with open("tile.dat", "rb") as f:
        tile = f.read(34 * TILE_SZ)
    try:
        m_init()
    except:
        end("musicモジュールを使用するには、opmdrv3もしくは"
            "zmusic2をシステムに組み込んでおく必要があります。")
    for i in range(2):
        m_vset(i + 1, unhexlify(VO[i]))
        m_alloc(i + 1, 1000)
    for i in range(2):
        m_assign(i + 1, i + 1)
        m_trk(i + 1, MML[i])
        
    stage = 0
    random_seed = None
    if len(argv) >= 2:
        stage = 3
        random_seed = int(argv[1])

    for i, code in enumerate((K_RUP, K_RDN, K_INS, K_DEL,
                              K_UP, K_LEFT, K_RIGHT, K_DOWN,
                              K_CLR, K_HELP, K_HOME, K_UNDO), start=21):
        key(i, chr(code).encode())
    
    while True:
        if stage != 3:
            stage = opening()
            if stage == 4:
                break
            random_seed = (time() % 10000) if stage == 3 else None                 
        if game_play(stage) == GAME_CLEAR:
            game_clear()
        stage = 0
        repeat_BGM()

    width(96)
    color(3)
    mouse(2)
    m_stop()
    if random_seed is not None:
        end(f"seed:{random_seed:04}")
    else:
        end()

PCM = unhexlify("7077fd0f" + "3481bd19" * 127)

VO = ("380f0200c8000000000300"
      "1a080507021c03030700001d040505011f0304010000"
      "1c040206022003010700001d09030301000301030001",
      "3a0f020096000000000300"
      "1f0d01040f2001000700001f0b010a0f370104050000"
      "1f0b010a0f1d00000200001f0b01080f000100030001")

MML = ("t178 @1 o4 g2.a4<c2d4f4c1d1>g2.a4<c2>a4<c4>g1&g1<c2.d4f2d4f4c1d1>"
       "g2.a4g2.a4<c2>a4g4f1",
       "@2 o2 f4<f4>f4<f4>f4<f4>f4<f4>f4<f4>f4<f4>f4<f4c4>f4"
       "g4<g4>g4<g4>g4<g4>g4<g4>g4<g4>g4a4<c4d4c4>a4"
       "f4<f4>f4<f4>f4<f4>f4<f4>f4<f4>f4<f4>f4<f4c4>f4"
       "g4<g4>g4<g4>g4a4<c4c4>a4<c4>g4a4f4<f4>f2")

PAT = (("3333333333333330322222222222223003222222222223000032222222223000"
        "0003222222230000000032222230000000000322230000000000003230000000"
        "0000000300000000" + "0" * 16 * 7),
       ("3300000000000000323000000000000032230000000000003222300000000000"
        "3222230000000000322222300000000032222223000000003222222230000000"
        "3222222230000000322222230000000032222230000000003222230000000000"
        "3222300000000000322300000000000032300000000000003300000000000000"),
       ("3333333333000000311111111300000031111111130000003111111113000000"
        "3113333333000000" + "3113000000000000" * 10 + "3333000000000000"))

GRP = (('mv', 74, 177, 73, 177, 71, 183, 77, 215, 77, 216, 85, 203,
        91, 190, 93, 183, 83, 180, 76, 177, 74, 177, 'mv', 137, 170, 124,
        172, 122, 173, 125, 178, 125, 191, 127, 194, 139, 196, 144, 203, 122,
        216, 111, 221, 110, 219, 120, 207, 112, 186, 113, 176, 109, 177, 101,
        181, 103, 194, 100, 206, 94, 211, 88, 217, 82, 218, 78, 221, 81, 234,
        86, 235, 112, 231, 144, 231, 149, 206, 152, 179, 145, 171, 137, 170,
        'mv', 131, 157, 155, 166, 165, 174, 170, 186, 169, 195, 160, 230,
        157, 243, 155, 249, 137, 245, 121, 243, 91, 248, 74, 242, 64, 212,
        62, 167, 64, 167, 68, 173, 85, 165, 104, 161, 131, 157, 'mv', 214,
        149, 224, 159, 232, 169, 235, 186, 233, 208, 227, 222, 222, 233, 211,
        241, 206, 233, 204, 221, 204, 218, 207, 219, 210, 222, 219, 203, 221,
        181, 219, 166, 215, 154, 213, 150, 214, 149, 'mv', 255, 131, 256,
        131, 262, 145, 262, 177, 264, 173, 272, 156, 273, 151, 272, 159, 266,
        184, 260, 215, 258, 220, 252, 221, 247, 215, 247, 200, 249, 176, 248,
        149, 246, 137, 251, 132, 255, 131, 'mv', 288, 116, 290, 116, 296,
        120, 303, 133, 301, 173, 303, 229, 301, 259, 295, 289, 292, 291, 285,
        216, 287, 134, 284, 130, 281, 127, 285, 118, 288, 116, 'mv', 400,
        115, 407, 120, 411, 135, 411, 152, 411, 158, 419, 146, 426, 141, 428,
        139, 422, 134, 422, 129, 429, 127, 435, 126, 443, 133, 446, 147, 444,
        152, 433, 147, 420, 146, 428, 153, 427, 161, 422, 169, 400, 196, 396,
        201, 395, 216, 395, 219, 405, 211, 412, 215, 412, 220, 401, 224, 394,
        225, 392, 235, 393, 236, 399, 235, 409, 236, 410, 241, 402, 257, 400,
        261, 410, 262, 416, 265, 420, 268, 422, 265, 421, 197, 417, 196, 400,
        209, 399, 209, 409, 191, 418, 184, 424, 186, 433, 212, 436, 273, 433,
        289, 424, 294, 416, 284, 414, 279, 400, 278, 391, 274, 385, 276, 379,
        264, 385, 213, 385, 211, 354, 243, 342, 252, 336, 241, 339, 228, 344,
        223, 347, 231, 376, 200, 386, 189, 400, 171, 402, 163, 394, 161, 388,
        151, 381, 151, 375, 160, 368, 167, 357, 152, 357, 143, 366, 140, 371,
        141, 377, 142, 384, 141, 391, 139, 395, 141, 392, 144, 397, 147, 397,
        138, 390, 121, 400, 115, 'mv', 391, 241, 391, 259, 393, 262, 399, 250,
        399, 246, 394, 244,391, 241, 'pa', 66, 179, 0x07c0, 'pa', 222, 163,
        0x07c0, 'pa', 256, 145, 0x07c0, 'pa', 292, 127, 0x07c0, 'pa', 401,
        124, 0x07c0, 'pa', 435, 137, 0x07c0),
       ('mv', 279, 264, 287, 261, 293, 259, 297, 257, 298, 254, 315, 183,
        332, 110, 330, 102, 324, 95, 322, 81, 324, 71, 329, 65, 332, 62, 332,
        55, 332, 51, 334, 48, 336, 46, 340, 49, 341, 52, 341, 57, 343, 65,
        347, 69, 349, 76, 350, 82, 349, 90, 344, 100, 342, 110, 351, 163,
        357, 197, 364, 235, 365, 239, 369, 242, 371, 240, 381, 224, 394, 206,
        398, 201, 404, 206, 399, 212, 386, 232, 375, 248, 374, 255, 379, 259,
        382, 259, 396, 249, 408, 237, 417, 223, 421, 216, 426, 216, 427, 216,
        431, 218, 431, 222, 430, 248, 427, 274, 422, 300, 414, 322, 397, 349,
        393, 348, 380, 318, 379, 310, 378, 300, 377, 290, 368, 282, 355, 286,
        349, 299, 351, 317, 358, 324, 361, 328, 367, 328, 371, 330, 381, 359,
        380, 364, 369, 372, 365, 369, 343, 322, 343, 313, 344, 297, 340, 286,
        333, 281, 322, 283, 316, 293, 314, 308, 318, 320, 328, 326, 334, 331,
        339, 344, 349, 377, 347, 381, 331, 386, 327, 383, 317, 354, 308, 328,
        307, 326, 306, 318, 307, 313, 308, 298, 304, 286, 296, 280, 287, 282,
        281, 292, 279, 306, 284, 320, 291, 326, 295, 330, 304, 355, 307, 376,
        309, 388, 306, 389, 284, 388, 281, 385, 275, 347, 270, 323, 272, 315,
        275, 298, 269, 283, 260, 278, 250, 283, 244, 297, 245, 306, 247, 314,
        252, 321, 256, 324, 259, 328, 262, 342, 262, 361, 262, 382, 260, 385,
        250, 382, 238, 380, 236, 376, 235, 343, 234, 306, 233, 287, 234, 280,
        242, 259, 244, 255, 247, 255, 274, 264, 279, 264, 'mv', 332, 171,
        331, 181, 326, 242, 326, 247, 330, 248, 333, 247, 339, 243, 337, 246,
        339, 239, 340, 235, 338, 191, 337, 145, 336, 124, 335, 124, 332, 171,
        'mv', 343, 256, 339, 257, 332, 259, 307, 268, 319, 270, 350, 268,
        365, 265, 367, 263, 367, 259, 364, 253, 360, 252, 343, 256, 'mv',
        355, 240, 356, 238, 356, 234, 351, 197, 344, 146, 341, 132, 341, 132,
        341, 137, 343, 177, 347, 233, 348, 241, 352, 242, 355, 240, 'mv',
        312, 227, 308, 249, 308, 254, 315, 252, 317, 247, 322, 201, 329, 149,
        329, 146, 328, 145, 312, 227, 'mv', 271, 351, 280, 396, 287, 437,
        288, 443, 286, 453, 278, 461, 273, 457, 270, 426, 268, 404, 266, 384,
        266, 357, 266, 346, 261, 322, 260, 318, 257, 315, 250, 307, 252, 293,
        258, 286, 265, 290, 269, 298, 267, 309, 265, 316, 266, 321, 271, 351,
        'mv', 304, 329, 316, 362, 332, 407, 339, 427, 340, 434, 340, 439,
        336, 448, 332, 451, 329, 445, 320, 418, 315, 402, 313, 392, 310, 370,
        308, 356, 302, 339, 297, 323, 295, 320, 291, 316, 286, 312, 284, 303,
        286, 296, 290, 290, 296, 288, 300, 292, 303, 300, 303, 307, 302, 307,
        300, 317, 303, 326, 304, 329, 'mv', 382, 421, 380, 427, 378, 431,
        374, 433, 372, 430, 357, 392, 350, 365, 336, 327, 334, 324, 328, 318,
        322, 314, 320, 306, 321, 299, 324, 291, 330, 289, 335, 292, 339, 301,
        338, 310, 338, 319, 351, 348, 367, 382, 378, 408, 382, 421, 'mv',
        359, 317, 355, 309, 356, 298, 359, 292, 367, 291, 372, 296, 374, 307,
        375, 316, 388, 345, 404, 379, 413, 397, 414, 401, 414, 408, 412, 413,
        406, 412, 392, 383, 390, 376, 387, 365, 383, 349, 377, 332, 370, 320,
        367, 319, 359, 317, 'mv', 459, 139, 458, 137, 456, 134, 452, 134,
        450, 137, 447, 134, 448, 127, 449, 124, 445, 117, 441, 114, 438, 113,
        435, 108, 434, 103, 436, 97, 440, 93, 444, 94, 450, 95, 466, 90, 469,
        87, 474, 83, 480, 86, 482, 93, 479, 102, 476, 108, 474, 123, 472,
        135, 473, 139, 474, 147, 472, 153, 471, 155, 468, 156, 464, 156, 464,
        155, 462, 153, 460, 149, 460, 141, 459, 139, 'mv', 468, 111, 462,
        119, 458, 127, 462, 133, 466, 136, 468, 131, 470, 121, 472, 111, 472,
        106, 468, 111, 'mv', 456, 115, 461, 107, 466, 98, 464, 98, 457, 100,
        450, 102, 448, 105, 448, 111, 451, 115, 456, 115, 'mv', 441, 188,
        441, 195, 438, 202, 434, 207, 428, 211, 420, 209, 415, 204, 411, 197,
        410, 187, 412, 174, 417, 168, 421, 164, 425, 163, 429, 163, 434, 167,
        438, 172, 440, 178, 441, 188, 'mv', 425, 196, 430, 192, 431, 186,
        429, 181, 425, 179, 422, 182, 420, 186, 421, 193, 425, 196, 'mv',
        425, 138, 425, 140, 423, 143, 419, 149, 417, 152, 416, 158, 415, 161,
        413, 165, 412, 160, 413, 158, 413, 150, 410, 142, 406, 138, 404, 137,
        409, 131, 413, 126, 419, 124, 423, 126, 425, 129, 426, 134, 425, 138,
        'mv', 401, 145, 406, 146, 408, 152, 409, 158, 408, 165, 409, 170,
        408, 175, 405, 171, 403, 170, 398, 169, 396, 170, 395, 167, 394, 163,
        394, 159, 395, 156, 396, 152, 397, 148, 399, 146, 401, 145, 'mv',
        423, 159, 421, 158, 421, 155, 423, 153, 424, 152, 426, 148, 427, 147,
        430, 140, 430, 134, 431, 128, 434, 128, 437, 130, 443, 136, 444, 139,
        442, 146, 437, 149, 435, 149, 433, 149, 433, 149, 430, 152, 430, 152,
        428, 155, 426, 158, 423, 159, 'mv', 454, 163, 453, 169, 450, 172,
        446, 168, 442, 161, 436, 161, 433, 160, 432, 157, 434, 156, 436, 156,
        439, 155, 443, 154, 446, 149, 447, 147, 449, 147, 451, 150, 451, 150,
        454, 159, 454, 163, 'mv', 402, 176, 405, 183, 406, 191, 407, 198,
        404, 197, 400, 193, 397, 186, 397, 178, 400, 175, 402, 176, 'mv',
        444, 180, 442, 175, 440, 167, 442, 168, 444, 172, 449, 178, 454, 178,
        453, 183, 451, 190, 449, 192, 445, 193, 445, 193, 445, 185, 444, 180,
        'pa', 336, 83, 0x07c0, 'pa', 415, 178, 0x07c0, 'pa', 399, 184,
        0x07c0, 'pa', 402, 156, 0x07c0, 'pa', 416, 132, 0x07c0, 'pa', 436,
        138, 0x07c0, 'pa', 446, 156, 0x07c0, 'pa', 449, 184, 0x07c0, 'pa',
        442, 101, 0x07c0, 'pa', 260, 301, 0x07c0, 'pa', 294, 303, 0x07c0,
        'pa', 327, 304, 0x07c0, 'pa', 361, 305, 0x07c0),
       ('mv', 205, 258, 212, 258, 212, 267, 205, 267, 205, 258, 'mv', 163,
        240, 160, 253, 166, 253, 164, 247, 163, 240, 'mv', 187, 238, 187,
        245, 190, 245, 192, 245, 193, 244, 194, 242, 193, 239, 190, 238, 188,
        238, 187, 238, 'mv', 205, 231, 212, 231, 212, 239, 211, 256, 207,
        256, 205, 239, 205, 231, 'mv', 179, 231, 192, 231, 197, 232, 200,
        235, 201, 241, 200, 246, 198, 250, 195, 251, 197, 252, 198, 254, 199,
        257, 203, 267, 195, 267, 191, 256, 189, 253, 187, 252, 187, 252, 187,
        267, 179, 267, 179, 249, 179, 231, 'mv', 159, 231, 167, 231, 176,
        267, 169, 267, 167, 261, 159, 261, 158, 267, 150, 267, 154, 249, 159,
        231, 'mv', 128, 231, 148, 231, 148, 238, 135, 238, 135, 244, 147,
        244, 147, 252, 135, 252, 135, 259, 148, 259, 148, 267, 128, 267, 128,
        248, 128, 231, 'mv', 105, 231, 112, 231, 112, 258, 124, 258, 124,
        267, 105, 267, 105, 249, 105, 231, 'mv', 90, 230, 97, 233, 101, 241,
        94, 244, 93, 241, 92, 239, 90, 238, 86, 242, 85, 249, 86, 257, 90,
        259, 93, 258, 94, 252, 101, 255, 99, 262, 95, 266, 90, 268, 83, 266,
        79, 260, 77, 249, 80, 237, 84, 231, 90, 230, 'mv', 108, 172, 105,
        186, 110, 186, 109, 180, 108, 172, 'mv', 151, 163, 171, 163, 171,
        171, 159, 171, 159, 176, 171, 176, 171, 184, 159, 184, 159, 191, 172,
        191, 172, 199, 151, 199, 151, 180, 151, 163, 'mv', 104, 163, 112,
        163, 121, 199, 113, 199, 112, 193, 103, 193, 102, 199, 94, 199, 99,
        179, 104, 163, 'mv', 73, 163, 96, 163, 96, 172, 88, 172, 88, 199,
        80, 199, 80, 172, 73, 172, 73, 167, 73, 163, 'mv', 135, 162, 141,
        163, 145, 167, 147, 173, 139, 175, 138, 171, 135, 170, 131, 173, 130,
        181, 131, 190, 135, 192, 138, 192, 140, 190, 140, 186, 135, 186, 135,
        179, 147, 179, 147, 194, 141, 199, 135, 200, 128, 198, 124, 191, 122,
        181, 124, 171, 129, 164, 135, 162, 'mv', 60, 162, 67, 165, 70, 173,
        63, 174, 62, 170, 59, 169, 57, 170, 57, 172, 57, 173, 60, 175, 67,
        178, 70, 182, 71, 188, 69, 194, 66, 199, 60, 200, 51, 197, 49, 187,
        56, 187, 57, 191, 60, 193, 63, 192, 63, 189, 63, 187, 59, 184, 52,
        180, 50, 173, 51, 168, 54, 164, 60, 162, 'pa', 54, 167, 0x003e, 'pa',
        85, 167, 0x003e, 'pa', 109, 167, 0x003e, 'pa', 137, 167, 0x003e,
        'pa', 155, 167, 0x003e, 'pa', 91, 235, 0x003e, 'pa', 109, 237,
        0x003e, 'pa', 133, 237, 0x003e, 'pa', 161, 237, 0x003e, 'pa', 181,
        237, 0x003e, 'pa', 210, 237, 0x003e, 'pa', 208, 261, 0x003e))

main()
