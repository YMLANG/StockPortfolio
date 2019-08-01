from flask import Flask, redirect, render_template, request, url_for
from flask_login import LoginManager,login_user, current_user, login_required, logout_user
from server import app,login_manager, currentUser
from user import users
from database import Controller, UserModel
from datafeed import *
from prediction import *
import re, datetime

import time


# Checking password of a user
def check_password(id, password):
    # get data from database based on id

    lower_id = id.lower()

    db_controller = Controller()
    get_data = db_controller.get_password(lower_id)

    if get_data == password and get_data != "":
        # set currentUser variable as current user, and login Flask   
        currentUser.set_id(lower_id)
        login_user(currentUser)
        return True

    return False

# Checking validity to register an account
def check_register_account(new_id, new_password):
    # get data from database based on id (only take id)
    lower_id = new_id.lower()

    db_controller = Controller()
    get_data = db_controller.not_exist_username(lower_id)

    if not get_data:
        # return "name exists"
        return "Username already exists"

    # name too short
    if len(new_id) < 4:
        # return "name must be at least 4 characters long"
        return "Username must be at least 4 characters long"


    # check id name contains symbol or spaces
    check_id = re.search(r'([^A-Z^a-z^0-9^\_\s])+', new_id)

    if check_id:
        # return "name contains symbol"
        return "Username must not contains symbols"

    # check password length
    if len(new_password) < 6:
        # return "password is less than 6 characters"
        return "Password must be at least 6 characters long"

    return "True"

# Create a new portfolio for a user
def create_new_portfolio(id, port_name):

    # Check if name is empty
    check_port_name = re.search('^\s*$', port_name)

    # If empty, return "Port name cant be empty"
    if check_port_name:
        return "Name for portfolio must not be empty"

    # If name contains symbol
    for each_char in port_name:
        if (ord(each_char) >= 128):
            return "Portfolio must not contain symbols"
        if (not each_char.isdigit() and not each_char.isalpha() and each_char != '_' and each_char != ' '):
            return "Portfolio must not contain symbols"

    # Get the time of creation
    calltime = datetime.datetime.now()
    today = str(calltime.hour) + ":" + str(calltime.minute) + " " + str(calltime.day) + "/" + str(calltime.month) + "/" + str(calltime.year)

    # Add new portfolio into the database
    # Return true if portfolio can be created,
    # False otherwise
    db_controller = Controller()
    valid = db_controller.add_portfolio(id, port_name, today, [])
    
    return valid

# Grab all portfolio connected to the certain user
def get_user_portfolio(id):
    # get all portfolio from a user

    db_controller = Controller()
    get_data = db_controller.get_PortIDs(id)

    return get_data

# Get a portfolio's name, time, and symbols (stocks)
def get_portfolio_details(port_id):

    db_controller = Controller()
    get_data = db_controller.get_port_info(port_id)

    return get_data

# Check if a port_id belongs to this user (security)
def port_user_validity(id, port_id):

    db_controller = Controller()
    get_data = db_controller.get_PortIDs(id)

    if port_id in get_data:
        return True

    return False

# Check if a link for a portfolio page is valid
def link_validity_port(port_link, p_id):
    # format : "port_name+?pid=id"

    port_name = ""
    port_id = ""
    output = {'name' : port_name, 'id' : port_id}

    # grabs the name of the portfolio
    # if not exists, return empty
    regex = re.search(r'^(.+)\+$', port_link)

    if regex:
        port_name = regex.group(1)
    else:
        return output

    # grab the information of the portfolio from database
    # compare it with the existing database
    # if the information matches, then return the name and id of the portfolio
    db_controller = Controller()
    get_data = db_controller.get_port_info(p_id)

    if get_data['name'] == port_name:
        output = {'name' : port_name, 'id' : p_id}

    return output

# Check if a link for a stock page is valid
def link_validity_stock(stock_name):
    # format : name

    # Check the database for the specific stock
    # If the stock exists, return True
    # Otherwise False
    db_controller = Controller()
    get_data = db_controller.get_symbol_details(stock_name)

    if get_data['name'] == stock_name:
        return True
        
    return False

