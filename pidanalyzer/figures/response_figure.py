from typing import List

import numpy as np
from matplotlib import pyplot as plt, rcParams
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

from . import TEXTSIZE
from .. import BANNER
from ..common import log
from ..trace import Trace


def create(path: str, name: str, header: dict, traces: List[Trace], old_style: bool = False) -> Figure:
    rcParams.update({'font.size': 9})
    log.info('Making PID plot...')
    fig = plt.figure('Response plot: Log number: ' + header['logNum'] + '          ' + path,
                     figsize=(16, 8))
    # gridspec devides window into 24 horizontal, 3*10 vertical fields
    gs1 = GridSpec(24, 3 * 10, wspace=0.6, hspace=0.7, left=0.04, right=1., bottom=0.05, top=0.97)

    for i, trace in enumerate(traces):
        ax0 = plt.subplot(gs1[0:6, i * 10:i * 10 + 9])
        plt.title(trace.name)
        plt.plot(trace.time, trace.gyro, label=trace.name + ' gyro')
        plt.plot(trace.time, trace.input, label=trace.name + ' loop input')
        plt.ylabel('degrees/second')
        ax0.get_yaxis().set_label_coords(-0.1, 0.5)
        plt.grid()
        tracelim = np.max([np.abs(trace.gyro), np.abs(trace.input)])
        plt.ylim([-tracelim * 1.1, tracelim * 1.1])
        plt.legend(loc=1)
        plt.setp(ax0.get_xticklabels(), visible=False)

        ax1 = plt.subplot(gs1[6:8, i * 10:i * 10 + 9], sharex=ax0)
        plt.hlines(header['tpa_percent'], trace.time[0], trace.time[-1], label='tpa', colors='red', alpha=0.5)
        plt.fill_between(trace.time, 0., trace.throttle, label='throttle', color='grey', alpha=0.2)
        plt.ylabel('throttle %')
        ax1.get_yaxis().set_label_coords(-0.1, 0.5)
        plt.grid()
        plt.xlim([trace.time[0], trace.time[-1]])
        plt.ylim([0, 100])
        plt.legend(loc=1)
        plt.xlabel('log time in s')

        if old_style:
            # response vs. time in color plot
            plt.setp(ax1.get_xticklabels(), visible=False)
            ax2 = plt.subplot(gs1[9:16, i * 10:i * 10 + 9], sharex=ax0)
            plt.pcolormesh(trace.avr_t, trace.time_resp, np.transpose(trace.spec_sm), vmin=0, vmax=2.)
            plt.ylabel('response time in s')
            ax2.get_yaxis().set_label_coords(-0.1, 0.5)
            plt.xlabel('log time in s')
            plt.xlim([trace.avr_t[0], trace.avr_t[-1]])
        else:
            # response vs throttle plot. more useful.
            ax2 = plt.subplot(gs1[9:16, i * 10:i * 10 + 9])
            plt.title(trace.name + ' response', y=0.88, color='w')
            if 1 == 0:
                # TypeError: Dimensions of C (478, 101) are incompatible with X (102) and/or Y (478); see help(pcolormesh)
                plt.pcolormesh(trace.thr_response['throt_scale'], trace.time_resp, trace.thr_response['hist2d_norm'],
                               vmin=0.,
                               vmax=2.)
            else:
                plt.pcolormesh(trace.thr_response['hist2d_norm'],
                               vmin=0.,
                               vmax=2.)
            plt.ylabel('response time in s')
            ax2.get_yaxis().set_label_coords(-0.1, 0.5)
            plt.xlabel('throttle in %')
            plt.xlim([0., 100.])

        cmap = plt.cm.get_cmap('Blues')
        cmap._init()
        alphas = np.abs(np.linspace(0., 0.5, cmap.N, dtype=np.float64))
        cmap._lut[:-3, -1] = alphas
        ax3 = plt.subplot(gs1[17:, i * 10:i * 10 + 9])
        plt.contourf(*trace.resp_low[2], cmap=cmap, linestyles=None, antialiased=True,
                     levels=np.linspace(0, 1, 20, dtype=np.float64))
        plt.plot(trace.time_resp, trace.resp_low[0],
                 label=trace.name + ' step response ' + '(<' + str(int(Trace.threshold)) + ') '
                       + ' PID ' + header[trace.name + 'PID'])

        if trace.high_mask.sum() > 0:
            cmap = plt.cm.get_cmap('Oranges')
            cmap._init()
            alphas = np.abs(np.linspace(0., 0.5, cmap.N, dtype=np.float64))
            cmap._lut[:-3, -1] = alphas
            plt.contourf(*trace.resp_high[2], cmap=cmap, linestyles=None, antialiased=True,
                         levels=np.linspace(0, 1, 20, dtype=np.float64))
            plt.plot(trace.time_resp, trace.resp_high[0],
                     label=trace.name + ' step response ' + '(>' + str(int(Trace.threshold)) + ') '
                           + ' PID ' + header[trace.name + 'PID'])
        plt.xlim([-0.001, 0.501])

        plt.legend(loc=1)
        plt.ylim([0., 2])
        plt.ylabel('strength')
        ax3.get_yaxis().set_label_coords(-0.1, 0.5)
        plt.xlabel('response time in s')

        plt.grid()

    meanfreq = 1. / (traces[0].time[1] - traces[0].time[0])
    ax4 = plt.subplot(gs1[12, -1])
    t = BANNER + " | Betaflight: Version " + header['version'] + ' | Craftname: ' + header[
        'craftName'] + \
        ' | meanFreq: ' + str(int(meanfreq)) + ' | rcRate/Expo: ' + header['rcRate'] + '/' + header[
            'rcExpo'] + '\nrcYawRate/Expo: ' + header['rcYawRate'] + '/' \
        + header['rcYawExpo'] + ' | deadBand: ' + header['deadBand'] + ' | yawDeadBand: ' + \
        header['yawDeadBand'] \
        + ' | Throttle min/tpa/max: ' + header['minThrottle'] + '/' + header['tpa_breakpoint'] + '/' + \
        header['maxThrottle'] \
        + ' | dynThrPID: ' + header['dynThrottle'] + '| D-TermSP: ' + header[
            'dTermSetPoint'] + '| vbatComp: ' + header['vbatComp']

    plt.text(0, 0, t, ha='left', va='center', rotation=90, color='grey', alpha=0.5, fontsize=TEXTSIZE)
    ax4.axis('off')
    log.info('Saving as image...')
    plt.savefig(path[:-13] + name + '_' + str(header['logNum']) + '_response.png')
    return fig
