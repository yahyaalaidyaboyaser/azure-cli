#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azdev.utilities import get_path_table
from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat
from azure.kusto.ingest import (
    IngestionProperties,
    QueuedIngestClient,
    ReportLevel,
)
from bs4 import BeautifulSoup
import csv
import datetime
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

OUTPUT_DIR = sys.argv[1]

BUILD_ID = os.environ.get('BUILD_ID')
INSTANCE_CNT = int(os.environ.get('INSTANCE_CNT'))
INSTANCE_IDX = int(os.environ.get('INSTANCE_IDX'))
# authenticate with AAD application.
KUSTO_CLIENT_ID = os.environ.get('KUSTO_CLIENT_ID')
KUSTO_CLIENT_SECRET = os.environ.get('KUSTO_CLIENT_SECRET')
KUSTO_CLUSTER = os.environ.get('KUSTO_CLUSTER')
KUSTO_DATABASE = os.environ.get('KUSTO_DATABASE')
KUSTO_TABLE = os.environ.get('KUSTO_TABLE')
# get tenant id from https://docs.microsoft.com/en-us/onedrive/find-your-office-365-tenant-id
KUSTO_TENANT_ID = os.environ.get('KUSTO_TENANT_ID')
OS_VERSION = os.environ.get('PLATFORM')
PLATFORM = os.environ.get('PLATFORM', None)
PYTHON_VERSION = os.environ.get('PYTHON_VERSION')
USER_LIVE = os.environ.get('USER_LIVE')
USER_PARALLELISM = int(os.environ.get('USER_PARALLELISM'))
USER_TARGET = os.environ.get('USER_TARGET')
USER_TARGET = os.environ.get('USER_TARGET')

