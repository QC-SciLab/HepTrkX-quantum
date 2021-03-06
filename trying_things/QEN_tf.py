#!/usr/bin/python
# Author: Cenk Tuysuz
# Date: 29.08.2019
# First attempt to test QuantumEdgeNetwork
# Run this code the train and test the network

import numpy as np
import matplotlib.pyplot as plt
from qiskit import *
from datasets.hitgraphs import get_datasets
import sys, time, datetime
import multiprocessing
import tensorflow as tf
import csv

def TTN_edge_forward(edge,theta_learn):
	# Takes the input and learning variables and applies the
	# network to obtain the output
	q       = QuantumRegister(len(edge))
	c       = ClassicalRegister(1)
	circuit = QuantumCircuit(q,c)
	# STATE PREPARATION
	for i in range(len(edge)):
		circuit.ry(edge[i],q[i])
	# APPLY forward sequence
	circuit.ry(theta_learn[0],q[0])
	circuit.ry(theta_learn[1],q[1])
	circuit.cx(q[0],q[1])
	circuit.ry(theta_learn[2],q[2])
	circuit.ry(theta_learn[3],q[3])
	circuit.cx(q[2],q[3])
	circuit.ry(theta_learn[4],q[4])
	circuit.ry(theta_learn[5],q[5])
	circuit.cx(q[5],q[4]) # reverse the order
	circuit.ry(theta_learn[6],q[1])
	circuit.ry(theta_learn[7],q[3])
	circuit.cx(q[1],q[3])
	circuit.ry(theta_learn[8],q[3])
	circuit.ry(theta_learn[9],q[4])
	circuit.cx(q[3],q[4])
	circuit.ry(theta_learn[10],q[4])
	# Qasm Backend
	circuit.measure(q[4],c)
	backend = Aer.get_backend('qasm_simulator')
	result = execute(circuit, backend, shots=1000).result()
	counts = result.get_counts(circuit)
	out    = 0
	for key in counts:
		if key=='1':
			out = counts[key]/1000
	return(out)
def TTN_edge_back(input_,theta_learn):
	# This function calculates the gradients for all learning 
	# variables numerically and updates them accordingly.
	epsilon = np.pi/2 # to take derivative
	gradient = np.zeros(len(theta_learn))
	update = np.zeros(len(theta_learn))
	for i in range(len(theta_learn)):
		## Compute f(x+epsilon)
		theta_learn[i] = (theta_learn[i] + epsilon)%(2*np.pi)
		## Evaluate
		out_plus = TTN_edge_forward(input_,theta_learn)
		## Compute f(x-epsilon)
		theta_learn[i] = (theta_learn[i] - 2*epsilon)%(2*np.pi)
		## Evaluate
		out_minus = TTN_edge_forward(input_,theta_learn)
		# Compute the gradient numerically
		gradient[i] = (out_plus-out_minus)/2
		## Bring theta to its original value
		theta_learn[i] = (theta_learn[i] + epsilon)%(2*np.pi)
	return gradient
def map2angle(B):
	# Maps input features to 0-2PI
	r_min     = 0.
	r_max     = 1.
	phi_min   = -1.
	phi_max   = 1.
	z_min     = 0.
	z_max     = 1.2
	B[:,0] =  (B[:,0]-r_min)/(r_max-r_min) * 2 * np.pi 
	B[:,1] =  (B[:,1]-phi_min)/(phi_max-phi_min) * 2 * np.pi 
	B[:,2] =  (B[:,2]-z_min)/(z_max-z_min) * 2 * np.pi 
	B[:,3] =  (B[:,3]-r_min)/(r_max-r_min) * 2 * np.pi 
	B[:,4] =  (B[:,4]-phi_min)/(phi_max-phi_min) * 2 * np.pi 
	B[:,5] =  (B[:,5]-z_min)/(z_max-z_min)* 2 * np.pi 
	return B
def MSE(output,label):
	return (output-label)**2
def binary_cross_entropy(output,label):
	return -(label*np.log(output+1e-6) + (1-label)*np.log(1-output+1e-6))
