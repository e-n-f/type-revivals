# Curve fitting from e-n-f/highway-61-revisited (highway61/work/vec.py).
import numpy as np,cv2
# ---------- Schneider cubic fitting ----------
def bez(ctrl,t):
    t=np.asarray(t)[:,None]; mt=1-t
    return mt**3*ctrl[0]+3*mt**2*t*ctrl[1]+3*mt*t**2*ctrl[2]+t**3*ctrl[3]
def bezd(ctrl,t):
    t=np.asarray(t)[:,None]; mt=1-t
    return 3*mt**2*(ctrl[1]-ctrl[0])+6*mt*t*(ctrl[2]-ctrl[1])+3*t**2*(ctrl[3]-ctrl[2])
def bezdd(ctrl,t):
    t=np.asarray(t)[:,None]
    return 6*(1-t)*(ctrl[2]-2*ctrl[1]+ctrl[0])+6*t*(ctrl[3]-2*ctrl[2]+ctrl[1])
def chord_param(P):
    d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
    return d/d[-1]
def gen_bez(P,u,t1,t2):
    p0,p3=P[0],P[-1]
    A1=u[:,None]*0+ (3*(1-u)**2*u)[:,None]*t1
    A2=(3*(1-u)*u**2)[:,None]*t2
    C=np.zeros((2,2)); X=np.zeros(2)
    C[0,0]=(A1*A1).sum(); C[0,1]=C[1,0]=(A1*A2).sum(); C[1,1]=(A2*A2).sum()
    B=((1-u)**3+3*(1-u)**2*u)[:,None]*p0+(3*(1-u)*u**2+u**3)[:,None]*p3
    tmp=P-B
    X[0]=(A1*tmp).sum(); X[1]=(A2*tmp).sum()
    det=C[0,0]*C[1,1]-C[0,1]**2
    seg=np.linalg.norm(p3-p0)
    if abs(det)>1e-9:
        a1=(X[0]*C[1,1]-X[1]*C[0,1])/det; a2=(C[0,0]*X[1]-C[0,1]*X[0])/det
    else: a1=a2=seg/3
    if a1<seg*0.05 or a2<seg*0.05 or a1>seg*0.75 or a2>seg*0.75: a1=a2=seg/3
    return np.array([p0,p0+t1*a1,p3+t2*a2,p3])
def reparam(ctrl,P,u):
    d=bez(ctrl,u)-P; d1=bezd(ctrl,u); d2=bezdd(ctrl,u)
    num=(d*d1).sum(1); den=(d1*d1+d*d2).sum(1)
    with np.errstate(divide='ignore',invalid='ignore'):
        nu=np.where(np.abs(den)>1e-9,u-num/den,u)
    return np.clip(nu,0,1)
def maxerr(ctrl,P,u):
    e=np.linalg.norm(bez(ctrl,u)-P,axis=1); i=int(np.argmax(e)); return e[i],i
def unit(v):
    n=np.linalg.norm(v); return v/n if n>1e-9 else v
def fit(P,t1,t2,err,out):
    if len(P)==2:
        d=np.linalg.norm(P[1]-P[0])/3; out.append(np.array([P[0],P[0]+t1*d,P[1]+t2*d,P[1]])); return
    u=chord_param(P)
    ctrl=gen_bez(P,u,t1,t2); e,i=maxerr(ctrl,P,u)
    if e<err: out.append(ctrl); return
    if e<err*4:
        for _ in range(6):
            u=reparam(ctrl,P,u); ctrl=gen_bez(P,u,t1,t2); e,i=maxerr(ctrl,P,u)
            if e<err: out.append(ctrl); return
    i=max(1,min(len(P)-2,i))
    tc=unit(P[i-1]-P[i+1])
    fit(P[:i+1],t1,tc,err,out); fit(P[i:],-tc,t2,err,out)
# ---------- contour processing ----------
def resample(C,step):
    C=np.vstack([C,C[:1]])
    d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(C,axis=0),axis=1))]
    n=max(8,int(d[-1]/step))
    s=np.linspace(0,d[-1],n,endpoint=False)
    return np.c_[np.interp(s,d,C[:,0]),np.interp(s,d,C[:,1])]
def corners(P,k=7,ang=55):
    n=len(P); idx=np.arange(n)
    a=P-P[(idx-k)%n]; b=P[(idx+k)%n]-P
    cosang=(a*b).sum(1)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)+1e-9)
    turn=np.degrees(np.arccos(np.clip(cosang,-1,1)))
    cs=[]
    for i in range(n):
        if turn[i]>ang and turn[i]>=max(turn[(i+j)%n] for j in range(-k,k+1)):
            if not cs or i-cs[-1]>k: cs.append(i)
    return cs
LTOL=1.1; ERR=2.5; MINRUN=110
def linedev(Q):
    a,b=Q[0],Q[-1]; d=b-a; L=np.hypot(*d)
    if L<1e-6: return 1e9
    return np.max(np.abs(d[0]*(Q[:,1]-a[1])-d[1]*(Q[:,0]-a[0])))/L
def find_runs(seg):
    n=len(seg); runs=[]; i=0
    while i<n-2:
        j=i+2
        if linedev(seg[i:j+1])>LTOL: i+=1; continue
        while j+1<n and linedev(seg[i:j+2])<=LTOL: j+=1
        if np.hypot(*(seg[j]-seg[i]))>=MINRUN: runs.append((i,j)); i=j
        else: i+=1
    return runs
def contour_segments(P,err=None):
    err=err or ERR
    n=len(P)
    cs=corners(P)
    closed_smooth=not cs
    if closed_smooth:
        i0=int(np.argmax(P[:,1])); P=np.roll(P,-i0,axis=0); cs=[0]
    cs=sorted(cs); out=[]
    for j,c in enumerate(cs):
        c2=cs[(j+1)%len(cs)]
        if c2<=c: c2+=n
        seg=P[np.arange(c,c2+1)%n]
        if len(seg)<2: continue
        runs=find_runs(seg)
        # pieces: alternate curve/line
        pos=0; prev_dir=None
        pieces=[]
        for (a,b) in runs:
            if a>pos: pieces.append(('c',pos,a))
            pieces.append(('l',a,b)); pos=b
        if pos<len(seg)-1: pieces.append(('c',pos,len(seg)-1))
        for k,(t,a,b) in enumerate(pieces):
            Q=seg[a:b+1]
            if t=='l': out.append(('L',Q[0],Q[-1])); continue
            if len(Q)<3 or linedev(Q)<LTOL:
                out.append(('L',Q[0],Q[-1])); continue
            m=min(4,len(Q)-1)
            # tangents: from adjacent line pieces if any, else local / closed-smooth
            if k>0 and pieces[k-1][0]=='l':
                pa,pb=pieces[k-1][1],pieces[k-1][2]; t1=unit(seg[pb]-seg[pa])
            elif closed_smooth and a==0 and k==0: t1=unit(seg[1]-seg[-2])
            else: t1=unit(Q[m]-Q[0])
            if k+1<len(pieces) and pieces[k+1][0]=='l':
                pa,pb=pieces[k+1][1],pieces[k+1][2]; t2=unit(seg[pa]-seg[pb])
            elif closed_smooth and k==len(pieces)-1: t2=unit(seg[-2]-seg[1]) if False else -unit(seg[1]-seg[-2])
            else: t2=unit(Q[-1-m]-Q[-1])
            cub=[]; fit(Q,t1,t2,err,cub)
            for cc in cub: out.append(('C',)+tuple(cc))
    return out
