#!/usr/bin/env python
'''
Create template lochness directory
'''
import lochness
from lochness.keyring import pretty_print_dict
from pathlib import Path
import argparse as ap
import sys
import re
from typing import List
import pandas as pd
import json
import importlib
from phoenix_generator import main as pg


lochness_root = Path(lochness.__file__).parent.parent
lochness_test_dir = lochness_root / 'test'


class ArgsForPheonix(object):
    def __init__(self, study, dir):
        self.study = study
        self.dir = dir
        self.verbose = False


def create_lochness_template(args):
    '''Create template for lochness'''
    # make sources small
    args.sources = [x.lower() for x in args.sources]
    args.outdir = Path(args.outdir).absolute()

    # make lochness root directory
    Path(args.outdir).mkdir(exist_ok=True)

    # PHOENIX root
    phoenix_root = Path(args.outdir) / 'PHOENIX'

    # create PHOENIX directory
    for study in args.studies:
        argsForPheonix = ArgsForPheonix(study, phoenix_root)
        try:
            pg(argsForPheonix)
        except SystemExit:
            pass
        metadata = phoenix_root / 'GENERAL' / study / f'{study}_metadata.csv'

        # create example metadata
        create_example_meta_file_advanced(metadata, study, args.sources)

    # create det_csv
    if not Path(args.det_csv).is_file():
        args.det_csv = args.outdir / 'data_entry_trigger_database.csv'


    # create pii table
    if not Path(args.pii_csv).is_file():
        args.pii_csv = args.outdir / 'pii_convert.csv'
        df = pd.DataFrame({
            'pii_label_string': [
                'address', 'phone_number', 'date',
                'patient_name', 'subject_name'],
            'process': [
                'remove', 'random_number', 'change_date',
                'random_string', 'replace_with_subject_id']
            })
        df.to_csv(args.pii_csv)

    # link lochness_sycn_history timestamp db
    if not Path(args.lochness_sync_history_csv).is_file():
        args.lochness_sync_history_csv = args.outdir / \
                'lochness_sync_history.csv'

    # create config
    config_loc = args.outdir / 'config.yml'
    create_config_template(config_loc, args)

    # create keyring
    keyring_loc = args.outdir / 'lochness.json'
    encrypt_keyring_loc = args.outdir / '.lochness.enc'
    create_keyring_template(keyring_loc, args)

    # write commands for the user to run after editing config and keyring
    write_commands_needed(args, config_loc, keyring_loc, encrypt_keyring_loc)


