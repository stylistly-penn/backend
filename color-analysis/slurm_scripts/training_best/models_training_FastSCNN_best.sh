#!/bin/bash
#SBATCH --partition=students-prod
#SBATCH --gres=gpu:2
#SBATCH --gpus=2
#SBATCH --error=models/outputs/models_training_FastSCNN_best.err
#SBATCH --output=models/outputs/models_training_FastSCNN_best.out

python models_training_or_hpo.py --config=best --model_name=fastscnn --evaluate=False --n_epochs=20