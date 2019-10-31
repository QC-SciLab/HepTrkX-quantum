import matplotlib.pyplot as plt 
import numpy as np
import csv

log_location = 'logs/bce/lr_1/'
png_location = 'png/bce/lr_1/'
with open(log_location + 'log_loss.csv', 'r') as f:
	reader = csv.reader(f, delimiter=',')
	loss = np.array(list(reader)).astype(float)
with open(log_location+'log_validation.csv', 'r') as f:
	reader = csv.reader(f, delimiter=',')
	valid = np.array(list(reader)).astype(float) * 100
with open(log_location+'log_theta.csv','r') as f:
	reader = csv.reader(f, delimiter=',')
	theta = np.delete(np.array(list(reader)[:-2]),11,1).astype(float) 
# Plot
plt.clf()   
x = [(i+1) for i  in range(len(loss))]
plt.plot(x[1:],loss[1:],marker='o')
plt.xlabel('Update')
plt.ylabel('Loss')
plt.savefig(png_location+'statistics_loss.pdf')

plt.clf()   
interval = 50
x = [i*interval for i  in range(len(loss)//interval)]
average_loss = [sum(loss[i*interval:(i+1)*interval])/interval for i in range(len(x))]
plt.plot(x,average_loss,marker='o')
plt.xlabel('Update')
plt.ylabel('Loss')
plt.savefig(png_location+'statistics_average_loss.pdf')

plt.clf()   
x = [i*50 for i  in range(len(valid))]
plt.plot(x,valid,marker='o')
plt.xlabel('Update')
plt.ylabel('Accuracy')
plt.savefig(png_location+'statistics_validation.pdf')

plt.clf()
x = [(i+1) for i in range(len(theta))]
for i in range(11):
	plt.plot(x,theta[:,i],marker='o',label=r'$\theta_{'+str(i)+'}$')
plt.xlabel('Update')
plt.ylabel(r'Angle (0 - 2$\pi$)')
plt.savefig(png_location+'statistics_angle.pdf')
"""
# Comparison plot
plt.clf()   
interval = 50
x = [i*interval for i  in range(len(loss)//interval)]
with np.load('logs/summaries.npz') as data:
	classical_loss = data['train_loss'][:len(loss)//(interval*3)]
average_loss = [sum(loss[i*interval:(i+1)*interval])/interval for i in range(len(x))]
plt.plot(x,average_loss,marker='o',label='QuantumEdgeNetwork',c='r')
xx = [i*interval*3 for i  in range(len(classical_loss))]
plt.plot(xx,classical_loss,marker='o',label='ClassicalEdgeNetwork',c='b')
plt.xlabel('Update')
plt.ylabel('Loss')
plt.legend()
plt.savefig(png_location+'statistics_comparison_loss.png')
"""