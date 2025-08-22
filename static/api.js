const create_user = async function(username, data) {
	const URL = '/users';
	const options =
		{ 'method': 'POST'
		, 'body': JSON.stringify({...data, 'username': username})
		}
	const response = await fetch(URL, options);
	if (response.ok) {
		return await response.json();
	} else {
		throw new Error(`Failed to create user. Status: ${response.status}`);
	}	
}

const read_user = async function(username='') {
	const URL = `/users/${username}`;
	const response = await(fetch(URL));
	if (response.ok) {
		return await response.json();
	} else {
		throw new Error(`Failed to read user "${username}". Status: ${response.status}`)
	}
}

const update_user = async function(username, data) {
	const URL = `/users/${username}`;
	const options =
		{ 'method': 'PATCH'
		, 'body': JSON.stringify(data)
		}
	const response = await fetch(URL, options);
}

const delete_user = async function(username) {
	const URL = `/users/${username}`;
	const options = {'method': 'DELETE'}
	const response = await fetch(URL, options);
	if (response.ok) return;
	throw new Error(`Failed to delete user ${username}. Status: ${response.status}`);
}
