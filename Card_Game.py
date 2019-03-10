import re
import random
from functools import total_ordering
import weakref

from Properties import Card_Value
from Exceptions.Game_Exceptions import *


@total_ordering
class Card:
  suits = ['Diamonds', 'Clubs', 'Hearts', 'Spades']
  ranks = [
    'NaR', 'Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten', 'Jack', 'Queen', 'King'
  ]
  api_rank = [
    'NaR', 'A', '2', '3', '4', '5', '6', '7', '8',
    '9', '10', 'J', 'Q', 'K'
  ]
  

  card_value = Card_Value.ACE_HIGH_RANK_SUIT_VALUE

  def __init__(self, suit, rank, name=None):
    self.suit = suit
    self.rank = rank
    self._value = None

  @property
  def value(self):
    if not self._value:
      self._value = self.card_value()
    return self._value

  @classmethod
  def new_from_name(cls, name):
    regex = re.compile(r'\w+\sof\s\w+')
    if not isinstance(name, str):
      raise TypeError('Expected a sting: %r' % value)
    if regex.match(name):
      r, s = name.split(' of ')
      if r in cls.ranks and s in cls.suits:
        return cls(cls.suits.index(s), cls.ranks.index(r))
      else:
        raise ValueError(
          'Name format does not match [value] of [suit] e.g. Four of Spades: %s'
          % value)
    else:
      raise ValueError(
        'Name format does not match [value] of [suit] e.g. Four of Spades: %s'
        % value)

  def __str__(self):
    return ('{} of {}'.format(self.ranks[self.rank], self.suits[self.suit]))

  def __repr__(self):
    return "Card(%i,%i) = %s" % (self.suit, self.rank, str(self))
    
  @property
  def api_name(self):
    return (self.suit, self.rank)

  def __lt__(self, other):
    return self.value < other.value

  def __eq__(self, other):
    return (self.rank == other.rank and self.suit == other.suit)


class Trick:
  Trick_Length = 4

  def __init__(self):
    self.turns = []
    self.round = None
    self._opening_card = None
    self._is_empty = True
    self._start_player = None
    self._resolved = False
    self._trick_winner = None

  @property
  def opening_card(self):
    if not self.is_empty():
      if self._opening_card is None:
        self._opening_card = self.turns[0][1]
    return self._opening_card

  @property
  def last_card_played(self):
    return self.turns[-1][1]
  
  @property
  def resolved(self):
    return self._resolved

  def add_card(self, card, player):
    if not isinstance(card, Card):
      raise TypeError('Expected a Card: %r' % card)
    elif self.is_full():
      raise ObjectFullError('Trick Object already full, cannot add more cards')
    elif self.is_empty() and player != self._start_player:
      raise TurnError('First player of this trick should be {}'.format(player))
    else:
      self.turns.append((player, card))
      self._is_empty = False

  def is_full(self):
    return (len(self.turns) == self.Trick_Length)

  def is_empty(self):
    return self._is_empty
    
  def __iter__(self):
    cards = [card for player, card in self.turns]
    return iter(cards)
  
  def __len__(self):
    return len(self.turns)


class Round:
  def __init__(self, players, no_of_packs=1):
    self.players = players
    self.game = None
    self.deck = Deck(no_of_packs=no_of_packs)
    self.deck.shuffle()
    self.results = None

  def player_order(self, start_player):
    first_player = self.players.index(start_player)
    num_players = len(self.players)
    order = [(first_player + i) % num_players for i in range(0, num_players)]
    return [self.players[i] for i in order]
    
  def deal(self):
    self.deck.deal(self.players)
    
  
      

class Tricks_Round(Round):
  Trick_Class = Trick

  def __init__(self, *args, **kwds):
    super().__init__(*args, **kwds)
    self.current_trick = self.Trick_Class()
    self.current_trick.round = weakref.ref(self)
    
  def next_trick(self):
    if not self.current_trick.resolved:
      raise TrickNotResolvedError("Cannot begin new trick until previous trick is resolved")
    elif max(len(player.hand) for player in self.players) == 0:
      self.current_trick = None
      #print('End of Round')
    else:
      start_player = self.current_trick._trick_winner[0]
      self.current_trick = self.Trick_Class()
      self.current_trick.round = weakref.ref(self)
      self.current_trick._start_player = start_player
    return self.current_trick


