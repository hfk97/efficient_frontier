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


def main():
    # for dotdotdot function
    global done_dot

    print("Welcome, this is a cmd-line interface tool to calculate minimum risk portfolio weights for a given set of "
          "stocks and a selected expected return.")
    print("In other words, this script calculated the portfolio weights and standard deviation for a portfolio at point"
          " mu_p of the efficient frontier.")
    print("If you are unfamiliar with Moskowitz's Efficient Frontier please read the README.md file.\n")


    while True:
        sel = input("\nIf you want to run a simulation for a custom group of (U.S.) stocks enter '0'.\n"
                    "If you want to run a simulation for all stocks within the SP500 "
                    "enter '1'.\n\nTo end the program enter 'q'")

        if sel == 'q':
            break

        elif sel == '0':
            tickers = [x for x in input("Please enter the tickers of the stocks you want to include in your portfolio."
                                        " Seperate them by a space: ").split()]
            mu_target = float(input("Please enter your target return in 0.XX format: "))
            option = int(input("If you want to incorporate shortselling enter '1' else enter '0': "))

            returns = get_returns(tickers)

        elif sel == '1':
            tickers = sp500_tickers()
            option = int(input("If you want to incorporate shortselling enter '1' else enter '0': "))
            mu_target = float(input("Please enter your target return in 0.XX format: "))

            returns = get_returns(tickers)

        else:
            print("invalid selection")

        #ToDo random portfolio example

        # prepare a loading message
        t = threading.Thread(target=dotdotdot, args=("Calculating optimal portfolio, this may take some time",))
        # starting loading... thread
        t.start()

        optimal_portfolio(returns, mu_target, option)

        done_dot = True
        time.sleep(0.3)
        print("\n")

        #ToDo Visualization option


    print("Thank you.\nGoodbye.")








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

    print(f"The following tickers will be omitted because of insufficient data: {', '.join(insufficient)}.\nThis could be due to"
          f" the company going public within the last year or no information being available on Yahoo finance.")

    return returns


main()
