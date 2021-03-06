from aeropy.geometry.parametric import CoordinateSystem
from aeropy.structural.stable_solution import (properties, boundary_conditions)
from aeropy.structural.shell import shell
from aeropy.xfoil_module import output_reader

from scipy.integrate import quad
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from optimization_tools.DOE import DOE
import pickle

def input_function(x):
    return np.array([0,0] + list(x))

def find_chord(P):
    def _to_minimize(l):
        def _to_integrate(y):
            den = np.sqrt(1-P**2/E**2/I**2*(l*y-y**2/2)**2)
            if np.isnan(den):
                return 100
            else:
                return 1/den
        l = l[0]
        current_L = quad(_to_integrate, 0, l)[0]
        return abs(L-current_L)
        
    return minimize(_to_minimize, L, method = 'Nelder-Mead',).x[0]

def find_deflection(y, l, P):
    def _to_integrate(y):
        num = P/E/I*(l*y-y**2/2)
        den = np.sqrt(1-P**2/E**2/I**2*(l*y-y**2/2)**2)
        if np.isnan(den):
            return 100
        else:
            return num/den
    
    x = []
    for y_i in y:
        x_i = current_L = quad(_to_integrate, 0, y_i)[0]
        x.append(x_i)
    return x
    
np.set_printoptions(precision=5)

# Results from Abaqus
abaqus_data = pickle.load(open('neutral_line.p', 'rb'))

# Beam properties
bp = properties()
bc = boundary_conditions(concentrated_load=np.array([[0.0, 0.0, -1.0], ]))
EB_solution = bc.concentrated_load[0][2]/(6*bp.young*bp.inertia) * \
    np.array([0, 0, 3, -1])

curve_parent = CoordinateSystem.polynomial(D=[0, 0, 0, 0], chord = 1, color = 'b')
curve_child = CoordinateSystem.polynomial(D=EB_solution, chord = 1, color  ='0.5')

beam = shell(curve_parent, curve_child, bp, bc)
chord_bounds = [[0., 2],]
beam.g_p.bounds = chord_bounds
beam.g_c.bounds = chord_bounds
beam.theta1 = np.linspace(0, beam.g_p.arclength()[0], 10)
beam.update_parent()
beam.update_child()
eulerBernoulle = beam.g_c.r(beam.g_c.x1_grid)

# Find stable solution
bounds = np.array(((-0.02,0.02),
                  (-0.02,0.02)))


beam.minimum_potential(x0=[0,0], input_function = lambda x: [0,0] + list(x),
                       bounds = bounds)




P = -1
E = bp.young
L = 1
I = bp.inertia
chord = find_chord(P)
beam_chen_x = np.linspace(0,chord,10)
beam_chen_y = find_deflection(beam_chen_x, chord, P)

[x,y,z] = eulerBernoulle.T
beam.g_p.plot(label='Parent')
plt.plot(x,z, 'k', lw = 3, label='Euler-Bernoulle', linestyle = '-', zorder=0)
beam.g_c.plot(label='Child', linestyle = '--')
plt.plot(beam_chen_x, beam_chen_y, 'r', label='Chen', linestyle = '--', lw = 3)
plt.scatter(abaqus_data['coord'][0:401:40,0], abaqus_data['coord'][0:401:40,1], c='g', label='FEA', edgecolors='k', zorder = 10)
plt.legend()
plt.show()

# Plot beam results
plt.figure()
u = beam.u()
u1 = beam.u(diff='x1')
u2 = beam.u(diff='x2')
plt.plot(beam.r_p[0], beam.r_p[1], label='parent')
plt.scatter(beam.r_p[0], beam.r_p[1], label='parent')
plt.plot(beam.r_c[0], beam.r_c[1], label='child')
plt.scatter(beam.r_c[0], beam.r_c[1], label='child')
plt.plot(eulerBernoulle[0], eulerBernoulle[1], label='Euler-Bernoulle')
plt.scatter(eulerBernoulle[0], eulerBernoulle[1], label='Euler-Bernoulle')
plt.plot(abaqus_data['coord'][:,0], abaqus_data['coord'][:,1], label='Abaqus')
plt.title('Position')
plt.grid()
plt.legend()


