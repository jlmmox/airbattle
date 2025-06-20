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
# 英雄发射子弹事件
Hero_FIRE_EVENT = pygame.USEREVENT + 1
ENEMY_FIRE_EVENT = pygame.USEREVENT + 2

pygame.font.init()
font = pygame.font.Font(None, 60)
font2 = pygame.font.Font(None, 20)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
pygame.display.set_caption("飞机游戏(请使用英文键盘)")


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
        self.base_speed = 2
        self.speed = self.base_speed * speed_multiplier
        self.rect.bottom = 0
        max_x = SCREEN_RECT.width - self.rect.width
        self.rect.x = random.randint(0, max_x)
        self.bullets = pygame.sprite.Group()
        self.last_shot = 0
        self.shot_delay = random.randint(1000, 3000)  # 1-3秒射击间隔
        self.base_shoot = 0.3
        self.can_shoot = random.random() < self.base_shoot * speed_multiplier
        self.speed_multiplier = speed_multiplier  # 保存速度倍数用于子弹
      
        self.is_powerup = random.random() < 0.1  # 10%概率是强化敌机
        if self.is_powerup:
            # 用颜色标记强化敌机（正式版可移除）
            colored = pygame.Surface((self.rect.width, self.rect.height))
            colored.fill((0, 255, 0))  # 绿色标记
            colored.blit(self.image, (0, 0))
            self.image = colored

    def fire(self):
        if not self.can_shoot:
            return None

        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shot_delay:
            self.last_shot = now
            bullet = EnemyBullet(self.speed_multiplier)  # 传入速度倍数
            bullet.rect.centerx = self.rect.centerx
            bullet.rect.top = self.rect.bottom
            return bullet
        return None

class EnemyBullet(GameSprite):
    """敌机子弹精灵"""
    def __init__(self, speed_multiplier=1.0):
        base_bullet_speed = 3  # 基础子弹速度
        super().__init__("./zidan.png", base_bullet_speed * speed_multiplier)
        self.speed_multiplier = speed_multiplier  # 保存速度倍数

    def update(self, *args):
        self.rect.y += self.speed  # 子弹向下飞行
        if self.rect.top > SCREEN_RECT.height:
            self.kill()
