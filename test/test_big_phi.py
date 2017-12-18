#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_big_phi.py

import pickle
from unittest.mock import patch

import numpy as np
import pytest

from pyphi import (Direction, Network, Subsystem, compute, config, constants,
                   models, utils)
from pyphi.compute.system import ComputeSystemIrreducibility, sia_bipartitions
from pyphi.models import Cut, _null_sia
from pyphi.partition import directed_bipartition

# pylint: disable=unused-argument

# TODO: split these into `concept` and `big_phi` tests

# Answers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

standard_answer = {
    'phi': 2.3125,
    'unpartitioned_small_phis': {
        (1,): 0.25,
        (2,): 0.5,
        (0, 1): 0.333333,
        (0, 1, 2): 0.5
    },
    'len_partitioned_ces': 1,
    'sum_partitioned_small_phis': 0.5,
    'cut': models.Cut(from_nodes=(1, 2), to_nodes=(0,))
}


noised_answer = {
    'phi': 1.928592,
    'unpartitioned_small_phis': {
        (0,): 0.0625,
        (1,): 0.2,
        (2,): 0.316326,
        (0, 1): 0.319047,
        (0, 2): 0.0125,
        (1, 2): 0.263847,
        (0, 1, 2): 0.35
    },
    'len_partitioned_ces': 7,
    'sum_partitioned_small_phis': 0.504906,
    'cut': models.Cut(from_nodes=(1, 2), to_nodes=(0,))
}


big_answer = {
    'phi': 10.729491,
    'unpartitioned_small_phis': {
        (0,): 0.25,
        (1,): 0.25,
        (2,): 0.25,
        (3,): 0.25,
        (4,): 0.25,
        (0, 1): 0.2,
        (0, 2): 0.2,
        (0, 3): 0.2,
        (0, 4): 0.2,
        (1, 2): 0.2,
        (1, 3): 0.2,
        (1, 4): 0.2,
        (2, 3): 0.2,
        (2, 4): 0.2,
        (3, 4): 0.2,
        (0, 1, 2): 0.2,
        (0, 1, 3): 0.257143,
        (0, 1, 4): 0.2,
        (0, 2, 3): 0.257143,
        (0, 2, 4): 0.257143,
        (0, 3, 4): 0.2,
        (1, 2, 3): 0.2,
        (1, 2, 4): 0.257143,
        (1, 3, 4): 0.257143,
        (2, 3, 4): 0.2,
        (0, 1, 2, 3): 0.185709,
        (0, 1, 2, 4): 0.185709,
        (0, 1, 3, 4): 0.185709,
        (0, 2, 3, 4): 0.185709,
        (1, 2, 3, 4): 0.185709
    },
    'len_partitioned_ces': 17,
    'sum_partitioned_small_phis': 3.564909,
    'cut': models.Cut(from_nodes=(2, 4), to_nodes=(0, 1, 3))
}


big_subsys_0_thru_3_answer = {
    'phi': 0.366389,
    'unpartitioned_small_phis': {
        (0,): 0.166667,
        (1,): 0.166667,
        (2,): 0.166667,
        (3,): 0.25,
        (0, 1): 0.133333,
        (1, 2): 0.133333
    },
    'len_partitioned_ces': 5,
    'sum_partitioned_small_phis': 0.883334,
    'cut': models.Cut(from_nodes=(1, 3), to_nodes=(0, 2))
}


