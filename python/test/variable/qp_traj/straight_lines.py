
import cvxpy as cp
from numpy.random import randn
from numpy import eye, ones, zeros, array
eps =0.000001


degree = 3
n = degree
nvars = degree+1
dim = 3
rdim = 2

#find the minimum time sequence of straight lines connecting from start to end position along union of convex sets

def solve_straight_lines(Pis, V, x_start = None, x_end = None): #TODO: add V and A    
    num_phases = len(Pis)
    num_vars = nvars * num_phases
    x   = [cp.Variable(rdim) for i in range(num_vars)] 
    tis = [cp.Variable(1) for i in range(num_phases)]
    
    constraints = []
    
    for j in range(len(Pis)):
        idx = j*nvars
        Pi = Pis[j]
        P    = Pi[0][:,:rdim]       ; p  = Pi  [1]
        Vn   = V[0][:,:rdim]*n        ; v = V[1]
        ti = tis[j]
        constraints = constraints + [
        #~ ti >= 0.0001,
        #positions
        P*(x[idx]) <= p,
        P*(x[idx+3]) <= p,
        P*(x[idx] + x[idx+1]) <= p,
        P*(x[idx+3] - x[idx+2]) <= p,
        #zero start/end velocities
        x[idx+1] == zeros(rdim),
        x[idx+2] == zeros(rdim),
        #velocities
        Vn*x[idx+1] <= v * ti,
        Vn*x[idx+2] <= v * ti,
        Vn*(x[idx+3]-x[idx+2]-x[idx+1]-x[idx]) <= v * ti,
        ]
        
    #continuity constraints
    for j in range(1,len(Pis)):
        idx = j*nvars
        constraints = constraints + [
        x[idx] == x[idx-1] #just positions because velocities at 0
        ]
            
    if x_start is not None:
        constraints = constraints + [x[0]  == x_start[:rdim]]
    if x_end is not None:
        constraints = constraints + [x[-1]  == x_end[:rdim]]
    
    obj = cp.Minimize(sum(tis))
    prob = cp.Problem(obj, constraints)
    prob.solve(solver="ECOS",verbose=False)
    return prob, tovals(x), tovals(tis)
    
    

def bezierFromVal(xis, ti):
    wps = zeros((len(xis),dim))
    wps[0,:rdim] = array(xis[0])
    wps[1,:rdim] = wps[0,:rdim] + array(xis[1])
    wps[3,:rdim] = array(xis[3])
    wps[2,:rdim] = wps[3,:rdim] - array(xis[2])
    
    return bezier(wps.transpose(), ti)
    
def bezierFromValAcc(xis, ti):
    wps = zeros((len(xis),dim))
    for i in range(3):
        wps[i,:rdim] = array(xis[0])
    for i in range(3,6):
        wps[i,:rdim] = array(xis[-1])    
    return bezier(wps.transpose(), ti)
    
def min_time(xs,V):
    b = bezierFromValAcc(xs, 1)
    wps = b.compute_derivate(1).waypoints()
    t = cp.Variable(1) 
    constraints = [ t >= 0.00001]
    for i in range(wps.shape[1]):
        #~ if (np.linalg.norm(wps[:2,i]) > 0.01):
        constraints = constraints + [ V[0].dot(wps[:2,i]) <= V[1] *t ]
    obj = cp.Minimize(t)
    prob = cp.Problem(obj, constraints)
    prob.solve(solver="ECOS",verbose=False)
    return t.value[0]
    
    
def add_acc(xs,ts,nphase, V):
    xis_rec = []
    for i in range(nphase):
        xis = xs[i*4:i*4+4]
        xis = [xis[0], xis[0], xis[0]] + [xis[-1], xis[-1], xis[-1]]
        ti = min_time(xis, V)
        xis_rec = xis_rec + xis
        ts[i] = ti
    return xis_rec, ts


from hpp_spline import bezier


def tovals(variables):
    return [el.value for el in variables]

    

from  cord_methods import *
from  plot_cord import *

def boundIneq():
    v = ones(4)*1.; #v[:-3] = -v[3:]
    V = zeros((4,2)); 
    V[:2,:] = identity(2); 
    V[2:,:] =-identity(2); 
    return (V, v)

if __name__ == '__main__':
    
        
    def one(nphase=2):
        plt.close()
        pDef, inequalities_per_phase = genProblemDef(6,nphase)
        V = boundIneq()
        x_start = pDef.start.reshape((-1,))
        x_end = pDef.end.reshape((-1,))

        prob, xis, tis = solve_straight_lines(inequalities_per_phase[:], V, x_start=x_start, x_end=x_end)
        
        #~ print "times", tis
        for i in range(len(tis)):
            ti = abs(tis[i][0])
            b = bezierFromVal(xis[i*4:i*4+4], abs(ti))
            plotBezier(b, colors[i], label = None, linewidth = 3.0)
            plotControlPoints(b, colors[i],linewidth=2)
        
        #~ print "tis,", tis
        
        xis, tis = add_acc(xis,tis,nphase,V)
        
        #~ print "tis,", tis
        
        tis = addSplit(tis)
        lastval = tis[-1]
        tis = [el / lastval for el in tis[:-1]]  
        #~ print "tis ", tis
        pDef.splits = array([tis]).T 
        res, cos = computeTrajectory(pDef, saveToFile=False)
        plot(pDef,res, "", saveToFile=False)
        
        plt.show()
        
        #~ plt.show()
        return b, tis
        
    b, tis = one(2)
    