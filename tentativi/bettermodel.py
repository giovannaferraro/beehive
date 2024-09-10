from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer


# General Bee class
class Bee(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.task = "idle"

    def step(self):
        # General behavior for bees like movement, pheromone interaction
        self.move()
        self.task_selection()

    def move(self):
        # Example of a simple move function for the bees
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

        # Emit footprint pheromone at current position
        #self.model.increase_pheromone('footprint', 0.005, pos=self.pos)

    def task_selection(self):
        # General task selection logic
        pass

    def perform_task(self):
        # General task execution
        pass

# Queen Bee Class
class QueenBee(Bee):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.pheromone_level = 1.0  # QMP Level
        self.egg_laying_interval = 10  # Lays eggs every 10 steps
        self.steps_since_last_egg = 0

    def step(self):
        # Queen-specific behavior
        self.emit_qmp()
        self.lay_eggs()
        self.move()

    def lay_eggs(self):
        self.steps_since_last_egg += 1
        if self.steps_since_last_egg >= self.egg_laying_interval:
            num_eggs = self.random.randint(1, 3)
            for _ in range(num_eggs):
                egg_id = self.model.next_id()
                egg = Egg(egg_id, self.model)
                x = self.random.randrange(self.model.grid.width)
                y = self.random.randrange(self.model.grid.height)
                self.model.grid.place_agent(egg, (x, y))
                self.model.schedule.add(egg)
            self.steps_since_last_egg = 0

    def move(self):
        # Queen-specific movement
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

        # Emit queen-specific footprint pheromone
        self.emit_queen_footprint()

    def emit_queen_footprint(self):
        pass
        # Emit a queen-specific footprint pheromone at the current position
        #self.model.increase_pheromone('queen_footprint', 0.02, pos=self.pos)


# Forager Bee Class
class ForagerBee(Bee):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.task = 'forager'

    def step(self):
        # Forager-specific behavior
        super().step()  # General behavior
        self.emit_forager_pheromone()

    def emit_forager_pheromone(self):
        pass


# Nurse Bee Class
class NurseBee(Bee):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.task = 'nurse'

    def step(self):
        # Nurse-specific behavior
        super().step()  # General behavior
        self.emit_nurse_pheromone()
        self.attend_brood()

    def emit_nurse_pheromone(self):
       pass

    def attend_brood(self):
        # Nurse bees are attracted to brood pheromone (BRP) to attend to larvae
        if self.model.get_pheromone_levels()['brood'] > 0.1:
            # Simulate tending to brood
            self.perform_task()


# Guard Bee Class
class GuardBee(Bee):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.task = 'guard'

    def step(self):
        # Guard-specific behavior
        super().step()  # General behavior
        self.emit_guard_pheromone()

    def emit_guard_pheromone(self):
        pass


# Egg agent class
class Egg(Agent):
    def __init__(self, unique_id, model, hatch_time=5):
        super().__init__(unique_id, model)
        self.hatch_time = hatch_time  # Number of steps until the egg hatches

    def step(self):
        # Emit Brood Recognition Pheromone (BRP)
        #self.model.increase_pheromone('brood', 0.01)
        self.hatch_time -= 1

        # Hatch the egg if the time is up
        if self.hatch_time <= 0:
            # Replace egg with a new bee (you can randomize the type of bee here)
            new_bee_id = self.model.next_id()
            new_bee = self.random.choice([ForagerBee, NurseBee, GuardBee, CleanerBee])(new_bee_id, self.model)
            self.model.grid.place_agent(new_bee, self.pos)
            self.model.schedule.add(new_bee)
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)


# Hive model class
class HiveModel(Model):
    def __init__(self, N, width, height):
        self.num_bees = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.next_id_val = N

        # Initialize pheromone levels
        self.pheromone_levels = {
            'forager': 0.5,
            'nurse': 0.5,
            'guard': 0.5
        }

        # Initialize DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "Forager Pheromone": lambda m: m.pheromone_levels['forager'],
                "Nurse Pheromone": lambda m: m.pheromone_levels['nurse'],
                "Guard Pheromone": lambda m: m.pheromone_levels['guard']
            }
        )

        # Create queen bee and place her in the grid
        self.queen_bee = QueenBee(self.next_id(), self)
        self.schedule.add(self.queen_bee)
        self.grid.place_agent(self.queen_bee, (self.grid.width // 2, self.grid.height // 2))

        # Create worker bees and place them in the grid
        for i in range(self.num_bees):
            bee_type = self.random.choice([ForagerBee, NurseBee, GuardBee])
            bee = bee_type(self.next_id(), self)
            self.schedule.add(bee)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(bee, (x, y))

        # Collect the initial data
        self.datacollector.collect(self)

    def next_id(self):
        self.next_id_val += 1
        return self.next_id_val

    def step(self):
        # Step through each agent in the schedule
        self.schedule.step()
        # Decay pheromones
        self.decay_pheromones()

        # Collect data after each step
        self.datacollector.collect(self)

    def get_pheromone_levels(self):
        return self.pheromone_levels


    def decay_pheromones(self):
        decay_rate = 0.01

        # Decay all global pheromones
        for pheromone in ['forager', 'nurse', 'guard']:
            self.pheromone_levels[pheromone] = max(0.0, self.pheromone_levels[pheromone] - decay_rate)

        # Decay footprint pheromones by position
        for pheromone_type in ['footprint', 'queen_footprint']:
            for pos in list(self.pheromone_levels[pheromone_type].keys()):
                self.pheromone_levels[pheromone_type][pos] -= decay_rate
                if self.pheromone_levels[pheromone_type][pos] <= 0:
                    del self.pheromone_levels[pheromone_type][pos]


# Visualization portrayal function
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
        else:
            portrayal["Color"] = "red"

    portrayal["Layer"] = 0
    return portrayal


# Set up the CanvasGrid for visualizing the agents on a grid
grid_width = 10
grid_height = 10
grid = CanvasGrid(bee_portrayal, grid_width, grid_height, 500, 500)

# Create a ChartModule to track pheromone levels over time
chart = ChartModule([
    {"Label": "Forager Pheromone", "Color": "green"},
    {"Label": "Nurse Pheromone", "Color": "blue"},
    {"Label": "Guard Pheromone", "Color": "red"},
], data_collector_name='datacollector')

# Set up user-settable parameters for the simulation

# Set up the server to run the simulation with the grid and chart
server = ModularServer(
    HiveModel,
    [grid, chart],  # Add both the grid and chart to the visualization
    "Bee Hive Simulation",
    {"N": 10, "width": grid_width, "height": grid_height}
)

server.port = 8521  # Set the port
server.launch()     # Start the server