rule152_answer = {
    'phi': 6.952286,
    'unpartitioned_small_phis': {
        (0,): 0.125,
        (1,): 0.125,
        (2,): 0.125,
        (3,): 0.125,
        (4,): 0.125,
        (0, 1): 0.25,
        (0, 2): 0.184614,
        (0, 3): 0.184614,
        (0, 4): 0.25,
        (1, 2): 0.25,
        (1, 3): 0.184614,
        (1, 4): 0.184614,
        (2, 3): 0.25,
        (2, 4): 0.184614,
        (3, 4): 0.25,
        (0, 1, 2): 0.25,
        (0, 1, 3): 0.316666,
        (0, 1, 4): 0.25,
        (0, 2, 3): 0.316666,
        (0, 2, 4): 0.316666,
        (0, 3, 4): 0.25,
        (1, 2, 3): 0.25,
        (1, 2, 4): 0.316666,
        (1, 3, 4): 0.316666,
        (2, 3, 4): 0.25,
        (0, 1, 2, 3): 0.25,
        (0, 1, 2, 4): 0.25,
        (0, 1, 3, 4): 0.25,
        (0, 2, 3, 4): 0.25,
        (1, 2, 3, 4): 0.25,
        (0, 1, 2, 3, 4): 0.25
    },
    'len_partitioned_ces': 24,
    'sum_partitioned_small_phis': 4.185363,
    'cuts': [
        models.Cut(from_nodes=(0, 1, 2, 3), to_nodes=(4,)),
        models.Cut(from_nodes=(0, 1, 2, 4), to_nodes=(3,)),
        models.Cut(from_nodes=(0, 1, 3, 4), to_nodes=(2,)),
        models.Cut(from_nodes=(0, 2, 3, 4), to_nodes=(1,)),
        models.Cut(from_nodes=(1, 2, 3, 4), to_nodes=(0,)),
        # TODO: are there other possible cuts?
    ]
}


micro_answer = {
    'phi': 0.974411,
    'unpartitioned_small_phis': {
        (0,): 0.175,
        (1,): 0.175,
        (2,): 0.175,
        (3,): 0.175,
        (0, 1): 0.348114,
        (2, 3): 0.348114,
    },
    'cuts': [
        models.Cut(from_nodes=(0, 2), to_nodes=(1, 3)),
        models.Cut(from_nodes=(1, 2), to_nodes=(0, 3)),
        models.Cut(from_nodes=(0, 3), to_nodes=(1, 2)),
        models.Cut(from_nodes=(1, 3), to_nodes=(0, 2)),
    ]
}

macro_answer = {
    'phi': 0.86905,
    'unpartitioned_small_phis': {
        (0,): 0.455,
        (1,): 0.455,
    },
    'cuts': [
        models.Cut(from_nodes=(0,), to_nodes=(1,)),
        models.Cut(from_nodes=(1,), to_nodes=(0,)),
    ]
}


# Helpers
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def check_unpartitioned_small_phis(small_phis, ces):
    assert len(small_phis) == len(ces)
    for c in ces:
        assert c.phi == small_phis[c.mechanism]


def check_partitioned_small_phis(answer, partitioned_ces):
    if 'len_partitioned_ces' in answer:
        assert (answer['len_partitioned_ces'] ==
                len(partitioned_ces))
    if 'sum_partitioned_small_phis' in answer:
        assert (round(sum(c.phi for c in partitioned_ces),
                      config.PRECISION) ==
                answer['sum_partitioned_small_phis'])


def check_mip(mip, answer):
    # Check big phi value.
    assert mip.phi == answer['phi']
    # Check small phis of unpartitioned CES.
    check_unpartitioned_small_phis(answer['unpartitioned_small_phis'],
                                   mip.ces)
    # Check sum of small phis of partitioned CES if answer is
    # available.
    check_partitioned_small_phis(answer, mip.partitioned_ces)
    # Check cut.
    if 'cut' in answer:
        assert mip.cut == answer['cut']
    elif 'cuts' in answer:
        assert mip.cut in answer['cuts']


# Tests
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def test_null_concept(s, flushcache, restore_fs_cache):
    flushcache()
    cause = models.MaximallyIrreducibleCause(models.RepertoireIrreducibilityAnalysis(
        repertoire=s.unconstrained_cause_repertoire(()),
        phi=0, direction=Direction.CAUSE, mechanism=(), purview=(),
        partition=None, partitioned_repertoire=None))
    effect = models.MaximallyIrreducibleEffect(models.RepertoireIrreducibilityAnalysis(
        repertoire=s.unconstrained_effect_repertoire(()),
        phi=0, direction=Direction.EFFECT, mechanism=(), purview=(),
        partition=None, partitioned_repertoire=None))
    assert (s.null_concept ==
            models.Concept(mechanism=(), cause=cause, effect=effect,
                           subsystem=s))


