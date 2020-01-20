# this script test the program using the 4 asset example from
from main import *

import numpy as np
import pandas as pd

mean = (0.07, 0.08, 0.09, 0.1)
cov = [[0.0225, 0.009,0.0131,0.0113], [0.009, 0.04, 0.019,0.006], [0.0131, 0.019, 0.0625, 0.0113], [0.0113, 0.006, 0.0113, 0.09]]
returns = np.random.multivariate_normal(mean, cov, 1000000)
a=pd.DataFrame(data=returns)
returns=[a[0],a[1],a[2],a[3]]

mu_target = 0.0766

import time
t = time.time()
sigma_p([0.586,0.26,0.059,0.095],np.cov(returns))
print("%.3f" % (time.time()-t))

res2 = np.round(optimal_portfolio(returns,mu_target,0).fun,5)

print(f"{res1}=={res2}")

print(res1 == res2)

