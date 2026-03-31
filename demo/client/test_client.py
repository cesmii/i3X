import asyncio
import httpx
import threading
import json
import jsonschema
from typing import Any
from urllib.parse import quote


#######################################
##### Test Client Helper Methods ######
#######################################
def pretty_print_json(data):
    """Pretty prints JSON data if it's valid JSON, otherwise prints as-is"""
    try:
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(data)
    except (TypeError, ValueError):
        print(data)


def get_user_selection(valid_selections: list[str] = None):
    """Gets user to select item from list of valid selections

    :param valid_selections: array of strings denoting valid selections
    :return: string user_selection from array of valid selections
    """
    if valid_selections is None:
        raise TypeError("valid_selections cannot be None")

    user_selection = input().strip()
    while user_selection.upper() not in valid_selections:
        print(
            f"Invalid input received. Received '{user_selection}'. Valid selections:{valid_selections}. Please enter a valid selection."
        )
        user_selection = input().strip()

    return user_selection


def get_include_metadata():
    """Prompts user if they want to 'Include Metadata'

    :return: True if user selected to include metadata, false otherwise
    """
    user_selection_include_metadata = input(
        f"Include Metadata? (1: yes, else no): "
    ).strip()
    if user_selection_include_metadata == "1":
        return True
    else:
        return False


async def get(url: str = None, params: dict = None):
    """get executes a get request against
    :param url: complete url of API method being called, up to the ?
    :param params: params for GET request. expects caller enforces expected input
    :return: response from calling url with associated method and passed params
    """
    if url is None:
        raise TypeError("url cannot be None")
    if params is None:
        params = {}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def put(url: str = None, payload: dict = None):
    """put executes a put request against url
    :param payload: JSON Payload to pass to put request
    :param url: complete url of API method being called
    :return: response returned from put request
    """
    if url is None:
        raise TypeError("url cannot be None")
    if payload is None:
        payload = {}

    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=payload)
        response.raise_for_status()
        return response.json()


async def post(url: str = None, payload: dict = None):
    """post executes a post request against url
    :param payload: JSON Payload to pass to post request
    :param url: complete url of API method being called
    :return: response returned from post request
    """
    if url is None:
        raise TypeError("url cannot be None")
    if payload is None:
        payload = {}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


async def delete(url: str = None):
    if url is None:
        raise TypeError("url cannot be None")

    async with httpx.AsyncClient() as client:
        response = await client.delete(url)
        response.raise_for_status()
        return response.json()


#######################################
######## Exploratory Methods ##########
#######################################
async def get_namespaces(base_url: str = None):
    """get_namespaces calls Get Namespaces (RFC 4.1.1)
    :param base_url: base URL of API method being called
    :return: namespaces dict"""
    if base_url is None:
        raise TypeError("base_url cannot be None")
    url = f"{base_url}/namespaces"
    return await get(url)


async def get_object_type(base_url: str = None, element_id: str = None):
    """get_object_type calls Query Object Types by ElementId (RFC 4.1.2)
    :param base_url: base URL of API method being called
    :param element_id: element id
    :return: object type def dict"""
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if element_id is None:
        raise TypeError("element_id cannot be None")
    url = f"{base_url}/objecttypes/query"
    payload = {"elementIds": [element_id]}
    response = await post(url, payload)
    # Response is an array of matching types
    if isinstance(response, list) and len(response) > 0:
        return response[0]
    elif isinstance(response, list):
        raise Exception("Object type not found")
    return response


async def get_object_types(base_url: str = None, namespace_uri: str = None):
    """get_object_types calls Get Object Types (RFC 4.1.3)
    :param base_url: base URL of API method being called
    :param namespace_uri: namespace uri, optional
    :return: object types dict
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    url = f"{base_url}/objecttypes"
    params = {}
    if namespace_uri is not None:
        params["namespaceUri"] = namespace_uri
    return await get(url, params)


async def get_relationship_types(base_url: str = None, namespace_uri: str = None):
    """get_relationship_types calls Get Relationship Types (RFC 4.1.4)
    :param base_url: base URL of API method being called
    :return: relationship types arr
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    url = f"{base_url}/relationshiptypes"
    params = {}
    if namespace_uri is not None:
        params["namespaceUri"] = namespace_uri
    return await get(url, params)


