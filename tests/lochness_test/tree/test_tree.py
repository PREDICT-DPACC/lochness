import lochness
from lochness.tree import get, Templates
import lochness.config as config

from pathlib import Path
import sys

import pytest
import shutil
import os

import zipfile
import tempfile as tf
import json
import cryptease as crypt
import pandas as pd

lochness_root = Path(lochness.__path__[0]).parent
scripts_dir = lochness_root / 'scripts'
test_dir = lochness_root / 'tests'
sys.path.append(str(scripts_dir))
sys.path.append(str(test_dir))
from lochness_create_template import create_lochness_template

from test_lochness import Args, Tokens, KeyringAndEncrypt, args, Lochness
from test_lochness import show_tree_then_delete, config_load_test



def test_get_nonbids():
    for data_type, temp_dict in Templates.items():
        base = 'PHOENIX/GENERAL/StudyA/1001'
        get(data_type, base, BIDS=False)
    
    for data_type, temp_dict in Templates.items():
        if data_type == 'behav_qc':
            assert (Path(base) / 'mri_behav' / 'processed' /
                    'behav_qc').is_dir()
        elif data_type == 'hearing':
            pass
        elif data_type == 'mindlamp':
            assert (Path(base) / 'phone' / 'processed').is_dir()
            assert (Path(base) / 'phone' / 'raw').is_dir()
        else:
            assert (Path(base) / data_type / 'processed').is_dir()
            assert (Path(base) / data_type / 'raw').is_dir()

    show_tree_then_delete('PHOENIX')


def test_get_bids():
    for data_type, temp_dict in Templates.items():
        base = 'PHOENIX/GENERAL/StudyA/1001'
        get(data_type, base)

    for data_type, temp_dict in Templates.items():
        if data_type == 'behav_qc':
            assert (Path(base).parent / 'processed' / '1001' / 'mri_behav' /
                    'behav_qc').is_dir()
        elif data_type == 'hearing':
            pass
        elif data_type == 'mindlamp':
            assert (Path(base).parent / 'processed' / '1001' /
                    'phone').is_dir()
            assert (Path(base).parent / 'raw' / '1001' / 'phone').is_dir()
        else:
            assert (Path(base).parent / 'processed' / '1001' /
                    data_type).is_dir()
            assert (Path(base).parent / 'raw' / '1001' / data_type).is_dir()

    show_tree_then_delete('PHOENIX')


def test_get_more_than_one_subject():
    for subject in [1001, 1002]:
        for data_type, temp_dict in Templates.items():
            base = f'PHOENIX/GENERAL/StudyA/{subject}'
            get(data_type, base)

    for subject in ['1001', '1002']:
        for data_type, temp_dict in Templates.items():
            if data_type == 'behav_qc':
                assert (Path(base).parent / 'processed' / subject /
                        'mri_behav' / 'behav_qc').is_dir()
            elif data_type == 'hearing':
                pass
            elif data_type == 'mindlamp':
                assert (Path(base).parent / 'processed' / subject /
                        'phone').is_dir()
                assert (Path(base).parent / 'raw' / subject / 'phone').is_dir()
            else:
                assert (Path(base).parent / 'processed' / subject /
                        data_type).is_dir()
                assert (Path(base).parent / 'raw' / subject /
                        data_type).is_dir()

    show_tree_then_delete('PHOENIX')


def test_get_more_than_one_study():
    for study in ['StudyA', 'StudyB']:
        for subject in [1001, 1002]:
            for data_type, temp_dict in Templates.items():
                base = f'PHOENIX/GENERAL/{study}/{subject}'
                get(data_type, base)

    for study in ['StudyA', 'StudyB']:
        for subject in ['1001', '1002']:
            base = f'PHOENIX/GENERAL/{study}/{subject}'
            for data_type, temp_dict in Templates.items():
                if data_type == 'behav_qc':
                    assert (Path(base).parent / 'processed' / subject /
                            'mri_behav' / 'behav_qc').is_dir()
                elif data_type == 'hearing':
                    pass
                elif data_type == 'mindlamp':
                    assert (Path(base).parent / 'processed' / subject /
                            'phone').is_dir()
                    assert (Path(base).parent / 'raw' / subject /
                            'phone').is_dir()
                else:
                    assert (Path(base).parent / 'processed' / subject /
                            data_type).is_dir()
                    assert (Path(base).parent / 'raw' / subject /
                            data_type).is_dir()
    show_tree_then_delete('PHOENIX')

