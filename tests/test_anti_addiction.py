"""防沉迷系统 - 红态测试"""
import pytest, sys, os
from datetime import datetime, date, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from anti.addiction import AntiAddictionSystem, PlayerState

class TestAccountLevelTracking:
    def test_play_time_tracked_by_account_not_device(self):
        aas = AntiAddictionSystem()
        aas.players["p1"] = PlayerState("p1", play_time_today=60)
        aas.update_play_time("p1", 30, "device2")
        assert aas.players["p1"].play_time_today == 90

class TestIDVerification:
    def test_name_and_id_must_match(self):
        aas = AntiAddictionSystem()
        assert aas.verify_id_card("张三", "110101199001011234") == True
        assert aas.verify_id_card("李四", "110101199001011234") == False

class TestCumulativeConsumption:
    def test_daily_consumption_limit_cumulative(self):
        aas = AntiAddictionSystem()
        aas.players["p1"] = PlayerState("p1", consumption_today=150)
        assert aas.check_consumption_limit("p1", 100) == False

class TestServerTime:
    def test_uses_server_time_not_client(self):
        aas = AntiAddictionSystem()
        aas.players["p1"] = PlayerState("p1", is_adult=False, play_time_today=130)
        assert aas.check_time_limit("p1", datetime.now()) == False

    def test_client_time_spoof_cannot_bypass(self):
        aas = AntiAddictionSystem()
        aas.players["p1"] = PlayerState("p1", is_adult=False, play_time_today=130)
        spoofed = datetime.now() - timedelta(days=1)
        assert aas.check_time_limit("p1", spoofed) == False


class TestDailyReset:
    def test_play_time_resets_across_days(self):
        aas = AntiAddictionSystem()
        aas.players["p1"] = PlayerState("p1", play_time_today=100)
        aas.players["p1"].last_play_date = date.today() - timedelta(days=1)
        aas.update_play_time("p1", 10, "device1")
        assert aas.players["p1"].play_time_today == 10

    def test_consumption_resets_across_days(self):
        aas = AntiAddictionSystem()
        aas.players["p1"] = PlayerState("p1", consumption_today=200)
        aas.players["p1"].last_consumption_date = date.today() - timedelta(days=1)
        assert aas.check_consumption_limit("p1", 100) == True
        assert aas.players["p1"].consumption_today == 100


class TestMultiPurchase:
    def test_split_purchases_cannot_evade_limit(self):
        aas = AntiAddictionSystem()
        aas.players["p1"] = PlayerState("p1")
        assert aas.check_consumption_limit("p1", 100) == True
        assert aas.check_consumption_limit("p1", 100) == True
        assert aas.check_consumption_limit("p1", 100) == False


class TestGuestMigration:
    def test_guest_play_time_migrated(self):
        aas = AntiAddictionSystem()
        aas.players["guest1"] = PlayerState("guest1", play_time_today=50)
        aas.migrate_guest_time("guest1", "player1")
        assert "player1" in aas.players
        assert aas.players["player1"].play_time_today == 50

    def test_guest_record_removed_after_migration(self):
        aas = AntiAddictionSystem()
        aas.players["guest1"] = PlayerState("guest1", play_time_today=50)
        aas.migrate_guest_time("guest1", "player1")
        assert "guest1" not in aas.players
