# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import json
import time
import os, uuid
import sys
import asyncio
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

# global counters
TEMPERATURE_THRESHOLD = 25
TWIN_CALLBACKS = 0
RECEIVED_MESSAGES = 0

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ( "IoT Edge Module for Python - version:0.0.7221256" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        # define behavior for receiving an input message on input1
        async def input1_listener(module_client):
            global RECEIVED_MESSAGES
            global TEMPERATURE_THRESHOLD
            while True:
                try:
                    method_request = await module_client.receive_method_request()
                    print (
                        "\nMethod callback called with:\nrequestID={request_id}\nmethodName = {method_name}\npayload = {payload}".format(
                            request_id=method_request.request_id,
                            method_name=method_request.name,
                            payload=method_request.payload
                        )
                    )


                    #f = open("jobs.txt", "a+")
                    #f.write("method_request.payload")
                    #f.close()
                    connect_str = "DefaultEndpointsProtocol=http;BlobEndpoint=http://azureblobstorageoniotedge:11002/request-processor;AccountName=request-processor;AccountKey=xq77wbfp+KwI77bonG5MziCuaUEOaYCym61goRX/Swk="
                    connect_str = "DefaultEndpointsProtocol=http;BlobEndpoint=http://azureblobstorageoniotedge:11002/metadatastore;AccountName=metadatastore;AccountKey=iYMKd+VQXJDxNwGInLuzl9tA5oUlxTcZnIVhfcGoUnRkXgGl7CROA7fYjOvXd+qFulujnhqjsdtYZpfNHqAVPg=="
                    print("Going for Connection establishment")
                    # Create the BlobServiceClient object which will be used to create a container client
                    try:
                        blob_service_client = BlobServiceClient.from_connection_string(connect_str, api_version='2019-07-07')
                        print("Getting API version")
                        print(blob_service_client.api_version)
                        print("Got API version")
                    except Exception as exception:
                        print("error occured while openning connection")
                        print(exception)

                    print(blob_service_client)

                    try:
                        new_container = blob_service_client.create_container("containerfromblobservice")
                        properties = new_container.get_container_properties()
                        print(properties)
                    except Exception as exe:
                        print("Container already exists.")
                        print(exe)
                        print("Printed error")

                    container_client = blob_service_client.get_container_client("containertest")
                    container_client.create_container(public_access='blob')
                    print("Created container: ")
                    try:
                        for blob in container_client.list_blobs():
                            print("Found blob: ", blob.name)
                    except ResourceNotFoundError:
                        print("Container not found.")
                        container_client.create_container(public_access=blob)

                    try:
                        blob_containers = blob_service_client.list_containers(include_metadata=True)
                        print(blob_containers)
                        print("Getting all the containers")
                        for container in blob_containers:
                            print(container)
                    except Exception as exception:
                        print("Error occured while getting containers")
                        print(exception)
                    #print(blob_service_client.get_service_properties())
                    #print(blob_service_client.get_account_information())
                    print("Connection established")

                    # # Create a unique name for the container
                    # container_name = "quickstart" + str(uuid.uuid4())
                    # container_name = "jetsonedgecontainer"

                    # # Create the container
                    # container_client = blob_service_client.create_container(container_name)
                    # print("container created")

                    # # Create a file in local data directory to upload and download
                    # local_path = ""
                    # local_file_name = "quickstart" + str(uuid.uuid4()) + ".txt"
                    # upload_file_path = os.path.join(local_path, local_file_name)

                    # # Write text to the file
                    # file = open(upload_file_path, 'w')
                    # file.write("Hello, World!")
                    # file.close()

                    # # Create a blob client using the local file name as the name for the blob
                    # blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

                    # print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

                    # # Upload the created file
                    # with open(upload_file_path, "rb") as data:
                    #     blob_client.upload_blob(data)

                    response_payload = {"Response": "Executed direct method {}".format(method_request.name)}
                    response_status = 200

                    # Creating a method response.
                    methodResponse = MethodResponse.create_from_method_request(method_request, response_status, response_payload)

                    # Responding back to the direct method call.
                    await module_client.send_method_response(methodResponse)


                except Exception as ex:
                    print ("Unexpected error in input1_listener: %s" % ex)


        # twin_patch_listener is invoked when the module twin's desired properties are updated.
        async def twin_patch_listener(module_client):
            global TWIN_CALLBACKS
            global TEMPERATURE_THRESHOLD
            while True:
                try:
                    data = await module_client.receive_twin_desired_properties_patch()  # blocking call
                    print( "The data in the desired properties patch was: %s" % data)
                    if "TemperatureThreshold" in data:
                        TEMPERATURE_THRESHOLD = data["TemperatureThreshold"]
                    TWIN_CALLBACKS += 1
                    print ( "Total calls confirmed: %d\n" % TWIN_CALLBACKS )
                except Exception as ex:
                    print ( "Unexpected error in twin_patch_listener: %s" % ex )

        # define behavior for halting the application
        def stdin_listener():
            while True:
                try:
                    selection = input("Press Q to quit\n")
                    if selection == "Q" or selection == "q":
                        print("Quitting...")
                        break
                except:
                    time.sleep(10)

        # Schedule task for C2D Listener
        listeners = asyncio.gather(input1_listener(module_client), twin_patch_listener(module_client))

        print ( "The sample is now waiting for messages. ")

        # Run the stdin listener in the event loop
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for messages
        await user_finished

        # Cancel listening
        listeners.cancel()

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % e )
        raise

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()

    # If using Python 3.7 or above, you can use following code instead:
    # asyncio.run(main())