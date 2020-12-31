from webull import webull, streamconn
# cli.py
import click
import pickle
import os

HEADER = '\033[95m'
BLUE = '\033[94m'
CYAN = '\033[96m'
GREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
RED = '\u001b[31m'
YELLOW = '\u001b[33m'
MAGENTA = '\u001b[35m'
SESSION_FILE = 'session.pickle'

wb = webull()
cur_stream_ticker = ''

def bordered(text):
    lines = text.splitlines()
    width = max(len(s) for s in lines)
    res = ['┌' + '─' * width + '┐']
    for s in lines:
        res.append('│' + (s + ' ' * width)[:width] + '│')
    res.append('└' + '─' * width + '┘')
    return '\n'.join(res)

def on_price_message(topic, data):
    # print (data)
	#the following fields will vary by topic number you recieve (topic 105 in this case)
    global cur_stream_ticker
    print(f"Ticker: {cur_stream_ticker.upper()}({topic['tickerId']}), Price: {data['deal']['price']}", end="\r", flush=True)
	#all your algo precessing code goes here

def on_order_message(topic, data):
    print('Order message: '+data)

@click.group()
def main():
    if os.path.exists('session.pickle'):
        try:
            sesh = pickle.load(open(SESSION_FILE,'rb'))
            print('===== {}Logged In ✓{}\n===== Current User: {}{}{}\n===== Refresh Token: {}\n===== Session Expiration Date: {}\n'.format(GREEN,ENDC,BLUE,sesh['settings']['userId'], ENDC, sesh['refreshToken'], sesh['tokenExpireTime']))
            if 'accessToken' in sesh:
                wb._access_token = sesh['accessToken']
                wb._refresh_token = sesh['refreshToken']
                wb._token_expire = sesh['tokenExpireTime']
                wb._uuid = sesh['uuid']
                wb._account_id = sesh['account_id']
        except Exception as exception:
            print('{}Session file was unable to load, resetting session{}'.format(FAIL, ENDC))
            filename = os.path.join('', SESSION_FILE)
            if os.path.exists(filename):
              os.remove(filename)
    else:
        print('===== {}User is not logged in{}\n===== Please run {}sendmfa{} before {}login{} to get mfa code\n'.format(FAIL, ENDC,BLUE, ENDC, BLUE, ENDC))

@main.command()
def status():
    pass

@main.command()
@click.argument('email')
def getmfa(email):
    print('Sending MFA Code to {}{}{}'.format(CYAN,email,ENDC))
    wb.get_mfa(email) #mobile number should be okay as well.
    print('MFA code sent')

@main.command()
@click.argument('email')
@click.argument('password')
@click.argument('mfa_code')
def login(email, password, mfa_code):
    print('Logging into webull')
    login_response = wb.login(email, password, mfa=mfa_code)
    wb._access_token = login_response['accessToken']
    wb._refresh_token = login_response['refreshToken']
    wb._token_expire = login_response['tokenExpireTime']
    wb._uuid = login_response['uuid']
    login_response['account_id'] = wb.get_account_id()
    filename = os.path.join('', SESSION_FILE)
    if os.path.exists(filename):
        print('{}Overwriting existing session with new login{}'.format(WARNING, ENDC))
    pickle.dump(login_response, open(filename, 'wb'))
    print('{}Login Successfull{}'.format(GREEN,ENDC))
    print('===== {}Logged In ✓{}\n===== Current User: {}{}{}\n===== Refresh Token: {}\n===== Session Expiration Date: {}\n'.format(BOLD,GREEN,ENDC,BLUE,login_response['settings']['userId'], ENDC, login_response['refreshToken'], login_response['tokenExpireTime']))

@main.command()
def logout():
    if wb._access_token == '':
        print('User already logged out')
        return
    wb.logout()
    filename = os.path.join('', SESSION_FILE)
    if os.path.exists(filename):
      os.remove(filename)
    print('User successfully logged out')
    print('===== {}User is not logged in{}\n===== Please run {}sendmfa{} before {}login{} to get mfa code\n'.format(FAIL, ENDC,BLUE, ENDC, BLUE, ENDC))

@main.command()
@click.argument('ticker')
def get_stock_price(ticker):
    try:
        stock_quote = wb.get_quote(stock=ticker)
        print('Price for {}{}{}: {}{}{}, bid: {}, ask: {}\n'.format(YELLOW, ticker.upper(), ENDC, GREEN, sum([float(stock_quote['askList'][0]['price']),float(stock_quote['bidList'][0]['price'])])/2, ENDC, stock_quote['bidList'][0]['price'], stock_quote['askList'][0]['price']))
    except Exception as e:
        print(e)
        print('{}Ticker name {}{}{} was not found{}\n'.format(FAIL, YELLOW, ticker.upper(), RED, ENDC))

