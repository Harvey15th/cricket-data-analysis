from typing import Dict
import argparse
from train import train
from benchmark import benchmark
from predict import predict
MODE_CHOICES = ['train', 'verify', 'predict']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",
                        choices = MODE_CHOICES,
                        help= f'Mode of operation: {str(MODE_CHOICES)}')
    parser.add_argument("-input_data", 
                        type=str, 
                        help='Path to the game data used for training or benchma',
                        argument_default = None)
    parser.add_argument("-output_path",
                        type=str,
                        help='Path to the output file',
                        argument_default = None)
    parser.add_argument("-input_data_verification", 
                        type=str, 
                        help="Path to the data file used for verification",
                        argument_default = None)
    parser.add_argument("-team_1",
                        type=str,
                        help="Name of first team used for predict",
                        argument_default=None)
    parser.add_argument("-team_2",
                        type=str,
                        help="Name of second team used for predict",
                        argument_default=None)
    args = parser.parse_args()

    if args.mode == 'train':
        #Verification
        if args.input_data is None:
            raise ValueError("Input data path must be provided for training mode.")
        if args.output_path is None:
            raise ValueError("Output path must be provided for training mode.")

        #Training
        if train(args.input_data, args.output_path):
            print(f"Successful! Results added to {args.output_path}")
        else:
            print("Training Unsuccessful")

    elif args.mode == 'benchmark':
        #Verification
        if args.input_data is None:
            raise ValueError("Input data path must be provided for benchmarking")
        if args.input_data_verification is None:
            raise ValueError("input_data_verification must be provided for benchmarking")
        if args.output_path is None:
            raise ValueError("Output path must be provided for benchmarking")
        
        #Benchmarking
        if benchmark(args.input_data, args.input_data_verification, args.output_path):
            print(f"Successful! Results added to {args.output_path}")
        else:
            print("Benchmark Unsuccessful")
    
    elif args.mode == 'predict':
        #Verification
        if args.team_1 is None:
            raise ValueError("Team 1 must be provided for prediction")
        if args.team_2 is None:
            raise ValueError("Team 2 must be provided for prediction")
        if args.input_data is None:
            raise ValueError("Input data path must be provided for prediction")

        #Prediction
        if not predict(args.input_data, args.team_1, args.team_2):
            print("Prediction Unsuccessful")

        

    
        