def loss_fn(outputs,label,pos_weight):
	loss_tensor =  tf.nn.weighted_cross_entropy_with_logits(labels=tf.Variable(label,tf.float64),logits=tf.Variable(outputs,tf.float64),pos_weight=pos_weight)
	print(tf.math.reduce_mean(loss_tensor))
	return tf.math.reduce_mean(loss_tensor)
def get_loss_and_gradient(edge_array,label,theta_learn,class_weight,loss_array,gradient_array,update_array):
	local_gradient = np.zeros(len(theta_learn))
	local_update   = np.zeros(len(theta_learn))
	outputs = []
	for i in range(len(edge_array)):
		output         = TTN_edge_forward(edge_array[i],theta_learn)
		outputs.append(output)
		error          = output - label[i]
		gradient       = TTN_edge_back(edge_array[i],theta_learn)*class_weight[int(label[i])]
		local_gradient += gradient
		local_update   += 2*error*gradient
	#loss_tensor = tf.nn.weighted_cross_entropy_with_logits(labels=tf.Variable(y,tf.float64),logits=tf.Variable(outputs,tf.float64),pos_weight=class_weight[1])
	#local_loss    = tf.math.reduce_mean(loss_tensor)
	#w = tf.Variable([[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0]], trainable=True, dtype=tf.float64)
	with tf.GradientTape() as tape:
		tape.watch(w)
		local_loss = loss_fn(outputs,label,class_weight[1])
	gradients = tape.gradient(tf.Variable(local_loss,tf.float64),w)
	print(gradients)
	adam.apply_gradients(zip(gradients,w))
	print(w)
	loss_array.append(local_loss)
	gradient_array.append(local_gradient)
	update_array.append(local_update)
def get_accuracy(edge_array,y,theta_learn,class_weight,acc_array):
	total_acc = 0.
	for i in range(len(edge_array)):
		total_acc += (1 - abs(TTN_edge_forward(edge_array[i],theta_learn) - y[i]))*class_weight[int(y[i])] 
	acc_array.append(total_acc)
def train(edges,theta_learn,labels):
	jobs         = []
	n_edges      = len(labels)
	n_feed       = n_edges//n_threads
	n_class      = [n_edges - sum(labels), sum(labels)]
	class_weight = [n_edges/(n_class[0]*2), n_edges/(n_class[1]*2)]
	# RESET variables
	manager        = multiprocessing.Manager()
	loss_array     = manager.list()
	gradient_array = manager.list()
	update_array   = manager.list()
	# RUN Multithread training
	for thread in range(n_threads):
		start = thread*n_feed
		end   = (thread+1)*n_feed
		if thread==(n_threads-1):   
			p = multiprocessing.Process(target=get_loss_and_gradient,args=(edges[start:,:],labels[start:],theta_learn,class_weight,loss_array,gradient_array,update_array,))
		else:
			p = multiprocessing.Process(target=get_loss_and_gradient,args=(edges[start:end,:],labels[start:end],theta_learn,class_weight,loss_array,gradient_array,update_array,))   
		jobs.append(p)
		p.start()
	# WAIT for jobs to finish
	for proc in jobs: 
		proc.join()
		#print('Thread ended')
			
	total_gradient = sum(gradient_array)
	total_update   = sum(update_array)
	## UPDATE WEIGHTS
	average_loss     = sum(loss_array)/n_threads
	average_gradient = total_gradient/n_edges
	average_update   = total_update/n_edges
	theta_learn       = (theta_learn - lr*average_update)%(2*np.pi)
	"""
	with open(log_dir+'log_gradients.csv', 'a') as f:
			for item in average_update:
				f.write('%.4f, ' % item)
			f.write('\n')		
	"""
	return theta_learn,average_loss
