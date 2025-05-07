from django.db import models
import json

class Room(models.Model):
    room_id = models.CharField(max_length=3, unique=True)
    host_name = models.CharField(max_length=50, blank=True)
    players = models.TextField(default='[]')  # JSONリストを文字列で保存

    def add_player(self, name):
        current = json.loads(self.players)
        if name not in current:
            current.append(name)
            self.players = json.dumps(current)
            self.save()

    def get_players(self):
        return json.loads(self.players)
