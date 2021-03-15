import numpy as np
from Model.genmodel import GenerativeModel
from Model.agent import Agent
from Model.network_tools import create_multiagents
import networkx as nx
from Model.pymdp.utils import obj_array, index_list_to_onehots, sample
from Model.pymdp.maths import spm_dot, dot_likelihood, softmax

N = 3 # total number of agents
idea_levels = 2 # the levels of beliefs that agents can have about the idea (e.g. 'True' vs. 'False', in case `idea_levels` ==2)
num_H = 2 #the number of hashtags, or observations that can shed light on the idea

G = nx.complete_graph(N)

G, agents_dict = create_multiagents(G, N = N)

hashtags = {0: "#republican", 1: "#democrat"}

#belief_state = {0 : "idea is true", 1: "idea is false"}
#hashtags = {0: "#republican", 1: "#democrat"}

def agent_loop(agent, observations = None, initial = False):  
    if initial == True:
        return agent.initial_action
    else:
        qs = agent.infer_states(0, tuple(observations))
        policy = agent.infer_policies(qs)
        action = agent.sample_action()
    print(observations)
    return action


actions = []
agents = []
idea_mappings = []

agent_neighbours = {}

for agent_i in G.nodes():
    agent_neighbours[agent_i] = list(nx.neighbors(G, agent_i))
    agent = Agent(**agents_dict[agent_i])
    agents.append(agent)
    idea_mappings.append(agent.genmodel.h_idea_mapping)

timestep = 0
action = None

observations = []
num_cohesion_levels = []
true_affirmations = []
trues = []
false_affirmations = []
falses = []

for agent in agents:
    observations.append([0,2,2,None])
    num_cohesion_levels.append( 2 * (agent.genmodel.num_neighbours+1))
    true_affirmations.append(0)
    trues.append(0)
    false_affirmations.append(0)
    falses.append(0)

initial = True
while timestep < 50:
    actions = [agent_loop(agents[i], observations[i], initial) for i in range(len(agents))]
    initial = False
    for idx, agent in enumerate(agents):
        my_tweet = int(actions[idx][-2])
        observations[idx][0] = my_tweet
        observed_neighbour = int(actions[idx][-1])
        #which actual agent is that?
        observed_agent = agent_neighbours[idx][observed_neighbour]
        observations[idx][observed_neighbour+1] = int(actions[observed_agent][-2])

        my_belief = np.argmax(idea_mappings[idx][my_tweet]) # p(true | h1) p(false | h1) so we just choose whether this agent beliefs the hashtag represents true or false 
        #TODO: we should use the distribution instead 

        if my_belief == 0:
            trues[idx] += 1
            if my_tweet == int(actions[observed_agent][-2]):
                true_affirmations[idx] += 1 #accumulate how many times we have all agreed on the idea being true
            cohesion_level = int((trues[idx] - true_affirmations[idx]) / trues[idx] * (num_cohesion_levels[idx]/2-1))
            #if i tweeted true, then my cohesion level is how much others have been agreeing with me
            # 0 is the most, 2 is the least 

        elif my_belief == 1:
            falses[idx] += 1
            if my_tweet == int(actions[observed_agent][-2]):
                false_affirmations[idx] += 1
            cohesion_level = int(false_affirmations[idx] / falses[idx] * (num_cohesion_levels[idx]-1))
            #if i tweeted false, then my cohesion level is how much others have been agreeing with me
            # 5 is the most, 3 is the least 
        observations[idx][-1] = cohesion_level
        
    timestep += 1





