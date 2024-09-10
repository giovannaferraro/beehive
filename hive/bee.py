from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from resource import ResourcePatch

class Bee(Agent):
    def __init__(self, unique_id, model, task):
        super().__init__(unique_id, model)
        self.age = self.random.randint(1, 35)
        self.lifecredit = 3
        self.JH_level = self.random.uniform(0, 1)
        self.task = task

    def assign_task(self):
        if self.JH_level < 0.3:
            self.model.totalbees["Nurse"] += 1
            return 'Nurse'
        elif 0.3 <= self.JH_level < 0.6:
            self.model.totalbees["Guard"] += 1
            return 'Guard'
        else:
            self.model.totalbees["Forager"] += 1
            return 'Forager'

    def step(self):
        # simulating bee feeding. If no resource, the bee looses a lifecredit
        self.JH_level = min(1.0, max(0.0, self.JH_level + 0.01 * self.age))
        self.task = self.assign_task()
        self.feed()

        if self.age >= 35:
            self.model.totalbees[self.task] -= 1
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
        
        if self.task == 'Forager':
            self.forage()
        elif self.task == 'Nurse':
            self.feed_larvae()
        elif self.task == 'Guard':
            self.guard_hive()
    
    def guard_hive(self):
        '''
        the random number has the meaning of a possible threat for the hive.
        I assume that if the random number is higher than 0.3 the bee fought the threat and died.
        '''
        if self.pos is not None and (self):
            if self.random.random() > 0.3:
                self.model.grid.remove_agent(self)
                #self.model.schedule.remove(self)
                self.model.totalbees['Guard'] -= 1

    def feed(self):
        if self.model.hive_resources > 0:
            self.age += 1 #normal aging to allow the bee to perform its task
            self.model.hive_resources -= 1 #feeding the bee
        else:
            self.lifecredit -= 1 #one step close to death
            if self.lifecredit == 0:
                self.model.grid.remove_agent(self)
                self.model.totalbees[self.task] -= 1
                self.model.schedule.remove(self)
        
    def forage(self):
        if self.pos is None:
            return

        # Find the nearest resource patch with available resources
        nearby_resources = self.model.grid.get_neighbors(self.pos, moore=True, radius=2, include_center=False)
        resource_patches = [agent for agent in nearby_resources if isinstance(agent, ResourcePatch)]

        if resource_patches:
            chosen_patch = self.random.choice(resource_patches)

            # Increase the closest resource patch's resources based on a random amount
            resource_increase = self.random.randint(1, 50)
            chosen_patch.resource_amount += resource_increase

            # Simulate foraging from the resource patch
            collected_amount = min(self.model.hive_resources, resource_increase)
            self.model.hive_resources -= collected_amount
            #self.carrying_resources += collected_amount

            # Simulate death with a 8% probability
            if self.random.random() < 0.08:
                self.model.totalbees['Forager'] -= 1
                self.model.schedule.remove(self)

    def feed_larvae(self):
        if self.model.larvae:
            larva = self.model.larvae.pop(0)
            larva.fed = True
            # Convert the larva into a bee
            new_bee = Bee(larva.unique_id, self.model, task='Nurse')
            self.model.schedule.remove(larva)
            self.model.schedule.add(new_bee)
            self.model.grid.place_agent(new_bee, larva.pos)
            self.model.grid.remove_agent(larva)
        