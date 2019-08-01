import sqlite3
import string, random
from datafeed import get_stockInfo

# SQLite visualization tricks
# .schema <tablename>
# .mode column
# .headers on

# Controller
class Controller(object):
    def __init__(self):
        pass

    # Initialize all tables
    def init_table(self):
        model = Model()
        model.init_all_table()

    # return # of rows in the table (# of users / # of portfolios...)
    def count(self, tablename):
        model = Model()
        nb = model.count(tablename)
        return nb

    # delete all records in the table
    def clear(self, tablename):
        model = Model()
        model.delete_all(tablename)

    # insert a new user into the <Users> table
    def register_user(self, username, password):
        model = UserModel()
        model.register(username, password)

    # return a dict of all the information of a user
    def get_user(self, username):
        model = UserModel()
        info = model.get_user(username)
        cols = model.get_columns('Users')
        return dict(zip(cols, info))

    # return True if not exist, okay to register
    # return False if already exist, can't register
    def not_exist_username(self, username):
        model = UserModel()
        return model.not_exist_username(username)

    # return the password for the username
    def get_password(self, username):
        model = UserModel()
        password = model.get_password(username)
        return password

    # add a portfolio to a user account
    # assume tickers is a list
    def add_portfolio(self, username, port_name, port_time, symbols):
        """
        :param username: 
        :param port_name: 
        :param port_time: 
        :param symbols: [(symbol1, market1), (symbol2, market2)...]
        :return: 
        """
        # security
        # Ensure the user exists before adding
        userModel = UserModel()
        check_user = userModel.not_exist_username(username)
        if check_user:
            return False
        
        # create a new portfolio in <Portfolio> table
        portModel = PortfolioModel()
        port_id = portModel.add_portfolio(port_name, port_time)[0][0]

        # link to users in <PORT_USER> table
        user_id = self.get_user(username)['ID']
        port_userModel = Port_UserModel()
        port_userModel.insertPort(port_id, user_id)

        # link the symbols and portfolio in <PORT_STOCK> table
        port_stockModel = Port_StockModel()
        for symbol in symbols:
            sym = symbol[0]
            mkt = symbol[1]
            
            port_stockModel.insertPort(port_id, sym, mkt)
            
        return True

    # return a list of Portfolio IDs for the user
    def get_PortIDs(self, username):
        userModel = UserModel()
        
        # security
        # Ensure the user exists before getting the details
        check_user = userModel.not_exist_username(username)
        if check_user:
            return []
        
        user_id = userModel.get_user(username)[0]            
        model = Port_UserModel()
        portIDs = model.get_portIDs(user_id)
        result = []
        for id in portIDs:
            result.append(id[1])
            
        return result

    # Don't use it, assume already loaded.
    def _load_symbols(self):
        stockModel = StockModel()
        stocks = get_stockInfo('nasdaq', 'asx', 'nyse')
        for stock in stocks:
            stockModel.add_ticker(stock['Symbol'], stock['market'],
                                  stock['Name'], stock['Sector'])

    # Delete a portfolio by port_id
    def delete_portfolio(self, port_id):
        models = [PortfolioModel(), Port_StockModel(), Port_UserModel()]
        for model in models:
            m = model
            m.del_portfolio(port_id)

    # Update the name of a portfolio into a new name
    def rename_portfolio(self, port_id, name):
        PortModel = PortfolioModel()
        PortModel.rename(port_id, name)

    # Add a new symbol into a portfolio
    def add_symbol(self, port_id, symbol, market):
        model = Port_StockModel()
        model.insertPort(port_id, symbol, market)

    # Delete a symbol from a portfolio
    def delete_symbol(self, port_id, symbol, market):
        model = Port_StockModel()
        model.del_symbol(port_id, symbol, market)

    # Get information of a portfolio (name, time, stocks)
    def get_port_info(self, port_id):
        PortModel = PortfolioModel()
        port_info = PortModel.port_info(port_id)
        return port_info
        
    # Get all symbols and its details from a market
    def get_market_stock(self, market):
        StockModels = StockModel()
        market_stock = StockModels.get_stocks_from_market(market)
        return market_stock
        
    # Get all symbols only from a market
    def get_symbol_by_market(self, market):
        StockModels = StockModel()
        market_stock = StockModels.get_stocks_symbols_by_market(market)
        return market_stock
        
    # Get details of a symbol
    def get_symbol_details(self, symbol):
        StockModels = StockModel()
        stock_info = StockModels.get_stock_info(symbol)
        return stock_info
        
    # Add a real time data of a symbol into the database
    def add_real_time_data(self, symbol, last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken):
        RealDataModels = RealDataModel()
        RealDataModels.add_realdata(symbol, last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken)
        
    # Get real time data from database
    def get_real_time_data(self, symbol):
        RealDataModels = RealDataModel()
        output = RealDataModels.get_realdata(symbol)
        return output
    
    # Update the real time data of a stock
    def update_real_time_data(self, symbol, last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken):
        RealDataModels = RealDataModel()
        RealDataModels.update_realdata(symbol, last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken)
        
    # Check if a specific stock exists from the real_data table
    def check_real_time_data(self, symbol):
        RealDataModels = RealDataModel()
        output = RealDataModels.check_realdata(symbol)
        return output

