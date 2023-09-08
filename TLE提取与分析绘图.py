# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 20:01:04 2023

@author: Rick-Li
"""
#%matplotlib auto
import urllib.request,urllib.error
import datetime
import numpy as np
from sgp4.api import Satrec, jday, SatrecArray
from astropy.coordinates import TEME, CartesianDifferential, CartesianRepresentation, ITRS
from astropy.time import Time
from astropy import units as u
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
import multiprocessing
import time
from mpl_toolkits.basemap import Basemap
from tqdm import tqdm
import threading
plt.rc('font',family='Times New Roman')

def transform(teme_dif,jd,fr):
    teme = TEME(teme_dif, obstime=Time(jd+fr,format='jd'))
    itrs_geo = teme.transform_to(ITRS(obstime=Time(jd+fr,format='jd')))
    location = itrs_geo.earth_location
    return [location.geodetic.lon.value,location.geodetic.lat.value,location.geodetic.height.value]

def position(r,v,jd,fr):
    #将TEME坐标转换到经纬度
    teme_p = CartesianRepresentation(r[:,0]*u.km,r[:,1]*u.km,r[:,2]*u.km)
    teme_v = CartesianDifferential(v[:,0]*u.km/u.s,v[:,1]*u.km/u.s,v[:,2]*u.km/u.s)
    teme_dif = teme_p.with_differentials(teme_v)
    
    num_cores = multiprocessing.cpu_count()
    results = np.array(Parallel(n_jobs=num_cores)(delayed(transform)(teme_dif[i],jd[i],fr[i]) for i in tqdm(range(len(r)))))
    
    return results

def satellite(url):
    out = []
    for i in url:
        res = urllib.request.urlopen(i)
        bys = res.read()
        a = bys.decode("utf-8")
        b = a.split('\n')
        out.append(Satrec.twoline2rv(b[1], b[2]))
    return SatrecArray(out)

def divide(results,col):
    tib = 0
    for i in range(len(results)-1):
        if results[i+1,0] - results[i,0] > 10:
            plt.plot(results[tib:i,0],results[tib:i,1],col+'--',linewidth=1.5)
            tib = i+1
        else:
            continue
    plt.plot(results[tib:,0],results[tib:,1],col+'--',linewidth=1.5)

def TEMECalculate(delta=0):
    
    url = ['http://celestrak.org/NORAD/elements/gp.php?CATNR=55252',
    'http://celestrak.org/NORAD/elements/gp.php?CATNR=55261']

    stars = satellite(url)
    
    ti = datetime.datetime.now() - datetime.timedelta(hours = 8)
    ti = ti - datetime.timedelta(seconds= ti.second) - datetime.timedelta(minutes= ti.minute) + datetime.timedelta(hours= delta)
    
    jds = []
    frs = []
    for i in range(5700):
        times = ti + datetime.timedelta(seconds= i)
        jd, fr = jday(times.year, times.month, times.day, times.hour, times.minute, times.second)
        jds.append(jd)
        frs.append(fr)
        
    jds = np.array(jds)
    frs = np.array(frs)
    
    e, r, v = stars.sgp4(jds, frs)
    
    
    results = []
    for i in range(len(r)):
        results.append(position(r[i], v[i], jds, frs))
        
    return results
     
def readtxt(flux):

    with open(flux,'r') as f:
        txt = f.read()
    
    data = txt.split('\n')[30:]
    
    datas = np.zeros((len(data)-2,1))
    
    for i in range(len(datas)):
        if float(data[i].split(',')[2])>=0.:
            datas[i] = float(data[i].split(',')[2])
    return datas.reshape(90, 121)

def plot(que,datas):
    
    plt.figure(figsize=(36, 16),dpi=60)
    while True:
        results = que.get()
        plt.clf()
        
        plt.contourf(np.linspace(-180,180,121), np.linspace(-89,89,90), datas,cmap='viridis_r',levels=np.linspace(1,datas.max(),100) ,alpha=0.3 ,linewidths=0.1,antialiased=True)
        cb = plt.colorbar(ticks=np.arange(0,datas.max(),5e5),fraction=0.0232)
        cb.ax.tick_params(labelright=False,labelleft=True,labelsize=15)
        cb.set_label(r'$Flux > 0.10MeV(cm^{-2}s^{-1})$ $at$ $500.0km$',size=15)
        cs = plt.contour(np.linspace(-180,180,121), np.linspace(-89,89,90), datas,levels=np.linspace(0,datas.max(),5) ,colors="k",linestyles="dashed")
        plt.clabel(cs,fontsize=9,inline=True)
        
        #projection='ortho'
        m = Basemap(lon_0 = 0 , lat_0 = 0)
        m.bluemarble()
        m.drawparallels(np.arange(-90., 90.1, 30.), labels=[1,0,0,0], fontsize=18,color='none')
        m.drawmeridians(np.arange(-180., 180., 30.), labels=[0,0,0,1], fontsize=18,color='none')
        # m.drawcoastlines(linewidth=1.5) 
        # m.drawcountries(linewidth=1.5) 
        #m.fillcontinents(color='coral',lake_color='aqua')
        m.drawmeridians(np.arange(-180,180,30))
        m.drawparallels(np.arange(-90,90.1,30))
        
        result1 = results[0]
        result2 = results[1]
        
        divide(result1,'r')
        divide(result2,'c')
        while True:
            t0 = datetime.datetime.utcnow()
            plt.title("%s (UTC)" % t0.strftime("%d %b %Y %H:%M:%S"),fontsize=20)
            DN = m.nightshade(t0)
            index = t0.minute*60+t0.second
            p1, = plt.plot(result1[index,0],result1[index,1],'r*',markersize='20')
            t1 = plt.text(result1[index,0]+0.5,result1[index,1],'TN01',fontsize=20,color='r')
            ll1 = plt.text(result1[index,0]+0.5,result1[index,1]-5,f'[{round(result1[index,0],1)},{round(result1[index,1],1)}]',fontsize=20,color='r')
            
            
            p2, = plt.plot(result2[index,0],result2[index,1],'c*',markersize='20')
            t2 = plt.text(result2[index,0]+0.5,result2[index,1],'TN02',fontsize=20,color='c')
            ll2 = plt.text(result2[index,0]+0.5,result2[index,1]-5,f'[{round(result2[index,0],1)},{round(result2[index,1],1)}]',fontsize=20,color='c')
            
            #plt.legend(loc='upper left',fontsize=20)
            plt.pause(0.9)
            p1.remove()
            t1.remove()
            ll1.remove()
            p2.remove()
            t2.remove()
            ll2.remove()
            for coll in DN.collections:
                coll.remove()
            if datetime.datetime.now().minute == 0 and datetime.datetime.now().second == 0:
                #plt.pause(0.5)
                break
    

def reCal(que):
    while True:
        if datetime.datetime.now().minute == 59 and datetime.datetime.now().second == 0:
            results = TEMECalculate(1)
            que.put(results)
        else:
            time.sleep(0.5)

if __name__ == '__main__': 
    multiprocessing.freeze_support()
    
    n = 0
    flu = '.\AE8_MIN_0.1MeV.txt'
    
    que = multiprocessing.Queue()
        
    if n == 0 :
        que.put(TEMECalculate())
        n+=1
    
    
    p_re = threading.Thread(target=reCal,args=(que,))
    p_re.daemon=True
    p_re.start()
    
    datas = readtxt(flu)
    plot(que,datas)    
            