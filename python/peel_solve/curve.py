# Copyright (c) 2021 Alastair Macleod
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from __future__ import print_function
import maya.cmds as m
from peel_solve import dag
import math
import collections
import bisect

from peel_solve import vector


class FCurve(object):
    """ Representation of an fcurve object

    * self.node - the name of the maya node
    * self.attr - the attribute on the node
    * self.data - dict of keys -> times/values
    """

    def __init__(self, node=None, attr=None):
        """ empty fcurve """

        if attr is None and isinstance(node, basestring) and '.' in node:
            self.node, self.attr = node.split(".")
        else:
            self.node = node
            self.attr = attr
        self.data = {}

    def fetch(self, sl=False, use_api=False):
        """ get the data from maya """

        if self.node is None or self.attr is None:
            raise ValueError("Invalid parameters for node/attr")

        if use_api:
            curve = dag.anim_curve(self.node, self.attr, create=False)
            n = curve.numKeys()
            for i in range(n):
                v = curve.value(i)
                t = curve.time(i).value()
                self.data[t] = v
        else:

            node_attr = self.node + '.' + self.attr
            k = m.keyframe(node_attr, q=True, sl=sl)
            v = m.keyframe(node_attr, q=True, vc=True, sl=sl)
            if k is None or v is None:
                print("no keys")
                return
            self.data = dict(zip(k, v))

    def apply(self, stepped=False, use_api=False, create=False):

        """ apply the data to maya """

        if not m.objExists(self.node):
            if not create:
                m.error("Node does not exist: " + self.node)
            else:
                m.spaceLocator(name=self.node)

        if not m.objExists(self.node + '.' + self.attr):
            if not create:
                m.error("Channel does not exist: " + self.node + '.' + self.attr)
            else:
                m.addAttr(self.node, ln=self.attr, k=True)

        if use_api:
            dag.apply_curve(self.node, self.attr, self.data, stepped)
        else:
            m.cutKey(self.node + '.' + self.attr)
            for k, v in self.data.items():
                m.setKeyframe(self.node + '.' + self.attr, t=k, v=v)

    def keys(self):
        """ return the keys """
        return sorted(self.data.keys())

    def values(self):
        """ return the values """
        return [i[1] for i in sorted(self.data.items())]

    def __getitem__(self, index):
        """ array method """
        return self.data[index]

    def __setitem__(self, index, value):
        """ array set method """
        self.data[index] = value

    def check_valid(self):
        if self.data is None or len(self.data) == 0:
            raise RuntimeError("No keys on " + self.node + "." + self.attr)

    def offset(self, value):

        """ offset the data in memory by a value, does not modify the scene - needs applied """

        self.check_valid()

        newdata = {}
        for k, v in self.data.iteritems():
            newdata[k + value] = v

        self.data = newdata

    def zero(self):

        """ move the keys so the first frame is at zero """

        self.check_valid()

        start = min(self.data.keys())
        if start == 0.0:
            return

        self.offset(-start)

    def selectKeys(self, keys):

        """ select the provided keys in the fcurve editor """

        m.select(self.node)
        m.selectKey(clear=True)
        for i in keys:
            m.selectKey(self.node + '.' + self.attr, t=(i, i), add=True)


