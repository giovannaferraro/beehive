import numpy as np
import pandas as pd

class Bee:
    def __init__(self, id, age, JH_level):
        self.id = id
        self.age = age
        self.JH_level = JH_level
        self.task = self.assign_task()

    def assign_task(self):
        if self.JH_level < 0.3:
            return 'Nurse'
        elif self.JH_level < 0.6:
            return 'Guard'
        else:
            return 'Forager'
        

def initialize_population(num_bees):
    bees = []
    for i in range(num_bees):
        age = np.random.randint(1, 50)  # Random age between 1 and 50 days
        JH_level = np.random.uniform(0, 1)  # Random JH level between 0 and 1
        bee = Bee(id=i, age=age, JH_level=JH_level)
        bees.append(bee)
    return bees


def population_to_dataframe(bees):
    data = {
        'ID': [bee.id for bee in bees],
        'Age': [bee.age for bee in bees],
        'JH_level': [bee.JH_level for bee in bees],
        'Task': [bee.task for bee in bees]
    }
    df = pd.DataFrame(data)
    return df


class Environment:
    def __init__(self, resources=100, threats=0):
        self.resources = resources
        self.threats = threats

    def update_resources(self, amount):
        self.resources += amount
        self.resources = max(0, self.resources)

    def set_threats(self, level):
        self.threats = level

class HiveRules:
    @staticmethod
    def age_progression(bees):
        for bee in bees:
            bee.age += 1
            HiveRules.update_JH_based_on_age(bee)

    @staticmethod
    def update_JH_based_on_age(bee):
        bee.JH_level = min(1.0, max(0.0, bee.JH_level + 0.01 * bee.age))

    @staticmethod
    def respond_to_resources(bees, environment):
        if environment.resources < 50:
            for bee in bees:
                if bee.task == 'Nurse' and np.random.rand() < 0.1:
                    bee.JH_level = min(1.0, bee.JH_level + 0.2)

    @staticmethod
    def respond_to_threats(bees, environment):
        if environment.threats > 0:
            for bee in bees:
                if bee.task == 'Forager' and np.random.rand() < 0.2:
                    bee.JH_level = max(0.3, bee.JH_level - 0.1)

    @staticmethod
    def assign_tasks(bees):
        for bee in bees:
            if bee.JH_level < 0.3:
                bee.task = 'Nurse'
            elif 0.3 <= bee.JH_level < 0.6:
                bee.task = 'Guard'
            else:
                bee.task = 'Forager'

    @staticmethod
    def signal_role_need(bees, environment):
        """
        Adjusts the JH levels of some bees if the hive needs more bees in a specific role.
        For simplicity, let's assume we need more foragers if resources are below a certain threshold.
        """
        if environment.resources < 50:
            # Need more foragers, raise JH levels of some non-forager bees
            for bee in bees:
                if bee.task != 'Forager' and np.random.rand() < 0.1:
                    bee.JH_level = min(1.0, bee.JH_level + 0.2)
        elif environment.resources > 150:
            # Need more nurses if resources are plentiful
            for bee in bees:
                if bee.task != 'Nurse' and np.random.rand() < 0.1:
                    bee.JH_level = max(0.0, bee.JH_level - 0.2)


environment = Environment(resources=100, threats=0)

def simulation_step(bees, environment):
    HiveRules.age_progression(bees)
    HiveRules.signal_role_need(bees, environment)
    HiveRules.assign_tasks(bees)

    # Update environment (e.g., simulate resource gathering or consumption)
    environment.update_resources(-10)  # Example resource consumption or gathering

# Example usage
num_bees = 100
population = initialize_population(num_bees)
for _ in range(10):  # Simulate 10 time steps
    simulation_step(population, environment)
    population_df = population_to_dataframe(population)
    print(population_df[10, 20])