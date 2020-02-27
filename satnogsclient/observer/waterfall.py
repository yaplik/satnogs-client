from __future__ import absolute_import, division, print_function

import logging

import matplotlib
import numpy as np

from satnogsclient import settings

LOGGER = logging.getLogger(__name__)

matplotlib.use('Agg')


def plot_waterfall(waterfall_file, waterfall_png):
    LOGGER.info('Read waterfall file')

    wf_file = open(waterfall_file)
    _ = np.fromfile(wf_file, dtype="|S32", count=1)[0]
    nchan = np.fromfile(wf_file, dtype='>i4', count=1)[0]
    samp_rate = np.fromfile(wf_file, dtype='>i4', count=1)[0]
    _ = np.fromfile(wf_file, dtype='>i4', count=1)[0]
    _ = np.fromfile(wf_file, dtype='>f4', count=1)[0]
    _ = np.fromfile(wf_file, dtype='>i4', count=1)[0]
    data_dtypes = np.dtype([('tabs', 'int64'), ('spec', 'float32', (nchan, ))])
    data = np.fromfile(wf_file, dtype=data_dtypes)
    wf_file.close()
    t_idx = data['tabs'] / 1000000.0
    freq = np.linspace(-0.5 * samp_rate, 0.5 * samp_rate, nchan, endpoint=False) / 1000.0
    spec = data['spec']
    tmin, tmax = np.min(t_idx), np.max(t_idx)
    fmin, fmax = np.min(freq), np.max(freq)
    c_idx = spec > -200.0
    if settings.SATNOGS_WATERFALL_AUTORANGE:
        if np.sum(c_idx) > 100:
            vmin = np.mean(spec[c_idx]) - 2.0 * np.std(spec[c_idx])
            vmax = np.mean(spec[c_idx]) + 6.0 * np.std(spec[c_idx])
        else:
            vmin = -100
            vmax = -50
    else:
        vmin = settings.SATNOGS_WATERFALL_MIN_VALUE
        vmax = settings.SATNOGS_WATERFALL_MAX_VALUE
    LOGGER.info('Plot waterfall file')
    matplotlib.pyplot.figure(figsize=(10, 20))
    matplotlib.pyplot.imshow(spec,
                             origin='lower',
                             aspect='auto',
                             interpolation='None',
                             extent=[fmin, fmax, tmin, tmax],
                             vmin=vmin,
                             vmax=vmax,
                             cmap="viridis")
    matplotlib.pyplot.xlabel("Frequency (kHz)")
    matplotlib.pyplot.ylabel("Time (seconds)")
    fig = matplotlib.pyplot.colorbar(aspect=50)
    fig.set_label("Power (dB)")
    matplotlib.pyplot.savefig(waterfall_png, bbox_inches='tight')
    matplotlib.pyplot.close()
    LOGGER.info('Waterfall plot finished')
