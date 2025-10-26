#!/bin/bash

# Example script for converting ForceUMI data to LeRobot format

# Activate LeRobot environment
# conda activate lerobot

# Example 1: Basic conversion
echo "Example 1: Basic conversion"
python convert_forceumi_to_lerobot.py \
  --data_dir data/session_20250101_120000 \
  --output_repo_id username/forceumi-task1 \
  --task "Pick and place red cube"

# Example 2: Convert with image resizing
echo -e "\nExample 2: Convert with image resizing"
python convert_forceumi_to_lerobot.py \
  --data_dir data/session_20250101_120000 \
  --output_repo_id username/forceumi-task1-224 \
  --task "Pick and place red cube" \
  --target_size 224 224

# Example 3: Skip warmup frames
echo -e "\nExample 3: Skip warmup frames"
python convert_forceumi_to_lerobot.py \
  --data_dir data/session_20250101_120000 \
  --output_repo_id username/forceumi-task1-clean \
  --task "Pick and place red cube" \
  --skip_frames 10

# Example 4: Convert all sessions
echo -e "\nExample 4: Convert all sessions"
python convert_forceumi_to_lerobot.py \
  --data_dir data \
  --output_repo_id username/forceumi-full-dataset \
  --task "Various manipulation tasks" \
  --target_size 224 224 \
  --skip_frames 5

# Example 5: Convert and push to HuggingFace Hub
echo -e "\nExample 5: Convert and push to Hub"
# Make sure to login first: huggingface-cli login
python convert_forceumi_to_lerobot.py \
  --data_dir data/session_20250101_120000 \
  --output_repo_id username/forceumi-task1 \
  --task "Pick and place red cube" \
  --target_size 224 224 \
  --fps 30 \
  --push_to_hub

echo -e "\nConversion complete!"