async def get_relationship_type(base_url: str = None, element_id: str = None):
    """get_relationship_type calls Query Relationship Types by ElementId (RFC 4.1.4)
    :param base_url: base URL of API method being called
    :return: relationship type dict
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if element_id is None or element_id == "":
        raise TypeError("element_id cannot be None")
    url = f"{base_url}/relationshiptypes/query"
    payload = {"elementIds": [element_id]}
    response = await post(url, payload)
    # Response is an array of matching relationship types
    if isinstance(response, list) and len(response) > 0:
        return response[0]
    elif isinstance(response, list):
        raise Exception("Relationship type not found")
    return response


async def get_objects(
    base_url: str = None, type_id: str = None, include_metadata: bool = False
):
    """get_instances calls Get Instances of an Object Type (RFC 4.1.5)
    :param base_url: base URL of API method being called
    :param type_id: type id, optional
    :param include_metadata: boolean, if true get instances metadata, default false
    :return: instances dict
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    url = f"{base_url}/objects"
    params = {}
    if type_id is not None:
        params["typeElementId"] = type_id
    if include_metadata:
        params["includeMetadata"] = "true"
    else:
        params["includeMetadata"] = "false"

    json_response = await get(url, params=params)
    return json_response


async def get_relationships(
    base_url: str = None,
    element_id: str = None,
    relationship_type: str = None,
    include_metadata: bool = False,
):
    """get_relationships calls Query Related Objects (RFC 4.1.6)
    :param base_url: base URL of API method being called
    :param element_id: element id
    :param relationship_type: relationship type
    :param include_metadata: boolean, if true include object metadata, default false
    :return: relationships array"""
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if element_id is None:
        raise ValueError("element_id is required to run get_relationships")
    if relationship_type is None:
        raise ValueError("relationship_type is required to run get_relationships")
    url = f"{base_url}/objects/related"
    payload = {
        "elementIds": [element_id],
        "relationshipType": relationship_type,
        "includeMetadata": include_metadata
    }
    response = await post(url, payload)
    # Response is an array of related objects
    return response


async def get_object(
    base_url: str = None, element_id: str = None, include_metadata: bool = False
):
    """get_object calls List Objects by ElementId (RFC 4.1.8)
    :param base_url: base URL of API method being called
    :param element_id: element id
    :param include_metadata: boolean, if true get object metadata, default false
    :return: object dict"""
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if element_id is None or element_id == "":
        raise ValueError("element_id is required to run get_object")
    url = f"{base_url}/objects/list"
    payload = {
        "elementIds": [element_id],
        "includeMetadata": include_metadata        
    }
    response = await post(url, payload)
    # Response is an array of matching objects
    if isinstance(response, list) and len(response) > 0:
        return response[0]
    elif isinstance(response, list):
        raise Exception("Object not found")
    return response


#######################################
########### Value Methods #############
#######################################
async def get_value(
    base_url: str = None, element_id: str = None, include_metadata: bool = False
):
    """get_value calls Query Last Known Values (RFC 4.2.1.1)
    :param base_url: base URL of API method being called
    :param include_metadata: boolean, if true get object metadata, default false
    :param element_id: element id
    :return: value dict keyed by elementId with nested {data: [VQT], ...children}"""
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if element_id is None:
        raise ValueError("element_id is required to run get_value")
    url = f"{base_url}/objects/value"
    payload = {
        "elementIds": [element_id],
        "maxDepth": 1
    }
    response = await post(url, payload)
    # Response is dict keyed by elementId: {elementId: {data: [VQT], ...children}}
    return response


