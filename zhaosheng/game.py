
import cv2
import mediapipe as mp
import pygame
import numpy as np
import sys
import os
import random

# 初始化MediaPipe手势识别
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Pygame初始化
pygame.init()
pygame.mixer.init()
screen_width, screen_height = 1280, 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("手势识别空战(移动手控制方向)")


# macOS字体配置
def get_chinese_font(size):
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        os.path.expanduser("~/Library/Fonts/Microsoft YaHei.ttf")
    ]
    for path in font_paths:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("Arial", size)


# 音频资源加载
class GameAudio:
    def __init__(self):
        self.explosion = pygame.mixer.Sound('static/explosion.wav')
        self.shoot = pygame.mixer.Sound('static/laser.wav')
        self.bgm = pygame.mixer.Sound('static/bgsound.wav')
        self.bgm.set_volume(1)
        self.shoot.set_volume(0.2)
        self.explosion.set_volume(1)


# 智能图像加载器
class AssetLoader:
    @staticmethod
    def load_image(path, size, bg_tolerance=40):
        try:
            img = pygame.image.load(path)
            surface = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            surface.blit(img, (0, 0))

            # 去除白色背景
            arr = pygame.surfarray.pixels3d(surface)
            alpha = pygame.surfarray.pixels_alpha(surface)
            white_min = 255 - bg_tolerance
            mask = np.all(arr >= white_min, axis=2)
            alpha[mask] = 0
            del arr, alpha
            return pygame.transform.scale(surface, size)
        except Exception as e:
            print(f"图片加载失败: {e}")
            return None


