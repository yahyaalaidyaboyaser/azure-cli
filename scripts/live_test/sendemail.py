# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from bs4 import BeautifulSoup
import generate_index
import logging
import os
import sys
import test_data
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

SENDGRID_KEY = sys.argv[1]
BUILD_ID = sys.argv[2]
USER_REPO = sys.argv[3]
USER_BRANCH = sys.argv[4]
USER_TARGET = sys.argv[5]
USER_LIVE = sys.argv[6]
ARTIFACT_DIR = sys.argv[7]
REQUESTED_FOR_EMAIL = sys.argv[8]
ACCOUNT_KEY = sys.argv[9]
COMMIT_ID = sys.argv[10]


def main():
    logger.warning('Enter main()')

    logger.warning(BUILD_ID)
    logger.warning(USER_REPO)
    logger.warning(USER_BRANCH)
    logger.warning(USER_TARGET)
    logger.warning(USER_LIVE)
    logger.warning(ARTIFACT_DIR)
    logger.warning(REQUESTED_FOR_EMAIL)
    logger.warning(COMMIT_ID)

    # Upload results to storage account, container
    container = ''
    try:
        logger.warning('Uploading test results to storage account...')
        container = get_container_name()
        upload_files(container)
    except Exception:
        logger.exception(traceback.format_exc())

    # Collect statistics
    testdata = test_data.TestData(ARTIFACT_DIR)
    testdata.collect()

    # Summary data by module
    summary_data_by_module(container, ARTIFACT_DIR, ACCOUNT_KEY, testdata)

    # Generate index.html, send email
    try:
        # Generate index.html
        container_url = 'https://clitestresultstac.blob.core.windows.net/' + container
        html_content = generate_index.generate(container, container_url, testdata, USER_REPO, USER_BRANCH, COMMIT_ID, USER_LIVE, USER_TARGET, ACCOUNT_KEY)
        # Send email
        send_email(html_content)
    except Exception:
        logger.exception(traceback.format_exc())

    # Write database
    # try:
    #     write_db(container, testdata)
    # except Exception:
    #     logger.exception(traceback.format_exc())

    logger.warning('Exit main()')


def summary_data_by_module(container, ARTIFACT_DIR, ACCOUNT_KEY):
    modules = set([module[0].split('.')[0] for module in testdata.modules])
    total_test = testdata.total[1] + testdata.total[2]
    # duration = 27.01
    passed = testdata.total[1]
    # skiped = -1
    failed = testdata.total[2]
    for module in modules:
        for root, dirs, files in os.walk(ARTIFACT_DIR):
            First = True
            fullpath = ''
            for file in files:
                if file.startswith(module) and file.endswith('html') and First:
                    First = False
                    html_name = '.'.join([module, 'html'])
                    json_name = '.'.join([module, 'json'])
                    platform = file.split('.')[1]
                    first = os.path.join(root, file)
                    dst_html = os.path.join(root, html_name)
                    dst_json = os.path.join(root, json_name)
                    with open(first, 'r') as f:
                        src_html = f.read()
                        src_soup = BeautifulSoup(src_html, 'html.parser')
                        th = src_soup.find('thead', id='results-table-head')
                        tr = th.find('tr')
                        new_th = src_soup.new_tag('th', **{'class': 'sortable', 'col': 'platform'})
                        new_th.string = 'Platform'
                        tr.insert(2, new_th)
                        tbodys = src_soup.findAll('tbody')
                        for tbody in tbodys:
                            tr = tbody.find('tr')
                            new_col = src_soup.new_tag('td', **{'class': 'col-platform'})
                            new_col.string = platform
                            tr.insert(2, new_col)
                        src_soup.find('title').string = f'{module}.html'
                        src_soup.find('h1').string = f'{module}.html'
                        env = src_soup.find('table', id='environment')
                        if env:
                            env_trs = env.findAll('tr')
                            for tr in env_trs:
                                if 'Platform' in tr.text:
                                    tr.decompose()
                        inputs = src_soup.findAll('input')
                        for i in inputs:
                            if 'disabled' in i.attrs:
                                del i['disabled']
                        src_soup.find('span', {'class': 'passed'}).string = f'{passed} passed'
                        # src_soup.find('span', {'class': 'skipped'}).string = f'{skiped} skipped'
                        src_soup.find('span', {'class': 'failed'}).string = f'{failed} failed'

                elif file.endswith('html'):
                    platform = file.split('.')[1]
                    other = os.path.join(root, file)
                    with open(other, 'r') as f:
                        other_html = f.read()
                        other_soup = BeautifulSoup(other_html, 'html.parser')
                        tbodys = other_soup.findAll('tbody')
                        for tbody in tbodys:
                            tr = tbody.find('tr')
                            new_col = src_soup.new_tag('td', **{'class': 'col-platform'})
                            new_col.string = platform
                            tr.insert(2, new_col)
                    table = src_soup.find('table', id='results-table')
                    for tbody in tbodys:
                        table.append(tbody)
                    duration_pattern = re.compile('.*tests ran in ')
                    p1 = src_soup.find('p', string=re.compile('.*tests ran in.*'))
                    duration = p1.string.split(' ')[-3]
                    p2 = other_soup.find('p', string=re.compile('.*tests ran in.*'))
                    duration2 = p2.string.split(' ')[-3]
                    duration = float(duration) + float(duration2)
                    p1.string = f'{total_test} tests ran in {duration} seconds. '

            with open(dst_html, 'w') as f:
                f.write(str(src_soup))

    # delete other html and json files
    files = os.listdir(ARTIFACT_DIR)
    for file in files:
        if len(file.split('.')) > 2:
            os.remove(file)


