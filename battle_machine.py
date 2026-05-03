# Pyxelライブラリ（レトロゲームエンジン）をインポートします
import pyxel
# ランダムな数値を生成するためのライブラリをインポートします
import random
# 数学的な計算（サイン波など）を行うためのライブラリをインポートします
import math
# 列挙型（Enum）を作成するための機能をインポートします
from enum import Enum, auto

# === CONFIG (ゲームの設定定数) ===
# 画面の横幅を160ピクセルに設定します
SCREEN_WIDTH = 160
# 画面の縦幅を120ピクセルに設定します
SCREEN_HEIGHT = 120
# キャラクターやアイテムにかかる重力加速度を設定します
GRAVITY = 0.8
# プレイヤーの最大体力を設定します
PLAYER_MAX_HP = 10
# ダメージを受けた後の無敵時間の長さ（フレーム数）を設定します
INVINCIBLE_DURATION = 40
# ボス戦が始まるX座標の位置を設定します
BOSS_START_X = 1200
# ダッシュ時の速度倍率を設定します
DASH_SPEED_MULTIPLIER = 2.0

# 音声を再生するかどうかの設定
ENABLE_SOUND = True

# 安全に効果音を再生するためのヘルパー関数
def safe_play(ch, snd):
    if ENABLE_SOUND:
        pyxel.play(ch, snd)

# 安全にBGMを再生するためのヘルパー関数
def safe_playm(mus, loop=False):
    if ENABLE_SOUND:
        pyxel.playm(mus, loop=loop)

# === 色定義 ===
COL_BLACK = 0       # 黒
COL_NAVY = 1        # 紺
COL_PURPLE = 2      # 紫
COL_GREEN = 3       # 緑
COL_BROWN = 4       # 茶
COL_DK_BLUE = 5     # 濃い青
COL_LT_BLUE = 6     # 水色
COL_WHITE = 7       # 白
COL_RED = 8         # 赤
COL_ORANGE = 9      # オレンジ
COL_YELLOW = 10     # 黄色
COL_LIME = 11       # ライム色
COL_CYAN = 12       # シアン
COL_GRAY = 13       # グレー
COL_PINK = 14       # ピンク
COL_PEACH = 15      # 肌色

# === マップチップ定義 ===
TILE_AIR = (0, 0)
TILE_GROUND = (1, 0)
TILE_SPIKE = (2, 0)
TILE_SPAWN_ENEMY = (0, 8)
TILE_SPAWN_ITEM = (1, 8)

# === サウンドID定義 ===
SND_JUMP = 0         # ジャンプ音
SND_ATTACK = 1       # 攻撃音
SND_HIT = 2          # 敵ヒット音
SND_DAMAGE = 3       # ダメージ音
SND_HEAL = 4         # 回復音
SND_START = 5        # ゲーム開始音
SND_EXPLOSION = 6    # 爆発音
MUS_STAGE = 0        # 通常ステージBGM
MUS_BOSS = 1         # ボス戦BGM

# === ゲーム状態の定義 ===
class GameState(Enum):
    TITLE = auto()
    PLAY = auto()
    BOSS = auto()
    BOSS_EXPLOSION = auto()
    PLAYER_DEAD = auto()
    GAMEOVER = auto()
    CLEAR = auto()

# === ENTITIES (ゲーム内オブジェクトのクラス) ===

class Entity:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.active = True

