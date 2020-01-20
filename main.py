import math

#needed for the next function
import subprocess
import importlib
import sys

# function that imports a library if it is installed, else installs it and then imports it
def getpack(package):
    try:
        return importlib.import_module(package)
        # import package
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", package],
  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return importlib.import_module(package)
        # import package

scipy = getpack("scipy")
np = getpack("numpy")

from scipy import optimize as opt


def sigma_p(weights,cov_matr):
    return math.sqrt(np.matmul(weights.transpose(),np.matmul(cov_matr,weights)))


def mu_check(weights,mus,mu_target):
    return mu_target-sum([weights[i]*mus[i] for i in range(len(weights))])


def optimal_portfolio(returns,mu_target,option=0):
    n = len(returns)

    mus = [np.mean(i) for i in returns]

    cov_matrix = np.cov(returns)


    # constraints
    # sum of all weights must be zero and portfolio mu must be target mu
    cons = [{'type': 'eq', 'fun': lambda x: 1 - sum(x)}, {'type': 'eq', 'fun': mu_check, 'args': (mus, mu_target)}]

    # without short-selling
    if option==0:
        #Required to have non negative values
        bnds = tuple((0,1) for x in range(n))

    #with short-selling
    elif option == 1:
        #Required to have non negative values
        bnds = tuple((-1,1) for x in range(n))

    else:
        print("Error invalid option")
        return

    res = opt.minimize(sigma_p, np.array([1.0/n] * n), method='SLSQP', args=(cov_matrix), bounds=bnds, constraints=cons)

    return res
