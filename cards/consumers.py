import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Deck, Player, UserSessions, GameTable
from django.db.models import Count
import asyncio
from time import sleep

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "game_%s" % self.room_name

        if not GameTable.objects.filter(name=self.room_name).exists():
            table = GameTable(name=self.room_name, state='')
            table.save()
        
        table = GameTable.objects.get(name=self.room_name)
        if not Deck.objects.filter(GameTable_id=table.id).exists():
            deck = Deck(GameTable_id=table.id)
            deck.create_cards(table)
            deck.save()

        if not Player.objects.filter(GameTable_id=table.id, name='Dealer').exists():
            dealer = Player(GameTable_id=table.id, name='Dealer', id_seat=0)
            dealer.save()

        # reset tout a false
        # table = GameTable.objects.get(name=self.room_name)
        # Deck.objects.filter(GameTable_id=table.id).update(excluded=False)

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        self.show_players()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    def receive(self, text_data):

        data_json = json.loads(text_data)
        if "show_players" in data_json:
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "show_players"})
        elif "start_game" in data_json:
            print("start game")
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "start"})
        elif "disconnect_user" in data_json:
            username = data_json["username"]
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "disconnect_user", 'username': username})
        elif "user" in data_json:
            user = data_json["user"]
            # if a message is sendt thats mean we are in chat 
            if "message" in data_json:
                message = data_json["message"]
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "chat", "message": message, "user": user})
        elif ("addme" in data_json):
            username = data_json["username"]
            id_seat = data_json["id_seat"]
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "addme", "username": username, "id_seat": id_seat})
        #  and len(self.players) > 2
        elif ("deal" in data_json):
            username = data_json["username"]
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "deal", 'username': username})

    # Receive message from room group
    def chat(self, event):
        user = event["user"]
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "user": user}))

    def disconnect_user(self, event):
        table = GameTable.objects.get(name=self.room_name)
        player = Player.objects.get(GameTable_id=table.id, name=event['username'])
        player_id_seat = player.id_seat
        Player.objects.get(GameTable_id=table.id, name=event['username']).delete()
        self.send(text_data=json.dumps({"disconnect": "disconnect", "player_id_seat": player_id_seat}))

    def show_players(self):
        table = GameTable.objects.get(name=self.room_name)
        players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
        for player in players:
            if player.card1 and player.card2:
                self.send(text_data=json.dumps({"player": player.name, "player_id_seat": player.id_seat, "player_chips": player.Chips, "player_cards": [
                    (player.card1.value, player.card1.suit), 
                    (player.card2.value, player.card2.suit)]}))
            else:
               self.send(text_data=json.dumps({"player": player.name, "player_id_seat": player.id_seat, "player_chips": player.Chips, "player_cards": [
                    ('', ''), 
                    ('', '')]}))

    def start(self, event):
        table = GameTable.objects.get(name=self.room_name)
        players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
        for player in players:
            deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
            player.playing = True
            player.card1 = deck[1]
            player.card2 = deck[2]
            Deck.objects.filter(id=deck[0].id).update(excluded=True)
            Deck.objects.filter(id=deck[1].id).update(excluded=True)
            player.save()
            self.send(text_data=json.dumps({"player": player.name, "player_id_seat": player.id_seat, "player_chips": player.Chips, "player_cards": [
                (player.card1.value, player.card1.suit), 
                (player.card2.value, player.card2.suit)]}))

    def deal(self, event):
        table = GameTable.objects.get(name=self.room_name)
        dealer = Player.objects.get(GameTable_id=table.id, name='Dealer')
        curr_player = Player.objects.get(GameTable_id=table.id, name=event['username'])
        curr_player.checked = True
        curr_player.save()
        players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer').exclude(playing=False)
        go_deal = True
        for player in players:
            if player.checked == False:
                go_deal = False
        old_state = table.state
        players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer').exclude(playing=False)
        for player in players:
            print(player.name)
            player.checked = False
            player.save()

        if old_state == '':
            deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
            dealer.card1 = deck[0]
            dealer.card2 = deck[1]
            dealer.card3 = deck[2]
            dealer.save()
            Deck.objects.filter(id=deck[0].id).update(excluded=True)
            Deck.objects.filter(id=deck[1].id).update(excluded=True)
            Deck.objects.filter(id=deck[2].id).update(excluded=True)

            table.state = 'flop'
            table.save()
            self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
                (dealer.card1.value, dealer.card1.suit), 
                (dealer.card2.value, dealer.card2.suit), 
                (dealer.card3.value, dealer.card3.suit)]}))
        elif old_state == 'flop':
            deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
            dealer.card4 = deck[0]
            Deck.objects.filter(id=deck[0].id).update(excluded=True)
            dealer.save()
            table.state = 'turn'
            table.save()
            self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
                (dealer.card1.value, dealer.card1.suit), 
                (dealer.card2.value, dealer.card2.suit), 
                (dealer.card3.value, dealer.card3.suit),
                (dealer.card4.value, dealer.card4.suit)]}))
        elif old_state == 'turn':
            deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)

            dealer.card5 = deck[0]
            Deck.objects.filter(id=deck[0].id).update(excluded=True)
            dealer.save()
            table.state = 'river'
            table.save()
            self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
                (dealer.card1.value, dealer.card1.suit), 
                (dealer.card2.value, dealer.card2.suit), 
                (dealer.card3.value, dealer.card3.suit),
                (dealer.card4.value, dealer.card4.suit),                
                (dealer.card5.value, dealer.card5.suit)]}))
        elif old_state == 'river':
            table.state = ''
            table.save()
            Deck.objects.filter(GameTable_id=table.id, excluded=True).update(excluded=False)
            dealer = Player.objects.get(GameTable_id=table.id, name='Dealer')
            dealer.card1 = None
            dealer.card2 = None
            dealer.card3 = None
            dealer.card4 = None
            dealer.card5 = None
            dealer.save()
            players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
            buttons = []
            for player in players:
                player.card1 = None
                player.card2 = None
                player.playing = True
                buttons.append(player.button_id) 
                player.save()
            self.send(text_data=json.dumps({"table_state": old_state, "buttons_id": buttons}))

    def addme(self, event):
        table = GameTable.objects.get(name=self.room_name)
        if not Player.objects.filter(GameTable_id=table.id, name=event["username"]).exists():
            new_player = (Player(GameTable_id=table.id, name=event["username"], id_seat=event["id_seat"]))
            new_player.save()
            self.send(text_data=json.dumps({"player": new_player.name, "id_seat": event['id_seat']}))
        else:
            print('player already exist')