def test_concept_nonexistent(s, flushcache, restore_fs_cache):
    flushcache()
    assert not compute.concept(s, (0, 2))


@patch('pyphi.compute.distance._ces_distance_simple')
@patch('pyphi.compute.distance._ces_distance_emd')
def test_ces_distance_uses_simple_vs_emd(mock_emd_distance,
                                                   mock_simple_distance, s):
    """Quick check that we use the correct CES distance function.

    If the two CESs differ only in that some concepts have
    moved to the null concept and all other concepts are the same then
    we use the simple CES distance. Otherwise, use the EMD.
    """
    mock_emd_distance.return_value = float()
    mock_simple_distance.return_value = float()

    make_mice = lambda: models.MaximallyIrreducibleCauseOrEffect(
        models.RepertoireIrreducibilityAnalysis(
            phi=0, direction=None, mechanism=None, purview=None,
            partition=None, repertoire=None, partitioned_repertoire=None))

    lone_concept = models.Concept(cause=make_mice(), effect=make_mice(),
                                  mechanism=(0, 1))
    # lone concept -> null concept
    compute.ces_distance((lone_concept,), ())
    assert mock_emd_distance.called is False
    assert mock_simple_distance.called is True
    mock_simple_distance.reset_mock()

    other_concept = models.Concept(cause=make_mice(), effect=make_mice(),
                                   mechanism=(0, 1, 2))
    # different concepts in CES
    compute.ces_distance((lone_concept,), (other_concept,))
    assert mock_emd_distance.called is True
    assert mock_simple_distance.called is False


def test_ces_distance_switches_to_small_phi_difference(s):
    mip = compute.sia(s)
    ce_structures = (mip.ces, mip.partitioned_ces)

    with config.override(
            USE_SMALL_PHI_DIFFERENCE_FOR_CES_DISTANCE=False):
        assert 2.3125 == compute.ces_distance(*ce_structures)

    with config.override(
            USE_SMALL_PHI_DIFFERENCE_FOR_CES_DISTANCE=True):
        assert 1.083333 == compute.ces_distance(*ce_structures)


@config.override(CACHE_SIAS=True)
def test_sia_cache_key_includes_config_dependencies(s, flushcache,
                                                        restore_fs_cache):
    flushcache()

    with config.override(MEASURE='EMD'):
        emd_big_phi = compute.phi(s)

    with config.override(MEASURE='L1'):
        l1_big_phi = compute.phi(s)

    assert l1_big_phi != emd_big_phi


def test_conceptual_info(s, flushcache, restore_fs_cache):
    flushcache()
    assert compute.conceptual_info(s) == 2.8125


def test_sia_empty_subsystem(s_empty, flushcache, restore_fs_cache):
    flushcache()
    assert (compute.sia(s_empty) ==
            models.SystemIrreducibilityAnalysis(phi=0.0,
                          ces=(),
                          partitioned_ces=(),
                          subsystem=s_empty,
                          cut_subsystem=s_empty))


def test_sia_disconnected_network(reducible, flushcache, restore_fs_cache):
    flushcache()
    assert (compute.sia(reducible) ==
            models.SystemIrreducibilityAnalysis(subsystem=reducible,
                                                cut_subsystem=reducible,
                                                phi=0.0,
                                                ces=[],
                                                partitioned_ces=[]))


def test_sia_wrappers(reducible, flushcache, restore_fs_cache):
    flushcache()
    assert (compute.sia(reducible) ==
            models.SystemIrreducibilityAnalysis(subsystem=reducible,
                                                cut_subsystem=reducible,
                                                phi=0.0,
                                                ces=[],
                                                partitioned_ces=[]))
    assert compute.phi(reducible) == 0.0


