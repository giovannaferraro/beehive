from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import random
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserParam
import yaml
from mesa.visualization.UserParam import Slider
random.seed(42)  

def is_position_taken(self, pos):
    return not self.grid.is_cell_empty(pos)

class Larvae(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.matured = False

class Bee(Agent):
    def __init__(self, unique_id, model, task):
        super().__init__(unique_id, model)
        self.task = task
        self.age = 0
        self.JH_level = 0
        self.lifecredit = 3
        self.wax = 0
        self.building_cell = None

        if self.task == 'Nurse':                     # api appena nate da maturazione di larve
            self.age = random.randint(1, 7)
            self.JH_level = random.uniform(0, 0.23)
            self.task = task
            
        elif self.task == 'Guard':                   # api adulte ma che non hanno ancora raggiunto le 3sett di vita
            self.age = random.randint(7, 20)
            self.JH_level = random.uniform(0.3, 0.53)
            self.task = task

        elif self.task == 'Forager':                 # api adulte oltre le 3sett di vita. hanno JH maggiore
            self.age = random.randint(21, 35)
            self.JH_level = random.uniform(0.6, 0.8)
            self.task = task
            #print("sono un apina forager e ho age: ", self.age, "JH: ", self.JH_level)
            
    def assign_task(self):
        if self.JH_level < 0.3:
            return 'Nurse'
        elif 0.3 <= self.JH_level < 0.6:
            return 'Guard'
        else:
            return 'Forager'
        
    def produce_wax(self):
        self.wax += 1

    def find_building_site(self):
        for neighbor in self.model.grid.get_neighbors(self.pos, moore=True):
            if neighbor.is_empty():
                self.building_cell = neighbor
                break

    def build_cell(self):
        if self.building_cell and self.wax >= 1:
            self.building_cell.state = "building"
            self.wax -= 1

    def check_cell_completion(self):
        if self.building_cell and self.building_cell.state == "building":
            if self.building_cell.is_complete():
                self.building_cell.state = "complete"
                self.building_cell = None

    def step(self):
        self.feed()
        if self.age > 3:                                                            ###
            self.JH_level = min(1.0, max(0.0, self.JH_level + 0.01 * (self.age-3))) ###
        else:                                                                       ###
            self.JH_level = min(1.0, max(0.0, self.JH_level + 0.01 * self.age))
        self.task = self.assign_task()

        if self.model.totalbees['Guard'] == 0 and self.pos is not None:
            if random.random() < 0.1:
                #print("Ape morta")
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                return
        
        if self.age > 35 and self.pos is not None:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        if self.task == 'Forager':
            self.forage()
        elif self.task == 'Nurse':
            self.feed_larvae()
        elif self.task == "Guard":
            self.guard_hive()
    
    def guard_hive(self):
        if self.pos is None:  
            return  

        threat_level = self.random.random()
        if threat_level > 0.8:
            self.model.grid.remove_agent(self) 
            self.model.schedule.remove(self) 
            return
        
    def feed(self):
        if self.model.hive_resources > 0:
            self.age += 1 
            self.model.hive_resources -= 1 
            self.lifecredit = 3
        else:
            self.lifecredit -= 1
            if self.pos is not None and self.lifecredit == 0:
                #print("Ape morta")
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                return

    def forage(self):
        if self.random.random() < 0.1 and self.pos is not None:
            #print("Ape morta prendendo cibo")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
        elif self.model.hive_resources <= self.model.maxresource and self.pos is not None:
            self.model.hive_resources += random.randint(1, 8)

    def feed_larvae(self):
        if self.model.hive_resources > 2 and self.model.larvae_count > 0:
            self.model.hive_resources -= 3
            for larvae in self.model.larvae_list:
                if not larvae.matured:
                    larvae.matured = True
                    self.model.create_new_bee(larvae)
                    break
                    #return 


class Cell(object):
    def __init__(self, state="empty"):
        self.state = state

    def is_empty(self):
        return self.state == "empty"

    def is_complete(self):
        # Implement a condition to check if the cell is complete (e.g., based on wax level)
        return self.state == "complete"

class QueenBee(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.age = 0
        self.laying_rate = model_params['laying_rate']
        self.max_age = 1000

    def lay_eggs(self):
        if self.model.datacollector.model_vars['Resource'][-1] > 0 and self.model.datacollector.model_vars['Nurse'][-1] > 0:
            #if self.model.datacollector.model_vars['Nurse'][-1] > 0:
                #print("numero di nurse nel datacollector: ", self.model.datacollector.model_vars['Nurse'][-1])
                for _ in range(self.laying_rate):
                    new_larvae = Larvae(self.model.next_id(), self.model)
                    self.model.schedule.add(new_larvae)
                    x = random.randrange(self.model.grid.width)
                    y = random.randrange(self.model.grid.height)
                    while(is_position_taken(self.model, (x, y))):
                        x = random.randrange(self.model.grid.width)
                        y = random.randrange(self.model.grid.height)
                    self.model.grid.place_agent(new_larvae, (x, y))
                    self.model.larvae_list.append(new_larvae)
                    self.model.larvae_count += 1

    def step(self):
        if self.model.hive_resources > 0:
            self.age += 1
            self.model.hive_resources -= 1

        if self.age <= self.max_age:
            self.lay_eggs()
        else:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)

'''class ResourcePatch(Agent):
    def __init__(self, unique_id, model, resource_amount):
        super().__init__(unique_id, model)
        self.resource_amount = resource_amount

    def step(self):
        self.resource_amount += self.model.regeneration_rate
        self.resource_amount = min(self.resource_amount, self.model.max_resource_amount)'''

class HiveModel(Model):
    def __init__(self, N, width, height, num_resources, percentage_foragers, percentage_nurses, percentage_guards, laying_rate ):
        super().__init__()
        self.num_bees = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.current_id = 0
        self.maxresource = num_resources
        self.hive_resources = num_resources
        self.larvae_count = 0
        self.adult_bees_count = 0
        self.larvae_list = []  
        self.larvae_maturity_threshold = 1 

        # piccolo check del numero di apine iniziali lollino
        if (percentage_foragers + percentage_nurses + percentage_guards) > 1:
            print("La somma delle percentuali delle api non è 1. Foragers ", percentage_foragers, " nurses ", percentage_nurses," guards",  percentage_guards)
            return

        self.num_of_foragers = int(self.num_bees*percentage_foragers)
        self.num_of_nurses = int(self.num_bees*percentage_nurses)
        self.num_of_guards = int(self.num_bees*percentage_guards)

        self.totalbees = {
        "Nurse": 0, 
        "Guard": 0, 
        "Forager": 0, 
        "Larvae": 0}
       
        self.queen = QueenBee(self.next_id(), self)
        self.queen.laying_rate = laying_rate
        self.schedule.add(self.queen)
        self.grid.place_agent(self.queen, (width // 2, height // 2))

        for _ in range(self.num_of_foragers):
            bee = Bee(self.next_id(), self, task="Forager")
            self.schedule.add(bee)
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            while(is_position_taken(self, (x, y))):
                    x = random.randrange(self.grid.width)
                    y = random.randrange(self.grid.height)
            self.grid.place_agent(bee, (x, y))

        for _ in range(self.num_of_nurses):
            bee = Bee(self.next_id(), self, task="Nurse")
            self.schedule.add(bee)
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            while(is_position_taken(self, (x, y))):
                    x = random.randrange(self.grid.width)
                    y = random.randrange(self.grid.height)  
            self.grid.place_agent(bee, (x, y))

        for _ in range(self.num_of_guards):
            bee = Bee(self.next_id(), self, task="Guard")
            self.schedule.add(bee)
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            while(is_position_taken(self, (x, y))):
                    x = random.randrange(self.grid.width)
                    y = random.randrange(self.grid.height)  
            self.grid.place_agent(bee, (x, y))

        '''# Create resource patches
        for _ in range(num_resources):
            resource = ResourcePatch(self.next_id(), self, random.randint(1, max_resource_amount))
            self.schedule.add(resource)
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            self.grid.place_agent(resource, (x, y))'''

        self.datacollector = DataCollector(
            model_reporters=
            {
                'Nurse': lambda m: m.count_agents_by_task()['Nurse'],
                'Guard': lambda m: m.count_agents_by_task()['Guard'],
                'Forager': lambda m: m.count_agents_by_task()['Forager'],
                'Larvae': lambda m: m.count_agents_by_task()['Larvae'],
                'Resource': lambda m: m.count_resources()
            }
        )

        self.datacollector.collect(self)
                
    def next_id(self):
        self.current_id += 1
        return self.current_id
    
    def create_new_bee(self, larvae):
        #print("SONO NATAAAAAA")
        new_bee = Bee(self.next_id(), self, task="Nurse")
        self.schedule.add(new_bee)
        
        x = random.randrange(self.grid.width)
        y = random.randrange(self.grid.height)
        self.grid.place_agent(new_bee, larvae.pos)
        self.grid.remove_agent(larvae)
        self.schedule.remove(larvae)

        self.larvae_list.remove(larvae)
        self.larvae_count -= 1

    def count_resources(self):
        return self.hive_resources
    
    def count_agents_by_task(self):
        self.totalbees['Nurse'] = 0
        self.totalbees['Forager'] = 0
        self.totalbees['Guard'] = 0
        self.totalbees['Larvae'] = 0

        for agent in self.schedule.agents:
            if hasattr(agent, 'task'):
                if agent.task == 'Nurse':
                    self.totalbees['Nurse'] += 1
                elif agent.task == 'Forager':
                    self.totalbees['Forager'] += 1
                elif agent.task == 'Guard':
                    self.totalbees['Guard'] += 1
            elif isinstance(agent, Larvae):
                self.totalbees['Larvae'] += 1
        return self.totalbees
    
    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
                
def bee_portrayal(agent):
    if agent is None:
        return
    
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5}
    if isinstance(agent, QueenBee):
        portrayal["Color"] = "yellow"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.8
    elif isinstance(agent, Larvae):
        portrayal["Color"] = "orange"
        portrayal["Layer"] = 1
    elif agent.task == "Nurse":
        portrayal["Color"] = "blue"
        portrayal["Layer"] = 1
    elif agent.task == "Guard":
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1
    else:  # Forager
        portrayal["Color"] = "green"
        portrayal["Layer"] = 1
    return portrayal

grid_width = 30
grid_height = 30
grid = CanvasGrid(bee_portrayal, grid_width, grid_height, 500, 500)

task_chart = ChartModule(
    [
    {"Label": "Nurse", "Color": "blue"},
    {"Label": "Guard", "Color": "red"},
    {"Label": "Forager", "Color": "green"},
    {"Label": "Larvae", "Color": "orange"},
    {"Label": "Resource", "Color": "black"}
     ],
    data_collector_name='datacollector'
)

model_params = {
    "N": Slider("Number of bees", 150, 5, 1000, 1), 
    "width": Slider("Grid Width", 17, 5, 30, 1),
    "height": Slider("Grid Height", 17, 5, 30, 1),
    "num_resources": Slider("Resources", 450, 5, 1000, 1),
    "percentage_foragers": Slider("{%} of foragers", 0.4, 0, 1 , 0.01), 
    "percentage_nurses": Slider("{%} of nurses", 0.4, 0, 1, 0.01), 
    "percentage_guards": Slider("{%} of guards", 0.2, 0, 1 , 0.01),
    "laying_rate": Slider("Laying rate of queen bee", 10, 1, 50 , 1)
}

server = ModularServer(
    HiveModel,
    [grid, task_chart],
    "Bee Hive Model",
    model_params
)

server.port = 8521
server.launch()