# Azure Post
How to detect an object using a pre-trained model and post to Azure IoT Hub.

# Pre-requisites
## Azure IoT Hub setup
The very first step is to create Azure IoT Hub in your Azure subscription. Follow the directions mentioned below to setup Azure IoT hub.

[Create an IoT hub using the Azure portal](https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-create-through-portal)

Once the IoT Hub is setup, you can proceed with the steps mentioned in the following section to register your NVidia Jetson Nano device.
## Device conection setup
1. Navigate to your Azure IoT Hub.
![alt text](images/navigatetoazureiothub.png "Navigate to Azure IoT Hub")

2. Select "IoT devices" and select "+ New".
![alt text](images/selectiotdevices.png "Select IoT devices and select +New")

3. Enter the Device ID.

![alt text](images/createdevice.png "Enter device id")

4. Save new device.
5. Select newly created device.
6. Save "Primary connection string". This will be used in defining "IOTHUB_DEVICE_CONNECTION_STRING" environment variable on NVIDIA Jetson device.
![alt text](images/deviceconnectionstring.png "Enter device id")

## Device pre-requisites

# Steps
1. Clone the source code from repository or download the folder for Azure-Post. For example 'IoT' folder.
```bash
~/IoT
```
2. Open the Jetson-nano terminal window.
3. Navigate to the 'azureposts' folder as shown below:
```bash
~/IoT/nvidia-jetson-nano/samples/azureposts
```
4. Create  IOTHUB_DEVICE_CONNECTION_STRING variable that was saved as part of Azure IoT Hub Setup prerequisite as shown below:
```bash
export IOT_HUB_DEVICE_CONNECTION_STRING = "HOSTName=XXXXXX.azure-devices.net;DeviceId=XXXXX;SahredAccessKey=XXXXXXXXXX"
```
5. Run the following command
```bash
python3.6 custom-model-azure-post.py --classNameForTargetObject=[Target object class name] --model=[path to your custom model] --input_blob=input_0 --output_blob=output_0 --labels=[path to your datasets's labels text file]
```
Example:
```bash
python3.6 custom-model-azure-post.py --model=/home/dlinano/jetson-inference/python/training/classification/[custom-model]/resnet18.onnx --input_blob=input_0 --output_blob=output_0 --labels=/home/dlinano/datasets/gil/labels.txt
```

#### Parameter details:
    --classNameForTargetObject = class name for the object that you want to detect in your custom model
    --model = path to your custom model. 
    --labels = path for the labels file on your custom model