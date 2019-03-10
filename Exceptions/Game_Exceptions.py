class ObjectFullError(Exception):
  pass
  
class ObjectNotFullError(Exception):
  pass

class ObjectEmptyError(Exception):
  pass
  
class IllegalMoveError(Exception):
  pass
  
class TurnError(Exception):
  pass
  
class NextMoveError(Exception):
  pass
  
class TrickNotResolvedError(Exception):
  pass
  
class RoundInProgressError(Exception):
  pass
  
class CardError(Exception):
  pass
