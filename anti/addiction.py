"""防沉迷系统"""
from dataclasses import dataclass, field
from datetime import date, datetime


def _today() -> date:
    return date.today()


@dataclass
class PlayerState:
    pid: str
    is_adult: bool = False
    play_time_today: int = 0  # 分钟
    device_id: str = ""
    consumption_today: int = 0
    last_play_date: date = field(default_factory=_today)
    last_consumption_date: date = field(default_factory=_today)


class AntiAddictionSystem:
    DAILY_PLAY_LIMIT_MINUTES = 120
    DAILY_CONSUMPTION_LIMIT = 200

    # 模拟实名认证库：身份证号 -> 姓名（生产环境应调用实名认证接口）
    _ID_REGISTRY = {
        "110101199001011234": "张三",
    }

    def __init__(self):
        self.players: dict[str, PlayerState] = {}
        self.last_reset: datetime = None

    @staticmethod
    def _server_now() -> datetime:
        # 服务端时间，不信任客户端上报的时间
        return datetime.now()

    def _reset_if_new_day(self, player: PlayerState) -> None:
        today = _today()
        if player.last_play_date != today:
            player.play_time_today = 0
            player.last_play_date = today
            self.last_reset = self._server_now()
        if player.last_consumption_date != today:
            player.consumption_today = 0
            player.last_consumption_date = today
            self.last_reset = self._server_now()

    def update_play_time(self, pid: str, minutes: int, device_id: str) -> bool:
        # 按账号统计游戏时间，与设备无关，换设备不清零
        player = self.players.get(pid)
        if player is None:
            player = PlayerState(pid)
            self.players[pid] = player
        self._reset_if_new_day(player)
        player.play_time_today += minutes
        player.device_id = device_id
        return True

    def verify_id_card(self, name: str, id_card: str) -> bool:
        if not self._is_valid_id_format(id_card):
            return False
        # 验证身份证号与姓名是否匹配，只格式合法不够
        return self._ID_REGISTRY.get(id_card) == name

    @staticmethod
    def _is_valid_id_format(id_card: str) -> bool:
        if len(id_card) != 18:
            return False
        body, check = id_card[:17], id_card[17]
        return body.isdigit() and (check.isdigit() or check in "Xx")

    def check_consumption_limit(self, pid: str, amount: int) -> bool:
        # 按当日累计消费限额，分多笔也无法绕过
        player = self.players.get(pid)
        if player is None:
            player = PlayerState(pid)
            self.players[pid] = player
        self._reset_if_new_day(player)
        if player.consumption_today + amount > self.DAILY_CONSUMPTION_LIMIT:
            return False
        player.consumption_today += amount
        return True

    def check_time_limit(self, pid: str, current_time: datetime = None) -> bool:
        # 使用服务端时间做跨天重置与判断，忽略客户端传入的 current_time，
        # 防止修改系统时间绕过限制
        player = self.players.get(pid)
        if not player or player.is_adult:
            return True
        self._reset_if_new_day(player)
        return player.play_time_today < self.DAILY_PLAY_LIMIT_MINUTES

    def migrate_guest_time(self, guest_id: str, player_id: str) -> bool:
        if guest_id == player_id:
            return True
        guest = self.players.get(guest_id)
        if guest is None:
            return False
        self._reset_if_new_day(guest)
        player = self.players.get(player_id)
        if player is None:
            player = PlayerState(player_id)
            self.players[player_id] = player
        self._reset_if_new_day(player)
        # 游客转正式账号后继承当日累计时长与消费，不从零开始
        player.play_time_today += guest.play_time_today
        player.consumption_today += guest.consumption_today
        del self.players[guest_id]
        return True
