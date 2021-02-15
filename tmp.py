# %% Imports
import numpy as np
from utils import obj_array, spm_dot, dot_likelihood, softmax
#from genmodel import generate_likelihood
# from genmodel_v2 import GenerativeModel
from genmodel import GenerativeModel

import itertools

# %% Initialize constants
"""
Constant parameters of a focal agent's generative model, e.g. its number of neighbours
"""

num_neighbours = 5 # number of neighbours whose tweets our focal agent can read

"""
Specify the mapping between hidden states (truth/falsity of Idea) and Hashtags - this matrix will be used to 'fill out' 
the appropriate high-dimensional slices of the modality-specific A matrices later on.

Note that how you set up this mapping determines:
(1) the number of hashtags (i.e. the dimensionality of the hashtag modality) that an agent can tweet 
(2) the focal agent's beliefs about the 'semantics' of the Idea--> Hashtag content mapping - how do Hashtags provide evidence for the Idea
"""

h_idea_mapping = np.array([[0.9, 0.1], [0.1, 0.9]])

    
# num_hashtags = 10
# num_truth_levels = 2
# h_idea_mapping = np.zeros((num_hashtags, num_truth_levels))
# semantic_fuzz = 0.1
# for truth_level_i in range(num_truth_levels):
#     h_idea_mapping[:,truth_level_i] = softmax(semantic_fuzz * np.eye(num_hashtags)[np.random.randint(num_hashtags)])

true_false_precisions = np.random.uniform(low=3.0, high=10.0, size=(num_neighbours,))

num_H = h_idea_mapping.shape[0] # add an extra observation level to include the `null` observation

# h_control_mapping = np.array([[1, 0], 
#                       [0, 1]])

h_control_mapping = np.eye(num_H)

stubborness_levels = np.random.uniform(low=0.5, high=3.0, size=(num_neighbours+1,)) # in theory, the first hidden state factor (my beliefs) should be parameterised based on the focal agent's beliefs _about the inherent stochasticity_ of the world,
                                                                                    # not the 'stubborness' of their own beliefs

genmodel = GenerativeModel(h_control_mapping, true_false_precisions, num_neighbours, stubborness_levels, h_idea_mapping)

A, num_states = genmodel.generate_likelihood()
B = genmodel.generate_transition()
C = genmodel.generate_prior_preferences()
E = genmodel.generate_policy_mapping()


# %% Some quick helper functions that will let you make quick, random hidden state and observation vectors

def create_hidden_state_vector(num_states, state_idx=None):

    """
    Generates a multi-factor hidden state vector in distributional form, i.e. a bunch of one-hot vectors of the
    form [1, 0, 0, 0, ...] for each hidden state factor, with a 1 at the index of the 'true' state.
    This distributional representation of the hidden state is useful for computations like spm_dot
    """

    s = obj_array(len(num_states))
    for f, num_levels_f in enumerate(num_states):
        s[f] = np.zeros(num_levels_f)
        if state_idx is not None:
            s[f][state_idx[f]] = 1.0
        else:
            s[f][np.random.choice(num_levels_f)] = 1.0
    
    return s

def create_observations(num_obs, ob_idx=None):
    """
    Generates a multi-modal observation vector in distributional form, i.e. a bunch of one-hot vectors of the
    form [1, 0, 0, 0, ...] for each observation modality, with a 1 at the index of the observation.
    This one-hot representation of the observation is useful for computations like dot_likelihood
    """

    o = obj_array(len(num_obs))
    for m, num_levels_m in enumerate(num_obs):
        o[m] = np.zeros(num_levels_m)
        if ob_idx is not None:
            o[m][ob_idx[m]] = 1.0
        else:
            o[m][np.random.choice(num_levels_m)] = 1.0
    
    return o

# %% How to use the A matrix to generate expected observations, given a particular hidden state configuration

state_indices = [0, 0, 0, 1, 0] 
# this^^ set of hidden state indices corresponds to the state of the world when the Idea is true, 
# neighbour 1 believes the Idea is true, neighbour 2 believes the Idea is true, I am tweeting
# Hashtag 2 (Hashtag Control State Idx = 1), and I am sampling neighbour 1

# generate the hidden state vector using the helper function defined above^
hidden_state_vector = create_hidden_state_vector(num_states, state_idx = state_indices)

# generate expected observations in the first modality, given that state of the world
expected_observations = spm_dot(A[0],hidden_state_vector)

which_hashtag = np.where(expected_observations)[0][0]+1 # this converts the observation into the label of either '1' or '2'
print(f'Given these hidden states, I expect to see myself tweeting Hashtag {which_hashtag}')

# %% How to use the A matrix to invert observations to get a likelihood over hidden states

num_obs = [A[m].shape[0] for m, _ in enumerate(A)]

observation_indices = [1, 1, 1]
# this^^ set of observation indices corresponds to the observation of myself tweeting Hashtag content 2,
# seeing my neighbour tweet 0, and seeing my other neighbour tweet null

observation_vector = create_observations(num_obs, ob_idx = observation_indices)

likelihood = dot_likelihood(A[0],observation_vector[0])
