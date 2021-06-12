import logging
import random
import numpy as np
from pymoo.model.problem import Problem
from pymoo.model.crossover import Crossover
from pymoo.model.mutation import Mutation
from pymoo.model.sampling import Sampling
from pymoo.algorithms.so_genetic_algorithm import GA
from pymoo.algorithms.nsga2 import NSGA2

from pymoo.optimize import minimize

class SubsetProblem(Problem):
    def __init__(self,
                 L,
                 fixed,
                 groups,
                 func
                 ):
        nvar = len(L[0]) - fixed
        super().__init__(n_var=len(L[0]), n_obj=1, n_constr=1, elementwise_evaluation=True)
        self.L = L
        self.nvar = nvar
        self.groups = []
        self.func = func
        pos = fixed
        for grp in groups:
            self.groups.append((pos, grp[0], grp[1]))
            pos += grp[0]
        self.n_max = sum(_[1] for _ in groups)

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = - self.func(self.L, x)
        out["G"] = (self.n_max - np.sum(x)) > 0


class MySampling(Sampling):

    def _do(self, problem, n_samples, **kwargs):
        X = np.full((n_samples, len(problem.L[0])), False, dtype=bool)
        for i in range(len(problem.L[0]) - problem.nvar):
            X[:, i] = True
        for k in range(n_samples):
            arr = []
            for grp in problem.groups:
               arr.append(grp[0] + np.random.permutation(grp[1])[:grp[2]])
            I = np.concatenate(arr)
            X[k, I] = True

        return X


class BinaryCrossover(Crossover):
    def __init__(self):
        super().__init__(2, 1)

    def _do(self, problem, X, **kwargs):
        n_parents, n_matings, n_var = X.shape

        _X = np.full((self.n_offsprings, n_matings, problem.n_var), False)

        for k in range(n_matings):
            p1, p2 = X[0, k], X[1, k]
            both_are_true = np.logical_and(p1, p2)
            _X[0, k, both_are_true] = True
            for start, count, max_n in problem.groups:
                end = start + count
                n_remaining = max_n - np.sum(both_are_true[start:end])
                I = start + np.where(np.logical_xor(p1[start:end], p2[start:end]))[0]
                S = I[np.random.permutation(len(I))][:n_remaining]
                _X[0, k, S] = True

        return _X


class MyMutation(Mutation):
    def _do(self, problem, X, **kwargs):
        for i in range(X.shape[0]):
            grp = problem.groups[random.randrange(len(problem.groups))]
            X[i, :] = X[i, :]
            is_false = grp[0] + np.where(np.logical_not(X[i, grp[0]:grp[0]+grp[1]]))[0]
            is_true = grp[0] + np.where(X[i, grp[0]:grp[0]+grp[1]])[0]
            X[i, np.random.choice(is_false)] = True
            X[i, np.random.choice(is_true)] = False

        return X


def run_optimizer(stats, offset, item_groups, func):
    problem = SubsetProblem(stats, offset, item_groups, func)

    #algorithm = NSGA2(
    algorithm = GA(
        pop_size=stats.shape[1]-offset,
        sampling=MySampling(),
        crossover=BinaryCrossover(),
        mutation=MyMutation(),
        eliminate_duplicates=True)

    res = minimize(problem,
                   algorithm,
                   ('n_gen', 60),
                   seed=1,
                   verbose=False)
    print("Function value: %s" % res.F[0])
    print("Subset:", np.where(res.X)[0])
    return np.where(res.X)[0], res
