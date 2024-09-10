from mesa import Agent

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