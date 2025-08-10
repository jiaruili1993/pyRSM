import numpy as np
import xrayutilities as xu
from silx.io.specfile import SpecFile,Scan
import silx
import os
import plotly
import plotly.graph_objects as go

from PIL import Image

import vtk
from vtk.util import numpy_support

def load_convert(file_name, scan_num):
    # it loads a certain scan with CCD images and calculate the corresponding h,k,l coordinates
    
    sf = silx.io.open(file_name + '.spec');

    # ============ load spec file and motor position====================
    scan = sf[str(scan_num) + '.1']
    length = len(scan['measurement/Epoch'].value)
    I0 = np.array(scan['measurement/Ion_Ch_4'].value)
    I0 /= np.nanmean(I0)

    #     =============== load images =============
    try:
        imgs = np.zeros((length,516, 516))
        for img_num in np.arange(length):
            im = Image.open('images\\S' + str(scan_num).zfill(3) + '\\'+ file_name +'_S' + str(scan_num).zfill(3)+ '_'+str(int(img_num)).zfill(5)+'.tif')
            imgs[img_num,:,:] = im/I0[img_num]
    except:
        print('Number of images does not equal scan point number.')
        return None

    # ========== load sample geometry ==============
    UB = np.array(scan['sample/ub_matrix'].value)[0]
    energy = float(scan['instrument/specfile/scan_header'][18].split(' ')[1])*1000

    try:
        delta = scan['measurement/Delta'].value
    except:
        delta = scan['instrument/positioners/Delta'].value * np.ones(length)

    try:
        eta = scan['measurement/Eta'].value
    except:
        eta = scan['instrument/positioners/Eta'].value * np.ones(length)

    try:
        chi = scan['measurement/Chi'].value
    except:
        chi = scan['instrument/positioners/Chi'].value * np.ones(length)

    try:
        phi = scan['measurement/Phi'].value
    except:
        phi = scan['instrument/positioners/Phi'].value * np.ones(length)

    try:
        nu = scan['measurement/Nu'].value
    except:
        nu = scan['instrument/positioners/Nu'].value * np.ones(length)

    try:
        mu = scan['measurement/Mu'].value
    except:
        mu = scan['instrument/positioners/Mu'].value * np.ones(length)

    # #     ================= load diffractometer geometry ==================

    qconversion = xu.QConversion(sampleAxis = ['x+','z-','y+','z-'], detectorAxis = ['x+','z-'], r_i = [0,1,0])

    hxrd = xu.HXRD( [0,1,0], [0,0,1], en = energy, qconv =  qconversion)

    hxrd.Ang2Q.init_area(
            'x-', 'z-',
            cch1=188, cch2=146,
            Nch1=516, Nch2=516,
            pwidth1=28.38/516, pwidth2=28.38/516,
            distance=770
        )
    # # first inner dimension, then outer dimension

    # #     ================= angle to hkl ====================
    angle_values =   [mu, eta, chi, phi, nu, delta]   #[[26.056],  [13.028]]
    qx, qy, qz = hxrd.Ang2Q.area(*angle_values, UB=UB)
    return imgs, qx, qy, qz

def rsm_convert(file_name, scan_list, h_n = 50, k_n = 50, l_n = 50, 
            return_imgs = False, hklrange = None):
    # This program calculates the intensity at a gridded point with h_n*k_n*l_n.
    # The return is a 3d matrix, and 3* 1d lists of h,k,l.
    # input:
    # file_name: the spec file name
    # scan_list: can be a single scan number (integer) or list of number i.e. [14, 15, 16...]
    # h_n, k_n, l_n: the number of voxels in the output
    # return_imgs: boolean, whether return detector image in order to check the calculation
    if isinstance(scan_list, int):
        imgs, qx, qy, qz = load_convert(file_name, scan_list)
    else:
        scan = scan_list[0]
        imgs, qx, qy, qz = load_convert(file_name, scan)
        for scan in scan_list[1:]:
            imgs_temp, qx_temp, qy_temp, qz_temp = load_convert(file_name, scan)
            imgs = np.vstack([imgs, imgs_temp])
            qx = np.vstack([qx, qx_temp])
            qy = np.vstack([qy, qy_temp])
            qz = np.vstack([qz, qz_temp])
    
