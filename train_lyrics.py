"""
	Lyrics-based Music Classification
------------------------------------------------------------------------------------------------
	CS 221 Fall 2016 Project

	Author: Dhruv Joshi

	A modular system to train different algorithms to identify strings of lyrics and classify them into genres.
	10 most common genres have been selected, based on topicality, propensity to being identified through lyrics and availability

	Algorithms used are: 
	- Logistic Regression

"""
''' Modules to read data from mysql, convert into a form which is pare-able by python, and then train data'''
import sys
import MySQLdb
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from textblob import TextBlob
import pandas as pd
import re

logistic = LogisticRegression()

# NOTE: Make sure mysql server has been started! 
# > mysql.server start
print 'establishing connection to db...',
db = MySQLdb.connect(host="localhost", db="cs221_nlp", read_default_file='~/.my.cnf')
db_cursor = db.cursor()
print 'done!'

valid_cli_args = ['-d', '-f']
# We fix upon 10 broad genres
genres = ['Rock', 'Pop', 'Hip Hop/Rap', 'R&B;', 'Electronic', 'Country', 'Jazz', 'Blues', 'Christian', 'Folk']

# Format in which to put the songs:
# genre, url, lyrics
def get_songs_by_genre(genre_of_interest):
	"""
	@param: genre_of_interest: The genre you are interested in, as a string
	Send query to db for a particular genre
	"""
	query = "select lyrics from song where genre = '%s'" %genre_of_interest
	db_cursor.execute(query)
	data = db_cursor.fetchall()
	return data

def get_data(genres=genres):
	"""
	@param genres: List of genres (strings) to collect from the db
	Gets data from the db, arranges it in the form ('lyrics', genre_class), where genre_class is an int representing the genre
	It correspondds to the index in the genres list. Returns a Panda object (dataframe).
	"""
	dataset = []
	for label, genre in enumerate(genres):
		data = get_songs_by_genre(genre)
		for song in data:
			# song is a singleton tuple (since the db query returns only tuples), so need to extract
			dataset.append([song[0], label])
	# convert to pandas
	dataset = pd.DataFrame.from_records(dataset, columns=['lyrics', 'genre'])
	return dataset

# convert to a format that the algo can use
# REF: https://www.codementor.io/python/tutorial/data-science-python-r-sentiment-classification-machine-learning
def feature_parse(data, option='bow'):
	"""
	The data is a tuple of tuples (lyrics, genre)
	We want to clean this up and make it into a numpy array
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

def train_logistic(dataset):
	"""
	@param dataset: DataFrame containing ('lyrics', genre) where genre is an integer class 0..N 
	trains a logistic regression classifier and reports how well it performs on a cross-validation dataset.
	returns the fitted classifier object (sklearn.linear_model.LogisticRegression).
	"""
	# create an instance of CountVectorizer class which will vectorize the data
	vectorizer = CountVectorizer(
	    analyzer = 'word',
	    tokenizer = feature_parse,
	    lowercase = True,
	    stop_words = 'english'
	)
	# Fit the data
	data_features = vectorizer.fit_transform(dataset['lyrics'].tolist())
	data_features = data_features.toarray()
	# print vectorizer.get_feature_names()

	# Now we prepare everything for logistic regression
	X_train, X_test, y_train, y_test  = train_test_split(
        data_features, 
        dataset['genre'],
        train_size=0.85
    )
	LogisticRegressionClassifier = LogisticRegression()
	LogisticRegressionClassifier = LogisticRegressionClassifier.fit(X=X_train, y=y_train)

	# print how well classification was done
	y_pred = LogisticRegressionClassifier.predict(X_test)
	from sklearn.metrics import classification_report
	print(classification_report(y_test, y_pred))

	return LogisticRegressionClassifier


if __name__ == "__main__":
	# Check command line args...
	option = str(sys.argv[1])
	assert option in valid_cli_args, '%s is not a valid argument!'%option
	if option == '-d':
		print 'Will grab data from MYSQL database..'
		dataset = get_data(genres=['Electronic', 'Country', 'Jazz', 'Blues', 'Christian', 'Folk'])
		train_logistic(dataset)
	if option == '-f':
		try:
			filename = str(sys.argv[2])
			print 'Will grab data from %s..'%filename,
		except IndexError:
			print 'ERROR: Please enter a file location to get the data from! Command is -f </path/to/file>. Quitting...'
			sys.exit(0)
		# Read data from the CSV file and call the classifier to train on it
		dataset = pd.read_csv(filename)
		print 'read complete. Training...'
		train_logistic(dataset)