# Details of a portfolio that is going to be deleted from a link
def del_port_var(long_link):
    # format : "port_name+id=id"

    port_name = ""
    port_id = ""
    output = {'name' : port_name, 'id' : port_id}

    # Grab the information by the format
    regex = re.search(r'^(.+)\+id\=([0-9]+)$', long_link)

    # If not exists, return empty
    if regex:
        port_name = regex.group(1)
        port_id = regex.group(2)
    else:
        return output

    # Grab the information from the database
    # If data matches, return the name and id
    # Else empty
    db_controller = Controller()
    get_data = db_controller.get_port_info(port_id)

    if get_data['name'] == port_name:
        output = {'name' : port_name, 'id' : port_id}

    return output

# Details of a symbol that is going to be deleted from a portfolio by a link
def del_symbol_var(long_link):
    # format : (symbol_name)+markt=(market)

    symbol_name = ""
    market = ""
    output = {'symbol' : symbol_name, 'market' : market}
    
    # Grab the information by the format
    regex = re.search(r'^(.+)\+markt\=(.+)$', long_link)

    # If not exists, return empty
    if regex:
        symbol_name = regex.group(1)
        market = regex.group(2)
    else:
        return output

    # From the database, match the information
    # If symbol exists in the database and by the market it is assigned to, return the name and the market
    # Else, empty
    db_controller = Controller()
    get_data = db_controller.get_symbol_by_market(market)

    if symbol_name in get_data:
        output = {'symbol' : symbol_name, 'market' : market}

    return output

# Insert a symbol to a portfolio
def symbol_into_port(port_id, symbol, market):

    # Grab information from a port for validity check
    db_controller = Controller()
    get_data = db_controller.get_port_info(port_id)
    valid = []

    # If 'ALL' is chosen when adding symbol
    if market.lower() == "all":
        # Available market
        all_market = ['nasdaq', 'nyse']
        avail_market = []
        
        # Find any market that offers the symbol in check
        for each_market in all_market:
            check_stock_in_market = db_controller.get_symbol_by_market(each_market)
            if symbol in check_stock_in_market:
                avail_market.append(each_market)

        # If no market offers this symbol, returns an error message
        if len(avail_market) > 0:
            pass
        else:
            return symbol + " does not exist"

    else:
        # Check if the market exists
        # If true, use it as a combination to be added
        # Else, return an error message
        check_market_valid = db_controller.get_symbol_by_market(market)
        if len(check_market_valid) > 0:
            valid = [symbol, market]
        else:
            return "Market does not exist"

    # Make sure port exists before adding
    if get_data['name'] != "":
    
        # If market is "all"
        if market.lower() == "all":
        
            # Try for each (symbol, market) combination and check if the portfolio contained these combination
            # Use the combination if it is not contained in the portfolio
            for each_test in avail_market:
                check_valid = [symbol, each_test]
                if check_valid not in get_data['stock']:
                    market = each_test
                    valid = [symbol, market]
                    break

        # if the stock to be added does not exist in the portfolio and not empty
        if valid not in get_data['stock'] and market.lower() != "all" and len(valid) > 0:
        
            # Make sure the symbol exists in the market
            # If so, add it to the portfolio
            check_stock_in_market = db_controller.get_symbol_by_market(market)
            if symbol in check_stock_in_market:
                db_controller.add_symbol(port_id, symbol, market)
                return True

    return symbol + " already exists"

# Delete a portfolio
def delete_port(port_id, port_name):
    
    # Check the database for information of the portfolio
    db_controller = Controller()
    get_data = db_controller.get_port_info(port_id)

    # Make sure the portfolio exists
    if get_data['name'] != "" and get_data['name'] == port_name:
        for each_stock in get_data['stock']:
            db_controller.delete_symbol(port_id, each_stock[0], each_stock[1])

        # Delete the portfolio
        db_controller.delete_portfolio(port_id)

