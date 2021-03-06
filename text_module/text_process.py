'''
@author: Terry Ruas 2018-03-12
'''
#general libraries
import re
import numpy as np
from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words

#self-packages
import wordnet_module.my_data as md

def build_word_data(words, trained_model, recurrent_flag):
    import wordnet_module.synset_tracker as systra 
    words_list = list()
   
    for word in words:
        temp_data = systra.build_synset_data(word, trained_model, recurrent_flag) #recurrent_flag = True : Refinement; False:Normal        
        if temp_data:
            tmp_word = md.WordsData(word)#initialize WordsData
            tmp_word.synset_pack = temp_data
            words_list.append(tmp_word)
        else:
            pass #no synset was mapped for this document
    return(words_list)    
#create a list of WordsData based on a iterable list of WORDS - Use RefiData or DefiData
#recurrent_flag = true : Workinf with RefiData; false - working with DefiData
#if the word does not exist in WordNet or in the Model we move to the new word in the document


def gloss_average_vector(words_data, token_model_embeddings, recurrent_flag):       
    
    if(recurrent_flag): return(words_data) #with synset-model is used there is no need to calculate gloss-avg-vector
    
    temp_dict = {}#temporary dictionary to avoid repetitive gloss-vector average for each document(words-data)
    for w in words_data: #word-token from text
        for gloss_data in w.synset_pack: #list of synsets with their offset/pos/glosses
            if gloss_data.sys_id in temp_dict: #check if the synset for this document already has an average-calculated vector
                gloss_data.gloss_avg_vec = temp_dict.get(gloss_data.sys_id)
            else: #if this is the first time the synset is evaluated calculate its average-gloss-vector        
                gloss_tokens = tokenize_gloss(gloss_data.gloss) #tokenize gloss
                vecs = []
                for gloss_token in gloss_tokens:
                    try:
                        vec = token_model_embeddings.word_vec(gloss_token) #return the vector for the token in the gloss
                        vecs.append(vec) #make a list of all token-vector from the word embedding
                    except KeyError:
                        pass #we do not want to average those non-existent vector. [0.0] should not count for the average
                gloss_data.gloss_avg_vec = np.average(vecs, axis=0) #average all token-gloss-vectors in vecs - independent of the model dimensionality
                temp_dict[gloss_data.sys_id] = gloss_data.gloss_avg_vec #add its synset:average-gloss-vector 
    return(words_data)           
#calculates the average dim-value of the words in the gloss of every word that exists in a word2vec model
 
def tokenize_gloss(gloss_text):
    tokenizer = RegexpTokenizer(r'\w+')
    en_stop = get_stop_words('en')   
    raw = str(gloss_text.lower())
    tokens = tokenizer.tokenize(raw)
    #remove stopwords
    stopped_tokens = [i for i in tokens[:] if not i in en_stop] #[1:] get rid of the first element
    # remove numbers
    nonumber_text = [re.sub(r'[\d]', ' ', i) for i in stopped_tokens]
    nonumber_text = ' '.join(nonumber_text).split()
    return(nonumber_text)
#cleans gloss words from numbers and stopwords

def key_parser(word, offset, pos):
    return(word.lower() +'#'+str(offset)+'#'+pos)
#Transforms word,offset,pos into key that is used in synset2vec model