def test_validation(valid_data,theta_learn,n_valid):
	t_start = time.time()
	print('Starting testing the validation set!')
	jobs         = []
	accuracy = 0.
	for n_test in range(n_valid):
		B,y          = preprocess(valid_data[n_test]) 
		n_edges      = len(y)
		n_feed       = n_edges//n_threads
		n_class      = [n_edges - sum(y), sum(y)]
		class_weight = [n_edges/(n_class[0]*2), n_edges/(n_class[1]*2)]
		# RESET variables
		manager        = multiprocessing.Manager()
		acc_array     = manager.list()
		# RUN Multithread training
		for thread in range(n_threads):
			start = thread*n_feed
			end   = (thread+1)*n_feed
			if thread==(n_threads-1):   
				p = multiprocessing.Process(target=get_accuracy,args=(B[start:,:],y[start:],theta_learn,class_weight,acc_array,))
			else:
				p = multiprocessing.Process(target=get_accuracy,args=(B[start:end,:],y[start:end],theta_learn,class_weight,acc_array,))   
			jobs.append(p)
			p.start()
		# WAIT for jobs to finish
		for proc in jobs: 
			proc.join()
		accuracy += sum(acc_array)/(n_edges * n_valid)
	with open(log_dir+'log_validation.csv', 'a') as f:
				f.write('%.4f\n' % accuracy)
	duration = time.time() - t_start
	print('Validation Accuracy: %.4f, Elapsed: %dm%ds' %(accuracy*100, duration/60, duration%60))
	return accuracy
def preprocess(data):
	X,Ro,Ri,y = data
	X[:,2] = np.abs(X[:,2]) # correction for negative z
	bo    = np.dot(Ro.T, X)
	bi    = np.dot(Ri.T, X)
	B     = np.concatenate((bo,bi),axis=1)
	return map2angle(B), y
############################################################################################
##### MAIN ######
if __name__ == '__main__':
	n_param     = 11
	theta_learn = np.random.rand(n_param)*np.pi*2 #/ np.sqrt(n_param)
	w = tf.Variable([[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0]], trainable=True, dtype=tf.float64)
	input_dir   = 'data/hitgraphs_big'
	log_dir     = 'logs/'  
	n_files     = 16*100
	n_valid     = int(n_files * 0.1)
	n_train     = n_files - n_valid	
	lr          = 1.
	n_epoch     = 2
	n_threads   = 1 # 28*2
	TEST_every  = 50
	loss        = 0.
	train_data, valid_data = get_datasets(input_dir, n_train, n_valid)
	valid_accuracy         = np.zeros(int((n_train // TEST_every )*n_epoch) + 2)
	#valid_accuracy[0]      = test_validation(valid_data,theta_learn,n_valid)
	print(str(datetime.datetime.now()) + ' Training is starting!')
	adam = tf.optimizers.Adam(learning_rate=0.3)
	print(w)
	for epoch in range(n_epoch): 
		for n_file in range(n_train):
			t0 = time.time()
			B, y = preprocess(train_data[n_file])
			theta_learn,loss = train(B[:10,:],theta_learn,y[:10])
			
			t = time.time() - t0
			# Log 
			with open(log_dir+'log_theta.csv', 'a') as f:
				for item in theta_learn:
					f.write('%.4f,' % item)
				f.write('\n')
			with open(log_dir+'log_loss.csv', 'a') as f:
				f.write('%.4f\n' % loss)
			with open(log_dir+'summary.csv', 'a') as f:
				f.write('Epoch: %d, Batch: %d, Loss: %.4f, Elapsed: %dm%ds\n' % (epoch+1, n_file+1, loss, t / 60, t % 60) )
			print(str(datetime.datetime.now()) + " Epoch: %d, Batch: %d, Loss: %.4f, Elapsed: %dm%ds" % (epoch+1, n_file+1, loss ,t / 60, t % 60) )
			# Test validation data
			if (n_file+1)%TEST_every==0:
				valid_accuracy[((n_file+1)//TEST_every)*(epoch+1)] = test_validation(valid_data,theta_learn,n_valid)
		print('Epoch Complete!')
	valid_accuracy[-1] = test_validation(valid_data,theta_learn,n_valid)
	print('Training Complete!')

	