class Item(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 8, 8)
        self.vy = 0
        self.life = 600
    
    def update(self, app):
        self.vy += GRAVITY
        self.y += self.vy
        
        foot_x = int(self.x + 4) // 8
        foot_y = int(self.y + 8) // 8
        tm = pyxel.tilemaps[0]

        if 0 <= foot_x < tm.width and 0 <= foot_y < tm.height:
            tile = tm.pget(foot_x, foot_y)
            if tile == TILE_GROUND:
                self.y = foot_y * 8 - 8
                self.vy = 0
            
        if self.y > 140:
            self.active = False

        if abs(self.x - app.player.x) < 12 and abs(self.y - app.player.y) < 12:
            self.active = False
            app.player.heal(3)
            app.add_effect(self.x, self.y, COL_PINK)
            safe_play(2, SND_HEAL)
            
        self.life -= 1
        if self.life < 0:
            self.active = False

    def draw(self):
        if self.life < 60 and (self.life // 4) % 2 == 0:
            return
        pyxel.blt(self.x, self.y, 0, 56, 0, 8, 8, COL_BLACK)

class Bullet(Entity):
    def __init__(self, x, y, dx, dy, is_player_bullet):
        super().__init__(x, y, 8, 8)
        self.dx = dx
        self.dy = dy
        self.is_player_bullet = is_player_bullet
        self.color = COL_LIME if is_player_bullet else COL_RED
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        if not (-20 < self.x < 2000) or not (-20 < self.y < 200):
            self.active = False
        
    def draw(self):
        pyxel.circ(self.x + 4, self.y + 4, 2, self.color)

class Effect:
    def __init__(self, x, y, color, life=10):
        self.x = x
        self.y = y
        self.color = color
        self.life = life
        self.max_life = life
        
    def update(self):
        self.life -= 1
        return self.life > 0
        
    def draw(self):
        r = (self.life * 3) // self.max_life
        if r > 0:
            pyxel.circ(self.x, self.y, r, self.color)

class Particle(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 2, 2)
        self.dx = random.uniform(-3, 3)
        self.dy = random.uniform(-3, 3)
        self.life = random.randint(20, 40)
        self.color = random.choice([COL_WHITE, COL_RED, COL_ORANGE, COL_YELLOW])
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        return self.life > 0
        
    def draw(self):
        size = 2 if self.life > 10 else 1
        pyxel.circ(self.x, self.y, size, self.color)

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 16, 16)
        self.dx = 0
        self.dy = 0
        self.direction = 1
        self.hp = PLAYER_MAX_HP
        self.is_grounded = False
        self.attack_frame = 0
        self.invincible_timer = 0
        self.jump_count = 0
        self.trail = [] 

    def update(self, app):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        is_dashing = pyxel.btn(pyxel.KEY_SHIFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_B)
        spd = 2.0 * (DASH_SPEED_MULTIPLIER if is_dashing else 1.0)

        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT):
            self.dx = -spd
            self.direction = -1
        elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT):
            self.dx = spd
            self.direction = 1
        else:
            self.dx *= 0.7 
        
        if self.attack_frame > 0:
            self.attack_frame -= 1
            if self.attack_frame == 10:
                self._check_hit(app)
        
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_Y):
             self.attack_frame = 15 
        
        if pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X):
            app.bullets.append(Bullet(self.x + (16 if self.direction==1 else -4), self.y+6, self.direction*5, 0, True))
            safe_play(3, SND_ATTACK)
            
        if (pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)) and (self.is_grounded or self.jump_count < 2):
            self.dy = -7
            self.jump_count += 1
            self.is_grounded = False
            safe_play(2, SND_JUMP)

        if is_dashing and (abs(self.dx) > 1.0):
            if pyxel.frame_count % 3 == 0:
                self.trail.append((self.x, self.y, 10))
        self.trail = [(tx, ty, tl-1) for tx, ty, tl in self.trail if tl > 0]

        self.dy += GRAVITY
        self.resolve_collisions(app)
        self.check_env(app)

    def heal(self, amount):
        self.hp = min(self.hp + amount, PLAYER_MAX_HP)

    def _check_hit(self, app):
        hx = self.x + (16 if self.direction == 1 else -12)
        hit = False
        for e in app.enemies:
            if e.active and self.check_overlap(hx, self.y, 16, 16, e):
                e.take_damage(app)
                hit = True
        if app.is_boss_active and self.check_overlap(hx, self.y, 16, 16, app.boss):
            app.boss.take_damage(3, app)
            hit = True
            
        if not hit:
            safe_play(3, SND_ATTACK)

    def take_damage(self, app, amount):
        if self.invincible_timer > 0 or self.hp <= 0:
            return
        self.hp = max(0, self.hp - amount)
        self.invincible_timer = INVINCIBLE_DURATION
        self.dy = -3
        self.dx = -self.direction * 4
        safe_play(2, SND_DAMAGE)

    def check_env(self, app):
        if self.hp <= 0:
            return
        cx = int(self.x+8)//8
        cy = int(self.y+14)//8
        tm = pyxel.tilemaps[0]
        if 0 <= cx < tm.width and 0 <= cy < tm.height:
            t = tm.pget(cx, cy)
            if t == TILE_SPIKE:
                self.hp = 0
                safe_play(2, SND_DAMAGE)

    def resolve_collisions(self, app):
        self.x += self.dx
        if self.x < 0:
            self.x = 0
        
        if app.is_boss_active:
            if self.x < BOSS_START_X:
                self.x = BOSS_START_X
            elif self.x > BOSS_START_X + SCREEN_WIDTH - 16:
                self.x = BOSS_START_X + SCREEN_WIDTH - 16
        
        if self.dx > 0: 
            if self._is_wall(self.x + 15, self.y) or self._is_wall(self.x + 15, self.y + 15):
                self.x = (int(self.x + 15) // 8) * 8 - 16
                self.dx = 0
        elif self.dx < 0: 
            if self._is_wall(self.x, self.y) or self._is_wall(self.x, self.y + 15):
                self.x = (int(self.x) // 8 + 1) * 8
                self.dx = 0

        self.y += self.dy
        self.is_grounded = False

        if self.dy > 0: 
            if self._is_ground(self.x + 4, self.y + 16) or self._is_ground(self.x + 12, self.y + 16):
                self.y = (int(self.y + 16) // 8) * 8 - 16
                self.dy = 0
                self.is_grounded = True
                self.jump_count = 0
        elif self.dy < 0: 
            if self._is_wall(self.x + 4, self.y) or self._is_wall(self.x + 12, self.y):
                self.y = (int(self.y) // 8 + 1) * 8
                self.dy = 0

    def _is_wall(self, x, y):
        tm = pyxel.tilemaps[0]
        tx = int(x) // 8
        ty = int(y) // 8
        if 0 <= tx < tm.width and 0 <= ty < tm.height:
            return tm.pget(tx, ty) == TILE_GROUND
        return False
    
    def _is_ground(self, x, y):
        tm = pyxel.tilemaps[0]
        tx = int(x) // 8
        ty = int(y) // 8
        if 0 <= tx < tm.width and 0 <= ty < tm.height:
            return tm.pget(tx, ty) == TILE_GROUND
        return False
    
    def check_overlap(self, x, y, w, h, t):
        return (x < t.x + t.w and x + w > t.x and y < t.y + t.h and y + h > t.y)
    
    def draw(self):
        for tx, ty, tl in self.trail:
            color = COL_GRAY if tl % 2 == 0 else COL_NAVY
            w = 16 if self.direction == 1 else -16
            pyxel.blt(tx, ty, 0, 0, 16, w, 16, color)

        if self.invincible_timer > 0 and (self.invincible_timer // 2) % 2 == 0:
            return
        
        u = 16 if self.attack_frame > 0 else 0
        w = 16 if self.direction == 1 else -16
        pyxel.blt(self.x, self.y, 0, u, 16, w, 16, 0)

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 16, 16)
        self.dir = -1
        self.dy = 0
    
    def update(self, app):
        if not self.active:
            return
        
        self.dy += GRAVITY
        self.y += self.dy
        
        foot_y = int(self.y + 16)
        tx_l = int(self.x) // 8
        tx_r = int(self.x + 15) // 8
        ty = foot_y // 8

        tile_l = TILE_AIR
        tile_r = TILE_AIR
        tm = pyxel.tilemaps[0]
        
        if 0 <= ty < tm.height:
            if 0 <= tx_l < tm.width:
                tile_l = tm.pget(tx_l, ty)
            if 0 <= tx_r < tm.width:
                tile_r = tm.pget(tx_r, ty)
                
        if tile_l == TILE_GROUND or tile_r == TILE_GROUND:
            self.y = (foot_y // 8) * 8 - 16
            self.dy = 0
        
        self.x += self.dir * 0.5
        if pyxel.frame_count % 120 == 0:
            self.dir *= -1 
        
        if abs(self.x - app.player.x) < 12 and abs(self.y - app.player.y) < 12:
            app.player.take_damage(app, 1)
        
        if self.y > 150:
            self.active = False 
    
    def take_damage(self, app): 
        self.active = False
        app.add_effect(self.x, self.y, COL_YELLOW)
        safe_play(3, SND_HIT)
        if random.random() < 0.25:
            app.items.append(Item(self.x, self.y))

    def draw(self):
        if self.active:
            pyxel.blt(self.x, self.y, 0, 32, 16, 16, 16, 0)

class Boss(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 24, 24)
        self.hp = 50
        self.state = "IDLE"
        self.timer = 0
        self.base_y = y
        self.wave_t = 0

    def update(self, app):
        self.timer += 1
        self.wave_t += 0.05
        hover_offset = math.sin(self.wave_t * 0.5) * 10 + math.sin(self.wave_t * 1.3) * 3
        
        if self.state in ["IDLE", "SHOOT"]:
            self.y = self.base_y + hover_offset

        if self.state == "IDLE":
            if self.timer > 60:
                self.state = random.choice(["DASH", "SHOOT", "SHOOT"])
                self.timer = 0
        elif self.state == "DASH":
            if self.timer < 20:
                self.y -= 2
            else:
                self.x -= 3
                if self.x < BOSS_START_X:
                    self.x = BOSS_START_X
                    self.state = "RETURN"
                    self.timer = 0
        elif self.state == "SHOOT":
            if self.timer % 20 == 0 and self.timer < 60:
                aim_y = 1 if app.player.y > self.y else -1
                app.bullets.append(Bullet(self.x, self.y+12, -3, aim_y, False))
                safe_play(3, SND_ATTACK)
            if self.timer > 80:
                self.state = "IDLE"
                self.timer = 0
        elif self.state == "RETURN":
            self.x += 1
            self.y += (self.base_y - self.y) * 0.1
            if abs(self.x - (BOSS_START_X + 100)) < 2:
                self.state = "IDLE"
                self.timer = 0
            
        if abs(self.x - app.player.x) < 16 and abs(self.y - app.player.y) < 16:
            app.player.take_damage(app, 2)
    
    def take_damage(self, amount, app): 
        self.hp -= amount
        app.add_effect(self.x+12, self.y+12, COL_ORANGE)
        safe_play(3, SND_HIT)

    def draw(self):
        off = random.randint(-1, 1) if self.state != "IDLE" else 0
        pyxel.blt(self.x + off, self.y, 0, 0, 32, 24, 24, 0)

# === MAIN APP (ゲーム全体を管理するクラス) ===
class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Battle Machine")
        
        try:
            pyxel.load("battle_machine.pyxres")
        except:
            pass
            
        # ★重要修正★
        # 起動時に1回だけマップをスキャンし、敵とアイテムの初期位置を保存します。
        # これにより、リセット時に pyxel.load() を呼ぶ必要がなくなり、Web版でのメモリ破壊を完全に防ぎます。
        self.initial_enemies = []
        self.initial_items = []
        tm = pyxel.tilemaps[0]
        for my in range(tm.height):
            for mx in range(tm.width):
                tile = tm.pget(mx, my)
                if tile == TILE_SPAWN_ENEMY:
                    self.initial_enemies.append((mx * 8, my * 8 - 4))
                    tm.pset(mx, my, TILE_AIR)
                elif tile == TILE_SPAWN_ITEM:
                    self.initial_items.append((mx * 8, my * 8 - 4))
                    tm.pset(mx, my, TILE_AIR)
        
        self.state = GameState.TITLE
        self.scroll_x = 0
        self.shake_duration = 0
        self.stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.uniform(0.1, 0.5)) for _ in range(40)]
        self.particles = []
        self.items = []
        
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        # pyxel.load() を削除し、メモリ安全性を確保！
        
        self.state = GameState.PLAY
        self.scroll_x = 0
        self.shake_duration = 0
        self.player = Player(10, 60)
        self.bullets = []
        self.effects = []
        self.particles = []
        self.boss = Boss(BOSS_START_X + 100, 50)
        self.is_boss_active = False
        
        # 起動時に記憶しておいた座標から、敵とアイテムを生成します
        self.enemies = [Enemy(ex, ey) for ex, ey in self.initial_enemies]
        self.items = [Item(ix, iy) for ix, iy in self.initial_items]
        
        # 完全に安全になったので、本来のBGM再生に戻します
        safe_playm(MUS_STAGE, loop=True)

    def add_effect(self, x, y, c):
        self.effects.append(Effect(x+8, y+8, c))
    
    def start_shake(self, duration):
        self.shake_duration = duration

    def update(self):
        for i, (sx, sy, spd) in enumerate(self.stars):
            sx -= spd
            if sx < 0:
                sx = SCREEN_WIDTH
            self.stars[i] = (sx, sy, spd)

        if self.state == GameState.TITLE:
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
                safe_play(3, SND_START)
                self.reset_game()
                
        elif self.state in [GameState.PLAY, GameState.BOSS]:
            self.update_play()
        elif self.state == GameState.BOSS_EXPLOSION:
            self.update_boss_explosion()
        elif self.state == GameState.PLAYER_DEAD:
            self.update_player_dead()
        elif self.state in [GameState.GAMEOVER, GameState.CLEAR]:
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A):
                self.reset_game()

    def update_play(self):
        self.player.update(self)
        if self.shake_duration > 0:
            self.shake_duration -= 1

        if not self.is_boss_active:
            target_scroll = self.player.x - 80
            if target_scroll > self.scroll_x:
                self.scroll_x = target_scroll
                
            if self.player.x > BOSS_START_X:
                self.is_boss_active = True
                self.state = GameState.BOSS
                self.scroll_x = BOSS_START_X
                safe_playm(MUS_BOSS, loop=True)

        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]
        
        for e in self.enemies:
            e.update(self)
        self.enemies = [e for e in self.enemies if e.active]
        
        self.items = [i for i in self.items if i.active]
        for i in self.items:
            i.update(self)

        for b in self.bullets:
            if b.active and b.is_player_bullet:
                for e in self.enemies:
                    if e.active and abs(e.x-b.x)<8 and abs(e.y-b.y)<8:
                        e.take_damage(self)
                        b.active = False
                if self.is_boss_active and self.boss.x<b.x<self.boss.x+24 and self.boss.y<b.y<self.boss.y+24:
                    self.boss.take_damage(1, self)
                    b.active = False
            elif b.active and not b.is_player_bullet:
                if abs(self.player.x-b.x)<8 and abs(self.player.y-b.y)<8:
                    self.player.take_damage(self, 1)
                    b.active = False

        if self.is_boss_active:
            self.boss.update(self)
            if self.boss.hp <= 0:
                self.state = GameState.BOSS_EXPLOSION
                self.explosion_timer = 120
                self.start_shake(120)
                pyxel.stop(0)
                pyxel.stop(1)

        self.effects = [ef for ef in self.effects if ef.update()]
        
        if self.player.hp <= 0 or self.player.y > 140:
            self.state = GameState.PLAYER_DEAD
            self.player_dead_timer = 60
            self.start_shake(10)
            pyxel.stop(0)
            pyxel.stop(1)
            safe_play(2, SND_EXPLOSION)
            for _ in range(15):
                self.particles.append(Particle(self.player.x + 8, self.player.y + 8))

    def update_player_dead(self):
        self.player_dead_timer -= 1
        if self.shake_duration > 0:
            self.shake_duration -= 1
        self.particles = [p for p in self.particles if p.update()]
        if self.player_dead_timer <= 0:
            self.state = GameState.GAMEOVER

    def update_boss_explosion(self):
        self.explosion_timer -= 1
        if self.shake_duration > 0:
            self.shake_duration -= 1
        if self.explosion_timer % 10 == 0:
            px = self.boss.x + random.randint(0, 24)
            py = self.boss.y + random.randint(0, 24)
            self.particles.append(Particle(px, py))
            safe_play(2, SND_EXPLOSION)
        self.particles = [p for p in self.particles if p.update()]
        if self.explosion_timer <= 0:
            self.state = GameState.CLEAR
            self.shake_duration = 0

    def draw_background_decor(self):
        factor = 0.5
        offset = (self.scroll_x * factor) % 100
        for i in range(3):
            bx = int((i * 100) - offset)
            if -20 < bx < SCREEN_WIDTH:
                pyxel.rect(bx, 40, 10, SCREEN_HEIGHT, COL_NAVY)
                pyxel.rect(bx+2, 40, 2, SCREEN_HEIGHT, COL_DK_BLUE)

    def draw(self):
        shake_x = random.randint(-2, 2) if self.shake_duration > 0 else 0
        shake_y = random.randint(-2, 2) if self.shake_duration > 0 else 0

        if self.state == GameState.TITLE:
            pyxel.cls(COL_BLACK)
            for sx, sy, _ in self.stars:
                pyxel.pset(sx, sy, COL_WHITE)
            pyxel.text(55, 20, "BATTLE MACHINE", COL_YELLOW)
            pyxel.line(55, 27, 95, 27, COL_YELLOW)
            by=40
            pyxel.text(20, by, "[ CONTROLS ]", COL_WHITE)
            pyxel.text(20, by+10, "MOVE : ARROW / D-PAD", COL_LT_BLUE)
            pyxel.text(20, by+20, "DASH : SHIFT / B BTN", COL_LT_BLUE)
            pyxel.text(20, by+30, "JUMP : SPACE / A BTN", COL_LT_BLUE)
            pyxel.text(20, by+40, "SWORD: Z KEY / Y BTN", COL_LT_BLUE)
            pyxel.text(20, by+50, "SHOT : X KEY / X BTN", COL_LT_BLUE)
            if pyxel.frame_count % 30 < 15:
                pyxel.text(45, 100, "- PRESS SPACE or A -", COL_WHITE)
            return

        pyxel.cls(COL_BLACK)
        
        pyxel.camera(0, 0)
        for sx, sy, spd in self.stars:
            draw_x = (sx - self.scroll_x * 0.1) % SCREEN_WIDTH
            pyxel.pset(draw_x + shake_x, sy + shake_y, COL_WHITE)

        self.draw_background_decor()
        
        render_scroll_x = int(self.scroll_x)
        
        pyxel.bltm(0 + shake_x, 0 + shake_y, 0, render_scroll_x, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0)
        
        pyxel.camera(render_scroll_x + shake_x, shake_y)
        
        if self.state != GameState.PLAYER_DEAD:
            self.player.draw()
        for b in self.bullets:
            b.draw()
        for e in self.enemies:
            e.draw()
        for i in self.items:
            i.draw()
        if self.is_boss_active:
            self.boss.draw()
        for ef in self.effects:
            ef.draw()
        for p in self.particles:
            p.draw()

        pyxel.camera(shake_x, shake_y) 
        
        if self.state != GameState.CLEAR and self.state != GameState.PLAYER_DEAD:
            pyxel.text(5, 5, f"HP: {max(0, self.player.hp)}", COL_YELLOW)
        
        if self.is_boss_active and self.state != GameState.CLEAR: 
            pyxel.rect(40, 10, max(0, self.boss.hp * 2), 4, COL_PURPLE)
            pyxel.text(40, 5, "BOSS", COL_WHITE)
            
        if self.state == GameState.GAMEOVER: 
            pyxel.text(60, 50, "GAME OVER", COL_RED)
            pyxel.text(45, 60, "PRESS SPACE or A", COL_WHITE)
        elif self.state == GameState.CLEAR: 
            pyxel.camera(0, 0) 
            pyxel.text(55, 50, "MISSION COMPLETE", COL_YELLOW)
            pyxel.text(45, 60, "PRESS SPACE or A", COL_WHITE)

if __name__ == "__main__":
    App()