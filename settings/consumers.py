import json
import random
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from collections import defaultdict
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from game.services import BasedFight
from game.logs import get_text_effect, select_log
from game.models import Room
from users.models import NewUser

class RoomDeleteConsumer(AsyncWebsocketConsumer):
    connected = defaultdict(lambda: [])
    
    @database_sync_to_async
    def delete_room(self):
        try:
            Room.objects.get(pk = int(self.room_name)).delete()
            del RoomDeleteConsumer.connected[self.room_group_name]
        except Room.DoesNotExist:
            pass

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        RoomDeleteConsumer.connected[self.room_group_name].append(self.channel_layer)
        if len(RoomDeleteConsumer.connected[self.room_group_name]) > 1:
            await self.delete_room()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


class ChatConsumer(AsyncWebsocketConsumer):
    room_connection_counts = defaultdict(lambda: {})

    @database_sync_to_async
    def get_user(self):
        user = get_user_model().objects.get(pk=self.user)
        return {'name': user.get_username(), 'lvl': user.lvl}


    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['url_route']['kwargs']['user']
        self.room_group_name = 'chat_%s' % self.room_name
        ChatConsumer.room_connection_counts[self.room_name][self.user] = await self.get_user()
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        connected_users = ChatConsumer.room_connection_counts[self.room_name]
        await self.accept()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_users',
                'users': connected_users
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        del ChatConsumer.room_connection_counts[self.room_name][self.user]
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_users',
                'users': ChatConsumer.room_connection_counts[self.room_name]
            }
        )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {"user": ChatConsumer.room_connection_counts[self.room_name][self.user], "message": message}
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def update_users(self, event):
        users = event['users']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'users': users
        }))


