#################################################################
#################################################################
############### DE 
#################################################################
#################################################################

#############################################
########## 1. Load libraries
#############################################
##### 1. General support #####
import qgrid, requests, json
import pandas as pd
import numpy as np
from IPython.display import display, Markdown

##### 2. Other libraries #####


#######################################################
#######################################################
########## S1. Function
#######################################################
#######################################################

#############################################
########## 1. Run
#############################################

def get_enrichr_results(user_list_id, gene_set_libraries, overlappingGenes=True):
	ENRICHR_URL = 'http://amp.pharm.mssm.edu/Enrichr/enrich'
	query_string = '?userListId=%s&backgroundType=%s'
	results = []
	for gene_set_library in gene_set_libraries:
		response = requests.get(
			ENRICHR_URL + query_string % (user_list_id, gene_set_library)
		 )
		if not response.ok:
			raise Exception('Error fetching enrichment results')

		data = json.loads(response.text)
		resultDataframe = pd.DataFrame(data[gene_set_library], columns=['rank', 'term_name', 'pvalue', 'zscore', 'combined_score', 'overlapping_genes', 'FDR', 'old_pvalue', 'old_FDR'])
		selectedColumns = ['term_name','zscore','combined_score','pvalue', 'FDR'] if not overlappingGenes else ['term_name','zscore','combined_score','FDR', 'pvalue', 'overlapping_genes']
		resultDataframe = resultDataframe.loc[:,selectedColumns]
		resultDataframe['gene_set_library'] = gene_set_library
		results.append(resultDataframe)
	concatenatedDataframe = pd.concat(results)
	return concatenatedDataframe

def run(enrichr_results, signature_label, libraries=['KEA_2015']):
	results = []
	for geneset in ['upregulated', 'downregulated']:
		enrichment_dataframe = get_enrichr_results(enrichr_results[geneset]['userListId'], libraries)
		enrichment_dataframe['geneset'] = geneset
		results.append(enrichment_dataframe)
	kinase_dataframe = pd.concat(results)
	kinase_dataframe['Protein Kinase'] = [x.split('_')[0] for x in kinase_dataframe['term_name']]
	kinase_dataframe = kinase_dataframe.sort_values('pvalue').rename(columns={'term_name': 'KEA Term', 'geneset': 'Direction', 'pvalue': 'P-value', 'overlapping_genes': 'Targets'}).drop_duplicates('Protein Kinase')
	kinase_dataframe['Rank'] = [x+1 for x in range(len(kinase_dataframe.index))]
	kinase_dataframe = kinase_dataframe[['Rank', 'Protein Kinase', 'P-value', 'FDR', 'Direction', 'Targets']]
	return {'kinase_dataframe': kinase_dataframe, 'signature_label': signature_label}

#############################################
########## 2. Plot
#############################################

def plot(kinase_analysis_results):
	kinase_dataframe = kinase_analysis_results['kinase_dataframe']
	kinase_dataframe['Protein Kinase'] = ['<a href="#">{}</a>'.format(x) for x in kinase_dataframe['Protein Kinase']]
	display(Markdown('### {signature_label} Signature:'.format(**kinase_analysis_results)))
	return display(qgrid.show_grid(kinase_dataframe.drop('Targets', axis=1).set_index('Rank'), grid_options={'maxVisibleRows': 4, 'forceFitColumns': True}))