import matplotlib.pyplot as plt
import sklearn.metrics as metrics
import numpy as np

from svdd_primal_sgd import SvddPrimalSGD
from cluster_svdd import ClusterSvdd


def generate_data(datapoints, outlier_frac=0.1, dims=2):
    X = np.zeros((dims, datapoints))
    y = np.zeros(datapoints)

    num_noise = np.floor(datapoints*outlier_frac)
    num_dpc = np.floor(float(datapoints-num_noise)/2.0)

    X[:, :num_noise] = 0.5*np.random.randn(dims, num_noise) + 0.
    y[:num_noise] = -1

    cnt = num_noise
    X[:, cnt:cnt+num_dpc] = 1.5*np.random.randn(dims, num_dpc) - 1.
    y[cnt:cnt+num_dpc] = 1
    cnt += num_dpc

    X[:, cnt:] = 0.5*np.random.randn(dims, num_dpc) + 1.
    y[cnt:] = 2
    return X, y


def plot_results(res_filename):
    foo = np.load(res_filename)
    maris = foo['maris']
    saris = foo['saris']
    nus = foo['nus']

    plt.figure(1)
    cols = np.random.rand(maris.shape[1], 3)
    fmts = ['-->', '--o', '--D', '--s', '--H']
    for i in range(maris.shape[1]):
        plt.errorbar(nus, maris[:, i], saris[:, i], fmt=fmts[i], color=cols[i, :], \
                     ecolor=cols[i, :], linewidth=2.0, elinewidth=1.0, alpha=0.8)
    for i in range(maris.shape[1]):
        plt.errorbar(nus[-1], maris[-1, i], saris[-1, i], \
                     color='r', ecolor='r', fmt=fmts[i][-1], markersize=6, linewidth=4.0, elinewidth=4.0, alpha=0.7)

    plt.xlim((-0.05, 1.05))
    plt.ylim((-0.05, 1.05))
    plt.xticks([0.0, 0.25, 0.5, 0.75, 1.0], ['0.0', '0.25', '0.5', '0.75', '1.0 = k-means'], fontsize=14)
    plt.yticks([0.0, 0.25, 0.5, 0.75, 1.0], fontsize=14)
    plt.grid()
    plt.xlabel(r'regularization parameter $\nu$', fontsize=14)
    plt.ylabel(r'Adjusted Rand Index (ARI)', fontsize=14)
    names = list()
    for i in range(maris.shape[1]):
        names.append('ClusterSVDD ($k$={0})'.format(ks[i]))
    for i in range(maris.shape[1]):
        names.append('$k$-means ($k$={0})'.format(ks[i]))
    plt.legend(names, loc=4, fontsize=14)

    plt.show()


def evaluate(res_filename, nus, ks, outlier_frac, reps, num_train, num_test):
    train = np.array(range(num_train), dtype='i')
    test = np.array(range(num_train, num_train + num_test), dtype='i')

    aris = np.zeros((reps, len(nus), len(ks)))
    for n in range(reps):
        # generate new gaussians
        data, y = generate_data(num_train + num_test, outlier_frac=outlier_frac)
        inds = np.random.permutation(range(num_test + num_train))
        data = data[:, inds]
        y = y[inds]
        for k in range(len(ks)):
            # fix the initialization for all methods
            membership = np.random.randint(0, ks[k], y.size)
            for i in range(len(nus)):
                svdds = list()
                for l in range(ks[k]):
                    svdds.append(SvddPrimalSGD(nus[i]))
                svdd = ClusterSvdd(svdds)
                svdd.fit(data[:, train], init_membership=membership[train])
                _, classes = svdd.predict(data[:, test])
                # evaluate clustering abilities
                inds = np.where(y[test] >= 0)[0]
                aris[n, i, k] = metrics.cluster.adjusted_rand_score(y[test[inds]], classes[inds])

    maris = np.mean(aris, axis=0)
    saris = np.std(aris, axis=0)
    print np.mean(aris, axis=0)
    print np.std(aris, axis=0)
    np.savez(res_filename, maris=maris, saris=saris, outlier_frac=outlier_frac,
             ntrain=num_train, ntest=num_test, reps=reps, nus=nus)


if __name__ == '__main__':
    nus = (np.arange(1, 21)/20.)
    ks = [2, 3, 4]

    outlier_frac = 0.05  # fraction of uniform noise in the generated data
    reps = 50  # number of repetitions for performance measures
    num_train = 1000
    num_test = 2000

    do_plot = False
    do_evaluation = True

    res_filename = 'res_robust_{0}_{1}_{2}_rbf.npz'.format(reps, len(ks), len(nus))

    if do_evaluation:
        evaluate(res_filename, nus, ks, outlier_frac, reps, num_train, num_test)
    if do_plot:
        plot_results(res_filename)

    print('DONE :)')
