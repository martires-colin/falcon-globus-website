from asyncio.windows_events import NULL
from socket import timeout
from ssl import HAS_TLSv1_1
from tracemalloc import start
import globus_sdk
from globus_sdk.scopes import GroupsScopes, AuthScopes, TransferScopes
import webbrowser
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_session import Session
import json

app = Flask(__name__)
app.secret_key = 'c9db57edadab97704a3b696d'

CLIENT_ID = "fe1fe34a-b528-4c7d-8708-5ebcfc53cc5a"
CLIENT_SECRET = "CQyDAvpU1oGp36Hs7omJZRFTzbLtPFOmje6yFCnmIGY="
REDIRECT_URI = "http://localhost:5000/code_page"
SCOPES = [
            GroupsScopes.view_my_groups_and_memberships,
            TransferScopes.all,
            AuthScopes.openid,
            AuthScopes.email,
            AuthScopes.profile
        ]

client = globus_sdk.ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)

@app.route("/")
@app.route("/login")
def login():
    if session.get("globus_auth_token"):
        return redirect(url_for('dashboard'))
    else:
        client.oauth2_start_flow(redirect_uri=REDIRECT_URI, requested_scopes=SCOPES)
        return render_template(
            'login.html',
            auth_url=client.oauth2_get_authorize_url()
        )

@app.route("/code_page")
def code_page():
    auth_code = request.args.get('code')
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    session["globus_auth_token"] = token_response.by_resource_server["auth.globus.org"]["access_token"]
    session["globus_transfer_token"] = token_response.by_resource_server["transfer.api.globus.org"]["access_token"]
    session["globus_groups_token"] = token_response.by_resource_server["groups.api.globus.org"]["access_token"]
    session["isLoggedIn"] = True

    return redirect(url_for('dashboard'))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("globus_auth_token"):
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/updateSrc', methods=['POST'])
def updateSrc():

    srcCollection = request.form["srcCollection"]
    srcPath = request.form["srcPath"]

    if srcCollection and srcPath:
        srcFiles = getFiles(srcCollection, srcPath)
    else:
        srcFiles = []

    return jsonify({'files': srcFiles["DATA"]})


@app.route('/updateDest', methods=['POST'])
def updateDest():

    destCollection = request.form["destCollection"]
    destPath = request.form["destPath"]

    if destCollection and destPath:
        destFiles = getFiles(destCollection, destPath)
    else:
        destFiles = []
        
    return jsonify({'files': destFiles["DATA"]})


@app.route('/transferFiles', methods=['POST'])
def transferFiles():
    selectedFiles = request.form.getlist("selectedFiles[]")
    return jsonify({'data': selectedFiles})


# RETRIEVE USER INFO
@app.route("/user_info")
def user_info():
    if not session.get("globus_auth_token"):
        return redirect(url_for('login'))

    authToken = session["globus_auth_token"]
    auth_client = globus_sdk.AuthClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(authToken)
    )

    return render_template('userInfo.html', user_info=auth_client.oauth2_userinfo())


# SEARCH COLLECTIONS
def searchCollections(tc):
    ep_search = input("\nSearch Collections: ")

    print('\n----------------Collections-----------------\n')
    for ep in tc.endpoint_search(ep_search):
        print(
            f'Name: {ep["display_name"]}\n' \
            f'Owner: {ep["owner_string"]}\n' \
            f'Organization: {ep["organization"]}\n' \
            f'Endpoint ID: {ep["id"]}\n'
        )


# TEST VALUES
# ep_id = 'ceea5ca0-89a9-11e7-a97f-22000a92523b'
# path = '/usr/include/'

# RETRIEVE USER FILES
def getFiles(epID, path):
    transferToken = session["globus_transfer_token"]
    transfer_client = globus_sdk.TransferClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(transferToken)
    )

    return transfer_client.operation_ls(epID, path=path, orderby=["name"])


if __name__ == "__main__":
    app.run(debug=True)