# Model
class Model(object):
    def __init__(self):
        pass

    # Initialize all table
    def init_all_table(self):
        payload = ()
        
        query = "CREATE TABLE IF NOT EXISTS USERS(ID INTEGER PRIMARY KEY AUTOINCREMENT,Username varchar(255),Password varchar(255))"
        self._dbPOST(query, payload)
        
        query = "CREATE TABLE IF NOT EXISTS PORT_USER(ID INTEGER PRIMARY KEY AUTOINCREMENT, port_id INTEGER, user_id INTEGER, foreign key(port_id) references users(id), foreign key(user_id) references portfolios(id))"
        self._dbPOST(query, payload)
        
        query = "CREATE TABLE IF NOT EXISTS PORTFOLIOS(ID INTEGER PRIMARY KEY AUTOINCREMENT, Name varchar(255) NOT NULL, Time varchar(255) NOT NULL)"
        self._dbPOST(query, payload)

        query = "CREATE TABLE IF NOT EXISTS PORT_STOCK(ID INTEGER PRIMARY KEY AUTOINCREMENT, Port_id INTEGER, Symbol varchar(255), Market varchar(255), foreign key(port_id) references portfolios(id))"
        self._dbPOST(query, payload)

        query = "CREATE TABLE IF NOT EXISTS STOCKS(Symbol varchar(255) NOT NULL, Market varchar(255) NOT NULL, Name varchar(255),Sector varchar(255), PRIMARY KEY(Symbol, Market))"
        self._dbPOST(query, payload)
        
        query = "CREATE TABLE IF NOT EXISTS REAL_DATA(Symbol varchar(255) NOT NULL, Last_Refresh varchar(255) NOT NULL, Time_Zone varchar(255) NOT NULL, Open varchar(255) NOT NULL, High varchar(255) NOT NULL, Low varchar(255) NOT NULL, Close varchar(255) NOT NULL, Volume varchar(255) NOT NULL, Change varchar(255) NOT NULL, Percent_Change varchar(255) NOT NULL, Desc varchar(255) NOT NULL, Time_Taken varchar(255) NOT NULL, Primary Key(Symbol))"
        self._dbPOST(query, payload)
        
    # GET information from the DB
    def _dbGET(self, query, payload):
        # connection
        connection = sqlite3.connect('niulio.db')
        cursorObj = connection.cursor()

        # execute the query
        rows = cursorObj.execute(query, payload)
        connection.commit()
        results = []
        for row in rows:
            results.append(row)
        cursorObj.close()
        return results

    # POST information to the DB
    def _dbPOST(self, query, payload):
        # connection
        connection = sqlite3.connect('niulio.db')
        cursorObj = connection.cursor()

        # execute the query
        cursorObj.execute(query, payload)
        connection.commit()
        connection.close()

    # get the column names of a table
    def get_columns(self, tablename):
        query = "PRAGMA table_info({})".format(tablename)
        payload = ()
        info = self._dbGET(query, payload)
        cols = [e[1] for e in info]
        return cols

    # count rows of a table
    def count(self, tablename):
        query = "SELECT COUNT(*) FROM {}".format(tablename)
        payload = ()
        nb = self._dbGET(query, payload)
        tupletolist = [e for l in nb for e in l]
        return tupletolist[0]

    # delete all stuff in the table
    def delete_all(self, tablename):
        query = "DELETE FROM {}".format(tablename)
        payload = ()
        self._dbPOST(query, payload)

    