async def get_history(
    base_url: str = None,
    element_id: str = None,
    start_time: str = None,
    end_time: str = None,
    include_metadata: bool = False,
):
    """get_history calls Query Historical Values (RFC 4.2.1.2)
    :param base_url: base url of API method being called
    :param element_id: element id
    :param include_metadata: boolean, if true get history metadata, default false
    :param start_time: start time, optional
    :param end_time: end time, optional
    :return: value dict keyed by elementId with nested {data: [VQT...], ...children}"""
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if element_id is None:
        raise ValueError("element_id is required to run get_history")
    url = f"{base_url}/objects/history"
    payload = {
        "elementIds": [element_id],
        "maxDepth": 1
    }
    if start_time is not None:
        payload["startTime"] = start_time
    if end_time is not None:
        payload["endTime"] = end_time
    response = await post(url, payload)
    # Response is dict keyed by elementId: {elementId: {data: [VQT...], ...children}}
    return response


#######################################
########### Update Methods ############
#######################################
async def update_objects_current_value(
    base_url: str = None,
    element_id: str = None,
    value: Any = None,
    timestamp: str = None,
):
    if base_url is None:
        raise TypeError("base_url cannot be None")
    url = f"{base_url}/objects"
    if element_id is None:
        raise ValueError("element_id is required to run update")
    if value is None:
        raise ValueError("value is required to run update")

    url += f"/{quote(element_id, safe='')}/value"
    payload = value
    return await put(url, payload)

async def update_object_history(
    base_url: str = None,
    element_ids: list[str] = None,
    values: list[str] = None,
    timestamps: list[str] = None,
):
    """update calls Update Object Element LastKnownValue (RFC 4.2.2.1)
    :param base_url: base URL of API method being called
    :param element_ids: element ids to update, required
    :param values: values to update, required
    :param timestamps: timestamps to update, optional - not currently supported by server
    Indices of item across element ID/value/timestamps
    :return: JSON response from update
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    url = f"{base_url}/objects"
    if element_ids is None or element_ids == []:
        raise ValueError("element_ids is required to run update")
    if values is None or values == []:
        raise ValueError("values is required to run update")
    if len(element_ids) != len(values):
        raise ValueError("element_ids and values must have same length")
    if timestamps is None or len(timestamps) != len(values):
        raise ValueError("timestamps must have same length as values")


    updates = []
    for element_id, value, timestamp in zip(element_ids, values, timestamps):
        updates.append(
            {"elementId": element_id, "value": value, "timestamp": timestamp}
        )
    url += "/history"
    payload = updates

    return await put(url, payload)


#######################################
######## Subscription Methods #########
#######################################
async def subscribe(base_url: str = None):
    """
    Calls Create Subscription (RFC 4.2.3.1)
    Creates a subscription that starts in queue mode.
    Use /register to add objects, then /stream for SSE or /sync for queued updates.
    :param base_url: base URL of API method being called
    :return: Json response from subscribe (containing subscription ID)
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    url = f"{base_url}/subscriptions"
    return await post(url, {})


async def register(
    base_url: str = None,
    subscription_id: str = None,
    element_ids: list[str] = None,
    include_metadata: bool = False,
    max_depth: int = 0,
):
    """
    register calls Register Monitored Items (RFC 4.2.3.2)
    :param base_url: base URL of API method being called
    :param max_depth: Max depth of elements to register
    :param include_metadata: Include metadata if true, default false
    :param subscription_id: subscription id to register elements for
    :param element_ids: element ids to register
    :return: JSON response from register
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if subscription_id is None:
        raise ValueError("subscription_id is required to run register")
    if element_ids is None:
        raise ValueError("element_ids is required to run register")

    payload = {
        "subscriptionId": subscription_id,
        "elementIds": element_ids,
        "maxDepth": max_depth,
    }

    url = f"{base_url}/subscriptions/register"
    return await post(url, payload)

async def unregister(
    base_url: str = None,
    subscription_id: str = None,
    element_ids: list[str] = None
):
    """
    unregister calls Unregister Monitored Items (RFC 4.2.3.5)
    :param base_url: base URL of API method being called
    :param subscription_id: subscription id to register elements for
    :param element_ids: element ids to register
    :return: JSON response from register
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if subscription_id is None:
        raise ValueError("subscription_id is required to run register")
    if element_ids is None:
        raise ValueError("element_ids is required to run register")

    payload = {
        "subscriptionId": subscription_id,
        "elementIds": element_ids,
    }

    url = f"{base_url}/subscriptions/unregister"
    return await post(url, payload)

