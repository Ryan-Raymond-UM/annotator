const refresh_users = async function() {
	console.log('Refreshing User List');
	const user_selector = document.getElementById('user-selector');
	const users = await read_user();
	user_selector.options.length = 0;
	for (const username in users) {
		const option = new Option(username, username);
		user_selector.add(option);
	};
	await user_selector_handler();
}

const refresh_user_data = async function(username) {
	console.log(`Refreshing user data for "${username}"`);
	const username_field = document.getElementById('username-field');
	const password_field = document.getElementById('password-field');
	const role_field = document.getElementById('role-field');
	const data = await read_user(username);
	username_field.innerText = data['username'] ?? 'n/a';
	password_field.innerText = data['password-hash'] ?? 'n/a';
	role_field.innerText = data['role'] ?? 'n/a';
	
}

/*	Form Handlers	*/
const create_form_handler = async function(event) {
	event.preventDefault();
	const username = document.getElementById('username').value;
	await create_user(username, {});
	await refresh_users();
}

const delete_form_handler = async function(event) {
	event.preventDefault();
	const username = document.getElementById('user-selector').value;
	const confirm_username = document.getElementById('confirm-username').value;

	if (username != confirm_username) {
		alert(`Username confirmation failed`);
		return;
	}

	await delete_user(username);
	await refresh_users();
}

const update_password_form_handler = async function(event) {
	event.preventDefault();
	const username = document.getElementById('user-selector').value;
	const password = document.getElementById('password').value;
	await update_user(username, {'password-hash': sha256(password)});
	await refresh_user_data(username);
}

const update_role_form_handler = async function(event) {
	event.preventDefault();
	const username = document.getElementById('user-selector').value;
	const role = document.getElementById('role').value;
	await update_user(username, {'role': role});
	await refresh_user_data(username);
}

/*	Event Handlers	*/
const user_selector_handler = async function(event) {
	console.log("Handling user-selector onchange event");
	const user_selector = document.getElementById('user-selector');
	const username = user_selector.value;
	await refresh_user_data(username);
}

const main = async function(event) {
	await refresh_users();
}

window.onload = main;
