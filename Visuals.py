from scene import *
import random
from math import pi
from functools import partial
from Exceptions.Game_Exceptions import IllegalMoveError

from Hearts_API import GameEngine


#GameEngine = Hearts_API.GameEngine

all_players = {'John': 'S', 'David': 'W', 'Paul': 'N', 'Tom': 'E'} 
position_dict = {'S':0, 'W':1, 'N':2, 'E':3}

def translate(API_Card_Name):
  suits = ['Diamonds', 'Clubs', 'Hearts', 'Spades']
  ranks = [
    'NaR', 'Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten', 'Jack', 'Queen', 'King'
  ]
  api_rank = [
    'NaR', 'A', '2', '3', '4', '5', '6', '7', '8',
    '9', '10', 'J', 'Q', 'K'
  ] 
  return 'card:{}{}'.format(suits[API_Card_Name[0]], api_rank[API_Card_Name[1]])

class CardNode(Node):
  def add_child(self,child_node):
    if not isinstance(child_node, Card):
      raise TypeError('Expected type Card')
    else:
      super().add_child(child_node)
      self.parent._all_cards.append(child_node)

class CardGameVisual(Scene):
  def setup(self):
    self.background_color = '#8bff72'
    
    self.W_players_cards = CardNode(parent=self)
    self.N_players_cards = CardNode(parent=self)
    self.E_players_cards = CardNode(parent=self)
    self.S_players_cards = CardNode(parent=self)
    self.cards = self.S_players_cards
    self._all_cards = []
    self.played_cards = Node(parent=self)
    self.await_response = True
    self.scale_players()
    self.next_game_actions = []
    self.is_animating = []
    self.pass_cards = True
    self.W_players_cards.rotation = pi/2
    self.E_players_cards.rotation = pi/2
    self.GameEngine = GameEngine('John', [player for player in all_players.keys() if player !='John'])
    player_cards = self.GameEngine.get_player_cards()
    self._deal_cards(player_cards)
    self.start_game()

  def start_game(self):
    #self.animate_computer_moves(self.GameEngine.get_computer_moves())
    self.next_game_actions = self.GameEngine.get_next_game_actions()
       
  def animate_computer_moves(self, moves):
    i = 0
    for player, card in moves:
      i += 1   
      node = getattr(self, computer_players[player] + '_players_cards')
      played_card = random.choice(node.children)
      texture = Texture(translate(card))
      self.move_card_to_centre(played_card, delay = i, new_texture = texture)
    
  
  def scale_players(self):
    for player in ['S', 'W', 'N', 'E']:
      node = getattr(self, player + '_players_cards')
      node.scale = self.cards_scale
    
  
  def _deal_cards(self, player_cards):
    for i in range(0, 13):
      for p in ['W', 'N', 'E']:
        centre = self.card_position(card_position = p, card_order = i)
        node = getattr(self, p+'_players_cards')
        node.add_child(Card('card:BackBlue2', position = centre, player=p, card_order = i))
      
    # Player cards
    for i, card in enumerate(player_cards):
      centre = self.card_position(card_position = 'S', card_order = i)
      self.cards.add_child(Card(translate(card), type = card, position = centre, player='S', card_order = i))

  def new_round(self):
    pass

  def touch_began(self, touch):
    if self.await_response:
      if self.pass_cards:
        card = self.touch_card(touch)
        if card:
          if card.selected_for_pass:
            self.lower_card(card)
            card.selected_for_pass = False
          else:  
            card.selected_for_pass = True
            self.raise_card(card)
        else:
          selected_cards = [c.type for c in self.cards.children if c.selected_for_pass == True]
          if len(selected_cards) == 3:
            print('Submit', selected_cards)
            self.GameEngine.pass_cards(selected_cards)
            for card in self._all_cards:
              card.remove_from_parent()
              card = None
            self.next_game_actions = self.GameEngine.get_next_game_actions()
            self.pass_cards = False
            self.await_response = False
      else:
        card = self.touch_card(touch)
        if card:
          self.submit_card(card)
          #self.await_response = False
  
  def raise_card(self, card):
    #print('Raise {}'.format(card))
    position = self.card_position(card.player, card.card_order) + self.raise_height()
    card.run_action(Action.move_to(*position, 0.5, TIMING_EASE_IN_OUT))   
    
  def raise_height(self):
    return (0, self.cards_scale*190)
  
  def lower_card(self, card):  
    #print('Lower {}'.format(card))
    position = self.card_position(card.player, card.card_order)
    card.run_action(Action.move_to(*position, 0.5, TIMING_EASE_IN_OUT))  
  
  def resolve_trick(self):
    direction = {'N' : (0,1), 'E' : (1,0), 'S' : (0,-1), 'W' : (-1,0)}
    trick_winner = self.GameEngine.resolve_trick()
    for card in self._all_cards:
      if card.selected == True:
        card.run_action(Action.move_by(*(direction[computer_players[trick_winner]] * self.size)))
    self.GameEngine.next_trick()    
  
  def submit_card(self, card):
    success = False
    try:
      success = self.GameEngine.send_human_move(card.type)
    except IllegalMoveError as e:
      print(e) 
    if success:
      self.move_card_to_centre(card)
      self.next_game_actions = self.GameEngine.get_next_game_actions() 
  
  @property
  def cards_scale(self):
    percent_of_width = 0.08
    percent_of_height = 0.15
    return min((self.size.w * percent_of_width)/140.0, (self.size.h * percent_of_height)/190.0)
        
  def touch_card(self, touch):
    touch_pos = self.cards.point_from_scene(touch.location)
    for child in self.cards.children:
      if touch_pos in child.frame:
        return child
    return False
    
  def _touch_card(self, touch):
    for player in ['S', 'W', 'N', 'E']:
      node = getattr(self, player + '_players_cards')
      touch_pos = node.point_from_scene(touch.location)
      for card in node.children:
        if touch_pos in card.frame:
          return card
    return False
        
  def move_card_to_centre(self, card, delay = 0, new_texture = None):
    rotate_angle = random.gauss(0, 0.25)
    actions = [Action.wait(delay)]
    group = []
    if new_texture is not None:
      card.texture_2 = new_texture
      group.append(Action.call(card.update_texture))
    
    group.extend([Action.move_to(*self.card_centre_position(card.player), 1.0,
        TIMING_EASE_IN_OUT), Action.rotate_by(rotate_angle)])
    actions.append(Action.group(group))
    card.run_action(Action.sequence(actions))
    card.selected = True
    
    
    # bring to front
    card.z_position = self.max_card_z_position + 0.1
    card.parent.z_position = self.max_player_z_position + 0.1
  
  def did_evaluate_actions(self):
    if not self.is_animating:
      if self.next_game_actions:
        next_action = self.next_game_actions.pop()
        method = getattr(self, '_' + next_action[0])
        method(*next_action[1:])
      else:
        self.await_response = True
    
  def _new_trick(self):
    pass
  
  def _play_card(self, player, card):
    node = getattr(self, all_players[player] + '_players_cards')
    played_card = random.choice([child for child in node.children if child.selected != True])   
    texture = Texture(translate(card))      
    self.move_card_to_centre(played_card, new_texture = texture)
    
  def _resolve_trick(self, trick_winner):
    direction = {'N' : (0.5,1.1), 'E' : (1.1,0.5), 'S' : (0.5,-0.1), 'W' : (-0.1,0.5)}
    
    for card in self._all_cards:
      if card.selected == True:
         position = card.parent.point_from_scene(direction[all_players[trick_winner]] * self.size)
         
         remove = partial(self.remove_card, card)
         card.run_action(Action.sequence(Action.wait(2), Action.move_to(*position), Action.call(remove)))
  
  def _round_results(self, results):
    print('Round results:', results)
    
  def _current_scores(self, scores):
    print('Current scores:', scores)
    
  def _await_pass_cards(self):
    self.pass_cards = True
    
  def remove_card(self, card):
    self.is_animating.pop()
    card.remove_from_parent()
    self._all_cards.remove(card)
  
  def animating_start(self):
    self.is_animating.append('card')
    
  def animating_done(self):
    self.is_animating.pop()
  
  def card_centre_position(self, player='S', offset_percentage = 0.04, percentage_error = 0.02):
    centre_dict = {'S':(0, -1), 'W':(-1, 0), 'N':(0, 1), 'E':(1, 0)}
    offset = [0.5 + i * offset_percentage + random.gauss(0, percentage_error) \
        for i in centre_dict[player]]
    position = self.size * offset
    node = getattr(self, player + '_players_cards')
    return node.point_from_scene(position)
  
  def card_position(self, card_position, card_order, \
        l_margin_percentage = 0.05, w_margin_percentage = 0.05):
    # ---- Constants for customising the positions of the different players
    # 0 for 'N' and 'S'; 1 for east and west
    i = position_dict[card_position] % 2
    # the oposite of i
    j= (i+1) % 2
    # 0 for 'S' and 'E'; 1 for 'N' and 'W'
    k = position_dict[card_position] >= 2
    
    # Extra margin for 'W' and 'E' to avoid clasing with 'S' and 'N' cards
    l_margin_percentage = l_margin_percentage + 0.25 * i
    
    # For distiguishing between oposite positions
    w_position = (k + ((-1) ** k) * w_margin_percentage) * self.size[j]
    
    # The seperation between each card
    seperation = (1-l_margin_percentage) * self.size[i] / 14
    
    # The position of the first card
    point = l_margin_percentage/2 * self.size[i] + seperation
    
    # The givens cards position
    l_position = point + card_order * seperation
    
    # The position as an ordered pair
    position = [l_position, w_position]
    
    node = getattr(self, card_position + '_players_cards')
    return node.point_from_scene((position[i], position[j]))
  
  def did_change_size(self):
    #print(self.size)
    self.scale_players()
    for card in self._all_cards:
      if card.selected == True:
        card.position = self.card_centre_position(card.player)
      elif card.selected_for_pass:
        card.position = self.card_position(card_position = card.player, card_order = card.card_order) + self.raise_height()      
      else:
        card.position = self.card_position(card_position = card.player, card_order = card.card_order)
    
  @property
  def max_card_z_position(self):
    return max(card.z_position for card in self._all_cards)
  @property
  def max_player_z_position(self):
      return max(self.N_players_cards.z_position, self.E_players_cards.z_position, 
          self.S_players_cards.z_position, self.W_players_cards.z_position)      


class Card(SpriteNode):
  def __init__(self, *args, type = None, player=None, card_order= 0, **kwds):
    SpriteNode.__init__(self, *args, **kwds)
    self.selected = False
    self.selected_for_pass = False
    self.player = player
    self.card_order = card_order
    self.type = type
    self.texture_2 = None
    
  def run_action(self, action, *args, **kwrds):
    action = Action.sequence(Action.call(self.scene.animating_start), action, Action.call(self.scene.animating_done))
    super().run_action(action, *args, **kwrds)
    
  def update_texture(self):
    self.texture = self.texture_2


def main():
  run(CardGameVisual())


if __name__ == '__main__':
  main()

