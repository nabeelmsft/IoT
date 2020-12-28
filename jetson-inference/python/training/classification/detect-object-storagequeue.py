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

		# Receive messages one-by-one
		queueMessage = queue.receive_message()
		print(queueMessage)
		if queueMessage != None:
			hasNewMessage = True
			print('Valid message')
			queueMessageArray = queueMessage.content.split("|")
			correlationId = queueMessageArray[0]
			classForObjectDetection = queueMessageArray[1]
			thresholdForObjectDetection = queueMessageArray[2]
			queue.delete_message(queueMessage)
			print('classForObjectDetection value', classForObjectDetection)
			print('Threshold value', thresholdForObjectDetection)

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
					message = "Found " + class_desc + " with confidence : " + str(confidence*100)
					font.OverlayText(img, img.width, img.height, "Found {:s} at {:05.2f}% confidence".format(class_desc, confidence * 100), 775, 50, font.Blue, font.Gray40)
					display.RenderOnce(img, img.width, img.height)
					jetson.utils.saveImageRGBA('test.jpg',img, img.width,img.height)
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

