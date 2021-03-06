"""
	Lyrics-based Music Classification
------------------------------------------------------------------------------------------------
	CS 221 Fall 2016 Project

	Author: Dhruv Joshi

	A modular system to train different algorithms to identify strings of lyrics and classify them into genres.
	10 most common genres have been selected, based on topicality, propensity to being identified through lyrics and availability

	Algorithms used are: 
	- Logistic Regression
	- Naive Bayes
	- Random Forest
	- Neural Networks

"""
''' Modules to read data from mysql, convert into a form which is pare-able by python, and then train data'''
import sys
import MySQLdb
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score

from textblob import TextBlob
import pandas as pd
import re
import numpy
import pickle

### ------------------------------------------------------------------------------------------####
# custom Modules 																			  ####
### ------------------------------------------------------------------------------------------####
import util
import classifiers
### ------------------------------------------------------------------------------------------####

logistic = LogisticRegression()

# command line parameter variables
valid_cli_args = ['-f', '-m']
valid_models = ['log', 'rfc', 'nn', 'baseline']

# We fix upon 10 broad genres
genres = util.get_genres()

### DO NOT CHANGE THE FILENAMES BELOW THIS LINE!
# topwords_dump_filename = 'TopWords_' + util.get_filename()
# with open(topwords_dump_filename) as f:
#	topwords = pickle.load(f)

### ------------------------------------------------------------------------------------------####



### ------------------------------------------------------------------------------------------####
### MODEL FUNCTIONS 
### ------------------------------------------------------------------------------------------####

def train_logistic(X_train, y_train, X_test, y_test):
	"""
	@param dataset: DataFrame containing ('lyrics', genre) where genre is an integer class 0..N 
	trains a logistic regression classifier and reports how well it performs on a cross-validation dataset.
	returns the fitted classifier object (sklearn.linear_model.LogisticRegression).
	REF: https://www.codementor.io/python/tutorial/data-science-python-r-sentiment-classification-machine-learning
	"""
	
	LogisticRegressionClassifier = LogisticRegression()
	LogisticRegressionClassifier = LogisticRegressionClassifier.fit(X=X_train, y=y_train)

	# print how well classification was done
	y_pred = LogisticRegressionClassifier.predict(X_test)
	print(classification_report(y_test, y_pred))

	return LogisticRegressionClassifier



def train_naiveBayes(dataset):
	"""
	@param dataset: DataFrame containing ('lyrics', genre) where genre is an integer class 0..N 
	Trains a Naive Bayes classifier and reports how well it performs
	REF: http://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html
	"""
	# create an instance of CountVectorizer class which will vectorize the data
	vectorizer = CountVectorizer(
	    analyzer = 'word',
	    tokenizer = feature_parse,
	    lowercase = True,
	    stop_words = 'english',
	    max_features = 3000
	)
	# fit bag of words model and convert to relative frequencies instead of absolute counts
	data_features = vectorizer.fit_transform(dataset['lyrics'].tolist())
	data_features = data_features.toarray()
	tfidf_transformer = TfidfTransformer()
	X_train_tfidf = tfidf_transformer.fit_transform(data_features)

	# Now we prepare everything for logistic regression
	X_train, X_test, y_train, y_test  = train_test_split(
        X_train_tfidf, 
        dataset['genre'],
        train_size=0.80
    )

	# train classifier
	naiveBayesClassifier = MultinomialNB().fit(X=X_train, y=y_train)
	# print how well classification was done
	y_pred = naiveBayesClassifier.predict(X_test)
	print(classification_report(y_test, y_pred))

	return naiveBayesClassifier 

def trainRandomForest(X_train, y_train, X_test, y_test):
	"""
	@param dataset: DataFrame containing ('lyrics', genre) where genre is an integer class 0..N 
	Trains a random forest classifier 
	https://www.stat.berkeley.edu/~breiman/RandomForests/cc_home.htm
	"""
	# random forest classifier with 100 trees
	forest = RandomForestClassifier(n_estimators = 100) 
	forest = forest.fit(X=X_train, y=y_train)

	y_pred = forest.predict(X_test)
	print classification_report(y_test, y_pred)
	print "accuracy:", accuracy_score(y_test, y_pred)

	return forest 

