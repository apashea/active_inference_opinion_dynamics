#%%
import os 
os.chdir('/Users/daphnedemekas/Desktop/Research/active_inference_opinion_dynamics')
#%%

import numpy as np
from model.agent import Agent
import networkx as nx
from model.pymdp import utils
from model.pymdp.utils import obj_array, index_list_to_onehots, sample, reduce_a_matrix
from model.pymdp.maths import softmax, spm_dot, spm_log, get_joint_likelihood, calc_free_energy
from model.pymdp.inference import update_posterior_states
from simulation.simtools import initialize_agent_params, generate_network, initialize_network, run_simulation
from analysis.analysis_tools import collect_idea_beliefs, collect_sampling_history, collect_tweets

from model.genmodel_sequencing import GenerativeModel
import seaborn as sns
from matplotlib import pyplot as plt

#%%

""" Set up the generative model """

idea_levels = 3 # the levels of beliefs that agents can have about the idea (e.g. 'True' vs. 'False', in case `idea_levels` ==2)
num_H = 3 #the number of hashtags, or observations that can shed light on the idea
num_neighbors = 2
h_idea_mapping = np.eye(num_H)
h_idea_mapping[:,0] = softmax(h_idea_mapping[:,0]*1.0)
h_idea_mapping[:,1] = softmax(h_idea_mapping[:,1]*1.0)
h_idea_mapping[:,2] = softmax(h_idea_mapping[:,2]*1.0)


""" Set parameters and generate agents"""
env_d = 8
c = 0
ecb = 4
belief_d = 7
T = 10 #the number of timesteps 
N = 3
p = 1


single_node_attrs = {
    'agent': {},
    'self_global_label_mapping': {},
    'qs': {},
    'q_pi': {},
    'o': {},
    'selected_actions': {},
    'my_tweet': {},
    'other_tweet': {},
    'sampled_neighbors': {}
    }


G = generate_network(N,p)



agent_constructor_params = initialize_agent_params(G, num_H = num_H, idea_levels = idea_levels, h_idea_mapping = h_idea_mapping, \
                                    ecb_precisions = ecb, B_idea_precisions = env_d, \
                                        B_neighbour_precisions = belief_d, model = "sequencing", model_parameters = {})

agent = Agent(**agent_constructor_params[0], model = "sequencing")

"""

def test_B():
    assert B[0].shape == B[1].shape == B[2].shape#for the number of neighbours
    assert that the hashtag states index of B is of shape num_H x num_H x num_H
    assert that the who_idx state index of B is of shape num_neighbours x num_neighbours x num_neighbours
"""
#%%

print(agent.genmodel.B.shape)
print(agent.genmodel.B[0].shape)
print(agent.genmodel.B[1].shape)
print(agent.genmodel.B[2].shape)
print(agent.genmodel.B[3].shape)
print(agent.genmodel.B[4].shape)

print(agent.genmodel.num_states)


G = initialize_network(G, agent_constructor_params, T = T, model = "sequencing")


G = run_simulation(G, T = T, model = "sequencing")



# %%