# Union of two lists with set
def union_list(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    result = list1 + list(set2 - set1)
    result.sort()
    return result

# Get all stocks from all markets
def get_all_stock():

    # initialize the dictionary (hard coded, since we will only be using 2 markets)
    db_controller = Controller()
    avail_market = ['nasdaq', 'nyse']
    data = {'all' : [], 'nasdaq' : [], 'nyse' : []}

    # For each market used, get all symbols related to it
    for each_market in avail_market:
        get_data = db_controller.get_symbol_by_market(each_market)
        data[each_market] = get_data

    # Combine the lists
    union_list12 = union_list(data['nasdaq'], data['nyse'])
    
    # Add them into all
    data['all'] = union_list12

    return data

# Delete a stock from a portfolio
def delete_stock(port_id, symbol, market):
    
    # Get portfolio's information
    db_controller = Controller()
    get_data = db_controller.get_port_info(port_id)

    # Make sure at least a stock exists
    # Make sure the specific stock exists
    if len(get_data['stock']) > 0:
        for each_stock in get_data['stock']:
            if each_stock[0] == symbol and each_stock[1] == market:
                db_controller.delete_symbol(port_id, symbol, market)


# Get real time data from a stock
def get_real_time_stock(symbol, interval):

    # Get information if the real time data of the symbol has been previously saved
    # If it is new, 'check_database' will be empty (init value would be 0.0000 and error, which can be used as error messages)
    db_controller = Controller()
    if_already_exist = db_controller.check_real_time_data(symbol)
    check_database = db_controller.get_real_time_data(symbol)
    
    # Get the details of the symbol and the current time
    stock_data = db_controller.get_symbol_details(symbol)
    time_now = datetime.datetime.now()
        
    # update interval 
    # 300 = 5 minutes
    update = 300
    
    # If the symbol has yet not saved previously
    if not if_already_exist:
        # INSERT INTO DATABASE
        get_data = get_realtimeData(symbol, interval)
        
        # Set the output
        # If the sector value is missing (which is used for error messages), replace it with the original sector (from database)
        try:
            output = {'name' : get_data['Symbol'], 'Last_Refreshed' : get_data['Last Refreshed'], 'Time_Zone' : get_data['Time Zone'], 'open' : get_data['open'], 'high' : get_data['high'], 'low' : get_data['low'], 'close' : get_data['close'], 'volume' : get_data['volume'], 'change' : float(get_data['change']), 'percent_change' : float(get_data['percent_change']), 'desc' : stock_data['desc'], 'sector' : get_data['sector']}
        except:
            output = {'name' : get_data['Symbol'], 'Last_Refreshed' : get_data['Last Refreshed'], 'Time_Zone' : get_data['Time Zone'], 'open' : get_data['open'], 'high' : get_data['high'], 'low' : get_data['low'], 'close' : get_data['close'], 'volume' : get_data['volume'], 'change' : float(get_data['change']), 'percent_change' : float(get_data['percent_change']), 'desc' : stock_data['desc'], 'sector' : stock_data['sector']}
        
        # If the output is Error (due to API error)
        # Don't add the value to the database
        if output['Last_Refreshed'] != 'Error':
            db_controller.add_real_time_data(get_data['Symbol'], get_data['Last Refreshed'], get_data['Time Zone'], get_data['open'], get_data['high'], get_data['low'], get_data['close'], get_data['volume'], get_data['change'], get_data['percent_change'], stock_data['desc'], time_now)
        
    else:
        # If the symbol real time data has been previously added in the database
        # check the time of when it was taken
        time_last = datetime.datetime.strptime(check_database['time_taken'], "%Y-%m-%d %H:%M:%S.%f")
        
        # get the time difference
        time_diff = time_now - time_last
        total_diff = time_diff.total_seconds()
        
        # If the value stored in database is not error and time difference is less that the update time (default 5 minutes)
        if total_diff <= update and check_database['Last Refreshed'] != 'Error':
            # return the values stored in the database
            output = {'name' : check_database['Symbol'], 'Last_Refreshed' : check_database['Last Refreshed'], 'Time_Zone' : check_database['Time Zone'], 'open' : check_database['open'], 'high' : check_database['high'], 'low' : check_database['low'], 'close' : check_database['close'], 'volume' : check_database['volume'], 'change' : float(check_database['change']), 'percent_change' : float(check_database['percent_change']), 'desc' : check_database['desc'], 'sector' : stock_data['sector']}
    
        else:
            # UPDATE DATABASE
            get_data = get_realtimeData(symbol, interval)
            
            # Set the output
            # If the sector value is missing (which is used for error messages), replace it with the original sector (from database)
            try:
                output = {'name' : get_data['Symbol'], 'Last_Refreshed' : get_data['Last Refreshed'], 'Time_Zone' : get_data['Time Zone'], 'open' : get_data['open'], 'high' : get_data['high'], 'low' : get_data['low'], 'close' : get_data['close'], 'volume' : get_data['volume'], 'change' : float(get_data['change']), 'percent_change' : float(get_data['percent_change']), 'desc' : stock_data['desc'], 'sector' : get_data['sector']}
            except:
                output = {'name' : get_data['Symbol'], 'Last_Refreshed' : get_data['Last Refreshed'], 'Time_Zone' : get_data['Time Zone'], 'open' : get_data['open'], 'high' : get_data['high'], 'low' : get_data['low'], 'close' : get_data['close'], 'volume' : get_data['volume'], 'change' : float(get_data['change']), 'percent_change' : float(get_data['percent_change']), 'desc' : stock_data['desc'], 'sector' : stock_data['sector']}

            # If the value gathered does not contain error (API works fine), update the symbol from the database
            if output['Last_Refreshed'] != 'Error':
                db_controller.update_real_time_data(get_data['Symbol'], get_data['Last Refreshed'], get_data['Time Zone'], get_data['open'], get_data['high'], get_data['low'], get_data['close'], get_data['volume'], get_data['change'], get_data['percent_change'], stock_data['desc'], time_now) 
                
    return output


# Get real time data from stocks of a port
def get_real_time_stock_for_a_port(port_id, interval):

    # Get details of the portfolio
    get_data = get_portfolio_details(port_id)
    db_controller = Controller()
    final_output = []
    
    # get the real time data of each stock
    # if the API returns an error, try again
    # 5 tries before returning error
    for each_stock in get_data['stock']:
        stock_data = db_controller.get_symbol_details(each_stock[0])

        retry = 0;
        dict_output = {'name' : each_stock[0], 'market' : each_stock[1], 'open' : '0.0000', 'high' : '0.0000', 'low' : '0.0000', 'close' : '0.0000', 'volume' : '0.0000', 'time' : 'Error', 'change' : 0.00, 'percent_change' : 0.00, 'desc' : 'Error', 'sector' : 'Error'}

        while retry < 5:
            try:
                real_time = get_real_time_stock(each_stock[0], interval)
                dict_output = {'name' : each_stock[0], 'market' : each_stock[1], 'open' : real_time['open'], 'high' : real_time['high'], 'low' : real_time['low'], 'close' : real_time['close'], 'volume' : real_time['volume'], 'time' : real_time['Last_Refreshed'] + " " + real_time['Time_Zone'], 'change' : float(real_time['change']), 'percent_change' : float(real_time['percent_change']), 'desc' : stock_data['desc'], 'sector' : real_time['sector']}
                break
            except:
                retry += 1
                

        final_output.append(dict_output)

    return final_output
    
# Get prediction data from datafeed
def get_prediction_chart(symbol):
    
    # Get the predictions and lay it in dictionary
    MA, EMA, MACD, MOM = chart_data_ti(symbol)
    output = {'MA' : MA, 'EMA' : EMA, 'MACD' : MACD, 'MOM' : MOM}

    return output
    
# Load the user identity
@login_manager.user_loader
def load_user(id):
    
    # check if user exists in database (security)
    # If yes, returns the user
    # Else, empty
    lower_id = id.lower()
    db_controller = Controller()
    data = db_controller.not_exist_username(lower_id)

    if not data:
        user = users(lower_id, 0)
    else:
        user = users("", 0)
    return user

# checks if a user is loginned
def check_login():
    flag = currentUser.get_id()

    if flag != "":
        return True

    return False

# Reset the currentUser field to empty and logout any existing user
def reset_user():
    logout_user()
    currentUser.set_id("")


#------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------

# Index of the route
@app.route("/index", methods=["GET", "POST"])
def index():

    message = ""
    if 'message' in request.args:
        message = request.args['message']

    # If user is not loginned, redirect to login page
    # Else, homepage (dashboard)
    if currentUser.get_id() == "":
        reset_user()
        return redirect(url_for("login", message = message))
    else:
        return redirect(url_for("homepage", message = message))


# Login route
@app.route("/", methods=["GET", "POST"])
def login():

    message = ""
    if 'message' in request.args:
        message = request.args['message']

    # If a user is loginned, redirect to homepage
    if currentUser.get_id() != "":
        return redirect(url_for("homepage", message = message))

    if request.method == "POST":
        input_id = request.form['username']
        input_pw = request.form['password']

        # Make sure that username and password field is not empty
        if len(input_id) == 0:
            return render_template("login.html", message = "Username field must not be empty")

        if len(input_pw) == 0:
            return render_template("login.html", message = "Password field must not be empty")

        # Check the username and password in the database
        if check_password(input_id, input_pw):
            greetings = "Hi " + input_id + "!"
            return redirect(url_for("homepage", message = greetings))
        else:
            message = "Username and/or Password invalid"

    return render_template("login.html", message = message)


# Sign up user route
@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():

    message = ""
    if 'message' in request.args:
        if request.args['message'] != "True":
            message = request.args['message']

    if request.method == "POST":
        input_id = request.form['username']
        input_pw = request.form['password']
        input_cfm = request.form ['confirm']

        # Make sure that password and confirm password fields are matching
        if input_pw != input_cfm:
            return render_template("signuppage.html", message = "Password does not match")

        # Checks if a user can be registered 
        check_validity = check_register_account(input_id, input_pw)

        if check_validity == "True":
            db_controller = Controller()
            get_data = db_controller.register_user(input_id, input_pw)

            return redirect(url_for("index", message = "Sign up successful!"))

        else:
            # Error messages
            return render_template("signuppage.html", message = check_validity)

    return render_template("signuppage.html", message = message)

# About page route
@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html", check_login = check_login())

# FAQ page route
@app.route("/faq", methods=["GET", "POST"])
def faq():
    return render_template("faq.html", check_login = check_login())

# Stock page route
# Displaying all stock information here
@app.route("/stock", methods=["GET", "POST"])
def stock():
    message = ""
    if 'message' in request.args:
        message = request.args['message']

    if request.method == "POST":
        textbox = request.form['symbol_name'].upper()
        # Trim any whitespaces
        trim_spaces = re.sub('\s*', '',textbox)

        # If empty, return "Field must not be empty"
        if trim_spaces == "":
            message = "Field must not be empty"

        else:
            return redirect(url_for("stockpage", message = "", stock_name = trim_spaces))
        
    return render_template("stock.html", message = message, all_stocks = get_all_stock(), check_login = check_login())


# Individual stock route
@app.route("/stock/<stock_name>", methods=["GET", "POST"])
def stockpage(stock_name):
    message = ""
    if 'message' in request.args:
        message = request.args['message']

    # Checks if the link is valid
    check_link = link_validity_stock(stock_name)
    
    if not check_link:
        final_message = stock_name + " does not exist"
        return redirect(url_for("stock", message = final_message))
    
    # get the real time value, chart (historical 100 days), and the predictions of each stock
    info = get_real_time_stock(stock_name, 1)
    chart = chart_data(stock_name)
    pred_chart = get_prediction_chart(stock_name)
    pred, size, time_t, acc = run_time(stock_name)
    prediction = {'pred' : pred, 'size' : size, 'time' : time_t, 'acc' : acc}
    #output = {'MA' : MA, 'EMA' : EMA, 'MACD' : MACD, 'MOM' : MOM}
    #print(pred_chart['MOM'])

    return render_template("stock_stuff.html", message = message, prediction = prediction, stock_data = info, chart_data = chart, pred_chart = pred_chart, check_login = check_login())


# User homepage route
@app.route("/home", methods=["GET", "POST"])
@login_required
def homepage():

    message = ""
    if 'message' in request.args:
        message = request.args['message']

    # Get all portfolio that the current user have
    get_port_ids = get_user_portfolio(currentUser.get_id())
    port_details = []
    for each_port_id in get_port_ids:
        id_name_dict = {'port_id' : each_port_id, 'port_name' : get_portfolio_details(each_port_id)['name']}
        port_details.append(id_name_dict)

    if request.method == "POST":
        # If the user pressed 'Create portfolio' button
        if request.form['submit_port'] == "create_port":
            # Get the new name for the portfolio
            textbox = request.form['new_port_name']
            
            # Check if the name is valid (not containing symbols, nor empty"
            check_validity = create_new_portfolio(currentUser.get_id(), textbox)
            if not check_validity:
                return redirect(url_for("index", message = "Failed creating portfolio"))
            else:
                if type(check_validity) == bool:
                    return redirect(url_for("homepage", message = "New port created!"))
                else:
                    return redirect(url_for("homepage", message = check_validity))

        elif request.form['submit_port'] == "delete_port":
            # If the user pressed 'Delete portfolio' button
            
            # Get all selected checkbox(es) value
            delete_port_id = []

            if 'delete_port' in request.form:
                delete_port_id = request.form.getlist('delete_port')

            # If checkbox(es) are selected
            # Delete the selected portfolios
            # Else, return "No portfolio selected"
            if len(delete_port_id) > 0:
                # final message for the names of the portfolio to be deleted
                final_message = ""
                total_ports = len(delete_port_id)
                message_commas = 0
                
                # For each selected checkbox value
                for delete_each_port in delete_port_id:
                    # Get the required data from the checkbox
                    # Value format : "port_name+id=id"
                    break_data = del_port_var(delete_each_port)
                    delete_port(break_data['id'], break_data['name'])

                    # Append the message
                    final_message += break_data['name']
                    if message_commas < total_ports - 1:
                        final_message += ", "
                        message_commas += 1

                if total_ports == 1:
                    final_message += " has been deleted."
                else:
                    final_message += " have been deleted."

                return redirect(url_for("homepage", message = final_message))

            else:
                return render_template("portfolio.html", message = "No portfolio selected", get_port = port_details)


    return render_template("portfolio.html", message = message, get_port = port_details)

# User's portfolio route
@app.route("/portfolio/<long_link>", methods=["GET", "POST"])
@login_required
def portpage(long_link):
    message = ""
    if 'message' in request.args:
        message = request.args['message']
        
    p_id = ""
    if 'pid' in request.args:
        p_id = request.args['pid']

    # No port id is 0 or less
    if p_id == "" or int(p_id) <= 0:
        return redirect(url_for("index", message = "Portfolio does not exist"))
        
    # Security to ensure that a portfolio exists and not fabricated
    check_link = link_validity_port(long_link, int(p_id))
    if check_link['name'] == "" and check_link['id'] == "":
        return redirect(url_for("index", message = "Portfolio does not exist"))

    check_valid = port_user_validity(currentUser.get_id(), int(p_id))
    if not check_valid:
        return redirect(url_for("index", message = "You are not authorized to view this page"))


    if request.method == "POST":
        # If a user pressed "Add symbol" button
        if request.form['submit_port'] == "add_symbol":
            # Get the input value (symbol and market)
            get_market = request.form.get("symbol_market").lower()
            get_symbol = request.form.get("symbol_name").upper()

            # Checks if the input values are valid
            # If yes, add it into the portfolio
            # Else, error message
            check_add_symbol = symbol_into_port(int(p_id), get_symbol, get_market)
            if type(check_add_symbol) == bool:
                message = get_symbol + " added!"
            else:
                message = check_add_symbol

        elif request.form['submit_port'] == "delete_symbol":
            # If the user pressed "Delete symbol" button
            delete_symbols = []

            # Similarly like the delete portfolio, get all checkbox(es) value
            if 'delete_symbol' in request.form:
                delete_symbols = request.form.getlist('delete_symbol')

            # If at least a checkbox is selected
            # Delete them from the portfolio
            # Else, return error message
            if len(delete_symbols) > 0:

                # Message output (feedback)
                final_message = ""
                total_symbols = len(delete_symbols)
                message_commas = 0
                
                # For each symbol selected
                for delete_each_symbol in delete_symbols:
                    # Delete each symbol from the portfolio
                    # Format : "(symbol_name)+markt=(market)"
                    break_data = del_symbol_var(delete_each_symbol)
                    delete_stock(int(p_id), break_data['symbol'], break_data['market'])

                    # Append the message
                    final_message += break_data['symbol']
                    if message_commas < total_symbols - 1:
                        final_message += ", "
                        message_commas += 1

                if total_symbols == 1:
                    final_message += " has been deleted."
                else:
                    final_message += " have been deleted."

                # Get real time value for all stocks in a portfolio
                # Interval for the stock would be 1 (as default)
                real_time_data = get_real_time_stock_for_a_port(p_id, 1)

                return render_template("portfolio2.html", message = final_message, data = get_portfolio_details(check_link['id']), all_stocks = get_all_stock(), stock_data = real_time_data)

            else:
                # Get real time value for all stocks in a portfolio
                # Interval for the stock would be 1 (as default)
                real_time_data = get_real_time_stock_for_a_port(p_id, 1)

                return render_template("portfolio2.html", message = "No symbol selected",  data = get_portfolio_details(check_link['id']), all_stocks = get_all_stock(), stock_data = real_time_data)

    # Render to some other template where layouts for single portfolio and symbols
    # Get real time value for all stocks in a portfolio
    # Interval for the stock would be 1 (as default)
    real_time_data = get_real_time_stock_for_a_port(p_id, 1)
    return render_template("portfolio2.html", message = message, data = get_portfolio_details(check_link['id']), all_stocks = get_all_stock(), stock_data = real_time_data)


# Logout route
@app.route("/logout", methods=["GET", "POST"])
def logout():
    reset_user()
    return redirect(url_for("index", message = "Logout successful"))