@config.override(SINGLE_MICRO_NODES_WITH_SELFLOOPS_HAVE_PHI=True)
@config.override(MEASURE='EMD')
def test_sia_single_micro_node_selfloops_have_phi(
        noisy_selfloop_single, flushcache, restore_fs_cache):
    flushcache()
    assert compute.sia(noisy_selfloop_single).phi == 0.2736


@config.override(SINGLE_MICRO_NODES_WITH_SELFLOOPS_HAVE_PHI=False)
def test_sia_single_micro_node_selfloops_dont_have_phi(
        noisy_selfloop_single, flushcache, restore_fs_cache):
    flushcache()
    assert compute.sia(noisy_selfloop_single).phi == 0.0


def test_sia_single_micro_nodes_without_selfloops_dont_have_phi(
        s_single, flushcache, restore_fs_cache):
    flushcache()
    assert compute.sia(s_single).phi == 0.0


@pytest.fixture
def standard_ComputeSystemIrreducibility(s):
    ces = compute.ces(s)
    cuts = sia_bipartitions(s.node_indices)
    return ComputeSystemIrreducibility(cuts, s, ces)


@config.override(PARALLEL_CUT_EVALUATION=False)
def test_find_mip_sequential_standard_example(standard_ComputeSystemIrreducibility, flushcache,
                                              restore_fs_cache):
    flushcache()
    mip = standard_ComputeSystemIrreducibility.run_sequential()
    check_mip(mip, standard_answer)


@config.override(PARALLEL_CUT_EVALUATION=True, NUMBER_OF_CORES=-2)
def test_find_mip_parallel_standard_example(standard_ComputeSystemIrreducibility, flushcache,
                                            restore_fs_cache):
    flushcache()
    mip = standard_ComputeSystemIrreducibility.run_parallel()
    check_mip(mip, standard_answer)


@pytest.fixture
def s_noised_ComputeSystemIrreducibility(s_noised):
    ces = compute.ces(s_noised)
    cuts = sia_bipartitions(s_noised.node_indices)
    return ComputeSystemIrreducibility(cuts, s_noised, ces)


@config.override(PARALLEL_CUT_EVALUATION=False)
def test_find_mip_sequential_noised_example(s_noised_ComputeSystemIrreducibility, flushcache,
                                            restore_fs_cache):
    flushcache()
    mip = s_noised_ComputeSystemIrreducibility.run_sequential()
    check_mip(mip, noised_answer)


@config.override(PARALLEL_CUT_EVALUATION=True, NUMBER_OF_CORES=-2)
def test_find_mip_parallel_noised_example(s_noised_ComputeSystemIrreducibility, flushcache,
                                          restore_fs_cache):
    flushcache()
    mip = s_noised_ComputeSystemIrreducibility.run_parallel()
    check_mip(mip, noised_answer)


@pytest.fixture
def micro_s_ComputeSystemIrreducibility(micro_s):
    ces = compute.ces(micro_s)
    cuts = sia_bipartitions(micro_s.node_indices)
    return ComputeSystemIrreducibility(cuts, micro_s, ces)


@config.override(PARALLEL_CUT_EVALUATION=True)
def test_find_mip_parallel_micro(micro_s_ComputeSystemIrreducibility, flushcache,
                                 restore_fs_cache):
    flushcache()
    mip = micro_s_ComputeSystemIrreducibility.run_parallel()
    check_mip(mip, micro_answer)


@config.override(PARALLEL_CUT_EVALUATION=False)
def test_find_mip_sequential_micro(micro_s_ComputeSystemIrreducibility, flushcache,
                                   restore_fs_cache):
    flushcache()
    mip = micro_s_ComputeSystemIrreducibility.run_sequential()
    check_mip(mip, micro_answer)


