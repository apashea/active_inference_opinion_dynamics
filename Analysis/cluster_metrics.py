import numpy as np
from .plots import belief_similarity_matrix, get_KLDs, get_JS, get_cluster_sorted_indices

# %% function to access the real parameters from the simulation
def davies_bouldin(all_qs): # a low DB index represents low inter cluster and high intra cluster similarity 
    believers = np.where(all_qs[-1,1,:] > 0.5)[0]
    nonbelievers = np.where(all_qs[-1,1,:] < 0.5)[0] 
    centroid1 = np.mean(all_qs[-1,:,believers],axis = 0)
    centroid2 = np.mean(all_qs[-1,:,nonbelievers], axis = 0)
    
    sigma1 = np.mean([KL_div(e[0],e[1], centroid1[0],centroid1[1]) for e in all_qs[-1,:,believers]])
    sigma2 = np.mean([KL_div(e[0],e[1], centroid2[0],centroid2[1])  for e in all_qs[-1,:,nonbelievers]])
    if np.isnan(KL_div(centroid1[0],centroid1[1], centroid2[0], centroid2[1])):
        return 1
    else:
        db = 0.5 * ((sigma1 + sigma2) / KL_div(centroid1[0],centroid1[1], centroid2[0], centroid2[1]))
    return db

def kld(arr1, arr2):
    return arr1*np.log(arr1/arr2)
def KL_div(array1_0, array1_1, array2_0, array2_1):
    return array1_0 * np.log(array1_0 / array2_0) + array1_1 * np.log(array1_1 / array2_1)

def cluster_kl(all_qs):
    cluster_metrics = np.zeros((all_qs.shape[0],1))
    believers = np.where(all_qs[-1,1,:] > 0.5)[0]
    nonbelievers = np.where(all_qs[-1,1,:] < 0.5)[0]
    for t in range(all_qs.shape[0]):
        believer_beliefs = all_qs[t,1,believers]
        non_believer_beliefs = all_qs[t,0,nonbelievers]
        if np.sum(believer_beliefs) == 0 or np.sum(non_believer_beliefs) == 0:
            cluster_ratio = 0.5
        else:
            cluster_metric_b = np.mean(np.ones(believer_beliefs.shape[0]) * np.log(np.ones(believer_beliefs.shape[0]) / believer_beliefs))         
            cluster_metric_nb = np.mean(np.ones(non_believer_beliefs.shape[0])* np.log(np.ones(non_believer_beliefs.shape[0]) / non_believer_beliefs) )        
            cluster_metrics[t] = (cluster_metric_b + cluster_metric_nb) / 2
    return cluster_metrics


def eigenvalue_decay(all_qs):
    JS_intra_beliefs = get_JS(all_qs)
    cluster_sorted_indices = get_cluster_sorted_indices(all_qs)

    distance_matrix = belief_similarity_matrix(-1, JS_intra_beliefs, cluster_sorted_indices)
    egd = np.sort(np.absolute(np.linalg.eigvals(distance_matrix)))[::-1]
    if len(egd) > 1:
        return np.max(np.gradient(egd))
    else:
        return np.nan

def is_connected(adj_mat):
    return np.where(adj_mat == 1)

def count_intersect(agent_samplings, cluster_group):
    unique, counts = np.unique(agent_samplings, return_counts=True)
    cluster_counts = [counts[i] for i, x in enumerate(unique) if x in cluster_group]
    return np.sum(cluster_counts)


