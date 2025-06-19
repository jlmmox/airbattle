import sys
import time
import pygame
import random

# 游戏屏幕的尺寸
SCREEN_RECT = pygame.Rect(0, 0, 433, 650)
# 游戏的刷新帧率
FRAME_PER_SEC = 60
# 敌机的定时器常量
CREATE_ENEMY_EVENT = pygame.USEREVENT
# 敌机发射子弹事件
ENEMY_FIRE_EVENT = pygame.USEREVENT + 1

pygame.font.init()
font = pygame.font.Font(None, 60)
font2 = pygame.font.Font(None, 20)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
pygame.display.set_caption("飞机游戏")


class GameSprite(pygame.sprite.Sprite):
    """游戏精灵基类"""

    def __init__(self, image_name, speed=1):
        super().__init__()
        self.image = pygame.image.load(image_name)
        self.rect = self.image.get_rect()
        self.speed = speed

    def update(self, *args):
        self.rect.y += self.speed


class Background(GameSprite):
    """游戏背景精灵"""

    def __init__(self, is_alt=False):
        image_name = "./background.jpg"
        super().__init__(image_name)
        if is_alt:
            self.rect.y = -self.rect.height

    def update(self, *args):
        super().update()
        if self.rect.y >= SCREEN_RECT.height:
            self.rect.y = -self.rect.height


