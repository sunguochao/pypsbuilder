#!/usr/bin/env python
"""
Visual pseudosection explorer for THERMOCALC
"""
# author: Ondrej Lexa
# website: petrol.natur.cuni.cz/~ondro

from .utils import *

import argparse
import time
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colorbar import ColorbarBase
from mpl_toolkits.axes_grid1 import make_axes_locatable

from shapely.geometry import MultiPoint
from descartes import PolygonPatch
from scipy.interpolate import Rbf
from tqdm import tqdm, trange


class PTPS:
    def __init__(self, projfile):
        self.prj = ProjectFile(projfile)
        # Check prefs and scriptfile
        if not os.path.exists(self.prefsfile):
            raise Exception('No tc-prefs.txt file in working directory.')
        for line in open(self.prefsfile, 'r'):
            kw = line.split()
            if kw != []:
                if kw[0] == 'scriptfile':
                    self.bname = kw[1]
                    if not os.path.exists(self.scriptfile):
                        raise Exception('tc-prefs: scriptfile tc-' + self.bname + '.txt does not exists in your working directory.')
                if kw[0] == 'calcmode':
                    if kw[1] != '1':
                        raise Exception('tc-prefs: calcmode must be 1.')
        if not hasattr(self, 'bname'):
            raise Exception('No scriptfile defined in tc-prefs.txt')
        if self.saved:
            stream = gzip.open(self.project, 'rb')
            data = pickle.load(stream)
            stream.close()
            self.shapes = data['shapes']
            self.edges = data['edges']
            self.variance = data['variance']
            self.tspace = data['tspace']
            self.pspace = data['pspace']
            self.tg = data['tg']
            self.pg = data['pg']
            self.gridcalcs = data['gridcalcs']
            self.masks = data['masks']
            self.status = data['status']
            self.delta = data['delta']
            self.ready = True
            self.gridded = True
            # print('Compositions loaded.')
        else:
            self.ready = False
            self.gridded = False

    def __iter__(self):
        if self.ready:
            return iter(self.shapes)
        else:
            return iter([])

    @property
    def phases(self):
        return {phase for key in self for phase in key}

    @property
    def keys(self):
        return list(self.shapes.keys())

    @property
    def tstep(self):
        return self.tspace[1] - self.tspace[0]

    @property
    def pstep(self):
        return self.pspace[1] - self.pspace[0]

    @property
    def scriptfile(self):
        return os.path.join(self.prj.workdir, 'tc-' + self.bname + '.txt')

    @property
    def logfile(self):
        return os.path.join(self.prj.workdir, 'tc-log.txt')

    @property
    def prefsfile(self):
        return os.path.join(self.prj.workdir, 'tc-prefs.txt')

    @property
    def tcexe(self):
        return os.path.join(self.prj.workdir, self.prj.tcexe)

    @property
    def drexe(self):
        return os.path.join(self.prj.workdir, self.prj.drexe)

    @property
    def project(self):
        return os.path.join(self.prj.workdir, self.prj.name + '.psi')

    @property
    def saved(self):
        return os.path.exists(self.project)

    def unidata(self, fid):
        return self.prj.unidata(fid)

    def invdata(self, fid):
        return self.prj.invdata(fid)

    def save(self):
        if self.ready and self.gridded:
            # put to dict
            data = {'shapes': self.shapes,
                    'edges': self.edges,
                    'variance': self.variance,
                    'tspace': self.tspace,
                    'pspace': self.pspace,
                    'tg': self.tg,
                    'pg': self.pg,
                    'gridcalcs': self.gridcalcs,
                    'masks': self.masks,
                    'status': self.status,
                    'delta': self.delta}
            # do save
            stream = gzip.open(self.project, 'wb')
            pickle.dump(data, stream)
            stream.close()

    def refresh_geometry(self):
        # Create shapes
        self.shapes, self.edges, self.bad_shapes = self.prj.create_shapes()
        # calculate variance
        self.variance = {}
        for key in self.shapes:
            ans = '{}\nkill\n\n'.format(' '.join(key))
            self.variance[key] = parse_variance(runprog(self.tcexe, self.prj.workdir, ans))
        self.ready = True

    def gendrawpd(self, export_areas=True):
        with open(self.drawpdfile, 'w', encoding=TCenc) as output:
            output.write('% Generated by PyPSbuilder (c) Ondrej Lexa 2016\n')
            output.write('2    % no. of variables in each line of data, in this case P, T\n')
            ex = list(self.excess)
            ex.insert(0, '')
            output.write('{}'.format(self.nc - len(self.excess)) +
                         '    %% effective size of the system: ' +
                         self.axname + ' +'.join(ex) + '\n')
            output.write('2 1  %% which columns to be x,y in phase diagram\n')
            output.write('\n')
            output.write('% Points\n')
            for i in self.prj.invlist:
                output.write('% ------------------------------\n')
                output.write('i%s   %s\n' % (i[0], i[1]))
                output.write('\n')
                output.write('%s %s\n' % (i[2]['p'][0], i[2]['T'][0]))
                output.write('\n')
            output.write('% Lines\n')
            for u in self.prj.unilist:
                output.write('% ------------------------------\n')
                output.write('u%s   %s\n' % (u[0], u[1]))
                output.write('\n')
                b1 = 'i%s' % u[2]
                if b1 == 'i0':
                    b1 = 'begin'
                b2 = 'i%s' % u[3]
                if b2 == 'i0':
                    b2 = 'end'
                if u[4]['manual']:
                    output.write(b1 + ' ' + b2 + ' connect\n')
                    output.write('\n')
                else:
                    output.write(b1 + ' ' + b2 + '\n')
                    output.write('\n')
                    for p, t in zip(u[4]['p'], u[4]['T']):
                        output.write('%s %s\n' % (p, t))
                    output.write('\n')
            output.write('*\n')
            output.write('% ----------------------------------------------\n\n')
            if export_areas:
                # phases in areas for TC-Investigator
                with open(os.path.join(self.workdir, 'assemblages.txt'), 'w', encoding=TCenc) as tcinv:
                    vertices, edges, phases, tedges, tphases = self.prj.construct_areas()
                    # write output
                    output.write('% Areas\n')
                    output.write('% ------------------------------\n')
                    maxpf = max([len(p) for p in phases]) + 1
                    for ed, ph, ve in zip(edges, phases, vertices):
                        v = np.array(ve)
                        if not (np.all(v[:, 0] < self.trange[0]) or
                                np.all(v[:, 0] > self.trange[1]) or
                                np.all(v[:, 1] < self.prange[0]) or
                                np.all(v[:, 1] > self.prange[1])):
                            d = ('{:.2f} '.format(len(ph) / maxpf) +
                                 ' '.join(['u{}'.format(e) for e in ed]) +
                                 ' % ' + ' '.join(ph) + '\n')
                            output.write(d)
                            tcinv.write(' '.join(ph.union(self.excess)) + '\n')
                    for ed, ph in zip(tedges, tphases):
                        d = ('{:.2f} '.format(len(ph) / maxpf) +
                             ' '.join(['u{}'.format(e) for e in ed]) +
                             ' %- ' + ' '.join(ph) + '\n')
                        output.write(d)
                        tcinv.write(' '.join(ph.union(self.excess)) + '\n')
            output.write('\n')
            output.write('*\n')
            output.write('\n')
            output.write('window {} {} '.format(*self.trange) +
                         '{} {}\n\n'.format(*self.prange))
            output.write('darkcolour  56 16 101\n\n')
            xt, yt = self.ax.get_xticks(), self.ax.get_yticks()
            xt = xt[xt > self.trange[0]]
            xt = xt[xt < self.trange[1]]
            yt = yt[yt > self.prange[0]]
            yt = yt[yt < self.prange[1]]
            output.write('bigticks ' +
                         '{} {} '.format(xt[1] - xt[0], xt[0]) +
                         '{} {}\n\n'.format(yt[1] - yt[0], yt[0]))
            output.write('smallticks {} '.format((xt[1] - xt[0]) / 10) +
                         '{}\n\n'.format((yt[1] - yt[0]) / 10))
            output.write('numbering yes\n\n')
            if export_areas:
                output.write('doareas yes\n\n')
            output.write('*\n')
            print('Drawpd file generated successfully.')

        try:
            runprog(self.drexe, self.workdir, self.bname + '\n')
            print('Drawpd sucessfully executed.')
        except OSError as err:
            print('Drawpd error!', str(err))

    def calculate_composition(self, numT=51, numP=51):
        self.tspace = np.linspace(self.prj.trange[0], self.prj.trange[1], numT)
        self.pspace = np.linspace(self.prj.prange[0], self.prj.prange[1], numP)
        self.tg, self.pg = np.meshgrid(self.tspace, self.pspace)
        self.gridcalcs = np.empty(self.tg.shape, np.dtype(object))
        self.status = np.empty(self.tg.shape)
        self.status[:] = np.nan
        self.delta = np.empty(self.tg.shape)
        self.delta[:] = np.nan
        # check shapes created
        if not self.ready:
            self.refresh_geometry()
        # do grid calculation
        for (r, c) in tqdm(np.ndindex(self.tg.shape), desc='Gridding', total=np.prod(self.tg.shape)):
            t, p = self.tg[r, c], self.pg[r, c]
            k = self.identify(t, p)
            if k is not None:
                self.status[r, c] = 0
                ans = '{}\n\n\n{}\n{}\nkill\n\n'.format(' '.join(k), p, t)
                start_time = time.time()
                runprog(self.tcexe, self.prj.workdir, ans)
                delta = time.time() - start_time
                status, variance, pts, res, output = parse_logfile(self.logfile)
                if len(res) == 1:
                    self.gridcalcs[r, c] = res[0]
                    self.status[r, c] = 1
                    self.delta[r, c] = delta
                # search already done inv neighs
                if self.status[r, c] == 0:
                    edges = self.edges[k]
                    for inv in {self.unidata(ed)['begin'] for ed in edges}.union({self.unidata(ed)['end'] for ed in edges}).difference({0}):
                        if not self.invdata(inv)['manual']:
                            update_guesses(self.scriptfile, self.invdata(inv)['results'][0]['ptguess'])
                            start_time = time.time()
                            runprog(self.tcexe, self.prj.workdir, ans)
                            delta = time.time() - start_time
                            status, variance, pts, res, output = parse_logfile(self.logfile)
                            if len(res) == 1:
                                self.gridcalcs[r, c] = res[0]
                                self.status[r, c] = 1
                                self.delta[r, c] = delta
                                break
                    if self.status[r, c] == 0:
                        self.gridcalcs[r, c] = None
            else:
                self.gridcalcs[r, c] = None
        print('Grid search done. {} empty grid points left.'.format(len(np.flatnonzero(self.status == 0))))
        self.gridded = True
        self.fix_solutions()
        self.create_masks()
        # save
        self.save()

    def create_masks(self):
        if self.ready and self.gridded:
            # Create data masks
            points = MultiPoint(list(zip(self.tg.flatten(), self.pg.flatten())))
            self.masks = OrderedDict()
            for key in tqdm(self, desc='Masking', total=len(self.shapes)):
                self.masks[key] = np.array(list(map(self.shapes[key].contains, points))).reshape(self.tg.shape)

    def fix_solutions(self):
        if self.gridded:
            ri, ci = np.nonzero(self.status == 0)
            fixed, ftot = 0, len(ri)
            tq = trange(ftot, desc='Fix ({}/{})'.format(fixed, ftot))
            for ind in tq:
                r, c = ri[ind], ci[ind]
                t, p = self.tg[r, c], self.pg[r, c]
                k = self.identify(t, p)
                ans = '{}\n\n\n{}\n{}\nkill\n\n'.format(' '.join(k), p, t)
                # search already done grid neighs
                for rn, cn in self.neighs(r, c):
                    if self.status[rn, cn] == 1:
                        start_time = time.time()
                        runprog(self.tcexe, self.prj.workdir, ans)
                        delta = time.time() - start_time
                        status, variance, pts, res, output = parse_logfile(self.logfile)
                        if len(res) == 1:
                            self.gridcalcs[r, c] = res[0]
                            self.status[r, c] = 1
                            self.delta[r, c] = delta
                            fixed += 1
                            tq.set_description(desc='Fix ({}/{})'.format(fixed, ftot))
                            break
                        else:
                            update_guesses(self.scriptfile, self.gridcalcs[rn, cn]['ptguess'])
                        start_time = time.time()
                        runprog(self.tcexe, self.prj.workdir, ans)
                        delta = time.time() - start_time
                        status, variance, pts, res, output = parse_logfile(self.logfile)
                        if len(res) == 1:
                            self.gridcalcs[r, c] = res[0]
                            self.status[r, c] = 1
                            self.delta[r, c] = delta
                            fixed += 1
                            tq.set_description(desc='Fix ({}/{})'.format(fixed, ftot))
                            break
                if self.status[r, c] == 0:
                    tqdm.write('No solution find for {}, {}'.format(t, p))
            print('Fix done. {} empty grid points left.'.format(len(np.flatnonzero(self.status == 0))))

    def neighs(self, r, c):
        m = np.array([[(r - 1, c - 1), (r - 1, c), (r - 1, c + 1)],
                      [(r, c - 1), (None, None), (r, c + 1)],
                      [(r + 1, c - 1), (r + 1, c), (r + 1, c + 1)]])
        if r < 1:
            m = m[1:, :]
        if r > len(self.pspace) - 2:
            m = m[:-1, :]
        if c < 1:
            m = m[:, 1:]
        if c > len(self.tspace) - 2:
            m = m[:, :-1]
        return zip([i for i in m[:, :, 0].flat if i is not None],
                   [i for i in m[:, :, 1].flat if i is not None])

    def data_keys(self, key):
        data = dict()
        if self.ready and self.gridded:
            res = self.gridcalcs[self.masks[key]]
            if len(res) > 0:
                dt = res[0]['data']
                for k in key.difference({'H2O'}):
                    data[k] = sorted(list(dt[k].keys()))
        return data

    @property
    def all_data_keys(self):
        data = dict()
        if self.ready and self.gridded:
            for key in self:
                res = self.gridcalcs[self.masks[key]]
                if len(res) > 0:
                    dt = res[0]['data']
                    for k in key.difference({'H2O'}):
                        data[k] = sorted(list(dt[k].keys()))
        return data

    def collect_inv_data(self, key, phase, expr):
        dt = dict(pts=[], data=[])
        if self.ready:
            edges = self.edges[key]
            for i in {self.unidata(ed)['begin'] for ed in edges}.union({self.unidata(ed)['end'] for ed in edges}).difference({0}):
                T = self.invdata(i)['T'][0]
                p = self.invdata(i)['p'][0]
                res = self.invdata(i)['results'][0]
                v = eval_expr(expr, res['data'][phase])
                dt['pts'].append((T, p))
                dt['data'].append(v)
        return dt

    def collect_edges_data(self, key, phase, expr):
        dt = dict(pts=[], data=[])
        if self.ready:
            for e in self.edges[key]:
                if not self.unidata(e)['manual']:
                    bix, eix = self.unidata(e)['begix'], self.unidata(e)['endix']
                    edt = zip(self.unidata(e)['T'][bix:eix + 1],
                              self.unidata(e)['p'][bix:eix + 1],
                              self.unidata(e)['results'][bix:eix + 1])
                    for T, p, res in edt:
                        v = eval_expr(expr, res['data'][phase])
                        dt['pts'].append((T, p))
                        dt['data'].append(v)
        return dt

    def collect_grid_data(self, key, phase, expr):
        dt = dict(pts=[], data=[])
        if self.ready and self.gridded:
            gdt = zip(self.tg[self.masks[key]],
                      self.pg[self.masks[key]],
                      self.gridcalcs[self.masks[key]],
                      self.status[self.masks[key]])
            for T, p, res, ok in gdt:
                if ok:
                    v = eval_expr(expr, res['data'][phase])
                    dt['pts'].append((T, p))
                    dt['data'].append(v)
        return dt

    def collect_data(self, key, phase, expr, which=7):
        dt = dict(pts=[], data=[])
        if which & (1 << 0):
            d = self.collect_inv_data(key, phase, expr)
            dt['pts'].extend(d['pts'])
            dt['data'].extend(d['data'])
        if which & (1 << 1):
            d = self.collect_edges_data(key, phase, expr)
            dt['pts'].extend(d['pts'])
            dt['data'].extend(d['data'])
        if which & (1 << 2):
            d = self.collect_grid_data(key, phase, expr)
            dt['pts'].extend(d['pts'])
            dt['data'].extend(d['data'])
        return dt

    def merge_data(self, phase, expr, which=7):
        mn, mx = sys.float_info.max, sys.float_info.min
        recs = OrderedDict()
        for key in self:
            if phase in key:
                d = self.collect_data(key, phase, expr, which=which)
                z = d['data']
                if z:
                    recs[key] = d
                    mn = min(mn, min(z))
                    mx = max(mx, max(z))
        return recs, mn, mx

    def show(self, out=None, cmap='viridis', alpha=1, label=False):
        def split_key(key):
            tl = list(key)
            wp = len(tl) // 4 + int(len(tl) % 4 > 1)
            return '\n'.join([' '.join(s) for s in [tl[i * len(tl) // wp: (i + 1) * len(tl) // wp] for i in range(wp)]])
        if isinstance(out, str):
            out = [out]
        vv = np.unique([self.variance[k] for k in self])
        pscolors = plt.get_cmap(cmap)(np.linspace(0, 1, vv.size))
        # Set alpha
        pscolors[:, -1] = alpha
        pscmap = ListedColormap(pscolors)
        norm = BoundaryNorm(np.arange(min(vv) - 0.5, max(vv) + 1), vv.size)
        fig, ax = plt.subplots()
        lbls = []
        exc = frozenset.intersection(*self.keys)
        for k in self:
            lbls.append((split_key(k.difference(exc)), self.shapes[k].representative_point().coords[0]))
            ax.add_patch(PolygonPatch(self.shapes[k], fc=pscmap(norm(self.variance[k])), ec='none'))
        ax.autoscale_view()
        self.add_overlay(ax)
        if out:
            for o in out:
                segx = [np.append(row[4]['fT'], np.nan) for row in self.prj.unilist if o in row[4]['out']]
                segy = [np.append(row[4]['fp'], np.nan) for row in self.prj.unilist if o in row[4]['out']]
                ax.plot(np.hstack(segx)[:-1], np.hstack(segy)[:-1], lw=2, label=o)
            # Shrink current axis's height by 6% on the bottom
            box = ax.get_position()
            ax.set_position([box.x0 + box.width * 0.05, box.y0, box.width * 0.95, box.height])
            # Put a legend below current axis
            ax.legend(loc='upper right', bbox_to_anchor=(-0.04, 1), title='Out', borderaxespad=0, frameon=False)
        if label:
            for txt, xy in lbls:

                ax.annotate(s=txt, xy=xy, weight='bold', fontsize=6, ha='center', va='center')
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='4%', pad=0.05)
        cb = ColorbarBase(ax=cax, cmap=pscmap, norm=norm, orientation='vertical', ticks=vv)
        cb.set_label('Variance')
        ax.axis(self.prj.trange + self.prj.prange)
        if label:
            ax.set_title(self.prj.name + (len(exc) * ' +{}').format(*exc))
        else:
            ax.set_title(self.prj.name)
        plt.show()
        return ax

    def add_overlay(self, ax, fc='none', ec='k'):
        for k in self:
            ax.add_patch(PolygonPatch(self.shapes[k], ec=ec, fc=fc, lw=0.5))

    def show_data(self, key, phase, expr, which=7):
        dt = self.collect_data(key, phase, expr, which=which)
        x, y = np.array(dt['pts']).T
        fig, ax = plt.subplots()
        pts = ax.scatter(x, y, c=dt['data'])
        ax.set_title('{} - {}({})'.format(' '.join(key), phase, expr))
        plt.colorbar(pts)
        plt.show()

    def show_status(self):
        fig, ax = plt.subplots()
        extent = (self.prj.trange[0] - self.tstep / 2, self.prj.trange[1] + self.tstep / 2,
                  self.prj.prange[0] - self.pstep / 2, self.prj.prange[1] + self.pstep / 2)
        cmap = ListedColormap(['orangered', 'limegreen'])
        ax.imshow(self.status, extent=extent, aspect='auto', origin='lower', cmap=cmap)
        self.add_overlay(ax)
        plt.axis(self.prj.trange + self.prj.prange)
        plt.show()

    def show_delta(self):
        fig, ax = plt.subplots()
        extent = (self.prj.trange[0] - self.tstep / 2, self.prj.trange[1] + self.tstep / 2,
                  self.prj.prange[0] - self.pstep / 2, self.prj.prange[1] + self.pstep / 2)
        im = ax.imshow(self.delta, extent=extent, aspect='auto', origin='lower')
        self.add_overlay(ax)
        cb = plt.colorbar(im)
        cb.set_label('sec/point')
        plt.title('THERMOCALC execution time')
        plt.axis(self.prj.trange + self.prj.prange)
        plt.show()

    def identify(self, T, p):
        for key in self:
            if Point(T, p).intersects(self.shapes[key]):
                return key

    def ginput(self):
        plt.ion()
        self.show()
        return self.identify(*plt.ginput()[0])

    def isopleths(self, phase, expr, which=7, smooth=0, filled=True, step=None, N=None, gradient=False, dt=True, only=None, refine=1):
        if step is None and N is None:
            N = 10
        print('Collecting...')
        if only is not None:
            recs = OrderedDict()
            d = self.collect_data(only, phase, expr, which=which)
            z = d['data']
            if z:
                recs[only] = d
                mn = min(z)
                mx = max(z)
        else:
            recs, mn, mx = self.merge_data(phase, expr, which=which)
        if step:
            cntv = np.arange(0, mx + step, step)
            cntv = cntv[cntv > mn - step]
        else:
            cntv = np.linspace(mn, mx, N)
        # Thin-plate contouring of areas
        print('Contouring...')
        scale = self.tstep / self.pstep
        fig, ax = plt.subplots()
        for key in recs:
            tmin, pmin, tmax, pmax = self.shapes[key].bounds
            # ttspace = self.tspace[np.logical_and(self.tspace >= tmin - self.tstep, self.tspace <= tmax + self.tstep)]
            # ppspace = self.pspace[np.logical_and(self.pspace >= pmin - self.pstep, self.pspace <= pmax + self.pstep)]
            ttspace = np.arange(tmin - self.tstep, tmax + self.tstep, self.tstep / refine)
            ppspace = np.arange(pmin - self.pstep, pmax + self.pstep, self.pstep / refine)
            tg, pg = np.meshgrid(ttspace, ppspace)
            x, y = np.array(recs[key]['pts']).T
            try:
                # Use scaling
                rbf = Rbf(x, scale * y, recs[key]['data'], function='thin_plate', smooth=smooth)
                zg = rbf(tg, scale * pg)
                # experimental
                if gradient:
                    if dt:
                        zg = np.gradient(zg, self.tstep, self.pstep)[0]
                    else:
                        zg = -np.gradient(zg, self.tstep, self.pstep)[1]
                    if N:
                        cntv = N
                    else:
                        cntv = 10
                # ------------
                if filled:
                    cont = ax.contourf(tg, pg, zg, cntv)
                else:
                    cont = ax.contour(tg, pg, zg, cntv)
                patch = PolygonPatch(self.shapes[key], fc='none', ec='none')
                ax.add_patch(patch)
                for col in cont.collections:
                    col.set_clip_path(patch)
            except:
                print('Error for {}'.format(key))
        if only is None:
            self.add_overlay(ax)
        plt.colorbar(cont)
        if only is None:
            ax.axis(self.prj.trange + self.prj.prange)
            ax.set_title('{}({})'.format(phase, expr))
        else:
            ax.set_title('{} - {}({})'.format(' '.join(only), phase, expr))
        plt.show()

    def get_gridded(self, phase, expr, which=7, smooth=0):
        recs, mn, mx = self.merge_data(phase, expr, which=which)
        scale = self.tstep / self.pstep
        gd = np.empty(self.tg.shape)
        gd[:] = np.nan
        for key in recs:
            tmin, pmin, tmax, pmax = self.shapes[key].bounds
            ttind = np.logical_and(self.tspace >= tmin - self.tstep, self.tspace <= tmax + self.tstep)
            ppind = np.logical_and(self.pspace >= pmin - self.pstep, self.pspace <= pmax + self.pstep)
            slc = np.ix_(ppind, ttind)
            tg, pg = self.tg[slc], self.pg[slc]
            x, y = np.array(recs[key]['pts']).T
            # Use scaling
            rbf = Rbf(x, scale * y, recs[key]['data'], function='thin_plate', smooth=smooth)
            zg = rbf(tg, scale * pg)
            gd[self.masks[key]] = zg[self.masks[key][slc]]
        return gd

    # Need FIX
    def save_tab(self, tabfile=None, comps=None):
        if not tabfile:
            tabfile = os.path.join(self.prj.workdir, self.prj.name + '.tab')
        if not comps:
            comps = self.all_data_keys
        data = []
        for comp in tqdm(comps, desc='Exporting'):
            data.append(self.get_gridded(comp).flatten())
        with open(tabfile, 'wb') as f:
            head = ['psbuilder', self.prj.name + '.tab', '{:12d}'.format(2),
                    'T(°C)', '   {:16.16f}'.format(self.prj.trange[0])[:19],
                    '   {:16.16f}'.format(self.tstep)[:19], '{:12d}'.format(len(self.tspace)),
                    'p(kbar)', '   {:16.16f}'.format(self.prj.prange[0])[:19],
                    '   {:16.16f}'.format(self.pstep)[:19], '{:12d}'.format(len(self.pspace)),
                    '{:12d}'.format(len(data)), (len(data) * '{:15s}').format(*comps)]
            for ln in head:
                f.write(bytes(ln + '\n', 'utf-8'))
            np.savetxt(f, np.transpose(data), fmt='%15.6f', delimiter='')
        print('Saved.')


def show_ps():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=str, choices=['ps', 'iso'],
                        help="operational mode")
    parser.add_argument("-o", "--out", nargs='+',
                        help="highlight out lines for given phases")
    args = parser.parse_args()
    print(args.mode)
    print(args.out)


if __name__ == "__main__":
    show_ps()