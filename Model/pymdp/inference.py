#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-member

""" Functions for performing variational inference on hidden states 

__author__: Conor Heins, Alexander Tschantz, Brennan Klein
"""

import numpy as np

from . import utils 
from . import maths 
from . import fpi

def average_states_over_policies(qs_pi, q_pi):
    """
    Parameters
    ----------
    `qs_seq_pi` - marginal posteriors over hidden states, per policy, at the current time point
    `q_pi` - posterior beliefs about policies  - (num_policies x 1) numpy 1D array

    Returns:
    ---------
    `qs_bma` - marginal posterior over hidden states for the current timepoint, averaged across policies according to their posterior probability given by `q_pi`
    """

    num_factors = len(qs_pi[0]) # get the number of hidden state factors using the shape of the first-policy-conditioned posterior
    num_states = [qs_f.shape[0] for qs_f in qs_pi[0]] # get the dimensionalities of each hidden state factor 

    qs_bma = utils.obj_array(num_factors)
    for f in range(num_factors):
        qs_bma[f] = np.zeros(num_states[f])

    for p_idx, policy_weight in enumerate(q_pi):

        for f in range(num_factors):

            qs_bma[f] += qs_pi[p_idx][f] * policy_weight

    return qs_bma

def update_posterior_states(obs, A, prior=None, **inference_params):
    """
    Update marginal posterior over hidden states using variational inference
        Can optionally set message passing algorithm used for inference
    Parameters
    ----------
    - 'A' [numpy nd.array (matrix or tensor or array-of-arrays) or Categorical]:
        Observation likelihood of the generative model, mapping from hidden states to observations
        Used to invert generative model to obtain marginal likelihood over hidden states,
        given the observation
    - 'obs' [numpy 1D array, array of arrays (with 1D numpy array entries), int or tuple]:
        The observation (generated by the environment). If single modality, this can be a 1D array
        (one-hot vector representation) or an int (observation index)
        If multi-modality, this can be an array of arrays (whose entries are 1D one-hot vectors)
        or a tuple (of observation indices)
    - 'prior' [numpy 1D array, array of arrays (with 1D numpy array entries), Categorical, or None]:
        Prior beliefs about hidden states, to be integrated with the marginal likelihood to obtain
         a posterior distribution.
        If None, prior is set to be equal to a flat categorical distribution (at the level of
        the individual inference functions).
        (optional)
    - **inference_params:
        List of keyword/parameter arguments corresponding to parameter values for the respective
        variational inference algorithm
    Returns
    ----------
    - 'qs' [numpy 1D array, array of arrays (with 1D numpy array entries), or Categorical]:
        Marginal posterior beliefs over hidden states
    """

    # safe convert to numpy
    A = utils.to_numpy(A)

    # collect model dimensions
    if utils.is_arr_of_arr(A):
        n_factors = A[0].ndim - 1
        n_states = list(A[0].shape[1:])
        n_modalities = len(A)
        n_observations = []
        for m in range(n_modalities):
            n_observations.append(A[m].shape[0])
    else:
        n_factors = A.ndim - 1
        n_states = list(A.shape[1:])
        n_modalities = 1
        n_observations = [A.shape[0]]

    obs = utils.process_observation(obs, n_modalities, n_observations)
    if prior is not None:
        prior = utils.process_prior(prior, n_factors)

    qs = fpi.run_fpi(A, obs, n_observations, n_states, prior, **inference_params)

    return qs