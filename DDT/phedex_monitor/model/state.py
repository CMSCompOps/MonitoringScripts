import logging

class State:

    COMMISSIONED = "COMMISSIONED"
    COMMISSIONED_DANGER = "COMMISSIONED-DANGER"
    NOT_TESTED = "NOT-TESTED"
    PENDING_COMMISSIONING = "PENDING-COMMISSIONING"
    PENDING_RATE = "PENDING-RATE"
    PROBLEM_RATE = "PROBLEM-RATE"
    DEFAULT_STATE = NOT_TESTED

    ALL_STATES = [COMMISSIONED, NOT_TESTED, PENDING_COMMISSIONING,
                  PENDING_RATE, PROBLEM_RATE, COMMISSIONED_DANGER]

    def __init__( self ):
        self.state = self.get_default_state()
        
    def get_default_state(self):
        return self.DEFAULT_STATE

    def is_commissioned(self):
        if (self.state == self.COMMISSIONED) or \
                (self.state == self.COMMISSIONED_DANGER):
            return True
        return False

