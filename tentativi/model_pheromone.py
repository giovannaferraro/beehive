from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer


class Egg(Agent):
    def __init__(self, unique_id, model, hatch_time=5):
        super().__init__(unique_id, model)
        self.hatch_time = hatch_time  # Number of steps until the egg hatches

    def step(self):
        # Decrease hatch time
        self.hatch_time -= 1

        # Hatch the egg if the time is up
        if self.hatch_time <= 0:
            # Replace egg with a new bee
            new_bee = Bee(self.unique_id, self.model)
            self.model.grid.place_agent(new_bee, self.pos)
            self.model.schedule.add(new_bee)

            # Remove the egg from the simulation
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)

class QueenBee(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.pheromone_level = 1.0  # The queen starts with a high pheromone level
        self.egg_laying_interval = 10  # Lays eggs every 10 steps
        self.steps_since_last_egg = 0

    def step(self):
        # since the queen be ages 
        self.model.increase_pheromone('queen', -0.0005)  # Natural decay

        self.steps_since_last_egg += 1
        if self.steps_since_last_egg >= self.egg_laying_interval:
            self.lay_eggs()
            self.steps_since_last_egg = 0

    def lay_eggs(self):
        # The queen lays 1 to 3 eggs each time
        num_eggs = self.random.randint(1, 3)
        for _ in range(num_eggs):
            # Create a new egg and place it in a random position in the grid
            egg_id = self.model.next_id()
            egg = Egg(egg_id, self.model)
            x = self.random.randrange(self.model.grid.width)
            y = self.random.randrange(self.model.grid.height)
            self.model.grid.place_agent(egg, (x, y))
            self.model.schedule.add(egg)

class Bee(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.task = "idle"  # Default task is idle

    def step(self):
        # The bee chooses its task based on the pheromone levels
        pheromones = self.model.get_pheromone_levels()
        
        if pheromones['queen'] < 0.2:
            # Low queen pheromone increases the likelihood of becoming a nurse
            if pheromones['nurse'] < 0.3:
                self.task = 'nurse'
            else:
                self.task = 'cleaner'
        else:
            # Normal task differentiation
            if pheromones['forager'] < 0.3:
                self.task = 'forager'
            elif pheromones['nurse'] < 0.3:
                self.task = 'nurse'
            elif pheromones['guard'] < 0.2:
                self.task = 'guard'
            else:
                self.task = 'cleaner'
        
        # Execute task logic
        self.perform_task()

    def perform_task(self):
        if self.task == 'forager':
            self.model.increase_pheromone('forager', 0.01)
        elif self.task == 'nurse':
            self.model.increase_pheromone('nurse', 0.01)
        elif self.task == 'guard':
            self.model.increase_pheromone('guard', 0.01)
        elif self.task == 'cleaner':
            self.model.increase_pheromone('cleaner', 0.01)

class HiveModel(Model):
    def __init__(self, N, width=10, height=10):
        self.num_bees = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.next_id_val = 0

        # Initialize pheromone levels
        self.pheromone_levels = {
            'forager': 0.5,
            'nurse': 0.5,
            'guard': 0.5,
            'cleaner': 0.5,
            'queen': 1.0
        }

        self.datacollector = DataCollector(
            model_reporters={
                "Forager Pheromone": lambda m: m.pheromone_levels['forager'],
                "Nurse Pheromone": lambda m: m.pheromone_levels['nurse'],
                "Guard Pheromone": lambda m: m.pheromone_levels['guard'],
                "Cleaner Pheromone": lambda m: m.pheromone_levels['cleaner'],
                "Queen Pheromone": lambda m: m.pheromone_levels['queen']
            }
        )

        self.queen_bee = QueenBee(self.next_id(), self)
        self.schedule.add(self.queen_bee)
        self.grid.place_agent(self.queen_bee, (self.grid.width // 2, self.grid.height // 2))

        # Create bees and place them in the model
        for i in range(self.num_bees):
            bee = Bee(i, self)
            self.schedule.add(bee)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(bee, (x, y))

        self.datacollector.collect(self)

    def next_id(self):
        self.next_id_val += 1
        return self.next_id_val

    def step(self):
        # Update the model by one step
        self.schedule.step()
        # Pheromone decay (optional)
        self.decay_pheromones()
        self.datacollector.collect(self)

    def get_pheromone_levels(self):
        return self.pheromone_levels

    def increase_pheromone(self, task, amount):
        self.pheromone_levels[task] = min(1.0, self.pheromone_levels[task] + amount)

    def decay_pheromones(self):
        decay_rate = 0.01
        for task in self.pheromone_levels:
            self.pheromone_levels[task] = max(0.0, self.pheromone_levels[task] - decay_rate)

def bee_portrayal(agent):
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.8}

    if isinstance(agent, QueenBee):
        portrayal["Color"] = "purple"
        portrayal["r"] = 1.2  # Larger size for the queen
    elif isinstance(agent, Egg):
        portrayal["Color"] = "white"
        portrayal["r"] = 0.5  # Smaller size for eggs
    else:
        if agent.task == "forager":
            portrayal["Color"] = "green"
        elif agent.task == "nurse":
            portrayal["Color"] = "blue"
        elif agent.task == "guard":
            portrayal["Color"] = "red"
        elif agent.task == "cleaner":
            portrayal["Color"] = "yellow"
        else:
            portrayal["Color"] = "gray"

    portrayal["Layer"] = 0
    return portrayal

# Set up the CanvasGrid for visualizing the agents on a grid
grid_width = 10
grid_height = 10
grid = CanvasGrid(bee_portrayal, grid_width, grid_height, 500, 500)


task_chart = ChartModule([
    {"Label": "Forager Pheromone", "Color": "green"},
    {"Label": "Nurse Pheromone", "Color": "blue"},
    {"Label": "Guard Pheromone", "Color": "red"},
    {"Label": "Cleaner Pheromone", "Color": "yellow"},
    {"Label": "Queen Pheromone", "Color": "purple"},
], data_collector_name='datacollector')

# Set up the server to run the simulation with the grid visualization
server = ModularServer(
    HiveModel,
    [grid, task_chart],
    "Bee Hive Model",
    {"N": 10, "width": grid_width, "height": grid_height}
)

server.port = 8521  # Set the port
server.launch()     # Start the server
