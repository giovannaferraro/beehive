from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
import yaml

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
            if self.pos is not None and self.lifecredit == 0:
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
        

class Larva(Agent):
    """Represents a bee larva."""

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.task = "Larva"

    def step(self):
        pass

class QueenBee(Agent):
    def __init__(self, unique_id, model, task="Queen"):
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


class ResourcePatch(Agent):
    '''
    questo resource patch sono le risorse
    '''

    def __init__(self, unique_id, model, resource_amount):
        super().__init__(unique_id, model)
        self.resource_amount = resource_amount  # The amount of nectar/pollen available

    def step(self):
        # Potentially regenerate resources over time
        self.resource_amount += self.model.regeneration_rate
        self.resource_amount = min(self.resource_amount, self.model.max_resource_amount)

class HiveModel(Model):
    def __init__(self, numbee, width, height, num_resources, max_resource_amount, regeneration_rate, percentage_foragers, percentage_nurses, percentage_guards):
        self.num_bee = numbee
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.current_id = 0
        self.hive_resources = 10 
        self.larvae = []
        self.max_resource_amount = max_resource_amount
        self.regeneration_rate = regeneration_rate

        num_of_foragers = int(self.num_bee*percentage_foragers)
        num_of_nurses = int(self.num_bee*percentage_nurses)
        num_of_guards = int(self.num_bee*percentage_guards)

        self.datacollector = DataCollector(
            model_reporters={
                "#Foragers": lambda m: m.totalbees['Forager'],
                "#Nurse": lambda m: m.totalbees['Nurse'],
                "#Guard": lambda m: m.totalbees['Guard']
            }
        )

        self.totalbees = {
            'Forager': num_of_foragers,
            'Nurse': num_of_nurses,
            'Guard': num_of_guards
            #todo add the num_of_larvae
        }

        self.queen = QueenBee(self.next_id(), self)
        self.schedule.add(self.queen)
        self.grid.place_agent(self.queen, (self.grid.width // 2, self.grid.height // 2))

        for _ in range(num_of_foragers):
            forager = Bee(self.next_id(), self, task='Forager')
            self.schedule.add(forager)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(forager, (x, y))
            

        for _ in range(num_of_nurses):
            nurse = Bee(self.next_id(), self, task='Nurse')
            self.schedule.add(nurse)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(nurse, (x, y))
            

        for _ in range(num_of_guards):
            guard = Bee(self.next_id(), self, task='Guard')
            self.schedule.add(guard)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(guard, (x, y))
            


        for _ in range(num_resources):
            resource = ResourcePatch(self.next_id(), self, self.random.randint(1, max_resource_amount))
            self.schedule.add(resource)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(resource, (x, y))


        self.datacollector.collect(self)

    def next_id(self):
        self.current_id += 1
        return self.current_id

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)


with open('/Users/giovanna/Desktop/Magistrale/SecondoAnno/DAI/beehive/hive/setup.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Visualization portrayal function
def bee_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.8}

    if isinstance(agent, ResourcePatch):
        portrayal["Color"] = "brown"
        portrayal["r"] = 0.6

    elif isinstance(agent, QueenBee):
        portrayal["Color"] = "purple"
        portrayal["r"] = 1.2  # Larger size for the queen
    elif isinstance(agent, Larva):
        portrayal["Color"] = "white"
        portrayal["r"] = 0.5  # Smaller size for eggs
    elif isinstance(agent, Bee):
        if agent.task == "Forager":
            portrayal["Color"] = "green"
        elif agent.task == "Nurse":
            portrayal["Color"] = "blue"
        elif agent.task == "Guard":
            portrayal["Color"] = "red"

    portrayal["Layer"] = 0
    return portrayal


grid = CanvasGrid(bee_portrayal, 
                  config['initmodel']['width'],
                  config['initmodel']['height'], 
                  500, 
                  500)

task_chart = ChartModule(
    [{"Label": "Nurse", "Color": "blue"},
     {"Label": "Guard", "Color": "red"},
     {"Label": "Forager", "Color": "green"}
     #, {"Label": "Larva", "Color": "purple"}
     ], data_collector_name='datacollector'
)

model_params = {
    "numbee": config['initmodel']['numbee'],
    "width": config['initmodel']['width'],
    "height": config['initmodel']['height'],
    "num_resources": config['initmodel']['num_resources'],
    "max_resource_amount": config['initmodel']['max_resource_amount'],
    "regeneration_rate": config['initmodel']['regeneration_rate'],
    "percentage_foragers": config['initmodel']['percentage_foragers'],
    "percentage_nurses": config['initmodel']['percentage_nurses'],
    "percentage_guards": config['initmodel']['percentage_guards']
}

server = ModularServer(
    HiveModel,
    [grid, task_chart],
    "Bee Hive Model",
    model_params
)
server.port = 8521
server.launch()