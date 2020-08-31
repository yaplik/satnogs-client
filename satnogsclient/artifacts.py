import logging
import tempfile

import h5py

LOGGER = logging.getLogger(__name__)


class Artifacts():  # pylint: disable=R0903
    def __init__(self, waterfall, observation_id):
        self.artifacts_file = None
        self._waterfall_data = waterfall.data
        self._observation_id = observation_id

    def create(self):
        self.artifacts_file = tempfile.TemporaryFile()
        hdf5_file = h5py.File(self.artifacts_file, 'w')
        hdf5_file.attrs['artifact_version'] = 1
        hdf5_file.attrs['observation_id'] = self._observation_id

        # Create waterfall group
        wf_group = hdf5_file.create_group('waterfall')

        # Store waterfall attributes
        wf_group.attrs['start_time'] = self._waterfall_data['timestamp']
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
                                data=self._waterfall_data['compressed']['offset'],
                                compression='gzip')
        wf_group.create_dataset('scale',
                                data=self._waterfall_data['compressed']['scale'],
                                compression='gzip')
        wf_group.create_dataset('data',
                                data=self._waterfall_data['compressed']['values'],
                                compression='gzip')
        wf_group.create_dataset('relative_time',
                                data=self._waterfall_data['trel'],
                                compression='gzip')
        wf_group.create_dataset('absolute_time',
                                data=self._waterfall_data['data']['tabs'],
                                compression='gzip')
        wf_group.create_dataset('frequency', data=self._waterfall_data['freq'], compression='gzip')

        # Store waterfall labels

        wf_group['offset'].dims[0].label = 'Time (seconds)'
        wf_group['scale'].dims[0].label = 'Time (seconds)'
        wf_group['relative_time'].dims[0].label = 'Time (seconds)'
        wf_group['absolute_time'].dims[0].label = 'Time (seconds)'
        wf_group['frequency'].dims[0].label = 'Frequency (kHz)'
        wf_group['data'].dims[0].label = 'Frequency (kHz)'
        wf_group['data'].dims[1].label = 'Time (seconds)'

        hdf5_file.close()
        self.artifacts_file.seek(0)
