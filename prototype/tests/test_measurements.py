import math, unittest
from workbench import measurements as m

class MeasurementTests(unittest.TestCase):
    def test_dc_and_rms(self):
        t=[i/1000 for i in range(1001)];v=[2+3*math.sin(2*math.pi*10*x) for x in t]
        out=m.readings(t,v)
        self.assertAlmostEqual(out['DC mean (V)'],2,places=4)
        self.assertAlmostEqual(out['AC RMS (V)'],3/math.sqrt(2),places=4)
        self.assertAlmostEqual(out['Frequency (Hz)'],10,places=4)
    def test_spectrum_peak(self):
        t=[i/1024 for i in range(1025)];v=[2*math.sin(2*math.pi*32*x) for x in t]
        f,a=m.spectrum(t,v,512)
        k=max(range(1,len(a)),key=lambda i:a[i])
        self.assertAlmostEqual(f[k],32,delta=1)
        self.assertAlmostEqual(a[k],2,delta=.03)
    def test_bad_axis_rejected(self):
        with self.assertRaises(ValueError):m.readings([0,0],[1,2])
        with self.assertRaises(ValueError):m.spectrum([0],[1])
    def test_spectrum_preserves_high_frequency_record(self):
        t=[i/2048 for i in range(2049)];v=[math.sin(2*math.pi*700*x) for x in t]
        f,a=m.spectrum(t,v,512)
        peak=max(range(1,len(a)),key=lambda i:a[i])
        self.assertAlmostEqual(f[peak],700,delta=1)
