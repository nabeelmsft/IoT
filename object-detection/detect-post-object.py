#!/usr/bin/python

import jetson.inference
import jetson.utils

import argparse
import sys

import os
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from azure.storage.queue import (
    QueueClient,
    BinaryBase64EncodePolicy,
    BinaryBase64DecodePolicy,
)

from azure.storage.blob.aio import BlobServiceClient, BlobClient, ContainerClient

# A helper class to support async blob actions.
class BlobHelperAsync(object):
    async def block_blob_upload_async(self, upload_path, savedFile):
        blob_service_client = BlobServiceClient.from_connection_string(
            os.getenv("STORAGE_CONNECTION_STRING")
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


async def main():

    # Code for object detection
    # parse the command line
    parser = argparse.ArgumentParser(
        description="Classifying an object from a live camera feed and once successfully classified a message is sent to Azure IoT Hub",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=jetson.inference.imageNet.Usage(),
    )
    parser.add_argument(
        "input_URI", type=str, default="", nargs="?", help="URI of the input stream"
    )
    parser.add_argument(
        "output_URI", type=str, default="", nargs="?", help="URI of the output stream"
    )
    parser.add_argument(
        "--network",
        type=str,
        default="googlenet",
        help="Pre-trained model to load (see below for options)",
    )
    parser.add_argument(
        "--camera",
        type=str,
        default="0",
        help="Index of the MIPI CSI camera to use (e.g. CSI camera 0)\nor for VL42 cameras, the /dev/video device to use.\nby default, MIPI CSI camera 0 will be used.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Desired width of camera stream (default is 1280 pixels)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Desired height of camera stream (default is 720 pixels)",
    )
    parser.add_argument(
        "--classNameForTargetObject",
        type=str,
        default="",
        help="Class name of the object that is required to be detected. Once object is detected and threshhold limit has crossed, the message would be sent to Azure IoT Hub",
    )
    parser.add_argument(
        "--detectionThreshold",
        type=int,
        default=90,
        help="The threshold value 'in percentage' for object detection",
    )

    try:
        opt = parser.parse_known_args()[0]
    except:
        parser.print_help()
        sys.exit(0)

    # load the recognition network
    net = jetson.inference.imageNet(opt.network, sys.argv)

    # create the camera and display
    font = jetson.utils.cudaFont()
    camera = jetson.utils.gstCamera(opt.width, opt.height, opt.camera)
    display = jetson.utils.glDisplay()
    input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)

    # Fetch the connection string from an environment variable
    conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")

    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    await device_client.connect()

    counter = 1
    still_looking = True
    # process frames until user exits
    while still_looking:
        # Code for listening to Storage queue

        print("Waiting for request queue_messages")

        queue = QueueClient.from_connection_string(
            os.getenv("STORAGE_CONNECTION_STRING"),
            "jetson-nano-object-classification-requests",
        )

        # Receive messages one-by-one
        queue_message = queue.receive_message()
        print(queue_message)
        if queue_message:
            has_new_message = True
            queue_message_array = queue_message.content.split("|")
            requestContent = queue_message.content
            correlationId = queue_message_array[0]
            classForObjectDetection = queue_message_array[1]
            thresholdForObjectDetection = int(queue_message_array[2])
            queue.delete_message(queue_message)

            while has_new_message:
                # capture the image
                # img, width, height = camera.CaptureRGBA()
                img = input.Capture()

                # classify the image
                class_idx, confidence = net.Classify(img)

                # find the object description
                class_desc = net.GetClassDesc(class_idx)

                # overlay the result on the image
                font.OverlayText(
                    img,
                    img.width,
                    img.height,
                    "{:05.2f}% {:s}".format(confidence * 100, class_desc),
                    15,
                    50,
                    font.Green,
                    font.Gray40,
                )

                # render the image
                display.RenderOnce(img, img.width, img.height)

                # update the title bar
                display.SetTitle(
                    "{:s} | Network {:.0f} FPS | Looking for {:s}".format(
                        net.GetNetworkName(),
                        net.GetNetworkFPS(),
                        opt.classNameForTargetObject,
                    )
                )

                # print out performance info
                net.PrintProfilerTimes()
                if (
                    class_desc == classForObjectDetection
                    and (confidence * 100) >= thresholdForObjectDetection
                ):
                    message = requestContent + "|" + str(confidence * 100)
                    font.OverlayText(
                        img,
                        img.width,
                        img.height,
                        "Found {:s} at {:05.2f}% confidence".format(
                            class_desc, confidence * 100
                        ),
                        775,
                        50,
                        font.Blue,
                        font.Gray40,
                    )
                    display.RenderOnce(img, img.width, img.height)
                    savedFile = "imageWithDetection.jpg"
                    jetson.utils.saveImageRGBA(savedFile, img, img.width, img.height)

                    # Create the BlobServiceClient object which will be used to create a container client
                    blob_service_client = BlobServiceClient.from_connection_string(
                        os.getenv("STORAGE_CONNECTION_STRING")
                    )
                    container_name = "jetson-nano-object-classification-responses"

                    # Create a blob client using the local file name as the name for the blob
                    folderMark = "/"
                    upload_path = folderMark.join([correlationId, savedFile])

                    blob_helper = BlobHelperAsync()
                    await blob_helper.block_blob_upload_async(upload_path, savedFile)

                    await device_client.send_message(message)
                    still_looking = True
                    has_new_message = False

            await device_client.disconnect()


if __name__ == "__main__":
    # asyncio.run(main())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
