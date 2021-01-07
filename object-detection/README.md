# Two Factor authentication leveraging AI on the edge using Jetson Nano and Azure IoT
## Introduction
The goal of this post is to show how we can use the Jetson Nano device running AI on edge  combined with power of Azure platform to create an end to end AI on edge  solution. We are going to use a custom model that is developed using Jetson nano device.
## Architecture
![Architecture](https://github.com/nabeelmsft/IoT/blob/master/object-detection/visio/Architecture.png?raw=true "Architecture")

## Running AI on the Edge
Jetson Nano device is running detect-object.py
https://github.com/nabeelmsft/IoT/blob/master/object-detection/detect-object.py

<script src="https://gist.github.com/nabeelmsft/45ad8b391d9c240d59fddea18d01e190.js"></script>

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
![Second factor](https://github.com/nabeelmsft/IoT/blob/master/object-detection/assets/hulk-detected-image.PNG?raw=true "Second factor")


## Conclusion
In this post we have seen how simple it is for running  AI on edge using Nvidia Jetson nano device leveraging Azure platform.
## Appendix - AI Model
The custom AI model that we have for this post is created using three class of images. 

Following is the view of the custom AI model:
![AI Model](https://github.com/nabeelmsft/IoT/blob/master/object-detection/assets/resnet18.onnx.png?raw=true "AI Model")

