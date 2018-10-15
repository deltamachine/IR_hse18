import os
import json
import string
import pickle
import numpy as np
import pandas as pd
from math import log
from judicial_splitter import splitter
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize
from pymorphy2 import MorphAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec, KeyedVectors, Doc2Vec
from gensim.models.doc2vec import LabeledSentence
from gensim import matutils

import warnings
warnings.filterwarnings("ignore")


def preprocessing(text, mode):
	morph = MorphAnalyzer()
	stops = stopwords.words('russian')
	punct = string.punctuation + '«»“”—…'
	
	text = text.lower()
	tokens = wordpunct_tokenize(text)
	all_lemmas = [morph.parse(token)[0].normal_form for token in tokens]
	
	if mode == 'd2v':
		cleaned_lemmas = [lemma for lemma in all_lemmas if lemma not in punct]
	else:
		cleaned_lemmas = [lemma for lemma in all_lemmas if lemma not in stops and lemma not in punct]
 
	return cleaned_lemmas


#==================Inverted index================


def score_BM25(idf, freq, D, avgdl):
	k1 = 2.0
	b = 0.75

	score = idf * (k1 + 1) * freq / (freq + k1 * (1 - b + b * D / avgdl))
	
	return score


def search_inv_index(request):
	request = preprocessing(request, 'ii')

	with open('data/list_of_files.txt', 'r', encoding='utf-8') as file:
		list_of_files = file.read().strip('\n').split('\n')

	with open('data/avito_tdm.json', 'r', encoding='utf-8') as file:
		term_doc_matrix = json.load(file)
	
	with open('data/avito_doc_lengths.json', 'r', encoding='utf-8') as file:
		doc_lengths = json.load(file)

	with open('data/avito_idfs.json', 'r', encoding='utf-8') as file:
		idfs = json.load(file)

	with open('data/avito_avgdl.txt', 'r', encoding='utf-8') as file:
		avgdl = float(file.read())

	results = {file: 0 for file in list_of_files}
	
	for word in request:
		if word in term_doc_matrix.keys():
			for doc in range(0, len(list_of_files)):
				if str(doc) in term_doc_matrix[word].keys():
					freq = term_doc_matrix[word][str(doc)]
				else:
					freq = 0

				D = doc_lengths[str(doc)]
				idf = idfs[word]  
				bm25 = score_BM25(float(idf), float(freq), int(D), avgdl)  
				
				results[list_of_files[doc]] += bm25
	
	return sorted(results.items(), key=lambda kv: kv[1], reverse=True)[:10]


#=======================Word2Vec==============================


def get_w2v_vectors(paragraph):
	model = Word2Vec.load('data/araneum_none_fasttextcbow_300_5_2018.model')
	counter = 0
	hypervector = np.zeros(300)
	
	for word in paragraph:
		try:
			vector = np.array(model.wv[word])
			hypervector += vector
			counter += 1
		except:
			continue

	hypervector = hypervector / counter
	
	return hypervector


def search_w2v(request):
	request = preprocessing(request, 'w2v')
	vec_request = get_w2v_vectors(request)  
	results = {}
	
	with open('data/avito_base_w2v.json', 'r', encoding='utf-8') as file:
		base = json.load(file)
	
	for elem in base:
		res = cosine_similarity([np.nan_to_num(vec_request)], [np.nan_to_num(elem[0])])[0][0]
		results[elem[1]] = res
	
	return sorted(results.items(), key=lambda kv: kv[1], reverse=True)[:10]


#====================Doc2Vec==============================


def search_d2v(request):
	request = ' '.join(preprocessing(request, 'd2v'))
	trained_model = Doc2Vec.load('data/avito_doc2vec.model')
	vec_request = trained_model.infer_vector(request) 
	results = {}
	
	with open('data/avito_base_d2v.json', 'r', encoding='utf-8') as file:
		base = json.load(file)
	
	for elem in base:
		res = cosine_similarity([np.nan_to_num(vec_request)], [np.nan_to_num(elem[0])])
		results[elem[1]] = res
	
	return sorted(results.items(), key=lambda kv: kv[1], reverse=True)[:10]


def search(request, mode):
	if mode == 'ii':
		res = search_inv_index(request)
	elif mode == 'w2v':
		res = search_w2v(request)
	elif mode == 'd2v':
		res = search_d2v(request)

	result = {i + 1: 'https://www.avito.ru/moskva/chasy_i_ukrasheniya/' + link[0].strip('.txt') for i, link in enumerate(res)}

	return result
