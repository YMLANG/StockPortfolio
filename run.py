#!/usr/bin/python3
from route import app
from database import Controller

app.run(debug=True, port=8085)

db_controller = Controller()
db_controller.init_table()
