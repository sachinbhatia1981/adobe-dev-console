import os
import flask
import requests
from six.moves import urllib
import json

# Start flask app
app = flask.Flask(__name__)

# Load config object from config.py
app.config.from_object('config.Config')

# Loading FLAST_SECRET from config.py
app.secret_key = app.config['FLASK_SECRET']

@app.route('/')
def home():
	return flask.render_template('index.html')

@app.route('/authorize')
def authorize():
	# Adobe OAuth2.0 authorization url
	authorization_url = 'https://ims-na1.adobelogin.com/ims/authorize/v2?'
	
	# Store required parameters in a dictionary
	params = {
		'client_id' : app.config['ADOBE_API_KEY'],
		'scope' : 'additional_info.roles, openid, profile, offline_access',
		'response_type' : 'code',
		'redirect_uri' : flask.url_for('callback', _external=True)
	}

	# This will prompt users with the approval page if consent has not been given
	# Once permission is provided, users will be redirected to the specified page
	return flask.redirect(authorization_url + urllib.parse.urlencode(params))

@app.route('/callback')
def callback():
	# Retrive the authorization code from callback
	authorization_code = flask.request.args.get('code')

	# Adobe OAuth2.0 token url
	token_url = 'https://ims-na1.adobelogin.com/ims/token/v3'
	
	# Store required parameters in a dictionary
	# And include the authorization code in it
	params = {
		'grant_type' : 'authorization_code',
		'client_id' : app.config['ADOBE_API_KEY'],
		'client_secret' : app.config['ADOBE_API_SECRET'],
		'code' : authorization_code
	}

	# Use requests library to send the POST request
	response = requests.post(token_url,
		params = params,
		headers = {'content-type': 'application/x-www-form-urlencoded'})

	# After receiving a 'OK' response, 
	if response.status_code == 200:
		# save credentials to session
		flask.session['credentials'] = response.json()
		return flask.redirect(flask.url_for('redirect_success'))
	else:
		return flask.render_template('index.html', response='login failed')

@app.route('/redirect')
def redirect_success():
	# Check if user is logged in
	if 'credentials' not in flask.session:
		return flask.redirect(flask.url_for('home'))
	return flask.render_template('home.html')

@app.route('/profile')
def profile():
	# Check if credentials exist. If not, ask the user to log in
	if 'credentials' not in flask.session:
		return flask.render_template('index.html', response='Please log in first')
	else:
		# Retrive the access token from the flask session
		access_token = flask.session['credentials']['access_token']

		# Adobe OAuth2.0 profile url
		profile_url = 'https://ims-na1.adobelogin.com/ims/userinfo/v2'
		
		# Store required parameters in a dictionary
		params = {
			'client_id' : app.config['ADOBE_API_KEY']
		}

		# Use requests library to send the GET request
		response = requests.get(profile_url,
			params = params,
			headers = {'Authorization': 'Bearer {}'.format(access_token)})

		if response.status_code == 200:
			return flask.render_template('home.html', response=json.dumps(response.json()))
		else:
			return flask.render_template('home.html', response='profile could not be retrieved')

@app.route('/accounts')
def list_accounts():
	# Check if credentials exist. If not, ask the user to log in
	if 'credentials' not in flask.session:
		return flask.render_template('home.html', response='Please log in first')
	
	# Retrieve the access token from the flask session
	access_token = flask.session['credentials']['access_token']

	# Frame.io API endpoint for accounts
	accounts_url = 'https://api.frame.io/v4/accounts'
	
	# Make the request to Frame.io API
	response = requests.get(
		accounts_url,
		headers={
			'Authorization': f'Bearer {access_token}',
			'Content-Type': 'application/json'
		}
	)

	if response.status_code == 200:
		accounts_data = response.json()
		# Extract just the accounts list for display
		accounts = accounts_data.get('data', [])
		return flask.render_template('home.html', accounts=accounts)
	else:
		error_message = f'Failed to fetch accounts. Status code: {response.status_code}, Response: {response.text}'
		return flask.render_template('home.html', response=error_message)

@app.route('/workspaces/<account_id>')
def list_workspaces(account_id):
	# Check if credentials exist
	if 'credentials' not in flask.session:
		return flask.render_template('home.html', response='Please log in first')
	
	# Retrieve the access token
	access_token = flask.session['credentials']['access_token']

	# Frame.io API endpoint for workspaces
	workspaces_url = f'https://api.frame.io/v4/accounts/{account_id}/workspaces'
	
	# Make the request to Frame.io API
	response = requests.get(
		workspaces_url,
		headers={
			'Authorization': f'Bearer {access_token}',
			'Content-Type': 'application/json'
		}
	)

	if response.status_code == 200:
		workspaces_data = response.json()
		# Extract just the workspaces list and pass account_id for project links
		workspaces = workspaces_data.get('data', [])
		return flask.render_template('home.html', workspaces=workspaces, account_id=account_id)
	else:
		error_message = f'Failed to fetch workspaces. Status code: {response.status_code}, Response: {response.text}'
		return flask.render_template('home.html', response=error_message)

@app.route('/projects/<account_id>/<workspace_id>')
def list_projects(account_id, workspace_id):
	# Check if credentials exist
	if 'credentials' not in flask.session:
		return flask.render_template('home.html', response='Please log in first')
	
	# Retrieve the access token
	access_token = flask.session['credentials']['access_token']

	# Frame.io API endpoint for projects
	projects_url = f'https://api.frame.io/v4/accounts/{account_id}/workspaces/{workspace_id}/projects'
	
	# Make the request to Frame.io API
	response = requests.get(
		projects_url,
		headers={
			'Authorization': f'Bearer {access_token}',
			'Content-Type': 'application/json'
		}
	)

	if response.status_code == 200:
		projects_data = response.json()
		# Extract just the projects list
		projects = projects_data.get('data', [])
		return flask.render_template('home.html', projects=projects)
	else:
		error_message = f'Failed to fetch projects. Status code: {response.status_code}, Response: {response.text}'
		return flask.render_template('home.html', response=error_message)

@app.route('/create_workspace/<account_id>', methods=['GET', 'POST'])
def create_workspace(account_id):
	# Check if credentials exist
	if 'credentials' not in flask.session:
		return flask.render_template('home.html', response='Please log in first')
	
	if flask.request.method == 'GET':
		return flask.render_template('home.html', show_workspace_form=True, account_id=account_id)
	
	# Handle POST request
	workspace_name = flask.request.form.get('workspace_name')
	if not workspace_name:
		return flask.render_template('home.html', response='Workspace name is required')

	# Retrieve the access token
	access_token = flask.session['credentials']['access_token']

	# Frame.io API endpoint for creating workspace
	workspace_url = f'https://api.frame.io/v4/accounts/{account_id}/workspaces'
	
	# Make the request to Frame.io API
	response = requests.post(
		workspace_url,
		headers={
			'Authorization': f'Bearer {access_token}',
			'Content-Type': 'application/json'
		},
		json={
			'data': {
				'name': workspace_name
			}
		}
	)

	if response.status_code in [200, 201]:
		return flask.redirect(flask.url_for('list_workspaces', account_id=account_id))
	else:
		error_message = f'Failed to create workspace. Status code: {response.status_code}, Response: {response.text}'
		return flask.render_template('home.html', response=error_message)

if __name__ == '__main__':
	# Make sure the hostname and port you provide match the valid redirect URI
	# specified in your project in the Adobe developer Console. 
	# Also, make sure to have `cert.pem` and `key.pem` in your directory
	app.run('localhost', 8000, debug=True, ssl_context=('cert.pem', 'key.pem'))