from asyncio.windows_events import NULL
from socket import timeout
from ssl import HAS_TLSv1_1
from tracemalloc import start
import globus_sdk
from globus_sdk.scopes import GroupsScopes, AuthScopes, TransferScopes
import webbrowser
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = 'c9db57edadab97704a3b696d'



# @app.route('/-tut')
# @app.route('/home-tut')
# def home_page_tut():
#     return render_template('home-tut.html')

# @app.route('/market-tut')
# def market_page_tut():

#     items = [
#         {'id': 1, 'name': 'Phone', 'barcode': '893212299897', 'price': 500},
#         {'id': 2, 'name': 'Laptop', 'barcode': '123985473165', 'price': 900},
#         {'id': 3, 'name': 'Keyboard', 'barcode': '231985128446', 'price': 150}
#     ]

#     return render_template('market-tut.html', items=items)






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
@app.route("/home")
def home():
    client.oauth2_start_flow(redirect_uri=REDIRECT_URI, requested_scopes=SCOPES)
    return render_template(
        'home.html',
        auth_url=client.oauth2_get_authorize_url()
    )

@app.route("/code_page")
def code_page():
    auth_code = request.args.get('code')
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    session["globus_auth_token"] = token_response.by_resource_server["auth.globus.org"]["access_token"]
    session["globus_transfer_token"] = token_response.by_resource_server["transfer.api.globus.org"]["access_token"]
    session["globus_groups_token"] = token_response.by_resource_server["groups.api.globus.org"]["access_token"]

    return redirect(url_for('dashboard'))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    # authToken = session["globus_auth_token"]
    # transferToken = session["globus_transfer_token"]
    # groupsToken = session["globus_groups_token"]
    if "globus_auth_token" and "globus_transfer_token" and "globus_groups_token" in session:
        
        if request.method == "POST":

            srcCollection = ''
            srcPath = ''
            destCollection = ''
            destPath = ''

            srcCollection = request.form["srcCollection"]
            srcPath = request.form["srcPath"]
            destCollection = request.form["destCollection"]
            destPath = request.form["destPath"]

            if srcCollection != '' and srcPath != '':
                srcFiles = getFiles(srcCollection, srcPath)
            else:
                srcFiles = []

            if destCollection != '' and destPath != '':
                destFiles = getFiles(destCollection, destPath)
            else:
                destFiles = []

            return render_template('dashboard.html', srcFiles=srcFiles, destFiles=destFiles, isValid=True)

        else:
            return render_template('dashboard.html', isValid=False)

        # change epID and path to variables retireved from search?
        # files = getFiles('ceea5ca0-89a9-11e7-a97f-22000a92523b', '/~/')
                
        # return render_template('dashboard.html', files=files)
    else:
        return redirect(url_for('home'))




# RETRIEVE USER INFO
@app.route("/user_info")
def user_info():
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

    # ep_id = input("\nEnter endpoint ID: ").strip()
    # path = input("Specify Path: ").strip()
    # print('\n----------------FILE INFORMATION-----------------\n')
    # for entry in transfer_client.operation_ls(epID, path=path, orderby=["name"]):
    #     print(
    #         f'File Name: {entry["name"]}\n' \
    #         f'Last Modified: {entry["last_modified"]}\n' \
    #         f'Size: {entry["size"]} bytes\n' \
    #         f'Permissions: {entry["permissions"]}\n' \
    #         f'Type: {entry["type"]}\n' \
    #         f'User: {entry["user"]}\n' \
    #         f'Group: {entry["group"]}\n' \
    #         f'DATA_TYPE: {entry["DATA_TYPE"]}\n' \
    #         f'link_group: {entry["link_group"]}\n' \
    #         f'link_last_modified: {entry["link_last_modified"]}\n' \
    #         f'link_size: {entry["link_size"]}\n' \
    #         f'link_target: {entry["link_target"]}\n' \
    #         f'link_user: {entry["link_user"]}\n'
    #     )

    return transfer_client.operation_ls(epID, path=path, orderby=["name"])


# TRANSFER FILES
# def transferFiles(tc):
    
#     # sourceEP = input("\nEnter source end point: ").strip()
#     # destEP = input("Enter destination end point: ").strip()
    
#     sourceEP = 'ceea5ca0-89a9-11e7-a97f-22000a92523b'
#     destEP = 'b256c034-1578-11eb-893e-0a5521ff3f4b'

#     sourceFilePath = input("Enter source file path: ").strip()
#     destFilePath = input("Enter destination file path: ").strip()

#     tdata = globus_sdk.TransferData(tc, sourceEP, destEP)
#     tdata.add_item(sourceFilePath, destFilePath)
#     transfer_result = tc.submit_transfer(tdata)

#     taskID = transfer_result["task_id"]

#     tc.task_wait(taskID, timeout=60, polling_interval=1)
#     # while not tc.task_wait(taskID, timeout=1, polling_interval=1):
#     #     print('.', end="")

#     taskStatus = tc.get_task(taskID)

#     print(f'\nTRANSFER RESULT:\n{transfer_result}')
#     print(f'\nTASK STATUS:\n{taskStatus}')


# def displayMenu():
#     print(
#         '\n---------------Menu OPTIONS---------------\n'
#         '1: Display User Info\n' \
#         '2: Display User Group Info\n' \
#         '3: Search Collections\n' \
#         '4: List Collection Files\n' \
#         '5: Transfer Files\n' \
#         '6: Exit Program\n'
#     )

# # RETRIEVE GROUP INFORMATION
# # @app.route("/group_info/<globus_groups_token>")
# def getGroupInfo(globus_groups_token):
#     groups_client = globus_sdk.GroupsClient(
#         authorizer=globus_sdk.AccessTokenAuthorizer(globus_groups_token)
#     )
#     group_data = []
#     groups = groups_client.get_my_groups()
#     for group in groups:
#         group_data.append(group)

#     return {"groups": group_data}

# def main():

#     authClient, transferClient, groupsClient = startAuthorization()

    # while True:
    #     displayMenu()
    #     userInput = input()

    #     if userInput == '1':
    #         getUserInfo(authClient)
    #     elif userInput == '2':
    #         getGroupInfo(groupsClient)
    #     elif userInput == '3':
    #         searchCollections(transferClient)
    #     elif userInput == '4':
    #         getFiles(transferClient)
    #     elif userInput == '5':
    #         transferFiles(transferClient)
    #     elif userInput == '6':
    #         break

    # transferFiles(transferClient)

if __name__ == "__main__":
    app.run(debug=True)
