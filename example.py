import threading
import itertools
import time

# this will later be used to add a loading '...' to some text
done_dot=False


def dotdotdot(text):
    for c in itertools.cycle(['.', '..', '...','']):
        if done_dot:
            break
        sys.stdout.write('\r'+text+c)
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write('\nDone!')


# needed for the next function
import subprocess
import importlib


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


# import necessary packages
from eff_fron import *
pd = getpack("pandas")
yf = getpack("yfinance")
bs = getpack("bs4")
requests = getpack("requests")
plt = getpack("matplotlib.pyplot")
import random


# get the tickers of all stocks in the SP500
def sp500_tickers():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        ticker = ticker.replace("\n", "")
        tickers.append(ticker)

    return tickers


# get the returns for a given list of tickers
def get_returns(tickers):
    returns = []

    # keep track of number of requests
    n_requests = 0
    # for tickers with insufficient return data
    insufficient = []
    print("Downloading return-information, this might takes some time.", end='\r')
    for i in tickers:
        # get data
        data_tick = yf.Ticker(i)
        # daily changes of past 1-years in percent
        ret = data_tick.history(period="1y").Close
        ret = [ret1 / ret2 - 1 for ret1, ret2 in zip(ret[1:], ret)]
        if len(ret) == 250:
            returns.append(ret)
        else:
            insufficient.append(i)
        del ret

        n_requests += 1
        print(f"Downloading return-information, this might takes some time. ({n_requests}/{len(tickers)})", end='\r')

    print("\nReturns downloaded.")
    if len(insufficient) > 0:
        print(f"The following tickers will be omitted because of insufficient data: {', '.join(insufficient)}.\n"
              f"This could be due to the company going public within the last year or no information being available on"
              f" Yahoo finance.")
    print("\n")

    return returns


# generate random portfolio weights for the random portfolios in the visualization
def random_weights(n, k):
    return np.random.dirichlet(np.ones(n), size=k)


