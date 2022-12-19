from django.db import models
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth.models import User
import random

class GameTable(models.Model):
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    # chipsOnTable = models.IntegerField(null=True)

class Deck(models.Model):
    suit = models.CharField(max_length = 30)
    value = models.CharField(max_length = 10)
    excluded = models.BooleanField(default=False)
    GameTable = models.ForeignKey(GameTable, on_delete=models.CASCADE)

    def create_cards(self, id_gametable):
        suits = ['Coeur', 'Carreau', 'Pique', 'Trefle']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Valet', 'Dame', 'Roi', 'As']
        deck = [Deck(suit=suit, value=value, GameTable=id_gametable) for value in values for suit in suits]
        random.shuffle(deck)
        Deck.objects.bulk_create(deck)

    # Return the top card
    def deal(self):
        return self.cards.pop()

class Player(models.Model):
    name = models.CharField(max_length=255)
    button_id = models.CharField(max_length=255, null=True)
    id_seat = models.IntegerField()
    checked = models.BooleanField(default=False)
    playing = models.BooleanField(default=False)
    card1 = models.ForeignKey(Deck, related_name='one', on_delete=models.CASCADE, null=True)
    card2 = models.ForeignKey(Deck, related_name='two', on_delete=models.CASCADE, null=True)
    card3 = models.ForeignKey(Deck, related_name='tree', on_delete=models.CASCADE, null=True)
    card4 = models.ForeignKey(Deck, related_name='fourth', on_delete=models.CASCADE, null=True)
    card5 = models.ForeignKey(Deck, related_name='five', on_delete=models.CASCADE, null=True)
    Chips = models.IntegerField(default=1000)
    GameTable = models.ForeignKey(GameTable, on_delete=models.CASCADE)

class UserSessions(object):
    def get_current_users():
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_id_list = []
        for session in active_sessions:
            data = session.get_decoded()
            user_id_list.append(data.get('_auth_user_id', None))
        # Query all logged in users based on id list
        return User.objects.filter(id__in=user_id_list)


# from django.db import models
# import random
# from django.contrib.auth.models import AbstractUser
# from django.contrib.sessions.models import Session
# from django.utils import timezone
# from django.contrib.auth.models import User
# import json
# from json import JSONEncoder


# from collections import OrderedDict
# import random

# from channels.generic.websocket import AsyncWebsocketConsumer

# PENDING = 'PENDING'
# RUNNING = 'RUNNING'
# MAX_PLAYERS = 9
# SMALL_BLIND = 10
# BIG_BLIND = 20

# class Card(models.Model):
#     suit = models.CharField(max_length = 30)
#     value = models.CharField(max_length = 10)

#     def __init__(self, suit, val):
#         self.suit = suit
#         self.value = val
        
#     def show(self):
#         if self.value == '1':
#             val = "As"
#         elif self.value == '11':
#             val = "Valet"
#         elif self.value == '12':
#             val = "Dame"
#         elif self.value == '13':
#             val = "Roi"
#         else:
#             val = self.value
#         return (val, self.suit)

#     def toJSON(self):
#         return (self.suit, self.value)


# class Deck(object):
#     def __init__(self):
#         self.cards = []
#         self.build()
#         self.shuffle()

#     # Display all cards in the deck
#     def show(self):
#         ret = []
#         for card in self.cards:
#             ret.append(card.show())
#         return ret

#     # Generate 52 cards
#     def build(self):
#         self.cards = []
#         for suit in ['Coeur', 'Carreau', 'Pique', 'Trefle']:
#             for val in range(1,14):
#                 self.cards.append(Card(suit, val))

#     # Shuffle the deck
#     def shuffle(self, num=1):
#         length = len(self.cards)
#         for _ in range(num):
#             # This is the fisher yates shuffle algorithm
#             for i in range(length - 1, 0, -1):
#                 randi = random.randint(0, i)
#                 if i == randi:
#                     continue
#                 self.cards[i], self.cards[randi] = self.cards[randi], self.cards[i]

#     # Return the top card
#     def deal(self):
#         return self.cards.pop()


# class Player(object):
#     def __init__(self, name):
#         self.name = name
#         self.hand = []

#     # Draw n number of cards from a deck
#     # Returns true in n cards are drawn, false if less then that
#     def draw(self, deck, num=1):
#         for _ in range(num):
#             card = deck.deal()
#             if card:
#                 self.hand.append(card)
#             else: 
#                 return False
#         return True

#     # Return all the cards in the players hand
#     def showHand(self):
#         ret = []
#         for card in self.hand:
#             ret.append(card.show())
#         return ret

#     def discard(self):
#         self.hand.pop()
#         return self

#     def discardAll(self):
#         self.hand.clear()
#         return self

#     def set_table(self, table_name):
#         self.table = table_name
    
#     def get_table(self):
#         return self.table

#     def toJSON(self):
#         data = []
#         print(self.hand)
#         for card in self.hand:
#             print (card)
#             data = card.suit[0], card.value[1]
#         print (data)
#         return data

# class GameTable:
#     def __init__(self, table_name):
#         self.name = table_name
#         self.dealer = Player('Dealer')
#         self.deck = Deck()
#         self.state = ''
#         self.players = []

# class UserSessions(object):
#     def get_current_users():
#         active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
#         user_id_list = []
#         for session in active_sessions:
#             data = session.get_decoded()
#             user_id_list.append(data.get('_auth_user_id', None))
#         # Query all logged in users based on id list
#         return User.objects.filter(id__in=user_id_list)


