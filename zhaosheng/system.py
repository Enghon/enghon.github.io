import curses
import time
import random
from curses import textpad
from enum import Enum


class DiskLayout(Enum):
    MBR = 1
    GPT = 2


class PEInstaller:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.disk_size = 1024 * 1024 * 1024  # 1TB
        self.partitions = []
        self.current_step = 0
        self.selected_disk = None
        self.system_image = None
        self.boot_mode = None
        self.disk_layout = None

    def draw_bios_interface(self):
        # BIOS界面模拟
        self.stdscr.clear()
        self.stdscr.addstr(2, 5, "American Megatrends BIOS Setup Utility", curses.A_BOLD)
        menu_items = [
            ("Main", "System Time and Date Settings"),
            ("Advanced", "Configure Advanced CPU Settings"),
            ("Boot", "Modify Boot Device Settings"),
            ("Security", "Set Administrator Password"),
            ("Exit", "Exit System Setup")
        ]
        for idx, (title, desc) in enumerate(menu_items):
            self.stdscr.addstr(5 + idx * 2, 10, f"{title}: {desc}",
                               curses.A_REVERSE if idx == self.current_step else curses.A_NORMAL)
        self.stdscr.refresh()

    def simulate_diskpart(self):
        # 磁盘分区工具模拟
        self.stdscr.clear()
        disks = [
            ("Disk0", "931.5GB", "Online"),
            ("USB1", "14.9GB", "Removable")
        ]
        textpad.rectangle(self.stdscr, 3, 5, 20, 60)
        self.stdscr.addstr(4, 7, "DiskPart Version 10.0.19041.1", curses.A_BOLD)

        # 显示磁盘列表
        for idx, (name, size, status) in enumerate(disks):
            self.stdscr.addstr(6 + idx, 7, f" {name}   {size}  {status} ",
                               curses.A_REVERSE if idx == self.current_step else curses.A_NORMAL)

        # 分区操作面板
        ops = [
            "Convert GPT",
            "Create Partition Primary Size=102400",
            "Format Quick FS=NTFS Label=Windows",
            "Assign Letter=C"
        ]
        for idx, op in enumerate(ops):
            self.stdscr.addstr(15 + idx, 7, f"[{idx + 1}] {op}")

        self.stdscr.refresh()

    def run_windows_setup(self):
        # Windows安装程序模拟
        win = curses.newwin(20, 70, 3, 5)
        win.border()
        stages = [
            ("准备文件", 30),
            ("安装功能", 45),
            ("安装更新", 60),
            ("完成安装", 100)
        ]
        win.addstr(2, 2, "正在安装 Windows 11 专业版", curses.A_BOLD)

        # 进度条动画
        progress = 0
        while progress < 100:
            win.addstr(5, 2, "进度: ")
            win.addstr(5, 10, "▓" * (progress // 2) + "░" * (50 - progress // 2))
            win.addstr(5, 65, f"{progress}%")

            # 动态日志输出
            logs = [
                "展开文件: winutils.dll...",
                "配置系统注册表项...",
                "应用安全策略设置...",
                "初始化用户配置文件..."
            ]
            for idx in range(8, 18):
                if random.random() > 0.7 and idx < 15:
                    win.addstr(idx, 2, random.choice(logs))

            win.refresh()
            time.sleep(0.1)
            progress += random.randint(1, 3)
            if progress > 100:
                progress = 100

    def handle_input(self, key):
        if key == curses.KEY_DOWN:
            self.current_step = min(self.current_step + 1, 4)
        elif key == curses.KEY_UP:
            self.current_step = max(self.current_step - 1, 0)
        elif key == ord('\n'):
            if self.current_step == 2:  # 选择Boot菜单
                self.boot_mode = "UEFI" if random.random() > 0.5 else "Legacy"
            elif self.current_step == 3:  # 安全设置
                pass  # 跳过密码设置

    def main_loop(self):
        curses.curs_set(0)
        self.stdscr.timeout(100)

        # 模拟BIOS启动过程
        for i in range(3, 0, -1):
            self.stdscr.clear()
            self.stdscr.addstr(10, 30, f"Press F2 to enter BIOS... ({i})")
            self.stdscr.refresh()
            time.sleep(1)

        # 主交互循环
        while True:
            self.draw_bios_interface()
            key = self.stdscr.getch()
            if key == ord('q'):
                break
            self.handle_input(key)

            # 进入分区工具
            if self.current_step == 2 and key == ord('\n'):
                self.simulate_diskpart()
                self.disk_layout = DiskLayout.GPT
                time.sleep(2)

                # 启动系统安装
                self.run_windows_setup()

                # 完成安装
                self.stdscr.clear()
                self.stdscr.addstr(10, 30, "安装完成！请移除安装介质并重启", curses.A_BOLD)
                self.stdscr.refresh()
                time.sleep(3)
                break


if __name__ == "__main__":
    curses.wrapper(lambda stdscr: PEInstaller(stdscr).main_loop())