def main():
    # for dotdotdot function
    global done_dot

    print("Welcome, this is a cmd-line interface tool to calculate minimum risk portfolio weights for a given set of "
          "stocks and a selected expected return  (daily).")
    print("In other words, this script calculated the portfolio weights and standard deviation for a portfolio at point"
          " mu_p of the efficient frontier.")
    print("If you are unfamiliar with Moskowitz's Efficient Frontier please read the README.md file.\n")

    while True:
        done_dot = False
        sel = input("\nIf you want to run a simulation for a custom group of (U.S.) stocks enter '0'.\n"
                    "If you want to run a simulation for all stocks within the SP500 "
                    "enter '1'. Disclaimer: depending on your hardware this might take very long or not work at all.\n"
                    "If you want to run a simulation for a random sample of stocks within the SP500 enter '2'\n\n"
                    "To end the program enter 'q'\n")

        # end program/loop if q is entered
        if sel == 'q':
            break

        # if custom portfolio get ticker input
        elif sel == '0':
            tickers = [x for x in input("Please enter the tickers of the stocks you want to include in your portfolio."
                                        " Seperate them by a space: ").split()]

        # if not custom either draw a sample of SP500 or use all (depending on selection)
        elif sel == '1' or sel == '2':
            tickers = sp500_tickers()
            if sel == '2':
                tickers = random.sample(tickers, int(input("How many securities should be in your random sample: ")))

        else:
            print("invalid selection")

        # get returns and whether short-selling should be incorporated
        returns = get_returns(tickers)
        option = int(input("If you want to incorporate short selling enter '1' else enter '0': "))

        # expected returns and covariance matrix
        mus = [np.mean(i) for i in returns]
        cov_m = np.cov(returns)

        # load weights result into df
        results = pd.DataFrame(list(zip(tickers, mus, [np.std(i) for i in returns])),
                               columns=["Ticker", "expected return", "standard dev"])
        pd.set_option('display.max_rows', results.shape[0] + 1)
        print(results)

        # get target return
        mu_target = float(input(f"Please enter your target return (e.g.: 5% as 0.05):"))

        # prepare a loading message
        t = threading.Thread(target=dotdotdot, args=("Calculating optimal portfolio, this may take some time",))
        # starting loading... thread
        t.start()

        # get risk-free rate e.g. 3-month t-bill
        # rf = yf.Ticker("^IRX").history(period="1y").Close[-1] / 100
        # rf = (1 + rf) ** (1 / 60) - 1
        rf = 0.0

        # risk minimizing portfolio for target return (or max possible return)
        res = optimal_portfolio(mus, cov_m, mu_target, rf, option)

        # minimum variance portfolio
        min_var = min_var_portfolio(mus, cov_m, rf)

        # calculate some portfolios on the frontier for visualization
        r_range = np.linspace(min_var.mu, max(mus), 75)
        efficient_fron = efficient_frontier(mus, cov_m, rf, r_range)
        del r_range

        # The code below could be used to calculate the tangency portfolio. Since this programm works with daily
        # returns, and I could not find a satisfactory solution for a daily risk free rate, it is not implemented.
        # tang_port = tangency_portfolio(mus, cov_m,rf)

        # end loading '...'
        done_dot = True
        time.sleep(0.3)
        print("\n")

        # display results and additional information
        print(f"The risk-minimizing portfolio for your selection has a standard deviation of {round(res.std,5)}, "
              f"an expected return of {round(res.mu,5)} and the following weights on the securities:")

        # make sure all rows will be displayed

        results["weights"] = [round(i, 5) for i in res.weights]
        pd.set_option('display.max_rows', results.shape[0] + 1)
        print(results)

        # if target mu and real mu differ more than 1 percent
        if abs(mu_target - res.mu) >= mu_target*0.01:
            print(f"\nYour target return of {mu_target} could not be reached. Try to integrate shortselling.")

        if min_var.mu > res.mu:
            print(f"\nAttention: though this portfolio minimizes the risk for your chosen return, the minimal risk "
                  f"portfolio achieves a higher mean return ({round(min_var.mu,5)}) with a standard deviation of "
                  f"{round(min_var.std,5)}. The weights on the minimal risk portfolio are: {min_var.weights}\n")

        # visualization option
        if 'y' in input("Would you like to see this result on the efficient frontier? (y/n)   "):
            # random portfolios for scatter plot
            rand_mus = []
            rand_std = []
            rand_sr = []

            for i in random_weights(len(tickers), len(tickers)*4000):
                r_mu = sum([i[j] * mus[j] for j in range(len(tickers))])
                rand_mus.append(r_mu)
                r_sig = sigma_p(i, cov_m)
                rand_std.append(r_sig)
                rand_sr.append((r_mu-rf)/r_sig)

            plt.scatter(rand_std, rand_mus, c=rand_sr, cmap='YlGnBu', marker='o', s=10, alpha=0.2)
            plt.title('Portfolio Optimization based on Efficient Frontier')
            plt.xlabel('Standard deviation')
            plt.ylabel('Expected return')
            plt.colorbar().set_label('Sharpe ratio')

            # chosen portfolio, minimum variance portfolio, tangency portfolio and efficient frontier
            plt.scatter(res.std, res.mu, marker='*', s=25, c='red', label="Your portfolio")
            plt.scatter(min_var.std, min_var.mu, marker='D', s=25, c='darkgreen', label="Minimum variance")
            # plt.scatter(tang_port.std, tang_port.mu, marker='^', s=25, c='gold', label="Tangency portfolio")
            plt.plot([p.std for p in efficient_fron], [p.mu for p in efficient_fron], linestyle='-.', color='black',
                     label='efficient frontier')

            plt.legend()

            plt.show()

            del rand_mus, rand_std

        if 'n' in input("Do you want to run another simulation? (y/n)   "):
            break

    print("Thank you.\nGoodbye.")


main()
