from Hearts import *
from Properties import Card_Value
from Exceptions.Game_Exceptions import NextMoveError, IllegalMoveError, CardError
import logging

logging.basicConfig(filename = 'api_log.log',level = logging.DEBUG)


class GameEngine:
  suits = ['Diamonds', 'Clubs', 'Hearts', 'Spades']
  ranks = [
    'NaR', 'Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten', 'Jack', 'Queen', 'King'
  ]
  
  def __init__(self, humanplayer, other_players):
    self.human_player = HeartsPlayer(humanplayer, comp_player = False)
    all_players = [self.human_player]
    for player_name in other_players:
      all_players.append(HeartsPlayer(player_name))
    self.game = Hearts(all_players)
    self.await_repsonse = False
    self.moves = None #self.game.rounds[-1].play_computer_players()
    self.EoT = False
    self.trick_resolved = False
    self.pass_card_status = 'awaiting'
  
  def get_player_cards(self):   
    self.human_player.hand.sort(descending = False, sort_type=Card_Value.ACE_HIGH_SUIT_RANK_VALUE)
    return self.human_player.hand.api_print
    
  def get_computer_moves(self):
    if self.await_repsonse == True:
      raise NextMoveError('Awaiting move from human player')
    computer_moves = []
    while True:
      player, card = next(self.moves)
      if player == 'Human_Player':
        self.await_repsonse = True
        return computer_moves
      elif player == 'End_of_Trick':
        self.EoT = True
        return computer_moves
      else:
        computer_moves.append((player, card.api_name))
        
  def _get_computer_moves(self):
    if self.await_repsonse == True:
      raise NextMoveError('Awaiting move from human player')
    computer_moves = []
    while True:
      player, card = next(self.moves)
      if player == 'Human_Player':
        self.await_repsonse = True
        return computer_moves
      elif player == 'End_of_Trick':
        self.EoT = True
        return computer_moves
      else:
        computer_moves.append(('play_card', player, card.api_name))
    
  def send_human_move(self, card):
    logging.debug('Submit: {}'.format(card))
    hand = self.human_player.hand
    round = self.game.rounds[-1]
    
    played_card = HeartsCard(*card)
    if played_card not in hand:
      raise IllegalMoveError('Players hand does not contain card: {}'.format(played_card))
    legal_move = round.check_move(played_card, hand)
    if legal_move != True:
      raise IllegalMoveError(legal_move)
    else:
      hand.remove_card(played_card)
      round.current_trick.add_card(played_card, self.human_player)
      self.await_repsonse = False
    return True
      
  def pass_cards(self, player_pass_cards):
    logging.debug('Pass Cards:')
    logging.debug(player_pass_cards)
    player_pass_cards = [HeartsCard(*card) for card in player_pass_cards]
    if len(player_pass_cards) != 3:
      raise CardError('Each player should pass three cards')
    else:
      for card in player_pass_cards:
        if card not in self.human_player.hand:
          raise CardError("All cards need to come from player's hands: {} not in hand".format(card))
    pass_dict = self.game.rounds[-1].get_computer_passes()
    pass_dict[self.human_player] = player_pass_cards
    self.game.rounds[-1].pass_cards(pass_dict)
    self.pass_card_status = 'update_cards'
    self.await_repsonse = False
    return True
      
  def resolve_trick(self):
    if not self.EoT:
      return 'Cannot Resolve incomplete tricks'
    else:
      winning_player = self.game.rounds[-1].current_trick.resolve()
      self.trick_resolved = True
      return winning_player.name
       
  def next_trick(self):
    if not self.trick_resolved:
      return 'Cannot begin new trick without resolving previous trick'
    else:
      self.EoT = False
      self.trick_resolved = False
      trick = self.game.rounds[-1].next_trick()
      self.moves = self.game.rounds[-1].play_computer_players()
    return trick
      
  def get_next_game_actions(self, reverse=True):
    actions =[]
    if self.pass_card_status == 'awaiting':
      actions.append(('await_pass_cards',))
    else:
      if self.pass_card_status == 'update_cards':
        actions.append(('deal_cards', self.get_player_cards()))
        self.pass_card_status = 'done'
        self.moves = self.game.rounds[-1].play_computer_players()
      actions.extend(self._get_computer_moves())
      if self.EoT:
        trick_winner = self.resolve_trick()
        actions.append(('resolve_trick', trick_winner))
        trick = self.next_trick()
        if trick is None:
          actions.append(('round_results', self.game.rounds[-1].get_results()))
          actions.append(('current_scores', self.game.player_points))
          if self.game.EoG == True:
            actions.append(('end_of_game',))
            print('End of Game')
          else:
            self.game.new_round()
            actions.append(('deal_cards',self.get_player_cards()))
            if self.game.rounds[-1].pass_direction != 'hold':
              self.await_repsonse = True
              self.pass_card_status = 'awaiting'
              actions.append(('await_pass_cards',))
            else:
              self.moves = self.game.rounds[-1].play_computer_players()
              actions.extend(self._get_computer_moves())
        else:
          actions.append(('new_trick',))
          actions.extend(self._get_computer_moves())
    if reverse:
      actions.reverse()
    logging.debug('Game Actions:')
    logging.debug(actions)
    return actions
    
    
  def new_round(self):
    pass
    
  def play_card(self, card):
    pass
    
  def card_name(self, card_api_name):
    return ('{} of {}'.format(self.ranks[card_api_name[1]], self.suits[card_api_name[0]]))
 
  def pprint_hand(self, hand):
    for i, card in enumerate(hand):
      print('{}-{}'.format(i, self.card_name(card)))
      

def main():
  human_player = 'John'
  other_players = ['David', 'Paul', 'Tom']
  g = GameEngine(human_player, other_players)
  
  g.human_player.comp_player = True
  print(g.get_next_game_actions())
  
  while True:
    print(g.pprint_hand(g.get_player_cards()))
    print(g.get_next_game_actions(reverse = False))
    
    x = input('What card would you like to send\n')
    if x.startswith('q'):
      break
    y = [int(i) for i in x.split()]
    g.send_human_move(y)
    
  
  

if __name__ == '__main__':
  main()