#   ================= binning into regular grid ====================
    if hklrange == None:
        h_min,h_max = [np.min(qx), np.max(qx)]
        k_min,k_max = [np.min(qy), np.max(qy)]
        l_min,l_max = [np.min(qz), np.max(qz)]
    else:
        h_min,h_max = hklrange[0]
        k_min,k_max = hklrange[1]
        l_min,l_max = hklrange[2]

    gridder = xu.Gridder3D(nx=h_n, ny=k_n, nz=l_n)
    gridder.KeepData(True)
    gridder.dataRange(
        xmin=h_min, xmax=h_max,
        ymin=k_min, ymax=k_max,
        zmin=l_min, zmax=l_max,
        fixed=True
    )
    flag = imgs>0
    gridder(qx[flag], qy[flag], qz[flag], imgs[flag])

    grid_data = gridder.data
    grid_data[grid_data<0.01]= np.nan
    coords = [gridder.xaxis, gridder.yaxis, gridder.zaxis]
    if return_imgs:
        return grid_data, coords, imgs, qx, qy, qz
    else:
        return grid_data, coords




def visualize_det(imgs, qx, qy, qz, cscale = [50, 99], downscale = 20):
    # This program views the loaded MCP image stack at corresponding hkl position.
    # The slider select the image frame.
    h_min,h_max = np.nanmin(qx), np.nanmax(qx)
    k_min,k_max = np.nanmin(qy), np.nanmax(qy)
    l_min,l_max = np.nanmin(qz), np.nanmax(qz)
    hlen = h_max-h_min
    klen = k_max-k_min
    llen = l_max-l_min
    cmin, cmax = np.nanpercentile(imgs, cscale)
    
    cmap = 'viridis'
    cmin = 0

    nb_frames = np.shape(imgs)[0]

    imgs = rebin(imgs, downscale)
    qx = rebin(qx, downscale)
    qy = rebin(qy, downscale)
    qz = rebin(qz, downscale)



    fig = go.Figure(frames=[go.Frame(data=go.Surface(
        x = qx[idx], 
        y = qy[idx], 
        z = qz[idx], 
        cmin=cmin, cmax=cmax, 
        surfacecolor=imgs[idx]
        ),
        name=str(idx) # you need to name the frame for the animation to behave properly
        )
        for idx in range(nb_frames)])

    # Add data to be displayed before animation starts
    fig.add_trace(go.Surface(
        x = qx[0], 
        y =qy[0], 
        z=qz[0], 
        cmin=cmin, cmax=cmax, 
        surfacecolor=imgs[0]
        ))

    def frame_args(duration):
        return {
                "frame": {"duration": duration},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

    sliders = [
                {
                    "pad": {"b": 10, "t": 60},
                    "len": 0.9,
                    "x": 0.1,
                    "y": 0,
                    "steps": [
                        {
                            "args": [[f.name], frame_args(0)],
                            "label": str(k),
                            "method": "animate",
                        }
                        for k, f in enumerate(fig.frames)
                    ],
                }
            ]

    # Layout
    fig.update_layout(
             width=600,
             height=600,
             scene=dict(
                        xaxis=dict(range=[h_min-abs(hlen)*0.05, h_max+abs(hlen)*0.05], autorange=False),
                        yaxis=dict(range=[k_min-abs(klen)*0.05, k_max+abs(klen)*0.05], autorange=False),
                        zaxis=dict(range=[l_min-abs(llen)*0.05, l_max+abs(llen)*0.05], autorange=False),
                        aspectratio=dict(x=1, y=1, z=1),
                        xaxis_title='H',
                        yaxis_title='K',
                        zaxis_title='L'
                        ),
             updatemenus = [
                {
                    "buttons": [
                        {
                            "args": [None, frame_args(50)],
                            "label": "&#9654;", # play symbol
                            "method": "animate",
                        },
                        {
                            "args": [[None], frame_args(0)],
                            "label": "&#9724;", # pause symbol
                            "method": "animate",
                        },
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 70},
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                }
             ],
             sliders=sliders
    )

    # fig.show()
    return fig

def l_slice(grid_data, coords, logscale = False, dichro = False, title = None, start = 0, cscale = [50, 99]):
    # With the exported intensity grid points and h,k,l list, show l_slices.
    # logscale: show in log color scale.
    # dichro: whether this is a dichroic signal, if yes, the color scale is from (-cmax, +cmax)
    # title: string for figure title
    # start: int, the starting frame number
    # cscale: defalt [50, 99] set color scale corresponding to 50% and 99% intensity level.
    if logscale:
        volume = np.log(grid_data)
    else:
        volume = grid_data
    r, c = len(coords[0]), len(coords[1])
    
    h_min,h_max = [coords[0][0], coords[0][-1]]
    k_min,k_max = [coords[1][0], coords[1][-1]]
    l_min,l_max = [coords[2][0], coords[2][-1]]
    hlen = h_max-h_min
    klen = k_max-k_min
    llen = l_max-l_min
    
    if dichro:
        cmap = 'RdBu'
        cmin, cmax = np.nanpercentile(abs(volume), cscale)
        cmin = -cmax
    else:
        cmin, cmax = np.nanpercentile(volume, cscale)
        cmap = 'viridis'
        cmin = 0


    nb_frames = len(coords[2])
    xx,zz = np.meshgrid(coords[0],coords[1])
    # print(np.shape(xx), np.shape(zz),np.shape(volume[0,1,:]))

    fig = go.Figure(frames=[go.Frame(data=go.Surface(
        z=(l_min + k/len(coords[2]) * llen) * np.ones((r, c)),
        surfacecolor=(volume[:,:,k]),
        cmin=cmin, cmax=cmax, 
        x = xx.T,#coords[2], 
        y= zz.T#coords[0]
        ),
        name=str(k) # you need to name the frame for the animation to behave properly
        )
        for k in range(nb_frames)])

    # Add data to be displayed before animation starts
    fig.add_trace(go.Surface(
        z=(l_min + start/len(coords[2]) * llen) * np.ones((r, c)),
        surfacecolor=(volume[:,:,start]),
        colorscale=cmap,
        cmin=cmin, cmax=cmax,
        colorbar=dict(thickness=20, ticklen=4), 
        x = xx.T,#coords[2], 
        y = zz.T #coords[0]
        ))

    def frame_args(duration):
        return {
                "frame": {"duration": duration},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

    sliders = [
                {
                    "pad": {"b": 10, "t": 60},
                    "len": 0.9,
                    "x": 0.1,
                    "y": 0,
                    "steps": [
                        {
                            "args": [[f.name], frame_args(0)],
                            "label": str(k),
                            "method": "animate",
                        }
                        for k, f in enumerate(fig.frames)
                    ],
                }
            ]

    # Layout
    fig.update_layout(
             title=title,
             width=600,
             height=600,
             scene=dict(
                        xaxis=dict(range=[h_min-abs(hlen)*0.05, h_max+abs(hlen)*0.05], autorange=False),
                        yaxis=dict(range=[k_min-abs(klen)*0.05, k_max+abs(klen)*0.05], autorange=False),
                        zaxis=dict(range=[l_min-abs(llen)*0.05, l_max+abs(llen)*0.05], autorange=False),
                        aspectratio=dict(x=1, y=1, z=1),
                        xaxis_title='H',
                        yaxis_title='K',
                        zaxis_title='L'
                        ),
             updatemenus = [
                {
                    "buttons": [
                        {
                            "args": [None, frame_args(50)],
                            "label": "&#9654;", # play symbol
                            "method": "animate",
                        },
                        {
                            "args": [[None], frame_args(0)],
                            "label": "&#9724;", # pause symbol
                            "method": "animate",
                        },
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 70},
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                }
             ],
             sliders=sliders
    )

    fig.show()
    return None


def k_slice(grid_data, coords, logscale = False, dichro = False, title = None, start = 0, cscale = [50, 99]):
    # With the exported intensity grid points and h,k,l list, show k_slices.
    # logscale: show in log color scale.
    # dichro: whether this is a dichroic signal, if yes, the color scale is from (-cmax, +cmax)
    # title: string for figure title
    # start: int, the starting frame number
    # cscale: defalt [50, 99] set color scale corresponding to 50% and 99% intensity level.
    if logscale:
        volume = np.log(grid_data)
    else:
        volume = grid_data
    r, c = len(coords[0]), len(coords[2])
    
    h_min,h_max = [coords[0][0], coords[0][-1]]
    k_min,k_max = [coords[1][0], coords[1][-1]]
    l_min,l_max = [coords[2][0], coords[2][-1]]
    hlen = h_max-h_min
    klen = k_max-k_min
    llen = l_max-l_min

    if dichro:
        cmap = 'RdBu'
        cmin, cmax = np.nanpercentile(abs(volume), cscale)
        cmin = -cmax
    else:
        cmin, cmax = np.nanpercentile(volume, cscale)
        cmap = 'viridis'
        cmin = 0


    nb_frames = len(coords[1])
    xx,zz = np.meshgrid(coords[0],coords[2])
    # print(np.shape(xx), np.shape(zz),np.shape(volume[:,0,:]))

    fig = go.Figure(frames=[go.Frame(data=go.Surface(
        y=(k_min + k/len(coords[1]) * klen) * np.ones((r, c)),
        surfacecolor=(volume[:,k,:]),
        cmin=cmin, cmax=cmax, 
        x = xx.T,#coords[2], 
        z= zz.T#coords[0]
        ),
        name=str(k) # you need to name the frame for the animation to behave properly
        )
        for k in range(nb_frames)])

    # Add data to be displayed before animation starts
    fig.add_trace(go.Surface(
        y=(k_min + start/len(coords[1]) * klen) * np.ones((r, c)),
        surfacecolor=(volume[:,start,:]),
        colorscale=cmap,
        cmin=cmin, cmax=cmax,
        colorbar=dict(thickness=20, ticklen=4), 
        x = xx.T,#coords[2], 
        z= zz.T #coords[0]
        ))

    def frame_args(duration):
        return {
                "frame": {"duration": duration},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

    sliders = [
                {
                    "pad": {"b": 10, "t": 60},
                    "len": 0.9,
                    "x": 0.1,
                    "y": 0,
                    "steps": [
                        {
                            "args": [[f.name], frame_args(0)],
                            "label": str(k),
                            "method": "animate",
                        }
                        for k, f in enumerate(fig.frames)
                    ],
                }
            ]

    # Layout
    fig.update_layout(
             title=title,
             width=600,
             height=600,
             scene=dict(
                        xaxis=dict(range=[h_min-abs(hlen)*0.05, h_max+abs(hlen)*0.05], autorange=False),
                        yaxis=dict(range=[k_min-abs(klen)*0.05, k_max+abs(klen)*0.05], autorange=False),
                        zaxis=dict(range=[l_min-abs(llen)*0.05, l_max+abs(llen)*0.05], autorange=False),
                        aspectratio=dict(x=1, y=1, z=1),
                        xaxis_title='H',
                        yaxis_title='K',
                        zaxis_title='L'
                        ),
             updatemenus = [
                {
                    "buttons": [
                        {
                            "args": [None, frame_args(50)],
                            "label": "&#9654;", # play symbol
                            "method": "animate",
                        },
                        {
                            "args": [[None], frame_args(0)],
                            "label": "&#9724;", # pause symbol
                            "method": "animate",
                        },
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 70},
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                }
             ],
             sliders=sliders
    )

    fig.show()
    return None

def h_slice(grid_data, coords, logscale = False, dichro = False, title = None, start = 0, cscale = [50, 99]):
    # With the exported intensity grid points and h,k,l list, show h_slices.
    # logscale: show in log color scale.
    # dichro: whether this is a dichroic signal, if yes, the color scale is from (-cmax, +cmax)
    # title: string for figure title
    # start: int, the starting frame number
    # cscale: defalt [50, 99] set color scale corresponding to 50% and 99% intensity level.
    if logscale:
        volume = np.log(grid_data)
    else:
        volume = grid_data
    r, c = len(coords[1]), len(coords[2])
    
    h_min,h_max = [coords[0][0], coords[0][-1]]
    k_min,k_max = [coords[1][0], coords[1][-1]]
    l_min,l_max = [coords[2][0], coords[2][-1]]
    hlen = h_max-h_min
    klen = k_max-k_min
    llen = l_max-l_min
    
    if dichro:
        cmap = 'RdBu'
        cmin, cmax = np.nanpercentile(abs(volume), cscale)
        cmin = -cmax
    else:
        cmin, cmax = np.nanpercentile(volume, cscale)
        cmap = 'viridis'
        cmin = 0

    nb_frames = len(coords[0])
    xx,zz = np.meshgrid(coords[1],coords[2])
    # print(np.shape(xx), np.shape(zz),np.shape(volume[0,1,:]))

    fig = go.Figure(frames=[go.Frame(data=go.Surface(
        x=(h_min + k/len(coords[0]) * hlen) * np.ones((r, c)),
        surfacecolor=(volume[k,:,:]),
        cmin=cmin, cmax=cmax, 
        y = xx.T,#coords[2], 
        z= zz.T#coords[0]
        ),
        name=str(k) # you need to name the frame for the animation to behave properly
        )
        for k in range(nb_frames)])

    # Add data to be displayed before animation starts
    fig.add_trace(go.Surface(
        x=(h_min + start/len(coords[0]) * hlen) * np.ones((r, c)),
        surfacecolor=(volume[start,:,:]),
        colorscale=cmap,
        cmin=cmin, cmax=cmax,
        colorbar=dict(thickness=20, ticklen=4), 
        y = xx.T,#coords[2], 
        z= zz.T #coords[0]
        ))

    def frame_args(duration):
        return {
                "frame": {"duration": duration},
                "mode": "immediate",
                "fromcurrent": True,
                "transition": {"duration": duration, "easing": "linear"},
            }

    sliders = [
                {
                    "pad": {"b": 10, "t": 60},
                    "len": 0.9,
                    "x": 0.1,
                    "y": 0,
                    "steps": [
                        {
                            "args": [[f.name], frame_args(0)],
                            "label": str(k),
                            "method": "animate",
                        }
                        for k, f in enumerate(fig.frames)
                    ],
                }
            ]

    # Layout
    fig.update_layout(
             title=title,
             width=600,
             height=600,
             scene=dict(
                        xaxis=dict(range=[h_min-abs(hlen)*0.05, h_max+abs(hlen)*0.05], autorange=False),
                        yaxis=dict(range=[k_min-abs(klen)*0.05, k_max+abs(klen)*0.05], autorange=False),
                        zaxis=dict(range=[l_min-abs(llen)*0.05, l_max+abs(llen)*0.05], autorange=False),
                        aspectratio=dict(x=1, y=1, z=1),
                        xaxis_title='H',
                        yaxis_title='K',
                        zaxis_title='L'
                        ),
             updatemenus = [
                {
                    "buttons": [
                        {
                            "args": [None, frame_args(50)],
                            "label": "&#9654;", # play symbol
                            "method": "animate",
                        },
                        {
                            "args": [[None], frame_args(0)],
                            "label": "&#9724;", # pause symbol
                            "method": "animate",
                        },
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 70},
                    "type": "buttons",
                    "x": 0.1,
                    "y": 0,
                }
             ],
             sliders=sliders
    )

    fig.show()
    return None

def make_gif(frame_folder):
    # create gif from pictures in the folder
    frames = [Image.open(image) for image in glob.glob(f"{frame_folder}*.png")]
    frame_one = frames[0]
    frame_one.save(frame_folder+".gif", format="GIF", append_images=frames,
               save_all=True, duration=100, loop=0)
    path = os.getcwd()
    print('Gif created in '+ path +'/'+ frame_folder+".gif")
    return None

def k_slice_gif(grid_data, coords, file_name, 
                logscale = False, dichro = False, cscale = [50, 99], start = 0, title = ''):
    # With the exported intensity grid points and h,k,l list, show l_slices.
    # logscale: show in log color scale.
    # dichro: whether this is a dichroic signal, if yes, the color scale is from (-cmax, +cmax)
    # title: string for figure title
    # start: int, the starting frame number
    # cscale: defalt [50, 99] set color scale corresponding to 50% and 99% intensity level.

    if logscale:
        volume = np.log(grid_data)
    else:
        volume = grid_data
    r, c = len(coords[0]), len(coords[2])
    
    h_min,h_max = [coords[0][0], coords[0][-1]]
    k_min,k_max = [coords[1][0], coords[1][-1]]
    l_min,l_max = [coords[2][0], coords[2][-1]]
    hlen = h_max-h_min
    klen = k_max-k_min
    llen = l_max-l_min
    
    
    if dichro:
        cmap = 'RdBu'
        cmin, cmax = np.nanpercentile(abs(volume), cscale)
        cmin = -cmax
    else:
        cmin, cmax = np.nanpercentile(volume, cscale)
        cmap = 'viridis'
        cmin = 0


    nb_frames = len(coords[1])
    xx,zz = np.meshgrid(coords[0],coords[2])
    
    def plot(k):
        fig = go.Figure()
        fig.add_trace(go.Surface(
            y=(k_min + k/len(coords[1]) * klen) * np.ones((r, c)),
            surfacecolor=(volume[:,k,:]),
            cmin=cmin, cmax=cmax, 
            x = xx.T,        z= zz.T
            )    )
        # Layout
        fig.update_layout(
                 title=title,
                 width=600,
                 height=600,
                 scene=dict(
                            xaxis=dict(range=[h_min-abs(hlen)*0.05, h_max+abs(hlen)*0.05], autorange=False),
                            yaxis=dict(range=[k_min-abs(klen)*0.05, k_max+abs(klen)*0.05], autorange=False),
                            zaxis=dict(range=[l_min-abs(llen)*0.05, l_max+abs(llen)*0.05], autorange=False),
                            aspectratio=dict(x=1, y=1, z=1),
                            xaxis_title='H',
                            yaxis_title='K',
                            zaxis_title='L'
                            )
        )
        return fig

    for ii in range(len(coords[1])):
        frame = plot(ii)
        frame.write_image("image_export\\"+file_name+'_'+str(ii).zfill(2)+".png")

    make_gif('image_export/'+file_name)
    
    return None

def h_slice_gif(grid_data, coords, file_name, 
                logscale = False, dichro = False, cscale = [50, 99], start = 0, title = ''):

    if logscale:
        volume = np.log(grid_data)
    else:
        volume = grid_data
    r, c = len(coords[1]), len(coords[2])
    
    h_min,h_max = [coords[0][0], coords[0][-1]]
    k_min,k_max = [coords[1][0], coords[1][-1]]
    l_min,l_max = [coords[2][0], coords[2][-1]]
    hlen = h_max-h_min
    klen = k_max-k_min
    llen = l_max-l_min
    
    if dichro:
        cmap = 'RdBu'
        cmin, cmax = np.nanpercentile(abs(volume), cscale)
        cmin = -cmax
    else:
        cmin, cmax = np.nanpercentile(volume, cscale)
        cmap = 'viridis'
        cmin = 0

    nb_frames = len(coords[0])
    xx,zz = np.meshgrid(coords[1],coords[2])
    
    def plot(k):
        fig = go.Figure()
        fig.add_trace(go.Surface(
            x=(h_min + k/len(coords[0]) * hlen) * np.ones((r, c)),
            surfacecolor=(volume[k,:,:]),
            cmin=cmin, cmax=cmax, 
            y = xx.T,        z= zz.T
            )    )
        # Layout
        fig.update_layout(
                 title=title,
                 width=600,
                 height=600,
                 scene=dict(
                            xaxis=dict(range=[h_min-abs(hlen)*0.05, h_max+abs(hlen)*0.05], autorange=False),
                            yaxis=dict(range=[k_min-abs(klen)*0.05, k_max+abs(klen)*0.05], autorange=False),
                            zaxis=dict(range=[l_min-abs(llen)*0.05, l_max+abs(llen)*0.05], autorange=False),
                            aspectratio=dict(x=1, y=1, z=1),
                            xaxis_title='H',
                            yaxis_title='K',
                            zaxis_title='L'
                            )
        )
        return fig

    for ii in range(len(coords[1])):
        frame = plot(ii)
        frame.write_image("image_export\\"+file_name+'_'+str(ii).zfill(2)+".png")

    make_gif('image_export/'+file_name)
    
    return None

def l_slice_gif(grid_data, coords, file_name, 
                logscale = False, dichro = False, cscale = [50, 99], start = 0, title = ''):

    if logscale:
        volume = np.log(grid_data)
    else:
        volume = grid_data
    r, c = len(coords[0]), len(coords[1])
    
    h_min,h_max = [coords[0][0], coords[0][-1]]
    k_min,k_max = [coords[1][0], coords[1][-1]]
    l_min,l_max = [coords[2][0], coords[2][-1]]
    hlen = h_max-h_min
    klen = k_max-k_min
    llen = l_max-l_min
    
    if dichro:
        cmap = 'RdBu'
        cmin, cmax = np.nanpercentile(abs(volume), cscale)
        cmin = -cmax
    else:
        cmin, cmax = np.nanpercentile(volume, cscale)
        cmap = 'viridis'
        cmin = 0

    nb_frames = len(coords[2])
    xx,zz = np.meshgrid(coords[0],coords[1])
    
    def plot(k):
        fig = go.Figure()
        fig.add_trace(go.Surface(
            z=(l_min + k/len(coords[2]) * llen) * np.ones((r, c)),
            surfacecolor=(volume[:,:,k]),
            cmin=cmin, cmax=cmax, 
            x = xx.T,        y= zz.T
            )    )
        # Layout
        fig.update_layout(
                 title=title,
                 width=600,
                 height=600,
                 scene=dict(
                            xaxis=dict(range=[h_min-abs(hlen)*0.05, h_max+abs(hlen)*0.05], autorange=False),
                            yaxis=dict(range=[k_min-abs(klen)*0.05, k_max+abs(klen)*0.05], autorange=False),
                            zaxis=dict(range=[l_min-abs(llen)*0.05, l_max+abs(llen)*0.05], autorange=False),
                            aspectratio=dict(x=1, y=1, z=1),
                            xaxis_title='H',
                            yaxis_title='K',
                            zaxis_title='L'
                            )
        )
        return fig

    for ii in range(len(coords[1])):
        frame = plot(ii)
        frame.write_image("image_export\\"+file_name+'_'+str(ii).zfill(2)+".png")

    make_gif('image_export/'+file_name)
    
    return None


def save_vtk(array: np.ndarray, coords, path) -> str:
    """Converts and saves numpy array to VTK image data."""

    directory_name = 'vtk_export'
    try:
        os.mkdir(directory_name)
        print(f"Directory '{directory_name}' created successfully.")
    except FileExistsError:
        pass

    data_array = numpy_support.numpy_to_vtk(array.flatten(order="F"))
    image_data = vtk.vtkImageData()

    qx_0, qy_0, qz_0 = coords[0][0], coords[1][0], coords[2][0]
    del_qx = coords[0][1] - coords[0][0]
    del_qy = coords[1][1] - coords[1][0]
    del_qz = coords[2][1] - coords[2][0]

    image_data.SetOrigin(qx_0, qy_0, qz_0)
    image_data.SetSpacing(del_qx, del_qy, del_qz)
    image_data.SetDimensions(*array.shape)

    image_data.GetPointData().SetScalars(data_array)

    writer = vtk.vtkXMLImageDataWriter()
    writer.SetFileName("vtk_export\\" + path + '.vti')
    writer.SetInputData(image_data)
    writer.Write()
    
def load_vtk(path):
    """
    Reads a VTK image data (.vti) file and converts it back to a numpy array with coordinate information.
    
    Parameters:
    -----------
    path : str
        Path to the .vti file
        
    Returns:
    --------
    tuple
        (array, coords) where:
        - array is the numpy array with the data
        - coords is a list of three numpy arrays representing x, y, z coordinates
    """
    # Create a reader for XML image data files
    reader = vtk.vtkXMLImageDataWriter()
    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(path)
    reader.Update()
    
    # Get the image data
    image_data = reader.GetOutput()
    
    # Get the dimensions of the data
    dims = image_data.GetDimensions()
    
    # Get origin and spacing
    origin = image_data.GetOrigin()
    spacing = image_data.GetSpacing()
    
    # Convert VTK data to numpy array
    vtk_data = image_data.GetPointData().GetScalars()
    numpy_data = numpy_support.vtk_to_numpy(vtk_data)
    
    # Reshape the data to match the original dimensions
    # Note: VTK data is stored in Fortran order (column-major)
    array = numpy_data.reshape(dims, order='F')
    
    # Reconstruct the coordinate arrays
    x_coords = np.array([origin[0] + i * spacing[0] for i in range(dims[0])])
    y_coords = np.array([origin[1] + i * spacing[1] for i in range(dims[1])])
    z_coords = np.array([origin[2] + i * spacing[2] for i in range(dims[2])])
    
    coords = [x_coords, y_coords, z_coords]
    
    return array, coords



def rebin(arr, bins):
    """
    Rebin a 3D array by averaging over bins x bins blocks.
    Works for any bin size, not just exact factors.
    
    Parameters:
    arr: 3D numpy array with shape (frames, height, width)
    bins: integer, size of the binning (bins x bins)
    
    Returns:
    Rebinned array with shape (frames, new_height, new_width)
    """
    
    if len(arr.shape) != 3:
        raise ValueError("Array must be 3D with shape (frames, height, width)")
    
    frames, height, width = arr.shape
    
    # Calculate new dimensions
    new_height = height // bins
    new_width = width // bins
    
    # Crop the array to make it divisible by bins
    cropped_height = new_height * bins
    cropped_width = new_width * bins
    
    # Crop the array
    arr_cropped = arr[:, :cropped_height, :cropped_width]
    
    # Reshape and average
    shape = (frames, new_height, bins, new_width, bins)
    reshaped = arr_cropped.reshape(shape)
    
    # Use nanmean to handle NaN values properly
    return np.nanmean(reshaped, axis=(2, 4))