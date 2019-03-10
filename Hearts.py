from Properties import Card_Value
from Card_Game import *
from Exceptions.Game_Exceptions import *
from math import ceil


suits = ['Diamonds', 'Clubs', 'Hearts', 'Spades']
ranks = [
    'NaR', 'Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten', 'Jack', 'Queen', 'King']

class HeartsCard(Card):
  card_value = Card_Value.ACE_HIGH_RANK_VALUE

  def __init__(self, *args, **kwds):
    super().__init__(*args, **kwds)
    self._points = None

  @property
  def points(self):
    if self._points is None:
      if self.suit == 2: self._points = 1
      elif self.suit == 3 and self.rank == 12: self._points = 13
      else: self._points = 0
    return self._points


class HeartsTrick(Trick):
  def __init__(self, *args, **kwds):
    super().__init__(*args, **kwds)
    self._opening_suit = None
    self._trick_winner = None
    

  @property
  def opening_suit(self):
    if self.is_empty():
      return None
    if self._opening_suit is None:
      self._opening_suit = self.opening_card.suit
    return self._opening_suit

  def add_card(self, card, player):
    if self.is_empty():
      self._trick_winner = (player, card.value)
    if card.suit == self.opening_suit and card.value > self._trick_winner[1]:
      self._trick_winner = (player, card.value)
    if card.suit == 2:
      self.round().hearts_broken = True
    if card.suit == 3 and card.value == 12:
      self.round().QoS_broken = True
    super().add_card(card, player)

  @property
  def points(self):
    return sum(turn[1].points for turn in self.turns)

  def resolve(self):
    if not self.is_full():
      raise ObjectNotFullError('Cannot resolve trick until opject is full')
    else:
      self._trick_winner[0].add_trick(self)
      self._resolved = True
      return self._trick_winner[0]


class HeartsRound(Tricks_Round):
  Trick_Class = HeartsTrick

  def __init__(self, *args, **kwrds):
    super().__init__(*args, **kwrds)
    self.hearts_broken = False
    self.QoS_broken = False
    self.pass_direction = None
    self.deal()
    self.current_trick._start_player = self._start_player()

  def pass_cards(self, pass_dict):
    if self.pass_direction is None:
      raise RoundInProgressError('Cannot pass cards after round has begun')
    if len(pass_dict) != 4:
      raise NumberOfPlayersError('The dictionary needs to contain one entry for each of the four players')
    else:
      for player, cards in pass_dict.items():
        if len(cards) != 3:
          raise CardError('Each player should pass three cards')
        else:
          for card in cards:
            if card not in player.hand:
              raise CardError('All cards need to come from player hands: {} not in {} hand'.format(card, player))
    if self.pass_direction != 'hold':
      direction = {'left' : 1, 'right' : 3, 'across' : 2, 'hold' : 0}
      for player, cards in pass_dict.items():
        player2 = self.players[(self.players.index(player) + direction[self.pass_direction]) % 4]
        player2.hand.add_cards(cards)
        player.hand.remove_cards(cards)
    self.pass_direction = None
    self.current_trick._start_player = self._start_player()
    return True
        
  def get_computer_passes(self):
    pass_dict = {}
    for player in self.players:
      if player.comp_player:
        cards = player.pass_cards()
        pass_dict[player] = cards
    return pass_dict
  
  
  def _start_player(self):
    for player in self.players:
      for card in player.hand:
        if card.suit == 1 and card.rank == 2:
          return player
  
  def play_computer_players(self):
    order_of_play = self.player_order(self.current_trick._start_player)
    for player in order_of_play:
      if player.comp_player == True:
        yield player.name, player.play_card(self.current_trick, self)
      else:
        yield 'Human_Player', 'Awiating_Response'
    yield 'End_of_Trick', 'End_of_Trick'
    
  def check_move(self, card, hand):
    trick = self.current_trick
       
    if trick.is_empty():
      if len(hand) == 13:
        if (card.suit, card.rank) == (1, 2):
          return True
        else:
          return 'Need to lead with two of clubs'
      elif card.suit !=2: 
        return True
      elif self.hearts_broken == True:
        return True
      else:
        non_hearts = [i for i in hand if i.suit !=2]
        if len(non_hearts) > 0:
          return 'Hearts has not been broken yet'
        else:
          return True
    else:
      cards_of_same_suit = [card for card in hand if card.suit == trick.opening_suit]
      if len(cards_of_same_suit) > 0 and card not in cards_of_same_suit:
        return 'You must follow suit; you can play any of the following cards: {}'.format(
          [str(card) for card in cards_of_same_suit])
      else:
        point_cards = [card for card in hand if (card.suit == 2 or (card.suit == 3 and card.rank == 12))]
        if len(hand) == 13 and card in point_cards and len(point_cards) != 13:
          return 'You cannot play a points scoring card in the first trick'
        else: 
          return True
          
  def get_results(self):
    if self.current_trick is None:
      shootmoon = False
      shoot_moon = None
      results = {}
      for player in self.players:
        #points = sum(trick.points for trick in player.current_tricks)
        points = player.resolve_tricks()
        results[player.name] = points
        if points == 26:
          shootmoon = True
          shoot_moon = player
      for player in self.players:
        if shootmoon:
          if shoot_moon != player:
            player.points += 26
            results[player.name] = 26
          else:
            player.points -= 26
            results[player.name] = 0
        if player.points >= 100:
          self.game().EoG = True
      self.results = results
      return results
    else:
      raise RoundInProgressError('Current Round still in progress cannot get results until round is finished')

