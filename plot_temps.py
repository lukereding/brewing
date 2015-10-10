import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
#from scipy.interpolate import spline
import sys

try:
	file = sys.argv[2]
except:
	file = "temps.txt"

try:
	annotation =str(sys.argv[1])
except:
	annotation = ""

temps = np.loadtxt(file)

# sliding window
window_size = int(0.08*temps.shape[0])

if window_size % 2 != 0:
	window_size = window_size + 1

# empty list
averages = []

for i in range(window_size/2, (temps.shape[0] - window_size/2)):
	# calculate the mean in the window
	averages.append(np.mean(temps[i-(window_size/2):i+(window_size/2)]))


# to plot raw data:
plt.plot(range(1,temps.shape[0]+1), temps, color='#3E4A89', alpha=0.6, linewidth = 0.60,label="raw temperature data")
plt.plot(range(window_size/2, (temps.shape[0] - window_size/2)), averages, color='#3E4A89', linewidth = 2.0, label="sliding window average. window size of "+str(window_size))
plt.ylabel("temperature")
plt.xlabel("time")
plt.text(5,min(temps),annotation)
plt.legend(loc='best', fancybox=True,prop={'size':10})
plt.title("raw and smoothed temperature data")
plt.savefig(str(annotation) + ".pdf",bbox_inches='tight',format='pdf')

"""
# number of points for interpolation when smoothing the data:
x_num = 25

# plot a smoothed line
x_smooth = np.linspace(0, temps.shape[0], x_num)
y_smooth = spline(np.asarray(range(0,temps.shape[0])), temps, x_smooth)

#f = interp1d(range(0,len(temps.shape[0])),temps)
#plt.plot(x_smooth,f(x_smooth))

plt.plot(range(0,x_num),y_smooth,'r-',linewidth=1.5)
x1,x2,y1,y2 = plt.axis()
plt.axis((x1,x2,68,80))
plt.xlabel("time")
plt.ylabel("temperature (F)")
plt.title("smoothed temperature data")
plt.savefig("temps_smoothed.png",bbox_inches="tight")
"""