def trainNeuralNet(X_train, y_train, X_test, y_test):
	"""
	@param dataset: DataFrame containing ('lyrics', genre) where genre is an integer class 0..N 
	Trains a neural network
	REF: http://scikit-learn.org/stable/modules/neural_networks_supervised.html
	"""
	# train NN, limited memory BFGS, step size 1e-5
	nn = MLPClassifier(solver='lbfgs', alpha=1e-5, hidden_layer_sizes=(5, 2), random_state=1)
	nn = nn.fit(X=X_train, y=y_train)

	y_pred = nn.predict(X_test)
	print(classification_report(y_test, y_pred))

	return nn


### ------------------------------------------------------------------------------------------####
### FEATURE EXTRACTION FUNCTIONS
### ------------------------------------------------------------------------------------------####

# convert to a format that the algo can use
# REF: https://www.codementor.io/python/tutorial/data-science-python-r-sentiment-classification-machine-learning
def feature_parse(data, option='bow'):
	"""
	The data is a tuple of tuples (lyrics, genre)
	"""
	# perform basic stuff, like stemming
	# stemmer = PorterStemmer()
	# data = stemmer.stem(data)
	if option == 'bow':
		# perform bag of words feature extraction
		tokens = re.findall(r"\w+(?:[-']\w+)*|'|[-.(]+|\S\w*", data)		# REF: http://www.nltk.org/book/ch03.html 'Regular expressions for tokenizing text'
	if option == '3gram':
		# 3-gram model (TODO: Including backoff?)
		raise Exception('3-gram has not been implemented yet!')
	return tokens

def numerical_features(dataset, n=3):
	# Different methodology to extract features
	# 'n' of the ngrams to be extracted
	'''
	for i, l in enumerate(dataset['lyrics'].tolist()):
		X.append(util.sentence_stats(l))
		y.append(dataset['genre'][i])
	'''
	# FIRST split into train test sets
	ridict = util.setupRID()	# setup RID object
	D_train, D_test, y_train, y_test  = train_test_split(dataset['lyrics'], dataset['genre'], train_size=0.80)

	# Then extract most popular words and n-grams from the training set ONLY
	print 'generating topwords and topngrams..',
	topwords = util.NmostComWords(D_train, y_train)
	topngrams = util.NMostComNgrams(D_train, y_train, n)
	print 'done!'

	# convert to design matrices
	# for i,l in enumerate(D_train):
	#	X_train.append(util.sentence_stats(l, topwords))
	print 'converting to vectors..',
	X_train = [util.sentence_stats(l, ridict, topwords, topngrams, n) for l in D_train]
	X_test = [util.sentence_stats(l, ridict, topwords, topngrams, n) for l in D_test]
	print 'done!'

	# for i,l in enumerate(D_test):
	#	X_test.append(util.sentence_stats(l, topwords)) 

	# convert all to numpy arrays before shipping out
	X_train = numpy.array(X_train)
	y_train = numpy.array(y_train)
	X_test = numpy.array(X_test)
	y_test = numpy.array(y_test)

	# return everything that you would need to keep constant
	# the topwords and topngrams should be saved for making future predictions...
	return (X_train, y_train, X_test, y_test, topwords, topngrams)
	# return (X_train, y_train, X_test, y_test)


def get_features(dataset, max_features=3000, tokenizer=feature_parse):
	"""
	Choose features and the way that features are created
	Create train test split from dataset after sparse feature representations are created
	"""
	# create an instance of CountVectorizer class which will vectorize the data
	vectorizer = CountVectorizer(
	    analyzer = 'word',
	    tokenizer = tokenizer,
	    lowercase = False,
	    stop_words = 'english',
	    max_features = max_features		# can go upto 5000 on corn.stanford.edu
	)
	# Fit the data
	data_features = vectorizer.fit_transform(dataset['lyrics'].tolist())
	data_features = data_features.toarray()
	# print vectorizer.get_feature_names()

	# tf-idf transformation
	# TODO: Put option for having or not having this
	# tfidf_transformer = TfidfTransformer()
	# X_tfidf = tfidf_transformer.fit_transform(data_features)

	# Now we prepare everything for logistic regression
	X_train, X_test, y_train, y_test  = train_test_split(
        data_features, 
	# X_tfidf,
        dataset['genre'],
        train_size=0.80
    )

    # Can extract a lot of features from the vectorizer
    # vectorizer.vocabulary_ gives the words used in the selected sparse feature matrix (http://stackoverflow.com/questions/22920801/can-i-use-countvectorizer-in-scikit-learn-to-count-frequency-of-documents-that-w)
    # 

	return (X_train, y_train, X_test, y_test)