class Hero(GameSprite):
    """英雄精灵"""

    def __init__(self):
        super().__init__("./air.png")
        self.rect.centerx = SCREEN_RECT.centerx
        self.rect.bottom = SCREEN_RECT.bottom - 120
        self.bullets = pygame.sprite.Group()
        self.last_shot = 0
        self.shot_delay = 300
        self.is_dead = False
        self.combo_count = 0
        self.last_hit_time = 0
        self.combo_timeout = 1500 # 1.5秒内连续击中有加成
        self.combo_multiplier = 1.0
        self.power_level = 0
        self.max_power = 3
        self.power_time = 0

    def fire(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shot_delay:
            self.last_shot = now
           # 根据强化等级发射不同子弹
            if self.power_level == 0:  # 默认单发
                self.__fire_single()
            elif self.power_level == 1:  # 双发
                self.__fire_double()
            else:  # 三发
                self.__fire_triple()
          
            
            # 强化倒计时
            if self.power_level > 0 and now - self.power_time > 1000:  # 1秒倒计时
                self.power_level -= 1
                print("Power level decreased to:", self.power_level)
                self.power_time = now

    def __fire_single(self):
        bullet = Bullet()
        bullet.rect.midbottom = self.rect.midtop
        self.bullets.add(bullet)

    def __fire_double(self):
        for offset in [-15, 15]:
            bullet = Bullet()
            bullet.rect.bottom = self.rect.y
            bullet.rect.centerx = self.rect.centerx + offset
            self.bullets.add(bullet)

    def __fire_triple(self):
        self.__fire_double()
        self.__fire_single()

    def die(self):
        self.is_dead = True

    def add_combo(self):
        now = pygame.time.get_ticks()
        if now - self.last_hit_time < self.combo_timeout:
            self.combo_count += 1
        else:
            self.combo_count = 1  # 重置连击

        self.last_hit_time = now
       
        # 连击加成公式：每5连击增加0.5倍 (1.0 -> 1.5 -> 2.0...)
        self.combo_multiplier = 1.0 + (self.combo_count // 5) * 0.5
        return int(10 * self.combo_multiplier)  # 基础分10分乘以倍率


class Bullet(GameSprite):
    """子弹精灵"""

    def __init__(self):
        super().__init__("./zidan.png", -2)

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
        pygame.time.set_timer(CREATE_ENEMY_EVENT, 800)
        pygame.time.set_timer(ENEMY_FIRE_EVENT, 500)  # 敌机射击事件
        pygame.mouse.set_visible(False)
        self.is_game_over = False
        self.game_start_time = time.time()
        self.speed_multiplier = 1.0  # 初始速度倍数
        self.base_shoot =0.4
        self.difficulty_increase_interval = 10  # 每10秒增加难度
        self.last_difficulty_increase = self.game_start_time
        self.score = 0
        self.using_keyboard = False  # 添加控制方式状态标记
        self.pause_text = font.render("PAUSED", True, (255, 255, 0))
        self.pause_rect = self.pause_text.get_rect(center=SCREEN_RECT.center)
        self.is_paused = False
        self.pause_start_time = 0
        self.total_paused_time = 0
        self.last_elapsed_time = 0  # 新增：记录暂停前的时间
        self.is_passed = False  # 新增通关标志

    def __handle_pause(self):
        """优化的暂停逻辑"""
        pause_start = time.time()
        while self.is_paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__game_over()
                    return 0  # 退出时返回0，防止None类型参与运算
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_paused = False
                        return time.time() - pause_start
            overlay = pygame.Surface(SCREEN_RECT.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.pause_text, self.pause_rect)
            paused_time = time.time() - pause_start
            time_text = font2.render(f"Paused: {paused_time:.1f}s", True, (255, 255, 255))
            self.screen.blit(time_text, (self.pause_rect.x, self.pause_rect.y + 50))
            pygame.display.flip()
            self.clock.tick(10)
        return 0

    def __create_sprites(self):
        """创建精灵和精灵组"""
        bg1 = Background()
        bg2 = Background(True)
        bg2.rect.y = -bg2.rect.height
        self.back_group = pygame.sprite.Group(bg1, bg2)
        self.enemy_group = pygame.sprite.Group()
        self.powerup_group = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()  # 所有敌机子弹
        self.hero = Hero()
        self.hero_group = pygame.sprite.Group(self.hero)

    def start_game(self):
        print("游戏开始...")
        self.game_start_time = time.time()
        self.total_paused_time = 0
        self.pause_start_time = 0
        # 游戏主循环
        while True:
            self.clock.tick(FRAME_PER_SEC)
            current_time = time.time()
            # 计算实际游戏时间（总时间-暂停时间）
            elapsed_time = current_time - self.game_start_time - self.total_paused_time
            # 暂停状态处理
            if self.is_paused:
                paused_duration = self.__handle_pause()
                self.total_paused_time += paused_duration
                continue
            if not self.is_game_over:
                self.last_elapsed_time = elapsed_time  # 只在非暂停时更新
                self.__update_game_state(elapsed_time, current_time)
            
        

            # 处理所有事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__game_over()
                elif event.type == CREATE_ENEMY_EVENT and not self.is_game_over and not self.is_passed:
                    enemy = Enemy(self.speed_multiplier)
                    self.enemy_group.add(enemy)
                    self.powerup_group.add(enemy)
                elif event.type == ENEMY_FIRE_EVENT and not self.is_game_over and not self.is_passed:
                    for enemy in self.enemy_group or self.powerup_group:
                        bullet = enemy.fire()
                        if bullet:
                            self.enemy_bullets.add(bullet)
                elif event.type == pygame.KEYDOWN and (self.is_game_over or self.is_passed):  # 支持通关界面按键
                    if event.key == pygame.K_r:  # 按R重新开始
                        self.__restart_game()
                    elif event.key == pygame.K_q:  # 按Q退出
                        self.__game_over()
                elif event.type == pygame.KEYDOWN and not self.is_game_over:
                    if event.key == pygame.K_ESCAPE:  # ESC暂停
                        self.is_paused = not self.is_paused
                        # 确保输出立即刷新
                        print("游戏已暂停" if self.is_paused else "游戏继续", flush=True)
                        
                        # 添加调试信息
                        print(f"当前暂停状态: {self.is_paused}")
                        print(f"游戏时间: {time.time() - self.game_start_time - self.total_paused_time:.2f}s")
                        if self.is_paused:
                            # 不要在这里调用self.__handle_pause()，主循环会自动处理
                            pass
            if self.is_passed:
                finished = self.__pass_update()
                if finished:
                    self.__pass_screen()
                else:
                    # 只绘制背景和hero动画，不显示通关文字
                    self.back_group.update()
                    self.back_group.draw(self.screen)
                    self.hero_group.update()
                    self.hero_group.draw(self.screen)
                pygame.display.update()
                continue
            elif not self.is_game_over or not self.__handle_pause:
                #击中检测
                self.__check_collide()
                # 更新精灵组
                self.__update_sprites()
                # 显示当前难度
                self.__show_difficulty(self.last_elapsed_time)  # 始终传递last_elapsed_time
            else:
                self.__game_over_screen()

            pygame.display.update()


    def __update_game_state(self, elapsed_time, current_time):
        """更新游戏状态"""
        if current_time - self.last_difficulty_increase > self.difficulty_increase_interval and not self.is_game_over:
            self.speed_multiplier += 0.2
            self.last_difficulty_increase = current_time
            print(f"难度增加! 速度倍数: {self.speed_multiplier}")
        
    def __show_difficulty(self, elapsed_time):
        """显示当前游戏时间和难度"""
        # 防止暂停时计时继续
        if self.is_paused:
            elapsed_time = self.last_elapsed_time
        time_text = font2.render(f"Time: {int(elapsed_time)}s", True, BLACK)
        difficulty_text = font2.render(f"Speed: x{self.speed_multiplier:.1f}", True,BLACK)
        self.screen.blit(time_text, (5, 5))
        self.screen.blit(difficulty_text, (5, 20))
        score_text = font2.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (5, 50))
        can_shoot = font2.render(f"can_shoot: {self.base_shoot * self.speed_multiplier}", True, BLACK)
        self.screen.blit(can_shoot, (5, 35))
        combo_text = font2.render(
            f"Combo: {self.hero.combo_count}x ({self.hero.combo_multiplier:.1f}倍)",
            True,
            (255, 0, 0) if self.hero.combo_count >= 5 else BLACK  # 5连击以上变红色
        )
        self.screen.blit(combo_text, (5, 60))
        if self.hero.combo_count > 0:
            now = pygame.time.get_ticks()
            remaining_time = max(0, self.hero.combo_timeout - (now - self.hero.last_hit_time))
            progress = remaining_time / self.hero.combo_timeout
            pygame.draw.rect(self.screen, (255, 0, 0), (5, 70, 100 * progress, 5))




    
      

    def __event_handle(self):
        """事件监听"""
        if not self.is_game_over and not self.hero.is_dead:
            #飞机开火
            self.hero.fire()
            
            # 键盘移动
            keys = pygame.key.get_pressed()
            move_speed = 5
            moved_by_keyboard = False
            
            if keys[pygame.K_LEFT]:
                self.hero.rect.x -= move_speed
                moved_by_keyboard = True
            if keys[pygame.K_a]:
                self.hero.rect.x -= move_speed
                moved_by_keyboard = True
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.hero.rect.x += move_speed
                moved_by_keyboard = True
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.hero.rect.y -= move_speed
                moved_by_keyboard = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.hero.rect.y += move_speed
                moved_by_keyboard = True

            # 更新控制方式状态
            if moved_by_keyboard:
                self.using_keyboard = True
            elif pygame.mouse.get_rel() != (0, 0):  # 检测鼠标移动
                self.using_keyboard = False

            # 鼠标移动
            if not self.using_keyboard:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if 0 <= mouse_x <= SCREEN_RECT.width and 0 <= mouse_y <= SCREEN_RECT.height:
                    self.hero.rect.centerx = mouse_x
                    self.hero.rect.centery = mouse_y

            # 边界限制
            if self.hero.rect.left < 0:
                self.hero.rect.left = 0
            if self.hero.rect.right > SCREEN_RECT.right:
                self.hero.rect.right = SCREEN_RECT.right
            if self.hero.rect.top < 0:
                self.hero.rect.top = 0
            if self.hero.rect.bottom > SCREEN_RECT.bottom:
                self.hero.rect.bottom = SCREEN_RECT.bottom
                
       
            
         
    def __check_collide(self):
        # 1. 先检测玩家与敌机/子弹的碰撞（保存碰撞结果）
        collided_enemies = pygame.sprite.spritecollide(self.hero, self.enemy_group, False)
        collided_bullets = pygame.sprite.spritecollide(self.hero, self.enemy_bullets, True)
        
        # 玩家被击中则死亡
        if (collided_enemies or collided_bullets) and not self.hero.is_dead:
            self.hero.die()
            self.is_game_over = True
            # 敌机被撞也消失
            for enemy in collided_enemies:
                enemy.kill()
            return  # 直接返回，不再处理其他碰撞
        
        # 2. 玩家子弹击中敌机（仅当玩家存活时处理）
        if not self.hero.is_dead:
            hits = pygame.sprite.groupcollide(
                self.hero.bullets, 
                self.enemy_group, 
                True,   # 删除子弹
                False   # 不自动删除敌机
            )
            
            # 处理击中逻辑
            for bullet, enemies in hits.items():
                for enemy in enemies:
                    if hasattr(enemy, "take_damage"):
                        dead = enemy.take_damage()
                    else:
                        dead = True
                    if dead:
                        self.score += 10
                        enemy.kill()
                        self.score += self.hero.add_combo()
                        if hasattr(enemy, "is_powerup") and enemy.is_powerup:
                            self.hero.power_level = min(self.hero.power_level+1, self.hero.max_power)
                            self.hero.power_time = pygame.time.get_ticks()
        
        # 3. 通关判断
        if self.score >= 1000:
            self.is_passed = True
            

    def __update_sprites(self):
        """更新精灵组"""
        self.back_group.update()
        self.back_group.draw(self.screen)
        self.enemy_group.update()
        self.enemy_group.draw(self.screen)
        self.powerup_group.update()
        self.powerup_group.draw(self.screen)
        self.hero_group.update()
        self.hero_group.draw(self.screen)
        self.hero.bullets.update()
        self.hero.bullets.draw(self.screen)
        self.enemy_bullets.update()
        self.enemy_bullets.draw(self.screen)
        # 更新英雄位置
        self.__event_handle()

    def __game_over_screen(self):
        """游戏结束界面"""
        # 半透明背景
        s = pygame.Surface((SCREEN_RECT.width, SCREEN_RECT.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))
        self.screen.blit(s, (0, 0))

        # 游戏结束文字
        game_over_text = font.render("Game Over!", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        #得分
        score_text = font.render(f"Score: {self.score}", True,RED)
        score_rect =score_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2 ))
        self.screen.blit(score_text, score_rect)
        # 操作提示
        restart_text = font.render("R == Restart_game!", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2 + 50))
        self.screen.blit(restart_text, restart_rect)

        quit_text = font.render("Q== Quit_game!", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2 + 120))
        self.screen.blit(quit_text, quit_rect)

    def __pass_update(self):
        """通关时hero慢慢飞出地图，飞出后返回True"""
        # 清空敌人和子弹
        self.enemy_group.empty()
        self.enemy_bullets.empty()
        self.powerup_group.empty()
        # 只让hero向上飞出
        if self.hero.rect.bottom > 0:
            self.hero.rect.y -= 10 # 更慢的飞出速度
            # 绘制背景和hero
            self.back_group.update()
            self.back_group.draw(self.screen)
            self.hero_group.update()
            self.hero_group.draw(self.screen)
            return False  # 尚未飞出
        else:
            return True   # 已飞出，显示通关界面

    def __pass_screen(self):
        """显示通关界面"""
        s = pygame.Surface((SCREEN_RECT.width, SCREEN_RECT.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))
        self.screen.blit(s, (0, 0))
        pass_text = font.render("YOU WIN!", True, (0, 255, 0))
        pass_rect = pass_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2 - 50))
        self.screen.blit(pass_text, pass_rect)
        score_text = font.render(f"Score: {self.score}", True, (0, 255, 0))
        score_rect = score_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2))
        self.screen.blit(score_text, score_rect)
        restart_text = font.render("R == Restart_game!", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2 + 50))
        self.screen.blit(restart_text, restart_rect)
        quit_text = font.render("Q== Quit_game!", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_RECT.width // 2, SCREEN_RECT.height // 2 + 120))
        self.screen.blit(quit_text, quit_rect)

    def __restart_game(self):
        """重新开始游戏"""
        self.__create_sprites()
        self.is_game_over = False
        self.speed_multiplier = 1.0
        self.score=0
        self.game_start_time = time.time()
        self.total_paused_time = 0
        self.pause_start_time = 0
        self.last_elapsed_time = 0  # 重置
        self.is_passed = False  # 重置通关标志

    @staticmethod
    def __game_over():
        """游戏结束"""
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = PlaneGame()
    game.start_game()