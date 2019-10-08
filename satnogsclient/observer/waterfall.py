from __future__ import absolute_import, division, print_function

import logging

import matplotlib.pyplot as plt
import numpy as np

from satnogsclient import settings

LOGGER = logging.getLogger(__name__)

plt.switch_backend('Agg')


def plot_waterfall(waterfall_file, waterfall_png):
    LOGGER.info('Read waterfall file')
    wf_file = open(waterfall_file)
    nchan = int(np.fromfile(wf_file, dtype='float32', count=1)[0])
    freq = np.fromfile(wf_file, dtype='float32', count=nchan) / 1000.0
    data = np.fromfile(wf_file, dtype='float32')
    data.resize((data.size // (nchan + 1), nchan + 1))
    wf_file.close()
    t_idx, spec = data[:, :1], data[:, 1:]
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
    plt.figure(figsize=(10, 20))
    plt.imshow(spec,
               origin='lower',
               aspect='auto',
               interpolation='None',
               extent=[fmin, fmax, tmin, tmax],
               vmin=vmin,
               vmax=vmax,
               cmap="viridis")
    plt.xlabel("Frequency (kHz)")
    plt.ylabel("Time (seconds)")
    fig = plt.colorbar(aspect=50)
    fig.set_label("Power (dB)")
    plt.savefig(waterfall_png, bbox_inches='tight')
    plt.close()
    LOGGER.info('Waterfall plot finished')