@main.command()
@click.argument('ticker')
def buy(ticker):
    # quantity must be 95% of daytrading margin
    try:
        wb.get_trade_token('123456')
        wb.place_order(stock=ticker, price=0, quant=0)
    except Exception as e:
        print('Error while placing order')
        print(e)

@main.command()
def watch_pos():
    try:
        positions = wb.get_positions()
        if not(len(positions)>0):
            print('No positions were found\n')
            return
        for i, position in enumerate(positions):
            print('{}.'.format(i+1), end='')
            print('\tTicker: {}\n\tPositon: {} shares\n'.format(position['ticker']['symbol'], position['position']))
        option_pick = input('Select which position to watch: ')
        print('Watching', positions[int(option_pick)-1]['ticker']['symbol'])
        print('Type following commands for {}'.format(positions[int(option_pick)-1]['ticker']['symbol']))
        print('(1) Set stop loss at breakeven, (2) Set stop loss slightly above breakeven (3) Set own stop loss')

    except Exception as e:
        print('Something went wrong:', e)

# Position response
# [{'id': 398413331259465728, 'brokerId': 8, 'ticker': {'tickerId': 913324077, 'symbol': 'MU', 'name': 'Micron Tech', 'tinyName': 'Micron Tech', 'listStatus': 1, 'exchangeCode': 'NAS', 'exchangeId': 10, 'type': 2, 'regionId': 6, 'currencyId': 247, 'currencyCode': 'USD', 'secType': [61], 'disExchangeCode': 'NASDAQ', 'disSymbol': 'MU'}, 'position': '850', 'assetType': 'stock', 'cost': '63877.50', 'costPrice': '75.150', 'currency': 'USD', 'lastPrice': '75.08', 'marketValue': '63818.00', 'unrealizedProfitLoss': '-59.50', 'unrealizedProfitLossRate': '-0.0009', 'positionProportion': '1.0000', 'exchangeRate': '1', 'lock': False, 'updatePositionTimeStamp': 1609435085000}]


# open market response
# {'tickerId': 913254235, 'exchangeId': 10, 'type': 2, 'secType': [61], 'regionId': 6, 'regionCode': 'US', 'currencyId': 247, 'name': 'AMD', 'symbol': 'AMD', 'disSymbol': 'AMD', 'disExchangeCode': 'NASDAQ', 'exchangeCode': 'NAS', 'listStatus': 1, 'template': 'stock', 'derivativeSupport': 1, 'tradeTime': '2020-12-31T15:03:31.110+0000', 'status': 'T', 'close': '91.45', 'change': '-0.85', 'changeRatio': '-0.0092', 'marketValue': '109981965736.91', 'volume': '5151536', 'turnoverRate': '0.0043', 'timeZone': 'America/New_York', 'tzName': 'EST', 'preClose': '92.29', 'open': '92.12', 'high': '92.30', 'low': '90.87', 'vibrateRatio': '0.0155', 'avgVol10D': '30466435', 'avgVol3M': '46084705', 'negMarketValue': '109300183914.11', 'pe': '277.95', 'forwardPe': '74.26', 'indicatedPe': '485.12', 'peTtm': '284.88', 'eps': '0.3290', 'epsTtm': '0.3210', 'pb': '28.42', 'totalShares': '1202711638', 'outstandingShares': '1195255989', 'fiftyTwoWkHigh': '97.98', 'fiftyTwoWkLow': '18.90', 'yield': '0.0000', 'baSize': 1, 'ntvSize': 0, 'askList': [{'price': '91.45', 'volume': '100'}], 'bidList': [{'price': '91.43', 'volume': '300'}], 'currencyCode': 'USD', 'lotSize': '1', 'latestDividendDate': '2000-08-22', 'latestSplitDate': '2000-08-22', 'latestEarningsDate': '2020-10-27', 'ps': '12.76', 'bps': '3.217', 'estimateEarningsDate': '01/26-02/01', 'tradeStatus': 'T'}

@main.command()
@click.argument('ticker')
def stream_stock_price(ticker):
    global cur_stream_ticker
    try:
        cur_stream_ticker = ticker
        conn = streamconn.StreamConn(debug_flg=False)
        conn.price_func = on_price_message
        conn.order_func = on_order_message
        if not wb._access_token is None and len(wb._access_token) > 1:
            conn.connect(wb._did, access_token=wb._access_token)
        else:
            conn.connect(wb._did)
        conn.subscribe(tId=wb.get_ticker(ticker))
        conn.run_loop_once()
        conn.run_blocking_loop()
    except:
        cur_stream_ticker = ''
        print('Closing stream')

if __name__ == "__main__":
    main()