class CardGame:
  Card_Class = Card
  Round_Class = Tricks_Round

  def __init__(self, players, no_of_packs=1):
    Deck.Card_Class = self.Card_Class
    self.no_of_packs = no_of_packs
    self.players = players
    self.rounds = []
    self.EoG = False
    self.new_round()

  def new_round(self):
    self.rounds.append(
      self.Round_Class(self.players, no_of_packs=self.no_of_packs))
    self.rounds[-1].game = weakref.ref(self)
      
  def player_order(self, start_player):
    first_player = self.players.index(start_player)
    num_players = len(self.players)
    order = [(first_player + i) % num_players for i in range(0, num_players)]
    return [self.players[i] for i in order]
  
  @property
  def player_points(self):
    points = {}
    for player in self.players:
      points[player.name] = player.points
    return points


class Deck(CardGame):
  Card_Class = Card

  def __init__(self, no_of_packs=1):
    self.cards = []
    for n in range(0, no_of_packs):
      for suit in range(0, 4):
        for rank in range(1, 14):
          self.cards.append(self.Card_Class(suit, rank))

  def shuffle(self):
    random.shuffle(self.cards)
    
  def sort(self, descending=True, sort_type=None):
    if sort_type is None:
      self.cards.sort(reverse=descending)
    else:
      self.cards.sort(key=sort_type, reverse=descending)

  def deal(self, players, no_of_cards=1000, no_of_cards_per_hand=None):
    no_of_hands = len(players)
    for player in players:
      player.deal_hand(Hand(player.name))
    if no_of_cards_per_hand:
      no_of_cards = no_of_hands * no_of_cards_per_hand
    for i in range(0, no_of_cards):
      if self.is_empty(): break
      players[i % no_of_hands].hand.add_card(self.pop())

  def remove_card(self, card):
    if card in self.cards:
      self.cards.remove(card)
      return True
    else:
      return False
  
  def remove_cards(self, cards):
    for card in cards:
      self.remove_card(card)

  def pop(self):
    return self.cards.pop()

  def is_empty(self):
    return (len(self.cards) == 0)

  def __repr__(self):
    return ('{0!s}({1!s})'.format(self.__class__.__name__,
                                  repr(self.cards)[1:-1]))
                                  
  def __str__(self):
    return str([str(card) for card in self.cards])

  def __iter__(self):
    return iter(self.cards)
      
  def __getitem__(self, index):
    return self.cards[index]
  
  @property    
  def api_print(self):
    return [card.api_name for card in self.cards]
    
  def __len__(self):
    return len(self.cards)


class Hand(Deck):
  def __init__(self, name='Player'):
    self.cards = []
    self.name = name

  def add_cards(self, cards):
    for card in cards:
      self.add_card(card)
  
  def add_card(self, card):
    if not isinstance(card, Card):
      raise TypeError('Expected a Card: %r' % card)
    else:
      self.cards.append(card)

  def __str__(self):
    return "{}'s Hand: ".format(self.name) + super().__str__()

  @property
  def value(self):
    return sum(card.value for card in self.cards)


class Player:
  def __init__(self, name, comp_player = True):
    self.name = name
    self.comp_player = comp_player
    self.hand = None
    self.current_tricks = []
    self.points = 0

  def add_trick(self, trick):
    if not isinstance(trick, Trick):
      raise TypeError('Expected type Trick')
    else:
      self.current_tricks.append(trick)
  
  def resolve_tricks(self):
    for trick in self.current_tricks:
      self.points += trick.points
      #print('{} points {}'.format(self.name, self.points))
    self.current_tricks = []
    return self.points

  def deal_hand(self, hand):
    if not isinstance(hand, Hand):
      raise TypeError('Expeceted type Hand')
    else:
      self.hand = hand

  def __repr__(self):
    return '{0}({1})'.format(self.__class__.__name__, self.name)


def main():
  y = Card(3, 5)
  print(y, y.value)
  player_names = ['John', 'David', 'Paul', 'Tom']
  players = [Player(name) for name in player_names]
  z = CardGame(players)
  x = z.rounds[0]
  print(x.deck)
  x.deck.deal(x.players, no_of_cards_per_hand=5)
  hand = x.players[0].hand
  hand.sort(sort_type=Card_Value.SUIT_RANK_VALUE)
  print(hand, hand.value)



if __name__ == '__main__':
  main()

