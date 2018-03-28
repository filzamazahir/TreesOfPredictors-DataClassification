# Algorithm 2 and 3 of ToPs - copied code from TreesOfPredictors.py as of Wed Mar 28 12:30am

# Trees of Predictors (ToPs) ensemble learning method
# Source: https://arxiv.org/abs/1706.01396v2

# Project - ECE657A  (Group 21)  Filza Mazahir 20295951  &  Tarneem Barayyan 20645942 

# Import Libraries 
import pandas as pd
import numpy as np

from sklearn import preprocessing
from sklearn.model_selection import train_test_split

from sklearn.svm import SVC
from sklearn import linear_model
from sklearn.dummy import DummyClassifier

from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import AdaBoostClassifier

from sklearn.metrics import log_loss

from math import inf
import time



# LOAD DATA
file_location = 'OnlineNewsPopularity.csv'
news_df_original = pd.read_csv(file_location, sep=', ', engine='python')

# Drop non-predictive attributes
news_df = news_df_original.drop(['url', 'timedelta'], axis = 1)






# Getting dataset ready for training
news_y = news_df['shares']
news_y = news_y.apply(lambda x: 1 if x >=1400 else 0)

news_x = news_df.drop(['shares'], axis = 1)

# Standardization of the data
# zscore = preprocessing.StandardScaler().fit_transform(news_x)
# news_x = pd.DataFrame(zscore, columns=list(news_x.columns.values)) #convert to nice table 

minmax = preprocessing.MinMaxScaler(feature_range=(0, 1)).fit_transform(news_x)
news_x = pd.DataFrame(minmax, columns=list(news_x.columns.values)) #convert to nice table 
# print(news_x)
class_names = ['Unpopular (<1400)', 'Popular (>=1400)']


# Dataset split - Training - 50%, Validation 1: 15%, Validation 2: 15%, Test: 20%
# Dataset x split: x_train, x_validate1, x_validate2, x_test
# Dataset y split: y_train, y_validate1, y_validate2, y_test
# Split dataset into test set - 20% for testing, rest for training and validation
x_rest, x_test, y_rest, y_test = train_test_split(news_x, news_y, test_size=0.20, stratify=news_y)

# Split again to get training and validation
x_train, x_validate, y_train, y_validate = train_test_split(x_rest, y_rest, test_size=0.375, stratify=y_rest)

# Split the validation set into two
x_validate1, x_validate2, y_validate1, y_validate2 = train_test_split(x_validate, y_validate, test_size=0.5, stratify=y_validate)

# print(news_y)