def test_possible_complexes(s):
    assert list(compute.possible_complexes(s.network, s.state)) == [
        Subsystem(s.network, s.state, (0, 1, 2)),
        Subsystem(s.network, s.state, (1, 2)),
        Subsystem(s.network, s.state, (0, 2)),
        Subsystem(s.network, s.state, (0, 1)),
        Subsystem(s.network, s.state, (1,)),
    ]


def test_complexes_standard(s, flushcache, restore_fs_cache):
    flushcache()
    complexes = list(compute.complexes(s.network, s.state))
    check_mip(complexes[0], standard_answer)


# TODO!! add more assertions for the smaller subsystems
def test_all_complexes_standard(s, flushcache, restore_fs_cache):
    flushcache()
    complexes = list(compute.all_complexes(s.network, s.state))
    check_mip(complexes[0], standard_answer)


@config.override(PARALLEL_CUT_EVALUATION=False)
def test_all_complexes_parallelization(s, flushcache, restore_fs_cache):
    flushcache()
    with config.override(PARALLEL_COMPLEX_EVALUATION=False):
        serial = compute.all_complexes(s.network, s.state)

    with config.override(PARALLEL_COMPLEX_EVALUATION=True):
        parallel = compute.all_complexes(s.network, s.state)

    assert sorted(serial) == sorted(parallel)


def test_sia_complete_graph_standard_example(s_complete):
    mip = compute.sia(s_complete)
    check_mip(mip, standard_answer)


def test_sia_complete_graph_s_noised(s_noised_complete):
    mip = compute.sia(s_noised_complete)
    check_mip(mip, noised_answer)


@pytest.mark.slow
def test_sia_complete_graph_big_subsys_all(big_subsys_all_complete):
    mip = compute.sia(big_subsys_all_complete)
    check_mip(mip, big_answer)


@pytest.mark.slow
def test_sia_complete_graph_rule152_s(rule152_s_complete):
    mip = compute.sia(rule152_s_complete)
    check_mip(mip, rule152_answer)


@pytest.mark.slow
def test_sia_big_network(big_subsys_all, flushcache, restore_fs_cache):
    flushcache()
    mip = compute.sia(big_subsys_all)
    check_mip(mip, big_answer)


def test_sia_big_network_0_thru_3(big_subsys_0_thru_3, flushcache,
                                      restore_fs_cache):
    flushcache()
    mip = compute.sia(big_subsys_0_thru_3)
    check_mip(mip, big_subsys_0_thru_3_answer)


@pytest.mark.slow
def test_sia_rule152(rule152_s, flushcache, restore_fs_cache):
    flushcache()
    mip = compute.sia(rule152_s)
    check_mip(mip, rule152_answer)