class BattleConsumer(AsyncWebsocketConsumer):
    battle_players = defaultdict(lambda: {})
    fight_selection = defaultdict(lambda: {})
    group_timers = defaultdict(lambda: asyncio.Task)
    logs = defaultdict(lambda: [])

    @database_sync_to_async
    def get_user(self):
        user = get_user_model().objects.get(pk=self.user)
        return {'name': user.get_username(), 'lvl': user.lvl}
    
    @database_sync_to_async
    def get_room(self):
        room = Room.objects.select_related("second_player", "first_player").get(pk=self.room_name)
        return room
    
    @database_sync_to_async
    def get_effects_count(self, obj: NewUser):
        return obj.effect_set.all().count()

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.user = int(self.scope['url_route']['kwargs']['user'])
        self.room_group_name = 'battle_%s' % self.room_name
        self.current_timer = None
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        room = await self.get_room()
        BattleConsumer.battle_players[self.room_group_name][room.first_player.id] = room.first_player
        if room.second_player != None:
            if room.second_player.id == int(self.user):
                self.second_user = room.first_player.id
            else:
                self.second_user = room.second_player.id
            BattleConsumer.battle_players[self.room_group_name][room.second_player.id] = room.second_player
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'connected_person',
                    'is_connected': True
                }
            )
        await self.send(text_data=json.dumps({
            "selected": BattleConsumer.fight_selection[self.room_group_name].get(self.user, None),
            "logs": BattleConsumer.logs[self.room_group_name]
        }))
        
    async def get_entity_effect(self, who: NewUser, whom: NewUser) -> None:
        if await self.get_effects_count(whom) > 3:  # pylint: disable=R1705
            return
        if who.role in ["agility", "shooter"] and random.randint(0, 100) < 5:
            BasedFight.async_apply_effect("Кровотеча", whom, 2)
            BattleConsumer.logs[self.room_group_name].append(get_text_effect(who.get_name(), whom.get_name(), "bliding"))
        elif who.role == "strength" and random.randint(0, 100) < 8:
            BasedFight.async_apply_effect("Перелом кістки", whom, 2)
            BattleConsumer.logs[self.room_group_name].append(get_text_effect(who.get_name(), whom.get_name(), "bones"))

    async def attack(self, who: NewUser, whom: NewUser) -> int:
        total_dmg = await who.async_return_all_damage_taken()
        total_defence = await whom.async_return_all_defence()
        attack = round(total_dmg - total_defence if total_defence < total_dmg else 1)
        attack_selection = BattleConsumer.fight_selection[self.room_group_name][who.id]['attack']
        defence_selection = BattleConsumer.fight_selection[self.room_group_name][whom.id]['defence']
        if attack_selection is not None and attack_selection != defence_selection:
            if whom.health - attack > 0:
                whom.health -= attack
            else:
                whom.health = 0
                self.is_winner = True
        else:
            attack = 0
        await self.get_entity_effect(who, whom)
        await whom.asave(update_fields=['health'])
        return attack

    async def disconnect(self, close_code):
        room = await self.get_room()
        if room.second_player == None:
            await room.adelete()
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # Send message to room group
        await self.send_waiting(text_data_json)

    async def send_waiting(self, data):
        BattleConsumer.fight_selection[self.room_group_name][self.user] = data
        if self.second_user not in BattleConsumer.fight_selection[self.room_group_name].keys():
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_is_ready',
                    'id': self.second_user
                }
            )    
            BattleConsumer.group_timers[self.room_group_name] = asyncio.create_task(self.timer_send())
        else: 
            await self.attack_process()            


    async def attack_process(self):
        if BattleConsumer.group_timers[self.room_group_name] is not None:
            BattleConsumer.group_timers[self.room_group_name].cancel()
        who = BattleConsumer.battle_players[self.room_group_name][self.second_user]
        whom = BattleConsumer.battle_players[self.room_group_name][self.user]
        if who.role == "agility":
            if random.randint(0, 100) < 5:
                dmg = await self.attack(who, whom)
                log = select_log(who=who.username,
                                    whom=whom.username,
                                    attack_type="agility", dmg=dmg)
                BattleConsumer.logs[self.room_group_name].append(log)
                await self.send_log_and_data(who, whom, log)
                return
        if whom.role == "agility":
            if random.randint(0, 100) < 5:
                dmg = await self.attack(whom, who)
                log = select_log(who=whom,
                                whom=who,
                                attack_type="agility", dmg=dmg)
                BattleConsumer.logs[self.room_group_name].append(log)
                await self.send_log_and_data(who, whom, log)
                return
        dmg = await self.attack(whom, who)
        log = select_log(who=whom.username,
                            whom=who.username,
                            dmg=dmg)
        BattleConsumer.logs[self.room_group_name].append(log)
        await self.send_log_and_data(who, whom, log)
        dmg = await self.attack(who, whom)
        log = select_log(who=who.username,
                            whom=whom.username,
                            dmg=dmg)
        BattleConsumer.logs[self.room_group_name].append(log)
        await self.send_log_and_data(who, whom, log)
        del BattleConsumer.fight_selection[self.room_group_name]

    async def send_log_and_data(self, who: NewUser, whom: NewUser, log: str):
        if who.health == 0 or whom.health == 0:
            is_finish = True
            BattleConsumer.logs.pop(self.room_group_name, None)
            BattleConsumer.battle_players.pop(self.room_group_name, None)
            BattleConsumer.group_timers.pop(self.room_group_name, None)
        else:
            is_finish = False
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_attack_result",
                "attack_data": json.dumps({
                    "id": self.user,
                    "enemy_hp": whom.health,
                    "user_hp": who.health,
                    "user_stats": await who.async_get_summary_stats(),
                    "enemy_stats": await whom.async_get_summary_stats(),
                    "is_finish": is_finish,
                    "log": log
                })
            }
        )

    async def timer_send(self):
        for i in range(10, 0, -1):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_test",
                    "time": i,
                    "id": self.second_user
                }        
            )
            await asyncio.sleep(1)
        BattleConsumer.fight_selection[self.room_group_name][self.second_user] = {
            "attack": None,
            "defence": None
        }
        asyncio.create_task(self.attack_process())

    async def send_is_ready(self, event):
        await self.send(text_data=json.dumps({
            'is_ready': {int(event['id']): True}
        }))

    async def send_test(self, event):
        await self.send(text_data=json.dumps({
            'time': {int(event['id']): int(event['time'])}
        }))

    async def send_attack_result(self, event):
        await self.send(text_data=json.dumps({"attack_data": event['attack_data']}))

    async def connected_person(self, event):
        message = event['is_connected']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'is_connected': message
        }))