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
	BinaryBase64DecodePolicy
)

from azure.storage.blob import (
	BlobServiceClient, 
	BlobClient, 
	ContainerClient
)

async def main():
	
	# Code for object detection
	# parse the command line
	parser = argparse.ArgumentParser(description="Classifying an object from a live camera feed and once successfully classified a message is sent to Azure IoT Hub", 
						   formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.imageNet.Usage())
	parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
	parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
	parser.add_argument("--network", type=str, default="googlenet", help="Pre-trained model to load (see below for options)")
	parser.add_argument("--camera", type=str, default="0", help="Index of the MIPI CSI camera to use (e.g. CSI camera 0)\nor for VL42 cameras, the /dev/video device to use.\nby default, MIPI CSI camera 0 will be used.")
	parser.add_argument("--width", type=int, default=1280, help="Desired width of camera stream (default is 1280 pixels)")
	parser.add_argument("--height", type=int, default=720, help="Desired height of camera stream (default is 720 pixels)")
	parser.add_argument("--classNameForTargetObject", type=str, default="", help="Class name of the object that is required to be detected. Once object is detected and threshhold limit has crossed, the message would be sent to Azure IoT Hub")
	parser.add_argument("--detectionThreshold", type=int, default=90, help="The threshold value 'in percentage' for object detection")

	try:
		opt = parser.parse_known_args()[0]
	except:
		parser.print_help()
		sys.exit(0)

	# load the recognition network
	net = jetson.inference.imageNet(opt.network, sys.argv)
	f'Loaded network'
	# create the camera and display
	font = jetson.utils.cudaFont()
	camera = jetson.utils.gstCamera(opt.width, opt.height, opt.camera)
	display = jetson.utils.glDisplay()
	input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)
	f'Loaded display'
	f'{display}'
	f'{camera}'
	# Fetch the connection string from an environment variable
	conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")

	device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
	await device_client.connect()

	counter = 1
	still_looking = True

	# process frames until user exits
	while still_looking:
		# Code for listening to Storage queue

		f'Waiting for request queueMessages'

		queue = QueueClient.from_connection_string(os.getenv("STORAGE_CONNECTION_STRING"), "jetson-nano-object-classification-requests")
		
		# Create the BlobServiceClient object which will be used to create a container client
		blob_service_client = BlobServiceClient.from_connection_string(os.getenv("STORAGE_CONNECTION_STRING"))
		container_name = "jetson-nano-object-classification-responses"

		# Receive messages one-by-one
		queueMessage = queue.receive_message()
		f'{queueMessage}'
		if queueMessage:
			hasNewMessage = True
			f'Valid message'
			queueMessageArray = queueMessage.content.split("|")
			requestContent = queueMessage.content
			correlationId = queueMessageArray[0]
			classForObjectDetection = queueMessageArray[1]
			thresholdForObjectDetection = queueMessageArray[2]
			queue.delete_message(queueMessage)
			f"request content = {requestContent}"
			f"classForObjectDetection value = {classForObjectDetection}"
			f"Threshold value = {thresholdForObjectDetection}"
			f"correlationId = {correlationId}"

			while hasNewMessage:
				f'About to capture image'
				# capture the image
				# img, width, height = camera.CaptureRGBA()
				img = input.Capture()

				# classify the image
				class_idx, confidence = net.Classify(img)
				f'Classified image'

				# find the object description
				class_desc = net.GetClassDesc(class_idx)
				f'Got class description'

				# overlay the result on the image	
				font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 15, 50, font.Green, font.Gray40)
				f'Set font overlay'

				# render the image
				display.RenderOnce(img, img.width, img.height)
				f'Rendered once'

				# update the title bar
				display.SetTitle("{:s} | Network {:.0f} FPS | Looking for {:s}".format(net.GetNetworkName(), net.GetNetworkFPS(), opt.classNameForTargetObject))
				f'Display is set'

				# print out performance info
				net.PrintProfilerTimes()
				if class_desc == classForObjectDetection and (confidence*100) >= int(thresholdForObjectDetection):
					message = requestContent + "|" + str(confidence*100)
					font.OverlayText(img, img.width, img.height, "Found {:s} at {:05.2f}% confidence".format(class_desc, confidence * 100), 775, 50, font.Blue, font.Gray40)
					display.RenderOnce(img, img.width, img.height)
					savedFile='test.jpg'
					jetson.utils.saveImageRGBA(savedFile,img, img.width,img.height)

					# Create a blob client using the local file name as the name for the blob
					folderMark = "/"
					upload_path = folderMark.join([correlationId, savedFile])
					blob_client = blob_service_client.get_blob_client(container=container_name, blob=upload_path)

					print("\nUploading to Azure Storage as blob:\n\t" + savedFile)

					# Upload the created file
					with open(savedFile, "rb") as data:
					    blob_client.upload_blob(data)


					f"Saved image"
					await device_client.send_message(message)
					f"Message sent for found object"
					still_looking = True
					hasNewMessage = False
				
			await device_client.disconnect()

if __name__ == "__main__":
	#asyncio.run(main())
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
	loop.close()
