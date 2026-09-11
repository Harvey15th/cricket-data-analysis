import matplotlib.pyplot as plt
from .csv_prepare import readDict

def plotBrier(evalLogPath, outputPath):
    evalLog = readDict(evalLogPath)

    x = list(range(1, len(evalLog) + 1))
    y = []

    currentSum = 0.0
    numberOfMatches = 0

    for match in evalLog:
        if match['elo_brier'] != '':
            numberOfMatches += 1
            currentSum += float(match['elo_brier'])

            y.append(currentSum / numberOfMatches)
        else:
            x.pop()

    plt.plot(x, y, marker='o', linestyle='-', color='b') 

    y = [0.25]*len(x)
    plt.plot(x, y, marker='o', linestyle='-', color='r') 

    plt.title("Cumulative Brier Score During Verification")
    plt.xlabel("Number of matches")
    plt.ylabel("Average Brier Score")

    plt.savefig(outputPath, dpi=300, bbox_inches='tight')
    plt.show()

    return True

