# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from azure.kusto.ingest import (
    IngestionProperties,
    QueuedIngestClient,
    ReportLevel,
)

from automation_full_test import AutomaticScheduling
from bs4 import BeautifulSoup
import csv
import datetime
import logging
import os
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

OUTPUT_DIR = sys.argv[1]
# authenticate with AAD application.
KUSTO_CLUSTER = os.environ.get('KUSTO_CLUSTER')
KUSTO_CLIENT_ID = os.environ.get('KUSTO_CLIENT_ID')
KUSTO_CLIENT_SECRET = os.environ.get('KUSTO_CLIENT_SECRET')
# get tenant id from https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
KUSTO_TENANT_ID = os.environ.get('KUSTO_TENANT_ID')
KUSTO_DATABASE = os.environ.get('KUSTO_DATABASE')
KUSTO_TABLE = os.environ.get('KUSTO_TABLE')
BUILD_ID = os.environ.get('BUILD_ID')
USER_TARGET = os.environ.get('USER_TARGET')
PYTHON_VERSION = os.environ.get('PYTHON_VERSION')
OS_VERSION = os.environ.get('PLATFORM')
INSTANCE_MODULES = AutomaticScheduling().get_instance_modules()


def generate_csv_file():
    for module in INSTANCE_MODULES.keys():
        logger.warning('Start generate csv file for {TARGET}.'.format(TARGET=module))
        data = []
        parallel_file = f'{OUTPUT_DIR}/{module}.{OS_VERSION}.report.parallel.html'
        sequential_file = f'{OUTPUT_DIR}/{module}.{OS_VERSION}.report.sequential.html'

        def _get_data(html_file):
            data = []
            if os.path.exists(html_file):
                with open(html_file) as file:
                    bs = BeautifulSoup(file, "html.parser")
                    results = bs.find(id="results-table")
                    Source = 'LiveTest'
                    BuildId = BUILD_ID
                    Module = module
                    Description = ''
                    ExtendedProperties = ''
                    for result in results.find_all('tbody'):
                        Name = result.find('td', {'class': 'col-name'}).text.split('::')[-1]
                        Duration = result.find('td', {'class': 'col-duration'}).text
                        Status = result.find('td', {'class': 'col-result'}).text
                        if Status == 'Failed':
                            contents = result.find('td', {'class': 'extra'}).find('div', {'class': 'log'}).contents
                            Details = ''
                            for content in contents:
                                if content.name == 'br':
                                    Details += '\n'
                                elif not content.name:
                                    Details += content
                                else:
                                    logger.warning(content.name)
                        else:
                            Details = ''
                        EndDateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        StartDateTime = (datetime.datetime.now() - datetime.timedelta(seconds=int(float(Duration)))).strftime("%Y-%m-%d %H:%M:%S")
                        data.append([Source, BuildId, OS_VERSION, PYTHON_VERSION, Module, Name, Description, StartDateTime, EndDateTime, Duration, Status, Details, ExtendedProperties])
            return data

        data.extend(_get_data(parallel_file))
        data.extend(_get_data(sequential_file))
        logger.warning('CSV data: {data}'.format(data=data))

        with open(f'{OUTPUT_DIR}/{module}.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        logger.warning('Finish generate csv file for {TARGET}.'.format(TARGET=module))


def send_to_kusto():
    for module in INSTANCE_MODULES.keys():
        # TODO add filter for main repo and ext repo
        if USER_TARGET.lower() in ['all', '']:
            logger.info('Start send csv data to kusto db for {TARGET}'.format(TARGET=module))
            kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(KUSTO_CLUSTER, KUSTO_CLIENT_ID, KUSTO_CLIENT_SECRET, KUSTO_TENANT_ID)
            # The authentication method will be taken from the chosen KustoConnectionStringBuilder.
            client = QueuedIngestClient(kcsb)

            # there are a lot of useful properties, make sure to go over docs and check them out
            ingestion_props = IngestionProperties(
                database=KUSTO_DATABASE,
                table=KUSTO_TABLE,
                data_format=DataFormat.CSV,
                report_level=ReportLevel.FailuresAndSuccesses
            )

            # ingest from file
            result = client.ingest_from_file(f"{OUTPUT_DIR}/{module}.csv", ingestion_properties=ingestion_props)
            # Inspect the result for useful information, such as source_id and blob_url
            print(repr(result))
            logger.info('Finsh send csv data to kusto db for {}.'.format(module))


if __name__ == '__main__':
    generate_csv_file()
    # send_to_kusto()
