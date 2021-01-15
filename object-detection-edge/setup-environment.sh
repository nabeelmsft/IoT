hub_name="nvidia-deepstream-hub"
nvidiaJetsonEdgeDevice="object-detection-edge-device"
az iot hub device-identity create --device-id $nvidiaJetsonEdgeDevice --edge-enabled --hub-name $hub_name