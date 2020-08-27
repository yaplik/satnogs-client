import logging
import tempfile

import h5py

LOGGER = logging.getLogger(__name__)


class Artifacts():
    def __init__(self, waterfall):
        self.artifacts_file = None
        self._waterfall = waterfall

    def create(self):
        self.artifacts_file = h5py.File(tempfile.TemporaryFile(), 'w')
        # Create waterfall group
        wf_group = self.artifacts_file.create_group('waterfall')

        # Store waterfall attributes
        wf_group.attrs['artifact_version'] = 1
        wf_group.attrs['start_time'] = self._waterfall['timestamp']
        wf_group.attrs['offset_in_stds'] = -2.0
        wf_group.attrs['scale_in_stds'] = 8.0

        # Store waterfall units
        wf_group.attrs['data_min_unit'] = 'dB'
        wf_group.attrs['data_max_unit'] = 'dB'
        wf_group.attrs['offset_unit'] = 'dB'
        wf_group.attrs['scale_unit'] = 'dB/div'
        wf_group.attrs['data_unit'] = 'div'
        wf_group.attrs['relative_time_unit'] = 'seconds'
        wf_group.attrs['absolute_time_unit'] = 'seconds'
        wf_group.attrs['frequency_unit'] = 'kHz'

        # Store waterfall datasets
        wf_group.create_dataset('offset',
                                data=self._waterfall['compressed']['offset'],
                                compression='gzip')
        wf_group.create_dataset('scale',
                                data=self._waterfall['compressed']['scale'],
                                compression='gzip')
        wf_group.create_dataset('data',
                                data=self._waterfall['compressed']['values'],
                                compression='gzip')
        wf_group.create_dataset('relative_time', data=self._waterfall['trel'], compression='gzip')
        wf_group.create_dataset('absolute_time',
                                data=self._waterfall['data']['tabs'],
                                compression='gzip')
        wf_group.create_dataset('frequency', data=self._waterfall['freq'], compression='gzip')

        # Store waterfall labels

        wf_group['offset'].dims[0].label = 'Time (seconds)'
        wf_group['scale'].dims[0].label = 'Time (seconds)'
        wf_group['relative_time'].dims[0].label = 'Time (seconds)'
        wf_group['absolute_time'].dims[0].label = 'Time (seconds)'
        wf_group['frequency'].dims[0].label = 'Frequency (kHz)'
        wf_group['data'].dims[0].label = 'Frequency (kHz)'
        wf_group['data'].dims[1].label = 'Time (seconds)'

    def close(self):
        self.artifacts_file.close()