# import json
# from channels.generic.websocket import WebsocketConsumer
# from asgiref.sync import async_to_sync
# from .models import Deck, Player, UserSessions, GameTable
# from django.db.models import Count
# import asyncio
# from time import sleep

# class GameConsumer(WebsocketConsumer):
#     def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = "game_%s" % self.room_name

#         if not GameTable.objects.filter(name=self.room_name).exists():
#             table = GameTable(name=self.room_name, state='')
#             table.save()
        
#         table = GameTable.objects.get(name=self.room_name)
#         if not Deck.objects.filter(GameTable_id=table.id).exists():
#             deck = Deck(GameTable_id=table.id)
#             deck.create_cards(table)
#             deck.save()

#         if not Player.objects.filter(GameTable_id=table.id, name='Dealer').exists():
#             dealer = Player(GameTable_id=table.id, name='Dealer', id_seat=0)
#             dealer.save()

#         # reset tout a false
#         # table = GameTable.objects.get(name=self.room_name)
#         # Deck.objects.filter(GameTable_id=table.id).update(excluded=False)

#         async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
#         self.accept()
#         self.show_players()

#     def disconnect(self, close_code):
#         # Leave room group
#         async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

#     # Receive message from WebSocket
#     def receive(self, text_data):

#         data_json = json.loads(text_data)
#         if "show_players" in data_json:
#             async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "show_players"})
#         elif "start_game" in data_json:
#             print("start game")
#             async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "start"})
#         elif "disconnect_user" in data_json:
#             username = data_json["username"]
#             async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "disconnect_user", 'username': username})
#         elif "check" in data_json:
#             username = data_json["username"]
#             async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "check", 'username': username})
#         elif "user" in data_json:
#             user = data_json["user"]
#             # if a message is sendt thats mean we are in chat 
#             if "message" in data_json:
#                 message = data_json["message"]
#                 async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "chat", "message": message, "user": user})
#         elif ("addme" in data_json):
#             username = data_json["username"]
#             id_seat = data_json["id_seat"]
#             async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "addme", "username": username, "id_seat": id_seat})
#         #  and len(self.players) > 2
#         elif ("deal" in data_json):
#             async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "deal"})

#     # Receive message from room group
#     def chat(self, event):
#         user = event["user"]
#         message = event["message"]

#         # Send message to WebSocket
#         self.send(text_data=json.dumps({"message": message, "user": user}))

#     def disconnect_user(self, event):
#         table = GameTable.objects.get(name=self.room_name)
#         player = Player.objects.get(GameTable_id=table.id, name=event['username'])
#         player_id_seat = player.id_seat
#         Player.objects.get(GameTable_id=table.id, name=event['username']).delete()
#         self.send(text_data=json.dumps({"disconnect": "disconnect", "player_id_seat": player_id_seat}))