class Hearts(CardGame):
  Card_Class = HeartsCard
  Round_Class = HeartsRound
  pass_direction = ['left', 'right', 'across', 'hold']

  def __init__(self, *args, **kwds):
    self.pass_order = -1
    super().__init__(*args, **kwds)
    
  def new_round(self):
    super().new_round()
    self.rounds[-1].pass_direction = self.pass_direction[(self.pass_order+1)%4]


class HeartsPlayer(Player):
  def play_card(self, trick, round):
    if trick.is_empty():
      card = self.choose_opening_card(trick, round)
    else:
      cards_of_same_suit = [
        card for card in self.hand if card.suit == trick.opening_suit
      ]
      if len(cards_of_same_suit) == 0:
        card = self.choose_discard(trick, round)
      else:
        card = self.choose_card_of_same_suit(cards_of_same_suit, trick, round)
    self.hand.remove_card(card)
    trick.add_card(card, self)
    return card

  def choose_opening_card(self, trick, round):
    two_of_clubs = HeartsCard(1,2)
    if two_of_clubs in self.hand:
      card = two_of_clubs
    else:
      options = self.hand.cards
      if not round.hearts_broken:
        options = [card for card in self.hand if card.suit != 2]
        if len(options) == 0:
          options = self.hand.cards
      options.sort(key = Card_Value.ACE_HIGH_RANK_SUIT_VALUE, reverse= False)
      half = ceil(len(options)/2)
      card = random.choice(options[:half])
      #card = random.choice(options)
    return card

  def choose_card_of_same_suit(self, options, trick, round):
    threshold = 2
    winning_card = trick._trick_winner[1]
    options.sort(key = Card_Value.ACE_HIGH_RANK_SUIT_VALUE, reverse= False)
    cards_less_than_winning_card = [card for card in options if card.value < winning_card]
    cards_more_than_winning_card = [card for card in options if card.value > winning_card]
    highest_card = options[-1]
    
    two_of_clubs = HeartsCard(1,2)
    if two_of_clubs in trick:
      card = highest_card
    elif trick.points >= threshold:
      if cards_less_than_winning_card:
        card = cards_less_than_winning_card.pop()
      elif len(trick) == 1:
        card = options[0]
      elif len(trick) == 2:
        card = random.choice(options)
      else:
        card = highest_card
    else:
      if len(trick) == 3:
        card = highest_card
      elif random.choice([True, False]) and cards_less_than_winning_card:
        card = cards_less_than_winning_card.pop()
      elif random.choice([True, False]) and cards_more_than_winning_card:
        card = random.choice(cards_more_than_winning_card)
      else:
        card = random.choice(options)
    return card

  def choose_discard(self, trick, round):
    self.hand.sort(sort_type=Card_Value.ACE_HIGH_RANK_SUIT_VALUE)
    options = self.hand
    if len(self.hand) == 13:
      options = [card for card in self.hand if card.suit !=2 or (card.suit !=3 and card.rank != 12)]
      if len(options) == 0:
        options = self.hand
    card = None
    QoS = HeartsCard(3,12)
    cards_by_suit = self.cards_by_suit()
    lengths = [(len(cards_by_suit[suit]),suit) for suit in cards_by_suit.keys() if len(cards_by_suit[suit])>0]
    if QoS in self.hand:
      card = QoS
    else:
      if not round.QoS_broken:
        spades = cards_by_suit['Spades']
        if len(spades) > 0 and len(spades)<=3:
          high_spade = spades[0]
          print(high_spade)
          if high_spade.value > 12:
            card=high_spade
    min_suit = min(lengths)
    if card is None and min_suit[0]==1:
      last_of_suit = cards_by_suit[min_suit[1]][0]
      if last_of_suit.value >8:
        card = last_of_suit
    if card is None and len(cards_by_suit['Hearts'])>0 and random.choice([True,False]):
      card = cards_by_suit['Hearts'][0]
    if card is None and random.choice([True,False]):
      card = options[0]
    if card is None:   
      card = random.choice(options)
    return card
    
  def cards_by_suit(self):
    cards_by_suit = {}
    for i in range(0, 4):
      cards_by_suit[suits[i]] = [card for card in self.hand if card.suit == i]
    return cards_by_suit
  
  def pass_cards(self):
    cards = []
    cards_by_suit = self.cards_by_suit()
    all_cards = self.hand.cards[:] 
    all_cards.sort(key = Card_Value.ACE_HIGH_RANK_SUIT_VALUE, reverse= False)
    #print(cards_by_suit)
    high_spades = [card for card in cards_by_suit['Spades'] if card.value >= 12]
    high_hearts = [card for card in cards_by_suit['Hearts'] if card.value >= 12]
    
    remaining = 3
    min_suit, min_cards = min(cards_by_suit.items(), key = lambda x : len(x[1]))
    
    # check for high spades
    if 2*len(high_spades) >= len(cards_by_suit['Spades']):
      cards.extend(high_spades)
      all_cards = [card for card in all_cards if card not in cards]
      remaining -= len(cards)
      if len(min_cards) <= remaining and min_suit != 'Spades':
        cards.extend(min_cards)
        
    #check for high hearts
    if 2*len(high_hearts) >= len(cards_by_suit['Hearts']):
      cards.extend(high_hearts)
      cards.sort(key = Card_Value.ACE_HIGH_RANK_SUIT_VALUE, reverse= True)
      while len(cards) >= 4:
        cards.pop()
      all_cards = [card for card in all_cards if card not in cards]
      remaining -= len(cards)
      if len(min_cards) <= remaining and min_suit != 'Hearts':
        cards.extend(min_cards)
    else:
      #pick between clearing a suit and passing high cards
      if random.choice([True,False]):
        if len(min_cards) <= remaining and min_suit != 'Spades':
          cards.extend(min_cards)
    
    while len(cards) < 3:
      cards.append(all_cards.pop())
    
    return cards

def main():
  player_names = ['John', 'David', 'Paul', 'Tom']
  players = [HeartsPlayer(name) for name in player_names]
  #players[3].comp_player = False
  Game = Hearts(players)
  Game.rounds[-1].pass_direction = 'hold'
  for player in players:
    print(player)
    print(player.hand)
    print('\n')
  pass_dict = Game.rounds[-1].get_computer_passes()
  print(pass_dict)
  print(Game.rounds[-1].pass_cards(pass_dict))
  for player in players:
    print(player)
    print(len(player.hand), player.hand)
    print('\n')
  
  
  return
  
  
  trick = Game.rounds[0].current_trick
  print(Game.rounds[-1].current_trick.round().hearts_broken)
  for player in Game.rounds[0].play_computer_players():
    
    print(player)
  return
  print(trick._start_player)
  for player in Game.players:
    player.play_card(trick)
  print(trick.turns, trick.points, trick._trick_winner[0])
  trick.resolve()
  print(trick._trick_winner[0].current_tricks)


if __name__ == '__main__':
  main()

