from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from bee import Bee
from resource import ResourcePatch

class HiveModel(Model):
    def __init__(self, numbee, width, height, num_resources, max_resource_amount, regeneration_rate, percentage_foragers, percentage_nurses, percentage_guards):
        self.num_bee = numbee
        self.grid = MultiGrid(width, height, torus=True)
        self.schedule = RandomActivation(self)
        self.current_id = 0
        self.hive_resources = 10 
        self.larvae = []
        self.max_resource_amount = max_resource_amount
        self.regeneration_rate = regeneration_rate

        num_of_foragers = int(self.num_bee*percentage_foragers)
        num_of_nurses = int(self.num_bee*percentage_nurses)
        num_of_guards = int(self.num_bee*percentage_guards)


        # Create queen bee
        from queenbee import QueenBee
        queen = QueenBee(self.next_id(), self)
        self.schedule.add(queen)
        self.grid.place_agent(queen, (self.grid.width // 2, self.grid.height // 2))

            
        # tre for loop per ogni task dell'ape. un po' brutto ma funziona
        for _ in range(num_of_foragers):
            forager = Bee(self.next_id(), self, task='Forager')
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(forager, (x, y))
            self.schedule.add(forager)

        for _ in range(num_of_nurses):
            nurse = Bee(self.next_id(), self, task='Nurse')
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(nurse, (x, y))
            self.schedule.add(nurse)

        for _ in range(num_of_guards):
            guard = Bee(self.next_id(), self, task='Guard')
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(guard, (x, y))
            self.schedule.add(guard)


        for _ in range(num_resources):
            resource = ResourcePatch(self.next_id(), self, self.random.randint(1, max_resource_amount))
            self.schedule.add(resource)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(resource, (x, y))


        self.totalbees = {
            'Forager': num_of_foragers,
            'Nurse': num_of_nurses,
            'Guard': num_of_guards
            #todo add the num_of_larvae
        }
        #fixme
        self.datacollector = DataCollector(
            model_reporters={
                "#Foragers": lambda m: m.totalbees['Forager'],
                "#Nurse": lambda m: m.totalbees['Nurse'],
                "#Guard": lambda m: m.totalbees['Guard']
            }
        )

        self.datacollector.collect(self)

    def next_id(self):
        self.current_id += 1
        return self.current_id

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)