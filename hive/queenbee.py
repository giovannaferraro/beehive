from mesa import Agent
from larva import Larva

class QueenBee(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.age = 0  
        self.laying_rate = 400
        self.max_age = 1000 
        
    

    def step(self):
        self.age += 1
        
        # Lay eggs if the queen is alive
        if self.age <= self.max_age:
            self.lay_eggs()
        else:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.schedule.stop()

    def lay_eggs(self):
        """Simulate egg-laying, producing new worker bees."""
        for _ in range(self.laying_rate):
            new_larva = Larva(self.model.next_id(), self.model)
            x = self.random.randrange(self.model.grid.width)
            y = self.random.randrange(self.model.grid.height)
            self.model.grid.place_agent(new_larva, (x, y))
            self.model.schedule.add(new_larva)