import csv,os,requests
from peewee import Model,SqliteDatabase,CharField,DateField,FloatField,PrimaryKeyField
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd

db = SqliteDatabase('cryptocurrencies.db')

class CryptoCurrency(Model):
	sno = PrimaryKeyField()
	name = CharField()
	symbol = CharField()
	date = DateField()
	high = FloatField()
	low = FloatField()
	open = FloatField()
	close = FloatField()
	volume = FloatField()
	marketcap = FloatField()

	class Meta:
		database = db

#first answer:

#listing all the files in the data/archive
def list_all_files():
	cryptocurrency_path = 'data\\archive\\'
	list_crypto_files = []
	for filename in os.listdir(cryptocurrency_path):
		if os.path.isfile(os.path.join(cryptocurrency_path,filename)) and filename[0] != '.':
			list_crypto_files.append(filename)
	return list_crypto_files

#creating the classes dinamically
dict_of_classes = {}
for filename in list_all_files():
	new_filename = filename.replace('coin_','')
	new_filename = new_filename.replace('.csv','')
	dict_of_classes[new_filename] = type(new_filename,(CryptoCurrency,),dict())

#getting the list of names of the cryptos
def get_list_of_cryptos(list_crypto_files):
	list_of_crypto = []
	for filename in list_crypto_files:
		new_filename = filename.replace('coin_','')
		new_filename = new_filename.replace('.csv','')
		list_of_crypto.append(new_filename)
	return list_of_crypto

#creating the tables with peewee dinamically
def recreate_tables():
	db.connect()
	for value in dict_of_classes.values():
		db.drop_tables([value])
		db.create_tables([value])
	db.close()

#dumping all the data from the CSVs to the sqlite database 
def dump_csv_sqlite(list_crypto_files):
	db.connect()
	for filename in list_crypto_files:
		crypto_file = open('./data/archive/' + filename,'r')
		name = filename.replace('coin_','')
		name = name.replace('.csv','')
		crypto_csv = csv.reader(crypto_file)
		csv_headers = []
		csv_headers = next(crypto_csv)
		csv_headers = [x.lower() for x in csv_headers]
		dict_of_classes[name].insert_many(crypto_csv,fields=csv_headers).execute()
		crypto_file.close()
	db.close()

#second answer
def get_crypto_close_price(p_name,p_date):
	db.connect()
	crypto_class = dict_of_classes[p_name]
	query = crypto_class.select().where(crypto_class.date == p_date).get()
	message = {'data':''}
	message['data'] = 'The %s close price was %s in %s' % (query.name,query.close,query.date)
	db.close()
	return message

def get_best_buy_sell(user_start_date,user_end_date):
	db.connect()
	result = {}
	list_returned_text = []
	user_start_date = datetime.strptime(user_start_date,'%Y-%m-%d')
	user_end_date = datetime.strptime(user_end_date,'%Y-%m-%d')
	for crypto_name,crypto_class in dict_of_classes.items():
		result[crypto_name] = []
		list_tuple_date_price = []
		list_possible_results = []

		query = crypto_class.select(crypto_class.date,crypto_class.close).where(crypto_class.date.between(user_start_date,user_end_date))
		for row in query:
			list_tuple_date_price.append((row.date,row.close))

		list_tuple_date_price_sorted = sorted(list_tuple_date_price, key=lambda value: value[1])
		length_list = len(list_tuple_date_price_sorted)
		max_amount = int(length_list/2)+1
		min_amount = int(length_list/2)

		for i in range(0,min_amount):
			min_date = list_tuple_date_price_sorted[i][0]
			min_close = list_tuple_date_price_sorted[i][1]
			for r in range(0,max_amount):
				max_date = list_tuple_date_price_sorted[-1-r][0]
				max_close = list_tuple_date_price_sorted[-1-r][1]
				if min_date < max_date and min_close < max_close:
					
					difference = max_close - min_close
					list_possible_results.append((difference,min_date,max_date))
				if list_possible_results:
					best_result = sorted(list_possible_results,reverse=True)[0]
					duplicated = [reg for reg in result[crypto_name] if reg[1] == max_date or reg[0] == min_date]
					if not duplicated:
						result[crypto_name].append((best_result[1],best_result[2],best_result[0]))
					list_possible_results = []
		
	for crypto_name,best_profits in result.items():
		for row in best_profits:
			#print("The best profit about %s is in this date: %s  -  %s  giving us a profit of: %s" % (crypto_name,row[0],row[1],row[2]))
			list_returned_text.append("The best profit about %s is in this date: %s  -  %s  giving us a profit of: %s" % (crypto_name,row[0],row[1],row[2]))
	db.close()
	return list_returned_text
	

