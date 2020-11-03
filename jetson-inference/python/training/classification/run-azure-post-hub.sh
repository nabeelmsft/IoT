export DATASET=~/IoT/datasets/gil_background_hulk
export IOTHUB_DEVICE_CONNECTION_STRING = "HostName=nvidia-deepstream-hub.azure-devices.net;DeviceId=nvidia-deepstream-deviceid;SharedAccessKey=7vwVc9zj3r3pq/mSJ4zAXsUIuICJlvi9eLE2FKmT91s="
python3 azure-post-hub.py --model=gil_background_hulk/resnet18.onnx --input_blob=input_0 --output_blob=output_0 --labels=$DATASET/labels.txt --camera=csi://0 --classNameForTargetObject=hulk --detectionThreshold=98
