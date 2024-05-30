import math
import os.path
import sys

from dotmap import DotMap

from verifai.samplers import ScenicSampler
from verifai.samplers import CompositionalScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier, compositional_falsifier
from verifai.monitor import specification_monitor, mtl_specification

# Load the Scenic scenario and create a sampler from it
is_compositional = False
if len(sys.argv) > 1:
    mode = sys.argv[1]
    assert mode in ["monolithic", "compositional"]
    if mode == "compositional":
        is_compositional = True

path = os.path.join(os.path.dirname(__file__), 'intersection.scenic')

if is_compositional:
    sampler = CompositionalScenicSampler.fromScenario(path, mode2D=True)
else:
    sampler = ScenicSampler.fromScenario(path, mode2D=True)

# Define the specification (i.e. evaluation metric) as an MTL formula.
# Our example spec will say that the ego object stays at least 5 meters away
# from all other objects.
class MyMonitor(specification_monitor):
    def __init__(self):
        self.specification = mtl_specification(['G safe'])
        super().__init__(self.specification)

    def evaluate(self, simulation):
        # Get trajectories of objects from the result of the simulation
        traj = simulation.result.trajectory

        # Compute time-stamped sequence of values for 'safe' atomic proposition;
        # we'll define safe = "distance from ego to all other objects > 5"
        safe_values = []
        for positions in traj:
            ego = positions[0]
            dist = min((ego.distanceTo(other) for other in positions[1:]),
                       default=math.inf)
            safe_values.append(dist - 5)
        eval_dictionary = {'safe' : list(enumerate(safe_values)) }

        # Evaluate MTL formula given values for its atomic propositions
        return self.specification.evaluate(eval_dictionary)


