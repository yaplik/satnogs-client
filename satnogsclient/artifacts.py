import json
import logging
import tempfile

import h5py

LOGGER = logging.getLogger(__name__)


class Artifacts():  # pylint: disable=R0903
    def __init__(self, waterfall, metadata):
        """
        Constructor.

        Arguments:
            waterfall_data: The Waterfall object to be stored
            metadata: A JSON-serializeable dictionary, structure:
                      {
                        'observation_id': integer number,
                        'tle': 3-line string,
                        'frequency': integer number,
                        'location': {
                          'latitude': number,
                          'longitude': number,
                          'altitude': self.location['elev']
                        }
                      }
        """
        self.artifacts_file = None
        self._waterfall_data = waterfall.data
        self._metadata = json.dumps(metadata)

    def create(self):
        self.artifacts_file = tempfile.TemporaryFile()
        hdf5_file = h5py.File(self.artifacts_file, 'w')
        hdf5_file.attrs['artifact_version'] = 2
        hdf5_file.attrs['metadata'] = self._metadata

        # Create waterfall group
        wf_group = hdf5_file.create_group('waterfall')

        # Store observation metadata
        # NOTE: start_time is not equal to observation start time
        wf_group.attrs['start_time'] = self._waterfall_data['timestamp']

        # Store waterfall attributes
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