"""
CREATE TABLE USERS(
ID INTEGER PRIMARY KEY AUTOINCREMENT,
Username varchar(255),
Password varchar(255));
"""

class UserModel(Model):
    # sign up new users
    def register(self, username, password):
        query = "INSERT INTO USERS (Username, Password) VALUES (?, ?)"
        username = username.lower()  # username are all lower cases
        payload = (username, password)
        self._dbPOST(query, payload)

    # Checks if a user exists in the database
    def not_exist_username(self, username):
        query = "SELECT * FROM USERS WHERE Username = ?"
        payload = (username,)
        user_info = self._dbGET(query, payload)
        if user_info == []:
            return True
        else:
            return False

    # get the password with a username for login
    def get_password(self, username):
        query = "SELECT Password FROM USERS WHERE Username = ?"
        payload = (username,)
        password = self._dbGET(query, payload, )
        tupletolist = [e for l in password for e in l]
        if len(tupletolist) == 1:
            return tupletolist[0]
        else:
            return ""
    
    # get a user's information from the database
    def get_user(self, username):
        """
        :param username: 
        :return: {}
        """
        query = "SELECT * FROM USERS WHERE Username = ?"
        payload = (username,)
        info = self._dbGET(query, payload)
        tupletolist = [e for l in info for e in l]
        return tupletolist


# this is the junction table to handle many-to-many relationship
"""
CREATE TABLE PORT_USER(
ID INTEGER PRIMARY KEY AUTOINCREMENT,
port_id INTEGER,
user_id INTEGER,
foreign key(port_id) references users(id),
foreign key(user_id) references portfolios(id));
"""

class Port_UserModel(Model):

    # Make a relation of a user and a port (A user id owns a new port id)
    def insertPort(self, port_id, user_id):
        query = "INSERT INTO PORT_USER (port_id, user_id) VALUES (?, ?)"
        payload = (port_id, user_id,)
        self._dbPOST(query, payload)

    # Delete a port id from a user
    def del_portfolio(self, port_id):
        query = "DELETE FROM PORT_USER WHERE Port_id = {}".format(port_id)
        payload = ()
        self._dbPOST(query, payload)

    # Get port ids from a user
    def get_portIDs(self, user_id):
        query = "SELECT * FROM PORT_USER WHERE User_id = {}".format(user_id)
        payload = ()
        return self._dbGET(query, payload)

