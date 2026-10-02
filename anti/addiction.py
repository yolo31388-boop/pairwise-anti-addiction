"""防沉迷系统"""
from dataclasses import dataclass
from datetime import date, datetime

DAILY_PLAY_LIMIT_MINUTES = 120
DAILY_CONSUMPTION_LIMIT = 200

# 实名认证权威库（模拟公安库）：身份证号 -> 姓名
_ID_REGISTRY = {
    "110101199001011234": "张三",
}


@dataclass
class PlayerState:
    pid: str
    is_adult: bool = False
    play_time_today: int = 0  # 分钟
    device_id: str = ""
    consumption_today: int = 0
    last_active_date: date | None = None  # 服务端记录的最近活跃日期


class AntiAddictionSystem:
    def __init__(self):
        self.players: dict[str, PlayerState] = {}
        self.last_reset: datetime = None

    def _server_now(self) -> datetime:
        # 统一使用服务端时间，防止客户端篡改系统时间绕过限制
        return datetime.now()

    def _refresh_daily(self, player: PlayerState) -> None:
        # 跨天自动重置当天累计（游戏时长与消费）
        today = self._server_now().date()
        if player.last_active_date is None:
            player.last_active_date = today
        elif player.last_active_date != today:
            player.play_time_today = 0
            player.consumption_today = 0
            player.last_active_date = today
            self.last_reset = self._server_now()

    def update_play_time(self, pid: str, minutes: int, device_id: str) -> bool:
        # 按账号统计游戏时间，与设备无关；换设备不清零
        player = self.players.get(pid)
        if player is None:
            player = PlayerState(pid, device_id=device_id)
            self.players[pid] = player
        self._refresh_daily(player)
        player.play_time_today += minutes
        return True

    def verify_id_card(self, name: str, id_card: str) -> bool:
        # 校验格式，并与权威库比对姓名和身份证号是否匹配
        if not self._is_valid_id_format(id_card):
            return False
        return _ID_REGISTRY.get(id_card) == name

    @staticmethod
    def _is_valid_id_format(id_card: str) -> bool:
        if len(id_card) != 18:
            return False
        if not id_card[:17].isdigit():
            return False
        if not (id_card[17].isdigit() or id_card[17] in "Xx"):
            return False
        try:
            datetime.strptime(id_card[6:14], "%Y%m%d")
        except ValueError:
            return False
        return True

    def check_consumption_limit(self, pid: str, amount: int) -> bool:
        # 按当天累计消费金额限制，防止拆单绕过限额
        player = self.players.get(pid)
        if player is None:
            return amount <= DAILY_CONSUMPTION_LIMIT
        self._refresh_daily(player)
        return player.consumption_today + amount <= DAILY_CONSUMPTION_LIMIT

    def check_time_limit(self, pid: str, current_time: datetime) -> bool:
        # 使用服务端时间校验，忽略客户端传入的 current_time（可被篡改）
        player = self.players.get(pid)
        if not player or player.is_adult:
            return True
        self._refresh_daily(player)
        return player.play_time_today < DAILY_PLAY_LIMIT_MINUTES

    def migrate_guest_time(self, guest_id: str, player_id: str) -> bool:
        # 游客转正式账号时继承游戏时间与消费，防止换号清零无限玩
        guest = self.players.get(guest_id)
        if guest is None:
            return False
        self._refresh_daily(guest)
        player = self.players.get(player_id)
        if player is None:
            player = PlayerState(player_id)
            self.players[player_id] = player
        else:
            self._refresh_daily(player)
        player.play_time_today += guest.play_time_today
        player.consumption_today += guest.consumption_today
        player.is_adult = player.is_adult or guest.is_adult
        del self.players[guest_id]
        return True