def get_container_name():
    """
    Generate container name in storage account. It is also an identifier of the pipeline run.
    :return:
    """
    logger.warning('Enter get_container_name()')
    if USER_TARGET:
        name = USER_TARGET + '-' + BUILD_ID
    else:
        name = 'all-' + BUILD_ID
    logger.warning('Exit get_container_name()')
    return name


def upload_files(container):
    """
    Upload html and json files to container
    :param container:
    :return:
    """
    logger.warning('Enter upload_files()')

    # Create container
    cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {} --public-access container'.format(container, ACCOUNT_KEY)
    os.system(cmd)

    # Upload files
    for root, dirs, files in os.walk(ARTIFACT_DIR):
        for name in files:
            if name.endswith('html') or name.endswith('json'):
                fullpath = os.path.join(root, name)
                cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac --account-key {}'.format(fullpath, container, name, ACCOUNT_KEY)
                os.system(cmd)

    logger.warning('Exit upload_files()')


def send_email(html_content):
    logger.warning('Sending email...')
    from azure.communication.email import EmailClient

    client = EmailClient.from_connection_string(SENDGRID_KEY);
    content = {
        "subject": "Test results of Azure CLI",
        "html": html_content,
    }

    recipients = ''

    if REQUESTED_FOR_EMAIL != '':
        recipients = {
            "to": [
                {
                    "address": REQUESTED_FOR_EMAIL
                },
            ]
        }
    # TODO: USER_TARGET == 'all'
    elif USER_TARGET == '' and USER_REPO == 'https://github.com/Azure/azure-cli.git' and USER_BRANCH == 'dev' and USER_LIVE == '--live' and REQUESTED_FOR_EMAIL == '':
        recipients = {
            "to": [
                {
                    "address": "AzPyCLI@microsoft.com"
                },
                {
                    "address": "antcliTest@microsoft.com"
                }
            ]
        }

    if recipients:
        message = {
            "content": content,
            "senderAddress": "DoNotReply@561634e2-1674-4377-9975-10a9197437d7.azurecomm.net",
            "recipients": recipients
        }

        client.begin_send(message)
        logger.warning('Finish sending email')
    else:
        logger.warning('No recipients, skip sending email')


if __name__ == '__main__':
    main()
