from flask import Flask 
from main import get_crypto_close_price,get_list_of_cryptos,list_all_files,get_best_buy_sell
app = Flask(__name__)

@app.route('/list-all-cryptos')
def list_all_cryptos():
	result = {'data':[]}
	list_crypto_files = list_all_files()
	result['data'] = get_list_of_cryptos(list_crypto_files)
	return result

@app.route('/crypto-close-price/<crypto_name>/<crypto_date>')
def get_crypto_close_price_flask(crypto_name,crypto_date):
	result = get_crypto_close_price(crypto_name,crypto_date)
	return result

@app.route('/best_buy_sell/<start_date>/<end_date>')
def get_best_buy_sell_flask(start_date,end_date):
	result = {'data':[]}
	result['data'] = get_best_buy_sell(start_date,end_date)
	return result

if __name__ == '__main__':
	app.run(app.run(debug=True, use_debugger=True,host='0.0.0.0'))