class Channel(object):
    """ A channel has x,y and z tranlsation keys a fixed time step apart (rate) """

    def __init__(self, node, rate, timeRange=None):

        """ create an empty channel.  Data is set to an empty dict """
        self.node = node
        self.rate = rate
        self.timeRange = timeRange
        self.data = {}

    def fetch(self):

        """ populate self.data with keys from the maya scene. """

        if self.node is None:
            raise ValueError("no node specified")

        if self.timeRange:

            kx = m.keyframe(self.node + '.tx', q=True, t=self.timeRange)
            ky = m.keyframe(self.node + '.ty', q=True, t=self.timeRange)
            kz = m.keyframe(self.node + '.tz', q=True, t=self.timeRange)

            vx = m.keyframe(self.node + '.tx', q=True, vc=True, t=self.timeRange)
            vy = m.keyframe(self.node + '.ty', q=True, vc=True, t=self.timeRange)
            vz = m.keyframe(self.node + '.tz', q=True, vc=True, t=self.timeRange)

        else:

            kx = m.keyframe(self.node + '.tx', q=True)
            ky = m.keyframe(self.node + '.ty', q=True)
            kz = m.keyframe(self.node + '.tz', q=True)

            vx = m.keyframe(self.node + '.tx', q=True, vc=True)
            vy = m.keyframe(self.node + '.ty', q=True, vc=True)
            vz = m.keyframe(self.node + '.tz', q=True, vc=True)

        if kx != ky: raise RuntimeError("Keys not aligned")
        if kx != kz: raise RuntimeError("Keys not aligned")

        self.data = dict(zip(kx, zip(vx, vy, vz)))

    def __getitem__(self, item):
        return vector.Vector(self.data[item])

    def neighbour_keys(self, frame=None):

        if frame is None:
            frame = m.currentTime(q=True)

        keys = sorted(self.data.keys())
        if len(keys) < 2:
            return None, None, None
        pos = bisect.bisect_left(keys, frame)
        if pos == 0:
            return None, keys[0], keys[1]
        if pos == len(keys):
            return keys[-2], keys[-1], None

        before = keys[pos - 1]
        after = keys[pos]
        if after - frame < frame - before:
            return before, after, keys[pos + 1]
        else:
            return keys[pos - 2], before, after

    def deltas(self):

        """ returns the pyhsical distance (length) between keys.  returns (keys, deltas) """

        keys, vals = zip(*sorted(self.data.items()))
        deltas = []

        for i in range(1, len(keys)):
            p2 = vals[i - 1]
            p1 = vals[i]
            deltav = math.sqrt(sum([(b - a) * (b - a) for a, b in zip(p1, p2)]))
            deltat = keys[i] - keys[i - 1]
            deltas.append(deltav / deltat)

        return keys, deltas

    def spikes(self, width, limit):

        """ uses the deltas to determine where possible spikes in the data may be.
         returns a list of keys where the spikes happen """

        keys, deltas = self.deltas()

        # create a 'width' sized deque and load it with the head of the data
        deck = collections.deque(deltas[:width])

        # slide the deck over the list keeping a moving average

        res = []
        for i in range(width, len(deltas)):
            halfset = sorted(list(deck))[:width / 2]
            average = sum(halfset) / len(halfset)
            res.append(average)
            deck.popleft()
            deck.append(deltas[i])

        out = []
        for i in range(len(deltas)):
            rval = res[i] if i < len(res) else res[-1]
            dif = deltas[i] / rval
            if dif > limit: out.append(keys[i + 1])

        return out

    def find_spikes(self, limit=30, debug=False, time=None):

        """ alternative (and not as good) method for finding spikes.  Deprecated.
        Finds moments where the data maintains the rate, but the key value 
        shifts more than a moving average """

        if self.data is None or len(self.data) is None:
            return None

        if len(self.data) < 2:
            return None

        # sort the keys and values by time
        keys, vals = zip(*sorted(self.data.items()))

        res = []
        last_delta = None
        delta = None

        for i in range(1, len(keys)):

            deltak = keys[i] - keys[i - 1]
            p2 = vals[i - 1]
            p1 = vals[i]
            deltav = math.sqrt(sum([(b - a) * (b - a) for a, b in zip(p1, p2)]))
            delta = deltav / deltak

            if last_delta is None:
                last_delta = delta
                continue

            theta = last_delta - delta

            if debug:
                f = lambda i: "{:10.4f}".format(i)
                x = (i, f(keys[i]), f(vals[i]), f(delta), f(theta), str(abs(theta) > limit))
                print("%02d   key:%s   val:%s   d:%s  t:%s   %s  " % x)

            if abs(theta) > limit:
                if time is not None:
                    if keys[i] < time[0]: continue
                    if keys[i] > time[1]: continue

                res.append((keys[i], theta))
            else:
                last_delta = delta

        return res


def ls():
    """ returns current selected keyframes as [ (node, keys), ... ] """

    res = []
    curves = m.keyframe(q=True, sl=True, n=True)
    if curves is None:
        return None
    for curve in curves:
        node = m.listConnections(curve + ".output", d=True, p=True)
        if node is None or len(node) == 0: continue
        keys = m.keyframe(curve, q=True, sl=True)
        res.append((node[0], keys))
    return res