def write_commands_needed(args: 'argparse',
                          config_loc: Path,
                          keyring_loc: Path,
                          encrypt_keyring_loc: Path) -> None:
    '''Write commands'''
    # encrypt_command.sh
    with open(args.outdir / '1_encrypt_command.sh', 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('# run this command to encrypt the edited keyring '
                '(lochness.json)\n')
        f.write('# eg) bash 1_encrypt_command.sh\n')
        command = f'crypt.py --encrypt {keyring_loc} ' \
                  f'-o {encrypt_keyring_loc}\n'
        f.write(command)

    # sync_command.sh
    with open(args.outdir / '2_sync_command.sh', 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('# run this command to run sync.py\n')
        f.write('# eg) bash 2_sync_command.sh\n')

        print(dir(args))
        if args.lochness_sync_send:
            if args.s3:
                command = f"sync.py -c {config_loc} \
                       --source {' '.join(args.sources)} \
                       --lochness_sync_send --s3 \
                       --debug --continuous\n"
            elif args.rsync:
                command = f"sync.py -c {config_loc} \
                        --source {' '.join(args.sources)} \
                        --lochness_sync_send --rsync \
                        --debug --continuous\n"
            else:
                command = f"sync.py -c {config_loc} \
                        --source {' '.join(args.sources)} \
                        --lochness_sync_send --s3 \
                        --debug --continuous\n"
        
        command = re.sub('\s\s+', ' \\\n\t', command)
        f.write(command)


def create_keyring_template(keyring_loc: Path, args: object) -> None:
    '''Create keyring template'''

    template_dict = {}
    template_dict['lochness'] = {}

    if 'redcap' in args.sources:
        template_dict['lochness']['REDCAP'] = {}
        template_dict['lochness']['SECRETS'] = {}
        for study in args.studies:
            study_dict = {f'redcap.{study}': [study]}
            study_secrete = '**PASSWORD_TO_ENCRYPTE_PROTECTED_DATA**'
            template_dict['lochness']['REDCAP'][study] = study_dict
            template_dict['lochness']['SECRETS'][study] = study_secrete

            # lower part of the keyring
            template_dict[f'redcap.{study}'] = {
                    'URL': f'**https://redcap.address.org/redcap/{study}**',
                    'API_TOKEN': {study: f'**API_TOEN_FOR_{study}**'}}

    if 'xnat' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'xnat.{study}'] = {
                'URL': f'**https://{study}-xnat.address.edu**',
                'USERNAME': f'**id_for_xnat_{study}**',
                'PASSWORD': f'**password_for_xnat_{study}**'}

    if 'SECRETS' not in template_dict['lochness'].keys():
        template_dict['lochness']['SECRETS'] = {}

    if 'box' in args.sources:
        for study in args.studies:
            template_dict['lochness']['SECRETS'][study] = 'LOCHNESS_SECRETS'

            # lower part of the keyring
            template_dict[f'box.{study}'] = {
                'CLIENT_ID': '**CLIENT_ID_FROM_BOX_APPS**',
                'CLIENT_SECRET': '**CLIENT_SECRET_FROM_BOX_APPS**',
                'API_TOEN': '**APITOKEN_FROM_BOX_APPS**'}

    if 'mediaflux' in args.sources:
        for study in args.studies:
            template_dict['lochness']['SECRETS'][study] = 'LOCHNESS_SECRETS'

            # lower part of the keyring
            template_dict[f'mediaflux.{study}'] = {
                'HOST': 'mediaflux.researchsoftware.unimelb.edu.au',
                'PORT': '443',
                'TRANSPORT': 'https',
                'TOKEN': '**TOKEN_delete_this_line_if_no_token**',
                'DOMAIN': 'local',
                'USER': '**ID**',
                'PASSWORD': '**PASSWORD**'}

    if 'mindlamp' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'mindlamp.{study}'] = {
                "URL": "**api.lamp.digital**",
                "ACCESS_KEY": args.email,
                "SECRET_KEY": "**PASSWORD**"}

    if 'daris' in args.sources:
        for study in args.studies:
            # lower part of the keyring
            template_dict[f'daris.{study}'] = {
                "URL": "https://daris.researchsoftware.unimelb.edu.au",
                "TOKEN": "******",
                "PROJECT_CID": "******",
                }

    if args.lochness_sync_send:
        if args.s3:
            pass
        elif args.rsync:
            # lower part of the keyring
            template_dict['rsync'] = {
                'ID': "rsync_server_id",
                'SERVER': "rsync_server_ip",
                'PASSWORD': "rsync_server_password",
                'PHOENIX_PATH_RSYNC': "/rsync/server/phoenix/path"}
        else:
            # lower part of the keyring
            template_dict[f'lochness_sync'] = {
                "HOST": "phslxftp2.partners.org",
                "USERNAME": "USERNAME",
                "PASSWORD": "*******",
                "PATH_IN_HOST": "/PATH/IN/HOST",
                "PORT": "2222",
                }

    if args.lochness_sync_receive:
        # lower part of the keyring
        template_dict[f'lochness_sync'] = {
            "PATH_IN_HOST": "/PATH/IN/HOST",
            }

    with open(keyring_loc, 'w') as f:
        json.dump(template_dict, f,
                  sort_keys=False,
                  indent='  ',
                  separators=(',', ': '))


def create_config_template(config_loc: Path, args: object) -> None:
    '''Create config file template'''

    config_example = f'''keyring_file: {args.outdir}/.lochness.enc
phoenix_root: {args.outdir}/PHOENIX
BIDS: True
pid: {args.outdir}/lochness.pid
stderr: {args.outdir}/lochness.stderr
stdout: {args.outdir}/lochness.stdout
poll_interval: {args.poll_interval}
ssh_user: {args.ssh_user}
ssh_host: {args.ssh_host}
sender: {args.email}
pii_table: {args.pii_csv}
lochness_sync_history_csv: {args.lochness_sync_history_csv}
'''

    if 'rpms' in args.sources:
        config_example += '''RPMS_PATH: /mnt/prescient/RPMS_incoming
RPMS_id_colname: src_subject_id
RPMS_consent_colname: Consent
'''

    if args.s3:
        s3_lines = f'''AWS_BUCKET_NAME: ampscz-dev
AWS_BUCKET_ROOT: TEST_PHOENIX_ROOT'''
        config_example += s3_lines
    
    if 'redcap' in args.sources:
        config_example += '\nredcap:'

        for study in args.studies:
            redcap_deidentify_lines = f'''
    {study}:
        deidentify: True
        data_entry_trigger_csv: {args.det_csv}
        update_metadata: True'''
            config_example += redcap_deidentify_lines

    if 'mediaflux' in args.sources:
        config_example += '\nmediaflux:'

        for study in args.studies:
            line_to_add = f'''
    {study}:
        namespace: /DATA/ROOT/UNDER/MEDIAFLUX/{study}
        delete_on_success: False
        file_patterns:
            actigraphy:
                - vendor: Philips
                  product: Actiwatch 2
                  data_dir: actigraphy
                  pattern: '*csv'
                  protect: True
                - vendor: Activinsights
                  product: GENEActiv
                  data_dir: actigraphy
                  pattern: '*csv'
                - vendor: Insights
                  product: GENEActivQC
                  data_dir: actigraphy
                  pattern: '*csv'
            eeg:
                   - product: eeg
                     data_dir: eeg
                     pattern: '*.csv'
            interviews:
                   - product: offsite_interview
                     data_dir: interviews
                     pattern: '*.mp4'
              '''

            config_example += line_to_add

    if 'box' in args.sources:
        config_example += '\nbox:'
        for study in args.studies:
            line_to_add = f'''
    {study}:
        base: /DATA/ROOT/UNDER/BOX
        delete_on_success: False
        file_patterns:
            actigraphy:
                - vendor: Philips
                  product: Actiwatch 2
                  data_dir: actigraphy
                  pattern: '*csv'
                  protect: True
                - vendor: Activinsights
                  product: GENEActiv
                  data_dir: actigraphy
                  pattern: '*csv'
                - vendor: Insights
                  product: GENEActivQC
                  data_dir: actigraphy
                  pattern: '*csv'
            eeg:
                   - product: eeg
                     data_dir: eeg
                     pattern: '*.csv'
            interviews:
                   - product: offsite_interview
                     data_dir: interviews
                     pattern: '*.mp4'
             '''

            config_example += line_to_add

    line_to_add = f'''
hdd:
    module_name:
        base: /PHOENIX
admins:
    - {args.email}
notify:
    __global__:
        - {args.email}
                '''
    config_example += line_to_add

    with open(config_loc, 'w') as f:
        f.write(config_example)


