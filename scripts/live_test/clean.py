# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# Clean Azure resources automatically
# version 1.0
from bs4 import BeautifulSoup
import datetime
import json
import os
import subprocess
import sys
import time
from tqdm import tqdm


BUILD_ID = sys.argv[1]
ACCOUNT_KEY = sys.argv[2]


resource_html = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Remaining resources.html</title>
    <style>body {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 12px;
  /* do not increase min-width as some may use split screens */
  min-width: 800px;
  color: #999;
}

h1 {
  font-size: 24px;
  color: black;
}

table {
  border-collapse: collapse;
}

/******************************
 * RESULTS TABLE
 *
 * 1. Table Layout
 * 2. Sorting items
 *
 ******************************/
/*------------------
 * 1. Table Layout
 *------------------*/
#results-table {
  border: 1px solid #e6e6e6;
  color: #999;
  font-size: 12px;
  width: 100%;
}
#results-table th,
#results-table td {
  padding: 5px;
  border: 1px solid #E6E6E6;
  text-align: left;
}
#results-table th {
  font-weight: bold;
}

/*------------------
 * 2. Sorting items
 *------------------*/
.sortable {
  cursor: pointer;
}

.sort-icon {
  font-size: 0px;
  float: left;
  margin-right: 5px;
  margin-top: 5px;
  /*triangle*/
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
}
.inactive .sort-icon {
  /*finish triangle*/
  border-top: 8px solid #E6E6E6;
}
.asc.active .sort-icon {
  /*finish triangle*/
  border-bottom: 8px solid #999;
}
.desc.active .sort-icon {
  /*finish triangle*/
  border-top: 8px solid #999;
}
</style></head>
  <body onLoad="init()">
    <script>/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */


function toArray(iter) {
    if (iter === null) {
        return null;
    }
    return Array.prototype.slice.call(iter);
}

function find(selector, elem) { // eslint-disable-line no-redeclare
    if (!elem) {
        elem = document;
    }
    return elem.querySelector(selector);
}

function findAll(selector, elem) {
    if (!elem) {
        elem = document;
    }
    return toArray(elem.querySelectorAll(selector));
}

function sortColumn(elem) {
    toggleSortStates(elem);
    const colIndex = toArray(elem.parentNode.childNodes).indexOf(elem);
    let key;
    key = keyAlpha;
    sortTable(elem, key(colIndex));
}

function showFilters() {
    let visibleString = getQueryParameter('visible') || 'all';
    visibleString = visibleString.toLowerCase();
    const checkedItems = visibleString.split(',');

    const filterItems = document.getElementsByClassName('filter');
    for (let i = 0; i < filterItems.length; i++) {
        filterItems[i].hidden = false;

        if (visibleString != 'all') {
            filterItems[i].checked = checkedItems.includes(filterItems[i].getAttribute('data-test-result'));
        }
    }
}

function getQueryParameter(name) {
    const match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
}

function init () { // eslint-disable-line no-unused-vars
    resetSortHeaders();

    showFilters();

    sortColumn(find('.initial-sort'));

    findAll('.sortable').forEach(function(elem) {
        elem.addEventListener('click',
            function() {
                sortColumn(elem);
            }, false);
    });
}

function sortTable(clicked, keyFunc) {
    const rows = findAll('.results-table-row');
    const reversed = !clicked.classList.contains('asc');
    const sortedRows = sort(rows, keyFunc, reversed);
    /* Whole table is removed here because browsers acts much slower
     * when appending existing elements.
     */
    const thead = document.getElementById('results-table-head');
    document.getElementById('results-table').remove();
    const parent = document.createElement('table');
    parent.id = 'results-table';
    parent.appendChild(thead);
    sortedRows.forEach(function(elem) {
        parent.appendChild(elem);
    });
    document.getElementsByTagName('BODY')[0].appendChild(parent);
}

function sort(items, keyFunc, reversed) {
    const sortArray = items.map(function(item, i) {
        return [keyFunc(item), i];
    });

    sortArray.sort(function(a, b) {
        const keyA = a[0];
        const keyB = b[0];

        if (keyA == keyB) return 0;

        if (reversed) {
            return keyA < keyB ? 1 : -1;
        } else {
            return keyA > keyB ? 1 : -1;
        }
    });

    return sortArray.map(function(item) {
        const index = item[1];
        return items[index];
    });
}

function keyAlpha(colIndex) {
    return function(elem) {
        return elem.childNodes[1].childNodes[colIndex].firstChild.data.toLowerCase();
    };
}

