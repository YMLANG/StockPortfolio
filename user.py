#!/usr/bin/python3
from flask_login import UserMixin

class users(UserMixin):
	
	# init
	def __init__(self, id, money):
		self._id = id
		self._money = money
		#self._pw = pw
	
	# get id
	def get_id(self):
		return self._id
	
	# get money
	def get_money(self):
		return self._money
	
	'''	
	# get password
	def get_pass(self):
		return self._pw
	'''	
		
	# set id
	def set_id(self, id):
		self._id = id
	
	# set money
	def set_money(self, money):
		self._money = money
	
	'''
	# set password
	def set_password(self, pw):
		self._pw = pw
	'''