# TODO fix this horribly outdated mess that never worked in the first place :P
@pytest.mark.veryslow
def test_rule152_complexes_no_caching(rule152):
    net = rule152
    # Mapping from index of a PyPhi subsystem in network.subsystems to the
    # index of the corresponding subsystem in the Matlab list of subsets
    perm = {0: 0, 1: 1, 2: 3, 3: 7, 4: 15, 5: 2, 6: 4, 7: 8, 8: 16, 9: 5, 10:
            9, 11: 17, 12: 11, 13: 19, 14: 23, 15: 6, 16: 10, 17: 18, 18: 12,
            19: 20, 20: 24, 21: 13, 22: 21, 23: 25, 24: 27, 25: 14, 26: 22, 27:
            26, 28: 28, 29: 29, 30: 30}
    with open('test/data/rule152_results.pkl', 'rb') as f:
        results = pickle.load(f)

    # Don't use concept caching for this test.
    constants.CACHE_CONCEPTS = False

    for state, result in results.items():
        # Empty the DB.
        _flushdb()
        # Unpack the state from the results key.
        # Generate the network with the state we're testing.
        net = Network(rule152.tpm, state,
                      connectivity_matrix=rule152.connectivity_matrix)
        # Comptue all the complexes, leaving out the first (empty) subsystem
        # since Matlab doesn't include it in results.
        complexes = list(compute.complexes(net))[1:]
        # Check the phi values of all complexes.
        zz = [(sia.phi, result['subsystem_phis'][perm[i]]) for i, sia in
            list(enumerate(complexes))]
        diff = [utils.eq(sia.phi, result['subsystem_phis'][perm[i]]) for
                i, sia in list(enumerate(complexes))]
        assert all(utils.eq(sia.phi, result['subsystem_phis'][perm[i]])
                   for i, sia in list(enumerate(complexes))[:])
        # Check the major complex in particular.
        major = compute.major_complex(net)
        # Check the phi value of the major complex.
        assert utils.eq(major.phi, result['phi'])
        # Check that the nodes are the same.
        assert (major.subsystem.node_indices ==
                complexes[result['major_complex'] - 1].subsystem.node_indices)
        # Check that the concept's phi values are the same.
        result_concepts = [c for c in result['concepts']
                           if c['is_irreducible']]
        z = list(zip([c.phi for c in major.ces],
                     [c['phi'] for c in result_concepts]))
        diff = [i for i in range(len(z)) if not utils.eq(z[i][0], z[i][1])]
        assert all(list(utils.eq(c.phi, result_concepts[i]['phi']) for i, c
                        in enumerate(major.ces)))
        # Check that the minimal cut is the same.
        assert major.cut == result['cut']


@pytest.mark.dev
def test_sia_macro(macro_s, flushcache, restore_fs_cache):
    flushcache()
    mip = compute.sia(macro_s)
    check_mip(mip, macro_answer)


def test_parallel_and_sequential_ces_are_equal(s, micro_s, macro_s):
    with config.override(PARALLEL_CONCEPT_EVALUATION=False):
        c = compute.ces(s)
        c_micro = compute.ces(micro_s)
        c_macro = compute.ces(macro_s)

    with config.override(PARALLEL_CONCEPT_EVALUATION=True):
        assert set(c) == set(compute.ces(s))
        assert set(c_micro) == set(compute.ces(micro_s))
        assert set(c_macro) == set(compute.ces(macro_s))


def test_sia_bipartitions():
    with config.override(CUT_ONE_APPROXIMATION=False):
        answer = [models.Cut((1,), (2, 3, 4)),
                  models.Cut((2,), (1, 3, 4)),
                  models.Cut((1, 2), (3, 4)),
                  models.Cut((3,), (1, 2, 4)),
                  models.Cut((1, 3), (2, 4)),
                  models.Cut((2, 3), (1, 4)),
                  models.Cut((1, 2, 3), (4,)),
                  models.Cut((4,), (1, 2, 3)),
                  models.Cut((1, 4), (2, 3)),
                  models.Cut((2, 4), (1, 3)),
                  models.Cut((1, 2, 4), (3,)),
                  models.Cut((3, 4), (1, 2)),
                  models.Cut((1, 3, 4), (2,)),
                  models.Cut((2, 3, 4), (1,))]
        assert sia_bipartitions((1, 2, 3, 4)) == answer

    with config.override(CUT_ONE_APPROXIMATION=True):
        answer = [models.Cut((1,), (2, 3, 4)),
                  models.Cut((2,), (1, 3, 4)),
                  models.Cut((3,), (1, 2, 4)),
                  models.Cut((4,), (1, 2, 3)),
                  models.Cut((2, 3, 4), (1,)),
                  models.Cut((1, 3, 4), (2,)),
                  models.Cut((1, 2, 4), (3,)),
                  models.Cut((1, 2, 3), (4,))]
        assert sia_bipartitions((1, 2, 3, 4)) == answer


def test_system_cut_styles(s, flushcache, restore_fs_cache):
    with config.override(SYSTEM_CUTS='3.0_STYLE'):
        assert compute.phi(s) == 2.3125

    with config.override(SYSTEM_CUTS='CONCEPT_STYLE'):
        assert compute.phi(s) == 0.6875