def show_candlestick_chart(crypto_name):
	list_crypto_data = []
	crypto_class = dict_of_classes[crypto_name]
	crypto_data = crypto_class.select()
	for row in crypto_data:
		list_crypto_data.append([row.date,row.open,row.close,row.high,row.low])
	dataframe = pd.DataFrame(list_crypto_data)
	dataframe.columns = ['date','open','close','high','low']
	dataframe = dataframe.set_index(pd.DatetimeIndex(dataframe['date'].values))
	figure = go.Figure(
		data = [
			go.Candlestick(
				x = dataframe.index,
				low = dataframe['low'],
				high = dataframe['high'],
				close = dataframe['close'],
				open = dataframe['open'],
				increasing_line_color = 'green',
				decreasing_line_color = 'red'
			)
		]
	)
	figure.show()
	#print(dataframe)


#the interactive tool function
def interactive_tool():
	user_input = ''
	while user_input == '':
		print("¡Bienvenid@ a la interfaz de consola de consulta de criptomonedas!")
		print("Hay estas opciones:")
		print("\t1-Listar el nombre de todas las criptomonedas.")
		print("\t2-Sacar el cierre de una criptomoneda según su fecha.")
		print("\t3-Según un rango de fechas, saber cuando es el mejor momento de comprar y vender.")
		print("\t4-Según una criptomoneda, saar su gráfico de velas japonesas.")
		print("\t5-Salir")
		user_input = input("¿Que función quieres invocar?:   ")

		if user_input == '1':
			response = requests.get('http://localhost:5000/list-all-cryptos')
			json_response = response.json()
			list_of_names = json_response['data']
			for name in list_of_names:
				print(name)
		elif user_input == '2':
			crypto_name_input = ''
			while crypto_name_input == '':
				print("Escribe el nombre de la criptomoneda en cuestión")
				crypto_name_input = input("Ej:Bitcoin,Monero,Dogecoin,CryptocomCoin:   ")
				try:
					dict_of_classes[crypto_name_input]
					print("Ahora introduce la fecha la cual quieras ver")
					crypto_date_input = input("Ej: \"2022-05-12\",\"2013-05-08\":    ")
					response = requests.get('http://localhost:5000/crypto-close-price/%s/%s' % (crypto_name_input,crypto_date_input))
					text_response = response.json()
					text_response = text_response['data']
					print(text_response)
					user_input = ''
				except KeyError:
					crypto_name_input = ''
					print("No se ha reconocido la moneda")
		elif user_input == '3':
			crypto_start_date = ''
			while crypto_start_date == '':
				print("Escribe la fecha de comienzo para invertir")
				crypto_start_date = input("Ej: \"2022-05-12\",\"2013-05-08\":    ")
				crypto_end_date = ''
				while crypto_end_date == '':
					print("Escribe la fecha de fin para invertir")
					crypto_end_date = input("Ej: \"2022-05-12\",\"2013-05-08\":    ")
					response = requests.get('http://localhost:5000/best_buy_sell/%s/%s' % (crypto_start_date,crypto_end_date))
					response_json = response.json()
					response_result = response_json['data']
					for reg in response_result:
						print(reg)
		elif user_input == '4':
			crypto_name_input = ''
			while crypto_name_input == '':
				print("Escribe el nombre de la criptomoneda para saber su gráfico en velas japonesas")
				crypto_name_input = input("Ej: Bitcoin, BinanceCoin, Tether...    ")
				show_candlestick_chart(crypto_name_input)
		elif user_input == '5':
			print("¡Hasta pronto!")
			break
		else:
			print("'Has pulsado una opción que no existe!")
			user_input = ''

if __name__ == '__main__':
	# descomenta primero las dos funciones de abajo
	#recreate_tables()
	#dump_csv_sqlite(list_all_files())

	# y despues puedes volver a comentarlas una vez hecho
	interactive_tool()
	show_candlestick_chart("Bitcoin")


