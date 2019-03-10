# Game standard rank
suits = ['Diamonds','Clubs','Hearts','Spades']
bridge_rank = {0:1, 1:0, 2:2, 3:3}
ace_high = {1:14, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:9, 10:10, 11:11, 12:12, 13:13}

def RANK_SUIT_VALUE(self):
	return self.rank + self.suit/4
	
def BRIDGE_SUIT_VALUE(self):
	return self.rank + bridge_rank[self.suit]/4
	
def ACE_HIGH_RANK_SUIT_VALUE(self):
	return ace_high[self.rank]+self.suit/4
	
def RANK_VALUE(self):
	return self.rank
	
def ACE_HIGH_RANK_VALUE(self):
	return ace_high[self.rank]
	
def SUIT_RANK_VALUE(self):
	return self.suit + self.rank/14
	
def ACE_HIGH_SUIT_RANK_VALUE(self):
	return self.suit + ace_high[self.rank]/15