# Node class
class Node:
	def __init__(self, x_train, y_train, x_validate1, y_validate1, loss_on_validation1, predictor, current_depth):
		self.x_train = x_train # Root node will have full data set
		self.y_train = y_train
		self.x_validate1 = x_validate1
		self.y_validate1 = y_validate1

		self.log_loss_value = loss_on_validation1
		self.predictor = predictor # Instance of a classifier predictor
		self.current_depth = current_depth

		self.left = None # Left side child Node instance
		self.right = None # Right side child Node instance

		# Set in the find_split function
		self.feature_to_split = None
		self.threshold = None


	def __str__(self):
		# string_to_print = 'Predictor: ' + str(self.predictor) + '\n'
		prefix = '   '*self.current_depth
		string_to_print = prefix + 'Feature to split: ' + str(self.feature_to_split) + '\n'
		string_to_print += prefix + 'Threshold: ' + str(self.threshold) +'\n'
		string_to_print += prefix + 'Log Loss: ' + str(self.log_loss_value) + '\n'
		if self.left == None:
			string_to_print += prefix + 'Left Child: ' + str(self.left) + '\n'
		else:
			string_to_print += prefix + 'Left Child: \n' + str(self.left) + '\n'

		if self.right == None:
			string_to_print += prefix + 'Right Child: ' + str(self.right) + '\n'
		else:
			string_to_print += prefix + 'Right Child: \n' + str(self.right) + '\n'

		# string_to_print += 'Features available: ' + str(self.training_data_x.columns.values) + '\n'

		return string_to_print
	


	# Split a node based on a given feature and threshold:\
	def split_node(self, threshold, feature):
		# print('Current Feature', feature)
		# print(' -Threshold', threshold)

		# Split the validation data
		right_x_validate1 = self.x_validate1[self.x_validate1[feature] >= threshold]
		right_validate1_indices = right_x_validate1.index.values
		right_y_validate1 = self.y_validate1.loc[right_validate1_indices]

		left_x_validate1 = self.x_validate1[self.x_validate1[feature] < threshold]
		left_validate1_indices = left_x_validate1.index.values
		left_y_validate1 = self.y_validate1.loc[left_validate1_indices]

		# Split the training data
		right_x_train = self.x_train[self.x_train[feature] >= threshold]
		right_train_indices = right_x_train.index.values
		right_y_train = self.y_train.loc[right_train_indices]

		left_x_train = self.x_train[self.x_train[feature] < threshold]
		left_train_indices = left_x_train.index.values
		left_y_train = self.y_train.loc[left_train_indices]

		# If data is too skewed one way and cannot be split 
		if len(right_x_train) == 0 or len(left_x_train) == 0 or len(right_x_validate1) == 0 or len(left_x_validate1) == 0:
			return None

		# Train classifier on the right data
		if len(right_y_train.unique()) == 1:
			clf_right = DummyClassifier()
			# print('Feature: {0}    Dummy Classifier used right'.format(feature))
		else:
			clf_right = linear_model.SGDClassifier(loss='log')
			# clf_right = RandomForestClassifier()
		clf_right.fit(right_x_train, right_y_train)
		clf_right_y_prediction = clf_right.predict(right_x_validate1)
		log_loss_value_right = log_loss(right_y_validate1, clf_right_y_prediction, normalize=False, labels = [0,1])

		# Train classifier on the left data
		if len(left_y_train.unique()) == 1:
			clf_left = DummyClassifier()
			# print('Feature: {0}    Dummy Classifier used left'.format(feature))
		else:
			clf_left = linear_model.SGDClassifier(loss='log')
			# clf_left = RandomForestClassifier()
		clf_left.fit(left_x_train, left_y_train) 
		clf_left_y_prediction = clf_left.predict(left_x_validate1)
		log_loss_value_left = log_loss(left_y_validate1, clf_left_y_prediction, normalize = False, labels = [0,1])

		# Create nodes based on this split, and return
		right_node = Node(right_x_train, right_y_train, right_x_validate1, right_y_validate1, log_loss_value_right, clf_right, self.current_depth+1)
		left_node = Node(left_x_train, left_y_train, left_x_validate1, left_y_validate1, log_loss_value_left, clf_left, self.current_depth+1)
	
		return(right_node, left_node)



	# Figure out what the feature_to_split and threshold is for current node, then assign children based on that split
	def find_feature_to_split(self, max_depth):
		# threshold = 0.5
		# feature = column_names[2]

		if self.current_depth >= max_depth:
			print('Depth reached - lets be done')
			return
		minimum_loss_so_far = inf
		feature_at_min_loss = None
		threshold_at_min_loss = None
		children_nodes_at_min_loss = None


		column_names = self.x_train.columns.values
		children_loss_values = []
		features_compared = []

		for feature in column_names:
			# threshold = 0.5   #FIX THRESHOLD!!
			for threshold in np.arange(0.1, 1.0, 0.1):
			# print(feature)
				children_nodes = self.split_node(threshold, feature)
				if children_nodes == None:
					continue

				right_node = children_nodes[0]
				left_node = children_nodes[1]

				# Compare log loss values of parent and children
				children_log_loss = (right_node.log_loss_value + left_node.log_loss_value)
				if children_log_loss < minimum_loss_so_far:
					# print("New min ", children_log_loss)
					minimum_loss_so_far = children_log_loss
					feature_at_min_loss = feature
					threshold_at_min_loss = threshold
					children_nodes_at_min_loss = children_nodes

			# print('Children log loss value appended', children_log_loss)
			# children_loss_values.append(children_log_loss)
			# features_compared.append(feature)

		# min_loss_column_index = children_loss_values.index(min(children_loss_values))
		# feature_to_split = features_compared[min_loss_column_index]

		if minimum_loss_so_far >= self.log_loss_value:
			print('END FUNCTION - All Children loss values bigger!!', minimum_loss_so_far)


		else: 
			print('---Parent loss bigger', self.log_loss_value) # we want this
			print('---All Children losses (smaller): ', minimum_loss_so_far)
			print('---Feature with this small loss:', feature_at_min_loss)

			# Assign threshold and feature_to_split, children attribute of this node
			self.threshold = threshold_at_min_loss
			self.feature_to_split = feature_at_min_loss
			self.right = children_nodes_at_min_loss[0]
			self.left = children_nodes_at_min_loss[1]

			# Assign children or this node based on threshold and feature_to_split found
			# self.right, self.left = self.split_node(threshold, feature_to_split)
			self.right.find_feature_to_split(max_depth)
			self.left.find_feature_to_split(max_depth)

		
		return

	def loss_values_of_all_leaf_nodes(self):
		sum_loss_value = 0

		if self.left == None and self.right == None:
			sum_loss_value += self.log_loss_value

		else:
			self.left.loss_values_of_all_leaf_nodes()
			self.right.loss_values_of_all_leaf_nodes()

		return sum_loss_value





def construct_root_node():
	clf_root = linear_model.SGDClassifier(loss='log')
	# clf_root = RandomForestClassifier()
	clf_root.fit(x_train, y_train) # Pass dataset into this function
	clf_root_y_prediction = clf_root.predict(x_validate1)
	loss_on_validation1 = log_loss(y_validate1, clf_root_y_prediction, normalize= False, labels = [0,1])

	root_node = Node(x_train, y_train, x_validate1, y_validate1, loss_on_validation1, clf_root, 0)
	return root_node
	


t0 = time.time()


root_node = construct_root_node()
root_node.find_feature_to_split(3)
print(root_node)
loss_on_leafs = root_node.loss_values_of_all_leaf_nodes
print('Loss values of all leafs', loss_on_leafs)


t1 = time.time()

print('Total Time taken: {0:.1f} seconds'.format(t1-t0))

















