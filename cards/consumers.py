import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Deck, Player, UserSessions, GameTable
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
            dealer = Player(GameTable_id=table.id, name='Dealer')
            dealer.save()

        # reset tout a false
        # table = GameTable.objects.get(name=self.room_name)
        # Deck.objects.filter(GameTable_id=table.id).update(excluded=False)

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    def receive(self, text_data):

        data_json = json.loads(text_data)
        if "user" in data_json:
            user = data_json["user"]
            # if a message is sendt thats mean we are in chat 
            if "message" in data_json:
                message = data_json["message"]
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "chat", "message": message, "user": user})
        elif ("addme" in data_json):
            username = data_json["username"]
            button_id = data_json["button_id"]
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "addme", "username": username, "button_id": button_id})
        #  and len(self.players) > 2
        elif ("deal" in data_json):
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type": "deal"})

    # Receive message from room group
    def chat(self, event):
        user = event["user"]
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "user": user}))

    def deal(self, event):
        table = GameTable.objects.get(name=self.room_name)
        dealer = Player.objects.get(GameTable_id=table.id, name='Dealer')

        old_state = table.state
        if old_state == '':
            players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
            for player in players:
                deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
                player.Card1 = deck[0]
                player.Card2 = deck[1]
                Deck.objects.filter(id=deck[0].id).update(excluded=True)
                Deck.objects.filter(id=deck[1].id).update(excluded=True)
                player.save() 
                self.send(text_data=json.dumps({"player": player.name, "player_button_id": player.button_id, "player_cards": [
                    (player.Card1.value, player.Card1.suit), 
                    (player.Card2.value, player.Card2.suit)]}))

            deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
            dealer.Card1 = deck[0]
            dealer.Card2 = deck[1]
            dealer.Card3 = deck[2]
            dealer.save()
            Deck.objects.filter(id=deck[0].id).update(excluded=True)
            Deck.objects.filter(id=deck[1].id).update(excluded=True)
            Deck.objects.filter(id=deck[2].id).update(excluded=True)

            table.state = 'flop'
            table.save()
            self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
                (dealer.Card1.value, dealer.Card1.suit), 
                (dealer.Card2.value, dealer.Card2.suit), 
                (dealer.Card3.value, dealer.Card3.suit)]}))
        elif old_state == 'flop':
            deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)
            dealer.Card4 = deck[0]
            Deck.objects.filter(id=deck[0].id).update(excluded=True)
            dealer.save()
            table.state = 'turn'
            table.save()
            self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
                (dealer.Card1.value, dealer.Card1.suit), 
                (dealer.Card2.value, dealer.Card2.suit), 
                (dealer.Card3.value, dealer.Card3.suit),
                (dealer.Card4.value, dealer.Card4.suit)]}))
        elif old_state == 'turn':
            deck = Deck.objects.filter(GameTable_id=table.id, excluded=False)

            dealer.Card5 = deck[0]
            Deck.objects.filter(id=deck[0].id).update(excluded=True)
            dealer.save()
            table.state = 'river'
            table.save()
            self.send(text_data=json.dumps({"table_state": old_state, "dealer_cards": [
                (dealer.Card1.value, dealer.Card1.suit), 
                (dealer.Card2.value, dealer.Card2.suit), 
                (dealer.Card3.value, dealer.Card3.suit),
                (dealer.Card4.value, dealer.Card4.suit),                
                (dealer.Card5.value, dealer.Card5.suit)]}))
        elif old_state == 'river':
            table.state = ''
            table.save()
            Deck.objects.filter(GameTable_id=table.id, excluded=True).update(excluded=False)
            dealer = Player.objects.get(GameTable_id=table.id, name='Dealer')
            dealer.Card1 = None
            dealer.Card2 = None
            dealer.Card3 = None
            dealer.Card4 = None
            dealer.Card5 = None
            dealer.save()
            players = Player.objects.filter(GameTable_id=table.id).exclude(name='Dealer')
            buttons = []
            for player in players:
                player.Card1 = None
                player.Card2 = None
                buttons.append(player.button_id) 
                player.save()
            self.send(text_data=json.dumps({"table_state": old_state, "buttons_id": buttons}))

    def addme(self, event):
        print("avant le new player")
        table = GameTable.objects.get(name=self.room_name)
        if not Player.objects.filter(GameTable_id=table.id, name=event["username"]).exists():
            new_player = (Player(GameTable_id=table.id, name=event["username"]))
            new_player.button_id = event['button_id']
            new_player.save()
            self.send(text_data=json.dumps({"player": new_player.name, "button_id": event['button_id']}))
        else:
            print('player already exist')

