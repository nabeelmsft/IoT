# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import uuid
import re
import json
import time
import types
import os
import sys
import asyncio
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse
from azure.storage.queue.aio import QueueClient

# global counters
TEMPERATURE_THRESHOLD = 25
TWIN_CALLBACKS = 0
RECEIVED_MESSAGES = 0

# A helper class to support async blob and queue actions.
class StorageHelperAsync:
    async def block_blob_upload_async(self, upload_path, savedFile):
        blob_service_client = BlobServiceClient.from_connection_string(
            os.getenv("storage_connection_string")
        )
        container_name = "jetson-nano-object-classification-responses"

        async with blob_service_client:
            # Instantiate a new ContainerClient
            container_client = blob_service_client.get_container_client(container_name)

            # Instantiate a new BlobClient
            blob_client = container_client.get_blob_client(blob=upload_path)

            # Upload content to block blob
            with open(savedFile, "rb") as data:
                await blob_client.upload_blob(data)
                # [END upload_a_blob]

    # Code for listening to Storage queue
    async def queue_receive_message_async(self):
        # from azure.storage.queue.aio import QueueClient
        queue_client = QueueClient.from_connection_string(
            os.getenv("storage_connection_string"),
            "iot-edge-object-classification-requests",
        )

        async with queue_client:
            response = queue_client.receive_messages(messages_per_page=1)
            async for message in response:
                queue_message = message
                await queue_client.delete_message(message)
                return queue_message

    async def queue_send_message_async(self, message):
        # from azure.storage.queue.aio import QueueClient
        print("storage connection string from send")
        print(os.getenv("storage_connection_string"))
        print("end storage connection string from send")
        queue_client = QueueClient.from_connection_string(
            os.getenv("storage_connection_string"),
            "iot-edge-object-classification-requests",
        )

        async with queue_client:
            await queue_client.send_message(message)
    
async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ("IoT Edge Module for Python - version:1.3.01121" )
        print(os.environ['storage_connection_string'])
        print("Printed storage_connection_string")
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
                    print(method_request.payload)
                    print(type(method_request.payload))
                    json_object = json.dumps(method_request.payload)
                    print(json_object)
                    print(type(json_object))
                    json_deserialized = json.loads(json_object)
                    print(json_deserialized)
                    print(type(json_deserialized))
                    module_key = hex(uuid.getnode())
                    print(module_key)
                    correlation_id = json_deserialized["CoorelationId"]
                    class_name = json_deserialized["ClassName"]
                    threshold_percentage = json_deserialized["ThresholdPercentage"]
                    print(correlation_id)
                    print(class_name)
                    print(threshold_percentage)
                    module_payload = correlation_id + "|" + class_name + "|" + str(threshold_percentage) + "|" + module_key
                    print(module_payload)
                    storage_helper = StorageHelperAsync()
                    await storage_helper.queue_send_message_async(module_payload)
                    print("message sent to queue")
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