async def sync(base_url: str = None, subscription_id: str = None):
    """
    sync calls Sync (RFC 4.2.3.3)
    :param base_url: base URL of API method being called
    :param subscription_id: subscription id to sync elements for
    :return: json response from sync
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if subscription_id is None:
        raise ValueError("subscription_id is required to run sync")
    url = f"{base_url}/subscriptions/sync"
    return await post(url, {"subscriptionId": subscription_id})

def get_user_selection_any_key():
    input("Press Enter to exit SSE...\n")

async def read_sse(url: str):
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers={"Accept": "text/event-stream"}) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        print(line[6:])  # Strip "data: " prefix for clean JSON output
                    elif line:
                        print(line)
    except asyncio.CancelledError:
        pass
    except httpx.StreamClosed:
        pass
    except Exception as e:
        print(f"SSE stream error: {e}")

def stream(base_url: str, subscription_id: str):
    url = f"{base_url}/subscriptions/stream"

    async def post_and_read_sse():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", url, json={"subscriptionId": subscription_id}, headers={"Accept": "text/event-stream"}) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            print(line[6:])
                        elif line:
                            print(line)
        except asyncio.CancelledError:
            pass
        except httpx.StreamClosed:
            pass
        except Exception as e:
            print(f"SSE stream error: {e}")

    # Create a new asyncio loop in a background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Task for SSE reader
    sse_task = loop.create_task(post_and_read_sse())

    # Run the event loop in a background thread
    def start_loop():
        loop.run_until_complete(sse_task)

    t = threading.Thread(target=start_loop, daemon=True)
    t.start()

    # Blocking input in main thread
    get_user_selection_any_key()

    # Cancel SSE task and wait for thread to finish
    loop.call_soon_threadsafe(sse_task.cancel)
    t.join()
    loop.close()

async def unsubscribe(base_url: str = None, subscription_id: str = None):
    """
    unsubscribe calls Unsubscribe by SubscriptionId (RFC 4.2.3.4)
    :param base_url: base URL of API method being called
    :param subscription_id: subscription id to unsubscribe from
    :return: json response from unsubscribe
    """
    if base_url is None:
        raise TypeError("base_url cannot be None")
    if subscription_id is None:
        raise ValueError("subscription_id is required to run unsubscribe")
    url = f"{base_url}/subscriptions/delete"
    return await post(url, {"subscriptionIds": [subscription_id]})


#######################################
########## Client Functions ###########
#######################################
async def main():
    try:
        print("Welcome to the CESMII I3X API Test Client.")
        default_url = "http://localhost:8080"
        base_url = input(
            f"Enter the base url (or press enter to leave as default '{default_url}'): "
        ).strip()
        if not base_url:
            base_url = default_url

        selections = "\n1: Exploratory Methods\n2: Query Methods\n3: Update Methods\n4: Subscription Methods \nX: Quit\n"

        ##### MAIN INPUT LOOP #####
        while True:  # broken by user input
            print(f"\nPlease make a selection.{selections}")
            user_selection = get_user_selection(["1", "2", "3", "4", "X"])
            if user_selection.upper() == "X":
                exit()

            ##### EXPLORATORY METHODS #####
            elif user_selection == "1":
                while True:
                    menu_text = (
                        "Exploratory Methods\n"
                        "0: Back\n"
                        "1: Get Namespaces\n"
                        "2: Get Object Types\n"
                        "3: Get Object Type\n"
                        "4: Get Objects\n"
                        "5: Get Object\n"
                        "6: Get Relationship Types\n"
                        "7: Get Relationship Type\n"
                        "8: Get Related Objects\n"
                        "X: Quit\n"
                    )
                    print(menu_text)

                    user_selection = get_user_selection(
                        ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X"]
                    )
                    if user_selection.upper() == "X":
                        exit()
                    elif user_selection == "0":
                        break
                    elif user_selection == "1":
                        pretty_print_json(await get_namespaces(base_url))
                    elif user_selection == "2":
                        namespace_uri = input(
                            "Enter namespace URI to filter on (optional, leave blank to return all): "
                        ).strip()
                        if not namespace_uri:
                            namespace_uri = None
                        pretty_print_json(
                            await get_object_types(base_url, namespace_uri)
                        )
                    elif user_selection == "3":
                        object_type = input("Enter Object Type's Element ID: ").strip()
                        try:
                            pretty_print_json(
                                await get_object_type(base_url, object_type)
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"Object type {object_type} not found")
                            else:
                                raise e
                    elif user_selection == "4":
                        type_id = input(
                            "Enter Type ElementID (leave blank to return all instance objects): "
                        ).strip()
                        try:
                            pretty_print_json(
                                await get_objects(
                                    base_url, type_id, get_include_metadata()
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"Type ID {type_id} not found")
                            else:
                                raise e
                    elif user_selection == "5":
                        element_id = input("Enter ElementID (required): ").strip()
                        try:
                            pretty_print_json(
                                await get_object(
                                    base_url, element_id, get_include_metadata()
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"ElementID '{element_id}' not found")
                            else:
                                raise e
                    elif user_selection == "6":
                        namespace_uri = input(
                            "Enter namespace URI to filter on (optional, leave blank to return all): "
                        ).strip()
                        if not namespace_uri:
                            namespace_uri = None
                        pretty_print_json(await get_relationship_types(base_url, namespace_uri))
                    elif user_selection == "7":
                        type_id = input(
                            "Enter RelationshipType ElementID (required): "
                        ).strip()
                        try:
                            pretty_print_json(
                                await get_relationship_type(
                                    base_url, type_id
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"RelationshipType ID {type_id} not found")
                            else:
                                raise e
                    elif user_selection == "8":
                        element_id = input("Enter ElementID (required): ").strip()
                        relationship_type = input(
                            "Enter Relationship Type (required, see 'Get Relationship Types'): "
                        ).strip()
                        try:
                            pretty_print_json(
                                await get_relationships(
                                    base_url,
                                    element_id,
                                    relationship_type,
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(
                                    f"ElementID '{element_id}' or Relationship Type '{relationship_type}' not found"
                                )
                            else:
                                raise e
                    print("\n")

            ##### QUERY METHODS #####
            elif user_selection == "2":
                while True:
                    print(
                        f"Query Methods\n0: Back\n1: Get Last Known Value\n2: Get Historical Values\nX: Quit\n"
                    )
                    user_selection = get_user_selection(["0", "1", "2", "X"])
                    if user_selection.upper() == "X":
                        exit()
                    elif user_selection == "0":
                        break
                    elif user_selection == "1":
                        element_id = input("Enter ElementID (required): ").strip()
                        try:
                            pretty_print_json(
                                await get_value(
                                    base_url, element_id, get_include_metadata()
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"ElementID '{element_id}' not found")
                            else:
                                raise e
                    elif user_selection == "2":
                        element_id = input("Enter ElementID (required): ").strip()
                        start_time = input("Enter Start Time (optional): ").strip()
                        end_time = input("Enter End Time (optional): ").strip()
                        if not start_time:
                            start_time = None
                        if not end_time:
                            end_time = None
                        try:
                            pretty_print_json(
                                await get_history(
                                    base_url,
                                    element_id,
                                    start_time,
                                    end_time,
                                    get_include_metadata(),
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"ElementID '{element_id}' not found")
                            else:
                                raise e
                    print("\n")

            ##### UPDATE METHODS #####
            elif user_selection == "3":
                while True:
                    menu_text = (
                        "Update Methods\n"
                        "0: Back\n"
                        "1: Update Object\n"
                        "2: Update Object History (not implemented)\n"
                        "X: Quit\n"
                    )
                    print(menu_text)

                    user_selection = get_user_selection(["0", "1", "2", "X"])
                    if user_selection.upper() == "X":
                        exit()
                    elif user_selection == "0":
                        break
                    elif user_selection == "1":
                        element_id = input("Enter ElementID of the Object to update: ").strip()
                        value = input(
                            f"Enter the value: "
                        ).strip()

                        if element_id and value:
                            pretty_print_json(
                                await update_objects_current_value(base_url, element_id, json.loads(value), None)
                            )
                    elif user_selection == "2":
                        print("Update Object History is not implemented in this test client.")
                    print("\n")

            ##### SUBSCRIPTION METHODS #####
            elif user_selection == "4":
                while True:
                    menu_text = (
                        "Subscription Methods\n"
                        "0: Back\n"
                        "1: Get Subscription\n"
                        "2: Create Subscription\n"
                        "3: Register Objects\n"
                        "4: Unregister Objects\n"
                        "5: Sync\n"
                        "6: Stream (Open SSE)\n"
                        "7: Delete Subscription\n"
                        "X: Quit\n"
                    )
                    print(menu_text)
                    user_selection = get_user_selection(["0", "1", "2", "3", "4", "5", "6", "7", "X"])
                    if user_selection.upper() == "X":
                        exit()
                    elif user_selection == "0":
                        break
                    elif user_selection == "1":
                        subscription_id = input("Enter Subscription ID: ").strip()
                        try:
                            pretty_print_json(
                                await post(
                                    f"{base_url}/subscriptions/list",
                                    {"subscriptionIds": [subscription_id]}
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"Subscription ID '{subscription_id}' not found")
                    elif user_selection == "2":
                        pretty_print_json(await subscribe(base_url))
                    elif user_selection == "3":
                        subscription_id = input("Enter Subscription ID: ").strip()
                        element_ids = []
                        while True:
                            element_id = input("Enter Element ID to register: ").strip()
                            element_ids.append(element_id)
                            another = input(
                                "Register another Element ID? (1: yes, else no): "
                            ).strip()
                            if another != "1":
                                break
                        try:
                            pretty_print_json(
                                await register(
                                    base_url,
                                    subscription_id,
                                    element_ids,
                                    False,
                                    0,
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(
                                    f"Subscription ID '{subscription_id}' or element in '{element_ids}' not found"
                                )
                    elif user_selection == "4":
                        subscription_id = input("Enter Subscription ID: ").strip()
                        element_ids = []
                        while True:
                            element_id = input("Enter Element ID to unregister: ").strip()
                            element_ids.append(element_id)
                            another = input(
                                "Unregister another Element ID? (1: yes, else no): "
                            ).strip()
                            if another != "1":
                                break
                        try:
                            pretty_print_json(
                                await unregister(
                                    base_url,
                                    subscription_id,
                                    element_ids
                                )
                            )
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(
                                    f"Subscription ID '{subscription_id}' or element in '{element_ids}' not found"
                                )
                    elif user_selection == "5":
                        subscription_id = input("Enter Subscription ID: ").strip()
                        try:
                            pretty_print_json(await sync(base_url, subscription_id))
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"Subscription ID '{subscription_id}' not found")
                    elif user_selection == "6":
                        subscription_id = input("Enter Subscription ID: ").strip()
                        try:
                            stream(base_url, subscription_id)
                        except Exception as e:
                            if str(e).startswith(
                                "Client error '404 Not Found' for url"
                            ):
                                print(f"Subscription ID '{subscription_id}' not found")
                    elif user_selection == "7":
                        subscription_id = input(
                            "Enter Subscription ID to delete: "
                        ).strip()
                        pretty_print_json(await unsubscribe(base_url, subscription_id))

    except Exception as e:
        print(f"an exception occurred: {e}")
        exit()


if __name__ == "__main__":
    asyncio.run(main())