function resetSortHeaders() {
    findAll('.sort-icon').forEach(function(elem) {
        elem.parentNode.removeChild(elem);
    });
    findAll('.sortable').forEach(function(elem) {
        const icon = document.createElement('div');
        icon.className = 'sort-icon';
        icon.textContent = 'vvv';
        elem.insertBefore(icon, elem.firstChild);
        elem.classList.remove('desc', 'active');
        elem.classList.add('asc', 'inactive');
    });
}

function toggleSortStates(elem) {
    //if active, toggle between asc and desc
    if (elem.classList.contains('active')) {
        elem.classList.toggle('asc');
        elem.classList.toggle('desc');
    }

    //if inactive, reset all other functions and add ascending active
    if (elem.classList.contains('inactive')) {
        resetSortHeaders();
        elem.classList.remove('inactive');
        elem.classList.add('active');
    }
}

</script>
    <h1>Resources to clean up</h1>
    <table id="results-table">
      <thead id="results-table-head">
        <tr>
          <th class="sortable initial-sort" col="module">Module</th>
          <th class="sortable" col="test-case">Test Case</th>
          <th class="sortable" col="date">Date</th>
          <th class="sortable" col="resource-group">Resource Group</th>
        </tr>
    </table>
  </body>
</html>
"""


def main():
    print('Azure cli resource clean up: version 1.0')
    clean_lock()
    clean_sig()
    clean_storage()
    clean_servicebus()
    clean_backup()
    clean_deleted_keyvault()
    clean_resource_group()
    get_remaining_tests()


def clean_lock():
    print('Clean lock')
    cmd = ['az', 'lock', 'list', '--query', '[][id, name, resourceGroup]']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    locks = json.loads(out.stdout)
    print(locks)
    cmd = ['az', 'group', 'list', '--tag', 'product=azurecli', '--query', '[].name']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    cli_test_resoure_groups = json.loads(out.stdout)
    print(cli_test_resoure_groups)
    for resource_id, lock_name, rg in tqdm(locks):
        if rg in cli_test_resoure_groups:
            cmd = f'az lock delete --name {lock_name} --resource-group {rg}'
            print(cmd)
            result = os.popen(cmd).read()
            print(result)
    cmd = ['az', 'lock', 'list', '--query', '[][id, name, resourceGroup]']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    locks = json.loads(out.stdout)
    print(locks)
    for resource_id, lock_name, rg in tqdm(locks):
        if rg in cli_test_resoure_groups:
            resource_id = resource_id.split('providers')[1].split('/')
            resource_name = resource_id[3]
            resource_type = "/".join(resource_id[1:3])
            cmd = f'az lock delete --name {lock_name} --resource-group {rg} --resource {resource_name} --resource-type {resource_type}'
            print(cmd)
            result = os.popen(cmd).read()
            print(result)


def clean_sig():
    print('Clean sig')
    # Gallery application still has gallery application versions.
    skip_grous = ['GALLERYAPP-TEST', 'CLITEST.RGZBEBLKTTJHO7IVJUGYWRRDO434XMUXDOAVDDSBGIMM67257RGJ55TQCILNERPAQWU']
    cmd = f'az sig list --query [].id'
    print(cmd)
    sig_list = json.loads(os.popen(cmd).read())
    print(sig_list)
    for sig_id in tqdm(sig_list):
        rg = sig_id.split('/')[4]
        if rg in skip_grous:
            continue
        gallery_name = sig_id.split('/')[8]
        cmd = ['az', 'lock', 'list', '-g', rg]
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        # skip the resource group when get a lock
        # b'[]\r\n'
        locks = json.loads(out.stdout)
        print(locks)
        if locks:
            continue
        cmd = f'az sig share reset --ids {sig_id}'
        result = os.popen(cmd).read()
        print(result)
        cmd = ['az', 'sig', 'gallery-application', 'create', '--gallery-name', gallery_name, '--name', 'AppName', '-g',
               rg, '--os-type', 'windows']
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        print(json.loads(out.stdout))
        cmd = ['az', 'sig', 'gallery-application', 'list', '--gallery-name', gallery_name, '-g', rg, '--query',
               '[].name']
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        app_names = json.loads(out.stdout)
        print(app_names)
        for name in app_names:
            if name != 'AppName':
                cmd = ['az', 'sig', 'gallery-application', 'create', '--gallery-name', gallery_name, '--name', name,
                       '-g', rg, '--os-type', 'windows']
                print(cmd)
                out = subprocess.run(cmd, capture_output=True)
                print(json.loads(out.stdout))
        for name in app_names:
            cmd = ['az', 'sig', 'gallery-application', 'delete', '--gallery-name', gallery_name, '--name', name, '-g',
                   rg, '--yes']
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            if out.returncode != 0:
                print(out.stderr)
    for sig_id in tqdm(sig_list):
        rg = sig_id.split('/')[4]
        if rg in skip_grous:
            continue
        cmd = ['az', 'lock', 'list', '-g', rg]
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        # skip the resource group when get a lock
        # b'[]\r\n'
        locks = json.loads(out.stdout)
        print(locks)
        if locks:
            continue
        cmd = f'az group delete -n {rg} --yes'
        result = os.popen(cmd).read()
        print(result)


def clean_storage():
    print('Clean storage')
    skip_grous = []
    cmd = ['az', 'storage', 'account', 'list', '--query', '[][name, resourceGroup]']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    accounts = json.loads(out.stdout)
    print(accounts)
    for account, rg in tqdm(accounts):
        delete_group = True
        if rg in skip_grous:
            continue
        cmd = ['az', 'lock', 'list', '-g', rg]
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        # skip the resource group when get a lock
        # b'[]\r\n'
        locks = json.loads(out.stdout)
        print(locks)
        if locks:
            continue
        cmd = ['az', 'storage', 'account', 'keys', 'list', '--account-name', account, '--query', '[].value']
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        keys = json.loads(out.stdout) if out.stdout else []
        if not keys:
            continue
        account_key = keys[0]
        cmd = ['az', 'storage', 'container', 'list', '--account-name', account, '--account-key', account_key, '--query',
               '[].name']
        out = subprocess.run(cmd, capture_output=True)
        containers = json.loads(out.stdout)
        print(containers)
        if not containers:
            continue
        for container in containers:
            cmd = f'az storage blob delete-batch --account-name {account} --account-key {account_key} --source {container}'
            result = os.popen(cmd).read()
            print(result)
            cmd = ['az', 'storage', 'container-rm', 'delete', '--storage-account', account, '--name', container, '--yes']
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            if out.returncode != 0:
                print(out.stderr)
                delete_group = False
                break
        if delete_group:
            cmd = f'az group delete -n {rg} --yes'
            print(cmd)
            result = os.popen(cmd).read()
            print(result)


def clean_servicebus():
    print('Clean servicebus')
    skip_grous = []
    cmd = ['az', 'group', 'list', '--query', '[].name']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    resource_groups = json.loads(out.stdout)
    print(resource_groups)
    for resource_group in tqdm(resource_groups):
        if resource_group in skip_grous:
            continue
        if resource_group.startswith('cli_test_sb_migration'):
            cmd = ['az', 'servicebus', 'namespace', 'list', '--resource-group', resource_group, '--query',
                   '[][name, resourceGroup, sku.name]']
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            servicebus_list = json.loads(out.stdout)
            print(servicebus_list)
            for name, rg, sku in tqdm(servicebus_list):
                if sku == 'Standard':
                    cmd = ['az', 'servicebus', 'migration', 'abort', '--resource-group', rg, '--name', name]
                    print(cmd)
                    out = subprocess.run(cmd, capture_output=True)
                    result = out.stdout
                    print(result)
                    time.sleep(180)
                    cmd = f'az group delete -n {rg} --yes'
                    print(cmd)
                    result = os.popen(cmd).read()
                    print(result)


def clean_backup():
    print('Clean backup')
    skip_grous = ['myResourceGroup', 'clitest.rgvt3xx3e4uwhbuq3pmtkf72fl674usgxlhezwreh6vdf4jbsvnf4pwohlb7hyyj6qy']
    cmd = ['az', 'backup', 'vault', 'list', '--query', '[][name, resourceGroup]']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    backup_vaults = json.loads(out.stdout)
    print(backup_vaults)
    for vault, resource_group in tqdm(backup_vaults):
        cmd = ['az', 'lock', 'list', '-g', resource_group]
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        # skip the resource group when get a lock
        # b'[]\r\n'
        locks = json.loads(out.stdout)
        print(locks)
        if locks:
            continue
        if resource_group in skip_grous:
            continue
        cmd = ['az', 'backup', 'item', 'list', '-v', vault, '--resource-group', resource_group, '--query',
               '[][properties.friendlyName, properties.backupManagementType, containerName]']
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        items = json.loads(out.stdout)
        print(items)
        for item, item_type, container in items:
            if container:
                container = container.split(';')[-1]
            else:
                container = item
            cmd = ['az', 'backup', 'protection', 'disable', '--container-name', container, '--backup-management-type',
                   item_type, '--delete-backup-data', 'true', '--item-name', item, '--resource-group', resource_group,
                   '--vault-name', vault, '--yes']
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            print(out.stdout)
            cmd = ['az', 'backup', 'container', 'show', '--name', container, '--resource-group',
                   resource_group, '--vault-name', vault, '--backup-management-type', item_type]
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            print(out.stdout)
            cmd = ['az', 'backup', 'container', 'unregister', '--container-name', container,
                   '--resource-group', resource_group, '--vault-name', vault, '--backup-management-type', item_type,
                   '--yes']
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            print(out.stdout)
        cmd = ['az', 'backup', 'policy', 'list', '--resource-group', resource_group, '--vault-name', vault, '--query',
               '[].id']
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        policy_ids = json.loads(out.stdout)
        if policy_ids:
            cmd = ['az', 'backup', 'policy', 'delete', '--ids']
            cmd.extend(policy_ids)
            print(cmd)
            out = subprocess.run(cmd, capture_output=True)
            print(out.stdout)
        cmd = f'az group delete -n {resource_group} --yes'
        print(cmd)
        result = os.popen(cmd).read()
        print(result)


def clean_deleted_keyvault():
    cmd = ['az', 'keyvault', 'list-deleted', '--query', '[][name, properties.scheduledPurgeDate, type]']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    deleted_keyvaults = json.loads(out.stdout)
    count = 0
    for name, scheduledPurgeDate, keyvault_type in tqdm(deleted_keyvaults):
        if scheduledPurgeDate <= datetime.datetime.now().isoformat():
            if keyvault_type == 'Microsoft.KeyVault/deletedVaults':
                cmd = ['az', 'keyvault', 'purge', '--name', name, '--no-wait']
            elif keyvault_type == 'Microsoft.KeyVault/deletedManagedHSMs':
                cmd = ['az', 'keyvault', 'purge', '--hsm-name', name, '--no-wait']
            else:
                continue
            print(cmd)
            count += 1
            out = subprocess.run(cmd, capture_output=True)
            print(out.stdout)
    print(count)


def clean_resource_group():
    skip_grous = []
    cmd = ['az', 'group', 'list', '--query', '[].name']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    rgs = json.loads(out.stdout) if out.stdout else []
    for rg in rgs:
        if rg in skip_grous:
            continue
        cmd = ['az', 'lock', 'list', '-g', rg]
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        # skip the resource group when get a lock
        # b'[]\r\n'
        locks = json.loads(out.stdout)
        print(locks)
        if locks:
            continue
        cmd = ['az', 'group', 'delete', '-n', rg, '--yes']
        print(cmd)
        out = subprocess.run(cmd, capture_output=True)
        print(out.stdout)


def get_remaining_tests():
    cmd = ['az', 'group', 'list', '--tag', 'module', '--query', '[][name, tags]']
    print(cmd)
    out = subprocess.run(cmd, capture_output=True)
    remaing_tests = json.loads(out.stdout) if out.stdout else []
    if remaing_tests:
        # sorted remaing tests by module name and test name
        sorted_tests = sorted(remaing_tests, key=lambda x: (x[1]['module'], x[1]['test']))
        soup = BeautifulSoup(resource_html, 'html.parser')
        for test in sorted_tests:
            module = test[1]['module']
            test_name = test[1]['test']
            date = test[1]['date']
            group = test[0]
            tbody = soup.new_tag('tbody', **{'class': 'results-table-row'})
            tr = soup.new_tag('tr')
            td_module = soup.new_tag('td', **{'class': 'col-module'})
            td_module.string = module
            tr.append(td_module)
            td_test = soup.new_tag('td', **{'class': 'col-test-case'})
            td_test.string = test_name
            tr.append(td_test)
            td_date = soup.new_tag('td', **{'class': 'col-date'})
            td_date.string = date
            tr.append(td_date)
            td_group = soup.new_tag('td', **{'class': 'col-resource-group'})
            td_group.string = group
            tr.append(td_group)
            tbody.append(tr)
            soup.table.append(tbody)
        with open('./resource.html', 'w') as f:
            f.write(str(soup))
        cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac --account-key {}'.format('./', BUILD_ID, 'resource.html', ACCOUNT_KEY)
        os.system(cmd)


if __name__ == '__main__':
    main()