# Test time (minutes) for each module.
jobs = {
    'acr': 34,
    'acs': 150,
    'advisor': 6,
    'ams': 43,
    'apim': 182,
    'appconfig': 38,
    'appservice': 63,
    'aro': 7,
    'backup': 150,
    'batch': 9,
    'batchai': 7,
    'billing': 6,
    'botservice': 8,
    'cdn': 23,
    'cloud': 6,
    'cognitiveservices': 21,
    'config': 6,
    'configure': 6,
    'consumption': 6,
    'container': 11,
    'cosmosdb': 102,
    'databoxedge': 7,
    'deploymentmanager': 6,
    'dla': 8,
    'dls': 8,
    'dms': 7,
    'eventgrid': 12,
    'eventhubs': 55,
    'extension': 6,
    'feedback': 6,
    'find': 6,
    'hdinsight': 23,
    'identity': 18,
    'iot': 36,
    'keyvault': 63,
    'kusto': 37,
    'lab': 6,
    'managedservices': 6,
    'maps': 6,
    'marketplaceordering': 18,
    'monitor': 34,
    'mysql': 6,
    'natgateway': 6,
    'netappfiles': 66,
    'network': 319,
    'policyinsights': 20,
    'privatedns': 17,
    'profile': 21,
    'rdbms': 193,
    'redis': 69,
    'relay': 9,
    'reservations': 6,
    'resource': 73,
    'role': 7,
    'search': 79,
    'security': 15,
    'servicebus': 43,
    'serviceconnector': 7,
    'servicefabric': 220,
    'signalr': 11,
    'sql': 264,
    'sqlvm': 50,
    'storage': 150,
    'synapse': 56,
    'util': 6,
    'vm': 186,
    'ext-account': 6,
    'ext-acrquery': 6,
    'ext-acrtransfer': 6,
    'ext-ad': 6,
    'ext-adp': 6,
    'ext-aem': 16,
    'ext-ai-examples': 6,
    'ext-aks-preview': 217,
    'ext-alertsmanagement': 6,
    'ext-alias': 6,
    'ext-amg': 15,
    'ext-application-insights': 10,
    'ext-appservice-kube': 10,
    'ext-attestation': 5,
    'ext-authV2': 7,
    'ext-automanage': 6,
    'ext-automation': 6,
    'ext-azure-firewall': 41,
    'ext-bastion': 6,
    'ext-billing-benefits': 6,
    'ext-blockchain': 6,
    'ext-blueprint': 6,
    'ext-change-analysis': 7,
    'ext-cli-translator': 6,
    'ext-cloudservice': 6,
    'ext-communication': 21,
    'ext-confcom': 6,
    'ext-confidentialledger': 6,
    'ext-confluent': 6,
    'ext-connectedk8s': 23,
    'ext-connectedmachine': 7,
    'ext-connectedvmware': 6,
    'ext-connection-monitor-preview': 12,
    'ext-containerapp': 9,
    'ext-containerapp-preview': 6,
    'ext-cosmosdb-preview': 138,
    'ext-costmanagement': 7,
    'ext-custom-providers': 6,
    'ext-databox': 22,
    'ext-databricks': 19,
    'ext-datadog': 6,
    'ext-datafactory': 17,
    'ext-datamigration': 6,
    'ext-dataprotection': 6,
    'ext-datashare': 9,
    'ext-db-up': 12,
    'ext-desktopvirtualization': 6,
    'ext-dev-spaces': 6,
    'ext-devcenter': 6,
    'ext-diskpool': 6,
    'ext-dms-preview': 6,
    'ext-dnc': 8,
    'ext-dns-resolver': 10,
    'ext-dynatrace': 7,
    'ext-edgeorder': 13,
    'ext-elastic': 6,
    'ext-elastic-san': 8,
    'ext-eventgrid': 6,
    'ext-express-route-cross-connection': 6,
    'ext-fleet': 25,
    'ext-fluid-relay': 7,
    'ext-footprint': 6,
    'ext-front-door': 11,
    'ext-functionapp': 6,
    'ext-guestconfig': 6,
    'ext-hack': 6,
    'ext-hardware-security-modules': 78,
    'ext-healthbot': 8,
    'ext-healthcareapis': 56,
    'ext-hpc-cache': 6,
    'ext-image-copy': 6,
    'ext-image-gallery': 8,
    'ext-import-export': 6,
    'ext-init': 6,
    'ext-interactive': 6,
    'ext-internet-analyzer': 6,
    'ext-ip-group': 7,
    'ext-k8s-configuration': 6,
    'ext-k8s-extension': 6,
    'ext-keyvault-preview': 6,
    'ext-kusto': 6,
    'ext-load': 6,
    'ext-log-analytics': 6,
    'ext-log-analytics-solution': 6,
    'ext-logic': 6,
    'ext-logz': 6,
    'ext-maintenance': 11,
    'ext-managedccfs': 6,
    'ext-managementpartner': 6,
    'ext-mesh': 7,
    'ext-mixed-reality': 7,
    'ext-mobile-network': 6,
    'ext-monitor-control-service': 8,
    'ext-netappfiles-preview': 37,
    'ext-network-manager': 7,
    'ext-next': 6,
    'ext-nginx': 6,
    'ext-notification-hub': 7,
    'ext-nsp': 6,
    'ext-offazure': 6,
    'ext-orbital': 6,
    'ext-peering': 6,
    'ext-portal': 6,
    'ext-powerbidedicated': 6,
    'ext-providerhub': 6,
    'ext-purview': 12,
    'ext-quantum': 7,
    'ext-quota': 9,
    'ext-rdbms-connect': 6,
    'ext-redisenterprise': 9,
    'ext-reservation': 6,
    'ext-resource-graph': 6,
    'ext-resource-mover': 7,
    'ext-scenario-guide': 6,
    'ext-scheduled-query': 11,
    'ext-scvmm': 6,
    'ext-securityinsight': 8,
    'ext-self-help': 6,
    'ext-serial-console': 17,
    'ext-serviceconnector-passwordless': 6,
    'ext-spring': 62,
    'ext-spring-cloud': 6,
    'ext-ssh': 6,
    'ext-stack-hci': 6,
    'ext-staticwebapp': 6,
    'ext-storage-blob-preview': 8,
    'ext-storage-mover': 6,
    'ext-storage-preview': 9,
    'ext-storagesync': 7,
    'ext-stream-analytics': 96,
    'ext-subscription': 6,
    'ext-support': 8,
    'ext-swiftlet': 8,
    'ext-timeseriesinsights': 9,
    'ext-traffic-collector': 19,
    'ext-virtual-network-tap': 6,
    'ext-virtual-wan': 150,
    'ext-vm-repair': 57,
    'ext-vmware': 6,
    'ext-voice-service': 6,
    'ext-webapp': 6,
    'ext-webpubsub': 9,
}


