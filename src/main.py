from data_generation import DataGenerator
from config import ORIGINAL_DATA_PATHS, DATASET_PATH
from statistics import Statistics

import json


if __name__ == "__main__":
    #DG = DataGenerator()
    #DG.generate(ORIGINAL_DATA_PATHS, DATASET_PATH)

    with open(DATASET_PATH) as f:
        data = json.load(f)

    S = Statistics(data)
    print(S.get_no_types())
    print(S.get_no_words())
    print(S.get_no_sentence())
    print(S.get_no_data())
    S.get_histogram(10)
    S.get_histogram(10, True)