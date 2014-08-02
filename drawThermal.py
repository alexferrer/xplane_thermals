'''
Use mathplot to graph the generated thermal map from a .cvs file
on Xplane's root directory 

'''
from pylab import *
import csv
datafile = "../../../thermal7.csv"  # X Plane root dir 
datafile = "test_columns_thermal.csv"
with open(datafile, "r") as f:
     data = list(map(int,rec) for rec in csv.reader(f, delimiter=','))
     
figure(1)
#print str(data)
data[0][0] = 0
imshow(data, interpolation='nearest')
show()
