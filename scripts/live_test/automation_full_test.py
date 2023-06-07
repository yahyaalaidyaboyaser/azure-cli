#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azdev.utilities import get_path_table
import json
import logging
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

# sys.argv is passed by
# .azure-pipelines/templates/automation_test.yml in section `Running full test`
# scripts/regression_test/regression_test.yml in section "Rerun tests"
instance_cnt = int(sys.argv[1]) if len(sys.argv) >= 2 else 1
instance_idx = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
profile = sys.argv[3] if len(sys.argv) >= 4 else 'latest'
serial_modules = sys.argv[4].split() if len(sys.argv) >= 5 else []
fix_failure_tests = sys.argv[5].lower() == 'true' if len(sys.argv) >= 6 else False
target = sys.argv[6].lower() if len(sys.argv) >= 7 else 'cli'
working_directory = os.getenv('BUILD_SOURCESDIRECTORY') if target == 'cli' else f"{os.getenv('BUILD_SOURCESDIRECTORY')}/azure-cli-extensions"
azdev_test_result_dir = os.path.expanduser("~/.azdev/env_config/mnt/vss/_work/1/s/env")
python_version = os.environ.get('PYTHON_VERSION', None)
job_name = os.environ.get('JOB_NAME', None)
pull_request_number = os.environ.get('PULL_REQUEST_NUMBER', None)
enable_pipeline_result = bool(job_name and python_version)
unique_job_name = ' '.join([job_name, python_version, profile, str(instance_idx)]) if enable_pipeline_result else None
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