### ------------------------------------------------------------------------------------------####
### MODEL RUNNING AND COMMAND LINE PARSING FUNCTIONS
### ------------------------------------------------------------------------------------------####

def run_model(cl):
	"""
	@param cl: The command line index from which to consider the model command
	Second one has to be one of 
	"""
	try:
		cl1 = str(sys.argv[cl])
		cl2 = str(sys.argv[cl+1])
	except IndexError:
		command_line_syntax('Please choose a model!')
		sys.exit(0)

	assert cl1 == '-m', command_line_syntax('You must enter -m to choose the model!')
	assert cl2 in valid_models, command_line_syntax('You have chosen an invalid model!')

	# First read in the data
	print 'Reading in data...',
	with open(util.get_filename(), 'r') as f:
		dataset = pd.read_csv(f)
	print 'done!'

	# Then create the features
	# X_train, y_train, X_test, y_test = get_features(dataset, max_features=5000)
	X_train, y_train, X_test, y_test = numerical_features(dataset)

	# Then run models based on what the argument says
	if cl2 == 'log':
		print 'Training logistic regression model...'
		logC = train_logistic(X_train, y_train, X_test, y_test)
	elif cl2 == 'rfc':
		print 'Training random forest classifier...'
		RFC = trainRandomForest(X_train, y_train, X_test, y_test)
	elif cl2 == 'nn':
		print 'Training Neural Net...'
		NN = trainNeuralNet(X_train, y_train, X_test, y_test)
	elif cl2 == 'baseline':
		training_set = [(x,y) for x,y in zip(X_train, y_train)]
		blC = classifiers.Baseline(training_set, class_labels=range(10), debug=True)
		blC.stochastic_grad_descent()
		y_pred = numpy.array([blC.predict(x) for x in X_test])
		# print y_pred
		# print y_test
		print classification_report(y_test, y_pred)
		print "accuracy score =", accuracy_score(y_test, y_pred)


def command_line_syntax(custom_starting_message=None):
	"""
	Tell user the correct syntax to use, then exit.
	"""
	if custom_starting_message:
		print custom_starting_message
	print 'Syntax of the command is:\npython main.py -f (optional)<file-to-get-data> -m <model-name>'
	print 'Options are\n\trfc - Random Forest Classifier\n\tbaseline - the baseline implementation\n\tnn - Neural Networks\n\tlog - Logstic Regression'
	print 'Quitting...'
	sys.exit(0)	


if __name__ == "__main__":
	# Check command line args...
	try:
		option = str(sys.argv[1])
		assert option in valid_cli_args, command_line_syntax('%s is not a valid argument!'%option)
	except IndexError:
		command_line_syntax('You have not entered any arguments!')

	if option == '-f':
		try:
			filename = str(sys.argv[2])
			print 'Will grab data from %s..'%filename,
		except IndexError:
			command_line_syntax('ERROR: Please enter a file location to get the data from!')
			sys.exit(0)
		# Read data from the CSV file and call the classifier to train on it
		# dataset = pd.read_csv(filename)
		print 'read complete.'

		# Now look for next argument for the type of classifier to use
		run_model(3)
	elif option == '-m':
		# first read default data
		run_model(1)
		sys.exit(0)
	command_line_syntax('No valid command line options given!')
	# train_logistic(dataset)
	# train_naiveBayes(dataset)
	# trainRandomForest(dataset)		# READ https://www.stat.berkeley.edu/~breiman/RandomForests/cc_home.htm
	# trainNeuralNet(dataset)