#     def show_players(self):
#         table = GameTable.objects.get(name=self.room_name)
#         players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
#         for player in players:
#             if player.card1 and player.card2:
#                 self.send(text_data=json.dumps({"player": player.name, "player_id_seat": player.id_seat, "player_chips": player.Chips, "player_cards": [
#                     (player.card1.value, player.card1.suit), 
#                     (player.card2.value, player.card2.suit)]}))
#             else:
#                self.send(text_data=json.dumps({"player": player.name, "player_id_seat": player.id_seat, "player_chips": player.Chips, "player_cards": [
#                     ('', ''), 
#                     ('', '')]}))

#     def start(self, event):
#         table = GameTable.objects.get(name=self.room_name)
#         players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
#         for player in players:
#             deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
#             player.playing = True
#             player.card1 = deck[1]
#             player.card2 = deck[2]
#             Deck.objects.filter(id=deck[0].id).update(excluded=True)
#             Deck.objects.filter(id=deck[1].id).update(excluded=True)
#             player.save()
#             self.send(text_data=json.dumps({"player": player.name, "player_id_seat": player.id_seat, "player_chips": player.Chips, "player_cards": [
#                 (player.card1.value, player.card1.suit), 
#                 (player.card2.value, player.card2.suit)]}))

#     def check(self, event):
#         table = GameTable.objects.get(name=self.room_name)
#         curr_player = Player.objects.get(GameTable_id=table.id, name=event['username'])
#         curr_player.checked = True
#         curr_player.save()
#         players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer').exclude(playing=False)
#         go_deal = True
#         for player in players:
#             if player.checked == False:
#                 go_deal = False

#         if go_deal:
#             async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "deal"})

#     def deal(self, event):
#         table = GameTable.objects.get(name=self.room_name)
#         dealer = Player.objects.get(GameTable_id=table.id, name='Dealer')

#         old_state = table.state
#         players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer').exclude(playing=False)
#         for player in players:
#             print(player.name)
#             player.checked = False
#             player.save()

#         if old_state == '':
#             deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
#             dealer.card1 = deck[0]
#             dealer.card2 = deck[1]
#             dealer.card3 = deck[2]
#             dealer.save()
#             Deck.objects.filter(id=deck[0].id).update(excluded=True)
#             Deck.objects.filter(id=deck[1].id).update(excluded=True)
#             Deck.objects.filter(id=deck[2].id).update(excluded=True)

#             table.state = 'flop'
#             table.save()
#             self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
#                 (dealer.card1.value, dealer.card1.suit), 
#                 (dealer.card2.value, dealer.card2.suit), 
#                 (dealer.card3.value, dealer.card3.suit)]}))
#         elif old_state == 'flop':
#             deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
#             dealer.card4 = deck[0]
#             Deck.objects.filter(id=deck[0].id).update(excluded=True)
#             dealer.save()
#             table.state = 'turn'
#             table.save()
#             self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
#                 (dealer.card1.value, dealer.card1.suit), 
#                 (dealer.card2.value, dealer.card2.suit), 
#                 (dealer.card3.value, dealer.card3.suit),
#                 (dealer.card4.value, dealer.card4.suit)]}))
#         elif old_state == 'turn':
#             deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)

#             dealer.card5 = deck[0]
#             Deck.objects.filter(id=deck[0].id).update(excluded=True)
#             dealer.save()
#             table.state = 'river'
#             table.save()
#             self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
#                 (dealer.card1.value, dealer.card1.suit), 
#                 (dealer.card2.value, dealer.card2.suit), 
#                 (dealer.card3.value, dealer.card3.suit),
#                 (dealer.card4.value, dealer.card4.suit),                
#                 (dealer.card5.value, dealer.card5.suit)]}))
#         elif old_state == 'river':
#             table.state = ''
#             table.save()
#             Deck.objects.filter(GameTable_id=table.id, excluded=True).update(excluded=False)
#             dealer = Player.objects.get(GameTable_id=table.id, name='Dealer')
#             dealer.card1 = None
#             dealer.card2 = None
#             dealer.card3 = None
#             dealer.card4 = None
#             dealer.card5 = None
#             dealer.save()
#             players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
#             buttons = []
#             for player in players:
#                 player.card1 = None
#                 player.card2 = None
#                 player.playing = True
#                 buttons.append(player.button_id) 
#                 player.save()
#             self.send(text_data=json.dumps({"table_state": old_state, "buttons_id": buttons}))

#     def addme(self, event):
#         table = GameTable.objects.get(name=self.room_name)
#         if not Player.objects.filter(GameTable_id=table.id, name=event["username"]).exists():
#             new_player = (Player(GameTable_id=table.id, name=event["username"], id_seat=event["id_seat"]))
#             new_player.save()
#             self.send(text_data=json.dumps({"player": new_player.name, "id_seat": event['id_seat']}))
#         else:
#             print('player already exist')

