import os
import json
import argparse

from cellpose import io, models

def main(args):

    logger, _ = io.logger_setup()

    model = models.CellposeModel(gpu=True, pretrained_model="cyto2")

    channels = [0, 0]

    train_dir = args.train_dir
    valid_dir = args.valid_dir
    experiment_name = args.experiment_name
    experiments_dir = args.experiments_dir

    save_dir = os.path.join(experiments_dir, experiment_name)

    logger.info("Loading training and validation data...")
    output = io.load_train_test_data(train_dir, valid_dir)
    train_data, train_labels, _, valid_data, valid_labels, _ = output

    logger.info("Starting model training...")
    model.train(train_data, train_labels, 
        test_data=valid_data,
        test_labels=valid_labels,
        channels=channels, 
        save_path=save_dir, 
        n_epochs=500,
        learning_rate=0.02,
        weight_decay=0.0001,
        nimg_per_epoch=16,
        min_train_masks=1,
        model_name=experiment_name)

    diam_labels = model.diam_labels.copy()

    with open(os.path.join(save_dir, "diam_estiamte.json"), "w") as f:
        json.dump({"diam_labels": diam_labels}, f)
        logger.info("Diameter labels saved to diam_estimate.json")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset paths and model name argument parser')

    parser.add_argument('--train_dir', type=str, required=True, help='Path to the training directory')
    parser.add_argument('--valid_dir', type=str, required=True, help='Path to the validation directory')
    parser.add_argument('--experiments_dir', type=str, default="./experiments", help='Directory to output images and evaluation')
    parser.add_argument('--experiment_name', type=str, required=True, help='Path to the testing directory')

    args = parser.parse_args()

    if os.path.exists(args.output_path):
        print(f"The experiments {args.experiments_dir} already exists.")
        exit()

    main(args)