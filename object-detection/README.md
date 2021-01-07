# Two Factor authentication leveraging AI on the edge using Jetson Nano and Azure IoT
## Introduction
The goal of this post is to show how we can use the Jetson Nano device running AI on edge  combined with power of Azure platform to create an end to end AI on edge  solution. We are going to use a custom model that is developed using Jetson nano device.
## Architecture
![Architecture](https://github.com/nabeelmsft/IoT/blob/master/object-detection/visio/Architecture.png?raw=true "Architecture")

## Running AI on the Edge
Jetson Nano device is running detect-object.py
https://github.com/nabeelmsft/IoT/blob/master/object-detection/detect-object.py


```python
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
	ContainerClient, 
	__version__
)

async def main():
	
	# Code for object detection
	# parse the command line
	parser = argparse.ArgumentParser(description="Classifying an object from a live camera feed and once successfully classified a message is sent to Azure IoT Hub", 
						   formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.imageNet.Usage())
	parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
	parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
	parser.add_argument("--network", type=str, default="googlenet", help="pre-trained model to load (see below for options)")
	parser.add_argument("--camera", type=str, default="0", help="index of the MIPI CSI camera to use (e.g. CSI camera 0)\nor for VL42 cameras, the /dev/video device to use.\nby default, MIPI CSI camera 0 will be used.")
	parser.add_argument("--width", type=int, default=1280, help="desired width of camera stream (default is 1280 pixels)")
	parser.add_argument("--height", type=int, default=720, help="desired height of camera stream (default is 720 pixels)")
	parser.add_argument("--classNameForTargetObject", type=str, default="", help="class name of the object that is required to be detected. Once object is detected and threshhold limit has crossed, the message would be sent to Azure IoT Hub")
	parser.add_argument("--detectionThreshold", type=int, default=90, help="The threshold value 'in percentage' for object detection")

	try:
		opt = parser.parse_known_args()[0]
	except:
		print("")
		parser.print_help()
		sys.exit(0)

	# load the recognition network
	net = jetson.inference.imageNet(opt.network, sys.argv)
	print('Loaded network')
	# create the camera and display
	font = jetson.utils.cudaFont()
	camera = jetson.utils.gstCamera(opt.width, opt.height, opt.camera)
	display = jetson.utils.glDisplay()
	input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)
	print('Loaded display')
	print(display)
	print(camera)
	# Fetch the connection string from an environment variable
	conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
	print("Connection string as: ")
	print(conn_str)

	device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
	await device_client.connect()

	counter = 1
	stillLooking = True

	# process frames until user exits
	while stillLooking:
		# Code for listening to Storage queue

		print('Waiting for request queueMessages')

		queue = QueueClient.from_connection_string(os.getenv("STORAGE_CONNECTION_STRING"), "jetson-nano-object-classification-requests")
		
		# Create the BlobServiceClient object which will be used to create a container client
		blob_service_client = BlobServiceClient.from_connection_string(os.getenv("STORAGE_CONNECTION_STRING"))
		container_name = "jetson-nano-object-classification-responses"

		# Receive messages one-by-one
		queueMessage = queue.receive_message()
		print(queueMessage)
		if queueMessage != None:
			hasNewMessage = True
			print('Valid message')
			queueMessageArray = queueMessage.content.split("|")
			requestContent = queueMessage.content
			correlationId = queueMessageArray[0]
			classForObjectDetection = queueMessageArray[1]
			thresholdForObjectDetection = queueMessageArray[2]
			queue.delete_message(queueMessage)
			print('request content', requestContent)
			print('classForObjectDetection value', classForObjectDetection)
			print('Threshold value', thresholdForObjectDetection)
			print('correlationId', correlationId)

			while hasNewMessage:
				print('About to capture image')
				# capture the image
				# img, width, height = camera.CaptureRGBA()
				img = input.Capture()

				# classify the image
				class_idx, confidence = net.Classify(img)
				print('Classified image')

				# find the object description
				class_desc = net.GetClassDesc(class_idx)
				print('Got class description')

				# overlay the result on the image	
				font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 15, 50, font.Green, font.Gray40)
				print('Set font overlay')

				# render the image
				display.RenderOnce(img, img.width, img.height)
				print('Rendered once')

				# update the title bar
				display.SetTitle("{:s} | Network {:.0f} FPS | Looking for {:s}".format(net.GetNetworkName(), net.GetNetworkFPS(), opt.classNameForTargetObject))
				print('Display is set')

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
					uploadPath = correlationId + folderMark + savedFile
					blob_client = blob_service_client.get_blob_client(container=container_name, blob=uploadPath)

					print("\nUploading to Azure Storage as blob:\n\t" + savedFile)

					# Upload the created file
					with open(savedFile, "rb") as data:
					    blob_client.upload_blob(data)


					print("Saved image")
					await device_client.send_message(message)
					print("Message sent for found object")
					print(conn_str)
					stillLooking = True
					hasNewMessage = False
				
			await device_client.disconnect()

if __name__ == "__main__":
	#asyncio.run(main())
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
	loop.close()

```

Following actions are taking place in detect-object.py

1. detect-object.py is constantly reading the request coming to Azure Storage Queue.
1. Once request is received, using the custom AI model running on Jetson Nano device, object is searched based on the request.
1. As soon as object is detected, the python code running on Jetson Nano device posts captured image to Azure Blob storage.
1. In addition, the code running on Jetson Nano device sends message to Azure IoT hub informing of correct match for the request.

## Web Interface
Following steps are taking on web interface.
1. User logins by supplying user name and password.
1. User is authenticated on the first factor using the combination of user name and password.
1. On successful completion of first factor, the web interface creates a request and sends that to Azure Storage as shown below:
![Azure Storage Queue view](https://github.com/nabeelmsft/IoT/blob/master/object-detection/assets/queue-message.PNG?raw=true "Azure Storage Queue detail view")
Detail view:
![Azure Storage Queue view](https://github.com/nabeelmsft/IoT/blob/master/object-detection/assets/queue-message-detail.PNG?raw=true "Azure Storage Queue detail view")
1. The Jetson Nano device which is listening to Azure Storage Queue initiates the second factor and completes the second factor.
1. Once the second factor is completed, the Jetson Nano device posts captured image for second factor to Azure Storage Blob as shown below:
![Azure Blob storage view](https://github.com/nabeelmsft/IoT/blob/master/object-detection/assets/storage-view.PNG?raw=true "Azure Blob storage view")
1. The web interface shows the captured image completing the flow as shown below:
![Second factor](https://github.com/nabeelmsft/IoT/blob/master/object-detection/assets/gil-detected-image.PNG?raw=true "Second factor")


## Conclusion
In this post we have seen how simple it is for running  AI on edge using Nvidia Jetson nano device leveraging Azure platform.
## Appendix - AI Model
The custom AI model that we have for this post is created using three class of images. 

Following is the view of the custom AI model created using https://netron.app/:
![AI Model](https://github.com/nabeelmsft/IoT/blob/master/object-detection/assets/resnet18.onnx.png?raw=true "AI Model")

