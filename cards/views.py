from django.shortcuts import render
from django.http import HttpResponseNotFound



# # Creation du deck + shuffle
# myTable = GameTable('room_name')
# myDeck = Deck()
# myDeck.shuffle()
# dealer = Player('Dealer')
# all_players = []


def index(request):
    return render(request, 'cards/index.html')

def room(request, room_name):
    if request.user.is_authenticated:
        pass
    else:  
        return HttpResponseNotFound("You are not authenticated")
    return render(request, 'cards/game.html', {"room_name": room_name})