def create_example_meta_file_advanced(metadata: str,
                                      project_name: str,
                                      sources: List[str]) -> None:
    '''Create example meta files'''

    col_input_to_col_dict = {'xnat': 'XNAT',
                             'redcap': 'REDCap',
                             'box': 'Box',
                             'mindlamp': 'Mindlamp',
                             'mediaflux': 'Mediaflux',
                             'daris': 'Daris',
                             'rpms': 'RPMS'}

    df = pd.DataFrame({
        'Active': [1],
        'Consent': '1988-09-16',
        'Subject ID': 'subject01'})

    for source in sources:
        source_col = col_input_to_col_dict[source]
        if source == 'xnat':
            value = f'xnat.{project_name}:subproject:subject01'
        else:
            value = f'{source}.{project_name}:subject01'
        df.loc[0, source_col] = value

    df.to_csv(metadata, index=False)


def get_arguments():
    '''Get arguments'''
    parser = ap.ArgumentParser(description='Lochness template maker')
    parser.add_argument('-o', '--outdir',
                        required=True,
                        help='Path of the Lochness template')
    parser.add_argument('-s', '--studies',
                        required=True,
                        nargs='+',
                        help='Names of studies')
    parser.add_argument('-ss', '--sources',
                        required=True,
                        nargs='+',
                        help='List of sources, eg) xnat, redcap, box, '
                             'mindlamp, mediaflux, etc.')
    parser.add_argument('-e', '--email',
                        required=True,
                        help='Email address')
    parser.add_argument('-p', '--poll_interval',
                        default=86400,
                        help='Poll interval in seconds')
    parser.add_argument('-sh', '--ssh_host',
                        required=True,
                        help='ssh id')
    parser.add_argument('-su', '--ssh_user',
                        required=True,
                        help='ssh id')
    parser.add_argument('-lss', '--lochness_sync_send',
                        default=True,
                        action='store_true',
                        help='Enable lochness to lochness transfer on the '
                             'sender side')
    parser.add_argument('--rsync',
                        default=False,
                        action='store_true',
                        help='Use rsync in lochness to lochness transfer')
    parser.add_argument('--s3',
                        default=False,
                        action='store_true',
                        help='Use s3 rsync in lochness to lochness transfer')
    parser.add_argument('-lsr', '--lochness_sync_receive',
                        default=False,
                        action='store_true',
                        help='Enable lochness to lochness transfer on the '
                             'server side')
    parser.add_argument('-lsh', '--lochness_sync_history_csv',
                        default='lochness_sync_history.csv',
                        help='Lochness sync history database csv path')
    parser.add_argument('-det', '--det_csv',
                        default='data_entry_trigger.csv',
                        help='Redcap data entry trigger database csv path')
    parser.add_argument('-pc', '--pii_csv',
                        default='pii_convert.csv',
                        help='Location of table to be used in deidentifying '
                             'redcap fields')

    args = parser.parse_args()

    if Path(args.outdir).is_dir():
        sys.exit(f'*{args.outdir} already exists. Please provide another path')


    create_lochness_template(args)


if __name__ == '__main__':
    get_arguments()
