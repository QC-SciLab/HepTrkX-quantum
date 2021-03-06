# Calculates gradients of a pennylane quantum circuit
# using tensorflow
import pennylane as qml 
from pennylane import numpy as np
import tensorflow as tf
import sys

dev1 = qml.device("default.qubit", wires=6)

@qml.qnode(dev1,interface='tf')
def TTN_edge_forward(edge,theta_learn):
	# Takes the input and learning variables and applies the
	# network to obtain the output
	
	# STATE PREPARATION
	for i in range(len(edge)):
		qml.RY(edge[i],wires=i)
	# APPLY forward sequence
	qml.RY(theta_learn[0],wires=0)
	qml.RY(theta_learn[1],wires=1)
	qml.CNOT(wires=[0,1])
	qml.RY(theta_learn[2],wires=2)
	qml.RY(theta_learn[3],wires=3)
	qml.CNOT(wires=[2,3])
	qml.RY(theta_learn[4],wires=4)
	qml.RY(theta_learn[5],wires=5)
	qml.CNOT(wires=[5,4])
	qml.RY(theta_learn[6],wires=1)
	qml.RY(theta_learn[7],wires=3)
	qml.CNOT(wires=[1,3])
	qml.RY(theta_learn[8],wires=3)
	qml.RY(theta_learn[9],wires=4)
	qml.CNOT(wires=[3,4])
	qml.RY(theta_learn[10],wires=4)		
	return qml.expval(qml.PauliZ(wires=4))

def binary_cross_entropy(output,label):
	return - label*tf.math.log(output+1e-6) - (1-label)*tf.math.log(1-output+1e-6) 

def tf_grad(edge,theta_learn,label):
	with tf.GradientTape() as tape:
		output = (1 - TTN_edge_forward(edge,theta_learn))/2
		loss = binary_cross_entropy(output,label)
		grad = tape.gradient(loss,theta_learn)
	return grad
############################################################################################
if __name__ == '__main__':
	tf.executing_eagerly()
	#w = tf.Variable(tf.random.uniform([11,1],0,2*np.pi,dtype=tf.float64),dtype=tf.float64)
	#theta_learn = np.array([0.59955824, 0.72293889, 0.76065828, 0.07674539, 0.22250796, 0.68152528, 0.72906506, 0.67450772, 0.51897852, 0.57968062, 0.3478734]) * 2 * np.pi
	#w = tf.Variable(theta_learn,dtype=tf.float64)
	w = tf.Variable(np.random.rand(11) * np.pi * 2,dtype=tf.float64)

	#sys.exit()

	edge_array = np.array([0.39437991, 0.58592331, 0.71819769, 0.07528009, 0.98749489, 0.21369549]) * 2 * np.pi 
	y = 0
	opt = tf.keras.optimizers.Adam(learning_rate=0.1)

	grad = tf_grad(edge_array,w,y)
	grad_np = 
	print(grad)
	
	print('Gradients: ')
	for idx in range(len(grad)):
		print('Angle %d: %.2f' %(idx,grad[idx]))
	print('Angles: ')
	for idx in range(tf.size(w)):
		print('Angle %d: %.2f' %(idx,w[idx]))

	print(w)
	print(grad)

	opt.apply_gradients(zip([grad],[w]))
	print(w)
	




