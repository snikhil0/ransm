from zope.interface.interface import Interface

class IEntityAction(Interface):

    def analyze(self, entity):
        pass


