import argparse
import json
import os

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, help='Path to the data file for input')
parser.add_argument('--output', type=str, help='Path to the data file for output')

args = parser.parse_args()

INPUT_PATH = args.input
OUTPUT_PATH = args.output

Processed_2D = []

for file in os.listdir(INPUT_PATH):
    if file.endswith('.json'):
        with open(os.path.join(INPUT_PATH, file), 'r') as f:
            matchData = json.load(f)


        match_id = str(file)[:-5]
        date = matchData['info']['dates'][0]
        team_1 = matchData['info']['teams'][0]
        team_2 = matchData['info']['teams'][1]
        match_type = matchData['info']['match_type']
        try:
            result = 'win'
            winner = matchData['info']['outcome']['winner']
            processed_data = [match_id, date, team_1, team_2, winner, match_type]
        except:
            result = matchData['info']['outcome']['result']
            processed_data = [match_id, date, team_1, team_2, result, match_type]
        Processed_2D.append(processed_data)

Processed_2D.sort(key = lambda x: x[1])

for processed_data in Processed_2D:
    processed_data = ','.join(processed_data)
    processed_data += "\n"

    with open(OUTPUT_PATH, 'a') as f:
        f.write(processed_data)

            
