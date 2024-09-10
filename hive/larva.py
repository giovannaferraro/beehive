from mesa import Agent, Model

class Larva(Agent):
    """Represents a bee larva."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.task = "Larva"

    def step(self):
        pass
