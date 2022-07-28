from socket import timeout
from tracemalloc import start
import globus_sdk
from globus_sdk.scopes import GroupsScopes, AuthScopes, TransferScopes
import webbrowser
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify
import json

app = Flask(__name__)


CLIENT_ID = "fe1fe34a-b528-4c7d-8708-5ebcfc53cc5a"
CLIENT_SECRET = "CQyDAvpU1oGp36Hs7omJZRFTzbLtPFOmje6yFCnmIGY="
# REDIRECT_URI should probably be homepage
REDIRECT_URI = "http://localhost:5000/code_page"
SCOPES = [
            GroupsScopes.view_my_groups_and_memberships,
            TransferScopes.all,
            AuthScopes.openid,
            AuthScopes.email,
            AuthScopes.profile
        ]


client = globus_sdk.ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)

@app.route("/auth_url")
def startAuthorization():
    client.oauth2_start_flow(redirect_uri=REDIRECT_URI, requested_scopes=SCOPES)
    return {
        "auth_url": client.oauth2_get_authorize_url()
    }

# can change "/code_page" later
@app.route("/code_page")
def tokens():
    auth_code = request.args.get('code')
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # use token to retrive data from Resource Servers
    globus_auth_data = token_response.by_resource_server["auth.globus.org"]
    globus_transfer_data = token_response.by_resource_server["transfer.api.globus.org"]
    globus_groups_data = token_response.by_resource_server["groups.api.globus.org"]

    return {
        "globus_auth_token": globus_auth_data["access_token"],
        "globus_transfer_token": globus_transfer_data["access_token"],
        "globus_groups_token": globus_groups_data["access_token"]
    }


# RETRIEVE GROUP INFORMATION
@app.route("/group_info/<globus_groups_token>")
def getGroupInfo(globus_groups_token):
    groups_client = globus_sdk.GroupsClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(globus_groups_token)
    )
    group_data = []
    groups = groups_client.get_my_groups()
    for group in groups:
        group_data.append(group)

    return jsonify({"groups": group_data})

# RETRIEVE USER INFO
@app.route("/user_info/<globus_auth_token>")
def getUserInfo(globus_auth_token):
    auth_client = globus_sdk.AuthClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(globus_auth_token)
    )
    user_info = auth_client.oauth2_userinfo()

    identities = []
    for identity in user_info["identity_set"]:
        identities.append(identity["identity_provider_display_name"])
    id_list = ', '.join(identities)

    return {
        'Sub': user_info["sub"],
        'Organization': user_info["organization"],
        'Name':user_info["name"],
        'Username': user_info["preferred_username"],
        'IDP': user_info["identity_provider"],
        'IDP Display Name': user_info["identity_provider_display_name"],
        'Email': user_info["email"],
        'Last Authentication': user_info["last_authentication"],
        'Identity Set': id_list
    }


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
def getFiles(tc):
    ep_id = input("\nEnter endpoint ID: ").strip()
    path = input("Specify Path: ").strip()
    print('\n----------------FILE INFORMATION-----------------\n')
    for entry in tc.operation_ls(ep_id, path=path, orderby=["name"]):
        print(
            f'File Name: {entry["name"]}\n' \
            f'Last Modified: {entry["last_modified"]}\n' \
            f'Size: {entry["size"]} bytes\n' \
            f'Permissions: {entry["permissions"]}\n' \
            f'Type: {entry["type"]}\n' \
            f'User: {entry["user"]}\n' \
            f'Group: {entry["group"]}\n' \
            f'DATA_TYPE: {entry["DATA_TYPE"]}\n' \
            f'link_group: {entry["link_group"]}\n' \
            f'link_last_modified: {entry["link_last_modified"]}\n' \
            f'link_size: {entry["link_size"]}\n' \
            f'link_target: {entry["link_target"]}\n' \
            f'link_user: {entry["link_user"]}\n' \
        )


# TRANSFER FILES
def transferFiles(tc):
    
    # sourceEP = input("\nEnter source end point: ").strip()
    # destEP = input("Enter destination end point: ").strip()
    
    sourceEP = 'ceea5ca0-89a9-11e7-a97f-22000a92523b'
    destEP = 'b256c034-1578-11eb-893e-0a5521ff3f4b'

    sourceFilePath = input("Enter source file path: ").strip()
    destFilePath = input("Enter destination file path: ").strip()

    tdata = globus_sdk.TransferData(tc, sourceEP, destEP)
    tdata.add_item(sourceFilePath, destFilePath)
    transfer_result = tc.submit_transfer(tdata)

    taskID = transfer_result["task_id"]

    tc.task_wait(taskID, timeout=60, polling_interval=1)
    # while not tc.task_wait(taskID, timeout=1, polling_interval=1):
    #     print('.', end="")

    taskStatus = tc.get_task(taskID)

    print(f'\nTRANSFER RESULT:\n{transfer_result}')
    print(f'\nTASK STATUS:\n{taskStatus}')


def displayMenu():
    print(
        '\n---------------Menu OPTIONS---------------\n'
        '1: Display User Info\n' \
        '2: Display User Group Info\n' \
        '3: Search Collections\n' \
        '4: List Collection Files\n' \
        '5: Transfer Files\n' \
        '6: Exit Program\n'
    )

def main():

    authClient, transferClient, groupsClient = startAuthorization()

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

    transferFiles(transferClient)

if __name__ == "__main__":
    app.run(debug=True)
