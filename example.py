import threading
import itertools
import time

#this will later be used to add a loading ... to some text
done_dot=False
def dotdotdot(text):
    for c in itertools.cycle(['.', '..', '...','']):
        if done_dot:
            break
        sys.stdout.write('\r'+text+c)
        sys.stdout.flush()
        time.sleep(0.3)
    sys.stdout.write('\nDone!')


#needed for the next function
import subprocess
import importlib

# function that imports a library if it is installed, else installs it and then imports it
def getpack(package):
    try:
        return (importlib.import_module(package))
        # import package
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", package],
  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return (importlib.import_module(package))
        # import package


from main import *
pd = getpack("pandas")
yf = getpack("yfinance")
bs=getpack("bs4")
requests=getpack("requests")
plt = getpack("matplotlib.pyplot")

# needed for random sample example
import random


def sp500_tickers():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        ticker = ticker.replace("\n","")
        tickers.append(ticker)

    return tickers

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
        print(f"The following tickers will be omitted because of insufficient data: {', '.join(insufficient)}.\nThis could be due to"
          f" the company going public within the last year or no information being available on Yahoo finance.")
    print("\n")

    return returns

def random_weights(n,k):
    return np.random.dirichlet(np.ones(n),size=k)



def main():
    # for dotdotdot function
    global done_dot

    print("Welcome, this is a cmd-line interface tool to calculate minimum risk portfolio weights for a given set of "
          "stocks and a selected expected return.")
    print("In other words, this script calculated the portfolio weights and standard deviation for a portfolio at point"
          " mu_p of the efficient frontier.")
    print("If you are unfamiliar with Moskowitz's Efficient Frontier please read the README.md file.\n")


    while True:
        done_dot = False
        sel = input("\nIf you want to run a simulation for a custom group of (U.S.) stocks enter '0'.\n"
                    "If you want to run a simulation for all stocks within the SP500 "
                    "enter '1'.\n"
                    "If you want to run a simulation for a random sample of stocks within the SP500 enter '2'\n\n"
                    "To end the program enter 'q'\n")

        if sel == 'q':
            break

        elif sel == '0':
            tickers = [x for x in input("Please enter the tickers of the stocks you want to include in your portfolio."
                                        " Seperate them by a space: ").split()]
            returns = get_returns(tickers)

        elif sel == '1' or sel == '2':
            tickers = sp500_tickers()
            if sel == '2':
                tickers = random.sample(tickers, int(input("How many securities should be in your random sample: ")))
            returns = get_returns(tickers)

        else:
            print("invalid selection")

        option = int(input("If you want to incorporate short selling enter '1' else enter '0': "))

        mus = [np.mean(i) for i in returns]
        # if we allow short selling and
        if option == 1:
            mu_target = float(input(f"Please enter your target return (must be < {max(mus,key=abs)} and"
                                    f" > -{max(mus,key=abs)})."))
            if not abs(mu_target) <= max(mus,key=abs):
                print("Bad selection.")
                break

        else:
            mu_target = float(input(f"Please enter your target return (must be < {max(mus)} and"
                                    f" > {min(mus)})."))
            if not min(mus) <= mu_target <= max(mus):
                print("Bad selection.")
                break

        # prepare a loading message
        t = threading.Thread(target=dotdotdot, args=("Calculating optimal portfolio, this may take some time",))
        # starting loading... thread
        t.start()

        res = optimal_portfolio(returns, mu_target, option)

        done_dot = True
        time.sleep(0.3)
        print("\n")

        opt_weights = res.x
        opt_ret = sum([a*b for a,b in zip(opt_weights,mus)])
        opt_std = res.fun

        # load weights result into df
        results = pd.DataFrame(list(zip(tickers, mus, [np.std(i) for i in returns], [round(i,5) for i in opt_weights])),
                               columns=["Ticker", "expected return", "standard dev", "weights"])

        print(f"The risk-minimizing portfolio for your selection has a standard deviation of {round(opt_std,5)}, "
              f"an expected return of {round(opt_ret,5)} and the following weights on the securities:")

        # make sure all rows will be displayed
        pd.set_option('display.max_rows', results.shape[0] + 1)
        print(results)

        #ToDo improve Visualization (add line)
        if 'y' in input("Would you like to see this result on the efficient frontier? (y/n)   "):
            cov_m = np.cov(returns)
            rand_ports = random_weights(len(tickers), 25000)
            rand_mus = []
            rand_std = []

            for i in rand_ports:
                rand_mus.append(sum([i[j]*mus[j] for j in range(len(tickers))]))
                rand_std.append(sigma_p(i,cov_m))

            plt.scatter(rand_std,rand_mus, marker='o', s=10, alpha=0.3)
            plt.title('Portfolio Optimization based on Efficient Frontier')
            plt.xlabel('Standard deviation')
            plt.ylabel('Expected return')
            plt.ylim(bottom=min(rand_mus)-.1*abs(min(rand_mus)),top=max(rand_mus)+.1*abs(max(rand_mus)))

            plt.scatter(opt_std,opt_ret, marker='x', s=20, label="Your portfolio")
            plt.legend()

            plt.show()

            print()

        if 'n' in input("Do you want to run another simulation? (y/n)   "):
            break


    print("Thank you.\nGoodbye.")







main()

#todo unit thing (returns)