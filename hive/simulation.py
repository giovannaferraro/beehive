from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from queenbee import QueenBee
from bee import Bee
from resource import ResourcePatch
from hive import HiveModel
import yaml

with open('/Users/giovanna/Desktop/Magistrale/SecondoAnno/DAI/beehive/hive/setup.yaml', 'r') as file:
    config = yaml.safe_load(file)

def bee_portrayal(agent):
    if agent is None:
        return
    
    if isinstance(agent, ResourcePatch):
        return {"Shape": "rect", "Color": "brown", "Filled": "true", "Layer": 0, "w": 1, "h": 1}
    
    portrayal = {"Shape": "circle", "Filled": "true", "r": 0.5}
    
    if isinstance(agent, QueenBee):
        portrayal["Color"] = "yellow"
        portrayal["r"] = 0.8
    elif agent.task == "Nurse":
        portrayal["Color"] = "blue"
    elif agent.task == "Guard":
        portrayal["Color"] = "red"
    else:  # Forager
        portrayal["Color"] = "green"

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
     ],
    data_collector_name='datacollector'
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