# 游戏实体类
class Player(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(screen_width // 2, screen_height - 100))
        self.speed_factor = 0.25
        self.invincible = False


class Enemy(pygame.sprite.Sprite):
    def __init__(self, image, base_speed, wave_type=0):
        super().__init__()
        self.image = image
        self.base_speed = base_speed
        self.speed = random.randint(base_speed, base_speed + 3)
        self.wave_type = wave_type
        self.angle = 0

        if wave_type == 0:
            x = random.randint(50, screen_width - 50)
        elif wave_type == 1:
            x = random.choice([200, 640, 1080])
        elif wave_type == 2:
            x = random.randint(100, screen_width - 100)

        self.rect = self.image.get_rect(center=(x, -100))

    def update(self):
        if self.wave_type == 0:
            self.rect.y += self.speed
        elif self.wave_type == 1:
            self.rect.y += self.speed
            self.rect.x += int(3 * np.sin(self.rect.y / 30))
        elif self.wave_type == 2:
            self.rect.y += self.speed
            self.angle += 2
            self.rect.x += int(5 * np.sin(np.radians(self.angle)))

        if self.rect.y > screen_height + 100:
            self.kill()


# 游戏主逻辑
class AirBattle:
    def __init__(self):
        self.assets = self.load_resources()
        self.player = Player(self.assets['player'])
        self.enemies = pygame.sprite.Group()
        self.cap = cv2.VideoCapture(0)
        self.audio = GameAudio()
        self.fonts = {
            'title': get_chinese_font(72),
            'ui': get_chinese_font(36)
        }
        self.start_time = pygame.time.get_ticks()
        self.game_active = True
        self.wave_count = 0
        self.current_cam_view = None  # 新增：存储当前摄像头画面

    def load_resources(self):
        loader = AssetLoader()
        return {
            'player': loader.load_image('static/plane.jpg', (120, 100)) or self.default_plane(),
            'enemy': loader.load_image('static/pd.png', (50, 70)) or self.default_enemy()
        }

    def default_plane(self):
        surface = pygame.Surface((120, 100), pygame.SRCALPHA)
        pygame.draw.polygon(surface, (0, 255, 0), [(40, 0), (75, 30), (40, 60), (5, 30)])
        return surface

    def default_enemy(self):
        surface = pygame.Surface((40, 60), pygame.SRCALPHA)
        pygame.draw.rect(surface, (200, 0, 0), (0, 0, 40, 60), border_radius=5)
        return surface

    def get_difficulty(self):
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        return min(5 + elapsed // 5, 20)

    def get_spawn_interval(self):
        return max(15, 40 - self.get_difficulty())

    def gesture_tracking(self):
        success, frame = self.cap.read()
        if not success: return None, None

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        hand_pos = None
        if results.multi_hand_landmarks:
            for landmarks in results.multi_hand_landmarks:
                point = landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                x = np.interp(point.x, [0, 1], [0, screen_width])
                y = np.interp(point.y, [0, 1], [0, screen_height])
                hand_pos = (x, y)
                mp_draw.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return hand_pos, pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")

    def run(self):
        spawn_counter = 0
        self.audio.bgm.play(-1)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                if event.type == pygame.KEYDOWN:
                    if not self.game_active:  # 只在游戏结束时响应任意按键
                        self.__init__()
                        continue

            if self.game_active:
                # 获取手势跟踪结果并保存摄像头画面
                hand_pos, cam_view = self.gesture_tracking()
                self.current_cam_view = cam_view  # 保存当前摄像头画面

                # 更新玩家位置
                if hand_pos:
                    self.player.rect.centerx += (hand_pos[0] - self.player.rect.centerx) * self.player.speed_factor
                    self.player.rect.centery += (hand_pos[1] - self.player.rect.centery) * self.player.speed_factor

                # 敌机生成逻辑
                current_interval = self.get_spawn_interval()
                if spawn_counter % current_interval == 0:
                    self.wave_count += 1
                    wave_type = self.wave_count // 10 % 3

                    for _ in range(random.randint(3, 5)):
                        enemy = Enemy(
                            self.assets['enemy'],
                            base_speed=self.get_difficulty(),
                            wave_type=wave_type
                        )
                        self.enemies.add(enemy)

                    self.audio.shoot.play()

                self.enemies.update()

                # 碰撞检测
                if not self.player.invincible:
                    if pygame.sprite.spritecollideany(self.player, self.enemies):
                        self.game_active = False
                        self.audio.explosion.play()

                spawn_counter += 1

            self.render()

    def render(self):
        screen.fill((25, 25, 35))

        if self.game_active:
            # 游戏UI信息
            info_text = self.fonts['ui'].render(
                f"难度: {self.get_difficulty()} 波次: {self.wave_count} 炮弹: {len(self.enemies)}",
                True, (180, 230, 180))
            screen.blit(info_text, (20, 20))

            # 绘制游戏元素
            screen.blit(self.player.image, self.player.rect)
            self.enemies.draw(screen)

            # 新增：画中画显示摄像头画面
            if self.current_cam_view:
                pip_width = 150  # 画中画宽度
                pip_height = 150  # 画中画高度
                pip_surface = pygame.transform.scale(self.current_cam_view, (pip_width, pip_height))
                border_rect = pygame.Rect(screen_width - pip_width - 15,
                                          screen_height - pip_height - 15,
                                          pip_width + 10,
                                          pip_height + 10)
                pygame.draw.rect(screen, (255, 255, 255), border_rect, 2, border_radius=5)
                screen.blit(pip_surface, (screen_width - pip_width - 10, screen_height - pip_height - 10))

        else:
            # 游戏结束界面
            title = self.fonts['title'].render("游戏结束", True, (200, 50, 50))
            screen.blit(title, (screen_width // 2 - 120, screen_height // 2 - 60))

            stats = self.fonts['ui'].render(
                f"最终波次: {self.wave_count} 存活时间: {(pygame.time.get_ticks() - self.start_time) // 1000}秒",
                False, (200, 200, 200))
            screen.blit(stats, (screen_width // 2 - 180, screen_height // 2 + 80))

            hint = self.fonts['ui'].render("按任意键重新开始", True, (180, 180, 180))
            screen.blit(hint, (screen_width // 2 - 100, screen_height // 2 + 20))

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    def quit_game(self):
        self.cap.release()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    AirBattle().run()