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

def bordered(text):
    lines = text.splitlines()
    width = max(len(s) for s in lines)
    res = ['┌' + '─' * width + '┐']
    for s in lines:
        res.append('│' + (s + ' ' * width)[:width] + '│')
    res.append('└' + '─' * width + '┘')
    return '\n'.join(res)

def on_price_message(topic, data):
    print (data)
	#the following fields will vary by topic number you recieve (topic 105 in this case)
    print(f"Ticker: {topic['tickerId']}, Price: {data['deal']['price']}, "
        + f"Volume: {data['deal']['volume']}, Trade time: {data['tradeTime']}")
	#all your algo precessing code goes here

def on_order_message(topic, data):
    print(data)

@click.group()
def main():
    if os.path.exists('session.pickle'):
        try:
            sesh = pickle.load(open(SESSION_FILE,'rb'))
            print('===== {}Logged In ✓{}\n===== Current User: {}{}{}\n===== Refresh Token: {}\n===== Session Expiration Date: {}\n'.format(BOLD,GREEN,ENDC,BLUE,sesh['settings']['userId'], ENDC, sesh['refreshToken'], sesh['tokenExpireTime']))
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
        print('Price for {}{}{}: {}\n'.format(YELLOW, ticker.upper(), ENDC, wb.get_quote(stock=ticker)['pPrice']))
    except:
        print('{}Ticker name {}{}{} was not found{}\n'.format(FAIL, YELLOW, ticker.upper(), RED, ENDC))

@main.command()
@click.argument('ticker')
def stream_stock_price(ticker):
    conn = streamconn.StreamConn(debug_flg=True)
    conn.price_func = on_price_message
    conn.order_func = on_order_message
    if not wb._access_token is None and len(wb._access_token) > 1:
        conn.connect(wb._did, access_token=wb._access_token)
    else:
        conn.connect(wb._did)
    conn.subscribe(tId=wb.get_ticker(ticker))
    conn.run_loop_once()
    conn.run_blocking_loop()

if __name__ == "__main__":
    main()