"""
CREATE TABLE PORTFOLIOS(
ID INTEGER PRIMARY KEY AUTOINCREMENT,
Name varchar(255) NOT NULL,
Time varchar(255) NOT NULL);
"""
class PortfolioModel(Model):
    
    # create a new portfolio and add it into the database
    def add_portfolio(self, port_name, port_time):
        query = "INSERT INTO PORTFOLIOS (Name, Time) VALUES (?, ?)"
        payload = (port_name, port_time)
        self._dbPOST(query, payload)

        # get the id for the new portfolio then store it to the <USERS> table
        query = "SELECT MAX(ID) FROM PORTFOLIOS"
        payload = ()
        port_id = self._dbGET(query, payload)
        return port_id

    # delete a portfolio from the database
    def del_portfolio(self, port_id):
        query = "DELETE FROM PORTFOLIOS WHERE ID = {}".format(port_id)
        payload = ()
        self._dbPOST(query, payload)

    # Update the name of a portfolio
    def rename(self, port_id, name):
        query = "UPDATE PORTFOLIOS SET Name = '{}' WHERE ID = {}".format(name, port_id)
        payload = ()
        self._dbPOST(query, payload)

    # Get name, time, and stocks (symbols) of a portfolio
    # Format : {name, time, [(stock, market)]}
    def port_info(self, port_id):
        query1 = "SELECT NAME, TIME FROM PORTFOLIOS WHERE ID = {}".format(port_id)
        payload1 = ()
        tuple1 = self._dbGET(query1, payload1)
        output1 = [e for l in tuple1 for e in l] 
        if len(output1) < 1:
            fail = {'name' : "", 'time' : "", 'stock' : ""}
            return fail
        
        port_name = output1[0]
        port_time = output1[1]
        
        query2 = "SELECT SYMBOL, MARKET FROM PORT_STOCK WHERE PORT_ID = {}".format(port_id)
        payload2 = ()
        tuple2 = self._dbGET(query2, payload2)
        
        port_stock = []
        for each_tuple in tuple2:
            port_stock.append([e for l in [each_tuple] for e in l])
        result = {'name' : port_name, 'time' : port_time, 'stock' : port_stock}
        return result

"""
CREATE TABLE PORT_STOCK(
ID INTEGER PRIMARY KEY AUTOINCREMENT,
Port_id INTEGER,
Symbol varchar(255),
Market varchar(255),
foreign key(port_id) references portfolios(id));
"""
class Port_StockModel(Model):
    
    # Insert a portfolio details into the database (id, symbol, market)
    def insertPort(self, port_id, symbol, market):
        query = "INSERT INTO PORT_STOCK (Port_id, Symbol, Market) VALUES (?, ?, ?)"
        payload = (port_id, symbol, market,)
        self._dbPOST(query, payload)

    # Delete a portfolio details from the database
    def del_portfolio(self, port_id):
        query = "DELETE FROM PORT_STOCK WHERE Port_id = {}".format(port_id)
        payload = ()
        self._dbPOST(query, payload)

    # Delete a symbol from a portfolio
    def del_symbol(self, port_id, symbol, market):
        query = "DELETE FROM PORT_STOCK WHERE Port_id = '{}' AND Symbol = '{}' AND Market = '{}'"\
            .format(port_id, symbol, market)
        payload = ()
        self._dbPOST(query, payload)

"""
CREATE TABLE STOCKS(
Symbol varchar(255) NOT NULL,
Market varchar(255) NOT NULL,
Name varchar(255),
Sector varchar(255),
PRIMARY KEY(Symbol, Market));
"""

class StockModel(Model):
    
    # add a stock (and simple info of it) to the database
    def add_ticker(self, symbol, market, company_name, sector):
        query = "INSERT INTO STOCKS (Symbol, Market, Name, Sector) VALUES (?, ?, ?, ?)"
        payload = (symbol, market, company_name, sector,)
        self._dbPOST(query, payload)

    # get all stocks of a market (in tuple)
    def get_stocks_from_market(self, market):
        query = "SELECT * FROM STOCKS WHERE Market LIKE '{}'".format(market)
        payload = ()
        stocks = self._dbGET(query, payload)
        return stocks
        
    # Get only symbols of a market
    def get_stocks_symbols_by_market(self, market):
        query = "SELECT symbol FROM STOCKS WHERE Market LIKE '{}'".format(market)
        payload = ()
        stocks = self._dbGET(query, "")
        output = [e for l in stocks for e in l]

        return output

    # Get information of a symbol (most preferable with the first occurence which is 'NASDAQ', since it was added first to the database)        
    # Format (symbol, description, sector)
    def get_stock_info(self, symbol):
        query = "SELECT * FROM STOCKS WHERE Symbol LIKE '{}' AND (Market Like '{}' or Market Like '{}') LIMIT 1".format(symbol, 'nasdaq', 'nyse')
        payload = ()
        
        stocks = self._dbGET(query, "")
        tupletolist = [e for l in stocks for e in l]
        
        if len(tupletolist) > 1:
            output = {'name' : tupletolist[0], 'desc' : tupletolist[2], 'sector' : tupletolist[3]}
        else:
            output = {'name' : "", 'desc' : "", 'sector' : ""}
            
        return output

