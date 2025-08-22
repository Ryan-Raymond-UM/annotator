class UserAlreadyExistsError(Exception):
	pass
class InvalidUserData(ValueError):
	pass
class UserNotFoundError(ValueError):
	pass
class InvalidUsernameError(ValueError):
	pass

def validate_data(data, complete=True):
	return True
def validate_username(username):
	return True

def create(db, username, data):
	if username in db:
		raise UserAlreadyExistsError()
	if not validate_data(data):
		raise InvalidUserData
	if not validate_username(username):
		raise InvalidUsernameError
	db[username] = data

def read(db, username=None):
	if not username:
		return dict(db)
	if username not in db:
		raise UserNotFoundError
	return db[username]

def update(db, username, data):
	if not username in db:
		raise UserNotFoundError
	if not validate_data(data, complete=False):
		raise InvalidUserData
	db[username] = db[username] | data

def delete(db, username):
	if not username in db:
		raise UserNotFoundError
	del db[username]
