from socket import timeout
from tracemalloc import start
import globus_sdk
from globus_sdk.scopes import GroupsScopes, AuthScopes, TransferScopes


CLIENT_ID = "5e68eed0-a383-4dbd-9756-bdbadb6461cc"
CLIENT_SECRET = "FNIpPmPfzkNWFjwjqq0/giRPrJVa5ZCCngglwG2jHJ0="
REDIRECT_URI = "http://localhost:3000/login"
SCOPES = [
            GroupsScopes.view_my_groups_and_memberships,
            TransferScopes.all,
            AuthScopes.openid,
            AuthScopes.email,
            AuthScopes.profile
        ]


def startAuthorization():
    client = globus_sdk.ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)

    # start the authorization flow
    client.oauth2_start_flow(redirect_uri=REDIRECT_URI, requested_scopes=SCOPES)

    # redirect to authorization url and exchange code for token
    authorize_url = client.oauth2_get_authorize_url()
    print(f"Please go to this URL and login:\n\n{authorize_url}\n")
    auth_code = input("Please enter the code here: ").strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # use token to retrive data from Resource Servers
    globus_auth_data = token_response.by_resource_server["auth.globus.org"]
    globus_transfer_data = token_response.by_resource_server["transfer.api.globus.org"]
    globus_groups_data = token_response.by_resource_server["groups.api.globus.org"]

    # retrieve access tokens from Data
    globus_auth_token = globus_auth_data["access_token"]
    globus_transfer_token = globus_transfer_data["access_token"]
    globus_groups_token = globus_groups_data["access_token"]

    # use tokens to establish clients
    auth_client = globus_sdk.AuthClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(globus_auth_token)
    )

    transfer_client = globus_sdk.TransferClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(globus_transfer_token)
    )

    groups_client = globus_sdk.GroupsClient(
        authorizer=globus_sdk.AccessTokenAuthorizer(globus_groups_token)
    )

    # display data retrieved from each resource server
    # print(f'\nHERE: \n{token_response.by_resource_server}\n')
    return auth_client, transfer_client, groups_client


# RETRIEVE GROUP INFORMATION
def getGroupInfo(gc):
    print("\n---------------GROUP INFORMATION---------------\n")
    for group in gc.get_my_groups():
        # parse the group to get data for output
        if group.get("enforce_session"):
            session_enforcement = "strict"
        else:
            session_enforcement = "not strict"
        roles = ",".join({m["role"] for m in group["my_memberships"]})

        print(
          f'ID: {group["id"]}\n' \
          f'Name: {group["name"]}\n' \
          f'Type: {group["group_type"]}\n' \
          f'Session Enforcement: {group["group_type"]}\n' \
          f'Roles: {roles}\n'
        )


# RETRIEVE USER INFO
def getUserInfo(ac):
    user_info = ac.oauth2_userinfo()

    identities = []
    for identity in user_info["identity_set"]:
        identities.append(identity["identity_provider_display_name"])

    id_list = ', '.join(identities)

    print('\n----------------USER INFORMATION----------------\n')
    print(
        f'Sub: {user_info["sub"]}\n' \
        f'Organization: {user_info["organization"]}\n' \
        f'Name: {user_info["name"]}\n' \
        f'Username: {user_info["preferred_username"]}\n' \
        f'IDP: {user_info["identity_provider"]}\n' \
        f'IDP Display Name: {user_info["identity_provider_display_name"]}\n' \
        f'Email: {user_info["email"]}\n' \
        f'Last Authentication: {user_info["last_authentication"]}\n' \
        f'Identity Set: {id_list}\n'
    )


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
def getFiles(tc, ep_id, path):
    # ep_id = input("\nEnter endpoint ID: ").strip()
    # path = input("Specify Path: ").strip()
    print('\n----------------FILE INFORMATION-----------------\n')
    # for entry in tc.operation_ls(ep_id, path=path, orderby=["name"]):
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
    #         f'link_user: {entry["link_user"]}\n' \
    #     )

    print(tc.operation_ls(ep_id, path=path, orderby=["name"]))


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

    getFiles(transferClient, 'ceea5ca0-89a9-11e7-a97f-22000a92523b', '/~/')
    # transferFiles(transferClient)

if __name__ == "__main__":
    main()