class Enemy(GameSprite):
    """敌机精灵"""

    def __init__(self, speed_multiplier=1.0):
        super().__init__("./enemy.png")
        self.base_speed = 0.5
        self.speed = self.base_speed * speed_multiplier
        self.rect.bottom = 0
        max_x = SCREEN_RECT.width - self.rect.width
        self.rect.x = random.randint(0, max_x)
        self.last_shot = pygame.time.get_ticks()
        self.shot_delay = random.randint(1500, 3000)

    def fire(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shot_delay:
            self.last_shot = now
            bullet = EnemyBullet()
            bullet.rect.centerx = self.rect.centerx
            bullet.rect.top = self.rect.bottom
            return bullet
        return None


class EnemyBullet(GameSprite):
    """敌机子弹精灵"""

    def __init__(self):
        super().__init__("./zidan.png", 3)  # 使用专门的敌机子弹图片
        self.damage = 1

    def update(self, *args):
        super().update()
        if self.rect.top > SCREEN_RECT.height:
            self.kill()


class Hero(GameSprite):
    """英雄精灵"""

    def __init__(self):
        super().__init__("./air.png", 0)
        self.rect.centerx = SCREEN_RECT.centerx
        self.rect.bottom = SCREEN_RECT.bottom - 120
        self.bullets = pygame.sprite.Group()
        self.last_shot = 0
        self.shot_delay = 200
        self.is_dead = False

    def fire(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shot_delay:
            self.last_shot = now
            bullet = Bullet()
            bullet.rect.bottom = self.rect.y
            bullet.rect.centerx = self.rect.centerx
            self.bullets.add(bullet)

    def die(self):
        self.is_dead = True


class Bullet(GameSprite):
    """子弹精灵"""

    def __init__(self):
        super().__init__("./zidan.png", -8)
        self.damage = 1

    def update(self, *args):
        super().update()
        if self.rect.bottom < 0:
            self.kill()


class PlaneGame(object):
    """飞机大战主游戏"""

    def __init__(self):
        print("游戏初始化..")
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_RECT.size)
        self.clock = pygame.time.Clock()
        self.__create_sprites()
        pygame.time.set_timer(CREATE_ENEMY_EVENT, 1000)
        pygame.time.set_timer(ENEMY_FIRE_EVENT, 300)  # 敌机射击检查频率
        pygame.mouse.set_visible(False)
        self.is_game_over = False
        self.game_start_time = time.time()
        self.speed_multiplier = 0.8
        self.difficulty_increase_interval = 15
        self.last_difficulty_increase = self.game_start_time
        self.score = 0

    def __create_sprites(self):
        """创建精灵和精灵组"""
        bg1 = Background()
        bg2 = Background(True)
        bg2.rect.y = -bg2.rect.height
        self.back_group = pygame.sprite.Group(bg1, bg2)
        self.enemy_group = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.hero = Hero()
        self.hero_group = pygame.sprite.Group(self.hero)

    def start_game(self):
        print("游戏开始...")
        while True:
            self.clock.tick(FRAME_PER_SEC)
            current_time = time.time()
            elapsed_time = current_time - self.game_start_time

            # 随时间增加难度
            if current_time - self.last_difficulty_increase > self.difficulty_increase_interval:
                self.speed_multiplier += 0.1
                self.last_difficulty_increase = current_time

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__game_over()
                elif event.type == CREATE_ENEMY_EVENT and not self.is_game_over:
                    enemy = Enemy(self.speed_multiplier)
                    self.enemy_group.add(enemy)
                elif event.type == ENEMY_FIRE_EVENT and not self.is_game_over:
                    for enemy in self.enemy_group:
                        bullet = enemy.fire()
                        if bullet:
                            self.enemy_bullets.add(bullet)
                elif event.type == pygame.KEYDOWN and self.is_game_over:
                    if event.key == pygame.K_r:
                        self.__restart_game()
                    elif event.key == pygame.K_q:
                        self.__game_over()

            if not self.is_game_over:
                self.__check_collide()
                self.__update_sprites()
                self.__show_difficulty(elapsed_time)
            else:
                self.__game_over_screen()

            pygame.display.update()

    def __check_collide(self):
        """碰撞检测"""
        # 玩家子弹击中敌机
        hits = pygame.sprite.groupcollide(
            self.hero.bullets,
            self.enemy_group,
            True,  # 删除子弹
            True  # 删除敌机
        )
        self.score += len(hits) * 10

        # 敌机或敌机子弹击中玩家
        if pygame.sprite.spritecollide(self.hero, self.enemy_group, True) or \
                pygame.sprite.spritecollide(self.hero, self.enemy_bullets, True):
            self.hero.die()
            self.is_game_over = True

    def __update_sprites(self):
        """更新精灵组"""
        self.back_group.update()
        self.back_group.draw(self.screen)
        self.enemy_group.update()
        self.enemy_group.draw(self.screen)
        self.hero_group.update()
        self.hero_group.draw(self.screen)
        self.hero.bullets.update()
        self.hero.bullets.draw(self.screen)
        self.enemy_bullets.update()
        self.enemy_bullets.draw(self.screen)

        # 控制英雄移动
        if not self.is_game_over and not self.hero.is_dead:
            self.__control_hero()

    def __control_hero(self):
        """控制英雄移动"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.hero.rect.centerx = mouse_x
        self.hero.rect.centery = mouse_y

        # 边界检查
        if self.hero.rect.left < 0:
            self.hero.rect.left = 0
        if self.hero.rect.right > SCREEN_RECT.right:
            self.hero.rect.right = SCREEN_RECT.right
        if self.hero.rect.top < 0:
            self.hero.rect.top = 0
        if self.hero.rect.bottom > SCREEN_RECT.bottom:
            self.hero.rect.bottom = SCREEN_RECT.bottom

    def __show_difficulty(self, elapsed_time):
        """显示游戏信息"""
        time_text = font2.render(f"Time: {int(elapsed_time)}s", True, BLACK)
        speed_text = font2.render(f"Speed: x{self.speed_multiplier:.1f}", True, BLACK)
        score_text = font2.render(f"Score: {self.score}", True, BLACK)

        self.screen.blit(time_text, (5, 5))
        self.screen.blit(speed_text, (5, 25))
        self.screen.blit(score_text, (5, 45))

    def __game_over_screen(self):
        """游戏结束界面"""
        s = pygame.Surface((SCREEN_RECT.width, SCREEN_RECT.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))

        game_over = font.render("GAME OVER", True, RED)
        restart = font.render("Press R to restart", True, WHITE)
        quit_text = font.render("Press Q to quit", True, WHITE)

        self.screen.blit(game_over, (SCREEN_RECT.width // 2 - game_over.get_width() // 2,
                                     SCREEN_RECT.height // 2 - 80))
        self.screen.blit(restart, (SCREEN_RECT.width // 2 - restart.get_width() // 2,
                                   SCREEN_RECT.height // 2))
        self.screen.blit(quit_text, (SCREEN_RECT.width // 2 - quit_text.get_width() // 2,
                                     SCREEN_RECT.height // 2 + 80))

    def __restart_game(self):
        """重新开始游戏"""
        self.__create_sprites()
        self.is_game_over = False
        self.game_start_time = time.time()
        self.speed_multiplier = 0.8
        self.score = 0

    @staticmethod
    def __game_over():
        """退出游戏"""
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = PlaneGame()
    game.start_game()