import os
import sys
import logging
from pathlib import Path
from string import Template
import re


Templates = {
    'actigraphy': {
        'raw': Template('${base}/actigraphy/raw'),
        'processed': Template('${base}/actigraphy/processed')
    },
    'eeg': {
        'raw': Template('${base}/eeg/raw'),
        'processed': Template('${base}/eeg/processed')
    },
    'mri': {
        'raw': Template('${base}/mri/raw'),
        'processed': Template('${base}/mri/processed')
    },
    'mri_behav': {
        'raw': Template('${base}/mri_behav/raw'),
        'processed': Template('${base}/mri_behav/processed')
    },
    'behav_qc': {
        'raw': Template('${base}/mri_behav/processed/behav_qc'),
        'processed': Template('${base}/mri_behav/processed/behav_qc')
    },
    'mri_eye': {
        'raw': Template('${base}/mri_eye/raw/eyeTracking'),
        'processed': Template('${base}/mri_eye/processed/eyeTracking')
    },
    'phone': {
        'raw': Template('${base}/phone/raw'),
        'processed': Template('${base}/phone/processed')
    },
    'physio': {
        'raw': Template('${base}/physio/raw'),
        'processed': Template('${base}/physio/processed')
    },
    'cogassess': {
        'raw': Template('${base}/cogassess/raw'),
        'processed': Template('${base}/cogassess/processed')
    },
    'hearing': {
        'raw': Template('${base}/cogassess/raw'),
        'processed': Template('${base}/cogassess/processed'),
    },
    'retroquest': {
        'raw': Template('${base}/retroquest/raw'),
        'processed': Template('${base}/retroquest/processed')
    },
    'saliva': {
        'raw': Template('${base}/saliva/raw'),
        'processed': Template('${base}/saliva/processed')
    },
    'offsite_interview': {
        'raw': Template('${base}/offsite_interview/raw'),
        'processed': Template('${base}/offsite_interview/processed')
    },
    'onsite_interview': {
        'raw': Template('${base}/onsite_interview/raw'),
        'processed': Template('${base}/onsite_interview/processed')
    },
    'interviews': {
        'raw': Template('${base}/interviews/raw'),
        'processed': Template('${base}/interviews/processed')
    },
    'surveys': {
        'raw': Template('${base}/surveys/raw'),
        'processed': Template('${base}/surveys/processed')
    },
    'mindlamp': {
        'raw': Template('${base}/phone/raw'),
        'processed': Template('${base}/phone/processed')
    }
}

logger = logging.getLogger(__name__)

def get(data_type, base, **kwargs):
    '''get phoenix folder for a subject and data_type'''
    if data_type not in Templates:
        raise TreeError('no tree templates defined for {0}'.format(data_type))

    raw_folder = None
    processed_folder = None

    if kwargs.get('BIDS', True):   # PHOENIX to BIDS
        phoenix_id = Path(base).name  # get SUBJECT
        study = Path(base).parent.name   # get study

        if 'raw' in Templates[data_type]:
            # restructure root
            base = Path(base).parent.parent / study / 'raw'
            sub_folder = Templates[data_type]['raw'].substitute(
                    base='', **kwargs)[1:]
            sub_folder = re.sub('/(raw|processed)', '', sub_folder)
            raw_folder = base / phoenix_id / sub_folder

        if 'processed' in Templates[data_type]:
            # restructure root
            base = Path(base).parent.parent / study / 'processed'
            sub_folder = Templates[data_type]['processed'].substitute(
                    base='', **kwargs)[1:]

            sub_folder = re.sub('/(raw|processed)', '', sub_folder)
            processed_folder = base / phoenix_id / sub_folder

    else:
        if 'raw' in Templates[data_type]:
            raw_folder = Templates[data_type]['raw'].substitute(
                    base=base, **kwargs)

        if 'processed' in Templates[data_type]:
            processed_folder = Templates[data_type]['processed'].substitute(
                    base=base, **kwargs)

    if kwargs.get('processed', True):
        if kwargs.get('makedirs', True) and \
                processed_folder and not os.path.exists(processed_folder):
            logger.debug(f'creating processed folder {processed_folder}')
            os.makedirs(processed_folder)
            os.chmod(processed_folder, 0o01777)
        return processed_folder
    else:
        if kwargs.get('makedirs', True) and \
                raw_folder and not os.path.exists(raw_folder):
            logger.debug(f'creating raw folder {raw_folder}')
            os.makedirs(raw_folder)
        return raw_folder


class TreeError(Exception):
    pass