def run_command(cmd, check_return_code=False):
    error_flag = False
    logger.info(cmd)
    try:
        out = subprocess.run(cmd, check=True)
        if check_return_code and out.returncode:
            raise RuntimeError(f"{cmd} failed")
    except subprocess.CalledProcessError:
        error_flag = True
    return error_flag


def install_extension(extension_module):

    try:
        cmd = ['azdev', 'extension', 'add', extension_module]
        error_flag = run_command(cmd, check_return_code=True)
    except Exception:
        error_flag = True

    return error_flag


def remove_extension(extension_module):
    try:
        cmd = ['azdev', 'extension', 'remove', extension_module]
        error_flag = run_command(cmd, check_return_code=True)
    except Exception:
        error_flag = True

    return error_flag


def is_extension(module):
    return module.startswith('ext-')


def get_extension_name(module):
    return module[4:]


class AutomaticScheduling(object):

    def __init__(self):
        """
        self.jobs: Record the test time of each module
        self.modules: All modules and core, ignore extensions
        self.works: Record which modules each worker needs to test
        self.instance_cnt:
        The total number of concurrent automation full test pipeline instance with specify python version
        Because we share the vm pool with azure-sdk team, so we can't set the number of concurrency arbitrarily
        Best practice is to keep the number of concurrent tasks below 50
        If you set a larger number of concurrency, it will cause many instances to be in the waiting state
        And the network module has the largest number of test cases and can only be tested serially for now, so setting instance_cnt = 8 is sufficient
        self.instance_idx:
        The index of concurrent automation full test pipeline instance with specify python version
        For example:
        instance_cnt = 8, instance_idx = 3: means we have 8 instances totally, and now we are scheduling modules on third instance
        instance_cnt = 1, instance_idx = 1: means we only have 1 instance, so we don't need to schedule modules
        """
        self.jobs = []
        self.modules = {}
        self.works = []
        self.instance_cnt = INSTANCE_CNT
        self.instance_idx = INSTANCE_IDX
        for i in range(self.instance_cnt):
            worker = {}
            self.works.append(worker)
        self.serial_modules = []
        self.get_all_modules()
        self.append_new_modules(jobs)


    def get_all_modules(self):
        result = get_path_table()
        out = subprocess.Popen(['azdev', 'extension', 'list', '-o', 'tsv'], stdout=subprocess.PIPE)
        stdout = out.communicate()[0]
        if not stdout:
            raise RuntimeError("No extension detected")
        extensions = stdout.decode('UTF-8').split('\n')
        exts = {'ext-' + extension.split('\t')[1]: extension.split('\t')[2].strip('\r')
                        for extension in extensions if len(extension.split('\t')) > 2}
        self.modules = {**result['mod'], **exts}
        logger.info(self.modules)


    def append_new_modules(self, jobs):
        # If add a new module, use average test time
        avg_cost = int(sum(jobs.values()) / len(jobs.values()))
        for module in self.modules:
            if module not in jobs.keys():
                jobs[module] = avg_cost
        # sort jobs by time cost (desc)
        self.jobs = sorted(jobs.items(), key=lambda item: -item[1])

    def get_worker(self):
        """
        Use greedy algorithm distribute jobs to each worker
        For each job, we assign it to the worker with the fewest jobs currently
        :return worker number
        """
        for idx, worker in enumerate(self.works):
            tmp_time = sum(worker.values()) if sum(worker.values()) else 0
            if idx == 0:
                worker_time = tmp_time
                worker_num = idx
            if tmp_time < worker_time:
                worker_time = tmp_time
                worker_num = idx
        return worker_num

    def get_instance_modules(self):
        # get modules which need to execute in the pipeline instance with specific index
        for k, v in self.jobs:
            idx = self.get_worker()
            self.works[idx][k] = v
        # instance_idx: 1~n, python list index: 0~n-1
        self.instance_idx -= 1
        return self.works[self.instance_idx]

    def run_instance_modules(self, instance_modules):
        global_error_flag = False
        error_flag = False
        logger.info(instance_modules)
        for module in instance_modules.keys():
            if is_extension(module) and (USER_TARGET.lower() in ['all', 'extension', ''] or module == USER_TARGET):
                ext = get_extension_name(module)
                error_flag = install_extension(ext)
                global_error_flag = global_error_flag or error_flag
                if not error_flag:
                    sequential = ['azdev', 'test', ext, USER_LIVE, '--mark', 'serial', '--xml-path', f'test_results.{ext}.sequential.xml', '--no-exitfirst', '-a',
                                  f'"-n 1 --json-report --json-report-summary --json-report-file={ext}.{PLATFORM}.report.sequential.json --html={ext}.{PLATFORM}.report.sequential.html --self-contained-html --capture=sys"']
                    logger.info(sequential)
                    error_flag = run_command(sequential, check_return_code=True)
                    global_error_flag = global_error_flag or error_flag
                    parallel = ['azdev', 'test', ext, USER_LIVE, '--mark', 'not serial', '--xml-path', f'test_results.{ext}.parallel.xml', '--no-exitfirst', '-a',
                                f'"-n {USER_PARALLELISM} --json-report --json-report-summary --json-report-file={ext}.{PLATFORM}.report.parallel.json --html={ext}.{PLATFORM}.report.parallel.html --self-contained-html --capture=sys"']
                    logger.info(parallel)
                    error_flag = run_command(parallel, check_return_code=True)
                    global_error_flag = global_error_flag or error_flag
                error_flag = remove_extension(ext)
                global_error_flag = global_error_flag or error_flag
            elif not is_extension(module) and (USER_TARGET.lower() in ['all', 'main', ''] or module == USER_TARGET):
                sequential = ['azdev', 'test', module, USER_LIVE, '--mark', 'serial', '--xml-path', f'test_results.{module}.sequential.xml', '--no-exitfirst', '-a',
                              f'"-n 1 --json-report --json-report-summary --json-report-file={module}.{PLATFORM}.report.sequential.json --html={module}.{PLATFORM}.report.sequential.html --self-contained-html --capture=sys"']
                logger.info(sequential)
                error_flag = run_command(sequential, check_return_code=True)
                global_error_flag = global_error_flag or error_flag
                parallel = ['azdev', 'test', module, USER_LIVE, '--mark', 'not serial', '--xml-path', f'test_results.{module}.parallel.xml', '--no-exitfirst', '-a',
                            f'"-n {USER_PARALLELISM} --json-report --json-report-summary --json-report-file={module}.{PLATFORM}.report.parallel.json --html={module}.{PLATFORM}.report.parallel.html --self-contained-html --capture=sys"']
                logger.info(parallel)
                error_flag = run_command(parallel, check_return_code=True)
                global_error_flag = global_error_flag or error_flag
            self.generate_csv_file(module)
            # TODO: add filter for main repo and ext repo
            if USER_TARGET.lower() in ['all', '']:
                # self.generate_csv_file(module)
                self.send_to_kusto(module)
        return global_error_flag or error_flag

    def generate_csv_file(self, module):
        logger.info('Start generate csv file for {TARGET}.'.format(TARGET=module))
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
        logger.info('CSV data: {data}'.format(data=data))

        with open(f'{OUTPUT_DIR}/{module}.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        logger.info('Finish generate csv file for {TARGET}.'.format(TARGET=module))


    def send_to_kusto(self, module):
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

def main():
    logger.info("Start automation full test ...\n")
    autoscheduling = AutomaticScheduling()
    instance_modules = autoscheduling.get_instance_modules()
    sys.exit(1) if autoscheduling.run_instance_modules(instance_modules) else sys.exit(0)


if __name__ == '__main__':
    main()
