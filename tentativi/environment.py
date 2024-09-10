import tentativi.init as init

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


environment = Environment(resources=100, threats=0)

def simulation_step(bees, environment):
    HiveRules.age_progression(bees)
    HiveRules.respond_to_resources(bees, environment)
    HiveRules.respond_to_threats(bees, environment)

    # Update environment (e.g., reduce resources as they are consumed)
    environment.update_resources(-10)  # Example resource consumption

# Example usage
num_bees = 100
population = initialize_population(num_bees)
for _ in range(10):  # Simulate 10 time steps
    simulation_step(population, environment)
    population_df = population_to_dataframe(population)
    print(population_df.head())
