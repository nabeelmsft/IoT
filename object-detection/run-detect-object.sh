export DATASET=~/IoT/datasets/gil_background_hulk
python3 detect-object.py --model=gil_background_hulk/resnet18.onnx --input_blob=input_0 --output_blob=output_0 --labels=$DATASET/labels.txt --camera=csi://0 --classNameForTargetObject=hulk --detectionThreshold=95
