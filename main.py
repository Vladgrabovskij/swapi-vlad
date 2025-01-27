import pandas as pd
import requests
import logging
import argparse
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("SWAPI")

class SWAPIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_data(self, resource):
        data_list = []
        next_url = f"{self.base_url}{resource}/"

        while next_url:
            log.info(f"Fetching data from: {next_url}")
            response = requests.get(next_url)
            response.raise_for_status()
            payload = response.json()

            data_list.extend(payload['results'])
            next_url = payload.get('next')

        return data_list

class SWAPIProcessor:
    def __init__(self, client):
        self.client = client
        self.records = {}

    def retrieve_data(self, resource):
        items = self.client.get_data(resource)
        self.records[resource] = pd.DataFrame(items)

    def filter_columns(self, resource, columns_to_remove):
        if resource in self.records:
            self.records[resource] = self.records[resource].drop(columns=columns_to_remove, errors='ignore')

    def export_to_excel(self, file_name):
        with pd.ExcelWriter(file_name) as excel_writer:
            for resource_name, dataframe in self.records.items():
                dataframe.to_excel(excel_writer, sheet_name=resource_name.capitalize(), index=False)
        log.info(f"Data successfully exported to: {file_name}")

def parse_args():
    parser = argparse.ArgumentParser(description="SWAPI Data Export Tool")
    parser.add_argument('--resources', type=str, required=True, help="Comma-separated list of SWAPI resources, e.g., people,planets")
    parser.add_argument('--output-file', type=str, required=True, help="Name of the output Excel file")
    parser.add_argument('--filters', type=str, help="Path to a JSON file specifying column filters")
    return parser.parse_args()

def load_filters_file(file_path):
    if file_path:
        try:
            with open(file_path, 'r') as filter_file:
                return json.load(filter_file)
        except Exception as ex:
            log.error(f"Error reading filters file: {ex}")
    return {}

def main():
    arguments = parse_args()

    api_client = SWAPIClient(base_url="https://swapi.dev/api/")
    data_processor = SWAPIProcessor(api_client)

    resources = arguments.resources.split(',')
    column_filters = load_filters_file(arguments.filters)

    for resource in resources:
        log.info(f"Processing resource: {resource}")
        data_processor.retrieve_data(resource)

        if resource in column_filters:
            data_processor.filter_columns(resource, column_filters[resource])

    data_processor.export_to_excel(arguments.output_file)

if __name__ == "__main__":
    main()
