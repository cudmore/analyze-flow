from multiprocessing import Pool
import os
import numpy as np
import time

def f(n):
    return np.var(np.random.sample((n, n)))

if __name__ =='__main__':
    result_objs = []
    n = 2000
    with Pool(processes=os.cpu_count() - 4) as pool:
        for _ in range(n):
            result = pool.apply_async(f, (n,))
            result_objs.append(result)

        results = [result.get() for result in result_objs]
        print(len(results), np.mean(results), np.var(results))