def get_sampling_ratios(all_qs, adj_mat, all_neighbour_samplings):
    sections = [0,20,40,60]
    ratio_per_section = np.empty(len(sections)-1)
    N = all_qs.shape[2]
    cluster1, cluster2  = np.where(all_qs[-1,1,:] > 0.5)[0], np.where(all_qs[-1,1,:] < 0.5)[0]
    agent_neighbours = [list(np.where(adj_mat[:,agent] ==1)[0]) for agent in range(N)]
    outsider_neighbours = [np.intersect1d(agent_neighbours[agent], cluster1) if agent not in cluster1 else np.intersect1d(agent_neighbours[agent], cluster2) for agent in range(N)]
    insider_neighbours = [np.intersect1d(agent_neighbours[agent], cluster1) if agent in cluster1 else np.intersect1d(agent_neighbours[agent], cluster2) for agent in range(N)]
    if len(cluster1) > 0 and len(cluster2) > 0:
        for s_idx in range(len(sections)-1):
            outsider_average = np.zeros(N)
            insider_average = np.zeros(N)
            for agent_idx in range(N):
                if len(outsider_neighbours[agent_idx]) > 0 and len(insider_neighbours[agent_idx]) > 0:
                    agent_samplings = all_neighbour_samplings[sections[s_idx]:sections[s_idx+1],agent_idx]
                    outsider_sum = count_intersect(agent_samplings, outsider_neighbours[agent_idx])
                    insider_sum = count_intersect(agent_samplings, insider_neighbours[agent_idx])
                    outsider_average[agent_idx] = outsider_sum
                    insider_average[agent_idx] = insider_sum
                else:
                    outsider_average[agent_idx] = np.nan
                    insider_average[agent_idx] = np.nan
            if (insider_average == 0).all():
                insider_average = np.ones(1)
            ratio_per_section[s_idx] = np.nanmean(outsider_average) / np.nanmean(insider_average)
    else:
        ratio_per_section[:] = np.nan
    return ratio_per_section



def belief_cluster_sizes(all_qs):
    cluster1 = np.zeros(30)
    cluster2 = np.zeros(30)
    for trial in range(30):
        all_beliefs_t = all_qs[trial,:,:,:] 
        cluster1[trial] = len(np.where(all_beliefs_t[-1,1,:] > 0.5)[0])
        cluster2[trial] = len(np.where(all_beliefs_t[-1,1,:] < 0.5)[0])
    return cluster1, cluster2
        

def sampling_ratio(all_qs, agent_view_per_timestep):
    #believers = np.where(all_qs[-1,1,:] > 0.5)[0]
    #nonbelievers = np.where(all_qs[-1,1,:] < 0.5)[0]
    in_time_step_ratios = []
    out_time_step_ratios = []
    sample_ratio_in_group = 0
    sample_ratio_out_group = 0
    chunks = np.linspace(0,all_qs.shape[0]-1,10)
    for t in range(len(chunks)-1):
        believers = np.where(all_qs[int(chunks[t+1]),1,:] > 0.5)[0]
        nonbelievers = np.where(all_qs[int(chunks[t+1]),1,:] < 0.5)[0]
        for i, cluster_agent_1 in enumerate(believers):
            viewee = agent_view_per_timestep[int(chunks[t]):int(chunks[t+1]),cluster_agent_1]
            for v in viewee:
                if v in believers:
                    sample_ratio_in_group += 1
                elif v in nonbelievers:
                    sample_ratio_out_group += 1

        for i, cluster_agent_2 in enumerate(nonbelievers):
            viewee = agent_view_per_timestep[int(chunks[t]):int(chunks[t+1]),cluster_agent_2]
            for v in viewee:
                if v in nonbelievers:
                    sample_ratio_in_group += 1
                elif v in believers:
                    sample_ratio_out_group += 1
        in_time_step_ratios.append(sample_ratio_in_group / (sample_ratio_in_group + sample_ratio_out_group))
        out_time_step_ratios.append(sample_ratio_out_group / (sample_ratio_in_group + sample_ratio_out_group))
    
    return np.nanmean(in_time_step_ratios)


def sampling_frequency(parameters, all_qs, adj_mat, all_samplings):
    for trial in range(30):
            #what are the clusters? 
        cluster1 = np.where(all_qs[trial][-1,1,:] > 0.5)
        cluster2 = np.where(all_qs[trial][-1,1,:] < 0.5)
        for agent in range(parameters[0]):
            agent_cluster = cluster1[0] if agent in cluster1[0] else cluster2[0]
            other_cluster = cluster1[0] if agent not in cluster1[0] else cluster2[0]
            neighbours = list(np.where(adj_mat[:,agent,:][0] ==1)[0])
            outsider_neighbours = np.intersect1d(neighbours, other_cluster)
            insider_neighbours = np.intersect1d(neighbours, agent_cluster)
            agent_samplings = all_samplings[:,:,agent][trial]
            outsider_indices = [np.where(agent_samplings == i) for i in outsider_neighbours]
            insider_indices = [np.where(agent_samplings == i) for i in insider_neighbours]

            outsider_freq = [outsider_indices[0][0][i+1]-outsider_indices[0][0][i] for i in range(len(outsider_indices[0][0])-1)]
            insider_freq = [insider_indices[0][0][i+1]-insider_indices[0][0][i] for i in range(len(insider_indices[0][0])-1)]
        



# %%
