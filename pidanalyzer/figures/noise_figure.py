from typing import List

import numpy as np
from matplotlib import colors as colors, pyplot as plt, rcParams
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from . import TEXTSIZE
from .. import BANNER
from ..common import log
from ..trace import Trace, to_mask


def _check_lims_list(lims: list) -> bool:
    if type(lims) is not list:
        log.info('noise_bounds is no valid list')
        return False
    lims = np.array(lims)
    if np.shape(lims) == (4,2):
        ll = lims[:, 1] - lims[:, 0]
        if np.sum(np.abs((ll - np.abs(ll)))) == 0:
            return True
    return False


def create(path: str, name: str, header: dict, traces: List[Trace], lims: list) -> Figure:
    rcParams.update({'font.size': 9})
    log.info('Making noise plot...')
    title = 'Noise plot: Log number: {}{}{}'.format(header['logNum'], (10 * ' '), path)
    fig = plt.figure(title, figsize=(16, 8))
    # gridspec devides window into 25 horizontal, 31 vertical fields
    gs1 = GridSpec(25, 3 * 10 + 2, wspace=0.6, hspace=0.7, left=0.04, right=1., bottom=0.05, top=0.97)

    max_noise_gyro = np.max(
        [traces[0].noise_gyro['max'], traces[1].noise_gyro['max'], traces[2].noise_gyro['max']]) + 1.
    max_noise_debug = np.max(
        [traces[0].noise_debug['max'], traces[1].noise_debug['max'], traces[2].noise_debug['max']]) + 1.
    max_noise_d = np.max([traces[0].noise_d['max'], traces[1].noise_d['max'], traces[2].noise_d['max']]) + 1.

    meanspec = np.array([traces[0].noise_gyro['hist2d_sm'].mean(axis=1).flatten(),
                         traces[1].noise_gyro['hist2d_sm'].mean(axis=1).flatten(),
                         traces[2].noise_gyro['hist2d_sm'].mean(axis=1).flatten()], dtype=np.float64)
    thresh = 100.
    mask = to_mask(traces[0].noise_gyro['freq_axis'].clip(thresh - 1e-9, thresh))
    meanspec_max = np.max(meanspec * mask[:-1])

    if not _check_lims_list(lims):
        lims = np.array([[1, max_noise_gyro], [1, max_noise_debug], [1, max_noise_d], [0, meanspec_max * 1.5]])
        if lims[0, 1] == 1:
            lims[0, 1] = 100.
        if lims[1, 1] == 1:
            lims[1, 1] = 100.
        if lims[2, 1] == 1:
            lims[2, 1] = 100.
    else:
        lims = np.array(lims)

    cax_gyro = plt.subplot(gs1[0, 0:7])
    cax_debug = plt.subplot(gs1[0, 8:15])
    cax_d = plt.subplot(gs1[0, 16:23])
    cmap = 'viridis'

    axes_gyro = []
    axes_debug = []
    axes_d = []
    axes_trans = []

    for i, tr in enumerate(traces):
        if tr.noise_gyro['freq_axis'][-1] > 1000:
            pltlim = [0, 1000]
        else:
            pltlim = [tr.noise_gyro['freq_axis'][-0], tr.noise_gyro['freq_axis'][-1]]
        # gyro plots
        ax0 = plt.subplot(gs1[1 + i * 8:1 + i * 8 + 8, 0:7])
        if len(axes_gyro):
            ax0.sharex(axes_gyro[0])
        axes_gyro.append(ax0)
        ax0.set_title('gyro ' + tr.name, y=0.88, color='w')
        pc0 = plt.pcolormesh(tr.noise_gyro['throt_axis'], tr.noise_gyro['freq_axis'],
                             tr.noise_gyro['hist2d_sm'] + 1., norm=colors.LogNorm(vmin=lims[0, 0], vmax=lims[0, 1]),
                             cmap=cmap)
        ax0.set_ylabel('frequency in Hz')
        ax0.grid()
        ax0.set_ylim(pltlim)
        if i < 2:
            plt.setp(ax0.get_xticklabels(), visible=False)
        else:
            ax0.set_xlabel('throttle in %')

        fig.colorbar(pc0, cax_gyro, orientation='horizontal')
        cax_gyro.xaxis.set_ticks_position('top')
        cax_gyro.xaxis.set_tick_params(pad=-0.5)

        if max_noise_gyro == 1.:
            ax0.text(0.5, 0.5, 'no gyro[' + str(i) + '] trace found!\n',
                     horizontalalignment='center', verticalalignment='center',
                     transform=ax0.transAxes, fontdict={'color': 'white'})

        # debug plots
        ax1 = plt.subplot(gs1[1 + i * 8:1 + i * 8 + 8, 8:15])
        if len(axes_debug):
            ax1.sharex(axes_debug[0])
        axes_debug.append(ax1)
        ax1.set_title('debug ' + tr.name, y=0.88, color='w')
        pc1 = plt.pcolormesh(tr.noise_debug['throt_axis'], tr.noise_debug['freq_axis'],
                             tr.noise_debug['hist2d_sm'] + 1.,
                             norm=colors.LogNorm(vmin=lims[1, 0], vmax=lims[1, 1]), cmap=cmap)
        ax1.set_ylabel('frequency in Hz')
        ax1.grid()
        ax1.set_ylim(pltlim)
        if i < 2:
            plt.setp(ax1.get_xticklabels(), visible=False)
        else:
            ax1.set_xlabel('throttle in %')

        fig.colorbar(pc1, cax_debug, orientation='horizontal')
        cax_debug.xaxis.set_ticks_position('top')
        cax_debug.xaxis.set_tick_params(pad=-0.5)

        if max_noise_debug == 1.:
            ax1.text(0.5, 0.5, 'no debug[' + str(i) + '] trace found!\n'
                                                      'To get transmission of\n'
                                                      '- all filters: set debug_mode = NOTCH\n'
                                                      '- LPF only: set debug_mode = GYRO',
                     horizontalalignment='center', verticalalignment='center',
                     transform=ax1.transAxes, fontdict={'color': 'white'})

        if i < 2:
            # dterm plots
            ax2 = plt.subplot(gs1[1 + i * 8:1 + i * 8 + 8, 16:23])
            if len(axes_d):
                ax2.sharex(axes_d[0])
            axes_d.append(ax2)
            ax2.set_title('D-term ' + tr.name, y=0.88, color='w')
            pc2 = plt.pcolormesh(tr.noise_d['throt_axis'], tr.noise_d['freq_axis'], tr.noise_d['hist2d_sm'] + 1.,
                                 norm=colors.LogNorm(vmin=lims[2, 0], vmax=lims[2, 1]), cmap=cmap)
            ax2.set_ylabel('frequency in Hz')
            ax2.grid()
            ax2.set_ylim(pltlim)
            plt.setp(ax2.get_xticklabels(), visible=False)

            fig.colorbar(pc2, cax_d, orientation='horizontal')
            cax_d.xaxis.set_ticks_position('top')
            cax_d.xaxis.set_tick_params(pad=-0.5)

            if max_noise_d == 1.:
                ax2.text(0.5, 0.5, 'no D[' + str(i) + '] trace found!\n',
                         horizontalalignment='center', verticalalignment='center',
                         transform=ax2.transAxes, fontdict={'color': 'white'})
        else:
            # throttle plots
            ax21 = plt.subplot(gs1[1 + i * 8:1 + i * 8 + 4, 16:23])
            ax22 = plt.subplot(gs1[1 + i * 8 + 5:1 + i * 8 + 8, 16:23])
            ax21.bar(tr.throt_scale[:-1], tr.throt_hist * 100., width=1., align='edge', color='black', alpha=0.2,
                     label='throttle distribution')
            ax21.sharex(axes_d[0])
            ax21.vlines(header['tpa_percent'], 0., 100., label='tpa', colors='red', alpha=0.5)
            ax21.grid()
            ax21.set_ylim([0., np.max(tr.throt_hist) * 100. * 1.1])
            ax21.set_xlabel('throttle in %')
            ax21.set_ylabel('usage %')
            ax21.set_xlim([0., 100.])
            handles, labels = ax21.get_legend_handles_labels()
            ax21.legend(handles[::-1], labels[::-1])
            ax22.fill_between(tr.time, 0., tr.throttle, label='throttle input', facecolors='black', alpha=0.2)
            ax22.hlines(header['tpa_percent'], tr.time[0], tr.time[-1], label='tpa', colors='red', alpha=0.5)

            ax22.set_ylabel('throttle in %')
            ax22.legend()
            ax22.grid()
            ax22.set_ylim([0., 100.])
            ax22.set_xlim([tr.time[0], tr.time[-1]])
            ax22.set_xlabel('time in s')

        # transmission plots
        ax3 = plt.subplot(gs1[1 + i * 8:1 + i * 8 + 8, 24:30])
        if len(axes_trans):
            ax3.sharex(axes_trans[0])
        axes_trans.append(ax3)
        ax3.fill_between(tr.noise_gyro['freq_axis'][:-1], 0, meanspec[i], label=tr.name + ' gyro noise', alpha=0.2)
        ax3.set_ylim(lims[3])
        ax3.set_ylabel(tr.name + ' gyro noise a.u.')
        ax3.grid()
        ax3r = plt.twinx(ax3)
        ax3r.plot(tr.noise_gyro['freq_axis'][:-1], tr.filter_trans * 100., label=tr.name + ' filter transmission')
        ax3r.set_ylabel('transmission in %')
        ax3r.set_ylim([0., 100.])
        ax3r.set_xlim([tr.noise_gyro['freq_axis'][0], tr.noise_gyro['freq_axis'][-2]])
        lines, labels = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3r.get_legend_handles_labels()
        ax3r.legend(lines + lines2, labels + labels2, loc=1)
        if i < 2:
            plt.setp(ax3.get_xticklabels(), visible=False)
        else:
            ax3.set_xlabel('frequency in hz')

    meanfreq = 1. / (traces[0].time[1] - traces[0].time[0])
    ax4 = plt.subplot(gs1[12, -1])
    t = BANNER + "| Betaflight: Version " + header['version'] + ' | Craftname: ' + header['craftName'] + \
        ' | meanFreq: ' + str(int(meanfreq)) + ' | rcRate/Expo: ' + header['rcRate'] + '/' + header['rcExpo'] + '\n' + \
        'rcYawRate/Expo: ' + header['rcYawRate'] + '/' + \
        header['rcYawExpo'] + ' | deadBand: ' + header['deadBand'] + ' | yawDeadBand: ' + header['yawDeadBand'] + \
        ' | Throttle min/tpa/max: ' + header['minThrottle'] + '/' + header['tpa_breakpoint'] + '/' + \
        header['maxThrottle'] + ' | dynThrPID: ' + header['dynThrottle'] + '| D-TermSP: ' + header['dTermSetPoint'] + \
        '| vbatComp: ' + header['vbatComp'] + ' | debug ' + header['debug_mode']

    ax4.text(0, 0, t, ha='left', va='center', rotation=90, color='grey', alpha=0.5, fontsize=TEXTSIZE)
    ax4.axis('off')

    ax5l = plt.subplot(gs1[:1, 24:27])
    ax5r = plt.subplot(gs1[:1, 27:30])
    ax5l.axis('off')
    ax5r.axis('off')
    filt_settings_l = 'G lpf type: ' + header['gyro_lpf'] + ' at ' + header['gyro_lowpass_hz'] + '\n' + \
                      'G notch at: ' + header['gyro_notch_hz'] + ' cut ' + header[
                      'gyro_notch_cutoff'] + '\n' + 'gyro lpf 2: ' + header['gyro_lowpass_type']
    filt_settings_r = '| D lpf type: ' + header['dterm_filter_type'] + ' at ' + header['dterm_lpf_hz'] + '\n' + \
                      '| D notch at: ' + header['dterm_notch_hz'] + ' cut ' + header['dterm_notch_cutoff'] + '\n' + \
                      '| Yaw lpf at: ' + header['yaw_lpf_hz']

    ax5l.text(0, 0, filt_settings_l, ha='left', fontsize=TEXTSIZE)
    ax5r.text(0, 0, filt_settings_r, ha='left', fontsize=TEXTSIZE)

    log.info('Saving as image...')
    plt.savefig(path[:-13] + name + '_' + str(header['logNum']) + '_noise.png')
    return fig
