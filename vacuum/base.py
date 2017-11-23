import logging



class VacuumBase(object):
    """docstring for VacuumBase"""
    def __init__(self, logger=logging):
        super(VacuumBase, self).__init__()
        self.logger = logger

    

    def run(self):
        pass
        