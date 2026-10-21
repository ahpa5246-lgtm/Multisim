"""Measurements on sampled voltages, independent of the UI and solver."""
import bisect, math, cmath

def validate(t,v):
    if len(t)!=len(v) or not t or not all(math.isfinite(x) for x in (*t,*v)):raise ValueError('Invalid measurement samples')
    if len(t)>1 and any(b<=a for a,b in zip(t,t[1:])):raise ValueError('Time samples must increase')

def mean(t,v):
    validate(t,v)
    if len(t)==1:return v[0]
    return sum((b-a)*(v[i]+v[i+1])/2 for i,(a,b) in enumerate(zip(t,t[1:])))/(t[-1]-t[0])

def readings(t,v):
    dc=mean(t,v);rms=math.sqrt(max(0,mean(t,[x*x for x in v])))
    crossings=[]
    for i in range(len(t)-1):
        if v[i]<=dc<v[i+1]:crossings.append(t[i]+(t[i+1]-t[i])*(dc-v[i])/(v[i+1]-v[i]))
    freq=(len(crossings)-1)/(crossings[-1]-crossings[0]) if len(crossings)>1 else None
    return {'DC mean (V)':dc,'Total RMS (V)':rms,'AC RMS (V)':math.sqrt(max(0,rms*rms-dc*dc)),
            'Peak-to-peak (V)':max(v)-min(v),'Frequency (Hz)':freq}

def spectrum(t,v,n=512):
    validate(t,v)
    if len(t)<3 or n<16 or n>2048:raise ValueError('Spectrum needs a transient record and 16–2048 resamples')
    # Preserve at least the original sample count instead of reducing every
    # record to 512 points (which can fold high frequencies into false peaks).
    n=1 << (max(n,len(t))-1).bit_length()
    if n>65536:raise ValueError('Spectrum record exceeds 65536 resamples; shorten the transient')
    duration=t[-1]-t[0]
    # End-exclusive uniform grid; never FFT the solver's adaptive samples directly.
    uniform=[t[0]+i*duration/n for i in range(n)];resampled=[]
    for x in uniform:
        j=max(1,min(len(t)-1,bisect.bisect_right(t,x)))
        resampled.append(v[j-1]+(v[j]-v[j-1])*(x-t[j-1])/(t[j]-t[j-1]))
    dc=sum(resampled)/n
    window=[.5-.5*math.cos(2*math.pi*i/n) for i in range(n)]
    y=[(x-dc)*w for x,w in zip(resampled,window)];gain=sum(window)
    transformed=_fft([complex(x) for x in y])
    amplitudes=[abs(transformed[k])/gain*(1 if k in (0,n//2) else 2) for k in range(n//2+1)]
    return [k/duration for k in range(n//2+1)],amplitudes


def _fft(values):
    """Original iterative radix-2 transform, no additional runtime dependency."""
    n=len(values);out=list(values);j=0
    for i in range(1,n):
        bit=n>>1
        while j & bit:j^=bit;bit>>=1
        j^=bit
        if i<j:out[i],out[j]=out[j],out[i]
    size=2
    while size<=n:
        root=cmath.exp(-2j*math.pi/size)
        for start in range(0,n,size):
            weight=1+0j
            for k in range(size//2):
                even=out[start+k];odd=weight*out[start+k+size//2]
                out[start+k]=even+odd;out[start+k+size//2]=even-odd;weight*=root
        size*=2
    return out