"""
CREATE TABLE(
Symbol varchar(255) NOT NULL,
Last_Refresh varchar(255) NOT NULL,
Time_Zone varchar(255) NOT NULL,
Open varchar(255) NOT NULL,
High varchar(255) NOT NULL,
Low varchar(255) NOT NULL,
Close varchar(255) NOT NULL,
Volume varchar(255) NOT NULL,
Change varchar(255) NOT NULL,
Percent_Change varchar(255) NOT NULL,
Desc varchar(255) NOT NULL,
Time_Taken varchar(255) NOT NULL,
Primary Key(Symbol));
"""

class RealDataModel(Model):

    # Add a real time data of a stock from backend to the database
    def add_realdata(self, symbol, last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken):
        # Security
        # To ensure this table always exists
        query = "CREATE TABLE IF NOT EXISTS REAL_DATA(Symbol varchar(255) NOT NULL, Last_Refresh varchar(255) NOT NULL, Time_Zone varchar(255) NOT NULL, Open varchar(255) NOT NULL, High varchar(255) NOT NULL, Low varchar(255) NOT NULL, Close varchar(255) NOT NULL, Volume varchar(255) NOT NULL, Change varchar(255) NOT NULL, Percent_Change varchar(255) NOT NULL, Desc varchar(255) NOT NULL, Time_Taken varchar(255) NOT NULL, Primary Key(Symbol))"
        payload = ()
        self._dbPOST(query, payload)
        
        query = "INSERT INTO REAL_DATA (Symbol, Last_Refresh, Time_Zone, Open, High, Low, Close, Volume, Change, Percent_change, Desc, Time_Taken) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        payload = (symbol, last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken)
        self._dbPOST(query, payload)

    # Get real time data of a stock that is stored in database
    def get_realdata(self, symbol):
        # Security
        # To ensure this table always exists
        query = "CREATE TABLE IF NOT EXISTS REAL_DATA(Symbol varchar(255) NOT NULL, Last_Refresh varchar(255) NOT NULL, Time_Zone varchar(255) NOT NULL, Open varchar(255) NOT NULL, High varchar(255) NOT NULL, Low varchar(255) NOT NULL, Close varchar(255) NOT NULL, Volume varchar(255) NOT NULL, Change varchar(255) NOT NULL, Percent_Change varchar(255) NOT NULL, Desc varchar(255) NOT NULL, Time_Taken varchar(255) NOT NULL, Primary Key(Symbol))"
        payload = ()
        self._dbPOST(query, payload)
    
        query = "SELECT * FROM REAL_DATA WHERE Symbol LIKE '{}'".format(symbol)
        payload = ()
        stocks = self._dbGET(query, payload)
        output = [e for l in stocks for e in l]
        
        # If data does not exist, return errors
        if len(output) == 0:
            dict_output = {'Symbol' : symbol, 'Last Refreshed' : 'Error', 'Time Zone' : 'Error', 'open' : 'Error', 'high' : 'Error', 'low' : 'Error', 'close' : 'Error', 'volume' : 'Error', 'change' : '0.00000', 'percent_change' : '0.00000', 'desc' : 'Error', 'time_taken' : 'Error'}
        else:
            dict_output = {'Symbol' : output[0], 'Last Refreshed' : output[1], 'Time Zone' : output[2], 'open' : output[3], 'high' : output[4], 'low' : output[5], 'close' : output[6], 'volume' : output[7], 'change' : output[8], 'percent_change' : output[9], 'desc' : output[10], 'time_taken' : output[11]}
                
        return dict_output

    # Check if a real data of a symbol exists
    def check_realdata(self, symbol):
        query = "CREATE TABLE IF NOT EXISTS REAL_DATA(Symbol varchar(255) NOT NULL, Last_Refresh varchar(255) NOT NULL, Time_Zone varchar(255) NOT NULL, Open varchar(255) NOT NULL, High varchar(255) NOT NULL, Low varchar(255) NOT NULL, Close varchar(255) NOT NULL, Volume varchar(255) NOT NULL, Change varchar(255) NOT NULL, Percent_Change varchar(255) NOT NULL, Desc varchar(255) NOT NULL, Time_Taken varchar(255) NOT NULL, Primary Key(Symbol))"
        payload = ()
        self._dbPOST(query, payload)
    
        query = "SELECT * FROM REAL_DATA WHERE Symbol LIKE '{}'".format(symbol)
        payload = ()
        stocks = self._dbGET(query, payload)
        output = [e for l in stocks for e in l]
        
        if len(output) == 0:
            return False
        else:
            return True
                
    # Update the real time data of a stock
    def update_realdata(self, symbol, last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken):
        # Security
        # To ensure this table always exists
        query = "CREATE TABLE IF NOT EXISTS REAL_DATA(Symbol varchar(255) NOT NULL, Last_Refresh varchar(255) NOT NULL, Time_Zone varchar(255) NOT NULL, Open varchar(255) NOT NULL, High varchar(255) NOT NULL, Low varchar(255) NOT NULL, Close varchar(255) NOT NULL, Volume varchar(255) NOT NULL, Change varchar(255) NOT NULL, Percent_Change varchar(255) NOT NULL, Desc varchar(255) NOT NULL, Time_Taken varchar(255) NOT NULL, Primary Key(Symbol))"
        payload = ()
        self._dbPOST(query, payload)
        
        # Ensure the sql does not fail if the symbol does not exists
        check_if_exists = self.check_realdata(symbol)
        if check_if_exists:
            query = "UPDATE REAL_DATA SET Last_Refresh = '{}', Time_Zone = '{}', Open = '{}', High = '{}', Low = '{}', Close = '{}', Volume = '{}', Change = '{}', Percent_change = '{}', Desc = '{}', Time_Taken = '{}' WHERE Symbol = '{}'".format(last_refresh, time_zone, open, high, low, close, volume, change, percent_change, desc, time_taken, symbol)
            self._dbPOST(query, payload)

