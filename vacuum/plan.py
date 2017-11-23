import yaml


class VaccumPlan(object):
    """docstring for VaccumPlan"""
    def __init__(self, fileplan):
        super(VaccumPlan, self).__init__()
        self.fileplan = fileplan
        self.plan = None
        self.load_plan()
        self.validate()

    def load_plan(self):
        with open(self.fileplan) as fileplan:
            self.plan = yaml.load(fileplan)

    def _validate_cleanup(self):
        pass


    def _validate_archive(self):
        pass


    def validate(self):
        self._validate_archive()
        self._validate_cleanup()