def get_keys(node_chan):
    """ returns a list of the keys (times) for the node.attr, or None """

    if '.' not in node_chan: node_chan += '.tx'
    keys = sorted(m.keyframe(node_chan, q=True))
    if keys is None: return None
    if len(keys) < 1: return None
    return keys


def current_segment_or_gap(node_chan, rate):
    """ returns ( 'gap' | 'segment', ( in, out ) ) or None """

    ct = m.currentTime(q=True)

    r = rate * 0.5

    seg = segments(node_chan, rate)
    if seg is None or len(seg) == 0: return None

    if ct < seg[0][0] - r:
        return 'before', seg[0][0]

    if ct > seg[-1][1] + r:
        return 'after', seg[-1][1]

    last = None
    for i, o in seg:
        # segments are greedy ( add r )
        if i - r < ct and ct < o + r:
            return ('segment', (i, o))
        if last is not None and last < ct and ct < i:
            return ('gap', (last, i))
        last = o


def current_spike_segment(node, rate, sampleWidth=10, limit=3):
    sel = m.ls(sl=True)[0]
    seg = current_segment_or_gap(sel, rate)
    if seg[0] != 'segment':
        return None
    inPoint, outPoint = seg[1]
    ct = m.currentTime(q=True)

    c = channel(sel, rate, seg[1])
    c.fetch()
    spikes = c.spikes(sampleWidth, limit)

    for spike in spikes:
        if spike < ct and spike > inPoint:
            inPoint = spike

        if spike > ct and spike < outPoint:
            outPoint = spike - rate

    return inPoint, outPoint


def segments(node_chan, rate):
    """ returns groups of keys clustered togther (opposite of gaps) """

    keys = getKeys(node_chan)
    if keys is None: return None

    # only one key so make that the only segment
    if len(keys) == 1:
        return [(keys[0], keys[0])]

    res = []
    current = keys[0]
    for i in range(1, len(keys)):
        delta = keys[i] - keys[i - 1]
        if round(delta, 2) - rate * 1.99 > 0:
            res.append((current, keys[i - 1]))
            current = keys[i]

    res.append((current, keys[-1]))
    return res


def gaps(node_chan, rate):
    """ returns the keys right before a gap on the node.channel """

    keys = getKeys(node_chan)
    if keys is None: return

    res = []
    for i in range(1, len(keys)):
        delta = keys[i] - keys[i - 1]
        if round(delta, 2) - rate * 1.99 > 0:
            res.append((keys[i - 1], keys[i]))
    return res


def select_keys(node_chan, keys):
    """ select the keys (time) on the node.channel """
    animcurve = m.listConnections(node_chan, s=True)
    for k in keys:
        m.selectKey(animcurve[0], add=True, k=True, t=(k, k))


def select_segment(node_chan, segment):
    animcurve = m.listConnections(node_chan, s=True)
    m.selectKey(animcurve[0], add=True, k=True, t=segment)


def zero(nodes, start_frame=0):

    start = None
    end = None
    curves = []

    for node in nodes:
        conn = m.listConnections(node, s=True, t="animCurve", p=True)
        if conn is None:
            continue
        for curve_node in conn:
            channel = m.listConnections(curve_node, d=True, p=True)[0]
            curve_obj = FCurve(channel)
            curve_obj.fetch(use_api=True)
            if start is None or min(curve_obj.data.keys()) < start:
                start = min(curve_obj.data.keys())
            if end is None or max(curve_obj.data.keys()) > end:
                end = max(curve_obj.data.keys())
            curves.append(curve_obj)

    if start is None:
        print("Could not find any animation")
        return

    if start == start_frame:
        print("Zero offset, skipping")
        return

    offset = start_frame - start

    for c in curves:
        c.offset(offset)
        c.apply(use_api=True)

    print("Offset %d channels by %f" % (len(curves), offset))

    m.playbackOptions(min=start + offset, max=end + offset)
    m.playbackOptions(ast=start + offset, aet=end + offset)