# DEBUG function
# generate one fake user
# username: 5 letters + 3 numbers
# password: 8 numbers
def fakeuser_gen():
    C = Controller()
    u_list = [random.choice(string.ascii_letters) for _ in range(5)] + [random.randint(0, 10) for _ in range(3)]
    pw_list = [random.randint(0, 10) for _ in range(8)]
    username = ''.join(str(e) for e in u_list)
    password = ''.join(str(e) for e in pw_list)
    C.register_user(username, password)


if __name__ == "__main__":
    '''
    #test = StockModel()
    #print(test.get_stock_info('HTY'))
    #cont = Controller()
    #print(cont.get_symbol_details('AAT'))
    test = RealDataModel()
    #test.add_realdata('TEST2', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'some time')
    print(test.get_realdata("TEST3"))
    test.update_realdata('TEST2', 'aaa', 'bbb', 'ccc', 'ddd', 'eee', 'fff', 'gggg', 'h', 'i', 'j', 'some time')
    print(test.get_realdata("TEST3"))
    #cont._load_symbols()
    #print(cont.get_port_info("3"))
    #print(cont.get_PortIDs("test123"))
    # cont.clear("Users")
    # for _ in range(20): fakeuser_gen()
    #
    # cont.register_user('mike', 'asdfasdf')

    # Test
    #cont.add_portfolio('test', 'awawawwwwww', 'yesterday', [('AAPL', 'nasdaq'), ('pih', 'nasdaq')])
    #cont.rename_portfolio(3, 'COOLport')
    #cont.rename_portfolio(4, 'name is long')
    #cont.delete_symbol(4, 'AAPL', 'nasdaq')
    #print(cont.get_PortIDs('test'))
    '''
    pass
