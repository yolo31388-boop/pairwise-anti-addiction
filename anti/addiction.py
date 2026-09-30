"""防沉迷系统 - 含5个bug"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class PlayerState:
    pid: str
    is_adult: bool = False
    play_time_today: int = 0  # 分钟
    device_id: str = ""
    consumption_today: int = 0

class AntiAddictionSystem:
    def __init__(self):
        self.players: dict[str, PlayerState] = {}
        self.last_reset: datetime = None  # bug1: 跨天不重置

    def update_play_time(self, pid: str, minutes: int, device_id: str) -> bool:
        # bug1: 按设备统计不按账号
        if pid not in self.players:
            self.players[pid] = PlayerState(pid, device_id=device_id)
        self.players[pid].play_time_today += minutes
        return True

    def verify_id_card(self, name: str, id_card: str) -> bool:
        # bug2: 只检查格式不验证匹配
        if len(id_card) == 18:
            return True
        return False

    def check_consumption_limit(self, pid: str, amount: int) -> bool:
        # bug3: 只检查单笔不检查累计
        return amount <= 200

    def check_time_limit(self, pid: str, current_time: datetime) -> bool:
        # bug4: 用客户端时间
        player = self.players.get(pid)
        if not player or player.is_adult:
            return True
        return player.play_time_today < 120

    def migrate_guest_time(self, guest_id: str, player_id: str) -> bool:
        # bug5: 游客时间不继承
        return True