def git_restore(file_path):
    if not file_path:
        return
    logger.info(f"git restore *{file_path}")
    out = subprocess.Popen(["git", "restore", "*" + file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, err = out.communicate()
    if stdout:
        logger.info(stdout)
    if err:
        logger.warning(err)


def git_push(message, modules=[]):
    out = subprocess.Popen(["git", "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = out.communicate()
    if "nothing to commit, working tree clean" in str(stdout):
        return
    try:
        if modules:
            build_id = os.getenv("BUILD_BUILDID")
            module_name = '_'.join(modules)
            branch_name = f"regression_test_{build_id}_{module_name}"
            run_command(["git", "checkout", "-b", branch_name])
            run_command(["git", "push", "--set-upstream", "azclibot", branch_name], check_return_code=True)
        run_command(["git", "add", "src/*"], check_return_code=True)
        run_command(["git", "commit", "-m", message], check_return_code=True)
    except RuntimeError as ex:
        raise ex
    retry = 3
    while retry >= 0:
        try:
            run_command(["git", "fetch"], check_return_code=True)
            run_command(["git", "pull", "--rebase"], check_return_code=True)
            run_command(["git", "push"], check_return_code=True)

            logger.info("git push all recording files")
            break
        except RuntimeError as ex:
            if retry == 0:
                raise ex
            retry -= 1
            time.sleep(10)


def get_failed_tests(test_result_fp):
    tree = ET.parse(test_result_fp)
    root = tree.getroot()
    failed_tests = {}
    for testsuite in root:
        for testcase in testsuite:
            # Collect failed tests
            failures = testcase.findall('failure')
            if failures:
                logger.info(f"failed testcase attributes: {testcase.attrib}")
                test_case = testcase.attrib['name']
                test_case_class = testcase.attrib['classname'] + '.' + test_case
                recording_folder = os.path.join(os.path.dirname(testcase.attrib['file']), 'recordings')
                failed_tests[test_case_class] = os.path.join(recording_folder, test_case + '.yaml')
    return failed_tests


def process_test(cmd, azdev_test_result_fp, live_rerun=False, modules=[]):
    error_flag = run_command(cmd)
    if not error_flag or not live_rerun:
        return error_flag
    if not os.path.exists(azdev_test_result_fp):
        logger.warning(f"{cmd} failed directly. The related module can't work!")
        if modules:
            test_results_error_modules_fp = os.path.join(azdev_test_result_dir, f'test_results_error_modules_{instance_idx}.txt')
            with open(test_results_error_modules_fp, 'a') as fp:
                fp.write(','.join(modules)+"\n")
        return error_flag
    # drop the original `--pytest-args` and add new arguments
    cmd = cmd[:-2] + ['--lf', '--live', '--pytest-args', '-o junit_family=xunit1']
    error_flag = run_command(cmd)
    # restore original recording yaml file for failed test in live run
    if error_flag:
        failed_tests = get_failed_tests(azdev_test_result_fp)
        for (test, file) in failed_tests.items():
            git_restore(file)
            test_results_failure_tests_fp = os.path.join(azdev_test_result_dir, f'test_results_failure_tests_{instance_idx}.txt')
            with open(test_results_failure_tests_fp, 'a') as fp:
                fp.write(test + "\n")

    # save live run recording changes to git
    commit_message = f"Rerun tests from instance {instance_idx}. See {os.path.basename(azdev_test_result_fp)} for details"
    git_push(commit_message, modules=modules)
    return False


class AutomaticScheduling(object):

    def __init__(self):
        """
        self.jobs: Record the test time of each module
        self.modules: All modules and core, ignore extensions
        self.serial_modules: All modules which need to execute in serial mode
        self.works: Record which modules each worker needs to test
        self.instance_cnt:
        The total number of concurrent automation full test pipeline instance with specify python version
        Because we share the vm pool with azure-sdk team, so we can't set the number of concurrency arbitrarily
        Best practice is to keep the number of concurrent tasks below 50
        If you set a larger number of concurrency, it will cause many instances to be in the waiting state
        And the network module has the largest number of test cases and can only be tested serially for now, so setting instance_cnt = 8 is sufficient
        Total concurrent number: AutomationTest20200901 * 3 + AutomationTest20190301 * 3 + AutomationTest20180301 * 3 + AutomationFullTest * 8 * 3 (python_version) = 33
        self.instance_idx:
        The index of concurrent automation full test pipeline instance with specify python version
        For example:
        instance_cnt = 8, instance_idx = 3: means we have 8 instances totally, and now we are scheduling modules on third instance
        instance_cnt = 1, instance_idx = 1: means we only have 1 instance, so we don't need to schedule modules
        """
        self.jobs = []
        self.modules = {}
        self.serial_modules = serial_modules
        self.works = []
        self.instance_cnt = instance_cnt
        self.instance_idx = instance_idx
        for i in range(self.instance_cnt):
            worker = {}
            self.works.append(worker)
        self.profile = profile

    def get_all_modules(self):
        result = get_path_table()
        # only get modules and core, ignore extensions
        self.modules = {**result['mod'], **result['ext']}
        logger.warning(self.modules)

    # def get_extension_modules(self):
    #     out = subprocess.Popen(['azdev', 'extension', 'list', '-o', 'tsv'], stdout=subprocess.PIPE)
    #     stdout = out.communicate()[0]
    #     if not stdout:
    #         raise RuntimeError("No extension detected")
    #     extensions = stdout.decode('UTF-8').split('\n')
    #     self.modules = {extension.split('\t')[1]: extension.split('\t')[2].strip('\r')
    #                     for extension in extensions if len(extension.split('\t')) > 2}
    #     logger.info(self.modules)

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
        # divide the modules that the current instance needs to execute into parallel or serial execution
        serial_error_flag = parallel_error_flag = False
        serial_tests = []
        parallel_tests = []
        for k, v in instance_modules.items():
            if k in self.serial_modules:
                serial_tests.append(k)
            else:
                parallel_tests.append(k)
        if serial_tests:
            azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{python_version}_{profile}_{instance_idx}.serial.xml")
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose', '--series'] + serial_tests + \
                  ['--profile', f'{profile}', '--xml-path', azdev_test_result_fp, '--pytest-args', '-o junit_family=xunit1 --durations=10 --tb=no']
            print(cmd)
            # serial_error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests)
        if parallel_tests:
            azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{python_version}_{profile}_{instance_idx}.parallel.xml")
            cmd = ['azdev', 'test', '--no-exitfirst', '--verbose'] + parallel_tests + \
                  ['--profile', f'{profile}', '--xml-path', azdev_test_result_fp, '--pytest-args', '-o junit_family=xunit1 --durations=10 --tb=no']
            print(cmd)
            # parallel_error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests)
        return serial_error_flag or parallel_error_flag

    def run_extension_instance_modules(self, instance_modules):
        global_error_flag = False
        for module, path in instance_modules.items():
            run_command(["git", "checkout", f"regression_test_{os.getenv('BUILD_BUILDID')}"], check_return_code=True)
            error_flag = install_extension(module)
            if not error_flag:
                azdev_test_result_fp = os.path.join(azdev_test_result_dir, f"test_results_{module}.xml")
                cmd = ['azdev', 'test', module, '--discover', '--no-exitfirst', '--verbose',
                       '--xml-path', azdev_test_result_fp, '--pytest-args', '"--durations=10"']
                error_flag = process_test(cmd, azdev_test_result_fp, live_rerun=fix_failure_tests, modules=[module])
            remove_extension(module)
            global_error_flag = global_error_flag or error_flag
        return global_error_flag


def main():
    logger.info("Start automation full test ...\n")
    autoscheduling = AutomaticScheduling()
    autoscheduling.get_all_modules()
    autoscheduling.append_new_modules(jobs)
    instance_modules = autoscheduling.get_instance_modules()
    sys.exit(1) if autoscheduling.run_instance_modules(instance_modules) else sys.exit(0)


if __name__ == '__main__':
    main()
